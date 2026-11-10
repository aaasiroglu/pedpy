"""Global PED inventory, step 2: locate each booklet project and fetch a candidate boundary from OpenStreetMap. (K-068)

For every project the *site name* (district, quarter, campus) is taken from the booklet's own text: a candidate
name is accepted only if it literally occurs in that project's section. The name is then searched in OSM
(Nominatim, ODbL) together with the city. Result levels:
  site_polygon  OSM has an area with that name  → candidate boundary (to be checked against the project map)
  site_point    OSM has only a point             → location known, boundary must be digitised
  city          no site name in the booklet/OSM  → only the city is known
Nothing here is a final boundary: `boundary_status` stays "candidate" until checked against a project document.

    python scripts/geocode_ped_inventory.py booklet.txt  → data/inventory/ped_sites_global.csv, ped_sites_global.geojson
"""

import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "data" / "inventory"
UA = "pedx-research/0.1 (MSc thesis, Istanbul Technical University)"
# candidate site names per booklet project number; kept only if the name occurs in that project's section
CAND = {1: ["Åland"], 2: ["Fleuriaye"], 4: ["Buiksloterham"], 5: ["Fornebu"], 6: ["Zorrotzaurre", "Zorrozaurre"], 8: ["Ydalir"],
        10: ["Reininghaus"], 11: ["Paddepoel", "Zernike"], 14: ["Brunnshög"], 16: ["Furuset"], 17: ["Kaukovainio"],
        18: ["Evenstad"], 19: ["Gløshaugen"], 20: ["Brattøra", "Sluppen"], 22: ["Ådland"],
        23: ["Espoonlahti", "Leppävaara", "Kera"], 24: ["Castelletto"], 25: ["La Pinada"], 26: ["Pietralata"],
        27: ["Ilokkaanpuisto"], 28: ["Santa Chiara"], 30: ["Jacob Borchs gate"], 31: ["Otaniemi"], 34: ["Linero"],
        35: ["Pozo Barredo"], 38: ["Hammarby Sjöstad"], 40: ["Hunziker Areal"], 42: ["Novoli"],
        45: ["Kalasatama", "Merihaka"], 47: ["Østerby"], 48: ["Nijstad-Oost"], 49: ["Pfaff"], 50: ["Brunnshög"],
        51: ["Medicon Village"], 52: ["Hyllie"], 53: ["Werksviertel"], 58: ["Dietenbach"], 60: ["Madonna Bianca"]}


def sections(txt):
    lines = Path(txt).read_text(encoding="utf-8").splitlines()
    idx = [i for i, l in enumerate(lines) if l.strip().lower() == "general information" and i > 290]
    return {n: "\n".join(lines[s:(idx[n] if n < len(idx) else len(lines))]) for n, s in enumerate(idx, 1)}


def nominatim(q):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "jsonv2", "polygon_geojson": 1, "limit": 3, "accept-language": "en"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40) as r:
                time.sleep(1.1)
                return json.load(r)
        except Exception:
            time.sleep(3 * (attempt + 1))
    return None


def area_ha(geojson):
    import shapely
    from shapely.geometry import shape
    g = shape(geojson); lat = g.centroid.y
    import math
    g = shapely.transform(g, lambda c: c * [111320 * math.cos(math.radians(lat)), 110540])
    return g.area / 1e4


def area_ok(x):
    """A named OSM area is a boundary candidate only if it is a place, an administrative unit or a land-use
    polygon (not a car park, road, stream or railway land)."""
    c, t = x.get("category"), x.get("type")
    return c in ("place", "boundary") or (c == "landuse" and t in ("residential", "industrial", "commercial", "construction", "brownfield", "retail"))


def main(txt):
    sec = sections(txt)
    rows = list(csv.DictReader((INV / "ped_booklet_2020.csv").open(encoding="utf-8")))
    cache_p = ROOT / "data" / "cache" / "nominatim_ped.json"
    cache = json.loads(cache_p.read_text()) if cache_p.exists() else {}
    out, feats = [], []
    for r in rows:
        n = int(r["no"]); city = re.sub(r"\s*\(.*?\)", "", r["place"]).split(",")[0].strip()
        names = [c for c in CAND.get(n, []) if c.lower() in sec.get(n, "").lower()] or [None]
        for name in names:
            q = ", ".join(x for x in (name, city, r["country"]) if x)
            if q not in cache:
                cache[q] = nominatim(q); cache_p.write_text(json.dumps(cache, ensure_ascii=False))
            res = cache[q] or []
            poly = next((x for x in res if x.get("geojson", {}).get("type") in ("Polygon", "MultiPolygon") and area_ok(x)), None)
            hit = (poly if name else None) or (res[0] if res else None)
            level = "not_found" if not hit else ("city" if not name else ("site_polygon" if hit is poly else "site_point"))
            rec = {"id": f"booklet-{n:02d}" + (f"-{names.index(name) + 1}" if len(names) > 1 else ""), "booklet_no": n,
                   "site_name": name or "", "city": city, "country": r["country"], "project": r["project"],
                   "declared_ped": "yes" if r["category"] == "PED" else "no (towards PED)", "status": r["status"],
                   "structure": r["structure"], "size_raw": r["size_raw"], "level": level,
                   "lat": hit and round(float(hit["lat"]), 6), "lon": hit and round(float(hit["lon"]), 6),
                   "osm": hit and f'{hit["osm_type"]}/{hit["osm_id"]}', "osm_class": hit and f'{hit.get("category")}={hit.get("type")}',
                   "osm_area_ha": round(area_ha(hit["geojson"]), 1) if level == "site_polygon" else "",
                   "osm_display": hit and hit.get("display_name", "")[:120], "boundary_status": "candidate" if level == "site_polygon" else "missing",
                   "source": r["source"]}
            out.append(rec)
            if hit:
                geom = hit["geojson"] if level == "site_polygon" else {"type": "Point", "coordinates": [float(hit["lon"]), float(hit["lat"])]}
                feats.append({"type": "Feature", "geometry": geom, "properties": {k: v for k, v in rec.items() if k not in ("lat", "lon")}})
            print(rec["id"], level, q, "→", rec["osm"], rec["osm_class"], flush=True)
    with (INV / "ped_sites_global.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(out[0])); w.writeheader(); w.writerows(out)
    (INV / "ped_sites_global.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False))
    from collections import Counter
    print(Counter(r["level"] for r in out), len(out))


if __name__ == "__main__":
    main(sys.argv[1])

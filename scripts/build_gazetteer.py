"""Place-name gazetteer for pedx-agent (K-058), built from data, not written by hand.

Every named Overture division (county, locality, macrohood, neighborhood, microhood; ODbL) and every Wikidata item
of a place class (neighbourhood, quarter, mahalle, suburb, district, city …; CC0) inside an area window becomes an
alias of that area. Wikidata is added because Overture misses well-known neighbourhoods (no "Moda" in Kadıköy).
A point that falls in several windows (Moda lies in the Caferağa, Kadıköy and İstanbul windows) goes to the window
whose site centre is nearest — the most specific pilot.
Names that occur in two different areas, or that are shorter than 4 letters, are dropped as ambiguous.

    python scripts/build_gazetteer.py   → src/pedx/agent/gazetteer.json
"""

import json
import math
import time
import urllib.parse as up
import urllib.request
from collections import defaultdict
from pathlib import Path

from pedx.agent.tools import _norm
from pedx.datalake import overture as ov

ROOT = Path(__file__).resolve().parents[1]
GRID = ROOT / "data" / "cache" / "citygrid"
OUT = ROOT / "src" / "pedx" / "agent" / "gazetteer.json"
SUBTYPES = {"county", "localadmin", "locality", "borough", "macrohood", "neighborhood", "microhood"}
LANGS = ("en", "tr", "fr", "es", "eu", "nl", "fi", "sv", "de", "no", "nb")
# Wikidata place classes: neighbourhood, quarter, mahalle, suburb, urban district, city, big city, municipality of
# Finland/Sweden-style districts, district of a city, administrative quarter, borough
WD_CLASSES = "Q123705 Q2983893 Q17051044 Q188509 Q15715406 Q515 Q1549591 Q1907114 Q1394476 Q12813115 Q5195043 Q3957 Q532 Q1529096 Q2198484 Q1080224 Q484170"
SUFFIX = (" mahallesi", " mahalle")


def km(lat1, lon1, lat2, lon2):
    return 6371 * math.hypot(math.radians(lat2 - lat1), math.radians(lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2)))


def wikidata_places(bbox, cache):
    """Wikidata items of a place class located in the window, with tr/en/local labels; cached as JSON (CC0)."""
    if cache.exists():
        return json.loads(cache.read_text())
    w, s, e, n = bbox
    vals = " ".join("wd:" + q for q in WD_CLASSES.split())
    q = f"""SELECT ?item ?coord ?label WHERE {{
      SERVICE wikibase:box {{ ?item wdt:P625 ?coord. bd:serviceParam wikibase:cornerSouthWest "Point({w} {s})"^^geo:wktLiteral.
                              bd:serviceParam wikibase:cornerNorthEast "Point({e} {n})"^^geo:wktLiteral. }}
      ?item wdt:P31 ?cls. VALUES ?cls {{ {vals} }}
      ?item rdfs:label ?label. FILTER(lang(?label) IN ({", ".join(repr(x).replace("'", '"') for x in LANGS)})) }}"""
    rq = urllib.request.Request("https://query.wikidata.org/sparql?" + up.urlencode({"query": q, "format": "json"}), headers={"User-Agent": "pedx-research/0.1"})
    for i in range(4):
        try:
            with urllib.request.urlopen(rq, timeout=180) as r:  # noqa: S310
                b = json.load(r)["results"]["bindings"]
            break
        except Exception:  # noqa: BLE001
            if i == 3:
                raise
            time.sleep(10 * 2**i)
    items = {}
    for x in b:
        lon, lat = map(float, x["coord"]["value"].removeprefix("Point(").rstrip(")").split())
        it = items.setdefault(x["item"]["value"].rsplit("/", 1)[1], {"lat": lat, "lon": lon, "labels": set()})
        it["labels"].add(x["label"]["value"])
    rows = [{"qid": k, "lat": v["lat"], "lon": v["lon"], "subtype": "wikidata", "labels": sorted(v["labels"])} for k, v in items.items()]
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(rows, ensure_ascii=False))
    time.sleep(2)
    return rows


def main():
    atlas = json.loads((ROOT / "web" / "data" / "atlas.json").read_text())["cities"]
    boxes = {c["key"]: json.loads((GRID / f"{c['key']}_r10.json").read_text())["bbox"] for c in atlas}
    cand = defaultdict(dict)  # norm name → {area: (distance, display, subtype)}
    for c in atlas:
        df, prov = ov.read_bbox("divisions", "division", tuple(boxes[c["key"]]), ["subtype", "names"], cache_dir=ROOT / "data" / "cache")
        pts = []
        for g, st, names in zip(df["geometry"], df["subtype"], df["names"]):
            if st in SUBTYPES and g is not None and names:
                p = g.representative_point()
                pts.append((p.x, p.y, st, {names.get("primary")} | {v for k, v in (names.get("common") or []) if k in LANGS}))
        wd = wikidata_places(boxes[c["key"]], ROOT / "data" / "cache" / "places" / f"{c['key']}_wikidata_places.json")
        pts += [(r["lon"], r["lat"], r["subtype"], set(r["labels"])) for r in wd]
        n = 0
        for px, py, st, labels in pts:
            for lab in filter(None, labels):
                t = " ".join(_norm(lab.replace("-", " ").replace("'", " ")).split())  # same tokens as glossary._words
                for s in SUFFIX:
                    t = t[: -len(s)] if t.endswith(s) else t
                if len(t) < 4:
                    continue
                # assign to the containing window with the nearest site centre
                inside = [a for a in atlas if boxes[a["key"]][0] <= px <= boxes[a["key"]][2] and boxes[a["key"]][1] <= py <= boxes[a["key"]][3]]
                if not inside:
                    continue
                best = min(inside, key=lambda a: km(py, px, a["lat"], a["lon"]))
                d = km(py, px, best["lat"], best["lon"])
                old = cand[t].get(best["key"])
                if old is None or d < old[0]:
                    cand[t][best["key"]] = (round(d, 2), lab, st)
                    n += 1
        print(c["key"], prov["rows_in_bbox"], "Overture divisions,", len(wd), "Wikidata places,", n, "names", flush=True)
    names, dropped = {}, []
    for t, by_area in sorted(cand.items()):
        if len(by_area) > 1:  # same name in two different areas → ambiguous
            dropped.append(t)
            continue
        (key, (d, lab, st)), = by_area.items()
        names[t] = {"area": key, "name": lab, "subtype": st, "km_from_site": d}
    out = {"source": f"Overture Maps divisions {ov.RELEASE} (ODbL; OpenStreetMap contributors) + Wikidata place items (CC0)", "rule": " ".join(__doc__.strip().splitlines()[2:9]),
           "n_names": len(names), "ambiguous_dropped": dropped, "names": names}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=0))
    print(OUT, len(names), "names,", len(dropped), "ambiguous dropped")


if __name__ == "__main__":
    main()

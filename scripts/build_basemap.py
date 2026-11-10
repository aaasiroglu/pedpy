"""Self-contained vector basemap for the web app (K-057).

claude.ai artifacts cannot load raster tiles from tile.openstreetmap.org (and OSM's tile policy discourages embedding),
so the basemap is shipped inside the page as simplified vectors:
* world: Natural Earth 1:110m admin-0 countries (public domain), geometry only, simplified
* per area window: Overture base/water polygons (ocean, sea, lakes, rivers; ODbL) and Overture transportation
  segments of class motorway/trunk/primary/secondary (ODbL), clipped to the window and simplified (~30 m)

    python scripts/build_basemap.py   → web/data/basemap.json
"""

import json
import urllib.request
from pathlib import Path

import shapely

from pedx.datalake import overture as ov

ROOT = Path(__file__).resolve().parents[1]
GRID = ROOT / "data" / "cache" / "citygrid"
OUT = ROOT / "web" / "data" / "basemap.json"
NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
ROADS = {"motorway", "trunk", "primary", "secondary"}
WATER = {"ocean", "lake", "reservoir", "river", "physical", "canal", "pond", "water"}


def rnd(geom, nd=5):
    return json.loads(json.dumps(shapely.geometry.mapping(geom)), parse_float=lambda x: round(float(x), nd))


def main():
    out = {"attribution": "Natural Earth (public domain) · Overture Maps Foundation, © OpenStreetMap contributors (ODbL)", "areas": {}}
    with urllib.request.urlopen(urllib.request.Request(NE, headers={"User-Agent": "pedx-research"}), timeout=120) as r:  # noqa: S310
        ne = json.load(r)
    out["world"] = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {}, "geometry": rnd(shapely.simplify(shapely.geometry.shape(f["geometry"]), 0.05), 3)} for f in ne["features"]]}
    keys = json.loads((ROOT / "web" / "data" / "atlas.json").read_text())
    for c in keys["cities"]:
        meta = json.loads((GRID / f"{c['key']}_r10.json").read_text())
        w, s, e, n = meta["bbox"]
        box = shapely.box(w, s, e, n)
        big = (e - w) > 0.5  # İstanbul 60 km window: coarser and without secondary roads
        tol = 0.0004 if not big else 0.0012
        road_classes = ROADS - ({"secondary"} if big else set())
        water, _ = ov.read_bbox("base", "water", (w, s, e, n), ["subtype", "class"], cache_dir=ROOT / "data" / "cache")
        polys = [shapely.intersection(g, box) for g, st in zip(water["geometry"], water["subtype"])
                 if g is not None and g.geom_type in ("Polygon", "MultiPolygon") and st in WATER]
        wgeom = shapely.simplify(shapely.union_all([p for p in polys if not p.is_empty]), tol) if polys else shapely.GeometryCollection()
        seg, _ = ov.read_bbox("transportation", "segment", (w, s, e, n), ["subtype", "class"], cache_dir=ROOT / "data" / "cache")
        lines = [shapely.intersection(g, box) for g, sub, cl in zip(seg["geometry"], seg["subtype"], seg["class"]) if sub == "road" and cl in road_classes]
        rgeom = shapely.simplify(shapely.line_merge(shapely.union_all([x for x in lines if not x.is_empty])), tol) if lines else shapely.GeometryCollection()
        out["areas"][c["key"]] = {"water": rnd(wgeom, 4) if not wgeom.is_empty else None, "roads": rnd(rgeom, 4) if not rgeom.is_empty else None}
        print(c["key"], len(polys), "water parts", len(lines), "road segments", flush=True)
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(OUT, round(OUT.stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    main()

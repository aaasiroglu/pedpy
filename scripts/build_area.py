"""Build the physical layer of one study area: boundary, buildings, urban blocks (K-071).

    python scripts/build_area.py caferaga        (area ids in data/areas.json)

Writes data/lake/<area>/{boundary.geojson, buildings.parquet, blocks.parquet} and registers both tables in
data/manifest.json. Inputs: OSM boundary (Nominatim), Overture buildings, land_use and transportation
(release pinned in pedx.datalake.overture.RELEASE), GHSL BUILT-H AGBH tile (height fallback).
"""

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pedx.datalake import overture as ov  # noqa: E402
from pedx.datalake.raster import fetch_ghsl_tile  # noqa: E402
from pedx.store import buildings as B  # noqa: E402
from pedx.store import manifest, schema, units  # noqa: E402

CACHE = ROOT / "data" / "cache"
UA = "pedx-research/0.1 (MSc thesis, Istanbul Technical University)"


def boundary(area, cfg, out):
    import geopandas as gpd
    f = out / "boundary.geojson"
    if not f.exists():
        url = f"https://nominatim.openstreetmap.org/lookup?osm_ids={cfg['osm']}&format=geojson&polygon_geojson=1"
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
            f.write_bytes(r.read())
    g = gpd.read_file(f)
    return g.geometry.union_all()


def main(area):
    import geopandas as gpd
    import shapely

    cfg = json.loads((ROOT / "data" / "areas.json").read_text())[area]
    out = ROOT / "data" / "lake" / area
    out.mkdir(parents=True, exist_ok=True)
    bnd = boundary(area, cfg, out)
    w, s, e, n = bnd.bounds
    pad = 0.002
    bbox = (w - pad, s - pad, e + pad, n + pad)
    raw, p_b = ov.read_bbox("buildings", "building", bbox, ["id", "height", "num_floors", "class", "subtype", "sources"], cache_dir=CACHE)
    lu, p_l = ov.read_bbox("base", "land_use", bbox, ["class", "subtype"], cache_dir=CACHE)
    seg, p_s = ov.read_bbox("transportation", "segment", bbox, ["subtype", "class"], cache_dir=CACHE)
    c = bnd.representative_point()
    tif = fetch_ghsl_tile("built_h_agbh_2018", c.y, c.x, CACHE / "ghsl")
    bld = B.standardise(raw, bnd, land_use=lu, ghsl_h_tif=tif)
    keep = ((seg["subtype"] == "road") & seg["class"].isin(units.BLOCK_ROADS)) | (seg["subtype"] == "rail")
    lines = [g for g in seg.loc[keep, "geometry"] if g is not None]
    blk = units.blocks_from_lines(lines, bnd)
    bld, blk = units.assign(bld, blk)
    for name, df in (("buildings", bld), ("blocks", blk)):
        probs = schema.validate(df, name)
        f = out / f"{name}.parquet"
        gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326").to_parquet(f, index=False)
        stats = {"problems": probs}
        if name == "buildings":
            stats.update(height_src=bld.height_src.value_counts().to_dict(), use_src=bld.use_src.value_counts().to_dict(),
                         use_class=bld.use_class.value_counts().to_dict(), data_src=bld.data_src.value_counts().to_dict(),
                         in_block=round(float(bld.block_id.notna().mean()), 4), footprint_m2=round(float(bld.footprint_m2.sum())))
        else:
            stats.update(median_area_m2=round(float(blk.area_m2.median())), empty_blocks=int((blk.n_buildings == 0).sum()))
        manifest.register(f"lake/{area}/{name}", f, name, schema.SCHEMAS[name].version, len(df), inputs=[
            {"source": "osm_boundary", "id": cfg["osm"], "via": "Nominatim", "licence": "ODbL 1.0"},
            {"source": "overture_buildings", "release": p_b["release"], "licence": "ODbL 1.0 (mixed sources, see data_src)"},
            {"source": "overture_land_use", "release": p_l["release"], "licence": "ODbL 1.0"},
            {"source": "overture_transportation", "release": p_s["release"], "licence": "ODbL 1.0"},
            {"source": "ghs_built_h_agbh_2018", "file": tif.name, "licence": "CC BY 4.0"}],
            params={"floor_height_m": B.FLOOR_H, "min_height_m": B.MIN_H, "ghsl_min_height_m": B.GHSL_MIN_H, "block_roads": sorted(units.BLOCK_ROADS), "bbox_pad_deg": pad}, stats=stats)
        print(area, name, len(df), "rows;", "schema ok" if not probs else probs)
    print("height_src", bld.height_src.value_counts(normalize=True).round(3).to_dict())
    print("use_src", bld.use_src.value_counts(normalize=True).round(3).to_dict())
    print("use_class", bld.use_class.value_counts().to_dict())
    print("in block", round(bld.block_id.notna().mean(), 3), "| blocks", len(blk), "median m2", round(blk.area_m2.median()))


if __name__ == "__main__":
    main(sys.argv[1])

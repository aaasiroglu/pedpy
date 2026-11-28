"""Fetch the global vulnerability and Overture layers for the Caferağa AOI → data/raw/sources/*.csv (+ provenance).

* Meta HRSL demographic COGs (CC BY 4.0): general, elderly 60+, children 0–5, youth 15–24, women 15–49
* Overture Maps (release pinned in pedx.datalake.overture.RELEASE): buildings (ODbL), places (CDLA-Permissive-2.0)

Only the AOI window / intersecting Parquet row groups are transferred. The Overture row-group
index is cached in data/cache (one-off, ≈ 10 s per theme).
"""

import json
import time
from pathlib import Path

import pandas as pd

from pedx.datalake import overture as ov
from pedx.datalake.vulnerability import hrsl_h3
from pedx.ingest.global_data import boundary_rings

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SRC = RAW / "sources"
CACHE = ROOT / "data" / "cache"
RES = 10

if __name__ == "__main__":
    b = boundary_rings(json.loads((RAW / "caferaga_boundary_overpass.json").read_text()))
    lats = [p[0] for r in b["outer"] for p in r]
    lons = [p[1] for r in b["outer"] for p in r]
    bbox = (min(lons), min(lats), max(lons), max(lats))
    prov = {}

    t = time.time()
    H, prov["hrsl"] = hrsl_h3(bbox, RES, mask=b)
    prov["hrsl"]["seconds"] = round(time.time() - t, 1)
    H.index.name = "cell"
    H.round(3).to_csv(SRC / "hrsl_h3r10_caferaga.csv")

    cells = sorted(H.index)
    t = time.time()
    bld, prov["overture_buildings"] = ov.read_bbox("buildings", "building", bbox, ["id", "height", "num_floors", "class", "sources"], cache_dir=CACHE)
    FB = ov.building_features(bld, cells, RES, mask=b)
    prov["overture_buildings"]["source_datasets"] = bld["sources"].map(ov._dataset).value_counts().to_dict()
    prov["overture_buildings"]["seconds"] = round(time.time() - t, 1)
    pl, prov["overture_places"] = ov.read_bbox("places", "place", bbox, ["id", "confidence", "basic_category", "taxonomy", "sources"], cache_dir=CACHE)
    FP = ov.place_features(pl, cells, RES, mask=b)
    prov["overture_places"]["source_datasets"] = pl["sources"].map(ov._dataset).value_counts().to_dict()
    F = FB.join(FP)
    F.index.name = "cell"
    F.round(4).to_csv(SRC / "overture_h3r10_caferaga.csv")
    (SRC / "layers_caferaga.json").write_text(json.dumps(prov, indent=1, default=str))
    print(H.sum().round(0).to_dict())
    print(F.describe().T[["count", "mean", "max"]].round(2).to_string())
    print(json.dumps(prov, default=str)[:800])

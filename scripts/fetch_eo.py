"""Fetch Earth-observation features for the Caferağa AOI → data/raw/sources/eo_h3r10_caferaga.csv (+ provenance JSON).

Landsat 8/9 C2 L2 LST (Jun–Sep 2023, cloud < 20 %), Sentinel-2 L2A NDVI/NDBI (least-cloudy Jun–Sep 2023
scene), Copernicus DEM GLO-30. Keyless, global; only the AOI window is transferred.
"""

import json
from pathlib import Path

import pandas as pd

from pedx.datalake.eo import dem_h3, landsat_lst_h3, sentinel2_indices_h3
from pedx.ingest.global_data import boundary_rings

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = RAW / "sources" / "eo_h3r10_caferaga.csv"

if __name__ == "__main__":
    b = boundary_rings(json.loads((RAW / "caferaga_boundary_overpass.json").read_text()))
    lats = [p[0] for r in b["outer"] for p in r]
    lons = [p[1] for r in b["outer"] for p in r]
    bbox = (min(lons), min(lats), max(lons), max(lats))
    lst, p_lst = landsat_lst_h3(bbox, "2023-06-01", "2023-09-30", 10, mask=b)
    s2, p_s2 = sentinel2_indices_h3(bbox, "2023-06-01", "2023-09-30", 10, mask=b)
    dem, p_dem = dem_h3(bbox, 10, mask=b)
    df = pd.concat([lst, s2, dem], axis=1)
    df["env_lst_anomaly_c"] = df["env_lst_mean_c"] - df["env_lst_mean_c"].median()
    df.index.name = "cell"
    df.round(4).to_csv(OUT)
    OUT.with_suffix(".json").write_text(json.dumps({"landsat": p_lst, "sentinel2": p_s2, "dem": p_dem}, indent=1))
    print(df.describe().loc[["count", "mean", "min", "max"]].round(3).to_string())
    print(json.dumps({"landsat_scenes": len(p_lst["scenes"]), "s2": p_s2, "dem": p_dem}))

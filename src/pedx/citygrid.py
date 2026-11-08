"""City grid: every raster and vector layer of the lake on one H3 grid over a city window (K-043).

Unit of global preparation. For a window of ``2·half_km`` around a point, all layers are read
once (windowed COG / Parquet row groups) and aggregated to H3 cells:

* Meta HRSL (people, 60+, 0–5)                      → population, vulnerability
* Overture buildings and places                       → footprint, floor-area proxy, POI richness
* Sentinel-2 L2A (least-cloudy summer scene)          → NDVI, NDBI
* Landsat 8/9 C2 L2 (least-cloudy summer scenes)      → LST mean, LST anomaly (vs city median)
* Copernicus DEM GLO-30                               → elevation, slope, relief
* PVGIS (city point), UNSD/OWID (country)             → PV yield Y, residential demand d

The grid is cached as one Parquet/CSV per city so that validation, the reference-class model and
the on-demand service can sample discs ("project sites") from it without re-reading the sources.
Population is HRSL everywhere here (one source for all cities → comparable); its known
over-count in commercial cores (G2: +65 % in Caferağa) is a level bias common to case and controls.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .params import PARAMS

__all__ = ["city_bbox", "city_grid", "disc_features", "EXTENSIVE", "INTENSIVE"]

DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "data" / "cache"

# disc aggregation rules: extensive quantities are summed, intensive ones averaged (population-weighted
# where a per-person reading is meant, else area-weighted = plain mean over equal-area H3 cells)
EXTENSIVE = ["vul_pop_hrsl", "vul_elderly60_n", "vul_children0_5_n", "ov_bld_n", "ov_bld_footprint_m2", "ov_gfa_m2",
             "ov_places_n", "energy_demand_res_kwh", "energy_pv_kwh",
             "ov_grid_assets_n", "ov_ev_chargers_n", "ov_generators_n", "ov_transit_stops_n", "ov_bike_n"]
INTENSIVE = ["env_ndvi_mean", "env_ndbi_mean", "env_lst_mean_c", "env_lst_anomaly_c", "env_elev_m", "env_slope_deg",
             "env_relief_m", "ov_floors_coverage", "ov_nonosm_share", "ov_places_categories",
             "env_wc_green_share", "env_wc_built_share", "env_wc_water_share", "env_wc_crop_share", "env_wc_bare_share"]


def city_bbox(lat: float, lon: float, half_km: float) -> Tuple[float, float, float, float]:
    dlat = half_km / 111.32
    dlon = half_km / (111.32 * math.cos(math.radians(lat)))
    return (lon - dlon, lat - dlat, lon + dlon, lat + dlat)


def city_grid(lat: float, lon: float, name: str, half_km: float = 8.0, resolution: int = 10,
              cache: Path = DEFAULT_CACHE, eo: bool = True, landsat_scenes: int = 4) -> Tuple[pd.DataFrame, dict]:
    """All layers on the H3 grid of a city window; cached as ``cache/citygrid/<name>_r<res>.csv``."""
    from .datalake import overture as ov
    from .datalake.vulnerability import hrsl_h3
    from .service import country_of, pv_yield, residential_kwh_per_capita

    out = cache / "citygrid" / f"{name}_r{resolution}.csv"
    meta = out.with_suffix(".json")
    bbox = city_bbox(lat, lon, half_km)
    if out.exists() and meta.exists():
        F, prov = pd.read_csv(out, index_col=0), json.loads(meta.read_text())
        if _addons(F, prov, bbox, resolution, cache):
            F.round(5).to_csv(out)
            meta.write_text(json.dumps(prov, default=str, indent=1))
        return F, prov
    prov: Dict[str, object] = {"name": name, "lat": lat, "lon": lon, "half_km": half_km, "resolution": resolution, "bbox": bbox}
    fails: Dict[str, str] = {}
    timing: Dict[str, float] = {}
    parts: List[pd.DataFrame] = []

    def step(key, fn):
        t = time.time()
        try:
            parts.append(fn())
        except Exception as exc:  # noqa: BLE001  (reported, never filled with synthetic values)
            fails[key] = f"{type(exc).__name__}: {exc}"[:300]
        timing[key] = round(time.time() - t, 1)

    def hrsl():
        H, prov["hrsl"] = hrsl_h3(bbox, resolution, layers=("general", "elderly_60_plus", "children_under_five"))
        return H

    step("hrsl", hrsl)
    cells = sorted(set(parts[0].index)) if parts else []

    def buildings():
        df, prov["overture_buildings"] = ov.read_bbox("buildings", "building", bbox, ["id", "height", "num_floors", "sources"], cache_dir=cache)
        return ov.building_features(df, sorted(set(cells) | set(_cells_of(df, resolution))), resolution)

    def places():
        df, prov["overture_places"] = ov.read_bbox("places", "place", bbox, ["id", "confidence", "basic_category", "taxonomy", "sources"], cache_dir=cache)
        P = ov.place_features(df, cells or _cells_of(df, resolution), resolution)
        return P[["ov_places_n", "ov_places_categories"]]

    step("overture_buildings", buildings)
    step("overture_places", places)
    if eo:
        from .datalake.eo import dem_h3, landsat_lst_h3, sentinel2_indices_h3

        def s2():
            S, prov["sentinel2"] = sentinel2_indices_h3(bbox, "2023-06-01", "2023-09-30", resolution, max_cloud=10.0)
            return S[["env_ndvi_mean", "env_ndbi_mean"]]

        def lst():
            L, prov["landsat"] = landsat_lst_h3(bbox, "2023-06-01", "2023-09-30", resolution, max_cloud=20.0, max_scenes=landsat_scenes)
            L["env_lst_anomaly_c"] = L["env_lst_mean_c"] - L["env_lst_mean_c"].median()
            return L[["env_lst_mean_c", "env_lst_anomaly_c"]]

        def dem():
            D, prov["dem"] = dem_h3(bbox, resolution)
            return D

        step("sentinel2", s2)
        step("landsat", lst)
        step("dem", dem)
    F = pd.concat(parts, axis=1) if parts else pd.DataFrame()
    F.index.name = "cell"
    for c in ("vul_pop_hrsl", "vul_elderly60_n", "vul_children0_5_n", "ov_bld_n", "ov_bld_footprint_m2", "ov_places_n"):
        if c in F:
            F[c] = F[c].fillna(0.0)

    def energy():
        c = country_of(lat, lon, cache)
        d = residential_kwh_per_capita(c, cache)
        y = pv_yield(lat, lon, cache)
        prov.update({"country": c, "demand": d, "pv_yield": y})
        u, eta = PARAMS["roof_utilization"]["value"], PARAMS["module_efficiency"]["value"]
        return pd.DataFrame({"energy_demand_res_kwh": F["vul_pop_hrsl"] * d["kwh_per_capita"],
                             "energy_pv_kwh": F["ov_bld_footprint_m2"] * u * eta * y["kwh_per_kwp"]}, index=F.index)

    t = time.time()
    try:
        F = F.join(energy())
    except Exception as exc:  # noqa: BLE001
        fails["energy"] = f"{type(exc).__name__}: {exc}"[:300]
    timing["energy"] = round(time.time() - t, 1)
    prov["failures"], prov["timing_s"] = fails, timing
    _addons(F, prov, bbox, resolution, cache)
    out.parent.mkdir(parents=True, exist_ok=True)
    F.round(5).to_csv(out)
    meta.write_text(json.dumps(prov, default=str, indent=1))
    return F, prov


def _addons(F: pd.DataFrame, prov: dict, bbox, resolution: int, cache: Path) -> bool:
    """Layers added after a grid was first cached (WorldCover, Overture infrastructure); in place."""
    from .datalake import overture as ov
    from .datalake.eo import worldcover_h3

    changed = False
    fails, timing = prov.setdefault("failures", {}), prov.setdefault("timing_s", {})
    if "env_wc_green_share" not in F and "worldcover" not in fails:
        t = time.time()
        try:
            W, prov["worldcover"] = worldcover_h3(bbox, resolution)
            for c in W:
                F[c] = W[c].reindex(F.index)
        except Exception as exc:  # noqa: BLE001
            fails["worldcover"] = f"{type(exc).__name__}: {exc}"[:300]
        timing["worldcover"], changed = round(time.time() - t, 1), True
    if "ov_grid_assets_n" not in F and "overture_infrastructure" not in fails:
        t = time.time()
        try:
            df, prov["overture_infrastructure"] = ov.read_bbox("base", "infrastructure", bbox, ["subtype", "class"], cache_dir=cache)
            I = ov.infrastructure_features(df, F.index, resolution)
            for c in I:
                F[c] = I[c]
        except Exception as exc:  # noqa: BLE001
            fails["overture_infrastructure"] = f"{type(exc).__name__}: {exc}"[:300]
        timing["overture_infrastructure"], changed = round(time.time() - t, 1), True
    if "energy_demand_res_kwh" not in F and "vul_pop_hrsl" in F:  # retry a failed country/PV lookup
        from .service import country_of, pv_yield, residential_kwh_per_capita

        lat, lon = (bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2
        try:
            c = country_of(lat, lon, cache)
            d, y = residential_kwh_per_capita(c, cache), pv_yield(lat, lon, cache)
            u, eta = PARAMS["roof_utilization"]["value"], PARAMS["module_efficiency"]["value"]
            F["energy_demand_res_kwh"] = F["vul_pop_hrsl"] * d["kwh_per_capita"]
            F["energy_pv_kwh"] = F["ov_bld_footprint_m2"] * u * eta * y["kwh_per_kwp"]
            prov.update({"country": c, "demand": d, "pv_yield": y})
            fails.pop("energy", None)
            changed = True
        except Exception as exc:  # noqa: BLE001
            fails["energy"] = f"{type(exc).__name__}: {exc}"[:300]
    return changed


def _cells_of(df: pd.DataFrame, resolution: int) -> List[str]:
    import shapely

    from .spatial.h3grid import assign_cells

    if df.empty:
        return []
    c = shapely.centroid(df["geometry"].to_numpy())
    return sorted(set(assign_cells(shapely.get_y(c), shapely.get_x(c), resolution)))


def disc_features(F: pd.DataFrame, centre: str, k: int = 2) -> Dict[str, float]:
    """Aggregate the k-ring disc around ``centre`` (a candidate project site) into one feature vector."""
    import h3

    D = F.reindex(sorted(h3.grid_disk(centre, k)))
    v: Dict[str, float] = {c: float(D[c].sum()) for c in EXTENSIVE if c in D}
    v.update({c: float(D[c].mean()) for c in INTENSIVE if c in D and D[c].notna().any()})
    P, A = v.get("vul_pop_hrsl", 0.0), v.get("ov_bld_footprint_m2", 0.0)
    area_ha = len(D) * h3.average_hexagon_area(h3.get_resolution(centre), unit="m^2") / 1e4
    v["pop_density_per_ha"] = P / area_ha
    v["footprint_coverage"] = A / (area_ha * 1e4)
    v["footprint_per_capita_m2"] = A / P if P > 0 else np.nan
    v["places_per_1000"] = 1000 * v.get("ov_places_n", 0.0) / P if P > 0 else np.nan
    v["elderly_share"] = v.get("vul_elderly60_n", 0.0) / P if P > 0 else np.nan
    v["children_share"] = v.get("vul_children0_5_n", 0.0) / P if P > 0 else np.nan
    v["gfa_per_capita_m2"] = v.get("ov_gfa_m2", np.nan) / P if P > 0 else np.nan
    km2 = area_ha / 100
    for c, nm in (("ov_transit_stops_n", "transit_per_km2"), ("ov_grid_assets_n", "grid_assets_per_km2"),
                  ("ov_ev_chargers_n", "ev_chargers_per_km2"), ("ov_bike_n", "bike_per_km2")):
        if c in v:
            v[nm] = v[c] / km2
    dem = v.get("energy_demand_res_kwh", 0.0)
    v["energy_balance"] = v.get("energy_pv_kwh", 0.0) / dem if dem > 0 else np.nan
    return v

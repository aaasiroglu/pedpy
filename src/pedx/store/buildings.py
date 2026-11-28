"""Building layer: Overture buildings → one standard table per area (schema 'buildings', K-071).

Every derived value carries its source column so that coverage can be audited:
  height_m   Overture height → Overture num_floors × FLOOR_H → GHSL BUILT-H AGBH (100 m pixel) → missing
  use_class  Overture class → Overture subtype → Overture land_use polygon under the centroid → 'unknown'
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

__all__ = ["FLOOR_H", "use_from_class", "use_from_subtype", "use_from_land_use", "standardise"]

FLOOR_H = 3.0  # m per storey (height ↔ floors); a parameter, reported in the manifest
MIN_H = 2.0  # m; Overture heights below this are data errors (falls back to floors / GHSL)
GHSL_MIN_H = 2.5  # m; a 100 m pixel average below one storey is not a usable building height

_CLASS = {
    "residential": ["apartments", "house", "residential", "detached", "semidetached_house", "terrace", "dormitory", "bungalow",
                    "static_caravan", "cabin", "houseboat", "farm", "stilt_house", "trullo", "nursing_home"],
    "education": ["school", "kindergarten", "university", "college", "library"],
    "sport": ["stadium", "sports_hall", "sports_centre", "grandstand", "pavilion", "riding_hall"],
    "civic": ["civic", "government", "public", "fire_station", "police", "townhall", "post_office", "military", "bunker"],
    "health": ["hospital", "clinic"],
    "religious": ["church", "mosque", "temple", "chapel", "cathedral", "synagogue", "shrine", "monastery", "religious", "presbytery", "wayside_shrine"],
    "commercial": ["commercial", "retail", "supermarket", "kiosk", "hotel", "service", "boathouse"],
    "office": ["office"],
    "industrial": ["industrial", "warehouse", "factory", "manufacture", "storage_tank", "silo", "digester", "water_tower"],
    "agricultural": ["barn", "farm_auxiliary", "greenhouse", "cowshed", "stable", "sty", "glasshouse", "agricultural"],
    "transport": ["train_station", "transportation", "parking", "garage", "garages", "carport", "hangar", "toll_booth"],
    "other": ["roof", "shed", "hut", "ruins", "construction", "toilets", "outbuilding", "allotment_house"],
}
CLASS_MAP = {c: u for u, cs in _CLASS.items() for c in cs}
SUBTYPE_MAP = {"agricultural": "agricultural", "civic": "civic", "commercial": "commercial", "education": "education",
               "entertainment": "commercial", "industrial": "industrial", "medical": "health", "military": "civic",
               "outbuilding": "other", "religious": "religious", "residential": "residential", "service": "other",
               "transportation": "transport"}
LAND_USE_CLASS = {"residential": "residential", "commercial": "commercial", "retail": "commercial", "industrial": "industrial",
                  "school": "education", "education": "education", "kindergarten": "education", "university": "education", "college": "education",
                  "hospital": "health", "clinic": "health", "religious": "religious", "pitch": "sport", "stadium": "sport",
                  "sports_centre": "sport", "track": "sport", "military": "civic", "railway": "transport", "garages": "transport",
                  "farmland": "agricultural", "farmyard": "agricultural", "greenhouse_horticulture": "agricultural"}
LAND_USE_SUBTYPE = {"residential": "residential", "education": "education", "medical": "health", "religious": "religious",
                    "agriculture": "agricultural", "horticulture": "agricultural", "military": "civic", "transportation": "transport"}


def use_from_class(c) -> Optional[str]:
    return CLASS_MAP.get(c) if isinstance(c, str) else None


def use_from_subtype(s) -> Optional[str]:
    return SUBTYPE_MAP.get(s) if isinstance(s, str) else None


def use_from_land_use(cls, sub) -> Optional[str]:
    return (LAND_USE_CLASS.get(cls) if isinstance(cls, str) else None) or (LAND_USE_SUBTYPE.get(sub) if isinstance(sub, str) else None)


def _first_dataset(src) -> str:
    try:
        return str(src[0]["dataset"]) if len(src) else "unknown"
    except Exception:
        return "unknown"


def standardise(raw: pd.DataFrame, boundary, land_use: Optional[pd.DataFrame] = None, ghsl_h_tif=None):
    """Overture rows (geometry decoded) → GeoDataFrame in schema 'buildings' (blocks are added by units.assign)."""
    import geopandas as gpd
    import h3
    import shapely

    g = gpd.GeoDataFrame(raw.drop(columns=[c for c in ("bbox",) if c in raw]), geometry="geometry", crs="EPSG:4326")
    g = g[g.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    g["geometry"] = shapely.make_valid(g.geometry.values)
    rep = g.geometry.representative_point()
    g = g[rep.within(boundary)].copy()
    rep = g.geometry.representative_point()
    utm = g.estimate_utm_crs()
    out = gpd.GeoDataFrame({"bld_id": g["id"].astype(str).values}, geometry=g.geometry.values, crs="EPSG:4326")
    out["footprint_m2"] = g.to_crs(utm).area.values
    h = pd.to_numeric(g["height"], errors="coerce").where(lambda v: v >= MIN_H).values
    fl = pd.to_numeric(g["num_floors"], errors="coerce").where(lambda v: v > 0).values
    height = np.where(np.isfinite(h), h, fl * FLOOR_H)
    src = np.where(np.isfinite(h), "overture_height", np.where(np.isfinite(fl), "overture_floors", "none")).astype(object)
    if ghsl_h_tif is not None:
        import rasterio
        need = ~np.isfinite(height)
        with rasterio.open(ghsl_h_tif) as r:
            vals = np.array([v[0] for v in r.sample(list(zip(rep.x.values[need], rep.y.values[need])))], dtype=float)
            if r.nodata is not None:
                vals[vals == r.nodata] = np.nan
        vals[vals < GHSL_MIN_H] = np.nan
        height[need] = vals
        src[need] = np.where(np.isfinite(vals), "ghsl_built_h", "none")
    out["height_m"] = height
    out["height_src"] = src
    out["floors"] = np.where(np.isfinite(fl), fl, np.maximum(1, np.round(height / FLOOR_H)))
    out["floor_area_m2"] = out["footprint_m2"] * out["floors"]
    u_cls = g["class"].map(use_from_class).values
    u_sub = g["subtype"].map(use_from_subtype).values
    use = np.where(pd.notna(u_cls), u_cls, u_sub).astype(object)
    use_src = np.where(pd.notna(u_cls), "overture_class", np.where(pd.notna(u_sub), "overture_subtype", "none")).astype(object)
    if land_use is not None and len(land_use):
        lu = gpd.GeoDataFrame(land_use[["class", "subtype"]].copy(), geometry=land_use["geometry"].values, crs="EPSG:4326")
        lu["u"] = [use_from_land_use(c, s) for c, s in zip(lu["class"], lu["subtype"])]
        lu = lu[lu["u"].notna() & lu.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
        pts = gpd.GeoDataFrame({"i": np.arange(len(g))}, geometry=rep.values, crs="EPSG:4326")
        j = gpd.sjoin(pts, lu[["u", "geometry"]], predicate="within", how="left").drop_duplicates("i").set_index("i")["u"]
        miss = pd.isna(use)
        use[miss] = j.reindex(np.arange(len(g))).values[miss]
        use_src[miss & pd.notna(use)] = "land_use"
    out["use_class"] = pd.Series(use).fillna("unknown").values
    out["use_src"] = use_src
    out["data_src"] = g["sources"].map(_first_dataset).values if "sources" in g else "unknown"
    for r in (9, 10, 11):
        out[f"h3_r{r}"] = [h3.latlng_to_cell(y, x, r) for x, y in zip(rep.x.values, rep.y.values)]
    out["block_id"] = None
    return out.reset_index(drop=True)

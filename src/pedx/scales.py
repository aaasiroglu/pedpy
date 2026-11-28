"""Multi-scale PED accounting: building → urban block → H3 r11 / r10 / r9 → drawn site (K-052).

Design principle: every spatial unit is an exact aggregation of buildings, so the district total is
identical at every scale and differences between scales are pure MAUP (Openshaw 1984), not
accounting artefacts.

1. Dasymetric population (Mennis 2003; Langford 2006): the population of each source zone (H3 r10
   cell from GHS-POP) is distributed to the buildings whose centroid lies in it, proportional to
   footprint area (floor counts are too sparse in OSM to use volume). Population of zones without
   buildings is reported as unallocated, never invented.
2. Building supply: PV = A·u·η·Y; demand = P_b·d (pedx.params). A building's own balance equals its
   zone's balance by construction (population ∝ footprint) — building-level *balance* is therefore
   not informative without building-level population, and is not reported; building-level *supply*
   (PV potential) is.
3. Urban blocks (Fleischmann et al. 2020, momepy): polygons enclosed by the street network
   (vehicular + pedestrian streets; footways, service roads, steps and paths excluded, as they
   subdivide blocks).
4. Any unit (block, H3 cell at any resolution, a drawn polygon) = sum over its buildings.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional, Sequence

import numpy as np
import pandas as pd

__all__ = ["dasymetric_buildings", "blocks_from_streets", "aggregate", "maup_summary", "BLOCK_STREETS"]

BLOCK_STREETS = {"motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential", "living_street",
                 "pedestrian", "busway", "primary_link", "secondary_link", "tertiary_link", "trunk_link"}


def dasymetric_buildings(bld: pd.DataFrame, zone_pop: pd.Series, zone_col: str = "cell") -> pd.DataFrame:
    """Population per building ∝ footprint within its source zone. Returns bld + ``pop`` and an attrs report."""
    b = bld.copy()
    tot = b.groupby(zone_col)["footprint_area_m2"].transform("sum")
    zp = b[zone_col].map(zone_pop).fillna(0.0)
    b["pop"] = np.where(tot > 0, zp * b["footprint_area_m2"] / tot, 0.0)
    allocated = float(b["pop"].sum())
    b.attrs["unallocated_population"] = float(zone_pop.sum()) - allocated
    b.attrs["zones_without_buildings"] = int((~zone_pop.index.isin(b[zone_col].unique()) & (zone_pop > 0)).sum())
    return b


def blocks_from_streets(payload: dict, boundary_outer: Sequence, allowed: Iterable[str] = BLOCK_STREETS):
    """Urban blocks = polygons enclosed by the street lines (shapely.polygonize), clipped to the boundary."""
    import geopandas as gpd
    import shapely

    allowed = set(allowed)
    lines = [shapely.LineString([(p["lon"], p["lat"]) for p in el["geometry"]]) for el in payload.get("elements", [])
             if el.get("type") == "way" and el.get("geometry") and len(el["geometry"]) >= 2 and el.get("tags", {}).get("highway") in allowed]
    merged = shapely.unary_union(lines)
    polys = list(shapely.get_parts(shapely.polygonize(shapely.get_parts(merged))))
    bnd = shapely.unary_union([shapely.Polygon([(lo, la) for la, lo in ring]) for ring in boundary_outer])
    g = gpd.GeoDataFrame(geometry=polys, crs="EPSG:4326")
    g = g[g.intersects(bnd)].copy()
    g["geometry"] = g.intersection(bnd)
    g = g[g.geometry.area > 0].reset_index(drop=True)
    g["block_id"] = [f"b{i:04d}" for i in range(len(g))]
    utm = g.estimate_utm_crs()
    g["area_m2"] = g.to_crs(utm).area
    return g


def aggregate(b: pd.DataFrame, unit_col: str, d_kwh: float, Y: float, u: float, eta: float) -> pd.DataFrame:
    """Sum buildings into units: population, footprint, PV, demand, balance."""
    g = b.groupby(unit_col).agg(n_buildings=("footprint_area_m2", "size"), footprint_m2=("footprint_area_m2", "sum"), pop=("pop", "sum"))
    g["pv_kwh"] = g["footprint_m2"] * u * eta * Y
    g["demand_kwh"] = g["pop"] * d_kwh
    g["balance"] = g["pv_kwh"] / g["demand_kwh"].where(g["demand_kwh"] > 0)
    return g


def _gini(x: np.ndarray) -> float:
    x = np.sort(x[np.isfinite(x) & (x >= 0)])
    if x.size == 0 or x.sum() == 0:
        return float("nan")
    n = x.size
    return float((2 * np.arange(1, n + 1) - n - 1) @ x / (n * x.sum()))


def maup_summary(units: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Per scale: n units, total balance (must be equal), share of units / population with B ≥ 1, quantiles, Gini."""
    rows = []
    for name, g0 in units.items():
        total = float(g0["pv_kwh"].sum() / g0["demand_kwh"].sum())  # over ALL units: identical across scales by construction
        g = g0[g0["pop"] > 0]
        B = g["balance"].to_numpy(float)
        rows.append({"scale": name, "n_units": int(len(g)), "median_area_ha": float(g["area_ha"].median()) if "area_ha" in g else np.nan,
                     "total_balance": total, "pv_share_in_unpopulated_units": float(g0.loc[g0["pop"] <= 0, "pv_kwh"].sum() / g0["pv_kwh"].sum()),
                     "share_units_B_ge_1": float((B >= 1).mean()), "share_pop_in_B_ge_1": float(g.loc[g["balance"] >= 1, "pop"].sum() / g["pop"].sum()),
                     "B_p10": float(np.nanpercentile(B, 10)), "B_median": float(np.nanmedian(B)), "B_p90": float(np.nanpercentile(B, 90)),
                     "gini_balance": _gini(B)})
    return pd.DataFrame(rows)

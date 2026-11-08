"""Urban-morphology features per H3 cell from OSM building polygons (momepy; Fleischmann, 2019).

Why these metrics (physics links, docs/13 §12):
* shared-wall ratio      – attached buildings lose less heat through walls (envelope area ↓)
* perimeter/area         – 2-D proxy of envelope compactness (heat loss, retrofit cost ∝ facade)
* compactness, elongation, rectangularity, corners – plan-form complexity (roof usability for PV)
* orientation deviation  – regularity of the street grid / roof azimuth spread (PV yield variance)

Requires the optional extra ``pip install pedx[morph]`` (momepy, geopandas, shapely).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["buildings_gdf", "morphology_features"]


def buildings_gdf(payload: dict, keep_ids=None):
    """GeoDataFrame (local UTM) of OSM building polygons from an Overpass ``out geom`` payload."""
    import geopandas as gpd
    from shapely.geometry import Polygon

    keep = None if keep_ids is None else set(keep_ids)
    rows, geoms = [], []
    for el in payload.get("elements", []):
        g = el.get("geometry")
        oid = f"way/{el.get('id')}"
        if el.get("type") != "way" or not g or len(g) < 4 or (keep is not None and oid not in keep):
            continue
        poly = Polygon([(p["lon"], p["lat"]) for p in g])
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty or poly.area == 0:
            continue
        rows.append(oid)
        geoms.append(poly)
    gdf = gpd.GeoDataFrame({"osm_id": rows}, geometry=geoms, crs=4326)
    return gdf.to_crs(gdf.estimate_utm_crs())


def _shared_wall_length(gdf, tolerance: float = 0.3) -> np.ndarray:
    """Length of each building's boundary that lies within ``tolerance`` metres of a neighbour.

    Known bias: up to ``2 * tolerance`` extra length at each end of a shared wall
    (corner overlap of the buffer); bounded and tested.
    """
    geoms = gdf.geometry.values
    tree = gdf.sindex
    out = np.zeros(len(gdf))
    for i, gi in enumerate(geoms):
        cand = tree.query(gi.buffer(tolerance), predicate="intersects")
        cand = cand[cand != i]
        if cand.size == 0:
            continue
        neigh = gdf.geometry.iloc[cand].buffer(tolerance).union_all()
        out[i] = gi.boundary.intersection(neigh).length
    return out


def morphology_features(gdf, cell_of: pd.Series) -> pd.DataFrame:
    """Per-cell morphometrics; ``cell_of`` maps osm_id → H3 cell."""
    import momepy

    g = gdf.copy()
    g["cell"] = g["osm_id"].map(cell_of)
    g = g[g["cell"].notna()]
    perim = g.length.to_numpy()
    area = g.area.to_numpy()
    shared = _shared_wall_length(g)
    m = pd.DataFrame({
        "cell": g["cell"].to_numpy(),
        "perimeter": perim,
        "area": area,
        "shared": np.minimum(shared, perim),
        "compactness": np.asarray(momepy.circular_compactness(g.geometry)),
        "elongation": np.asarray(momepy.elongation(g.geometry)),
        "rectangularity": np.asarray(momepy.rectangularity(g.geometry)),
        "corners": np.asarray(momepy.corners(g.geometry)),
        "orientation": np.asarray(momepy.orientation(g.geometry)),
    })
    grp = m.groupby("cell")
    out = pd.DataFrame({
        "morph_shared_wall_ratio": grp["shared"].sum() / grp["perimeter"].sum(),
        "morph_perimeter_area_ratio": grp["perimeter"].sum() / grp["area"].sum(),
        "morph_compactness_mean": grp["compactness"].mean(),
        "morph_elongation_mean": grp["elongation"].mean(),
        "morph_rectangularity_mean": grp["rectangularity"].mean(),
        "morph_corners_mean": grp["corners"].mean(),
        "morph_orientation_std": grp["orientation"].std(ddof=0),
    })
    return out

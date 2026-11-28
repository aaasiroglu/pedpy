"""Spatial units: urban blocks from street lines and the area boundary (schema 'blocks', K-071).

A block is a polygon enclosed by streets (and rail lines) and the area boundary. Footways, steps and service
roads do not split blocks. Block ids are assigned in a fixed spatial order so that a rebuild from the same
inputs gives the same ids.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["BLOCK_ROADS", "blocks_from_lines", "assign"]

BLOCK_ROADS = {"motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential", "living_street",
               "pedestrian", "busway", "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link"}


def blocks_from_lines(lines, boundary, min_area_m2: float = 50.0):
    """Polygonise ``lines`` + the boundary ring; keep pieces inside ``boundary``."""
    import geopandas as gpd
    import shapely

    rings = [boundary.exterior] if boundary.geom_type == "Polygon" else [p.exterior for p in boundary.geoms]
    net = shapely.union_all([*lines, *rings])
    polys = list(shapely.get_parts(shapely.polygonize(shapely.get_parts(net))))
    g = gpd.GeoDataFrame(geometry=polys, crs="EPSG:4326")
    g = g[g.geometry.representative_point().within(boundary)].copy()
    utm = g.estimate_utm_crs()
    g["area_m2"] = g.to_crs(utm).area.values
    g = g[g["area_m2"] >= min_area_m2].copy()
    c = g.geometry.representative_point()
    g = g.assign(_y=np.round(c.y.values, 6), _x=np.round(c.x.values, 6)).sort_values(["_y", "_x"], ascending=[False, True])
    g["block_id"] = [f"blk-{i:05d}" for i in range(len(g))]
    return g.drop(columns=["_y", "_x"]).reset_index(drop=True)[["block_id", "area_m2", "geometry"]]


def assign(buildings, blocks):
    """Set buildings.block_id (block containing the representative point); add n_buildings and footprint_m2 to blocks."""
    import geopandas as gpd

    pts = gpd.GeoDataFrame({"i": np.arange(len(buildings))}, geometry=buildings.geometry.representative_point().values, crs="EPSG:4326")
    j = gpd.sjoin(pts, blocks[["block_id", "geometry"]], predicate="within", how="left").drop_duplicates("i").set_index("i")["block_id"]
    b = buildings.copy()
    b["block_id"] = j.reindex(np.arange(len(b))).values
    agg = b.groupby("block_id").agg(n_buildings=("bld_id", "size"), footprint_m2=("footprint_m2", "sum"))
    k = blocks.copy()
    k["n_buildings"] = k["block_id"].map(agg["n_buildings"]).fillna(0).astype(int)
    k["footprint_m2"] = k["block_id"].map(agg["footprint_m2"]).fillna(0.0)
    return b, k[["block_id", "area_m2", "n_buildings", "footprint_m2", "geometry"]]

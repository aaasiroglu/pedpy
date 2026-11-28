"""Generic raster → H3 zonal engine and GHSL tile connector.

``zonal_h3`` reads only the window covering the AOI (no global download into memory), assigns
each pixel centre to an H3 cell (optionally inside a polygon mask) and aggregates with ``sum``
(extensive quantities: people, m², m³) or ``mean`` (intensive: height). This is the single
code path by which any global raster enters the hex feature store.
"""

from __future__ import annotations

import io
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from ..ingest.global_data import ghs_pop_tile_id, points_in_polygon

__all__ = ["GHSL_PRODUCTS", "ghsl_tile_path", "ghsl_tile_url", "fetch_ghsl_tile", "zonal_h3"]

GHSL_BASE = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL"
GHSL_PRODUCTS = {
    "pop_2020": ("GHS_POP_GLOBE_R2023A", "GHS_POP_E2020_GLOBE_R2023A_4326_3ss"),
    "built_s_2020": ("GHS_BUILT_S_GLOBE_R2023A", "GHS_BUILT_S_E2020_GLOBE_R2023A_4326_3ss"),
    "built_s_nres_2020": ("GHS_BUILT_S_GLOBE_R2023A", "GHS_BUILT_S_NRES_E2020_GLOBE_R2023A_4326_3ss"),
    "built_v_2020": ("GHS_BUILT_V_GLOBE_R2023A", "GHS_BUILT_V_E2020_GLOBE_R2023A_4326_3ss"),
    "built_v_nres_2020": ("GHS_BUILT_V_GLOBE_R2023A", "GHS_BUILT_V_NRES_E2020_GLOBE_R2023A_4326_3ss"),
    "built_h_agbh_2018": ("GHS_BUILT_H_GLOBE_R2023A", "GHS_BUILT_H_AGBH_E2018_GLOBE_R2023A_4326_3ss"),
    # multi-temporal built-up surface: epoch of first urbanisation (vulnerability proxy, K-039)
    "built_s_1975": ("GHS_BUILT_S_GLOBE_R2023A", "GHS_BUILT_S_E1975_GLOBE_R2023A_4326_3ss"),
    "built_s_1990": ("GHS_BUILT_S_GLOBE_R2023A", "GHS_BUILT_S_E1990_GLOBE_R2023A_4326_3ss"),
    "built_s_2000": ("GHS_BUILT_S_GLOBE_R2023A", "GHS_BUILT_S_E2000_GLOBE_R2023A_4326_3ss"),
}


def ghsl_tile_url(product: str, lat: float, lon: float) -> str:
    coll, name = GHSL_PRODUCTS[product]
    return f"{GHSL_BASE}/{coll}/{name}/V1-0/tiles/{name}_V1_0_{ghs_pop_tile_id(lat, lon)}.zip"


def ghsl_tile_path(product: str, lat: float, lon: float, root: Path) -> Path:
    _, name = GHSL_PRODUCTS[product]
    return Path(root) / f"{name}_V1_0_{ghs_pop_tile_id(lat, lon)}.tif"


def fetch_ghsl_tile(product: str, lat: float, lon: float, root: Path) -> Path:
    """Download and unzip the WGS84 3″ tile containing (lat, lon) if not cached."""
    out = ghsl_tile_path(product, lat, lon, root)
    if not out.exists():
        with urllib.request.urlopen(ghsl_tile_url(product, lat, lon), timeout=1800) as r:  # noqa: S310
            zipfile.ZipFile(io.BytesIO(r.read())).extractall(Path(root))
    return out


def zonal_h3(tif_path: Path, bbox: Tuple[float, float, float, float], resolution: int, stat: str = "sum",
             mask: Optional[Dict[str, Sequence]] = None, name: str = "value") -> pd.Series:
    """Aggregate raster pixels into H3 cells by pixel centre (``stat``: sum | mean)."""
    import rasterio
    from rasterio.windows import from_bounds

    from ..spatial.h3grid import assign_cells

    if stat not in ("sum", "mean"):
        raise ValueError("stat must be 'sum' or 'mean'")
    s, w, n, e = bbox
    with rasterio.open(tif_path) as src:
        win = from_bounds(w, s, e, n, transform=src.transform).round_offsets().round_lengths()
        arr = src.read(1, window=win).astype(float)
        nodata = src.nodata
        tr = src.window_transform(win)
    valid = np.isfinite(arr) & (arr >= 0)
    if nodata is not None:
        valid &= arr != nodata
    rows, cols = np.nonzero(valid)
    if rows.size == 0:
        return pd.Series(dtype=float, name=name)
    xs = tr.c + (cols + 0.5) * tr.a
    ys = tr.f + (rows + 0.5) * tr.e
    vals = arr[rows, cols]
    if mask is not None:
        keep = points_in_polygon(ys, xs, mask["outer"], mask.get("inner", ()))
        xs, ys, vals = xs[keep], ys[keep], vals[keep]
    cells = assign_cells(ys, xs, resolution)
    g = pd.Series(vals, index=cells).groupby(level=0)
    return (g.sum() if stat == "sum" else g.mean()).rename(name)

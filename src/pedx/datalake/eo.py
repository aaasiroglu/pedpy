"""Earth-observation connectors (global, open, keyless): Landsat C2 L2 surface temperature,
Sentinel-2 L2A indices and Copernicus DEM GLO-30 — aggregated to H3 (K-036).

Method follows the open SUHII-mapping logic (Landsat C2 L2 ST band, QA cloud masking, warm-season
mean; DEM to control elevation; OSM for land use) — re-implemented from the published product
specifications, not copied (the reference tool is AGPL-3.0).

Sources
* Landsat C2 L2 (USGS) via Microsoft Planetary Computer STAC (anonymous SAS token). LST [°C] =
  DN·0.00341802 + 149.0 − 273.15 (USGS C2 L2 ST scale factors). QA_PIXEL bits 1–4 (dilated cloud,
  cirrus, cloud, cloud shadow) masked.
* Sentinel-2 L2A via Element 84 Earth Search STAC (public COGs). NDVI = (B08−B04)/(B08+B04),
  NDBI = (B11−B08)/(B11+B08); SCL classes 3, 8, 9, 10 (shadow, cloud medium/high, cirrus) masked.
* Copernicus DEM GLO-30 (public COG on AWS) → elevation, slope.

GDAL reads remote COGs by HTTP range requests (only the AOI window is transferred).
"""

from __future__ import annotations

import json
import math
import os
import urllib.request
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

__all__ = ["stac_search", "landsat_lst_h3", "sentinel2_indices_h3", "dem_h3", "zonal_array_h3"]

PC_STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
PC_TOKEN = "https://planetarycomputer.microsoft.com/api/sas/v1/token/{collection}"
ES_STAC = "https://earth-search.aws.element84.com/v1/search"
COP_DEM = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{ns}{lat:02d}_00_{ew}{lon:03d}_00_DEM/Copernicus_DSM_COG_10_{ns}{lat:02d}_00_{ew}{lon:03d}_00_DEM.tif"

BBox = Tuple[float, float, float, float]  # (west, south, east, north) — STAC order


def _gdal_env() -> None:
    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    ca = "/root/.ccr/ca-bundle.crt"
    if os.path.exists(ca):
        os.environ.setdefault("CURL_CA_BUNDLE", ca)
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        os.environ.setdefault("GDAL_HTTP_PROXY", proxy.replace("http://", ""))


def stac_search(url: str, collections: Sequence[str], bbox: BBox, start: str, end: str,
                max_cloud: Optional[float] = None, limit: int = 100) -> List[dict]:
    body = {"collections": list(collections), "bbox": list(bbox), "limit": limit,
            "datetime": f"{start}T00:00:00Z/{end}T23:59:59Z"}
    if max_cloud is not None:
        body["query"] = {"eo:cloud_cover": {"lt": max_cloud}}
    rq = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(rq, timeout=120) as r:  # noqa: S310
        return json.load(r)["features"]


def _read_window(href: str, bbox: BBox):
    import rasterio
    from rasterio.warp import transform_bounds
    from rasterio.windows import from_bounds

    _gdal_env()
    with rasterio.open(href) as src:
        b = transform_bounds("EPSG:4326", src.crs, *bbox) if src.crs.to_epsg() != 4326 else bbox
        win = from_bounds(*b, transform=src.transform).round_offsets().round_lengths()
        return src.read(1, window=win, boundless=True).astype(float), src.window_transform(win), src.crs


def zonal_array_h3(arr: np.ndarray, transform, crs, resolution: int, stat: str = "mean",
                   mask: Optional[Dict[str, Sequence]] = None, name: str = "value") -> pd.Series:
    """Aggregate a georeferenced array (any CRS) to H3 by pixel centre; NaN pixels ignored."""
    from rasterio.warp import transform as warp

    from ..ingest.global_data import points_in_polygon
    from ..spatial.h3grid import assign_cells

    rows, cols = np.nonzero(np.isfinite(arr))
    if rows.size == 0:
        return pd.Series(dtype=float, name=name)
    xs = transform.c + (cols + 0.5) * transform.a
    ys = transform.f + (rows + 0.5) * transform.e
    if crs.to_epsg() != 4326:
        xs, ys = warp(crs, "EPSG:4326", xs, ys)
    xs, ys = np.asarray(xs), np.asarray(ys)
    vals = arr[rows, cols]
    if mask is not None:
        keep = points_in_polygon(ys, xs, mask["outer"], mask.get("inner", ()))
        xs, ys, vals = xs[keep], ys[keep], vals[keep]
    g = pd.Series(vals, index=assign_cells(ys, xs, resolution)).groupby(level=0)
    agg = {"mean": g.mean, "sum": g.sum, "std": lambda: g.std(ddof=0)}[stat]()
    return agg.rename(name)


def landsat_lst_h3(bbox: BBox, start: str, end: str, resolution: int, mask=None, max_cloud: float = 20.0) -> Tuple[pd.Series, dict]:
    """Warm-season mean LST [°C] per H3 cell from Landsat 8/9 C2 L2 (Planetary Computer)."""
    items = [f for f in stac_search(PC_STAC, ["landsat-c2-l2"], bbox, start, end, max_cloud)
             if f["properties"].get("platform") in ("landsat-8", "landsat-9")]
    with urllib.request.urlopen(PC_TOKEN.format(collection="landsat-c2-l2"), timeout=60) as r:  # noqa: S310
        token = json.load(r)["token"]
    stack, used, ref = [], [], None
    for f in items:
        lst, tr, crs = _read_window(f["assets"]["lwir11"]["href"] + "?" + token, bbox)
        qa, _, _ = _read_window(f["assets"]["qa_pixel"]["href"] + "?" + token, bbox)
        if ref is None:
            ref = (tr, crs, lst.shape)
        if lst.shape != ref[2] or crs != ref[1]:
            continue  # different UTM zone / footprint: skip to keep one grid
        bad = (qa.astype(np.int64) & 0b11110) > 0
        valid = (~bad) & (lst > 0)
        if valid.mean() < 0.3:
            continue
        stack.append(np.where(valid, lst * 0.00341802 + 149.0 - 273.15, np.nan))
        used.append(f["id"])
    if not stack:
        raise RuntimeError("no usable Landsat scene")
    mean = np.nanmean(np.stack(stack), axis=0)
    s = pd.concat([zonal_array_h3(mean, ref[0], ref[1], resolution, "mean", mask, "env_lst_mean_c"),
                   zonal_array_h3(mean, ref[0], ref[1], resolution, "std", mask, "env_lst_std_c")], axis=1)
    return s, {"scenes": used, "n_candidates": len(items), "window": f"{start}/{end}", "max_cloud": max_cloud}


def sentinel2_indices_h3(bbox: BBox, start: str, end: str, resolution: int, mask=None, max_cloud: float = 5.0) -> Tuple[pd.DataFrame, dict]:
    """NDVI and NDBI per H3 cell from the least-cloudy Sentinel-2 L2A scene (Earth Search)."""
    items = sorted(stac_search(ES_STAC, ["sentinel-2-l2a"], bbox, start, end, max_cloud), key=lambda f: f["properties"]["eo:cloud_cover"])
    if not items:
        raise RuntimeError("no Sentinel-2 scene")
    f = items[0]

    def band(key):
        a = f["assets"][key]
        arr, tr, crs = _read_window(a["href"], bbox)
        rb = (a.get("raster:bands") or [{}])[0]
        # Earth Search harmonises processing baseline ≥ 04.00 itself (earthsearch:boa_offset_applied = True);
        # the asset metadata still lists offset −0.1, which must then NOT be applied again.
        offset = 0.0 if f["properties"].get("earthsearch:boa_offset_applied") else rb.get("offset", 0.0)
        arr = arr * rb.get("scale", 1.0) + offset
        return np.clip(arr, 0.0, 1.0), tr, crs  # physical reflectance range; offset can push dark pixels < 0

    red, tr10, crs = band("red")
    nir, _, _ = band("nir")
    swir, tr20, _ = band("swir16")
    scl, _, _ = _read_window(f["assets"]["scl"]["href"], bbox)
    h20, w20 = min(swir.shape[0], scl.shape[0]), min(swir.shape[1], scl.shape[1])
    swir, cloud20 = swir[:h20, :w20], np.isin(scl[:h20, :w20], [3, 8, 9, 10])
    h10, w10 = min(red.shape[0], nir.shape[0], 2 * h20), min(red.shape[1], nir.shape[1], 2 * w20)
    red, nir = red[:h10, :w10], nir[:h10, :w10]
    cloud10 = np.repeat(np.repeat(cloud20, 2, 0), 2, 1)[:h10, :w10]
    nir20 = nir[::2, ::2][:h20, :w20]
    h20, w20 = nir20.shape
    swir, cloud20 = swir[:h20, :w20], cloud20[:h20, :w20]
    with np.errstate(divide="ignore", invalid="ignore"):
        ndbi = np.where(~cloud20 & ((swir + nir20) > 0.02), (swir - nir20) / (swir + nir20), np.nan)
        ndvi = np.where(~cloud10 & ((nir + red) > 0.02), (nir - red) / (nir + red), np.nan)
    out = pd.DataFrame({
        "env_ndvi_mean": zonal_array_h3(ndvi, tr10, crs, resolution, "mean", mask),
        "env_ndvi_std": zonal_array_h3(ndvi, tr10, crs, resolution, "std", mask),
        "env_ndbi_mean": zonal_array_h3(ndbi, tr20, crs, resolution, "mean", mask),
    })
    return out, {"scene": f["id"], "cloud_cover": f["properties"]["eo:cloud_cover"], "date": f["properties"]["datetime"]}


def dem_h3(bbox: BBox, resolution: int, mask=None) -> Tuple[pd.DataFrame, dict]:
    """Elevation [m] and slope [°] per H3 cell from Copernicus DEM GLO-30 (single 1°×1° tile)."""
    w, s, e, n = bbox
    lat, lon = math.floor(s), math.floor(w)
    url = COP_DEM.format(ns="N" if lat >= 0 else "S", lat=abs(lat), ew="E" if lon >= 0 else "W", lon=abs(lon))
    z, tr, crs = _read_window(url, bbox)
    lat_c = (s + n) / 2
    dy = abs(tr.e) * 111_320.0
    dx = abs(tr.a) * 111_320.0 * math.cos(math.radians(lat_c))
    gy, gx = np.gradient(z, dy, dx)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    out = pd.DataFrame({
        "env_elev_m": zonal_array_h3(z, tr, crs, resolution, "mean", mask),
        "env_slope_deg": zonal_array_h3(slope, tr, crs, resolution, "mean", mask),
        "env_relief_m": zonal_array_h3(z, tr, crs, resolution, "std", mask),
    })
    return out, {"tile": url.rsplit("/", 1)[-1]}

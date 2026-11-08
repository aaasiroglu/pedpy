"""Overture Maps connector: read only the AOI rows of the global GeoParquet release (K-038).

Overture Maps Foundation publishes the world as GeoParquet on S3 (``s3://overturemaps-us-west-2``,
anonymous). Each file is split into row groups whose ``bbox.*`` column statistics give a tight
extent. We index those statistics once per release and theme (≈ 84 k row groups for buildings,
built in seconds from the file footers) and then read only the row groups that intersect the AOI.
This is the same "global catalogue, fetch the window on demand" pattern as the raster connectors.

Licences (docs.overturemaps.org/attribution): buildings, transportation, base, divisions → ODbL 1.0
(they contain OpenStreetMap); places → CDLA-Permissive-2.0. Attribution: "© OpenStreetMap
contributors, Overture Maps Foundation".
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

import numpy as np
import pandas as pd

__all__ = ["RELEASE", "rowgroup_index", "read_bbox", "building_features", "place_features"]

BUCKET = "overturemaps-us-west-2"
RELEASE = "2026-10-21.0"  # pinned for reproducibility; provenance records it
BBox = Tuple[float, float, float, float]  # (west, south, east, north)


def _fs():
    import pyarrow.fs as pafs

    kw = {"anonymous": True, "region": "us-west-2"}
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        p = urlparse(proxy)
        kw["proxy_options"] = {"scheme": p.scheme, "host": p.hostname, "port": p.port}
    ca = "/root/.ccr/ca-bundle.crt"
    if os.path.exists(ca):
        kw["tls_ca_file_path"] = ca
    return pafs.S3FileSystem(**kw)


def _prefix(theme: str, typ: str, release: str) -> str:
    return f"{BUCKET}/release/{release}/theme={theme}/type={typ}/"


def rowgroup_index(theme: str, typ: str, release: str = RELEASE, cache_dir: Optional[Path] = None) -> pd.DataFrame:
    """(file, row_group, xmin, ymin, xmax, ymax, rows) for every row group of a theme/type."""
    import pyarrow.fs as pafs
    import pyarrow.parquet as pq

    cache = Path(cache_dir) / f"overture_{release}_{theme}_{typ}_rg.json" if cache_dir else None
    if cache is not None and cache.exists():
        return pd.DataFrame(json.loads(cache.read_text()), columns=["file", "rg", "xmin", "ymin", "xmax", "ymax", "rows"])
    fs = _fs()
    files = [i.path for i in fs.get_file_info(pafs.FileSelector(_prefix(theme, typ, release))) if i.path.endswith(".parquet")]

    def one(path: str) -> List[tuple]:
        md = pq.ParquetFile(fs.open_input_file(path)).metadata
        ix = {md.schema.column(i).path: i for i in range(md.num_columns)}
        out = []
        for r in range(md.num_row_groups):
            rg = md.row_group(r)
            st = {k: rg.column(ix[f"bbox.{k}"]).statistics for k in ("xmin", "ymin", "xmax", "ymax")}
            out.append((path.rsplit("/", 1)[-1], r, st["xmin"].min, st["ymin"].min, st["xmax"].max, st["ymax"].max, rg.num_rows))
        return out

    with ThreadPoolExecutor(32) as ex:
        rows = [x for part in ex.map(one, files) for x in part]
    if cache is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(rows))
    return pd.DataFrame(rows, columns=["file", "rg", "xmin", "ymin", "xmax", "ymax", "rows"])


def read_bbox(theme: str, typ: str, bbox: BBox, columns: Sequence[str], release: str = RELEASE,
              cache_dir: Optional[Path] = None) -> Tuple[pd.DataFrame, dict]:
    """Rows of ``theme/type`` whose bbox intersects ``bbox``; ``geometry`` decoded to shapely."""
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    import shapely

    w, s, e, n = bbox
    idx = rowgroup_index(theme, typ, release, cache_dir)
    hit = idx[(idx.xmin <= e) & (idx.xmax >= w) & (idx.ymin <= n) & (idx.ymax >= s)]
    fs = _fs()
    cols = list(dict.fromkeys([*columns, "geometry", "bbox"]))
    tables = []
    for f, g in hit.groupby("file"):
        t = pq.ParquetFile(fs.open_input_file(_prefix(theme, typ, release) + f)).read_row_groups(g["rg"].tolist(), columns=cols)
        b = t.column("bbox")
        keep = pc.and_(pc.and_(pc.less_equal(pc.struct_field(b, "xmin"), e), pc.greater_equal(pc.struct_field(b, "xmax"), w)),
                       pc.and_(pc.less_equal(pc.struct_field(b, "ymin"), n), pc.greater_equal(pc.struct_field(b, "ymax"), s)))
        tables.append(t.filter(keep))
    prov = {"release": release, "theme": theme, "type": typ, "row_groups_read": int(len(hit)),
            "row_groups_total": int(len(idx)), "rows_scanned": int(hit["rows"].sum())}
    if not tables:
        return pd.DataFrame(columns=cols), prov
    t = pa.concat_tables(tables)
    df = t.drop(["geometry"]).to_pandas()
    df["geometry"] = shapely.from_wkb(t.column("geometry").to_numpy(zero_copy_only=False))
    prov["rows_in_bbox"] = int(len(df))
    return df, prov


def _dataset(sources) -> str:
    try:
        return str(sources[0]["dataset"])
    except Exception:  # noqa: BLE001
        return "unknown"


def _first(seq):
    return seq[0] if seq is not None and len(seq) else None


def building_features(df: pd.DataFrame, cells: Iterable[str], resolution: int, mask=None,
                      storey_m: float = 3.0) -> pd.DataFrame:
    """Per-cell Overture building stock: count, height/floor coverage, mean height, gross floor area.

    Footprint area is computed in a local equal-distance projection; a building belongs to the cell of
    its centroid. Gross floor area uses ``num_floors`` when present, else ``height / storey_m``,
    else nothing (coverage columns report how much is observed rather than imputed).
    """
    import shapely

    from ..ingest.global_data import points_in_polygon
    from ..spatial.h3grid import assign_cells

    cells = list(cells)
    if df.empty:
        return pd.DataFrame(index=pd.Index(cells, name="cell"))
    geom = df["geometry"].to_numpy()
    cen = shapely.centroid(geom)
    lon, lat = shapely.get_x(cen), shapely.get_y(cen)
    lat0 = np.radians(np.nanmean(lat))
    # local metric coordinates (equirectangular about the AOI centre; < 0.1 % error at district scale)
    k = np.pi / 180 * 6_371_008.8
    to_m = lambda xy: np.c_[xy[:, 0] * k * np.cos(lat0), xy[:, 1] * k]  # noqa: E731
    area = shapely.area(shapely.transform(geom, to_m))
    d = pd.DataFrame({"lat": lat, "lon": lon, "area": area,
                      "height": pd.to_numeric(df.get("height"), errors="coerce"),
                      "floors": pd.to_numeric(df.get("num_floors"), errors="coerce"),
                      "ml": [_dataset(x) not in ("OpenStreetMap",) for x in df.get("sources", [None] * len(df))]})
    if mask is not None:
        d = d[points_in_polygon(d["lat"].to_numpy(), d["lon"].to_numpy(), mask["outer"], mask.get("inner", ()))]
    d["cell"] = assign_cells(d["lat"].to_numpy(), d["lon"].to_numpy(), resolution)
    d["fl_est"] = d["floors"].where(d["floors"].notna(), (d["height"] / storey_m).round().clip(lower=1))
    d["gfa"] = d["area"] * d["fl_est"]
    g = d.groupby("cell")
    out = pd.DataFrame(index=pd.Index(cells, name="cell"))
    out["ov_bld_n"] = g.size().reindex(cells).fillna(0)
    out["ov_bld_footprint_m2"] = g["area"].sum().reindex(cells).fillna(0)
    out["ov_height_coverage"] = g["height"].apply(lambda s: float(s.notna().mean())).reindex(cells)
    out["ov_floors_coverage"] = g["floors"].apply(lambda s: float(s.notna().mean())).reindex(cells)
    hw = d.dropna(subset=["height"]).groupby("cell").apply(lambda x: float(np.average(x["height"], weights=x["area"])), include_groups=False)
    out["ov_height_mean_m"] = hw.reindex(cells)
    out["ov_gfa_m2"] = g["gfa"].sum(min_count=1).reindex(cells)
    out["ov_nonosm_share"] = g["ml"].mean().reindex(cells)
    return out


def place_features(df: pd.DataFrame, cells: Iterable[str], resolution: int, mask=None,
                   min_confidence: float = 0.5) -> pd.DataFrame:
    """Per-cell Overture places (confidence ≥ ``min_confidence``): count, category richness, top-level mix.

    Schema ≥ 2025: ``basic_category`` (≈ 280 classes) and ``taxonomy.hierarchy`` (top level first).
    """
    import shapely

    from ..ingest.global_data import points_in_polygon
    from ..spatial.h3grid import assign_cells

    cells = list(cells)
    out = pd.DataFrame(index=pd.Index(cells, name="cell"))
    if df.empty:
        return out
    d = pd.DataFrame({"lon": shapely.get_x(df["geometry"].to_numpy()), "lat": shapely.get_y(df["geometry"].to_numpy()),
                      "conf": pd.to_numeric(df["confidence"], errors="coerce"),
                      "cat": df["basic_category"].to_numpy(),
                      "top": [_first(t.get("hierarchy")) if isinstance(t, dict) else None for t in df["taxonomy"]],
                      "src": [_dataset(x) for x in df["sources"]]})
    d = d[d["conf"] >= min_confidence]
    if mask is not None:
        d = d[points_in_polygon(d["lat"].to_numpy(), d["lon"].to_numpy(), mask["outer"], mask.get("inner", ()))]
    d["cell"] = assign_cells(d["lat"].to_numpy(), d["lon"].to_numpy(), resolution)
    g = d.groupby("cell")
    out["ov_places_n"] = g.size().reindex(cells).fillna(0)
    out["ov_places_categories"] = g["cat"].nunique().reindex(cells).fillna(0)
    top = pd.crosstab(d["cell"], d["top"]).reindex(cells).fillna(0)
    for c in top.columns:
        out[f"ov_places_{c}"] = top[c]
    return out

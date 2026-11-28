"""Export helpers for the web demo (GeoJSON / JSON)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, Iterable, Sequence

import numpy as np
import pandas as pd

__all__ = ["cells_geojson", "rings_geojson", "buildings_geojson", "write_json"]


def _clean(v):
    if isinstance(v, (np.floating, float)):
        return None if not math.isfinite(float(v)) else round(float(v), 6)
    if isinstance(v, (np.integer,)):
        return int(v)
    return v


def cells_geojson(df: pd.DataFrame) -> dict:
    """FeatureCollection of H3 cells (index = cell id) with all columns as properties."""
    from .spatial.h3grid import require_h3

    h3 = require_h3()
    feats = []
    for cell, row in df.iterrows():
        ring = [[lon, lat] for lat, lon in h3.cell_to_boundary(cell)]
        ring.append(ring[0])
        props = {"cell": cell, **{k: _clean(v) for k, v in row.items()}}
        feats.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]}, "properties": props})
    return {"type": "FeatureCollection", "features": feats}


def rings_geojson(outer: Sequence, inner: Sequence = (), props: dict | None = None) -> dict:
    polys = [[[[lon, lat] for lat, lon in r]] for r in outer]
    geom = {"type": "MultiPolygon", "coordinates": polys}
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": geom, "properties": props or {}}]}


def buildings_geojson(payload: dict, keep_ids: Iterable[str], ndigits: int = 6) -> dict:
    keep = set(keep_ids)
    feats = []
    for el in payload.get("elements", []):
        oid = f"way/{el.get('id')}"
        if el.get("type") != "way" or oid not in keep or "geometry" not in el:
            continue
        ring = [[round(p["lon"], ndigits), round(p["lat"], ndigits)] for p in el["geometry"]]
        tags = el.get("tags", {})
        feats.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [ring]},
                "properties": {"id": oid, "building": tags.get("building"), "levels": tags.get("building:levels")},
            }
        )
    return {"type": "FeatureCollection", "features": feats}


def write_json(obj, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))

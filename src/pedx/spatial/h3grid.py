"""H3 hexagonal indexing: the primary spatial unit of pedx (K-019).

Buildings are assigned to the H3 cell that contains their centroid. Hexagons
have uniform 6-neighbour adjacency, which makes graph operations (PED boundary
growth, Shapley attribution) and multi-resolution (MAUP) analysis uniform
across cities.

Requires the optional dependency ``h3>=4`` (``pip install pedx[h3]``).
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence

import numpy as np

__all__ = ["require_h3", "assign_cells", "cell_adjacency", "cell_centroids", "cell_area_m2"]


def require_h3():
    try:
        import h3  # noqa: F401
    except ImportError as exc:  # pragma: no cover - exercised only without h3
        raise ImportError("H3 support requires `pip install pedx[h3]` (h3>=4)") from exc
    return h3


def assign_cells(lats: Sequence[float], lons: Sequence[float], resolution: int) -> List[str]:
    """H3 cell id for every (lat, lon) point at ``resolution`` (0–15)."""
    h3 = require_h3()
    if not 0 <= resolution <= 15:
        raise ValueError("H3 resolution must be in [0, 15]")
    lats = np.asarray(lats, dtype=float)
    lons = np.asarray(lons, dtype=float)
    if lats.shape != lons.shape:
        raise ValueError("lats and lons must have the same shape")
    return [h3.latlng_to_cell(float(a), float(b), resolution) for a, b in zip(lats, lons)]


def cell_adjacency(cells: Iterable[str], k: int = 1) -> Dict[str, List[str]]:
    """Adjacency restricted to the given cells (ring distance <= ``k``)."""
    h3 = require_h3()
    present = set(cells)
    adj: Dict[str, List[str]] = {}
    for c in sorted(present):
        adj[c] = sorted(n for n in h3.grid_disk(c, k) if n != c and n in present)
    return adj


def cell_centroids(cells: Iterable[str]) -> Dict[str, tuple]:
    h3 = require_h3()
    return {c: h3.cell_to_latlng(c) for c in cells}


def cell_area_m2(cell: str) -> float:
    h3 = require_h3()
    return float(h3.cell_area(cell, unit="m^2"))

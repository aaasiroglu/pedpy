"""Complementarity-aware PED boundary growth on the cell adjacency graph.

Starting from a seed cell, neighbours are added one at a time. The candidate
score combines the (normalised) readiness of the cell and its *hourly
complementarity* with the current cluster:

    Δ_j = (I_C + I_j - I_{C∪j}) / D_j

the share of cell j's demand that no longer needs grid import thanks to
sharing with C (``I`` = annual grid import of a node). While the cluster has
not reached the PED balance target, candidates that raise the balance are
preferred; once it has, only candidates that keep it are allowed.

This is a greedy heuristic. :func:`exhaustive_best_cluster` (small graphs) and
:func:`random_contiguous_growth` provide the optimality-gap and null baselines
required to make claims about it (docs/07, R7).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from ..energy.aggregate import CellEnergy
from ..energy.load_match import load_match

__all__ = ["cluster_metrics", "grow_ped_boundary", "random_contiguous_growth", "exhaustive_best_cluster", "GrowthResult"]


def cluster_metrics(cells: CellEnergy, members: Sequence[str]) -> dict:
    idx = [cells.index[c] for c in members]
    g = cells.generation_kwh[idx].sum(0)
    d = cells.demand_kwh[idx].sum(0)
    m = load_match(g, d, cells.dt_hours)
    return {k: float(v) for k, v in m.items()}


def _annual_import(g: np.ndarray, d: np.ndarray) -> float:
    return float(np.maximum(d - g, 0.0).sum())


@dataclass
class GrowthResult:
    path: pd.DataFrame
    ped_cells: List[str]
    is_ped: bool

    def __repr__(self) -> str:  # pragma: no cover
        return f"GrowthResult(n_path={len(self.path)}, ped_cells={len(self.ped_cells)}, is_ped={self.is_ped})"


def grow_ped_boundary(
    cells: CellEnergy,
    adjacency: Mapping[str, Sequence[str]],
    seed: str,
    max_cells: int = 12,
    balance_target: float = 1.0,
    readiness: Optional[Mapping[str, float]] = None,
    beta: float = 0.5,
) -> GrowthResult:
    if seed not in cells.index:
        raise KeyError(f"seed {seed} not in cells")
    if not 0 <= beta <= 1:
        raise ValueError("beta must be in [0, 1]")
    if readiness is None:
        beta = 0.0
        r_norm = {c: 0.0 for c in cells.cell_ids}
    else:
        vals = np.array([readiness[c] for c in cells.cell_ids], float)
        lo, hi = np.nanmin(vals), np.nanmax(vals)
        span = hi - lo if hi > lo else 1.0
        r_norm = {c: (readiness[c] - lo) / span for c in cells.cell_ids}

    G, D, ix = cells.generation_kwh, cells.demand_kwh, cells.index
    members = [seed]
    g_c, d_c = G[ix[seed]].copy(), D[ix[seed]].copy()
    rows = []

    def record(step, added, delta, score):
        m = load_match(g_c, d_c, cells.dt_hours)
        rows.append(
            {
                "step": step,
                "added": added,
                "n_cells": len(members),
                "balance": float(m["balance"]),
                "ssr": float(m["ssr"]),
                "peak_relief": float(m["peak_relief"]),
                "complementarity": delta,
                "candidate_score": score,
            }
        )

    record(0, seed, np.nan, np.nan)
    while len(members) < max_cells:
        frontier = sorted({n for c in members for n in adjacency.get(c, ()) if n not in members and n in ix})
        if not frontier:
            break
        imp_c = _annual_import(g_c, d_c)
        bal_c = g_c.sum() / d_c.sum() if d_c.sum() > 0 else np.inf
        cands = []
        for j in frontier:
            gj, dj = G[ix[j]], D[ix[j]]
            g_new, d_new = g_c + gj, d_c + dj
            dsum = dj.sum()
            delta = (imp_c + _annual_import(gj, dj) - _annual_import(g_new, d_new)) / dsum if dsum > 0 else 0.0
            bal_new = g_new.sum() / d_new.sum() if d_new.sum() > 0 else np.inf
            score = beta * r_norm[j] + (1 - beta) * delta
            cands.append((j, delta, bal_new, score))
        if bal_c >= balance_target:
            cands = [c for c in cands if c[2] >= balance_target]
            if not cands:
                break
            j, delta, _, score = max(cands, key=lambda c: (c[3], c[0]))
        else:
            j, delta, _, score = max(cands, key=lambda c: (c[2] > bal_c, c[3], c[0]))
        members.append(j)
        g_c += G[ix[j]]
        d_c += D[ix[j]]
        record(len(members) - 1, j, float(delta), float(score))

    path = pd.DataFrame(rows)
    feasible = path.index[path["balance"] >= balance_target]
    if len(feasible):
        last = int(feasible.max())
        return GrowthResult(path, list(path["added"].iloc[: last + 1]), True)
    return GrowthResult(path, list(path["added"]), False)


def random_contiguous_growth(
    cells: CellEnergy,
    adjacency: Mapping[str, Sequence[str]],
    seed: str,
    n_cells: int,
    rng: Optional[np.random.Generator] = None,
) -> List[str]:
    """Null model: grow a connected cluster by adding uniformly random frontier cells."""
    rng = np.random.default_rng() if rng is None else rng
    members = [seed]
    while len(members) < n_cells:
        frontier = sorted({n for c in members for n in adjacency.get(c, ()) if n not in members and n in cells.index})
        if not frontier:
            break
        members.append(frontier[int(rng.integers(len(frontier)))])
    return members


def _connected_sets_with(seed: str, adjacency: Mapping[str, Sequence[str]], size: int, allowed: set) -> List[frozenset]:
    level = {frozenset([seed])}
    for _ in range(size - 1):
        nxt = set()
        for s in level:
            for c in s:
                for nb in adjacency.get(c, ()):
                    if nb in allowed and nb not in s:
                        nxt.add(s | {nb})
        level = nxt
    return list(level)


def exhaustive_best_cluster(
    cells: CellEnergy,
    adjacency: Mapping[str, Sequence[str]],
    seed: str,
    size: int,
    objective: str = "ssr",
    balance_target: Optional[float] = 1.0,
    max_sets: int = 200_000,
) -> Dict[str, object]:
    """Best connected cluster of exactly ``size`` cells containing ``seed`` (exact, small graphs)."""
    sets = _connected_sets_with(seed, adjacency, size, set(cells.index))
    if len(sets) > max_sets:
        raise ValueError(f"{len(sets)} candidate sets exceed max_sets={max_sets}")
    best, best_val = None, -np.inf
    for s in sets:
        m = cluster_metrics(cells, sorted(s))
        if balance_target is not None and m["balance"] < balance_target:
            continue
        if m[objective] > best_val:
            best, best_val = sorted(s), m[objective]
    return {"cells": best, "value": best_val, "n_candidates": len(sets)}

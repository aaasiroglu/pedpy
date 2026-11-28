"""NumPy-only statistical helpers (rank correlations, error metrics).

These are deliberately dependency-free so that the core of ``pedpy`` runs
with only ``numpy`` and ``pandas`` installed.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "rankdata",
    "ranks_descending",
    "spearman_rho",
    "kendall_tau_b",
    "rmse",
    "mape",
]


def rankdata(values: np.ndarray) -> np.ndarray:
    """Average ranks (1-based, ascending), equivalent to ``scipy.stats.rankdata``."""
    a = np.asarray(values, dtype=float).ravel()
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(a.size, dtype=float)
    sorted_a = a[order]
    i = 0
    n = a.size
    while i < n:
        j = i
        while j + 1 < n and sorted_a[j + 1] == sorted_a[i]:
            j += 1
        ranks[order[i : j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return ranks


def ranks_descending(scores: np.ndarray) -> np.ndarray:
    """Integer ranks where 1 = highest score (ties broken by position)."""
    s = np.asarray(scores, dtype=float).ravel()
    order = np.argsort(-s, kind="mergesort")
    ranks = np.empty(s.size, dtype=int)
    ranks[order] = np.arange(1, s.size + 1)
    return ranks


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    xm = x - x.mean()
    ym = y - y.mean()
    den = np.sqrt((xm**2).sum() * (ym**2).sum())
    if den == 0.0:
        return float("nan")
    return float((xm * ym).sum() / den)


def spearman_rho(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation (tie-aware, via Pearson on average ranks)."""
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    if x.size != y.size:
        raise ValueError("x and y must have the same length")
    return _pearson(rankdata(x), rankdata(y))


def kendall_tau_b(x: np.ndarray, y: np.ndarray) -> float:
    """Kendall's tau-b (tie-corrected), O(n^2) implementation."""
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    if x.size != y.size:
        raise ValueError("x and y must have the same length")
    dx = np.sign(x[:, None] - x[None, :])
    dy = np.sign(y[:, None] - y[None, :])
    iu = np.triu_indices(x.size, k=1)
    sx, sy = dx[iu], dy[iu]
    s = float((sx * sy).sum())
    n_x = float((sx != 0).sum())
    n_y = float((sy != 0).sum())
    if n_x == 0 or n_y == 0:
        return float("nan")
    return s / np.sqrt(n_x * n_y)


def rmse(pred: np.ndarray, ref: np.ndarray) -> float:
    pred = np.asarray(pred, dtype=float)
    ref = np.asarray(ref, dtype=float)
    return float(np.sqrt(np.mean((pred - ref) ** 2)))


def mape(pred: np.ndarray, ref: np.ndarray) -> float:
    """Mean absolute percentage error in percent; reference zeros are skipped."""
    pred = np.asarray(pred, dtype=float)
    ref = np.asarray(ref, dtype=float)
    mask = ref != 0
    if not mask.any():
        return float("nan")
    return float(100.0 * np.mean(np.abs((pred[mask] - ref[mask]) / ref[mask])))

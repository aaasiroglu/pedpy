"""Set-relative MCDM methods (within-city prioritisation view).

These scores depend on the current set of alternatives (ideal/anti-ideal or
column norms), so they are *not* comparable across cities; the primary pedx
output is the absolute readiness index (:mod:`pedx.index`).

MARCOS equivalence (Xie & Zou, 2025; verified numerically in tests):
``f(K_i) = κ · S_i`` with ``κ = (S_ai + S_aai) / (S_ai² + S_ai·S_aai + S_aai²) > 0``,
so MARCOS ranks exactly like the weighted sum ``S_i`` of its ratio-normalised
matrix. ``marcos`` returns ``kappa`` so this can be checked on any input.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .._stats import ranks_descending

__all__ = ["marcos_normalize", "marcos", "wsm", "topsis"]


def _check(X, w, is_benefit):
    X = np.asarray(X, float)
    w = np.asarray(w, float)
    ben = np.asarray(is_benefit, bool)
    if X.ndim != 2 or X.shape[1] != w.size or ben.size != w.size:
        raise ValueError("shape mismatch between X, weights and is_benefit")
    if np.any(w < 0) or not np.isclose(w.sum(), 1.0):
        raise ValueError("weights must be non-negative and sum to 1")
    return X, w, ben


def marcos_normalize(X, is_benefit: Sequence[bool]):
    """Ratio normalisation against the ideal (Stević et al., 2020). Requires positive data."""
    X = np.asarray(X, float)
    ben = np.asarray(is_benefit, bool)
    if np.any(X <= 0):
        raise ValueError(
            "MARCOS ratio normalisation is undefined for non-positive values (K-004); "
            "transform or shift the data explicitly before calling"
        )
    ai = np.where(ben, X.max(0), X.min(0))
    aai = np.where(ben, X.min(0), X.max(0))
    norm = lambda M: np.where(ben, M / ai, ai / M)  # noqa: E731
    return norm(X), norm(aai[None, :])[0], norm(ai[None, :])[0]


def marcos(X, weights, is_benefit) -> dict:
    X, w, ben = _check(X, weights, is_benefit)
    N, n_aai, n_ai = marcos_normalize(X, ben)
    S = N @ w
    s_aai, s_ai = float(n_aai @ w), float(n_ai @ w)
    k_minus, k_plus = S / s_aai, S / s_ai
    f_minus = k_plus / (k_plus + k_minus)
    f_plus = k_minus / (k_plus + k_minus)
    f_k = (k_plus + k_minus) / (1.0 + (1.0 - f_plus) / f_plus + (1.0 - f_minus) / f_minus)
    kappa = (s_ai + s_aai) / (s_ai**2 + s_ai * s_aai + s_aai**2)
    return {"f_k": f_k, "S": S, "kappa": kappa, "N": N, "ranks": ranks_descending(f_k)}


def wsm(N, weights) -> dict:
    """Weighted sum of an already normalised (benefit-oriented) matrix."""
    N = np.asarray(N, float)
    w = np.asarray(weights, float)
    s = N @ w
    return {"score": s, "ranks": ranks_descending(s)}


def topsis(X, weights, is_benefit) -> dict:
    X, w, ben = _check(X, weights, is_benefit)
    norms = np.sqrt((X**2).sum(0))
    norms = np.where(norms > 0, norms, 1.0)
    V = X / norms * w
    pis = np.where(ben, V.max(0), V.min(0))
    nis = np.where(ben, V.min(0), V.max(0))
    dp = np.sqrt(((V - pis) ** 2).sum(1))
    dn = np.sqrt(((V - nis) ** 2).sum(1))
    den = dp + dn
    cc = np.where(den > 0, dn / np.where(den > 0, den, 1.0), 0.5)
    return {"score": cc, "ranks": ranks_descending(cc)}

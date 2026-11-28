"""Objective and subjective criteria weights.

In pedx, weights are a *policy dimension with uncertainty*, not a single truth
(docs/07, B4). These functions provide reference points in the weight simplex.

* CRITIC (Diakoulaki et al., 1995): direction-aware min-max normalisation,
  population std, Pearson conflict; constant columns get weight 0.
* Entropy: computed on direction-aware min-max normalised data (K-008, avoids
  the raw-data distortions documented by Zhu et al., 2020); constant columns
  get weight 0.
* Linear BWM (Rezaei, 2016): requires SciPy (``pip install pedx[mcdm]``).
* Linear fusion ``w = λ w_bwm + (1-λ)(α w_critic + (1-α) w_entropy)``,
  optionally projected onto ``{w_j >= lb on active columns, Σw = 1}``.
"""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

import numpy as np

__all__ = [
    "minmax_directed",
    "constant_columns",
    "critic_weights",
    "entropy_weights",
    "bwm_linear",
    "fuse_weights",
    "project_bounded_simplex",
]


def _as_matrix(X) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or X.shape[0] < 2:
        raise ValueError("X must be a 2-D matrix with at least two alternatives")
    if not np.all(np.isfinite(X)):
        raise ValueError("X contains NaN/inf")
    return X


def constant_columns(X, atol: float = 1e-12) -> np.ndarray:
    X = _as_matrix(X)
    return np.ptp(X, axis=0) <= atol


def minmax_directed(X, is_benefit: Optional[Sequence[bool]] = None) -> np.ndarray:
    """``r = (x - min)/(max - min)`` (benefit) or ``(max - x)/(max - min)`` (cost); constant columns → 0."""
    X = _as_matrix(X)
    ben = np.ones(X.shape[1], bool) if is_benefit is None else np.asarray(is_benefit, bool)
    lo, hi = X.min(0), X.max(0)
    rng = hi - lo
    const = rng <= 1e-12
    safe = np.where(const, 1.0, rng)
    R = np.where(ben, (X - lo) / safe, (hi - X) / safe)
    R[:, const] = 0.0
    return R


def critic_weights(X, is_benefit: Optional[Sequence[bool]] = None) -> Tuple[np.ndarray, dict]:
    R = minmax_directed(X, is_benefit)
    const = constant_columns(X)
    sigma = R.std(axis=0, ddof=0)
    n = R.shape[1]
    corr = np.zeros((n, n))
    act = ~const
    if act.sum() >= 2:
        corr_act = np.corrcoef(R[:, act], rowvar=False)
        corr[np.ix_(act, act)] = np.atleast_2d(corr_act)
    elif act.sum() == 1:
        corr[np.ix_(act, act)] = 1.0
    conflict = np.where(act, (1.0 - corr)[:, act].sum(axis=1), 0.0)
    C = sigma * conflict
    if C.sum() <= 0:
        w = np.where(act, 1.0 / max(act.sum(), 1), 0.0)
    else:
        w = C / C.sum()
    return w, {"sigma": sigma, "R": corr, "C": C, "constant_mask": const}


def entropy_weights(X, is_benefit: Optional[Sequence[bool]] = None) -> Tuple[np.ndarray, dict]:
    R = minmax_directed(X, is_benefit)
    const = constant_columns(X)
    m = R.shape[0]
    colsum = R.sum(axis=0)
    P = np.where(colsum > 0, R / np.where(colsum > 0, colsum, 1.0), 1.0 / m)
    with np.errstate(divide="ignore", invalid="ignore"):
        plogp = np.where(P > 0, P * np.log(P), 0.0)
    E = -plogp.sum(axis=0) / np.log(m)
    E[const] = 1.0
    d = 1.0 - E
    w = d / d.sum() if d.sum() > 0 else np.where(~const, 1.0 / max((~const).sum(), 1), 0.0)
    return w, {"E": E, "d": d, "constant_mask": const}


def bwm_linear(best_to_others: Sequence[float], others_to_worst: Sequence[float], best: int, worst: int) -> Tuple[np.ndarray, float]:
    """Linear BWM: ``min ξ`` s.t. ``|w_B - a_Bj w_j| <= ξ``, ``|w_j - a_jW w_W| <= ξ``, ``Σw = 1``, ``w >= 0``.

    Returns ``(weights, xi)``; smaller ``xi`` = more consistent comparisons.
    """
    try:
        from scipy.optimize import linprog
    except ImportError as exc:  # pragma: no cover
        raise ImportError("bwm_linear requires SciPy: pip install pedx[mcdm]") from exc
    a_b = np.asarray(best_to_others, float)
    a_w = np.asarray(others_to_worst, float)
    n = a_b.size
    if a_w.size != n or not (0 <= best < n and 0 <= worst < n) or best == worst:
        raise ValueError("inconsistent BWM inputs")
    if np.any(a_b < 1) or np.any(a_w < 1) or a_b[best] != 1 or a_w[worst] != 1:
        raise ValueError("comparisons must be >= 1 and a_BB = a_WW = 1")
    # variables: w_0..w_{n-1}, xi
    A, b = [], []
    for j in range(n):
        for sign in (1.0, -1.0):
            row = np.zeros(n + 1)
            row[best] += sign
            row[j] -= sign * a_b[j]
            row[-1] = -1.0
            A.append(row)
            b.append(0.0)
            row = np.zeros(n + 1)
            row[j] += sign
            row[worst] -= sign * a_w[j]
            row[-1] = -1.0
            A.append(row)
            b.append(0.0)
    A_eq = np.zeros((1, n + 1))
    A_eq[0, :n] = 1.0
    c = np.zeros(n + 1)
    c[-1] = 1.0
    res = linprog(c, A_ub=np.array(A), b_ub=np.array(b), A_eq=A_eq, b_eq=[1.0], bounds=[(0, None)] * (n + 1), method="highs")
    if not res.success:  # pragma: no cover
        raise RuntimeError(f"BWM LP failed: {res.message}")
    return res.x[:n], float(res.x[-1])


def project_bounded_simplex(v: np.ndarray, lower: float = 0.0, active: Optional[np.ndarray] = None) -> np.ndarray:
    """Euclidean projection onto ``{w : w_j >= lower (active), w_j = 0 (inactive), Σw = 1}``."""
    v = np.asarray(v, float)
    act = np.ones(v.size, bool) if active is None else np.asarray(active, bool)
    k = act.sum()
    if k == 0:
        raise ValueError("no active columns")
    if lower * k > 1 + 1e-12:
        raise ValueError(f"lower bound {lower} infeasible for {k} active columns")
    z = 1.0 - lower * k
    u = v[act] - lower
    # projection of u onto the simplex {x >= 0, Σx = z}
    s = np.sort(u)[::-1]
    css = np.cumsum(s) - z
    idx = np.arange(1, s.size + 1)
    rho = np.nonzero(s - css / idx > 0)[0][-1]
    theta = css[rho] / (rho + 1)
    out = np.zeros_like(v)
    out[act] = np.maximum(u - theta, 0.0) + lower
    return out


def fuse_weights(
    w_critic: np.ndarray,
    w_entropy: np.ndarray,
    w_expert: Optional[np.ndarray] = None,
    alpha: float = 0.5,
    lam: float = 0.0,
    lower: float = 0.0,
    constant_mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """``λ w_expert + (1-λ)(α w_critic + (1-α) w_entropy)``, projected onto the bounded simplex."""
    if not (0 <= alpha <= 1 and 0 <= lam <= 1):
        raise ValueError("alpha and lam must be in [0, 1]")
    w_obj = alpha * np.asarray(w_critic, float) + (1 - alpha) * np.asarray(w_entropy, float)
    if lam > 0:
        if w_expert is None:
            raise ValueError("lam > 0 requires w_expert")
        w = lam * np.asarray(w_expert, float) + (1 - lam) * w_obj
    else:
        w = w_obj
    active = None if constant_mask is None else ~np.asarray(constant_mask, bool)
    return project_bounded_simplex(w, lower, active)

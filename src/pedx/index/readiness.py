"""Absolute, physically anchored PED Readiness Index (K-014).

Unlike set-relative MCDM scores (MARCOS, TOPSIS, CRITIC-weighted sums), every
value function here is anchored to a *physical* reference, so a score of 0.8
means the same thing in Istanbul and in Berlin, and adding or removing cells
never changes another cell's score (no rank reversal).

Energy axis (computed from hourly simulation, no free anchors):

=============  ====================================  ==========================
value          definition                            anchor
=============  ====================================  ==========================
``v_balance``  ``min(B, 1)``, ``B = ΣG / ΣD``         1 = annual PED balance met
``v_ssr``      ``SSR``                                1 = fully self-sufficient
``v_relief``   ``1 - CVaR(I) / CVaR(D)``              1 = stress-hour load removed
=============  ====================================  ==========================

``energy_score = Σ w_k v_k`` with weights on the simplex (default equal).
Weights are *not* treated as a single truth: see :func:`rank_intervals`.
"""

from __future__ import annotations

from typing import Dict, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from .._backend import get_xp, smooth_clip01
from .._stats import ranks_descending

__all__ = [
    "ENERGY_VALUES",
    "energy_values",
    "energy_score",
    "contributions",
    "rank_intervals",
]

ENERGY_VALUES = ("v_balance", "v_ssr", "v_relief")
DEFAULT_ENERGY_WEIGHTS = {"v_balance": 1 / 3, "v_ssr": 1 / 3, "v_relief": 1 / 3}


def energy_values(indicators: Mapping, sharpness: float = 0.0) -> Dict[str, object]:
    """Map load-matching indicators (from :func:`pedx.energy.load_match`) to [0, 1] values.

    ``sharpness > 0`` replaces the hard clip of the balance by a smooth one, for
    gradient-based inverse analysis.
    """
    bal = indicators["balance"]
    xp = get_xp(bal)
    return {
        "v_balance": smooth_clip01(bal, sharpness) if sharpness else xp.clip(bal, 0.0, 1.0),
        "v_ssr": indicators["ssr"],
        "v_relief": indicators["peak_relief"],
    }


def _weights(weights: Optional[Mapping[str, float]]) -> Dict[str, float]:
    w = dict(DEFAULT_ENERGY_WEIGHTS if weights is None else weights)
    if set(w) != set(ENERGY_VALUES):
        raise ValueError(f"weights must have keys {ENERGY_VALUES}")
    vals = np.array([w[k] for k in ENERGY_VALUES], dtype=float)
    if np.any(vals < 0) or not np.isclose(vals.sum(), 1.0):
        raise ValueError("weights must be non-negative and sum to 1")
    return w


def energy_score(values: Mapping, weights: Optional[Mapping[str, float]] = None):
    w = _weights(weights)
    return sum(w[k] * values[k] for k in ENERGY_VALUES)


def contributions(values: pd.DataFrame, weights: Optional[Mapping[str, float]] = None, baseline: str = "mean") -> pd.DataFrame:
    """Exact additive attribution ``phi_ik = w_k (v_ik - v_ref,k)``.

    For a linear score these are the exact Shapley values w.r.t. the reference
    (``baseline='mean'`` → the average cell, ``'zero'`` → a cell with all values 0).
    ``phi.sum(axis=1) == score - score_ref`` holds exactly (efficiency).
    """
    w = _weights(weights)
    v = values[list(ENERGY_VALUES)].astype(float)
    if baseline == "mean":
        ref = v.mean(axis=0)
    elif baseline == "zero":
        ref = pd.Series(0.0, index=v.columns)
    else:
        raise ValueError("baseline must be 'mean' or 'zero'")
    return (v - ref) * pd.Series(w)


def rank_intervals(
    values: pd.DataFrame,
    weights: Optional[Mapping[str, float]] = None,
    concentration: float = 50.0,
    n_samples: int = 2000,
    top_k: int = 5,
    seed: Optional[int] = 0,
    interval: Sequence[float] = (0.05, 0.95),
) -> pd.DataFrame:
    """Rank uncertainty under weight uncertainty (SMAA-style acceptability).

    Weights are drawn from ``Dirichlet(concentration * w)``: large
    ``concentration`` = confident policy, small = vague policy. Returns per cell
    the median rank, a rank interval, the probability of being ranked first
    (first-rank acceptability) and of being in the top ``k``.
    """
    w = _weights(weights)
    alpha = concentration * np.array([w[k] for k in ENERGY_VALUES])
    alpha = np.where(alpha > 0, alpha, 1e-6)
    rng = np.random.default_rng(seed)
    W = rng.dirichlet(alpha, size=n_samples)  # (S, K)
    V = values[list(ENERGY_VALUES)].to_numpy(dtype=float)  # (n, K)
    if np.isnan(V).any():
        raise ValueError("values contain NaN; resolve undefined indicators first")
    scores = W @ V.T  # (S, n)
    ranks = np.apply_along_axis(ranks_descending, 1, scores)  # (S, n)
    lo, hi = np.quantile(ranks, interval, axis=0)
    return pd.DataFrame(
        {
            "rank_median": np.median(ranks, axis=0),
            "rank_lo": lo,
            "rank_hi": hi,
            "p_first": (ranks == 1).mean(axis=0),
            f"p_top{top_k}": (ranks <= top_k).mean(axis=0),
        },
        index=values.index,
    )

"""Inverse weight (policy) stability analysis.

Question: *what is the smallest change of the weight vector that would put
cell k in first place?* For any linear score ``s_i(w) = v_i · w`` (the
absolute readiness index, WSM, and – by the equivalence theorem – MARCOS on its
normalised matrix) this is a convex quadratic program:

    min_w ||w - w0||²   s.t.  (v_k - v_j) · w >= 0  for ALL j != k,
                              Σ w = 1,  w >= lower

Two improvements over a pairwise "beat the current leader" formulation:

* k must beat *every* competitor, otherwise a third cell may take first place.
* Before solving, an LP checks whether k can be first under *any* admissible
  weights. If not, k is "not potentially optimal" (its first-rank
  acceptability in SMAA terms is zero) — this is weaker than Pareto dominance
  and is reported as such.

Requires SciPy (``pip install pedx[mcdm]``).
"""

from __future__ import annotations

from typing import Optional, Sequence

import numpy as np

__all__ = ["inverse_weight_stability"]


def inverse_weight_stability(
    V,
    w0: Sequence[float],
    k: int,
    lower: float = 0.0,
    margin: float = 0.0,
    names: Optional[Sequence[str]] = None,
) -> dict:
    """Minimal L2 weight shift that makes alternative ``k`` rank first.

    ``V``: (n, K) matrix of benefit-oriented normalised values; ``w0``: current
    weights on the simplex. Returns a dict with ``potentially_optimal``,
    ``min_l2_shift``, ``weights`` and ``delta`` (None when infeasible).
    """
    try:
        from scipy.optimize import linprog, minimize
    except ImportError as exc:  # pragma: no cover
        raise ImportError("inverse_weight_stability requires SciPy: pip install pedx[mcdm]") from exc

    V = np.asarray(V, float)
    w0 = np.asarray(w0, float)
    n, K = V.shape
    if w0.size != K or not 0 <= k < n:
        raise ValueError("shape mismatch or invalid k")
    if lower * K > 1 + 1e-12:
        raise ValueError("lower bound infeasible")
    others = [j for j in range(n) if j != k]
    D = V[k][None, :] - V[others]  # (n-1, K); need D @ w >= margin

    # LP: max t s.t. D w >= t, Σw = 1, w >= lower  →  variables (w, t)
    c = np.zeros(K + 1)
    c[-1] = -1.0
    A_ub = np.hstack([-D, np.ones((len(others), 1))])
    lp = linprog(
        c,
        A_ub=A_ub,
        b_ub=np.zeros(len(others)),
        A_eq=np.r_[np.ones(K), 0.0][None, :],
        b_eq=[1.0],
        bounds=[(lower, 1.0)] * K + [(None, None)],
        method="highs",
    )
    best_margin = float(-lp.fun) if lp.success else -np.inf
    current_gap = float((D @ w0).min()) if others else np.inf
    out = {
        "k": k,
        "name": None if names is None else names[k],
        "potentially_optimal": best_margin >= margin - 1e-12,
        "best_achievable_margin": best_margin,
        "current_min_gap": current_gap,
    }
    if current_gap >= margin:
        out.update(min_l2_shift=0.0, weights=w0.copy(), delta=np.zeros(K))
        return out
    if not out["potentially_optimal"]:
        out.update(min_l2_shift=np.inf, weights=None, delta=None)
        return out

    start = lp.x[:K]
    cons = [
        {"type": "eq", "fun": lambda w: w.sum() - 1.0, "jac": lambda w: np.ones(K)},
        {"type": "ineq", "fun": lambda w: D @ w - margin, "jac": lambda w: D},
    ]
    res = minimize(
        lambda w: float(((w - w0) ** 2).sum()),
        start,
        jac=lambda w: 2 * (w - w0),
        bounds=[(lower, 1.0)] * K,
        constraints=cons,
        method="SLSQP",
        options={"ftol": 1e-12, "maxiter": 500},
    )
    w = res.x if res.success else start
    if (D @ w).min() < margin - 1e-7:  # fall back to the LP point, which is feasible
        w = start
    out.update(min_l2_shift=float(np.linalg.norm(w - w0)), weights=w, delta=w - w0, solver_success=bool(res.success))
    return out

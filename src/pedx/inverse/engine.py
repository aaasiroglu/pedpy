"""Differentiable inverse (prescriptive) analysis in the physical intervention space.

Three coupled inverse problems (docs/08):

1. **Budget problem** – ``max_u score(u)  s.t.  c·u <= B,  0 <= u <= u_max``
2. **Target problem** – ``min_u c·u  s.t.  score(u) >= target,  0 <= u <= u_max``
   solved as the smallest budget whose budget-problem optimum reaches the
   target (bisection; valid because the optimal score is non-decreasing in B).
3. **Pareto / improvement-cost curve** – the budget problem over a budget grid.

Search uses gradients of the *smoothed* physics (JAX autodiff through the
hourly simulation and battery scan) with projected Adam steps on the
budget-constrained box. Every candidate is re-scored with the *exact* model
and every returned prescription passes :func:`pedx.inverse.model.audit`.
"Smooth for search, exact for reporting" – the relaxation never reaches the
reported numbers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np
import pandas as pd

from .model import LEVERS, CellState, audit, score

__all__ = ["InverseEngine", "Prescription", "project_box_budget"]


def project_box_budget(z: np.ndarray, c: np.ndarray, budget: float) -> np.ndarray:
    """Euclidean projection onto ``{0 <= z <= 1, c·z <= budget}`` (c >= 0)."""
    z = np.clip(z, 0.0, 1.0)
    if c @ z <= budget + 1e-12:
        return z
    lo, hi = 0.0, float(np.max(z / np.where(c > 0, c, np.inf))) + 1.0
    for _ in range(100):
        lam = 0.5 * (lo + hi)
        if c @ np.clip(z - lam * c, 0.0, 1.0) > budget:
            lo = lam
        else:
            hi = lam
    return np.clip(z - hi * c, 0.0, 1.0)


@dataclass
class Prescription:
    cell_id: str
    budget: Optional[float]
    u: np.ndarray
    cost: float
    score: float
    baseline_score: float
    audit: dict

    def as_dict(self) -> dict:
        d = {
            "cell": self.cell_id,
            "budget": self.budget,
            "cost": self.cost,
            "score": self.score,
            "baseline_score": self.baseline_score,
            "audit_passed": self.audit["passed"],
        }
        d.update({f"u_{k}": float(v) for k, v in zip(LEVERS, self.u)})
        d.update({k: v for k, v in self.audit["indicators"].items() if k in ("balance", "ssr", "peak_relief")})
        return d


class InverseEngine:
    """Gradient-based inverse analysis for one :class:`CellState`.

    Parameters
    ----------
    tau_rel : soft-min temperature relative to mean hourly demand; the SSR
        relaxation error is bounded by ``tau_rel * ln 2`` per unit (see
        :mod:`pedx._backend`). Default 0.02.
    sharpness : smoothness of the balance clip in the search objective.
    """

    def __init__(
        self,
        state: CellState,
        weights=None,
        tau_rel: float = 0.02,
        sharpness: float = 50.0,
        steps: int = 150,
        lr: float = 0.05,
        n_starts: int = 3,
        check_every: int = 10,
    ):
        try:
            import jax
        except ImportError as exc:  # pragma: no cover
            raise ImportError("InverseEngine requires JAX: pip install pedx[diff]") from exc
        jax.config.update("jax_enable_x64", True)
        import jax.numpy as jnp

        self.state = state
        self.weights = weights
        self.lo = state.lower_vec
        self.hi = state.upper_vec
        self.span = self.hi - self.lo
        self.active = self.span > 0
        self.c = state.cost_vec
        self.steps, self.lr, self.n_starts, self.check_every = steps, lr, n_starts, check_every
        self.tau = float(tau_rel * np.mean(state.base_demand_kwh))
        self.sharpness = sharpness
        lo_j, span_j = jnp.asarray(self.lo), jnp.asarray(self.span)

        def smooth_obj(z):
            return score(state, lo_j + z * span_j, tau=self.tau, sharpness=sharpness, weights=weights)

        self._grad = jax.jit(jax.value_and_grad(smooth_obj))
        self.baseline = self.exact_score(np.zeros(len(LEVERS)))

    # ------------------------------------------------------------ helpers
    def exact_score(self, u) -> float:
        return float(score(self.state, np.asarray(u, float), tau=0.0, weights=self.weights))

    def _u(self, z: np.ndarray) -> np.ndarray:
        return self.lo + z * self.span

    def _starts(self, cz: np.ndarray, budget_z: float) -> list:
        k = int(self.active.sum())
        starts = [np.zeros_like(cz)]
        even = np.where(self.active, 1.0, 0.0)
        starts.append(even * min(1.0, budget_z / max(cz @ even, 1e-12)))
        for j in np.flatnonzero(self.active):  # single-lever corners
            e = np.zeros_like(cz)
            e[j] = 1.0 if cz[j] == 0 else min(1.0, budget_z / cz[j])
            starts.append(e)
        return starts[: max(self.n_starts, 2 + k)]

    # ------------------------------------------------------------ problem 1
    def maximize_score(self, budget: float) -> Prescription:
        """Budget problem: best exact score reachable with cost <= budget."""
        if budget < 0:
            raise ValueError("budget must be non-negative")
        cz = self.c * self.span  # cost per unit of z
        bz = budget - self.c @ self.lo
        best_u, best_s = np.zeros(len(LEVERS)), self.baseline
        for z0 in self._starts(cz, bz):
            z = project_box_budget(np.where(self.active, z0, 0.0), cz, bz)
            m = np.zeros_like(z)
            v = np.zeros_like(z)
            for it in range(1, self.steps + 1):
                _, g = self._grad(z)
                g = np.where(self.active, np.asarray(g), 0.0)
                m = 0.9 * m + 0.1 * g
                v = 0.999 * v + 0.001 * g * g
                step = self.lr * (m / (1 - 0.9**it)) / (np.sqrt(v / (1 - 0.999**it)) + 1e-12)
                z = project_box_budget(np.where(self.active, z + step, 0.0), cz, bz)
                if it % self.check_every == 0 or it == self.steps:
                    u = self._u(z)
                    s = self.exact_score(u)
                    if s > best_s + 1e-12 or (np.isclose(s, best_s) and self.state.cost(u) < self.state.cost(best_u)):
                        best_u, best_s = u.copy(), s
        best_u = self._trim(best_u, best_s)
        return self._prescription(best_u, budget)

    def _trim(self, u: np.ndarray, s_target: float, tol: float = 1e-4) -> np.ndarray:
        """Remove wasted spending: scale each lever down while the exact score stays within tol."""
        u = u.copy()
        for j in np.argsort(-self.c * u):
            if u[j] <= 0:
                continue
            lo, hi = 0.0, u[j]
            for _ in range(30):
                mid = 0.5 * (lo + hi)
                trial = u.copy()
                trial[j] = mid
                if self.exact_score(trial) >= s_target - tol:
                    hi = mid
                else:
                    lo = mid
            u[j] = hi
        return u

    def _prescription(self, u: np.ndarray, budget: Optional[float]) -> Prescription:
        a = audit(self.state, u, budget)
        return Prescription(self.state.cell_id, budget, u, a["cost"], a["score"], self.baseline, a)

    # ------------------------------------------------------------ problem 2
    def min_cost_for_target(self, target: float, rel_tol: float = 0.01, max_iter: int = 20) -> dict:
        """Target problem via bisection on the budget of the budget problem."""
        if self.baseline >= target:
            return {"feasible": True, "prescription": self._prescription(np.zeros(len(LEVERS)), 0.0), "note": "already meets target"}
        u_max = self.hi.copy()
        s_max = self.exact_score(u_max)
        if s_max < target:
            return {
                "feasible": False,
                "max_achievable_score": s_max,
                "note": "target unreachable within physical bounds",
            }
        lo, hi = 0.0, self.state.cost(u_max)
        best = self._prescription(u_max, hi)
        for _ in range(max_iter):
            if hi - lo <= rel_tol * hi:
                break
            mid = 0.5 * (lo + hi)
            p = self.maximize_score(mid)
            if p.score >= target:
                hi, best = min(mid, p.cost), p
            else:
                lo = mid
        best_u = self._trim(best.u, target, tol=0.0)
        return {"feasible": True, "prescription": self._prescription(best_u, None), "budget_bracket": (lo, hi)}

    # ------------------------------------------------------------ problem 3
    def pareto_curve(self, budgets: Sequence[float]) -> pd.DataFrame:
        """Improvement-cost curve: best exact score for each budget level."""
        rows = []
        best_so_far = None
        for b in sorted(budgets):
            p = self.maximize_score(b)
            if best_so_far is not None and best_so_far.score > p.score and best_so_far.cost <= b:
                p = best_so_far  # enforce monotonicity: a cheaper solution is still affordable
            best_so_far = p
            rows.append(p.as_dict())
        df = pd.DataFrame(rows)
        df["marginal_score_per_1k"] = df["score"].diff() / (df["budget"].diff() / 1000.0)
        return df

    # ------------------------------------------------------------ XAI
    def marginal_value(self, u=None, step_frac: float = 0.02) -> pd.Series:
        """XAI: exact score gain per 1000 € spent on each lever at ``u`` (default: today).

        Computed with one-sided *exact* finite differences, not with the smooth
        gradient: at kinks (e.g. a battery with no PV surplus) the relaxation
        produces phantom sensitivities, which must never reach an explanation.
        """
        u = np.zeros(len(LEVERS)) if u is None else np.asarray(u, float)
        s0 = self.exact_score(u)
        out = np.full(len(LEVERS), np.nan)
        for j in range(len(LEVERS)):
            if self.span[j] <= 0 or self.c[j] <= 0:
                continue
            h = step_frac * self.span[j]
            if u[j] + h <= self.hi[j]:
                trial = u.copy()
                trial[j] += h
                ds = self.exact_score(trial) - s0
            else:
                trial = u.copy()
                trial[j] -= h
                ds = s0 - self.exact_score(trial)
            out[j] = ds / (h * self.c[j]) * 1000.0
        return pd.Series(out, index=[f"{k}_per_1k_eur" for k in LEVERS])

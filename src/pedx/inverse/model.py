"""Physics-coupled intervention model for one cell (K-016).

Decision variables are *physical interventions*, never criteria values:

======  ============================  ======  =====================================
lever   meaning                       unit    effect on the hourly energy balance
======  ============================  ======  =====================================
``pv``       added PV panel area          m²      ``G_t += y_t * pv`` (y = specific yield)
``retrofit`` envelope retrofit depth      [0,1]*  ``D_t -= retrofit * H_t`` (H = envelope-
                                                  sensitive *electric* load: cooling, heat pumps)
``storage``  battery capacity             kWh     hourly state-of-charge dispatch (below)
``shift``    functional load conversion   [0,1]*  ``D_t <- (1-s) D_t + s * shape_t * ΣD``
======  ============================  ======  =====================================

(*) bounded by the cell's physical/planning limits.

All criteria (balance, SSR, peak relief) are *outputs* of the same hourly
energy equations, so every prescription is energy-consistent by construction.

Battery: greedy self-consumption dispatch, the standard rule in the PV
self-consumption literature (Luthander et al., 2015):

    charge_t    = min(surplus_t,  P_max, (C - soc_t) / η_c)
    discharge_t = min(deficit_t,  P_max, soc_t * η_d)
    soc_{t+1}   = soc_t + η_c charge_t - discharge_t / η_d

``P_max = c_rate * C * dt``, ``η_c = η_d = sqrt(η_rt)``. NumPy evaluation is
exact (hard ``min``); JAX evaluation uses the soft minimum with temperature
``tau`` and is used *only* to compute search directions. Every reported
result is re-evaluated with the exact model (:func:`audit`).

Note (Istanbul context): most space heating in the existing stock is not
electric, so ``H_t`` (envelope-sensitive electric load) is often small;
insulation then barely changes the *electric* PED balance. This is physics,
not a bug: do not credit gas savings to an electricity balance (docs/08).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np

from .._backend import get_xp, smooth_min, smooth_relu
from ..energy.load_match import cvar_top
from ..index.readiness import ENERGY_VALUES, energy_score

__all__ = ["LEVERS", "CellState", "simulate", "score", "audit"]

LEVERS = ("pv", "retrofit", "storage", "shift")


@dataclass
class CellState:
    cell_id: str
    pv_yield_kwh_per_m2: np.ndarray  # (T,) specific yield per m² of panel per step
    base_generation_kwh: np.ndarray  # (T,)
    base_demand_kwh: np.ndarray  # (T,)
    envelope_load_kwh: Optional[np.ndarray] = None  # (T,) part of D reducible by retrofit
    shift_shape: Optional[np.ndarray] = None  # (T,) target shape for converted load, sums to 1
    upper: Dict[str, float] = field(default_factory=dict)  # per-lever upper bounds
    unit_cost: Dict[str, float] = field(default_factory=dict)  # € per unit of each lever
    dt_hours: float = 1.0
    battery_rt_efficiency: float = 0.90
    battery_c_rate: float = 0.5
    cvar_q: float = 0.99

    def __post_init__(self) -> None:
        T = np.asarray(self.base_demand_kwh).size
        for name in ("pv_yield_kwh_per_m2", "base_generation_kwh", "base_demand_kwh"):
            arr = np.asarray(getattr(self, name), float).ravel()
            if arr.size != T or np.any(arr < 0):
                raise ValueError(f"{name} must be a non-negative array of length {T}")
            setattr(self, name, arr)
        if self.envelope_load_kwh is None:
            self.envelope_load_kwh = np.zeros(T)
        self.envelope_load_kwh = np.asarray(self.envelope_load_kwh, float).ravel()
        if np.any(self.envelope_load_kwh > self.base_demand_kwh + 1e-9) or np.any(self.envelope_load_kwh < 0):
            raise ValueError("envelope_load_kwh must satisfy 0 <= H_t <= D_t")
        if self.shift_shape is not None:
            s = np.asarray(self.shift_shape, float).ravel()
            if s.size != T or np.any(s < 0) or not np.isclose(s.sum(), 1.0):
                raise ValueError("shift_shape must be non-negative and sum to 1")
            self.shift_shape = s
        for lever in self.upper:
            if lever not in LEVERS:
                raise ValueError(f"unknown lever {lever!r}")
        if self.upper.get("retrofit", 0) > 1 or self.upper.get("shift", 0) > 1:
            raise ValueError("retrofit and shift upper bounds must be <= 1")
        if self.upper.get("shift", 0) > 0 and self.shift_shape is None:
            raise ValueError("shift lever needs shift_shape")
        if not 0 < self.battery_rt_efficiency <= 1:
            raise ValueError("battery_rt_efficiency must be in (0, 1]")

    @property
    def lower_vec(self) -> np.ndarray:
        return np.zeros(len(LEVERS))

    @property
    def upper_vec(self) -> np.ndarray:
        return np.array([float(self.upper.get(k, 0.0)) for k in LEVERS])

    @property
    def cost_vec(self) -> np.ndarray:
        return np.array([float(self.unit_cost.get(k, 0.0)) for k in LEVERS])

    def cost(self, u) -> float:
        return float(np.dot(self.cost_vec, np.asarray(u, float)))


# ---------------------------------------------------------------- battery
def _battery_numpy(surplus, deficit, cap, p_max, eta):
    T = surplus.size
    ch = np.zeros(T)
    dis = np.zeros(T)
    soc_hist = np.zeros(T + 1)
    soc = 0.0
    for t in range(T):
        c = min(surplus[t], p_max, (cap - soc) / eta)
        c = max(c, 0.0)
        soc += eta * c
        d = min(deficit[t], p_max, soc * eta)
        d = max(d, 0.0)
        soc -= d / eta
        ch[t], dis[t] = c, d
        soc_hist[t + 1] = soc
    return ch, dis, soc_hist


def _battery_jax(surplus, deficit, cap, p_max, eta, tau):
    import jax
    import jax.numpy as jnp

    def step(soc, x):
        s, d = x
        c = smooth_relu(smooth_min(smooth_min(s, p_max, tau), (cap - soc) / eta, tau), tau)
        soc = soc + eta * c
        out = smooth_relu(smooth_min(smooth_min(d, p_max, tau), soc * eta, tau), tau)
        soc = soc - out / eta
        return soc, (c, out, soc)

    soc_end, (ch, dis, soc) = jax.lax.scan(step, jnp.zeros(()), (surplus, deficit))
    return ch, dis, jnp.concatenate([jnp.zeros((1,)), soc])


# ---------------------------------------------------------------- simulation
def simulate(state: CellState, u, tau: float = 0.0) -> dict:
    """Hourly energy flows and indicators after applying interventions ``u``.

    ``u`` = [pv m², retrofit, storage kWh, shift]. With a NumPy ``u`` and
    ``tau == 0`` the result is exact; with a JAX ``u`` the computation is
    differentiable (use ``tau > 0`` for informative gradients).
    """
    xp = get_xp(u)
    u = u if xp is not np else np.asarray(u, float)
    pv, retro, cap, shift = u[0], u[1], u[2], u[3]
    y = xp.asarray(state.pv_yield_kwh_per_m2)
    G = xp.asarray(state.base_generation_kwh) + pv * y
    D0 = xp.asarray(state.base_demand_kwh) - retro * xp.asarray(state.envelope_load_kwh)
    if state.shift_shape is not None:
        D = (1.0 - shift) * D0 + shift * xp.asarray(state.shift_shape) * D0.sum()
    else:
        D = D0
    direct = smooth_min(G, D, tau)
    surplus = smooth_relu(G - direct, tau) if tau else G - direct
    deficit = smooth_relu(D - direct, tau) if tau else D - direct
    eta = float(np.sqrt(state.battery_rt_efficiency))
    p_max = state.battery_c_rate * cap * state.dt_hours
    if xp is np:
        ch, dis, soc = _battery_numpy(surplus, deficit, float(cap), float(p_max), eta)
    else:
        ch, dis, soc = _battery_jax(surplus, deficit, cap, p_max, eta, tau)
    imp = deficit - dis
    exp_ = surplus - ch
    sc = direct + dis
    tg, td = G.sum(), D.sum()
    cvar_imp = cvar_top(imp, state.cvar_q)
    cvar_d = cvar_top(D, state.cvar_q)
    ind = {
        "balance": tg / td,
        "ssr": sc.sum() / td,
        "peak_relief": 1.0 - cvar_imp / cvar_d,
        "generation_kwh": tg,
        "demand_kwh": td,
        "self_consumed_kwh": sc.sum(),
        "grid_import_kwh": imp.sum(),
        "grid_export_kwh": exp_.sum(),
    }
    return {
        "indicators": ind,
        "flows": {
            "G": G, "D": D, "direct": direct, "charge": ch, "discharge": dis,
            "import": imp, "export": exp_, "soc": soc,
        },
    }


def score(state: CellState, u, tau: float = 0.0, sharpness: float = 0.0, weights=None):
    """Absolute energy readiness score of the cell after interventions ``u``."""
    from ..index.readiness import energy_values

    ind = simulate(state, u, tau)["indicators"]
    return energy_score(energy_values(ind, sharpness), weights)


def audit(state: CellState, u, budget: Optional[float] = None, atol: float = 1e-6) -> dict:
    """Independent exact re-simulation and physical checks of a prescription.

    Independent of the search: uses the exact NumPy model (hard min, exact
    battery), recomputes indicators from flows, and checks bounds, budget,
    per-hour energy conservation and state-of-charge limits.
    """
    u = np.asarray(u, float)
    res = simulate(state, u, tau=0.0)
    f = res["flows"]
    eta = np.sqrt(state.battery_rt_efficiency)
    checks = {
        "within_bounds": bool(np.all(u >= -atol) and np.all(u <= state.upper_vec + atol)),
        "within_budget": True if budget is None else bool(state.cost(u) <= budget * (1 + 1e-9) + atol),
        "generation_conserved": bool(np.allclose(f["G"], f["direct"] + f["charge"] + f["export"], atol=atol)),
        "demand_conserved": bool(np.allclose(f["D"], f["direct"] + f["discharge"] + f["import"], atol=atol)),
        "flows_non_negative": bool(
            min(f["charge"].min(), f["discharge"].min(), f["import"].min(), f["export"].min()) >= -atol
        ),
        "soc_within_capacity": bool(f["soc"].min() >= -atol and f["soc"].max() <= u[2] + atol),
        "storage_balance": bool(
            np.isclose(f["soc"][-1], eta * f["charge"].sum() - f["discharge"].sum() / eta, atol=1e-6 * max(1.0, u[2]))
        ),
    }
    ind = res["indicators"]
    from ..index.readiness import energy_values

    exact_score = float(energy_score(energy_values(ind)))
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "score": exact_score,
        "cost": state.cost(u),
        "indicators": {k: float(v) for k, v in ind.items()},
        "values": {k: float(v) for k, v in energy_values(ind).items() if k in ENERGY_VALUES},
    }

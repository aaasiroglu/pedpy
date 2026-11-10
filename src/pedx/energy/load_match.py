"""Hourly load-matching indicators (Salom et al., 2014; Luthander et al., 2015).

All functions accept arrays of shape ``(T,)`` or batches ``(..., T)`` (e.g.
``(n_cells, T)``) of energy per time step [kWh], and work with NumPy (exact)
or JAX (differentiable) arrays.

Definitions (``E_sc`` self-consumed, ``I`` import, ``X`` export):

* ``E_sc,t = min(G_t, D_t)``, ``I_t = D_t - E_sc,t``, ``X_t = G_t - E_sc,t``
* annual balance        ``B   = sum G / sum D``          (PED condition: B >= 1)
* self-sufficiency      ``SSR = sum E_sc / sum D``
* self-consumption      ``SCR = sum E_sc / sum G``        (NaN without generation)
* grid stress           ``GS  = CVaR_q(I) / mean(D)``     (mean of the top (1-q) import hours)
* peak relief           ``PR  = 1 - CVaR_q(I) / CVaR_q(D)``  in [0, 1]

``CVaR_q`` (mean of the highest ``ceil((1-q) T)`` values) replaces the single
maximum used in earlier drafts: it is robust to one outlier hour and convex.
``PR`` is scale-free and needs no arbitrary anchor: it is the share of the
stress-hour load that local generation removes (0 = none, 1 = all).

With ``tau > 0`` the ``min`` is replaced by a soft minimum (see
:mod:`pedx._backend`); results then differ from the exact ones by a provable
bound, and become differentiable.
"""

from __future__ import annotations

import math

import numpy as np

from .._backend import get_xp, smooth_min

__all__ = ["hourly_flows", "cvar_top", "load_match"]


def hourly_flows(generation_kwh, demand_kwh, tau: float = 0.0) -> dict:
    """Per-step self-consumption, import and export (exact if ``tau == 0``)."""
    xp = get_xp(generation_kwh, demand_kwh)
    g = generation_kwh if xp is not np else np.asarray(generation_kwh, dtype=float)
    d = demand_kwh if xp is not np else np.asarray(demand_kwh, dtype=float)
    if g.shape != d.shape:
        raise ValueError(f"generation {g.shape} and demand {d.shape} shapes differ")
    if xp is np and (np.any(g < 0) or np.any(d < 0)):
        raise ValueError("generation and demand must be non-negative")
    sc = smooth_min(g, d, tau)
    return {"self_consumed_kwh": sc, "grid_import_kwh": d - sc, "grid_export_kwh": g - sc}


def cvar_top(x, q: float = 0.99):
    """Mean of the top ``ceil((1-q) * T)`` values along the last axis."""
    if not 0.0 <= q < 1.0:
        raise ValueError("q must be in [0, 1)")
    xp = get_xp(x)
    n = x.shape[-1]
    k = max(1, int(math.ceil((1.0 - q) * n - 1e-9)))
    return xp.sort(x, axis=-1)[..., n - k :].mean(axis=-1)


def _div(num, den, xp):
    if xp is np:
        num = np.asarray(num, dtype=float)
        den = np.asarray(den, dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            out = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
        return out if out.ndim else float(out)
    safe = xp.where(den > 0, den, 1.0)
    return xp.where(den > 0, num / safe, xp.nan)


def load_match(
    generation_kwh,
    demand_kwh,
    dt_hours: float = 1.0,
    tau: float = 0.0,
    cvar_q: float = 0.99,
    self_consumed_kwh=None,
) -> dict:
    """Load-matching indicators for one node or a batch of nodes.

    ``self_consumed_kwh`` can be passed when sharing is restricted (e.g. the
    sum of building-level self-consumption inside a cell); otherwise it is
    ``min(G_t, D_t)`` at the node level.
    """
    xp = get_xp(generation_kwh, demand_kwh)
    flows = hourly_flows(generation_kwh, demand_kwh, tau)
    g = generation_kwh if xp is not np else np.asarray(generation_kwh, dtype=float)
    d = demand_kwh if xp is not np else np.asarray(demand_kwh, dtype=float)
    sc = flows["self_consumed_kwh"] if self_consumed_kwh is None else self_consumed_kwh
    imp = d - sc
    exp_ = g - sc
    tg, td, tsc = g.sum(-1), d.sum(-1), sc.sum(-1)
    n_steps = d.shape[-1]
    mean_d_kw = td / (n_steps * dt_hours)
    cvar_imp_kw = cvar_top(imp, cvar_q) / dt_hours
    cvar_d_kw = cvar_top(d, cvar_q) / dt_hours
    return {
        "generation_kwh": tg,
        "demand_kwh": td,
        "self_consumed_kwh": tsc,
        "grid_import_kwh": imp.sum(-1),
        "grid_export_kwh": exp_.sum(-1),
        "balance": _div(tg, td, xp),
        "ssr": _div(tsc, td, xp),
        "scr": _div(tsc, tg, xp),
        "grid_stress": _div(cvar_imp_kw, mean_d_kw, xp),
        "peak_relief": 1.0 - _div(cvar_imp_kw, cvar_d_kw, xp),
        "cvar_import_kw": cvar_imp_kw,
    }

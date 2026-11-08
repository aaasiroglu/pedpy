"""Hourly load-matching indicators (Salom et al., 2014).

Definitions used throughout ``pedpy`` (energies in kWh per time step):

* self-consumed energy   ``E_sc,t = min(G_t, D_t)``
* grid import            ``I_t = max(D_t - G_t, 0)``
* grid export            ``X_t = max(G_t - D_t, 0)``
* Self-Sufficiency Ratio ``SSR = sum(E_sc) / sum(D)``         (NaN if no demand)
* Self-Consumption Ratio ``SCR = sum(E_sc) / sum(G)``         (NaN if no generation)
* Peak-to-Average grid-draw Ratio
  ``PAR = max_t(I_t / dt) / (sum(D) / (T * dt))`` – the peak grid import power
  divided by the mean demand power. It is dimensionless, ``>= 0`` and a cost
  criterion; ``PAR = 0`` when the PV system covers every hour.

Energy conservation holds per step: ``G = E_sc + X`` and ``D = E_sc + I``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["LoadMatchResult", "hourly_flows", "load_match_indicators"]


@dataclass(frozen=True)
class LoadMatchResult:
    total_generation_kwh: float
    total_demand_kwh: float
    self_consumed_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    ssr: float
    scr: float
    par: float
    peak_import_kw: float

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def hourly_flows(generation_kwh: np.ndarray, demand_kwh: np.ndarray) -> dict:
    """Return per-step self-consumption, import and export arrays."""
    g = np.asarray(generation_kwh, dtype=float)
    d = np.asarray(demand_kwh, dtype=float)
    if g.shape != d.shape:
        raise ValueError(f"generation {g.shape} and demand {d.shape} shapes differ")
    if np.any(g < 0) or np.any(d < 0):
        raise ValueError("generation and demand must be non-negative")
    sc = np.minimum(g, d)
    return {
        "self_consumed_kwh": sc,
        "grid_import_kwh": d - sc,
        "grid_export_kwh": g - sc,
    }


def _ratio(num: float, den: float) -> float:
    return float(num / den) if den > 0 else float("nan")


def load_match_indicators(
    generation_kwh: np.ndarray,
    demand_kwh: np.ndarray,
    dt_hours: float = 1.0,
    self_consumed_kwh: np.ndarray | None = None,
) -> LoadMatchResult:
    """Compute SSR, SCR and PAR for one energy node (building, block, cluster).

    ``self_consumed_kwh`` may be supplied when sharing is restricted (e.g.
    building-level self-consumption summed over a block); otherwise it is
    ``min(G_t, D_t)``.
    """
    g = np.asarray(generation_kwh, dtype=float)
    d = np.asarray(demand_kwh, dtype=float)
    flows = hourly_flows(g, d)
    sc = flows["self_consumed_kwh"] if self_consumed_kwh is None else np.asarray(self_consumed_kwh, float)
    imp = d - sc
    exp = g - sc
    tg, td, tsc = float(g.sum()), float(d.sum()), float(sc.sum())
    peak_import_kw = float(imp.max() / dt_hours) if imp.size else 0.0
    mean_demand_kw = td / (d.size * dt_hours) if d.size else 0.0
    par = _ratio(peak_import_kw, mean_demand_kw)
    return LoadMatchResult(
        total_generation_kwh=tg,
        total_demand_kwh=td,
        self_consumed_kwh=tsc,
        grid_import_kwh=float(imp.sum()),
        grid_export_kwh=float(exp.sum()),
        ssr=_ratio(tsc, td),
        scr=_ratio(tsc, tg),
        par=par,
        peak_import_kw=peak_import_kw,
    )

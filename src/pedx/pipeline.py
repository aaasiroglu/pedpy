"""v0 end-to-end pipeline: OSM buildings → hourly energy → H3 cells → index → XAI → graph → inverse.

Two scenarios are always kept apart:

* ``current``   – today's installed PV (OSM rarely maps it, so usually 0)
* ``potential`` – technical potential: PV on all usable roof area

The *readiness* ranking uses the potential scenario (where could a PED
work?); the *inverse* analysis starts from the current scenario (what must be
built, at what cost?).

Every constant comes from :mod:`pedx.assumptions`; every imputation is flagged
in the returned data-quality report. Hourly demand shapes in v0 are SYNTHETIC
(:mod:`pedx.synthetic`) until real profiles are available (docs/07, C1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from .assumptions import DEFAULTS, Assumption, table
from .energy import BuildingEnergyRecord, CellEnergy, aggregate_to_cells
from .graph import grow_ped_boundary, shapley_self_consumption
from .index import contributions, energy_score, energy_values, rank_intervals
from .spatial import cell_adjacency
from .synthetic import day_shape, demand_profile

__all__ = ["USAGE_MAP", "records_from_osm", "cell_state", "assess", "V0Result"]

USAGE_MAP = {
    "residential": "residential", "apartments": "residential", "house": "residential", "detached": "residential",
    "terrace": "residential", "dormitory": "residential", "yes": "residential",
    "commercial": "office", "office": "office", "retail": "office", "public": "office", "school": "office",
    "university": "office", "hospital": "office", "civic": "office", "government": "office", "hotel": "office",
}


def _a(assumptions: Mapping[str, Assumption], key: str) -> float:
    return float(assumptions[key].value)


def records_from_osm(
    buildings: pd.DataFrame,
    irradiance_kw_m2: np.ndarray,
    scenario: str = "potential",
    assumptions: Mapping[str, Assumption] = DEFAULTS,
) -> tuple[List[BuildingEnergyRecord], pd.DataFrame]:
    """Building records from a parsed OSM table (:func:`pedx.ingest.parse_buildings`)."""
    if scenario not in ("current", "potential"):
        raise ValueError("scenario must be 'current' or 'potential'")
    df = buildings.copy()
    df = df[df["footprint_area_m2"] > 10].reset_index(drop=True)
    known = df["levels"].dropna()
    median_levels = float(known.median()) if len(known) else 1.0
    df["levels_imputed"] = df["levels"].isna()
    df["levels_used"] = df["levels"].fillna(median_levels).clip(lower=1)
    df["usage"] = df["building"].map(USAGE_MAP).fillna("residential")
    df["floor_area_m2"] = df["footprint_area_m2"] * df["levels_used"]
    intensity = df["usage"].map(
        {"residential": _a(assumptions, "intensity_residential_kwh_m2"), "office": _a(assumptions, "intensity_office_kwh_m2")}
    )
    df["annual_demand_kwh"] = df["floor_area_m2"] * intensity
    df["usable_roof_m2"] = df["footprint_area_m2"] * _a(assumptions, "roof_utilization")
    eta, pr = _a(assumptions, "pv_efficiency"), _a(assumptions, "performance_ratio")
    n = len(irradiance_kw_m2)
    recs = []
    for r in df.itertuples():
        pv_area = r.usable_roof_m2 if scenario == "potential" else 0.0
        recs.append(
            BuildingEnergyRecord.from_irradiance(
                r.osm_id, r.lat, r.lon, irradiance_kw_m2,
                demand_profile(r.annual_demand_kwh, r.usage, n_hours=n),
                footprint_area_m2=r.footprint_area_m2, usable_roof_area_m2=r.usable_roof_m2,
                installed_pv_area_m2=pv_area, pv_efficiency=eta, performance_ratio=pr,
                usage_type=r.usage, height_m=r.height_m,
            )
        )
    quality = pd.Series(
        {
            "n_buildings": len(df),
            "share_levels_imputed": float(df["levels_imputed"].mean()) if len(df) else np.nan,
            "median_levels_used": median_levels,
            "share_height_missing": float((df["height_source"] == "missing").mean()) if len(df) else np.nan,
            "share_start_year_known": float(df["start_year"].notna().mean()) if len(df) else np.nan,
            "demand_profiles": "SYNTHETIC (pedx.synthetic.day_shape)",
            "shading": "not modelled in v0 (s_t = 1)",
        }
    )
    return recs, quality.to_frame("value")


def cell_state(cells_current: CellEnergy, cell: str, irradiance_kw_m2: np.ndarray, assumptions: Mapping[str, Assumption] = DEFAULTS):
    """Inverse-analysis state of one cell (current scenario) with bounds and costs from assumptions."""
    from .inverse import CellState

    i = cells_current.index[cell]
    attrs = cells_current.attributes.loc[cell]
    D = cells_current.demand_kwh[i]
    T = D.size
    roof_free = max(float(attrs["usable_roof_area_m2"] - attrs["installed_pv_area_m2"]), 0.0)
    footprint = float(attrs["footprint_area_m2"])
    envelope_m2 = 2.0 * footprint + 4.0 * np.sqrt(max(footprint, 1.0)) * 3.0 * 4  # square plan, ~4 floors: v0 proxy
    max_depth = _a(assumptions, "max_retrofit_depth")
    shape = np.tile(day_shape("office"), T // 24 + 1)[:T]
    return CellState(
        cell,
        pv_yield_kwh_per_m2=np.asarray(irradiance_kw_m2) * _a(assumptions, "pv_efficiency") * _a(assumptions, "performance_ratio"),
        base_generation_kwh=cells_current.generation_kwh[i],
        base_demand_kwh=D,
        envelope_load_kwh=_a(assumptions, "envelope_share_of_electric_demand") * D,
        shift_shape=shape / shape.sum(),
        upper={
            "pv": roof_free,
            "retrofit": max_depth,
            "storage": _a(assumptions, "storage_kwh_per_m2_roof") * float(attrs["usable_roof_area_m2"]),
            "shift": _a(assumptions, "max_shift"),
        },
        unit_cost={
            "pv": _a(assumptions, "cost_pv_eur_m2"),
            "storage": _a(assumptions, "cost_storage_eur_kwh"),
            "retrofit": _a(assumptions, "cost_retrofit_eur_m2_envelope") * envelope_m2 / max_depth,
            "shift": _a(assumptions, "cost_shift_eur_per_frac"),
        },
        cvar_q=_a(assumptions, "cvar_q"),
    )


@dataclass
class V0Result:
    scores: pd.DataFrame
    rank_uncertainty: pd.DataFrame
    contributions: pd.DataFrame
    boundary_path: pd.DataFrame
    boundary_cells: List[str]
    shapley: pd.DataFrame
    prescriptions: pd.DataFrame
    data_quality: pd.DataFrame
    assumptions: pd.DataFrame = field(default_factory=table)


def assess(
    buildings: pd.DataFrame,
    irradiance_kw_m2: np.ndarray,
    resolution: int = 10,
    weights: Optional[Dict[str, float]] = None,
    max_cluster: int = 8,
    n_prescribe: int = 3,
    budgets: Sequence[float] = (0, 25_000, 50_000, 100_000, 200_000),
    assumptions: Mapping[str, Assumption] = DEFAULTS,
    inverse_steps: int = 60,
) -> V0Result:
    recs_pot, quality = records_from_osm(buildings, irradiance_kw_m2, "potential", assumptions)
    recs_cur, _ = records_from_osm(buildings, irradiance_kw_m2, "current", assumptions)
    cells_pot = aggregate_to_cells(recs_pot, resolution=resolution)
    cells_cur = aggregate_to_cells(recs_cur, resolution=resolution)

    m = cells_pot.metrics("shared", cvar_q=_a(assumptions, "cvar_q"))
    vals = pd.DataFrame(energy_values(m), index=m.index)
    m = m.join(vals)
    m["readiness"] = energy_score(vals, weights)
    m = m.sort_values("readiness", ascending=False)
    ranks = rank_intervals(vals.loc[m.index], weights)
    contrib = contributions(vals.loc[m.index], weights)

    adj = cell_adjacency(cells_pot.cell_ids)
    seed = m.index[0]
    growth = grow_ped_boundary(cells_pot, adj, seed, max_cells=max_cluster, readiness=m["readiness"].to_dict())
    members = list(growth.path["added"])
    sub = cells_pot.subset(members)
    shap = shapley_self_consumption(sub.generation_kwh, sub.demand_kwh, members)

    rows = []
    if n_prescribe > 0:
        from .inverse import InverseEngine

        for cell in list(m.index[-n_prescribe:]):
            st = cell_state(cells_cur, cell, irradiance_kw_m2, assumptions)
            eng = InverseEngine(st, weights=weights, steps=inverse_steps)
            curve = eng.pareto_curve(list(budgets))
            mv = eng.marginal_value()
            for k, v in mv.items():
                curve[k] = v
            rows.append(curve)
    prescriptions = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    return V0Result(m, ranks, contrib, growth.path, growth.ped_cells, shap, prescriptions, quality, table())

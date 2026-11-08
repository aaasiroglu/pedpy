"""Core criteria C1-C6 and helpers to compute the non-energy criteria.

=====  =======================================  ===========  ===================
Code   Criterion                                Direction    Unit / range
=====  =======================================  ===========  ===================
C1     Roof PV yield                            benefit      kWh/m²/year
C2     Self-sufficiency ratio (SSR)             benefit      [0, 1]
C3     Peak-to-average grid draw (PAR)          cost         >= 0
C4     Function diversity (Shannon, normalised) benefit*     [0, 1]
C5     Thermal retrofit proxy index             cost         [0, 1]
C6     Energy infrastructure accessibility      benefit      (0, 1]
=====  =======================================  ===========  ===================

(*) C4 is a *conditional* benefit: mixed use helps load complementarity, but
it should be interpreted together with C2/C3.
"""

from __future__ import annotations

from typing import Mapping, Optional, Sequence

import numpy as np

__all__ = [
    "CRITERIA",
    "CRITERIA_COLUMNS",
    "IS_BENEFIT",
    "shannon_diversity",
    "thermal_retrofit_proxy",
    "infrastructure_accessibility",
]

CRITERIA = {
    "C1_pv_yield": {"name": "Roof PV yield", "benefit": True, "unit": "kWh/m2/yr"},
    "C2_ssr": {"name": "Self-sufficiency ratio", "benefit": True, "unit": "-"},
    "C3_par": {"name": "Peak-to-average grid draw ratio", "benefit": False, "unit": "-"},
    "C4_div": {"name": "Function diversity", "benefit": True, "unit": "-"},
    "C5_therm": {"name": "Thermal retrofit proxy", "benefit": False, "unit": "-"},
    "C6_infra": {"name": "Energy infrastructure accessibility", "benefit": True, "unit": "-"},
}
CRITERIA_COLUMNS = list(CRITERIA)
IS_BENEFIT = [CRITERIA[c]["benefit"] for c in CRITERIA_COLUMNS]


def shannon_diversity(counts: Sequence[float] | Mapping[str, float], n_categories: Optional[int] = None) -> float:
    """Normalised Shannon entropy ``H = -sum p ln p / ln(K)`` in [0, 1].

    ``K`` is ``n_categories`` if given (recommended: the size of the full
    land-use / POI taxonomy, so blocks are comparable), else ``len(counts)``.
    """
    vals = np.asarray(list(counts.values()) if isinstance(counts, Mapping) else counts, dtype=float)
    if np.any(vals < 0):
        raise ValueError("counts must be non-negative")
    k = int(n_categories) if n_categories is not None else vals.size
    if k < vals[vals > 0].size:
        raise ValueError("n_categories is smaller than the number of observed categories")
    total = vals.sum()
    if total <= 0 or k <= 1:
        return 0.0
    p = vals[vals > 0] / total
    return float(-(p * np.log(p)).sum() / np.log(k))


def thermal_retrofit_proxy(
    construction_year: Optional[float],
    av_ratio: Optional[float],
    reference_year: int = 2026,
    age_span_years: float = 100.0,
    av_max: float = 1.2,
    age_weight: float = 0.6,
) -> float:
    """Retrofit-need proxy in [0, 1] (higher = more retrofit needed, cost).

    Combines normalised building age and compactness (A/V, envelope area per
    heated volume). Missing inputs fall back to the available component; if
    both are missing ``NaN`` is returned.
    """
    parts, weights = [], []
    if construction_year is not None and np.isfinite(construction_year):
        parts.append(np.clip((reference_year - construction_year) / age_span_years, 0.0, 1.0))
        weights.append(age_weight)
    if av_ratio is not None and np.isfinite(av_ratio):
        parts.append(np.clip(av_ratio / av_max, 0.0, 1.0))
        weights.append(1.0 - age_weight)
    if not parts:
        return float("nan")
    return float(np.dot(parts, weights) / np.sum(weights))


DEFAULT_DECAY_M = {"transformer": 300.0, "ev_charger": 500.0, "transit": 400.0}


def infrastructure_accessibility(
    distances_m: Mapping[str, float],
    decay_m: Optional[Mapping[str, float]] = None,
    weights: Optional[Mapping[str, float]] = None,
) -> float:
    """Exponential-decay accessibility ``sum w_k exp(-d_k / d0_k)`` in (0, 1].

    ``distances_m`` maps an infrastructure type (e.g. ``transformer``,
    ``ev_charger``, ``transit``) to the network/Euclidean distance in metres.
    """
    decay = dict(DEFAULT_DECAY_M)
    if decay_m:
        decay.update(decay_m)
    keys = list(distances_m)
    if not keys:
        raise ValueError("distances_m is empty")
    w = np.array([1.0 if weights is None else float(weights[k]) for k in keys])
    w = w / w.sum()
    d = np.array([float(distances_m[k]) for k in keys])
    if np.any(d < 0):
        raise ValueError("distances must be non-negative")
    d0 = np.array([decay.get(k, 400.0) for k in keys])
    return float(np.dot(w, np.exp(-d / d0)))

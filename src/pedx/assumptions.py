"""Single table of every numeric assumption used by the v0 pipeline (K-012).

Rule: each constant has a unit, a source and a status. ``status`` is one of

* ``kaynakli``       – taken from a cited source
* ``varsayim``       – placeholder; MUST be replaced (İBB data, Demirel et al.
                       2025, TABULA, literature) and enters sensitivity analysis

The pipeline never uses a constant that is not listed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd

__all__ = ["Assumption", "DEFAULTS", "table"]


@dataclass(frozen=True)
class Assumption:
    value: float
    unit: str
    source: str
    status: str
    note: str = ""


DEFAULTS: Dict[str, Assumption] = {
    "pv_efficiency": Assumption(0.20, "-", "tipik mono-Si modül verimi; kaynak eklenecek", "varsayim"),
    "performance_ratio": Assumption(0.80, "-", "PR literatür aralığı ~0.75–0.85; kaynak eklenecek", "varsayim"),
    "roof_utilization": Assumption(0.50, "-", "Demirel vd. (2025) 3B çatı analizinden türetilecek", "varsayim",
                                   "sonuçlara doğrusal etki eder; duyarlılık analizinde"),
    "level_height_m": Assumption(3.0, "m", "OSM building:levels → yükseklik dönüşümünde yaygın kabul", "varsayim"),
    "intensity_residential_kwh_m2": Assumption(30.0, "kWh/m² kat alanı/yıl", "İBB / Hande Hoca verisiyle değiştirilecek", "varsayim",
                                               "yalnızca elektrik; ısıtma çoğunlukla doğalgaz"),
    "intensity_office_kwh_m2": Assumption(80.0, "kWh/m² kat alanı/yıl", "İBB / literatür ile değiştirilecek", "varsayim"),
    "envelope_share_of_electric_demand": Assumption(0.10, "-", "soğutma payı; İstanbul için kaynak gerekli", "varsayim",
                                                    "ısı pompası senaryosunda artar"),
    "cost_pv_eur_m2": Assumption(220.0, "€/m² panel", "Türkiye piyasa verisi ile değiştirilecek", "varsayim"),
    "cost_storage_eur_kwh": Assumption(350.0, "€/kWh", "piyasa verisi ile değiştirilecek", "varsayim"),
    "cost_retrofit_eur_m2_envelope": Assumption(60.0, "€/m² kabuk (tam derinlik)", "Bakanlık birim fiyatları ile değiştirilecek", "varsayim"),
    "cost_shift_eur_per_frac": Assumption(5.0e5, "€/(kaydırılan talep oranı)", "kaynak yok — yalnızca senaryo", "varsayim"),
    "max_retrofit_depth": Assumption(0.35, "-", "kullanıcı önerisi [0, 0.35]; kaynak gerekli", "varsayim"),
    "max_shift": Assumption(0.20, "-", "kullanıcı önerisi [0, 0.20]; kaynak gerekli", "varsayim"),
    "storage_kwh_per_m2_roof": Assumption(0.5, "kWh/m² kullanılabilir çatı", "üst sınır ölçeği; kaynak gerekli", "varsayim"),
    "cvar_q": Assumption(0.99, "-", "üst %1 saat; K-021", "varsayim"),
}


def table() -> pd.DataFrame:
    return pd.DataFrame({k: vars(v) for k, v in DEFAULTS.items()}).T.rename_axis("assumption")

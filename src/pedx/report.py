"""Comprehensive site report for a clicked hexagon / candidate site (K-051): PED + urban transformation.

Every metric is computed on the site disc (k = 2 H3 r10 cells ≈ 28 ha) from the city grid and is
shown with its percentile inside the city, so a planner reads "high/low for this city", not raw
numbers that differ by country. Groups follow the questions of an urban-transformation brief.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

__all__ = ["REPORT", "report_metrics"]

# key, label (tr), unit, section, literature anchor
REPORT: List[Dict[str, str]] = [
    {"key": "energy_balance", "label": "Yıllık konut elektriği dengesi", "unit": "PV/talep", "section": "Enerji ve PED", "ref": "Salom vd. 2014"},
    {"key": "footprint_per_capita_m2", "label": "Kişi başı çatı tabanı", "unit": "m²/kişi", "section": "Enerji ve PED", "ref": ""},
    {"key": "pop_density_per_ha", "label": "Nüfus yoğunluğu", "unit": "kişi/ha", "section": "Nüfus ve kırılganlık", "ref": "Meta HRSL"},
    {"key": "elderly_share", "label": "60+ payı", "unit": "%", "section": "Nüfus ve kırılganlık", "ref": "Meta HRSL"},
    {"key": "children_share", "label": "0–5 yaş payı", "unit": "%", "section": "Nüfus ve kırılganlık", "ref": "Meta HRSL"},
    {"key": "places_density_ha", "label": "Mekân yoğunluğu", "unit": "adet/ha", "section": "Kentsel işlev", "ref": "Overture"},
    {"key": "mix_entropy", "label": "İşlev karışımı (Shannon)", "unit": "0–1", "section": "Kentsel işlev", "ref": "Jacobs 1961"},
    {"key": "daily_per_1000", "label": "Günlük ihtiyaç (market, bakkal)", "unit": "/1000 kişi", "section": "Kentsel işlev", "ref": "Moreno vd. 2021"},
    {"key": "retail_ha", "label": "Perakende", "unit": "/ha", "section": "Kentsel işlev", "ref": ""},
    {"key": "office_ha", "label": "Ofis ve profesyonel hizmet", "unit": "/ha", "section": "Ekonomik ve finansal yapı", "ref": ""},
    {"key": "finance_ha", "label": "Finans ve emlak", "unit": "/ha", "section": "Ekonomik ve finansal yapı", "ref": ""},
    {"key": "crafts_ha", "label": "Zanaat, tamir, üretim hizmeti", "unit": "/ha", "section": "Ekonomik ve finansal yapı", "ref": ""},
    {"key": "tourism_ha", "label": "Turizm ve konaklama", "unit": "/ha", "section": "Ekonomik ve finansal yapı", "ref": ""},
    {"key": "social_infra_per_1000", "label": "Sosyal altyapı", "unit": "/1000 kişi", "section": "Sosyal yapı, eğitim, kültür", "ref": "Klinenberg 2018"},
    {"key": "education_per_1000", "label": "Eğitim", "unit": "/1000 kişi", "section": "Sosyal yapı, eğitim, kültür", "ref": ""},
    {"key": "health_per_1000", "label": "Sağlık", "unit": "/1000 kişi", "section": "Sosyal yapı, eğitim, kültür", "ref": ""},
    {"key": "culture_ha", "label": "Kültür, sanat, miras", "unit": "/ha", "section": "Sosyal yapı, eğitim, kültür", "ref": "Florida 2002"},
    {"key": "faith_ha", "label": "İnanç mekânları", "unit": "/ha", "section": "Sosyal yapı, eğitim, kültür", "ref": ""},
    {"key": "third_places_per_1000", "label": "Üçüncü mekânlar (kafe, çay evi)", "unit": "/1000 kişi", "section": "Mekânın ruhu", "ref": "Oldenburg 1989"},
    {"key": "night_ha", "label": "Gece yaşamı", "unit": "/ha", "section": "Mekânın ruhu", "ref": ""},
    {"key": "attention_ha", "label": "Kolektif dikkat (Wikidata bağlantıları)", "unit": "/ha", "section": "Mekânın ruhu", "ref": "Norberg-Schulz 1980"},
    {"key": "photos_ha", "label": "Fotoğraflanmış önemli yer (Wikidata P18; Commons varsa eklenir)", "unit": "/ha", "section": "Mekânın ruhu", "ref": "Seresinhe vd. 2017"},
    {"key": "plaza_m2_per_1000", "label": "Meydan ve yaya alanı", "unit": "m²/1000 kişi", "section": "Mekânın ruhu", "ref": "Gehl 2010"},
    {"key": "heritage_n", "label": "Miras öğesi (Overture + Wikidata)", "unit": "adet", "section": "Mekânın ruhu", "ref": ""},
    {"key": "green_share", "label": "Yeşil alan payı (WorldCover)", "unit": "%", "section": "Çevre", "ref": "ESA WorldCover"},
    {"key": "env_ndvi_mean", "label": "NDVI", "unit": "-", "section": "Çevre", "ref": "Sentinel-2"},
    {"key": "env_lst_anomaly_c", "label": "Yaz yüzey sıcaklığı anomalisi", "unit": "°C", "section": "Çevre", "ref": "Landsat"},
    {"key": "water_share", "label": "Su yüzeyi payı", "unit": "%", "section": "Çevre", "ref": "ESA WorldCover"},
    {"key": "env_slope_deg", "label": "Eğim", "unit": "°", "section": "Çevre", "ref": "Copernicus DEM"},
    {"key": "transit_per_km2", "label": "Toplu taşıma durağı (OSM)", "unit": "/km²", "section": "Altyapı", "ref": "OSM"},
    {"key": "grid_assets_per_km2", "label": "Trafo ve şebeke varlığı", "unit": "/km²", "section": "Altyapı", "ref": "Overture"},
    {"key": "ev_chargers_per_km2", "label": "EV şarj noktası", "unit": "/km²", "section": "Altyapı", "ref": "Overture"},
    {"key": "footprint_coverage", "label": "Yapı örtüsü", "unit": "%", "section": "Kentsel dönüşüm", "ref": ""},
    {"key": "construction_share", "label": "Aktif inşaat alanı payı", "unit": "%", "section": "Kentsel dönüşüm", "ref": "Overture land_use"},
    {"key": "residential_share", "label": "Konut arazisi payı", "unit": "%", "section": "Kentsel dönüşüm", "ref": "Overture land_use"},
    {"key": "nonosm_share", "label": "OSM dışı bina payı (veri boşluğu)", "unit": "%", "section": "Kentsel dönüşüm", "ref": "Overture"},
    {"key": "nres_share", "label": "Konut dışı yapı yüzeyi payı (GHSL)", "unit": "%", "section": "Kentsel dönüşüm", "ref": "Pesaresi vd. 2024"},
    {"key": "special_share", "label": "Özel arazi payı (havalimanı, sanayi, liman, askeri; OSM)", "unit": "%", "section": "Kentsel dönüşüm", "ref": "OSM"},
]
GROUPS = ["pl_arts", "pl_crafts", "pl_culture", "pl_daily", "pl_education", "pl_faith", "pl_finance", "pl_food", "pl_health", "pl_heritage",
          "pl_night", "pl_office", "pl_park", "pl_personal", "pl_public", "pl_retail", "pl_social", "pl_sport", "pl_third", "pl_tourism"]


def report_metrics(C: pd.DataFrame, area_ha: float) -> pd.DataFrame:
    """Report metrics from candidate disc aggregates (pedx.score.candidate_discs output)."""
    g = lambda c: C[c] if c in C else pd.Series(0.0, index=C.index)  # noqa: E731
    P = g("vul_pop_hrsl").where(g("vul_pop_hrsl") > 0)
    k1000 = 1000 / P
    out = pd.DataFrame(index=C.index)
    for c in ("energy_balance", "footprint_per_capita_m2", "pop_density_per_ha", "env_ndvi_mean", "env_lst_anomaly_c", "env_slope_deg",
              "transit_per_km2", "grid_assets_per_km2", "ev_chargers_per_km2"):
        out[c] = g(c)
    out["elderly_share"] = 100 * g("elderly_share")
    out["children_share"] = 100 * g("children_share")
    G = pd.DataFrame({c: g(c) for c in GROUPS})
    tot = G.sum(axis=1)
    out["places_density_ha"] = tot / area_ha
    p = G.div(tot.where(tot > 0), axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        out["mix_entropy"] = -(p * np.log(p.where(p > 0))).sum(axis=1, min_count=1) / np.log(len(GROUPS))
    out["daily_per_1000"] = g("pl_daily") * k1000
    out["retail_ha"] = g("pl_retail") / area_ha
    out["office_ha"] = g("pl_office") / area_ha
    out["finance_ha"] = g("pl_finance") / area_ha
    out["crafts_ha"] = g("pl_crafts") / area_ha
    out["tourism_ha"] = g("pl_tourism") / area_ha
    out["social_infra_per_1000"] = (g("pl_social") + g("pl_public") + g("pl_education") + g("pl_health") + g("pl_faith") + g("pl_park")) * k1000
    out["education_per_1000"] = g("pl_education") * k1000
    out["health_per_1000"] = g("pl_health") * k1000
    out["culture_ha"] = (g("pl_culture") + g("pl_heritage") + g("pl_arts")) / area_ha
    out["faith_ha"] = g("pl_faith") / area_ha
    out["third_places_per_1000"] = g("pl_third") * k1000
    out["night_ha"] = g("pl_night") / area_ha
    out["attention_ha"] = g("wd_sitelinks") / area_ha
    out["photos_ha"] = (g("wd_photo_n") + g("cm_photos_n")) / area_ha
    out["plaza_m2_per_1000"] = g("lu_plaza_m2") * k1000
    out["heritage_n"] = g("pl_heritage") + g("wd_heritage_n")
    out["green_share"] = 100 * g("env_wc_green_share")
    out["water_share"] = 100 * g("env_wc_water_share")
    out["footprint_coverage"] = 100 * g("footprint_coverage")
    m2 = area_ha * 1e4
    out["construction_share"] = 100 * g("lu_construction_m2") / m2
    out["residential_share"] = 100 * g("lu_residential_m2") / m2
    out["nonosm_share"] = 100 * g("ov_nonosm_share")
    out["nres_share"] = 100 * g("ghsl_nres_m2") / g("ghsl_built_m2").where(g("ghsl_built_m2") > 0)
    out["special_share"] = 100 * g("osm_special").fillna(0.0)
    return out[[r["key"] for r in REPORT]]

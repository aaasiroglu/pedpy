"""Feature catalogue of the H3 hex feature store (data contract, K-029).

Every feature that can ever appear in the store is declared here with its
family, unit, source, licence, role (G1 input / G2 validation) and status.
The store refuses columns that are not declared (no undocumented data).

Families mirror the questions of a PED-formation / urban-transformation study:
energy, built form, demography, POI (urban function), economy, mobility,
environment, climate. "Even weakly related" layers are welcome — but they are
registered, licensed and versioned, and the modelling layer must treat them
with grouped validation and multiple-testing control (docs/13, §6).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List

import pandas as pd

__all__ = ["FeatureSpec", "CATALOG", "FAMILIES", "catalog_frame", "spec"]

FAMILIES = {
    "energy": "Enerji",
    "built": "Yapılı çevre",
    "demography": "Demografi",
    "poi": "POI / kentsel işlev",
    "economy": "Ekonomi",
    "mobility": "Ulaşım",
    "environment": "Çevre",
    "climate": "İklim",
}


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    family: str
    label_tr: str
    unit: str
    source: str
    license: str
    status: str = "active"  # active | planned
    role: str = "G1"
    note: str = ""


_OSM = ("OpenStreetMap (Overpass)", "ODbL 1.0")
_GHS = ("JRC GHS-POP R2023A E2020 3″", "CC BY 4.0")
_POI_FAMS = {
    "food_drink": "Yeme-içme", "retail": "Perakende", "health": "Sağlık", "education": "Eğitim",
    "finance": "Finans", "leisure_culture": "Eğlence / kültür", "office_business": "Ofis / iş",
    "tourism": "Turizm / konaklama", "public_civic": "Kamu / sivil", "transport": "Ulaşım hizmeti",
    "religion": "İbadet", "street_furniture": "Kent mobilyası", "craft": "Zanaat", "other": "Diğer",
}

_ACTIVE: List[FeatureSpec] = [
    # energy (annual, global open)
    FeatureSpec("energy_demand_res_kwh", "energy", "Konut elektriği talebi", "kWh/yıl", "GHS-POP × UNSD hane tüketimi / UN nüfusu (2023)", "CC BY 4.0; UNdata"),
    FeatureSpec("energy_pv_kwh", "energy", "Çatı PV potansiyeli", "kWh/yıl", "OSM taban alanı × parametreler × PVGIS 5.3 (2023)", "ODbL; AB"),
    FeatureSpec("energy_balance", "energy", "Yıllık denge (PV/talep)", "-", "türetilmiş", "-"),
    FeatureSpec("energy_balance_low", "energy", "Yıllık denge, alt senaryo", "-", "türetilmiş", "-"),
    FeatureSpec("energy_balance_high", "energy", "Yıllık denge, üst senaryo", "-", "türetilmiş", "-"),
    FeatureSpec("energy_roof_share_needed", "energy", "Denge = 1 için gereken çatı payı", "-", "türetilmiş (tersine, fiziksel)", "-"),
    FeatureSpec("energy_pv_kwp", "energy", "PV kurulu güç potansiyeli", "kWp", "türetilmiş", "-"),
    FeatureSpec("xai_logbal_built", "energy", "XAI: dengeye yapı (taban alanı) katkısı", "log birim", "kesin ayrıştırma: Δln B = Δln A − Δln P", "-",
                note="Mahalle ortalamasına göre; toplamı Δln(denge)"),
    FeatureSpec("xai_logbal_population", "energy", "XAI: dengeye nüfus katkısı", "log birim", "kesin ayrıştırma", "-"),
    # built form (OSM)
    FeatureSpec("built_n_buildings", "built", "Bina sayısı", "adet", *_OSM),
    FeatureSpec("built_footprint_m2", "built", "Toplam taban alanı", "m²", *_OSM),
    FeatureSpec("built_coverage", "built", "Taban alanı / hücre alanı", "-", *_OSM),
    FeatureSpec("built_mean_footprint_m2", "built", "Ortalama bina taban alanı", "m²", *_OSM),
    FeatureSpec("built_levels_known_share", "built", "Kat bilgisi olan bina payı (OSM tamlığı)", "-", *_OSM),
    FeatureSpec("built_mean_levels", "built", "Ortalama kat (bilinenler)", "kat", *_OSM),
    FeatureSpec("built_share_residential", "built", "Konut etiketli taban alanı payı", "-", *_OSM),
    FeatureSpec("built_share_nonresidential", "built", "Konut dışı etiketli taban alanı payı", "-", *_OSM),
    FeatureSpec("built_share_untyped", "built", "Türü belirsiz ('yes') taban alanı payı", "-", *_OSM),
    # demography
    FeatureSpec("demo_population", "demography", "Nüfus", "kişi", *_GHS),
    FeatureSpec("demo_density_per_ha", "demography", "Nüfus yoğunluğu", "kişi/ha", *_GHS),
    FeatureSpec("demo_m2_footprint_per_capita", "demography", "Kişi başı taban alanı", "m²/kişi", "OSM + GHS-POP", "ODbL; CC BY 4.0"),
    # POI
    FeatureSpec("poi_total", "poi", "POI sayısı", "adet", *_OSM),
    FeatureSpec("poi_density_per_ha", "poi", "POI yoğunluğu", "adet/ha", *_OSM),
    FeatureSpec("poi_diversity", "poi", "POI çeşitliliği (normalize Shannon)", "0–1", *_OSM),
    FeatureSpec("poi_per_1000_pop", "poi", "1000 kişi başına POI", "adet", "OSM + GHS-POP", "ODbL; CC BY 4.0"),
    FeatureSpec("poi_daytime_share", "poi", "Gündüz işlevli POI payı (perakende, ofis, sağlık, eğitim, finans)", "-", *_OSM,
                note="Yük tamamlayıcılığı için vekil gösterge; gündüz ve gece işlev dengesi"),
    FeatureSpec("poi_night_share", "poi", "Akşam ve gece işlevli POI payı (bar, pub, gece kulübü, restoran)", "-", *_OSM),
] + [
    FeatureSpec(f"poi_n_{k}", "poi", f"POI: {v}", "adet", *_OSM) for k, v in _POI_FAMS.items()
]

_PLANNED: List[FeatureSpec] = [
    FeatureSpec("econ_gdp_ppp", "economy", "Izgara GSYH (SGP)", "USD", "Kummu vd. 2018, Dryad doi:10.5061/dryad.dk1j0 (30″/5′)", "CC0 1.0 (2018 sürümü)", "planned"),
    FeatureSpec("econ_hdi", "economy", "İnsani Gelişme Endeksi", "0–1", "Kummu vd. 2018 (5′)", "CC0 1.0", "planned"),
    FeatureSpec("econ_gdp_1km", "economy", "1 km gerçek GSYH (gece ışığına kalibre)", "USD", "Chen vd. 2022, figshare doi:10.6084/m9.figshare.17004523", "lisans teyit edilecek", "planned"),
    FeatureSpec("econ_elec_1km", "economy", "1 km elektrik tüketimi (gece ışığına kalibre)", "kWh", "Chen vd. 2022", "lisans teyit edilecek", "planned",
                note="Talep modelinin bağımsız G1 sınaması"),
    FeatureSpec("econ_poi_commercial_intensity", "economy", "Ticari yoğunluk (POI tabanlı vekil)", "adet/ha", "OSM", "ODbL", "planned"),
    FeatureSpec("built_nres_surface_m2", "built", "Konut dışı yapı alanı", "m²", "JRC GHS-BUILT-S NRES R2023A", "AB yeniden kullanımı (teyit)", "planned"),
    FeatureSpec("built_height_m", "built", "Ortalama yapı yüksekliği", "m", "JRC GHS-BUILT-H R2023A (100 m)", "AB yeniden kullanımı (teyit)", "planned"),
    FeatureSpec("built_volume_m3", "built", "Yapı hacmi", "m³", "JRC GHS-BUILT-V R2023A", "AB yeniden kullanımı (teyit)", "planned"),
    FeatureSpec("demo_age_65plus_share", "demography", "65 yaş üstü payı", "-", "WorldPop yaş ve cinsiyet yapısı", "CC BY 4.0", "planned"),
    FeatureSpec("mob_transit_stops", "mobility", "Toplu taşıma durağı sayısı", "adet", "OSM public_transport", "ODbL", "planned"),
    FeatureSpec("mob_road_density", "mobility", "Yol yoğunluğu", "km/km²", "OSM highway", "ODbL", "planned"),
    FeatureSpec("mob_ev_chargers", "mobility", "EV şarj noktası", "adet", "OSM amenity=charging_station", "ODbL", "planned"),
    FeatureSpec("env_green_share", "environment", "Yeşil alan payı", "-", "ESA WorldCover 10 m", "CC BY 4.0", "planned"),
    FeatureSpec("env_slope_deg", "environment", "Eğim", "°", "Copernicus DEM GLO-30", "Copernicus lisansı", "planned"),
    FeatureSpec("clim_hdd", "climate", "Isıtma derece-gün", "°C·gün", "ERA5 (Open-Meteo veya PVGIS T2m)", "Copernicus lisansı", "planned"),
    FeatureSpec("clim_cdd", "climate", "Soğutma derece-gün", "°C·gün", "ERA5", "Copernicus lisansı", "planned"),
    FeatureSpec("energy_grid_substations", "energy", "Trafo merkezi yakınlığı", "m", "OSM power=substation", "ODbL", "planned"),
]

CATALOG: Dict[str, FeatureSpec] = {f.name: f for f in _ACTIVE + _PLANNED}
POI_FAMILY_LABELS = _POI_FAMS


def spec(name: str) -> FeatureSpec:
    if name not in CATALOG:
        raise KeyError(f"feature {name!r} is not registered in the catalogue (docs/13 data contract)")
    return CATALOG[name]


def catalog_frame() -> pd.DataFrame:
    return pd.DataFrame([asdict(f) for f in CATALOG.values()]).set_index("name")

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
    "morphology": "Kentsel morfoloji",
    "imagery": "Uydu ve sokak görüntüsü",
    "social": "Sosyal",
    "embedding": "Gömme (tüm katmanlar, PCA)",
    "vulnerability": "Kırılganlık ve afete direnç",
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
_HRSL = ("Meta Data for Good HRSL demografik haritaları (1″, COG/AWS)", "CC BY 4.0")
_GHSL_T = ("JRC GHS-BUILT-S R2023A çok zamanlı (E1975/E1990/E2000/E2020)", "CC BY 4.0")
_OV_B = ("Overture Maps buildings (sürüm overture.RELEASE)", "ODbL 1.0")
_OV_P = ("Overture Maps places (Meta, Foursquare OS Places, Microsoft, AllThePlaces)", "CDLA-Permissive-2.0")
_OV_TOP = {
    "food_and_drink": "Yeme-içme", "shopping": "Alışveriş", "services_and_business": "Hizmet ve iş", "education": "Eğitim",
    "lifestyle_services": "Kişisel hizmet", "arts_and_entertainment": "Sanat ve eğlence", "community_and_government": "Toplum ve kamu",
    "health_care": "Sağlık", "travel_and_transportation": "Seyahat ve ulaşım", "sports_and_recreation": "Spor ve rekreasyon",
    "lodging": "Konaklama", "cultural_and_historic": "Kültür ve tarih", "geographic_entities": "Coğrafi öğe",
}
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
    FeatureSpec("morph_shared_wall_ratio", "morphology", "Ortak duvar oranı (bitişik nizam)", "-", "OSM + momepy (Fleischmann 2019); 0,3 m tolerans", "ODbL; BSD-3",
                note="Isı kaybı ve kabuk alanı için fiziksel gösterge"),
    FeatureSpec("morph_perimeter_area_ratio", "morphology", "Çevre / alan oranı (kabuk kompaktlığı, 2B)", "1/m", "OSM + momepy", "ODbL; BSD-3"),
    FeatureSpec("morph_compactness_mean", "morphology", "Ortalama dairesel kompaktlık", "0–1", "OSM + momepy", "ODbL; BSD-3"),
    FeatureSpec("morph_elongation_mean", "morphology", "Ortalama uzama", "0–1", "OSM + momepy", "ODbL; BSD-3"),
    FeatureSpec("morph_rectangularity_mean", "morphology", "Ortalama dikdörtgensellik", "0–1", "OSM + momepy", "ODbL; BSD-3"),
    FeatureSpec("morph_corners_mean", "morphology", "Ortalama köşe sayısı", "adet", "OSM + momepy", "ODbL; BSD-3"),
    FeatureSpec("morph_orientation_std", "morphology", "Yönelim sapması (ızgara düzensizliği)", "°", "OSM + momepy", "ODbL; BSD-3",
                note="Çatı azimutu dağılımı → PV verimi değişkenliği"),
] + [
    FeatureSpec("ghsl_built_surface_m2", "built", "Yapı alanı (GHSL)", "m²", "GHS-BUILT-S E2020", "CC BY 4.0"),
    FeatureSpec("ghsl_nres_surface_m2", "built", "Konut dışı yapı alanı (GHSL)", "m²", "GHS-BUILT-S NRES E2020", "CC BY 4.0"),
    FeatureSpec("ghsl_nres_share", "built", "Konut dışı yapı payı (GHSL)", "-", "GHS-BUILT-S NRES / S", "CC BY 4.0",
                note="Zemin kat ticareti gibi karma kullanımı eksik sayar (POI ile karşılaştırın)"),
    FeatureSpec("ghsl_volume_m3", "built", "Yapı hacmi (GHSL)", "m³", "GHS-BUILT-V E2020", "CC BY 4.0"),
    FeatureSpec("ghsl_nres_volume_m3", "built", "Konut dışı yapı hacmi (GHSL)", "m³", "GHS-BUILT-V NRES E2020", "CC BY 4.0"),
    FeatureSpec("ghsl_mean_height_m", "built", "Ortalama yapı yüksekliği (hacim/alan, GHSL)", "m", "GHS-BUILT-V / GHS-BUILT-S", "CC BY 4.0"),
    FeatureSpec("ghsl_agbh_m", "built", "Ortalama brüt bina yüksekliği (AGBH, GHSL)", "m", "GHS-BUILT-H AGBH E2018", "CC BY 4.0"),
    FeatureSpec("osm_vs_ghsl_surface", "built", "OSM taban alanı / GHSL yapı alanı (OSM tamlığı)", "-", "OSM + GHS-BUILT-S", "ODbL; CC BY 4.0",
                note="1'in altı: OSM'de eksik bina; G1 içi çapraz kontrol"),
] + [
    FeatureSpec("env_lst_mean_c", "environment", "Yaz yüzey sıcaklığı (LST) ortalaması", "°C", *('Landsat 8/9 C2 L2 ST, Haz–Eyl 2023, bulut < %20 (Planetary Computer)', 'USGS kamu malı'), note="Hava sıcaklığı değil; yüzey sıcaklığı"),
    FeatureSpec("env_lst_std_c", "environment", "LST hücre içi sapma (ısıl doku)", "°C", *('Landsat 8/9 C2 L2 ST, Haz–Eyl 2023, bulut < %20 (Planetary Computer)', 'USGS kamu malı')),
    FeatureSpec("env_lst_anomaly_c", "environment", "LST anomalisi (mahalle ortancasına göre)", "°C", *('Landsat 8/9 C2 L2 ST, Haz–Eyl 2023, bulut < %20 (Planetary Computer)', 'USGS kamu malı'),
                note="Mahalle içi anomali; kırsal referanslı SUHII kent ölçeğinde hesaplanacak"),
    FeatureSpec("env_ndvi_mean", "environment", "NDVI ortalaması (bitki örtüsü)", "-", *('Sentinel-2 L2A, en az bulutlu Haz–Eyl 2023 sahnesi (Earth Search)', 'Copernicus açık')),
    FeatureSpec("env_ndvi_std", "environment", "NDVI hücre içi sapma (yeşil doku)", "-", *('Sentinel-2 L2A, en az bulutlu Haz–Eyl 2023 sahnesi (Earth Search)', 'Copernicus açık')),
    FeatureSpec("env_ndbi_mean", "environment", "NDBI ortalaması (yapılaşma)", "-", *('Sentinel-2 L2A, en az bulutlu Haz–Eyl 2023 sahnesi (Earth Search)', 'Copernicus açık')),
    FeatureSpec("env_elev_m", "environment", "Ortalama yükseklik", "m", *('Copernicus DEM GLO-30 (AWS)', 'Copernicus DEM lisansı')),
    FeatureSpec("env_slope_deg", "environment", "Ortalama eğim", "°", *('Copernicus DEM GLO-30 (AWS)', 'Copernicus DEM lisansı')),
    FeatureSpec("env_relief_m", "environment", "Yükseklik sapması (rölyef)", "m", *('Copernicus DEM GLO-30 (AWS)', 'Copernicus DEM lisansı')),
    FeatureSpec("mob_orientation_entropy", "mobility", "Sokak yönelim entropisi", "nat", "OSM; Boeing 2019", "ODbL"),
    FeatureSpec("mob_orientation_order", "mobility", "Sokak yönelim düzeni φ (1 = ızgara)", "0–1", "OSM; Boeing 2019", "ODbL"),
    FeatureSpec("mob_circuity", "mobility", "Sokak dolambaçlılığı (yol/düz mesafe)", "-", "OSM", "ODbL"),
    FeatureSpec("mob_deadend_share", "mobility", "Çıkmaz sokak payı", "-", "OSM", "ODbL"),
    FeatureSpec("mob_streets_per_node", "mobility", "Düğüm başına sokak", "-", "OSM", "ODbL"),
] + [
    FeatureSpec(f"emb_pca_{i}", "embedding", f"Hücre imzası, {i}. bileşen (PCA)", "-", "Tüm G1 özellikleri, standartlaştırılmış", "türetilmiş",
                note="Yorum için bileşen yükleri: Veri ve yöntem bölümü") for i in range(1, 6)
] + [
    FeatureSpec("mob_walk800_pois", "mobility", "10 dk yürüme (800 m ağ) içinde POI", "adet", "OSM yaya ağı + POI; Dijkstra", "ODbL"),
    FeatureSpec("mob_walk800_daily_needs", "mobility", "10 dk yürümede günlük ihtiyaç POI'si", "adet", "OSM; aileler: yeme-içme, perakende, sağlık, eğitim, finans", "ODbL"),
    FeatureSpec("mob_walk800_daily_completeness", "mobility", "10 dk yürümede günlük ihtiyaç tamlığı (5 aile)", "0–1", "OSM ('15 dakika kenti' vekili)", "ODbL"),
    FeatureSpec("mob_walk800_transit_stops", "mobility", "10 dk yürümede toplu taşıma durağı", "adet", "OSM bus_stop, platform, istasyon, iskele", "ODbL"),
    FeatureSpec("mob_walk800_network_km", "mobility", "10 dk yürümede erişilen yaya ağı uzunluğu", "km", "OSM yaya ağı", "ODbL"),
    FeatureSpec("mob_street_density_km_per_km2", "mobility", "Yaya sokak yoğunluğu", "km/km²", "OSM highway (yaya erişimli)", "ODbL"),
    FeatureSpec("mob_intersection_density_per_km2", "mobility", "Kavşak yoğunluğu (derece ≥ 3)", "adet/km²", "OSM", "ODbL"),
] + [
    FeatureSpec(f"poi_n_{k}", "poi", f"POI: {v}", "adet", *_OSM) for k, v in _POI_FAMS.items()
] + [
    # ---- vulnerability & disaster resilience (K-039)
    FeatureSpec("vul_pop_hrsl", "vulnerability", "Nüfus (HRSL, ham toplam; G2 karşılaştırması için)", "kişi", *_HRSL,
                note="Caferağa'da TÜİK'e göre +%66; ticari çekirdekte yerleşim pikseline nüfus atar → nüfus tabanı GHS-POP kalır"),
    FeatureSpec("vul_elderly60_n", "vulnerability", "60 yaş ve üstü kişi", "kişi", *_HRSL, note="GHS-POP × HRSL payı"),
    FeatureSpec("vul_children0_5_n", "vulnerability", "0–5 yaş çocuk", "kişi", *_HRSL, note="GHS-POP × HRSL payı"),
    FeatureSpec("vul_youth15_24_n", "vulnerability", "15–24 yaş genç", "kişi", *_HRSL, note="GHS-POP × HRSL payı"),
    FeatureSpec("vul_women15_49_n", "vulnerability", "15–49 yaş kadın", "kişi", *_HRSL, note="GHS-POP × HRSL payı"),
    FeatureSpec("vul_elderly60_share", "vulnerability", "60+ payı", "-", *_HRSL, note="Sayım birimi içinde sabit (ilçe düzeyi oran)"),
    FeatureSpec("vul_children0_5_share", "vulnerability", "0–5 yaş payı", "-", *_HRSL, note="Sayım birimi içinde sabit"),
    FeatureSpec("vul_youth15_24_share", "vulnerability", "15–24 yaş payı", "-", *_HRSL, note="Sayım birimi içinde sabit"),
    FeatureSpec("vul_women15_49_share", "vulnerability", "15–49 yaş kadın payı", "-", *_HRSL, note="Sayım birimi içinde sabit"),
    FeatureSpec("vul_dependent_n", "vulnerability", "Bakıma bağımlı kişi (60+ ve 0–5)", "kişi", *_HRSL),
    FeatureSpec("vul_heat_exposed_vulnerable", "vulnerability", "Isıya maruz kırılgan nüfus (60+ ve 0–5 × LST anomalisi⁺)", "kişi·°C",
                "HRSL × Landsat C2 L2 LST", "CC BY 4.0 / kamu malı", note="Tehlike × maruziyet × duyarlılık (IPCC AR5); bileşik endeks değil"),
    FeatureSpec("vul_built_pre1975_share", "vulnerability", "2020 yapılı alanın 1975'te var olan payı", "-", *_GHSL_T,
                note="Kent dokusunun yaşı vekili; aynı parselde yeniden yapım görünmez"),
    FeatureSpec("vul_built_pre1990_share", "vulnerability", "2020 yapılı alanın 1990'da var olan payı", "-", *_GHSL_T),
    FeatureSpec("vul_built_pre2000_share", "vulnerability", "2020 yapılı alanın 2000'de var olan payı", "-", *_GHSL_T,
                note="Türkiye'de 1998/2007 deprem yönetmeliklerinden önceki doku vekili"),
    FeatureSpec("res_hospital_dist_m", "vulnerability", "En yakın hastaneye kuş uçuşu uzaklık", "m", *_OSM),
    FeatureSpec("res_fire_station_dist_m", "vulnerability", "En yakın itfaiyeye kuş uçuşu uzaklık", "m", *_OSM),
    FeatureSpec("res_assembly_point_dist_m", "vulnerability", "En yakın afet toplanma alanına uzaklık", "m", *_OSM,
                note="İstanbul'da OSM'de emergency=assembly_point yok → boş; İBB toplanma alanları G2"),
    FeatureSpec("res_health_within800", "vulnerability", "800 m içinde hastane/klinik", "adet", *_OSM),
    FeatureSpec("res_school_within800", "vulnerability", "800 m içinde okul/anaokulu", "adet", *_OSM),
    FeatureSpec("res_care_within800", "vulnerability", "800 m içinde sosyal tesis/huzurevi", "adet", *_OSM),
    # ---- Overture Maps (K-038)
    FeatureSpec("ov_bld_n", "built", "Bina sayısı (Overture)", "adet", *_OV_B),
    FeatureSpec("ov_bld_footprint_m2", "built", "Taban alanı (Overture)", "m²", *_OV_B),
    FeatureSpec("ov_height_coverage", "built", "Yükseklik bilgisi olan bina payı (Overture)", "-", *_OV_B),
    FeatureSpec("ov_floors_coverage", "built", "Kat bilgisi olan bina payı (Overture)", "-", *_OV_B),
    FeatureSpec("ov_height_mean_m", "built", "Alan ağırlıklı yükseklik (Overture)", "m", *_OV_B),
    FeatureSpec("ov_gfa_m2", "built", "Brüt kat alanı (kat ya da yükseklik/3 m bilinen binalar)", "m²", *_OV_B),
    FeatureSpec("ov_nonosm_share", "built", "OSM dışı (ML) taban alanı kaynağının payı", "-", *_OV_B,
                note="OSM eksikliğinin küresel göstergesi; Caferağa'da 0"),
    FeatureSpec("ov_places_n", "poi", "Mekân sayısı (Overture, güven ≥ 0,5)", "adet", *_OV_P),
    FeatureSpec("ov_places_categories", "poi", "Farklı mekân kategorisi sayısı (Overture)", "adet", *_OV_P),
] + [
    FeatureSpec(f"ov_places_{k}", "poi", f"Overture mekân: {v}", "adet", *_OV_P) for k, v in _OV_TOP.items()
]

_PLANNED: List[FeatureSpec] = [
    FeatureSpec("img_albedo_mean", "imagery", "Yüzey albedosu (çatı ve zemin)", "-", "Sentinel-2 / Landsat 8-9 (USGS, kamu malı)", "açık", "planned"),
    FeatureSpec("img_emb_pca_1", "imagery", "Uydu gömme vektörü, 1. bileşen (64-B AlphaEarth ya da açık temel model)", "-",
                "AlphaEarth Satellite Embedding (Earth Engine; lisans teyit) veya Clay/Prithvi + Sentinel-2", "teyit edilecek", "planned",
                note="Tam gömmeler ayrı bir vektör deposunda tutulur; tabloya PCA ile yorumlanabilir bileşenler girer"),
    FeatureSpec("img_svi_levels_est", "imagery", "Sokak görüntüsünden kat sayısı tahmini", "kat", "Mapillary (CC BY-SA 4.0), erişim anahtarı gerekli", "CC BY-SA 4.0", "planned",
                note="OSM'de %83 eksik olan kat bilgisini tamamlar → kat alanı ve talep"),
    FeatureSpec("img_svi_wwr_est", "imagery", "Cephe pencere/duvar oranı tahmini", "-", "Mapillary + segmentasyon modeli", "CC BY-SA 4.0", "planned"),
    FeatureSpec("soc_gdelt_energy_tone", "social", "Enerji ve iklim haberlerinin tonu", "-", "GDELT (açık)", "açık; teyit", "planned"),
    FeatureSpec("econ_gdp_ppp", "economy", "Izgara GSYH (SGP)", "USD", "Kummu vd. 2018, Dryad doi:10.5061/dryad.dk1j0 (30″/5′)", "CC0 1.0 (2018 sürümü)", "planned"),
    FeatureSpec("econ_hdi", "economy", "İnsani Gelişme Endeksi", "0–1", "Kummu vd. 2018 (5′)", "CC0 1.0", "planned"),
    FeatureSpec("econ_gdp_1km", "economy", "1 km gerçek GSYH (gece ışığına kalibre)", "USD", "Chen vd. 2022, figshare doi:10.6084/m9.figshare.17004523", "lisans teyit edilecek", "planned"),
    FeatureSpec("econ_elec_1km", "economy", "1 km elektrik tüketimi (gece ışığına kalibre)", "kWh", "Chen vd. 2022", "lisans teyit edilecek", "planned",
                note="Talep modelinin bağımsız G1 sınaması"),
    FeatureSpec("econ_poi_commercial_intensity", "economy", "Ticari yoğunluk (POI tabanlı vekil)", "adet/ha", "OSM", "ODbL", "planned"),
    FeatureSpec("mob_ev_chargers", "mobility", "EV şarj noktası", "adet", "OSM amenity=charging_station", "ODbL", "planned"),
    FeatureSpec("env_green_share", "environment", "Yeşil alan payı", "-", "ESA WorldCover 10 m", "CC BY 4.0", "planned"),
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

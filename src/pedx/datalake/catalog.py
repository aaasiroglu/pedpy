"""Global open geodata catalogue of the pedx data lake (K-035).

Design (docs/PROJE_DOSYASI.md §2): the lake does not copy "all data in the world". It holds a
catalogue of global raster/vector datasets with a connector per dataset; for an area of interest
(AOI) the connector fetches only the needed tile/window, caches it under data/raw, and the zonal
engine (pedx.datalake.raster) turns it into registered H3 features. Same code, any city.

status: ingested  – connector implemented and data in the Caferağa store
        connector – access verified, ingestion not yet wired
        planned   – licence/access to be confirmed
        rejected  – evaluated and excluded (licence/terms not open); kept so the decision is visible
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import List

import pandas as pd

__all__ = ["Dataset", "DATASETS", "catalog_frame"]


@dataclass(frozen=True)
class Dataset:
    id: str
    theme: str  # insan, bina, sokak, kent, enerji, cevre, iklim, ekonomi, sosyal, goruntu, ped
    kind: str  # raster | vector | table | timeseries
    provider: str
    resolution: str
    license: str
    access: str
    status: str
    pedx_use: str


DATASETS: List[Dataset] = [
    # ---- people
    Dataset("ghs_pop_2020", "insan", "raster", "JRC GHS-POP R2023A", "3″ (~90 m), 1975–2030", "CC BY 4.0", "jeodpp.jrc.ec.europa.eu tiles", "ingested", "demo_population"),
    Dataset("worldpop_agesex", "insan", "raster", "WorldPop", "100 m", "CC BY 4.0", "data.worldpop.org", "planned", "yaş yapısı (HRSL'ye alternatif)"),
    Dataset("meta_hrsl_demographic", "kirilganlik", "raster", "Meta Data for Good HRSL (genel, 60+, 0–5, 15–24, kadın 15–49)", "1″ (~30 m)", "CC BY 4.0", "AWS COG (dataforgood-fb-data/hrsl-cogs)", "ingested", "vul_* (yaşlı, çocuk, genç)"),
    Dataset("ghs_built_s_epochs", "kirilganlik", "raster", "JRC GHS-BUILT-S R2023A E1975/E1990/E2000", "3″", "CC BY 4.0", "jeodpp tiles", "ingested", "vul_built_pre*_share (doku yaşı)"),
    Dataset("osm_resilience", "kirilganlik", "vector", "OpenStreetMap (hastane, itfaiye, okul, bakım, toplanma alanı)", "nokta", "ODbL 1.0", "Overpass API", "ingested", "res_*"),
    Dataset("glofas_flood_hazard", "kirilganlik", "raster", "JRC GloFAS/CEMS taşkın tehlike haritaları (10–500 yıl)", "3″ (~90 m)", "kısıtsız (JRC)", "data.jrc.ec.europa.eu", "planned", "taşkın derinliği"),
    Dataset("gem_seismic_hazard", "kirilganlik", "raster", "GEM Global Seismic Hazard Map (PGA, 475 yıl)", "~1 km", "CC BY-NC-SA 4.0 (ticari kullanım anlaşmayla)", "globalquakemodel.org", "planned", "deprem tehlikesi (akademik)"),
    Dataset("ibb_assembly_points", "kirilganlik", "vector", "İBB Açık Veri: afet toplanma alanları", "nokta", "İBB Açık Veri Lisansı", "data.ibb.gov.tr", "planned", "yalnız G2 doğrulama (OSM'de yok)"),
    Dataset("ghs_smod", "kent", "raster", "JRC GHS-SMOD R2023A", "1 km", "CC BY 4.0", "jeodpp", "planned", "kentsel/kırsal derece"),
    # ---- buildings
    Dataset("osm_buildings", "bina", "vector", "OpenStreetMap", "poligon", "ODbL 1.0", "Overpass API", "ingested", "built_*, morph_*"),
    Dataset("ghs_built_s_2020", "bina", "raster", "JRC GHS-BUILT-S R2023A (toplam)", "3″", "CC BY 4.0", "jeodpp tiles", "ingested", "ghsl_built_surface_m2"),
    Dataset("ghs_built_s_nres_2020", "bina", "raster", "JRC GHS-BUILT-S NRES R2023A", "3″", "CC BY 4.0", "jeodpp tiles", "ingested", "ghsl_nres_surface_m2"),
    Dataset("ghs_built_v_2020", "bina", "raster", "JRC GHS-BUILT-V R2023A (toplam)", "3″", "CC BY 4.0", "jeodpp tiles", "ingested", "ghsl_volume_m3"),
    Dataset("ghs_built_v_nres_2020", "bina", "raster", "JRC GHS-BUILT-V NRES R2023A", "3″", "CC BY 4.0", "jeodpp tiles", "ingested", "ghsl_nres_volume_m3"),
    Dataset("ghs_built_h_agbh_2018", "bina", "raster", "JRC GHS-BUILT-H AGBH R2023A", "3″", "CC BY 4.0", "jeodpp tiles", "ingested", "ghsl_height_m"),
    Dataset("overture_buildings", "bina", "vector", "Overture Maps buildings (OSM + Microsoft/Google ML + Esri)", "poligon + yükseklik/kat", "ODbL 1.0", "S3 GeoParquet (satır grubu indeksi)", "ingested", "ov_bld_*, ov_nonosm_share; tıkla→hesapla taban alanı"),
    Dataset("ms_buildings", "bina", "vector", "Microsoft Global ML Building Footprints", "poligon", "ODbL", "GitHub / Planetary Computer", "planned", "taban alanı tamlığı"),
    Dataset("google_open_buildings", "bina", "vector", "Google Open Buildings (2.5D Temporal)", "poligon / 4 m", "CC BY 4.0 / ODbL", "GCS", "planned", "yükseklik (kapsam teyit)"),
    # ---- streets & mobility
    Dataset("osm_walk_network", "sokak", "vector", "OpenStreetMap highway", "çizgi", "ODbL 1.0", "Overpass API", "ingested", "mob_*"),
    Dataset("osm_transit_stops", "sokak", "vector", "OpenStreetMap", "nokta", "ODbL 1.0", "Overpass API", "ingested", "mob_walk800_transit_stops"),
    Dataset("mobility_database_gtfs", "sokak", "table", "MobilityData", "tarife", "kaynağa göre açık", "mobilitydatabase.org", "planned", "sefer sıklığı"),
    # ---- city function
    Dataset("osm_pois", "kent", "vector", "OpenStreetMap", "nokta", "ODbL 1.0", "Overpass API", "ingested", "poi_*"),
    Dataset("overture_places", "kent", "vector", "Overture Maps places (Meta, Foursquare OS Places, Microsoft, AllThePlaces)", "nokta", "CDLA-Permissive-2.0", "S3 GeoParquet", "ingested", "ov_places_* (Caferağa: OSM'nin 1,7 katı)"),
    Dataset("overture_transportation", "sokak", "vector", "Overture Maps transportation (segment, connector)", "çizgi", "ODbL 1.0", "S3 GeoParquet", "connector", "OSM yaya ağına küresel yedek"),
    Dataset("overture_divisions", "kent", "vector", "Overture Maps divisions (ülke…mahalle)", "poligon", "ODbL 1.0", "S3 GeoParquet", "connector", "ülke/bölge eşlemesi"),
    Dataset("fsq_os_places", "kent", "vector", "Foursquare OS Places (Swarm/Foursquare tabanı, 100M+)", "nokta", "Apache 2.0", "HF (kayıtlı) / Source Cooperative", "connector", "Overture places içinde zaten var"),
    Dataset("uber_h3", "sokak", "table", "Uber H3 (açık kaynak altıgen ızgara)", "ızgara", "Apache 2.0", "pip h3", "ingested", "tüm mekânsal birim"),
    Dataset("uber_movement", "sokak", "timeseries", "Uber Movement seyahat süreleri", "bölge çifti", "kapatıldı / kullanım koşulları", "-", "rejected", "erişilemez"),
    Dataset("google_popular_times", "sosyal", "table", "Google Maps Popular Times / yorumlar", "mekân", "Google ToS (açık değil), KVKK/GDPR", "-", "rejected", "kazıma yasak"),
    Dataset("google_eie", "enerji", "table", "Google Environmental Insights Explorer", "kent", "lisanslı paylaşım, açık değil", "-", "rejected", "yalnız literatür karşılaştırması"),
    Dataset("yandex_maps", "kent", "vector", "Yandex Haritalar / panorama", "-", "açık lisans yok", "-", "rejected", "kullanılamaz"),
    Dataset("osm_admin", "kent", "vector", "OpenStreetMap boundary", "poligon", "ODbL 1.0", "Overpass API", "ingested", "AOI sınırı"),
    # ---- energy
    Dataset("pvgis_pv", "enerji", "timeseries", "EU JRC PVGIS 5.3", "saatlik, nokta", "AB yeniden kullanım", "re.jrc.ec.europa.eu API", "ingested", "energy_pv_*"),
    Dataset("unsd_energy", "enerji", "table", "UN Statistics Division (UNdata)", "ülke, yıllık", "atıfla serbest", "data.un.org", "ingested", "konut elektriği/kişi"),
    Dataset("owid_energy", "enerji", "table", "Our World in Data (Ember, UN WPP)", "ülke, yıllık", "CC BY 4.0", "GitHub CSV", "ingested", "nüfus, talep/kişi"),
    Dataset("epias_national_load", "enerji", "timeseries", "EPİAŞ Şeffaflık (TR ulusal yük)", "saatlik, ülke", "atıfla kullanım; hesap gerekli", "seffaflik.epias.com.tr API (TGT)", "connector", "saatlik taban şekil"),
    Dataset("chen2022_elec_gdp", "enerji", "raster", "Chen vd. 2022 (figshare)", "1 km, 1992–2019", "teyit", "figshare", "planned", "bağımsız talep sınaması"),
    Dataset("osm_power", "enerji", "vector", "OpenStreetMap power=*", "nokta/çizgi", "ODbL 1.0", "Overpass API", "planned", "trafo yakınlığı"),
    Dataset("global_solar_atlas", "enerji", "raster", "World Bank / Solargis Global Solar Atlas", "250 m", "CC BY 4.0", "globalsolaratlas.info", "planned", "PVGIS çapraz kontrol"),
    # ---- climate & environment
    Dataset("era5_openmeteo", "iklim", "timeseries", "ECMWF ERA5 (Open-Meteo)", "saatlik, ~25 km", "CC BY 4.0", "archive-api.open-meteo.com", "ingested", "Demand.ninja girdisi"),
    Dataset("esa_worldcover", "cevre", "raster", "ESA WorldCover 2021", "10 m", "CC BY 4.0", "AWS / Zenodo", "planned", "yeşil alan payı"),
    Dataset("copernicus_dem", "cevre", "raster", "Copernicus DEM GLO-30", "30 m", "Copernicus DEM lisansı", "AWS open data (COG)", "ingested", "yükseklik, eğim, rölyef"),
    Dataset("sentinel2_l2a", "goruntu", "raster", "Copernicus Sentinel-2 L2A", "10 m", "Copernicus açık", "Earth Search STAC (COG)", "ingested", "NDVI, NDBI"),
    Dataset("landsat_c2", "goruntu", "raster", "USGS Landsat 8/9 C2 L2 (ST)", "30 m (ısıl 100 m)", "kamu malı", "Planetary Computer STAC (COG)", "ingested", "yüzey sıcaklığı (LST)"),
    Dataset("alphaearth_embeddings", "goruntu", "raster", "Google AlphaEarth Satellite Embedding", "10 m, 64-B", "teyit", "Earth Engine", "planned", "gömme vektörleri"),
    Dataset("mapillary", "goruntu", "vector", "Mapillary", "sokak görüntüsü", "CC BY-SA 4.0; anahtar", "graph.mapillary.com", "planned", "kat ve cephe tahmini"),
    # ---- economy & social
    Dataset("kummu2018_gdp_hdi", "ekonomi", "raster", "Kummu vd. 2018 (Dryad)", "5′ / 30″", "CC0 1.0", "datadryad.org", "planned", "GSYH, İGE"),
    Dataset("gdelt", "sosyal", "table", "GDELT Project", "olay, şehir", "açık (teyit)", "gdeltproject.org", "planned", "haber tonu"),
    # ---- PED reference class
    Dataset("ped_database", "ped", "table", "PED Database (COST PED-EU-NET, JPI UE, IEA Annex 83)", "proje", "teyit", "pedeu.net / Annex 83", "planned", "referans sınıfı"),
]


def catalog_frame() -> pd.DataFrame:
    return pd.DataFrame([asdict(d) for d in DATASETS]).set_index("id")

"""Global open geodata catalogue of the pedx data lake (K-035).

Design (docs/PROJE_DOSYASI.md §2): the lake does not copy "all data in the world". It holds a
catalogue of global raster/vector datasets with a connector per dataset; for an area of interest
(AOI) the connector fetches only the needed tile/window, caches it under data/raw, and the zonal
engine (pedx.datalake.raster) turns it into registered H3 features. Same code, any city.

status: ingested  – connector implemented and data in the Caferağa store
        connector – access verified, ingestion not yet wired
        planned   – licence/access to be confirmed
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
    Dataset("worldpop_agesex", "insan", "raster", "WorldPop", "100 m", "CC BY 4.0", "data.worldpop.org", "planned", "yaş yapısı"),
    Dataset("ghs_smod", "kent", "raster", "JRC GHS-SMOD R2023A", "1 km", "CC BY 4.0", "jeodpp", "planned", "kentsel/kırsal derece"),
    # ---- buildings
    Dataset("osm_buildings", "bina", "vector", "OpenStreetMap", "poligon", "ODbL 1.0", "Overpass API", "ingested", "built_*, morph_*"),
    Dataset("ghs_built_s_2020", "bina", "raster", "JRC GHS-BUILT-S R2023A (toplam)", "3″", "CC BY 4.0", "jeodpp tiles", "ingested", "ghsl_built_surface_m2"),
    Dataset("ghs_built_s_nres_2020", "bina", "raster", "JRC GHS-BUILT-S NRES R2023A", "3″", "CC BY 4.0", "jeodpp tiles", "ingested", "ghsl_nres_surface_m2"),
    Dataset("ghs_built_v_2020", "bina", "raster", "JRC GHS-BUILT-V R2023A (toplam)", "3″", "CC BY 4.0", "jeodpp tiles", "ingested", "ghsl_volume_m3"),
    Dataset("ghs_built_v_nres_2020", "bina", "raster", "JRC GHS-BUILT-V NRES R2023A", "3″", "CC BY 4.0", "jeodpp tiles", "ingested", "ghsl_nres_volume_m3"),
    Dataset("ghs_built_h_agbh_2018", "bina", "raster", "JRC GHS-BUILT-H AGBH R2023A", "3″", "CC BY 4.0", "jeodpp tiles", "ingested", "ghsl_height_m"),
    Dataset("overture_buildings", "bina", "vector", "Overture Maps Foundation", "poligon + yükseklik", "ODbL / CDLA (katmana göre)", "S3/Azure GeoParquet", "planned", "kat ve yükseklik"),
    Dataset("ms_buildings", "bina", "vector", "Microsoft Global ML Building Footprints", "poligon", "ODbL", "GitHub / Planetary Computer", "planned", "taban alanı tamlığı"),
    Dataset("google_open_buildings", "bina", "vector", "Google Open Buildings (2.5D Temporal)", "poligon / 4 m", "CC BY 4.0 / ODbL", "GCS", "planned", "yükseklik (kapsam teyit)"),
    # ---- streets & mobility
    Dataset("osm_walk_network", "sokak", "vector", "OpenStreetMap highway", "çizgi", "ODbL 1.0", "Overpass API", "ingested", "mob_*"),
    Dataset("osm_transit_stops", "sokak", "vector", "OpenStreetMap", "nokta", "ODbL 1.0", "Overpass API", "ingested", "mob_walk800_transit_stops"),
    Dataset("mobility_database_gtfs", "sokak", "table", "MobilityData", "tarife", "kaynağa göre açık", "mobilitydatabase.org", "planned", "sefer sıklığı"),
    # ---- city function
    Dataset("osm_pois", "kent", "vector", "OpenStreetMap", "nokta", "ODbL 1.0", "Overpass API", "ingested", "poi_*"),
    Dataset("overture_places", "kent", "vector", "Overture Maps Places", "nokta", "CDLA-Permissive 2.0 (teyit)", "GeoParquet", "planned", "POI tamlığı"),
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
    Dataset("copernicus_dem", "cevre", "raster", "Copernicus DEM GLO-30", "30 m", "Copernicus DEM lisansı", "AWS open data", "planned", "eğim"),
    Dataset("sentinel2_l2a", "goruntu", "raster", "Copernicus Sentinel-2 L2A", "10 m", "Copernicus açık", "Earth Search STAC (COG)", "planned", "NDVI, NDBI, gömmeler"),
    Dataset("landsat_c2", "goruntu", "raster", "USGS Landsat 8/9 C2", "30 m", "kamu malı", "AWS / Planetary Computer", "planned", "yüzey sıcaklığı"),
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

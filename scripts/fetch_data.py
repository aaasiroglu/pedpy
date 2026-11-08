"""Download every raw open-data input of the Caferağa demo into data/raw (idempotent, with retries).

Sources and licences: docs/11_veri_kaynaklari.md. Run:  python scripts/fetch_data.py
Validation-only (G2) documents are downloaded too, into data/raw/sources/.
"""

from __future__ import annotations

import io
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SRC = RAW / "sources"
UA = {"User-Agent": "pedx-research (open-data thesis pipeline)"}
OVERPASS = "https://overpass-api.de/api/interpreter"
BBOX = "40.9782847,29.0148423,40.9931934,29.0342259"  # bbox of OSM relation 9441032 (Caferağa Mahallesi)
POI_KEYS = ("amenity", "shop", "office", "leisure", "tourism", "craft", "healthcare")

JOBS = [
    ("caferaga_boundary_overpass.json", "overpass", "[out:json][timeout:120];relation(9441032);out geom;"),
    ("caferaga_buildings_boundary_bbox.json", "overpass", f'[out:json][timeout:180];way["building"]({BBOX});out tags geom;'),
    ("caferaga_pois_full.json", "overpass",
     "[out:json][timeout:180];(" + "".join(f'node["{k}"]({BBOX});way["{k}"]({BBOX});' for k in POI_KEYS) + ");out tags center;"),
    ("caferaga_walk_network.json", "overpass",
     '[out:json][timeout:180];way["highway"]["highway"!~"motorway|motorway_link|trunk|trunk_link|construction|proposed|raceway|bus_guideway"]'
     '["foot"!="no"]["access"!="private"](40.9707,29.0053,41.0007,29.0437);out geom;'),
    ("caferaga_transit_stops.json", "overpass",
     '[out:json][timeout:120];(node["highway"="bus_stop"](40.9707,29.0053,41.0007,29.0437);node["public_transport"="platform"](40.9707,29.0053,41.0007,29.0437);'
     'node["railway"~"station|halt|tram_stop|subway_entrance"](40.9707,29.0053,41.0007,29.0437);node["amenity"="ferry_terminal"](40.9707,29.0053,41.0007,29.0437););out;'),
    ("sources/pvgis_pv_caferaga_2023.json", "get",
     "https://re.jrc.ec.europa.eu/api/v5_3/seriescalc?lat=40.986&lon=29.028&startyear=2023&endyear=2023&pvcalculation=1"
     "&peakpower=1&loss=14&pvtechchoice=crystSi&mountingplace=building&optimalangles=1&outputformat=json"),
    ("sources/openmeteo_era5_caferaga_2023.json", "get",
     "https://archive-api.open-meteo.com/v1/archive?latitude=40.986&longitude=29.028&start_date=2023-01-01&end_date=2023-12-31"
     "&hourly=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,shortwave_radiation&wind_speed_unit=ms&timezone=UTC"),
    ("sources/undata_tr_1231.html", "get", "https://data.un.org/Data.aspx?d=EDATA&f=cmID%3aEL%3btrID%3a1231%3bcrID%3a792"),
    ("sources/undata_tr_1235.html", "get", "https://data.un.org/Data.aspx?d=EDATA&f=cmID%3aEL%3btrID%3a1235%3bcrID%3a792"),
    ("sources/owid-energy-data.csv", "get", "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"),
    ("sources/tedas_2023_sektor_raporu.pdf", "get", "https://www.tedas.gov.tr/FileUpload/MediaFolder/25819eac-d024-4308-891a-d248db8c1e0a.pdf"),
]
GHS_ZIP = ("https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E2020_GLOBE_R2023A_4326_3ss/"
           "V1-0/tiles/GHS_POP_E2020_GLOBE_R2023A_4326_3ss_V1_0_R5_C21.zip")


def _fetch(url: str, data: bytes | None = None, tries: int = 6, timeout: int = 300) -> bytes:
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=UA), timeout=timeout) as r:  # noqa: S310
                return r.read()
        except Exception as exc:  # noqa: BLE001
            wait = 5 * 2**i
            print(f"  ! {type(exc).__name__}: {exc} — {wait}s sonra yeniden denenecek")
            time.sleep(wait)
    raise RuntimeError(f"indirilemedi: {url}")


def main() -> None:
    SRC.mkdir(parents=True, exist_ok=True)
    for name, kind, spec in JOBS:
        out = RAW / name
        if out.exists() and out.stat().st_size > 0:
            print(f"✓ {name} (önbellekte)")
            continue
        print(f"↓ {name}")
        body = _fetch(OVERPASS, urllib.parse.urlencode({"data": spec}).encode()) if kind == "overpass" else _fetch(spec)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(body)
    tif = SRC / "ghs_pop" / "GHS_POP_E2020_GLOBE_R2023A_4326_3ss_V1_0_R5_C21.tif"
    if not tif.exists():
        print("↓ GHS-POP R2023A E2020 karosu R5_C21 (~120 MB)")
        zipfile.ZipFile(io.BytesIO(_fetch(GHS_ZIP, timeout=900))).extractall(tif.parent)
    else:
        print("✓ GHS-POP karosu (önbellekte)")
    print("Tamam. Şimdi:  make build && make serve")


if __name__ == "__main__":
    main()

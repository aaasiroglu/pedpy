"""EU JRC PVGIS hourly irradiance (free, open; SARAH-3 / ERA5 based).

API: ``https://re.jrc.ec.europa.eu/api/<version>/seriescalc``. We request the
plane-of-array irradiance ``G(i)`` [W/m²] for one calendar year and return it in
kW/m², with 29 February removed so every series has 8760 hours. Use the *same*
year for demand modelling so that hourly matching is meaningful (docs/07, C3).
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

__all__ = ["PVGIS_URL", "pvgis_query_url", "parse_pvgis_hourly", "fetch_pvgis_hourly"]

PVGIS_URL = "https://re.jrc.ec.europa.eu/api/v5_3/seriescalc"


def pvgis_query_url(lat: float, lon: float, year: int, angle: float = 0.0, aspect: float = 0.0, url: str = PVGIS_URL) -> str:
    """``angle`` = tilt from horizontal [deg]; ``aspect`` = azimuth, 0 = south, 90 = west (PVGIS convention)."""
    params = {
        "lat": lat, "lon": lon, "startyear": year, "endyear": year,
        "pvcalculation": 0, "angle": angle, "aspect": aspect, "outputformat": "json",
    }
    return f"{url}?{urllib.parse.urlencode(params)}"


def parse_pvgis_hourly(payload: dict) -> pd.DataFrame:
    """DataFrame indexed by UTC timestamp with ``irradiance_kw_m2`` and, if present, ``t2m_c``."""
    hourly = payload["outputs"]["hourly"]
    df = pd.DataFrame(hourly)
    ts = pd.to_datetime(df["time"], format="%Y%m%d:%H%M", utc=True)
    out = pd.DataFrame({"irradiance_kw_m2": df["G(i)"].astype(float).to_numpy() / 1000.0}, index=ts)
    if "T2m" in df:
        out["t2m_c"] = df["T2m"].astype(float).to_numpy()
    out = out[~((out.index.month == 2) & (out.index.day == 29))]
    if np.any(out["irradiance_kw_m2"] < 0):
        raise ValueError("negative irradiance in PVGIS response")
    return out


def fetch_pvgis_hourly(lat: float, lon: float, year: int = 2019, angle: float = 0.0, aspect: float = 0.0, cache: Optional[Path] = None) -> pd.DataFrame:
    if cache is not None and Path(cache).exists():
        return parse_pvgis_hourly(json.loads(Path(cache).read_text()))
    with urllib.request.urlopen(pvgis_query_url(lat, lon, year, angle, aspect), timeout=120) as resp:  # noqa: S310
        payload = json.loads(resp.read().decode("utf-8"))
    if cache is not None:
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
        Path(cache).write_text(json.dumps(payload))
    return parse_pvgis_hourly(payload)

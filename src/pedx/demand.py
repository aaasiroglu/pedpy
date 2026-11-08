"""Hourly residential demand from global open sources (K-034).

Design:  D_t = E_res · [ (1 − w) · b_t + w · m_t ]
  E_res  annual residential electricity of the area (GHS-POP × UNSD households / UN population)
  b_t    base (non-weather) hourly shape = national hourly load with the weather-driven part removed
  m_t    weather-driven shape from Demand.ninja (Staffell, Pfenninger & Johnson 2023), ERA5 weather
  w      weather-driven share, estimated from the national load itself (regression on Demand.ninja
         heating/cooling degree-hours) — no free constant.

National hourly load (G1): EPİAŞ transparency platform for Türkiye — listed in the global
"Awesome Electricity Demand" catalogue of open national demand data ("use with attribution").
EPİAŞ requires a free account; ``fetch_epias_realtime`` reads credentials from environment
variables, never from code or chat. Regional residential profiles (EPİAŞ mesken/AYEDAŞ) are G2
(validation only).

Demand.ninja is vendored under ``pedx._vendor.demand_ninja`` (BSD-3, © 2023 Stefan Pfenninger);
upstream pins pandas<1.5, so the unchanged model code is shipped with its licence.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Dict, Optional

import numpy as np
import pandas as pd

__all__ = [
    "era5_to_ninja_inputs", "weather_driven_demand", "decompose_national_load",
    "residential_hourly", "fetch_epias_realtime", "parse_epias_realtime",
]


def _specific_humidity_gkg(t_c, rh_pct, p_hpa):
    """Specific humidity [g/kg] from temperature, relative humidity and pressure (Magnus–Tetens)."""
    es = 6.112 * np.exp(17.67 * t_c / (t_c + 243.5))  # hPa
    e = rh_pct / 100.0 * es
    q = 0.622 * e / (p_hpa - 0.378 * e)
    return 1000.0 * q


def era5_to_ninja_inputs(openmeteo: dict) -> pd.DataFrame:
    """Demand.ninja inputs from an Open-Meteo ERA5 archive response.

    Requires hourly temperature_2m [°C], relative_humidity_2m [%], surface_pressure [hPa],
    wind_speed_10m [m/s] (``wind_speed_unit=ms``) and shortwave_radiation [W/m²].
    10 m wind is reduced to 2 m with the FAO-56 log profile: u2 = u10 · 4.87 / ln(67.8·10 − 5.42).
    """
    h = openmeteo["hourly"]
    if openmeteo.get("hourly_units", {}).get("wind_speed_10m") not in (None, "m/s"):
        raise ValueError("request wind_speed_unit=ms from Open-Meteo")
    idx = pd.to_datetime(h["time"], utc=True)
    t = np.asarray(h["temperature_2m"], float)
    df = pd.DataFrame({
        "humidity": _specific_humidity_gkg(t, np.asarray(h["relative_humidity_2m"], float), np.asarray(h["surface_pressure"], float)),
        "radiation_global_horizontal": np.asarray(h["shortwave_radiation"], float),
        "temperature": t,
        "wind_speed_2m": np.asarray(h["wind_speed_10m"], float) * 4.87 / np.log(67.8 * 10 - 5.42),
    }, index=idx)
    return df[~((df.index.month == 2) & (df.index.day == 29))]


def weather_driven_demand(inputs: pd.DataFrame, **params) -> pd.DataFrame:
    """Run Demand.ninja; returns hourly ``heating_demand``, ``cooling_demand`` (relative units) and BAIT."""
    from ._vendor.demand_ninja.core import demand

    out = demand(inputs, raw=True, **params)
    return out


def decompose_national_load(load: pd.Series, heat: pd.Series, cool: pd.Series) -> Dict[str, object]:
    """OLS: load_t = Σ_h,daytype α_(h,d) + β_h·heat_t + β_c·cool_t.

    Returns the weather-driven share w (heating and cooling separately), the base shape b_t
    (load minus fitted weather part, normalised) and R².
    """
    df = pd.DataFrame({"y": load, "heat": heat, "cool": cool}).dropna()
    hours = df.index.hour
    daytype = np.where(df.index.dayofweek >= 5, 1, 0)
    dummies = pd.get_dummies(pd.Series(hours * 2 + daytype, index=df.index), prefix="hd").astype(float)
    X = pd.concat([dummies, df[["heat", "cool"]]], axis=1).to_numpy()
    beta, *_ = np.linalg.lstsq(X, df["y"].to_numpy(), rcond=None)
    fitted = X @ beta
    ss_res = float(((df["y"] - fitted) ** 2).sum())
    ss_tot = float(((df["y"] - df["y"].mean()) ** 2).sum())
    bh, bc = float(beta[-2]), float(beta[-1])
    w_heat = max(bh, 0.0) * df["heat"].sum() / df["y"].sum()
    w_cool = max(bc, 0.0) * df["cool"].sum() / df["y"].sum()
    base = df["y"] - max(bh, 0.0) * df["heat"] - max(bc, 0.0) * df["cool"]
    base = base.clip(lower=0)
    return {"w_heat": w_heat, "w_cool": w_cool, "base_shape": base / base.sum(), "r2": 1 - ss_res / ss_tot,
            "beta_heat": bh, "beta_cool": bc}


def residential_hourly(annual_kwh: float, base_shape: pd.Series, weather: pd.Series, w: float) -> pd.Series:
    """D_t = E · [(1 − w) b_t + w m_t] with both shapes normalised to sum 1."""
    if not 0 <= w < 1:
        raise ValueError("weather share w must be in [0, 1)")
    m = weather / weather.sum() if weather.sum() > 0 else weather * 0
    b = base_shape / base_shape.sum()
    return annual_kwh * ((1 - w) * b.reindex(m.index).fillna(0) + w * m)


# ---------------------------------------------------------------- EPİAŞ (national hourly load)

EPIAS_TGT_URL = "https://giris.epias.com.tr/cas/v1/tickets"
EPIAS_RTC_URL = "https://seffaflik.epias.com.tr/electricity-service/v1/consumption/data/realtime-consumption"


def fetch_epias_realtime(year: int, username: Optional[str] = None, password: Optional[str] = None) -> pd.DataFrame:
    """Hourly real-time consumption of Türkiye for ``year`` (MWh). Credentials from EPIAS_USERNAME / EPIAS_PASSWORD."""
    user = username or os.environ.get("EPIAS_USERNAME")
    pw = password or os.environ.get("EPIAS_PASSWORD")
    if not user or not pw:
        raise RuntimeError("EPİAŞ hesabı gerekli: EPIAS_USERNAME ve EPIAS_PASSWORD ortam değişkenlerini ayarlayın")
    req = urllib.request.Request(EPIAS_TGT_URL, data=urllib.parse.urlencode({"username": user, "password": pw}).encode(),
                                 headers={"Accept": "text/plain", "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
        tgt = r.read().decode().strip()
    rows = []
    for m in range(1, 13):
        start = pd.Timestamp(year=year, month=m, day=1)
        end = start + pd.offsets.MonthEnd(0) + pd.Timedelta(hours=23)
        body = json.dumps({"startDate": start.strftime("%Y-%m-%dT%H:%M:%S+03:00"), "endDate": end.strftime("%Y-%m-%dT%H:%M:%S+03:00")}).encode()
        rq = urllib.request.Request(EPIAS_RTC_URL, data=body, headers={"TGT": tgt, "Content-Type": "application/json", "Accept": "application/json"})
        with urllib.request.urlopen(rq, timeout=120) as r:  # noqa: S310
            rows += json.loads(r.read().decode())["items"]
    return parse_epias_realtime({"items": rows})


def parse_epias_realtime(payload: dict) -> pd.DataFrame:
    """``items`` with ``date`` (ISO, +03:00) and ``consumption`` (MWh) → UTC-indexed hourly frame."""
    df = pd.DataFrame(payload["items"])
    idx = pd.to_datetime(df["date"], utc=True)
    out = pd.DataFrame({"consumption_mwh": df["consumption"].astype(float).to_numpy()}, index=idx).sort_index()
    out = out[~out.index.duplicated()]
    return out[~((out.index.month == 2) & (out.index.day == 29))]

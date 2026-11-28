"""Hourly demand model: ERA5 conversions, Demand.ninja run, national-load decomposition."""

import numpy as np
import pandas as pd
import pytest

from pedx.demand import _specific_humidity_gkg, decompose_national_load, era5_to_ninja_inputs, parse_epias_realtime, residential_hourly


def test_specific_humidity_reference_value():
    # 20 °C, 50 % RH, 1013.25 hPa → ~7.3 g/kg (psychrometric tables)
    assert _specific_humidity_gkg(20.0, 50.0, 1013.25) == pytest.approx(7.3, abs=0.15)


def _om(n=48):
    t = pd.date_range("2023-01-01", periods=n, freq="h", tz="UTC").strftime("%Y-%m-%dT%H:%M").tolist()
    return {"hourly_units": {"wind_speed_10m": "m/s"}, "hourly": {"time": t, "temperature_2m": [5.0] * n, "relative_humidity_2m": [70.0] * n,
            "surface_pressure": [1010.0] * n, "wind_speed_10m": [5.0] * n, "shortwave_radiation": [100.0] * n}}


def test_era5_inputs_units_and_wind_profile():
    df = era5_to_ninja_inputs(_om())
    assert list(df.columns) == ["humidity", "radiation_global_horizontal", "temperature", "wind_speed_2m"]
    assert df["wind_speed_2m"].iloc[0] == pytest.approx(5.0 * 4.87 / np.log(67.8 * 10 - 5.42))
    bad = _om(); bad["hourly_units"]["wind_speed_10m"] = "km/h"
    with pytest.raises(ValueError):
        era5_to_ninja_inputs(bad)


def test_demand_ninja_runs_and_heats_in_cold_weather():
    from pedx.demand import weather_driven_demand

    out = weather_driven_demand(era5_to_ninja_inputs(_om(24 * 5)))
    assert (out["heating_demand"] > 0).any() and (out["cooling_demand"] == 0).all()


def test_decomposition_recovers_known_weather_share():
    idx = pd.date_range("2023-01-01", periods=24 * 60, freq="h", tz="UTC")
    rng = np.random.default_rng(0)
    base = 100 + 20 * np.sin(2 * np.pi * idx.hour / 24)
    heat = pd.Series(np.clip(rng.normal(5, 3, len(idx)), 0, None), index=idx)
    cool = pd.Series(np.clip(rng.normal(1, 1, len(idx)), 0, None), index=idx)
    load = pd.Series(base + 4.0 * heat + 2.0 * cool, index=idx)
    r = decompose_national_load(load, heat, cool)
    assert r["beta_heat"] == pytest.approx(4.0, rel=1e-6) and r["beta_cool"] == pytest.approx(2.0, rel=1e-6)
    assert r["r2"] == pytest.approx(1.0)
    assert r["w_heat"] == pytest.approx(4.0 * heat.sum() / load.sum())
    d = residential_hourly(1000.0, r["base_shape"], heat, r["w_heat"])
    assert d.sum() == pytest.approx(1000.0)


def test_parse_epias():
    items = [{"date": "2023-01-01T00:00:00+03:00", "consumption": 30000.5}, {"date": "2023-01-01T01:00:00+03:00", "consumption": 29000.0}]
    df = parse_epias_realtime({"items": items})
    assert df.index[0] == pd.Timestamp("2022-12-31T21:00:00Z") and df["consumption_mwh"].iloc[0] == 30000.5

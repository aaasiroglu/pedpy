"""Offline tests for OSM/PVGIS parsers and a small end-to-end pipeline run."""

import numpy as np
import pandas as pd
import pytest

from pedx.ingest import buildings_query, parse_buildings, parse_pois, polygon_area_m2
from pedx.ingest.pvgis import parse_pvgis_hourly, pvgis_query_url


def _square(lat0, lon0, side_m):
    dlat = side_m / 111_195.0
    dlon = side_m / (111_195.0 * np.cos(np.radians(lat0)))
    return [
        {"lat": lat0, "lon": lon0},
        {"lat": lat0, "lon": lon0 + dlon},
        {"lat": lat0 + dlat, "lon": lon0 + dlon},
        {"lat": lat0 + dlat, "lon": lon0},
        {"lat": lat0, "lon": lon0},
    ]


OVERPASS = {
    "elements": [
        {"type": "way", "id": 1, "tags": {"building": "apartments", "building:levels": "5"}, "geometry": _square(40.986, 29.028, 20)},
        {"type": "way", "id": 2, "tags": {"building": "yes", "height": "12 m", "start_date": "1975"}, "geometry": _square(40.987, 29.029, 10)},
        {"type": "way", "id": 3, "tags": {"building": "office"}, "geometry": _square(40.985, 29.027, 30)},
        {"type": "way", "id": 4, "tags": {"highway": "residential"}, "geometry": _square(40.985, 29.027, 30)},
    ]
}


def test_polygon_area_of_20m_square():
    g = _square(40.986, 29.028, 20)
    assert polygon_area_m2([p["lat"] for p in g], [p["lon"] for p in g]) == pytest.approx(400, rel=2e-3)


def test_parse_buildings_flags_sources():
    df = parse_buildings(OVERPASS)
    assert len(df) == 3
    row = df.set_index("osm_id")
    assert row.loc["way/1", "height_m"] == pytest.approx(15.0) and row.loc["way/1", "height_source"] == "levels"
    assert row.loc["way/2", "height_m"] == pytest.approx(12.0) and row.loc["way/2", "start_year"] == 1975
    assert row.loc["way/3", "height_source"] == "missing" and np.isnan(row.loc["way/3", "height_m"])


def test_parse_pois():
    payload = {"elements": [{"type": "node", "id": 9, "lat": 40.9, "lon": 29.0, "tags": {"shop": "bakery"}}]}
    df = parse_pois(payload)
    assert df.iloc[0]["key"] == "shop"


def test_query_builders_validate_bbox():
    assert "way[\"building\"]" in buildings_query((40.98, 29.02, 40.99, 29.03))
    with pytest.raises(ValueError):
        buildings_query((40.99, 29.02, 40.98, 29.03))
    assert "seriescalc" in pvgis_query_url(41, 29, 2019)


def test_parse_pvgis_drops_feb29_and_converts_units():
    times = pd.date_range("2020-01-01", periods=8784, freq="h", tz="UTC")
    payload = {"outputs": {"hourly": [{"time": t.strftime("%Y%m%d:%H%M"), "G(i)": 500.0, "T2m": 10.0} for t in times]}}
    df = parse_pvgis_hourly(payload)
    assert len(df) == 8760
    assert df["irradiance_kw_m2"].iloc[0] == pytest.approx(0.5)


def test_pipeline_end_to_end_small():
    pytest.importorskip("h3")
    from pedx.pipeline import assess
    from pedx.synthetic import solar_irradiance

    rng = np.random.default_rng(0)
    n = 60
    b = pd.DataFrame(
        {
            "osm_id": [f"w/{i}" for i in range(n)],
            "lat": rng.uniform(40.981, 40.991, n),
            "lon": rng.uniform(29.021, 29.035, n),
            "footprint_area_m2": rng.uniform(80, 400, n),
            "building": rng.choice(["apartments", "office"], n),
            "levels": np.where(rng.random(n) < 0.5, 4, np.nan),
            "height_m": np.nan,
            "height_source": "missing",
            "start_year": np.nan,
            "roof_shape": None,
        }
    )
    res = assess(b, solar_irradiance(41.0), resolution=9, n_prescribe=0)
    assert res.scores["readiness"].between(0, 1).all()
    assert res.data_quality.loc["share_levels_imputed", "value"] == pytest.approx(0.5, abs=0.2)
    assert res.shapley["shapley_kwh"].sum() > 0

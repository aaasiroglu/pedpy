"""Offline tests for global open-data parsers and geometry helpers."""

import numpy as np
import pytest

from pedx.ingest.global_data import (
    _join_segments,
    boundary_rings,
    ghs_pop_tile_id,
    parse_pvgis_pv,
    parse_undata_table,
    points_in_polygon,
)


def test_ghs_pop_tile_for_istanbul():
    assert ghs_pop_tile_id(40.986, 29.028) == "R5_C21"


def test_join_segments_builds_closed_ring():
    a, b, c, d = (0, 0), (0, 1), (1, 1), (1, 0)
    rings = _join_segments([[a, b], [c, b], [c, d, a]])
    assert len(rings) == 1 and rings[0][0] == rings[0][-1] and len(rings[0]) == 5


def test_boundary_rings_and_point_in_polygon():
    sq = [{"lat": 0, "lon": 0}, {"lat": 0, "lon": 1}, {"lat": 1, "lon": 1}, {"lat": 1, "lon": 0}]
    payload = {"elements": [{"type": "relation", "id": 7, "tags": {"name": "X"}, "members": [
        {"type": "way", "role": "outer", "geometry": sq[:3]},
        {"type": "way", "role": "outer", "geometry": [sq[2], sq[3], sq[0]]},
    ]}]}
    b = boundary_rings(payload)
    assert b["osm_id"] == "relation/7"
    inside = points_in_polygon(np.array([0.5, 1.5]), np.array([0.5, 0.5]), b["outer"])
    assert inside.tolist() == [True, False]


def test_parse_undata_table():
    html = "<table><tr><td>Türkiye</td><td>Electricity - Consumption by households</td><td>2023</td><td>Kilowatt-hours, million</td><td>65,541</td><td></td></tr></table>"
    df = parse_undata_table(html)
    assert df.iloc[0]["value"] == 65541.0 and df.iloc[0]["year"] == 2023


def test_parse_pvgis_pv_units():
    payload = {"outputs": {"hourly": [{"time": "20230101:1210", "P": 500.0}, {"time": "20230101:1310", "P": 250.0}]}}
    df = parse_pvgis_pv(payload)
    assert df["pv_kwh_per_kwp"].sum() == pytest.approx(0.75)

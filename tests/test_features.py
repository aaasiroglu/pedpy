"""Hex feature store: catalogue contract and layer computations."""

import numpy as np
import pandas as pd
import pytest

from pedx.features import CATALOG, building_features, catalog_frame, poi_family, poi_features, validate_columns


def test_every_feature_has_source_licence_and_known_family():
    cat = catalog_frame()
    assert cat["source"].str.len().gt(0).all() and cat["license"].str.len().gt(0).all()
    assert set(cat["family"]) <= {"energy", "built", "demography", "poi", "economy", "mobility", "environment", "climate"}
    assert set(cat["status"]) <= {"active", "planned"}


def test_contract_rejects_unregistered_or_planned_columns():
    validate_columns(["energy_balance", "poi_total"])
    with pytest.raises(ValueError):
        validate_columns(["secret_column"])
    with pytest.raises(ValueError):
        validate_columns(["econ_gdp_ppp"])  # planned, not yet active


def test_poi_taxonomy():
    assert poi_family("amenity", "cafe") == "food_drink"
    assert poi_family("shop", "bakery") == "retail"
    assert poi_family("amenity", "unknown_value") == "other"
    assert poi_family("nonkey", "x") == "other"


def test_poi_features_counts_diversity_and_shares():
    pois = pd.DataFrame({"cell": ["a"] * 4 + ["b"], "key": ["amenity", "amenity", "shop", "office", "amenity"],
                         "value": ["cafe", "bar", "bakery", "company", "bench"]})
    f = poi_features(pois, pd.Series({"a": 2.0, "b": 1.0}), pd.Series({"a": 100.0, "b": 0.0}))
    assert f.loc["a", "poi_total"] == 4 and f.loc["a", "poi_n_food_drink"] == 2
    assert 0 < f.loc["a", "poi_diversity"] <= 1 and f.loc["b", "poi_diversity"] == 0.0
    assert f.loc["a", "poi_daytime_share"] == pytest.approx(0.5)  # retail + office
    assert f.loc["a", "poi_night_share"] == pytest.approx(0.25)  # bar
    assert f.loc["a", "poi_density_per_ha"] == pytest.approx(2.0)
    assert np.isnan(f.loc["b", "poi_per_1000_pop"])
    validate_columns(f.columns)


def test_building_features_shares_sum_to_one():
    bld = pd.DataFrame({"cell": ["a", "a", "a"], "building": ["apartments", "retail", "yes"],
                        "footprint_area_m2": [100.0, 50.0, 50.0], "levels": [5, np.nan, np.nan]})
    f = building_features(bld, pd.Series({"a": 1.0}))
    s = f.loc["a", ["built_share_residential", "built_share_nonresidential", "built_share_untyped"]].sum()
    assert s == pytest.approx(1.0)
    assert f.loc["a", "built_coverage"] == pytest.approx(200 / 1e4)
    assert f.loc["a", "built_levels_known_share"] == pytest.approx(1 / 3)
    validate_columns(f.columns)

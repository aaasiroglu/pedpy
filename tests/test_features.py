"""Hex feature store: catalogue contract and layer computations."""

import numpy as np
import pandas as pd
import pytest

from pedx.features import CATALOG, building_features, catalog_frame, poi_family, poi_features, validate_columns


def test_every_feature_has_source_licence_and_known_family():
    cat = catalog_frame()
    assert cat["source"].str.len().gt(0).all() and cat["license"].str.len().gt(0).all()
    from pedx.features import FAMILIES

    assert set(cat["family"]) <= set(FAMILIES)
    assert {"energy", "built", "demography", "poi", "vulnerability", "embedding"} <= set(FAMILIES)
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


def test_morphology_shared_walls_detects_attached_buildings():
    pytest.importorskip("momepy")
    import geopandas as gpd
    from shapely.geometry import box

    from pedx.features.morphology import morphology_features

    # two attached 10x10 m squares (sharing a 10 m wall, 1 cm gap) and one detached square
    g = gpd.GeoDataFrame({"osm_id": ["a", "b", "c"]},
                         geometry=[box(0, 0, 10, 10), box(10.01, 0, 20, 10), box(50, 50, 60, 60)], crs=32635)
    f = morphology_features(g, pd.Series({"a": "h1", "b": "h1", "c": "h2"}))
    # exact 20/80; the 0.3 m tolerance adds ≤ 2·tol at each end of each shared wall (known, bounded bias)
    r = f.loc["h1", "morph_shared_wall_ratio"]
    assert 20 / 80 <= r <= (20 + 4 * 0.3) / 80 + 1e-9
    assert f.loc["h2", "morph_shared_wall_ratio"] == 0.0
    assert f.loc["h1", "morph_compactness_mean"] > 0
    validate_columns(f.columns)


def test_walk_accessibility_on_a_line_graph():
    pytest.importorskip("networkx")
    pytest.importorskip("h3")
    import h3

    from pedx.features.accessibility import accessibility_features, walk_graph

    # straight N–S street of ~1.1 km made of 11 segments; POIs at both ends
    lat0, lon0 = 40.98, 29.02
    geom = [{"lat": lat0 + i * 0.001, "lon": lon0} for i in range(12)]
    G = walk_graph({"elements": [{"type": "way", "id": 1, "geometry": geom}]})
    assert G.number_of_edges() == 11
    cell = h3.latlng_to_cell(lat0, lon0, 10)
    pois = pd.DataFrame({"lat": [lat0, lat0 + 0.011], "lon": [lon0, lon0], "family": ["retail", "health"]})
    stops = pd.DataFrame({"lat": [lat0 + 0.0005], "lon": [lon0]})
    f = accessibility_features(G, [cell], pois, stops, pd.Series({cell: 1.5}))
    # the far POI (~1.2 km away along the street) is outside the 800 m walk
    assert f.loc[cell, "mob_walk800_pois"] == 1 and f.loc[cell, "mob_walk800_daily_needs"] == 1
    assert f.loc[cell, "mob_walk800_daily_completeness"] == pytest.approx(1 / 5)
    assert f.loc[cell, "mob_walk800_transit_stops"] == 1
    validate_columns(f.columns)


def test_zonal_h3_sum_and_mean(tmp_path):
    rasterio = pytest.importorskip("rasterio")
    pytest.importorskip("h3")
    from rasterio.transform import from_origin

    from pedx.datalake import zonal_h3

    arr = np.array([[1.0, 2.0], [3.0, -200.0]], dtype="float32")  # negative = nodata-like, ignored
    path = tmp_path / "r.tif"
    with rasterio.open(path, "w", driver="GTiff", height=2, width=2, count=1, dtype="float32", crs="EPSG:4326",
                       transform=from_origin(29.0, 41.0, 0.0001, 0.0001)) as dst:
        dst.write(arr, 1)
    s = zonal_h3(path, (40.9998, 29.0, 41.0, 29.0002), 7, "sum")
    assert s.sum() == pytest.approx(6.0)
    m = zonal_h3(path, (40.9998, 29.0, 41.0, 29.0002), 7, "mean")
    assert m.iloc[0] == pytest.approx(2.0)


def test_datalake_catalog_integrity():
    from pedx.datalake import catalog_frame as lake

    c = lake()
    assert c.index.is_unique and set(c["status"]) <= {"ingested", "connector", "planned", "rejected"}
    assert set(c["kind"]) <= {"raster", "vector", "table", "timeseries"}
    assert (c["license"].str.len() > 0).all()


def test_orientation_order_of_a_grid_is_one():
    pytest.importorskip("networkx")
    h3 = pytest.importorskip("h3")
    from pedx.features.accessibility import network_complexity_features, walk_graph

    lat0, lon0, d = 40.98, 29.02, 0.0002
    ways = []
    for i in range(3):  # N–S and E–W streets of a small orthogonal grid
        ways.append({"type": "way", "id": 100 + i, "geometry": [{"lat": lat0 + j * d, "lon": lon0 + i * d} for j in range(3)]})
        ways.append({"type": "way", "id": 200 + i, "geometry": [{"lat": lat0 + i * d, "lon": lon0 + j * d} for j in range(3)]})
    payload = {"elements": ways}
    G = walk_graph(payload)
    cell = h3.latlng_to_cell(lat0 + d, lon0 + d, 9)
    f = network_complexity_features(payload, G, [cell], pd.Series({cell: 10.0}))
    assert f.loc[cell, "mob_orientation_order"] == pytest.approx(1.0, abs=0.02)
    assert f.loc[cell, "mob_circuity"] == pytest.approx(1.0, abs=1e-3)
    validate_columns(f.columns)


def test_pca_embedding_shapes_and_variance():
    from pedx.features.embedding import pca_embedding

    rng = np.random.default_rng(0)
    F = pd.DataFrame(rng.normal(size=(40, 6)), columns=list("abcdef"))
    F["g"] = F["a"] * 2 + rng.normal(scale=0.01, size=40)  # redundant feature → strong first component
    E, info = pca_embedding(F, list(F.columns), k=3)
    assert E.shape == (40, 3)
    assert 0 < sum(c["explained_variance"] for c in info["components"]) <= 1
    assert {t["feature"] for t in info["components"][0]["top_loadings"][:2]} == {"a", "g"}

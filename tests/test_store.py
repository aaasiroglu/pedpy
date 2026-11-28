"""Data infrastructure (K-071): contracts, manifest, use-class rules, blocks, inventory parsers."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pedx.store import manifest, schema
from pedx.store.buildings import use_from_class, use_from_land_use, use_from_subtype

ROOT = Path(__file__).resolve().parents[1]


def _sites(**kw):
    base = dict(site_id=["A1", "A2"], name=["a", "b"], city=["x", "y"], country=["NL", "SE"], lat=[52.0, 59.0], lon=[4.9, 18.0],
                coord_src=["database", "osm_site"], ped_class=["A", "Lab"], phase=["planning", "operation"], structure=["new", "unknown"],
                area_ha=[4.0, np.nan], boundary_type=["Geographic", None], financing=[None, None], ownership_land=[None, None],
                in_core16=[True, False], sources=["s1", "s2"], url=[None, None])
    base.update(kw)
    return pd.DataFrame(base)


def test_contract_passes_and_catches_errors():
    assert schema.validate(_sites(), "ped_sites") == []
    probs = schema.validate(_sites(site_id=["A1", "A1"], lat=[95.0, 59.0], ped_class=["A", "Z"]), "ped_sites")
    text = " | ".join(probs)
    assert "duplicates" in text and "above 90" in text and "unexpected values" in text
    assert any("missing column" in p for p in schema.validate(_sites().drop(columns=["sources"]), "ped_sites"))


def test_coverage_rule():
    probs = schema.validate(_sites(lat=[np.nan, np.nan], lon=[np.nan, np.nan]), "ped_sites")
    assert any("coverage" in p for p in probs)


def test_manifest_roundtrip(tmp_path, monkeypatch):
    f = ROOT / "data" / "_tmp_manifest_test.csv"
    f.write_text("a\n1\n")
    mf = tmp_path / "manifest.json"
    try:
        e = manifest.register("t/x", f, "ped_sites", "1.0", 1, inputs=[{"source": "unit"}], path=mf)
        assert e["rows"] == 1 and len(e["sha256"]) == 64
        assert manifest.check(mf) == []
        f.write_text("a\n2\n")
        assert any("checksum" in p for p in manifest.check(mf))
    finally:
        f.unlink()
    assert any("missing" in p for p in manifest.check(mf))


def test_use_class_rules():
    assert use_from_class("stadium") == "sport" and use_from_class("apartments") == "residential"
    assert use_from_subtype("medical") == "health" and use_from_subtype(None) is None
    assert use_from_land_use("pitch", "recreation") == "sport" and use_from_land_use(None, "residential") == "residential"
    assert use_from_land_use("grass", "managed") is None


def test_blocks_from_a_street_grid():
    shapely = pytest.importorskip("shapely")
    pytest.importorskip("geopandas")
    from pedx.store.units import blocks_from_lines
    # 3×3 grid of streets inside a square boundary → 4 inner blocks + 12 edge pieces bounded by the boundary ring
    bnd = shapely.box(0.0, 0.0, 0.004, 0.004)
    xs = [0.001, 0.002, 0.003]
    lines = [shapely.LineString([(x, -0.001), (x, 0.005)]) for x in xs] + [shapely.LineString([(-0.001, y), (0.005, y)]) for y in xs]
    b = blocks_from_lines(lines, bnd)
    assert len(b) == 16 and b["block_id"].is_unique
    assert schema.validate(b.assign(n_buildings=0, footprint_m2=0.0), "blocks") == []
    assert list(blocks_from_lines(lines, bnd)["block_id"]) == list(b["block_id"])  # stable ids


def test_inventory_parsers():
    spec = importlib.util.spec_from_file_location("bps", ROOT / "scripts" / "build_ped_sites.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.area_m2("1,280,000") == 1_280_000 and m.area_m2("330.000") == 330_000 and m.area_m2("485") == 485
    assert m.booklet_ha("Ha: 65") == 65 and m.booklet_ha("about 52 ha") == 52 and m.booklet_ha("1km²") == 100
    assert np.isnan(m.booklet_ha("28,500 m2 GFA"))
    assert m.structure("Newly built; Existing neighbourhood") == "mixed" and m.structure("Existing neighbourhood") == "existing"

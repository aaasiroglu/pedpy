"""Data contracts: one schema per product, checked by ``validate`` (K-071).

A schema is a list of ``Col``. ``validate`` returns human-readable problems (empty list = healthy).
Coverage rules (share of non-missing values) are part of the contract so that a silently degraded input
(e.g. a building source that loses its heights) fails the check instead of flowing into results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

__all__ = ["Col", "Schema", "SCHEMAS", "validate", "USE_CLASSES"]

# building use classes used for demand modelling (docs/32 §4)
USE_CLASSES = ("residential", "education", "sport", "civic", "health", "religious", "commercial", "office",
               "industrial", "agricultural", "transport", "other", "unknown")


@dataclass(frozen=True)
class Col:
    name: str
    kind: str  # str | float | int | bool | geometry
    unit: str = ""
    required: bool = True  # column must exist
    nullable: bool = True
    lo: Optional[float] = None
    hi: Optional[float] = None
    allowed: Optional[Sequence[str]] = None
    unique: bool = False
    doc: str = ""


@dataclass(frozen=True)
class Schema:
    name: str
    version: str
    cols: List[Col]
    min_coverage: Dict[str, float] = field(default_factory=dict)  # column → minimum non-null share
    doc: str = ""


PED_SITES = Schema("ped_sites", "1.0", [
    Col("site_id", "str", nullable=False, unique=True, doc="PEDDB-<id> | BKL-<no> | SCC-<n> | C-<n>"),
    Col("name", "str", nullable=False),
    Col("city", "str"),
    Col("country", "str", nullable=False),
    Col("lat", "float", "deg", lo=-90, hi=90),
    Col("lon", "float", "deg", lo=-180, hi=180),
    Col("coord_src", "str", nullable=False, allowed=("database", "database_corrected", "osm_site", "osm_city", "core16", "missing")),
    Col("ped_class", "str", nullable=False, allowed=("A", "B", "Lab", "C")),
    Col("phase", "str", nullable=False, allowed=("planning", "implementation", "operation", "completed", "unknown")),
    Col("structure", "str", nullable=False, allowed=("new", "existing", "mixed", "unknown")),
    Col("area_ha", "float", "ha", lo=0.01, hi=1e6),
    Col("boundary_type", "str"),
    Col("financing", "str"),
    Col("ownership_land", "str"),
    Col("in_core16", "bool", nullable=False),
    Col("sources", "str", nullable=False, doc="semicolon list of source records"),
    Col("url", "str"),
], min_coverage={"lat": 0.85}, doc="Unified global PED inventory (booklet + database + core 16 + class C)")

BUILDINGS = Schema("buildings", "1.0", [
    Col("bld_id", "str", nullable=False, unique=True, doc="Overture GERS id"),
    Col("footprint_m2", "float", "m²", nullable=False, lo=1, hi=5e5),
    Col("height_m", "float", "m", lo=1, hi=500),
    Col("height_src", "str", nullable=False, allowed=("overture_height", "overture_floors", "ghsl_built_h", "none")),
    Col("floors", "float", "", lo=1, hi=150),
    Col("floor_area_m2", "float", "m²", lo=0),
    Col("use_class", "str", nullable=False, allowed=USE_CLASSES),
    Col("use_src", "str", nullable=False, allowed=("overture_class", "overture_subtype", "land_use", "none")),
    Col("data_src", "str", nullable=False, doc="first source dataset (OpenStreetMap, Microsoft ML Buildings, ...)"),
    Col("block_id", "str"),
    Col("h3_r9", "str", nullable=False), Col("h3_r10", "str", nullable=False), Col("h3_r11", "str", nullable=False),
    Col("geometry", "geometry", nullable=False),
], min_coverage={"height_m": 0.80, "block_id": 0.80}, doc="One row per building inside the area boundary")

BLOCKS = Schema("blocks", "1.0", [
    Col("block_id", "str", nullable=False, unique=True),
    Col("area_m2", "float", "m²", nullable=False, lo=1),
    Col("n_buildings", "int", nullable=False, lo=0),
    Col("footprint_m2", "float", "m²", nullable=False, lo=0),
    Col("geometry", "geometry", nullable=False),
], doc="Urban blocks: polygons enclosed by streets and the area boundary")

SCHEMAS: Dict[str, Schema] = {s.name: s for s in (PED_SITES, BUILDINGS, BLOCKS)}


def _kind_ok(s: pd.Series, kind: str) -> bool:
    x = s.dropna()
    if x.empty or kind == "geometry":
        return True
    if kind == "str":
        return x.map(lambda v: isinstance(v, str)).all()
    if kind == "bool":
        return x.map(lambda v: isinstance(v, (bool, np.bool_))).all()
    return pd.api.types.is_numeric_dtype(x)


def validate(df: pd.DataFrame, schema: "Schema | str") -> List[str]:
    """Problems found in ``df`` against ``schema`` (empty list = passes)."""
    sc = SCHEMAS[schema] if isinstance(schema, str) else schema
    out: List[str] = []
    for c in sc.cols:
        if c.name not in df.columns:
            if c.required:
                out.append(f"{sc.name}: missing column '{c.name}'")
            continue
        s = df[c.name]
        if c.kind == "geometry":
            bad = int(s.isna().sum() + (~s.dropna().map(lambda g: getattr(g, "is_valid", False))).sum())
            if bad:
                out.append(f"{sc.name}.{c.name}: {bad} missing or invalid geometries")
            continue
        if not _kind_ok(s, c.kind):
            out.append(f"{sc.name}.{c.name}: expected {c.kind}")
            continue
        if not c.nullable and s.isna().any():
            out.append(f"{sc.name}.{c.name}: {int(s.isna().sum())} missing values in a non-null column")
        x = s.dropna()
        if c.lo is not None and (x < c.lo).any():
            out.append(f"{sc.name}.{c.name}: {int((x < c.lo).sum())} values below {c.lo} {c.unit}".rstrip())
        if c.hi is not None and (x > c.hi).any():
            out.append(f"{sc.name}.{c.name}: {int((x > c.hi).sum())} values above {c.hi} {c.unit}".rstrip())
        if c.allowed is not None and not x.isin(c.allowed).all():
            out.append(f"{sc.name}.{c.name}: unexpected values {sorted(set(x[~x.isin(c.allowed)]))[:5]}")
        if c.unique and s.duplicated().any():
            out.append(f"{sc.name}.{c.name}: {int(s.duplicated().sum())} duplicates")
    for col, share in sc.min_coverage.items():
        if col in df.columns and len(df):
            cov = float(df[col].notna().mean())
            if cov < share:
                out.append(f"{sc.name}.{col}: coverage {cov:.0%} below the contract minimum {share:.0%}")
    return out

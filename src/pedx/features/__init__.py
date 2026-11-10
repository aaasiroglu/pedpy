"""H3 hex feature store: registered, licensed open-data features per hexagon (K-029)."""

from .layers import POI_TAXONOMY, building_features, demography_features, poi_family, poi_features
from .registry import CATALOG, FAMILIES, FeatureSpec, catalog_frame, spec

__all__ = [
    "CATALOG", "FAMILIES", "FeatureSpec", "POI_TAXONOMY", "building_features", "catalog_frame",
    "demography_features", "poi_family", "poi_features", "spec", "validate_columns",
]


def validate_columns(columns) -> None:
    """Data contract: every exported feature column must be registered and active."""
    bad = [c for c in columns if c not in CATALOG or CATALOG[c].status != "active"]
    if bad:
        raise ValueError(f"unregistered or inactive feature columns: {bad}")

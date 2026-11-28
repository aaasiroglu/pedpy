"""Hex-level feature layers computed from open data (OSM buildings, OSM POIs, population)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .registry import POI_FAMILY_LABELS

__all__ = ["POI_TAXONOMY", "poi_family", "poi_features", "building_features", "demography_features"]

# OSM key=value → POI family. Order of keys follows OSM's primary feature keys.
POI_TAXONOMY = {
    "amenity": {
        "food_drink": {"cafe", "restaurant", "fast_food", "bar", "pub", "ice_cream", "food_court", "biergarten", "nightclub"},
        "health": {"pharmacy", "clinic", "hospital", "doctors", "dentist", "veterinary"},
        "education": {"school", "kindergarten", "university", "college", "library", "language_school", "driving_school", "music_school"},
        "finance": {"atm", "bank", "bureau_de_change", "money_transfer"},
        "leisure_culture": {"theatre", "cinema", "arts_centre", "community_centre", "events_venue", "studio", "social_facility"},
        "public_civic": {"townhall", "police", "fire_station", "post_office", "courthouse", "public_building", "toilets", "recycling", "waste_basket", "drinking_water", "shelter"},
        "transport": {"parking", "parking_entrance", "bicycle_parking", "fuel", "charging_station", "ferry_terminal", "bus_station", "taxi", "car_rental", "bicycle_rental", "car_wash"},
        "religion": {"place_of_worship"},
        "street_furniture": {"bench", "fountain", "clock", "vending_machine", "telephone"},
    },
    "shop": "retail",
    "office": "office_business",
    "craft": "craft",
    "healthcare": "health",
    "tourism": "tourism",
    "leisure": "leisure_culture",
}
DAYTIME = {"retail", "office_business", "health", "education", "finance"}
NIGHT_VALUES = {"bar", "pub", "nightclub", "restaurant", "biergarten"}


def poi_family(key: str, value: str) -> str:
    rule = POI_TAXONOMY.get(key)
    if rule is None:
        return "other"
    if isinstance(rule, str):
        return rule
    for fam, values in rule.items():
        if value in values:
            return fam
    return "other"


def _shannon(counts: np.ndarray, k: int) -> float:
    total = counts.sum()
    if total <= 0 or k <= 1:
        return 0.0
    p = counts[counts > 0] / total
    return float(-(p * np.log(p)).sum() / np.log(k))


def poi_features(pois: pd.DataFrame, cell_area_ha: pd.Series, population: pd.Series) -> pd.DataFrame:
    """Per-cell POI counts by family, density, normalised Shannon diversity, day/night shares.

    ``pois`` needs columns ``cell, key, value``.
    """
    df = pois.copy()
    df["family"] = [poi_family(k, v) for k, v in zip(df["key"], df["value"])]
    fams = list(POI_FAMILY_LABELS)
    counts = df.pivot_table(index="cell", columns="family", values="key", aggfunc="size", fill_value=0)
    counts = counts.reindex(columns=fams, fill_value=0)
    out = counts.add_prefix("poi_n_")
    out["poi_total"] = counts.sum(axis=1)
    out["poi_diversity"] = [_shannon(r, len(fams) - 1) for r in counts.drop(columns="other").to_numpy()]
    out["poi_daytime_share"] = counts[list(DAYTIME)].sum(axis=1) / out["poi_total"].where(out["poi_total"] > 0)
    night = df[df["value"].isin(NIGHT_VALUES)].groupby("cell").size()
    out["poi_night_share"] = night.reindex(out.index, fill_value=0) / out["poi_total"].where(out["poi_total"] > 0)
    area = cell_area_ha.reindex(out.index)
    out["poi_density_per_ha"] = out["poi_total"] / area
    pop = population.reindex(out.index)
    out["poi_per_1000_pop"] = np.where(pop > 0, out["poi_total"] / pop * 1000.0, np.nan)
    return out


RESIDENTIAL_TAGS = {"residential", "apartments", "house", "detached", "terrace", "dormitory", "semidetached_house"}
UNTYPED_TAGS = {"yes", None}


def building_features(bld: pd.DataFrame, cell_area_ha: pd.Series) -> pd.DataFrame:
    """Per-cell built-form features from parsed OSM buildings (needs ``cell`` column)."""
    b = bld.copy()
    b["cls"] = np.where(b["building"].isin(RESIDENTIAL_TAGS), "res",
                        np.where(b["building"].isin(["yes"]) | b["building"].isna(), "untyped", "nonres"))
    g = b.groupby("cell")
    out = pd.DataFrame({
        "built_n_buildings": g.size(),
        "built_footprint_m2": g["footprint_area_m2"].sum(),
        "built_mean_footprint_m2": g["footprint_area_m2"].mean(),
        "built_levels_known_share": g["levels"].apply(lambda s: float(s.notna().mean())),
        "built_mean_levels": g["levels"].mean(),
    })
    area_by_cls = b.pivot_table(index="cell", columns="cls", values="footprint_area_m2", aggfunc="sum", fill_value=0.0)
    for c in ("res", "nonres", "untyped"):
        if c not in area_by_cls:
            area_by_cls[c] = 0.0
    tot = area_by_cls[["res", "nonres", "untyped"]].sum(axis=1)
    out["built_share_residential"] = area_by_cls["res"] / tot
    out["built_share_nonresidential"] = area_by_cls["nonres"] / tot
    out["built_share_untyped"] = area_by_cls["untyped"] / tot
    out["built_coverage"] = out["built_footprint_m2"] / (cell_area_ha.reindex(out.index) * 1e4)
    return out


def demography_features(population: pd.Series, cell_area_ha: pd.Series, footprint_m2: pd.Series) -> pd.DataFrame:
    idx = population.index.union(footprint_m2.index)
    pop = population.reindex(idx).fillna(0.0)
    out = pd.DataFrame({"demo_population": pop})
    out["demo_density_per_ha"] = pop / cell_area_ha.reindex(idx)
    fp = footprint_m2.reindex(idx).fillna(0.0)
    out["demo_m2_footprint_per_capita"] = np.where(pop > 0, fp / pop, np.nan)
    return out

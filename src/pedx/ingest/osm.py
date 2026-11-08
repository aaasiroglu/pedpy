"""OpenStreetMap ingestion via the Overpass API (primary open data source, K-021).

Network access and parsing are separated so parsing is testable offline and
results are reproducible: :func:`fetch_overpass` stores the raw JSON, and
:func:`parse_buildings` / :func:`parse_pois` turn it into tables.

Footprint areas are computed on a local equirectangular projection around
each polygon (error well below 0.1 % at district scale). Heights follow the
OSM conventions ``height`` → ``building:levels * level_height`` → missing;
missing values are *flagged*, never silently filled (imputation is a separate,
reported step).

Data © OpenStreetMap contributors, ODbL 1.0.
"""

from __future__ import annotations

import json
import math
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

__all__ = [
    "DEFAULT_ENDPOINT",
    "buildings_query",
    "pois_query",
    "fetch_overpass",
    "polygon_area_m2",
    "parse_buildings",
    "parse_pois",
]

DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"
EARTH_R = 6_371_008.8
POI_KEYS = ("amenity", "shop", "office", "leisure", "tourism", "craft", "healthcare")

BBox = Tuple[float, float, float, float]  # (south, west, north, east)


def _bbox_str(bbox: BBox) -> str:
    s, w, n, e = bbox
    if not (-90 <= s < n <= 90 and -180 <= w < e <= 180):
        raise ValueError("bbox must be (south, west, north, east) with south < north and west < east")
    return f"{s},{w},{n},{e}"


def buildings_query(bbox: BBox, timeout: int = 120) -> str:
    return f'[out:json][timeout:{timeout}];(way["building"]({_bbox_str(bbox)}););out tags geom;'


def pois_query(bbox: BBox, keys: Sequence[str] = POI_KEYS, timeout: int = 120) -> str:
    b = _bbox_str(bbox)
    parts = "".join(f'node["{k}"]({b});way["{k}"]({b});' for k in keys)
    return f"[out:json][timeout:{timeout}];({parts});out tags center;"


def fetch_overpass(query: str, endpoint: str = DEFAULT_ENDPOINT, cache: Optional[Path] = None, user_agent: str = "pedx") -> dict:
    """POST an Overpass query; optionally cache the raw JSON at ``cache``."""
    if cache is not None and Path(cache).exists():
        return json.loads(Path(cache).read_text())
    data = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(endpoint, data=data, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=300) as resp:  # noqa: S310 - fixed https endpoint
        payload = json.loads(resp.read().decode("utf-8"))
    if cache is not None:
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
        Path(cache).write_text(json.dumps(payload))
    return payload


def polygon_area_m2(lats: Sequence[float], lons: Sequence[float]) -> float:
    """Planar area of a lat/lon ring on a local equirectangular projection."""
    lat = np.asarray(lats, float)
    lon = np.asarray(lons, float)
    if lat.size < 3:
        return 0.0
    lat0 = math.radians(float(lat.mean()))
    x = np.radians(lon) * EARTH_R * math.cos(lat0)
    y = np.radians(lat) * EARTH_R
    return float(0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def _centroid(lats, lons) -> Tuple[float, float]:
    lat = np.asarray(lats, float)
    lon = np.asarray(lons, float)
    if lat.size >= 3 and (lat[0] == lat[-1] and lon[0] == lon[-1]):
        lat, lon = lat[:-1], lon[:-1]
    return float(lat.mean()), float(lon.mean())


_NUM = re.compile(r"[-+]?\d*\.?\d+")


def _to_float(value: Optional[str]) -> float:
    if value is None:
        return np.nan
    m = _NUM.search(str(value).replace(",", "."))
    return float(m.group()) if m else np.nan


def _year(value: Optional[str]) -> float:
    if value is None:
        return np.nan
    m = re.search(r"(1[5-9]\d\d|20\d\d)", str(value))
    return float(m.group()) if m else np.nan


def parse_buildings(payload: dict, level_height_m: float = 3.0) -> pd.DataFrame:
    """Building footprints and attributes from an Overpass ``out geom`` response."""
    rows = []
    for el in payload.get("elements", []):
        if el.get("type") != "way" or "geometry" not in el:
            continue
        tags = el.get("tags", {})
        if "building" not in tags:
            continue
        lats = [p["lat"] for p in el["geometry"]]
        lons = [p["lon"] for p in el["geometry"]]
        lat, lon = _centroid(lats, lons)
        height = _to_float(tags.get("height"))
        levels = _to_float(tags.get("building:levels"))
        if np.isnan(height) and not np.isnan(levels):
            height_src = "levels"
            height = levels * level_height_m
        else:
            height_src = "tag" if not np.isnan(height) else "missing"
        rows.append(
            {
                "osm_id": f"way/{el['id']}",
                "lat": lat,
                "lon": lon,
                "footprint_area_m2": polygon_area_m2(lats, lons),
                "building": tags.get("building"),
                "levels": levels,
                "height_m": height,
                "height_source": height_src,
                "start_year": _year(tags.get("start_date") or tags.get("building:start_date")),
                "roof_shape": tags.get("roof:shape"),
            }
        )
    return pd.DataFrame(rows)


def parse_pois(payload: dict, keys: Iterable[str] = POI_KEYS) -> pd.DataFrame:
    rows = []
    for el in payload.get("elements", []):
        tags = el.get("tags", {})
        if el.get("type") == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:
            c = el.get("center") or {}
            lat, lon = c.get("lat"), c.get("lon")
        if lat is None:
            continue
        for k in keys:
            if k in tags:
                rows.append({"osm_id": f"{el['type']}/{el['id']}", "lat": lat, "lon": lon, "key": k, "value": tags[k]})
                break
    return pd.DataFrame(rows)

"""Globally available open data layers (G1 inputs; K-025).

Rule: every input layer must exist, under an open licence, for (almost) every
country, so the same pipeline runs anywhere. Local datasets (İBB, TEDAŞ,
EPİAŞ, ...) are used only for validation (G2). Provenance of every layer is
documented in docs/11_veri_kaynaklari.md.

Layers implemented here
-----------------------
* administrative boundary  – OpenStreetMap relation via Overpass (ODbL)
* population               – JRC GHS-POP R2023A, 3 arc-second WGS84 tiles (CC BY 4.0)
* household electricity    – UN Statistics Division Energy Statistics Database via UNdata
                             ("Electricity - Consumption by households"; free reuse with citation)
* PV yield                 – EU JRC PVGIS 5.3 hourly PV output per kWp (SARAH-3 / ERA5)
"""

from __future__ import annotations

import html
import json
import math
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

__all__ = [
    "boundary_query",
    "boundary_rings",
    "points_in_polygon",
    "ghs_pop_tile_id",
    "ghs_pop_tile_url",
    "population_by_cell",
    "parse_undata_table",
    "pvgis_pv_url",
    "parse_pvgis_pv",
]

# ---------------------------------------------------------------- boundary (OSM)


def boundary_query(name: str, admin_level: Optional[int] = None, bbox: Optional[Tuple[float, float, float, float]] = None) -> str:
    lvl = f'["admin_level"="{admin_level}"]' if admin_level is not None else ""
    area = f"({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]})" if bbox else ""
    return f'[out:json][timeout:120];relation["boundary"="administrative"]["name"="{name}"]{lvl}{area};out geom;'


def _join_segments(segments: List[List[Tuple[float, float]]]) -> List[List[Tuple[float, float]]]:
    """Join way segments end-to-end into closed rings."""
    segs = [list(s) for s in segments if len(s) >= 2]
    rings = []
    while segs:
        ring = segs.pop(0)
        changed = True
        while changed and ring[0] != ring[-1]:
            changed = False
            for i, s in enumerate(segs):
                if s[0] == ring[-1]:
                    ring += s[1:]
                elif s[-1] == ring[-1]:
                    ring += s[::-1][1:]
                elif s[-1] == ring[0]:
                    ring = s[:-1] + ring
                elif s[0] == ring[0]:
                    ring = s[::-1][:-1] + ring
                else:
                    continue
                segs.pop(i)
                changed = True
                break
        if ring[0] == ring[-1] and len(ring) >= 4:
            rings.append(ring)
    return rings


def boundary_rings(payload: dict) -> Dict[str, object]:
    """Outer and inner rings (lists of (lat, lon)) of the first relation in an Overpass response."""
    rels = [e for e in payload.get("elements", []) if e.get("type") == "relation"]
    if not rels:
        raise ValueError("no relation in Overpass response")
    rel = rels[0]
    outer, inner = [], []
    for m in rel.get("members", []):
        if m.get("type") != "way" or "geometry" not in m:
            continue
        seg = [(p["lat"], p["lon"]) for p in m["geometry"]]
        (inner if m.get("role") == "inner" else outer).append(seg)
    return {
        "osm_id": f"relation/{rel['id']}",
        "tags": rel.get("tags", {}),
        "outer": _join_segments(outer),
        "inner": _join_segments(inner),
    }


def _pip(lat: np.ndarray, lon: np.ndarray, ring: Sequence[Tuple[float, float]]) -> np.ndarray:
    ry = np.array([p[0] for p in ring])
    rx = np.array([p[1] for p in ring])
    inside = np.zeros(lat.shape, bool)
    j = len(ring) - 1
    for i in range(len(ring)):
        cond = ((ry[i] > lat) != (ry[j] > lat)) & (lon < (rx[j] - rx[i]) * (lat - ry[i]) / (ry[j] - ry[i] + 1e-300) + rx[i])
        inside ^= cond
        j = i
    return inside


def points_in_polygon(lats, lons, outer: Sequence, inner: Sequence = ()) -> np.ndarray:
    """Even-odd point-in-polygon test for (multi)polygons given as rings of (lat, lon)."""
    lat = np.asarray(lats, float)
    lon = np.asarray(lons, float)
    inside = np.zeros(lat.shape, bool)
    for ring in outer:
        inside |= _pip(lat, lon, ring)
    for ring in inner:
        inside &= ~_pip(lat, lon, ring)
    return inside


# ---------------------------------------------------------------- population (GHS-POP)

GHS_POP_BASE = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A"


def ghs_pop_tile_id(lat: float, lon: float) -> str:
    """Row/column of the 10°×10° WGS84 tile grid used by GHSL 4326 products (R1 starts at 90°N, C1 at 180°W)."""
    row = int(math.floor((90.0 - lat) / 10.0)) + 1
    col = int(math.floor((lon + 180.0) / 10.0)) + 1
    return f"R{row}_C{col}"


def ghs_pop_tile_url(lat: float, lon: float, epoch: int = 2020) -> str:
    name = f"GHS_POP_E{epoch}_GLOBE_R2023A_4326_3ss"
    return f"{GHS_POP_BASE}/{name}/V1-0/tiles/{name}_V1_0_{ghs_pop_tile_id(lat, lon)}.zip"


def population_by_cell(tif_path: Path, bbox: Tuple[float, float, float, float], resolution: int,
                       mask: Optional[Dict[str, Sequence]] = None) -> pd.Series:
    """Sum GHS-POP pixels into H3 cells by pixel centre; optional polygon mask (outer/inner rings).

    Returns persons per cell (float; GHS-POP is a modelled, disaggregated count).
    """
    import rasterio
    from rasterio.windows import from_bounds

    from ..spatial.h3grid import assign_cells

    s, w, n, e = bbox
    with rasterio.open(tif_path) as src:
        win = from_bounds(w, s, e, n, transform=src.transform).round_offsets().round_lengths()
        arr = src.read(1, window=win).astype(float)
        nodata = src.nodata
        tr = src.window_transform(win)
    if nodata is not None:
        arr[arr == nodata] = 0.0
    arr[arr < 0] = 0.0
    rows, cols = np.nonzero(arr > 0)
    if rows.size == 0:
        return pd.Series(dtype=float)
    xs = tr.c + (cols + 0.5) * tr.a
    ys = tr.f + (rows + 0.5) * tr.e
    vals = arr[rows, cols]
    if mask is not None:
        keep = points_in_polygon(ys, xs, mask["outer"], mask.get("inner", ()))
        xs, ys, vals = xs[keep], ys[keep], vals[keep]
    cells = assign_cells(ys, xs, resolution)
    return pd.Series(vals, index=cells).groupby(level=0).sum().rename("population")


# ---------------------------------------------------------------- UNdata (UNSD energy statistics)

UNDATA_URL = "https://data.un.org/Data.aspx?d=EDATA&f=cmID%3aEL%3btrID%3a{tr}%3bcrID%3a{cr}"
UNDATA_TRANSACTIONS = {"households": 1231, "commercial_public_services": 1235}


def parse_undata_table(page_html: str) -> pd.DataFrame:
    """Rows (country, transaction, year, unit, value) from a UNdata EDATA results page."""
    rows = []
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", page_html, flags=re.S):
        c = [html.unescape(re.sub(r"<[^>]+>", "", x)).strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", r, flags=re.S)]
        if len(c) >= 5 and re.fullmatch(r"\d{4}", c[2] or ""):
            try:
                val = float(c[4].replace(",", ""))
            except ValueError:
                continue
            rows.append({"country": c[0], "transaction": c[1], "year": int(c[2]), "unit": c[3], "value": val})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- PVGIS PV output


def pvgis_pv_url(lat: float, lon: float, year: int, loss: float = 14.0, mounting: str = "building") -> str:
    """Hourly PV output of a 1 kWp crystalline-Si system at optimal tilt/azimuth (PVGIS 5.3).

    ``loss=14`` is the PVGIS default system loss; ``mounting='building'`` is PVGIS'
    building-integrated option (conservative module temperatures for rooftop arrays).
    """
    params = {
        "lat": lat, "lon": lon, "startyear": year, "endyear": year, "pvcalculation": 1, "peakpower": 1,
        "loss": loss, "pvtechchoice": "crystSi", "mountingplace": mounting, "optimalangles": 1, "outputformat": "json",
    }
    return "https://re.jrc.ec.europa.eu/api/v5_3/seriescalc?" + urllib.parse.urlencode(params)


def parse_pvgis_pv(payload: dict) -> pd.DataFrame:
    """Hourly AC output per kWp [kWh/kWp] (P in W for 1 kWp → /1000); 29 Feb dropped."""
    df = pd.DataFrame(payload["outputs"]["hourly"])
    ts = pd.to_datetime(df["time"], format="%Y%m%d:%H%M", utc=True)
    out = pd.DataFrame({"pv_kwh_per_kwp": df["P"].astype(float).to_numpy() / 1000.0}, index=ts)
    out = out[~((out.index.month == 2) & (out.index.day == 29))]
    return out

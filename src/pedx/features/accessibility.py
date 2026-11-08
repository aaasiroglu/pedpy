"""Pedestrian network accessibility per H3 cell (OSM walk network; "10-minute walk" metrics).

Method (transparent, dependency-light):
1. Build an undirected graph from OSM ``highway`` ways open to pedestrians;
   vertices = OSM geometry vertices (rounded to 1e-7°), edge weight = haversine length.
2. Each cell centroid, POI and transit stop is snapped to its nearest graph vertex
   (snap distance is reported; points > ``max_snap_m`` away are ignored).
3. Dijkstra from each cell's vertex with cutoff ``walk_m`` (800 m ≈ 10 min at 4.8 km/h).

Street-network metrics follow common practice in the walkability literature
(intersection density, street density; e.g. Boeing 2017, OSMnx). Requires
``networkx`` and ``scipy`` (``pip install pedx[morph]``).
"""

from __future__ import annotations

import math
from typing import Dict, Iterable

import numpy as np
import pandas as pd

__all__ = ["walk_graph", "accessibility_features", "DAILY_NEEDS"]

R = 6_371_008.8
DAILY_NEEDS = ("food_drink", "retail", "health", "education", "finance")


def _hav(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dl = np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def walk_graph(payload: dict):
    """networkx Graph of the pedestrian network (node attrs: lat, lon; edge attr: length m)."""
    import networkx as nx

    G = nx.Graph()
    for el in payload.get("elements", []):
        geom = el.get("geometry")
        if el.get("type") != "way" or not geom or len(geom) < 2:
            continue
        pts = [(round(p["lat"], 7), round(p["lon"], 7)) for p in geom]
        for (a, b) in zip(pts[:-1], pts[1:]):
            if a == b:
                continue
            d = float(_hav(a[0], a[1], b[0], b[1]))
            G.add_node(a, lat=a[0], lon=a[1])
            G.add_node(b, lat=b[0], lon=b[1])
            G.add_edge(a, b, length=d)
    return G


def _snap(G, lats, lons):
    from scipy.spatial import cKDTree

    nodes = list(G.nodes)
    arr = np.array(nodes)
    lat0 = math.radians(float(arr[:, 0].mean()))
    xy = np.c_[arr[:, 1] * math.cos(lat0), arr[:, 0]]
    tree = cKDTree(xy)
    q = np.c_[np.asarray(lons) * math.cos(lat0), np.asarray(lats)]
    _, idx = tree.query(q)
    snapped = [nodes[i] for i in idx]
    dist = _hav(np.asarray(lats), np.asarray(lons), arr[idx, 0], arr[idx, 1])
    return snapped, dist


def accessibility_features(G, cells: Iterable[str], pois: pd.DataFrame, stops: pd.DataFrame,
                           cell_area_ha: pd.Series, walk_m: float = 800.0, max_snap_m: float = 150.0) -> pd.DataFrame:
    """Per-cell walkability: street/intersection density and POIs/stops reachable within ``walk_m``.

    ``pois`` needs ``lat, lon, family``; ``stops`` needs ``lat, lon``.
    """
    import h3
    import networkx as nx

    cells = list(cells)
    # --- in-cell street length and intersections
    edge_mid_lat, edge_mid_lon, edge_len = [], [], []
    for a, b, d in G.edges(data="length"):
        edge_mid_lat.append((a[0] + b[0]) / 2)
        edge_mid_lon.append((a[1] + b[1]) / 2)
        edge_len.append(d)
    res = h3.get_resolution(cells[0])
    ecell = [h3.latlng_to_cell(la, lo, res) for la, lo in zip(edge_mid_lat, edge_mid_lon)]
    street_km = pd.Series(edge_len, index=ecell).groupby(level=0).sum() / 1000.0
    inter = [n for n, deg in G.degree() if deg >= 3]
    icell = pd.Series(1, index=[h3.latlng_to_cell(n[0], n[1], res) for n in inter]).groupby(level=0).sum()
    area_km2 = cell_area_ha.reindex(cells) / 100.0

    # --- snapping
    cen = [h3.cell_to_latlng(c) for c in cells]
    c_nodes, c_snap = _snap(G, [p[0] for p in cen], [p[1] for p in cen])
    p_nodes, p_snap = _snap(G, pois["lat"].to_numpy(), pois["lon"].to_numpy())
    s_nodes, s_snap = _snap(G, stops["lat"].to_numpy(), stops["lon"].to_numpy())
    poi_at: Dict[tuple, list] = {}
    for n, fam, d in zip(p_nodes, pois["family"].to_numpy(), p_snap):
        if d <= max_snap_m:
            poi_at.setdefault(n, []).append(fam)
    stop_at: Dict[tuple, int] = {}
    for n, d in zip(s_nodes, s_snap):
        if d <= max_snap_m:
            stop_at[n] = stop_at.get(n, 0) + 1

    rows = []
    for c, n, d in zip(cells, c_nodes, c_snap):
        if d > max_snap_m:
            rows.append({"cell": c})
            continue
        reach = nx.single_source_dijkstra_path_length(G, n, cutoff=walk_m, weight="length")
        fams = [f for v in reach if v in poi_at for f in poi_at[v]]
        daily = [f for f in fams if f in DAILY_NEEDS]
        rows.append({
            "cell": c,
            "mob_walk800_pois": len(fams),
            "mob_walk800_daily_needs": len(daily),
            "mob_walk800_daily_completeness": len(set(daily)) / len(DAILY_NEEDS),
            "mob_walk800_transit_stops": sum(stop_at.get(v, 0) for v in reach),
            "mob_walk800_network_km": sum(G.edges[u, v]["length"] for u, v in G.subgraph(reach).edges) / 1000.0,
        })
    out = pd.DataFrame(rows).set_index("cell")
    out["mob_street_density_km_per_km2"] = street_km.reindex(cells).fillna(0.0) / area_km2
    out["mob_intersection_density_per_km2"] = icell.reindex(cells).fillna(0.0) / area_km2
    return out


def network_complexity_features(payload: dict, G, cells, cell_area_ha: pd.Series, bins: int = 36) -> pd.DataFrame:
    """Street-network order and complexity per H3 cell (Boeing 2019, Applied Network Science 4:67).

    * orientation entropy H over 36 bearing bins (edges counted in both directions, length-weighted);
      orientation order φ = 1 − ((H − H_g)/(H_max − H_g))², H_max = ln 36, H_g = ln 4 (perfect grid)
    * circuity = OSM way polyline length / straight-line distance between its end points
    * dead-end share and streets per node among non-trivial nodes (degree ≠ 2)
    """
    import h3

    cells = list(cells)
    res = h3.get_resolution(cells[0])
    # --- bearings (length-weighted, both directions)
    lat1, lon1, lat2, lon2, length = [], [], [], [], []
    for a, b, d in G.edges(data="length"):
        lat1.append(a[0]); lon1.append(a[1]); lat2.append(b[0]); lon2.append(b[1]); length.append(d)
    lat1, lon1, lat2, lon2, length = map(np.asarray, (lat1, lon1, lat2, lon2, length))
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dl = np.radians(lon2 - lon1)
    brg = (np.degrees(np.arctan2(np.sin(dl) * np.cos(p2), np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl))) + 360) % 360
    ecell = np.array([h3.latlng_to_cell((x1 + x2) / 2, (y1 + y2) / 2, res) for x1, y1, x2, y2 in zip(lat1, lon1, lat2, lon2)])
    edges = pd.DataFrame({"cell": ecell, "b": brg, "w": length})
    hmax, hg = np.log(bins), np.log(4)

    def entropy(g):
        b = np.concatenate([g["b"].to_numpy(), (g["b"].to_numpy() + 180) % 360])
        w = np.concatenate([g["w"].to_numpy(), g["w"].to_numpy()])
        # bins centred on 0°, 10°, ... (offset half a bin as in Boeing 2019)
        hist, _ = np.histogram((b + 360 / bins / 2) % 360, bins=bins, range=(0, 360), weights=w)
        p = hist[hist > 0] / hist.sum()
        return float(-(p * np.log(p)).sum())

    H = edges.groupby("cell").apply(entropy, include_groups=False)
    # --- circuity per OSM way (assigned by way midpoint vertex)
    rows = []
    for el in payload.get("elements", []):
        g = el.get("geometry")
        if el.get("type") != "way" or not g or len(g) < 2:
            continue
        la = np.array([p["lat"] for p in g]); lo = np.array([p["lon"] for p in g])
        L = float(_hav(la[:-1], lo[:-1], la[1:], lo[1:]).sum())
        D = float(_hav(la[0], lo[0], la[-1], lo[-1]))
        if D > 5:
            m = len(g) // 2
            rows.append((h3.latlng_to_cell(la[m], lo[m], res), L, D))
    circ = pd.DataFrame(rows, columns=["cell", "L", "D"]).groupby("cell").sum()
    # --- node topology (degree ≠ 2)
    deg = pd.DataFrame([(h3.latlng_to_cell(n[0], n[1], res), d) for n, d in G.degree() if d != 2], columns=["cell", "deg"])
    gd = deg.groupby("cell")["deg"]
    out = pd.DataFrame(index=pd.Index(cells, name="cell"))
    out["mob_orientation_entropy"] = H.reindex(cells)
    out["mob_orientation_order"] = 1 - ((out["mob_orientation_entropy"] - hg) / (hmax - hg)) ** 2
    out["mob_circuity"] = (circ["L"] / circ["D"]).reindex(cells)
    out["mob_deadend_share"] = gd.apply(lambda s: float((s == 1).mean())).reindex(cells)
    out["mob_streets_per_node"] = gd.mean().reindex(cells)
    return out

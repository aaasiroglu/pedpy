"""Fit the total PED score and export the multi-city atlas for the web MVP (K-049).

1. For every cached city grid (data/cache/citygrid, built by validate_ped_sites.py): all inhabited
   candidate sites (k = 2 discs) → city statistics (mean, sd, median per score feature).
2. Fit the PED score (logistic, real PEDs vs inhabited controls) on z-scores against those city
   statistics — the same standardisation the browser and the API use at inference.
3. Leave-one-city-out: score each held-out city with a model that never saw it → AUC.
4. Export web/data/atlas.json: per city, one candidate site per H3 r9 cell (its centre r10 child,
   k = 2 disc ≈ 28 ha), with z-features, balance, population, footprint; plus the model.

    python scripts/build_atlas.py
"""

import json
import re
from pathlib import Path

import h3
import numpy as np
import pandas as pd

from pedx.score import LABELS_TR, SCORE_FEATURES, PEDScore, _z, candidate_discs, city_stats

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "data" / "validation"
GRID = ROOT / "data" / "cache" / "citygrid"
OUT = ROOT / "web" / "data" / "atlas.json"


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower().encode("ascii", "ignore").decode()).strip("_")


def main():
    sites = json.loads((VAL / "ped_sites.json").read_text())
    cities = [{"key": slug(s["site"]), "site": s["site"], "city": s["city"], "lat": s["lat"], "lon": s["lon"], "osm": s["osm"], "is_ped": True} for s in sites]
    cities.append({"key": "caferaa_istanbul", "site": "Caferağa", "city": "İstanbul", "lat": 40.9857, "lon": 29.0245, "osm": "relation/9441032", "is_ped": False})
    stats, grids = {}, {}
    for c in cities:
        F = pd.read_csv(GRID / f"{c['key']}_r10.csv", index_col=0)
        grids[c["key"]] = F
        stats[c["key"]] = city_stats(candidate_discs(F))
    # ---- training rows (cases + inhabited controls from the validation run)
    D = pd.read_csv(VAL / "ped_features.csv")
    key_of = {c["site"]: c["key"] for c in cities}
    D["key"] = D["site"].map(key_of)
    Z = np.vstack([_z(r._asdict(), stats[r.key]) for r in D[SCORE_FEATURES + ["key"]].itertuples(index=False)])
    y = (D["role"] == "case").astype(int).to_numpy()
    # ---- leave-one-city-out
    pct = {}
    for k in D["key"].unique():
        tr, te = (D["key"] != k).to_numpy(), (D["key"] == k).to_numpy()
        m = PEDScore.fit(Z[tr], y[tr])
        lg = Z[te] @ m.coef + m.intercept
        yy = y[te]
        case, ctl = lg[yy == 1][0], lg[yy == 0]
        pct[k] = float((ctl < case).mean() + 0.5 * (ctl == case).mean())
    auc = float(np.mean(list(pct.values())))
    model = PEDScore.fit(Z, y, n_cases=int(y.sum()), n_controls=int((1 - y).sum()), auc_loco=auc,
                         loco_percentiles=pct, standardisation="within-city over inhabited k=2 candidate discs")
    model.to_json(VAL / "ped_score_model.json")
    print(f"LOCO AUC = {auc:.3f}", {k: round(v, 2) for k, v in pct.items()})
    # ---- atlas export
    atlas = {"model": {"features": SCORE_FEATURES, "coef": [round(float(b), 5) for b in model.coef], "intercept": round(model.intercept, 5),
                       "labels_tr": LABELS_TR, "auc_loco": auc, "n_cases": int(y.sum()), "n_controls": int((1 - y).sum())},
             "cities": []}
    for c in cities:
        F, st = grids[c["key"]], stats[c["key"]]
        inhabited = F.index[(F["vul_pop_hrsl"] >= 20) & (F["ov_bld_footprint_m2"] > 0)]
        parents = sorted({h3.cell_to_parent(x, 9) for x in inhabited})
        centres = [h3.cell_to_center_child(p, 10) for p in parents]
        C = candidate_discs(F, centres=centres)
        keep = (C["vul_pop_hrsl"] >= 100) & (C["ov_bld_footprint_m2"] > 0) & np.isfinite(C["log_energy_balance"])
        C = C[keep]
        cells = []
        for centre, r in C.iterrows():
            z = _z(r.to_dict(), st)
            cells.append([h3.cell_to_parent(centre, 9), round(float(r["energy_balance"]), 3), round(float(r["vul_pop_hrsl"])),
                          round(float(r["ov_bld_footprint_m2"])), [round(float(v), 2) for v in z]])
        site_cell = h3.latlng_to_cell(c["lat"], c["lon"], 10)
        sx = candidate_discs(F, centres=[site_cell]).iloc[0].to_dict()
        e = model.explain(sx, st)
        prov = json.loads((GRID / f"{c['key']}_r10.json").read_text())
        atlas["cities"].append({
            **{k: c[k] for k in ("key", "site", "city", "lat", "lon", "osm", "is_ped")},
            "site_r9": h3.cell_to_parent(site_cell, 9), "site_score": round(e["score"], 1),
            "site_balance": round(float(sx["energy_balance"]), 3) if np.isfinite(sx["energy_balance"]) else None,
            "site_z": [round(v, 2) for v in e["z"].values()],
            "stats": {f: {"mean": round(st[f]["mean"], 5), "sd": round(st[f]["sd"], 5)} for f in SCORE_FEATURES},
            "country": (prov.get("country") or {}).get("name"), "kwh_per_capita": (prov.get("demand") or {}).get("kwh_per_capita"),
            "pv_yield": (prov.get("pv_yield") or {}).get("kwh_per_kwp"), "failures": list((prov.get("failures") or {}).keys()),
            "cells": cells})
        print(c["key"], len(cells), "site score", round(e["score"], 1))
    OUT.write_text(json.dumps(atlas, ensure_ascii=False, separators=(",", ":")))
    print(OUT, round(OUT.stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    main()

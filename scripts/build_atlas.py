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

from scipy.stats import wilcoxon

from pedx.report import REPORT, report_metrics
from pedx.score import LABELS_TR, PEDScore, _z, candidate_discs, city_stats

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "data" / "validation"
GRID = ROOT / "data" / "cache" / "citygrid"
OUT = ROOT / "web" / "data" / "atlas.json"


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower().encode("ascii", "ignore").decode()).strip("_")


def main():
    sites = json.loads((VAL / "ped_sites.json").read_text())
    cities = [{"key": slug(s["site"]), "site": s["site"], "city": s["city"], "lat": s["lat"], "lon": s["lon"], "osm": s["osm"], "is_ped": True} for s in sites]
    for a in json.loads((VAL / "pilot_areas.json").read_text()):  # pilot hierarchy Caferağa → Kadıköy → İstanbul (K-053)
        if (GRID / f"{a['key']}_r10.csv").exists():
            cities.append({**a, "is_ped": False})
    FA = json.loads((VAL / "feature_analysis.json").read_text())  # scripts/feature_analysis.py
    FEATS = FA["clean_features"]
    stats, grids = {}, {}
    for c in cities:
        F = pd.read_csv(GRID / f"{c['key']}_r10.csv", index_col=0)
        grids[c["key"]] = F
        stats[c["key"]] = city_stats(candidate_discs(F), FEATS)
    D = pd.read_csv(VAL / "ped_features.csv")
    key_of = {c["site"]: c["key"] for c in cities}
    D["key"] = D["site"].map(key_of)
    D = D[D["site"].isin(D.loc[D.role == "case"].dropna(subset=["energy_balance"])["site"])].reset_index(drop=True)
    Z = np.vstack([_z(dict(zip(FEATS, r[:-1])), stats[r[-1]], FEATS) for r in D[FEATS + ["key"]].itertuples(index=False)])
    y = (D["role"] == "case").astype(int).to_numpy()

    def evidence(train_keys):
        """Criteria weights ∝ |effect d| of features with BH q < 0.10 over the training cities (K-050)."""
        m = D["key"].isin(train_keys).to_numpy()
        ctl_mean = {k: Z[m & (D["key"] == k).to_numpy() & (y == 0)].mean(axis=0) for k in train_keys}
        dz = np.vstack([Z[m & (D["key"] == k).to_numpy() & (y == 1)][0] - ctl_mean[k] for k in train_keys])
        d = dz.mean(axis=0)
        p = np.array([wilcoxon(dz[:, j]).pvalue if np.any(dz[:, j] != 0) else 1.0 for j in range(dz.shape[1])])
        o = np.argsort(p); q = p[o] * len(p) / (np.arange(len(p)) + 1); q = np.minimum.accumulate(q[::-1])[::-1]
        qq = np.empty_like(q); qq[o] = np.minimum(q, 1)
        w = np.where(qq < 0.10, np.abs(d), 0.0)
        w = w / w.sum() if w.sum() > 0 else np.full(len(d), 1 / len(d))
        return w, np.where(d >= 0, 1.0, -1.0), d, qq

    keys = list(D["key"].unique())
    pct = {}
    for k in keys:  # leave-one-city-out: weights, directions and calibration never see the held-out city
        tr = (D["key"] != k).to_numpy()
        w, dr, _, _ = evidence([x for x in keys if x != k])
        m = PEDScore.from_weights(FEATS, w, dr, Z[tr], y[tr])
        lg = Z[~tr] @ m.coef + m.intercept
        yy = y[~tr]
        case, ctl = lg[yy == 1][0], lg[yy == 0]
        pct[k] = float((ctl < case).mean() + 0.5 * (ctl == case).mean())
    auc = float(np.mean(list(pct.values())))
    w, dr, d, q = evidence(keys)
    model = PEDScore.from_weights(FEATS, w, dr, Z, y, n_cases=int(y.sum()), n_controls=int((1 - y).sum()), auc_loco=auc,
                                  loco_percentiles=pct, effect_d=[float(v) for v in d], q_bh=[float(v) for v in q],
                                  standardisation="within-city over inhabited k=2 candidate discs",
                                  weighting="evidence: |d| of criteria with BH q<0.10; reverse-causal suspects excluded")
    keep = np.flatnonzero(w > 0)  # export only criteria that carry weight
    model = PEDScore(model.coef[keep], model.intercept, [FEATS[j] for j in keep],
                     meta=dict(model.meta, weights=[float(w[j]) for j in keep], direction=[float(dr[j]) for j in keep]))
    FEATS = model.features
    stats = {k: {f: v[f] for f in FEATS} for k, v in stats.items()}
    # area of applicability (Meyer & Pebesma 2021): weighted nearest-neighbour distance to training sites of OTHER cities;
    # threshold = 95th percentile of those leave-one-city-out distances over the training sites themselves
    Ztr, wk = Z[:, keep], np.asarray(model.meta["weights"])
    keys_arr = D["key"].to_numpy()
    dmin = []
    for i in range(len(Ztr)):
        other = keys_arr != keys_arr[i]
        dmin.append(float(np.sqrt(((Ztr[other] - Ztr[i]) ** 2 * wk).sum(axis=1)).min()))
    aoa = {"train_z": np.round(Ztr, 2).tolist(), "threshold": float(np.percentile(dmin, 95)), "method": "Meyer & Pebesma 2021, weighted NN distance, LOCO 95th pct"}
    model.to_json(VAL / "ped_score_model.json")
    print(f"LOCO AUC = {auc:.3f}", {k: round(v, 2) for k, v in pct.items()})
    print([(f, round(wt, 3)) for f, wt in zip(FEATS, model.meta["weights"])])
    # ---- atlas export
    atlas = {"model": {"features": FEATS, "coef": [round(float(b), 5) for b in model.coef], "intercept": round(model.intercept, 5),
                       "weights": [round(x, 4) for x in model.meta["weights"]], "direction": model.meta["direction"],
                       "labels_tr": LABELS_TR, "auc_loco": auc, "n_cases": int(y.sum()), "n_controls": int((1 - y).sum()),
                       "form": "MCDM: kanıta dayalı kriter ağırlıkları + Platt kalibrasyonu", "aoa": aoa},
             "report": REPORT,
             "cities": []}
    for c in cities:
        F, st = grids[c["key"]], stats[c["key"]]
        inhabited = F.index[(F["vul_pop_hrsl"] >= 20) & (F["ov_bld_footprint_m2"] > 0)]
        parents = sorted({h3.cell_to_parent(x, 9) for x in inhabited})
        centres = [h3.cell_to_center_child(p, 10) for p in parents]
        C = candidate_discs(F, centres=centres)
        keep = (C["vul_pop_hrsl"] >= 100) & (C["ov_bld_footprint_m2"] > 0) & np.isfinite(C["log_energy_balance"])
        C = C[keep]
        area_ha = 19 * h3.average_hexagon_area(10, unit="m^2") / 1e4
        RM = report_metrics(C, area_ha)

        def rnd(v):
            return None if v is None or not np.isfinite(v) else float(f"{v:.3g}")

        cells = []
        for centre, r in C.iterrows():
            z = _z(r.to_dict(), st, FEATS)
            cells.append([h3.cell_to_parent(centre, 9), round(float(r["energy_balance"]), 3), round(float(r["vul_pop_hrsl"])),
                          round(float(r["ov_bld_footprint_m2"])), [round(float(v), 2) for v in z], [rnd(v) for v in RM.loc[centre].to_numpy(float)]])
        site_cell = h3.latlng_to_cell(c["lat"], c["lon"], 10)
        sx = candidate_discs(F, centres=[site_cell]).iloc[0].to_dict()
        e = model.explain(sx, st)
        prov = json.loads((GRID / f"{c['key']}_r10.json").read_text())
        atlas["cities"].append({
            **{k: c[k] for k in ("key", "site", "city", "lat", "lon", "osm", "is_ped")},
            "site_r9": h3.cell_to_parent(site_cell, 9), "site_score": round(e["score"], 1),
            "site_balance": round(float(sx["energy_balance"]), 3) if np.isfinite(sx["energy_balance"]) else None,
            "site_z": [round(v, 2) for v in e["z"].values()],
            "stats": {f: {"mean": round(st[f]["mean"], 5), "sd": round(st[f]["sd"], 5)} for f in FEATS},
            "country": (prov.get("country") or {}).get("name"), "kwh_per_capita": (prov.get("demand") or {}).get("kwh_per_capita"),
            "pv_yield": (prov.get("pv_yield") or {}).get("kwh_per_kwp"), "failures": list((prov.get("failures") or {}).keys()),
            "cells": cells})
        print(c["key"], len(cells), "site score", round(e["score"], 1))
    OUT.write_text(json.dumps(atlas, ensure_ascii=False, separators=(",", ":")))
    print(OUT, round(OUT.stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    main()

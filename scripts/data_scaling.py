"""Data-scaling curve: does adding data families make the decision more certain? (K-044)

The thesis' overarching question — "with unlimited data, could a decision-support engine decide
with certainty?" (Laplace's demon) — is made testable as a value-of-information experiment:
feature families are added one at a time (fixed order, set before results) and, at each step, the
leave-one-city-out AUC of recognising real PEDs among inhabited controls is computed, with a
bootstrap 90 % interval over sites. Saturation of the curve + width of the interval = how much
more data can still buy, and how much uncertainty is irreducible at this sample size.

Reads data/validation/ped_features.csv (scripts/validate_ped_sites.py); no new downloads.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "data" / "validation"
SEED = 20261108
FAMILIES = [  # cumulative order: physics first, then increasingly indirect evidence
    ("Fizik: enerji dengesi", ["log_energy_balance"]),
    ("+ Yapılı çevre (Overture)", ["footprint_coverage", "log_footprint_per_capita_m2", "ov_floors_coverage", "ov_nonosm_share"]),
    ("+ Demografi ve kırılganlık (HRSL)", ["pop_density_per_ha", "elderly_share", "children_share"]),
    ("+ Uydu: Sentinel-2, Landsat, WorldCover", ["env_ndvi_mean", "env_ndbi_mean", "env_lst_anomaly_c", "env_wc_green_share", "env_wc_water_share"]),
    ("+ Arazi (Copernicus DEM)", ["env_slope_deg", "env_relief_m"]),
    ("+ Kentsel işlev (Overture mekânlar)", ["places_per_1000", "ov_places_categories"]),
    ("+ Altyapı (trafo, EV, toplu taşıma)", ["transit_per_km2", "grid_assets_per_km2", "ev_chargers_per_km2"]),
]


def z_within(D, cols):
    out = []
    for _, g in D.groupby("site"):
        X = g[cols].astype(float)
        X = X.fillna(X.median())
        out.append(((X - X.mean()) / X.std(ddof=0).replace(0, 1.0)).fillna(0.0))
    return pd.concat(out).loc[D.index]


def loco_percentiles(D, cols):
    Z, y = z_within(D, cols), (D["role"] == "case").astype(int).to_numpy()
    score = pd.Series(np.nan, index=D.index)
    for s in D["site"].unique():
        tr, te = D["site"] != s, D["site"] == s
        m = LogisticRegression(C=0.5, class_weight="balanced", max_iter=2000).fit(Z[tr], y[tr])
        score[te] = m.decision_function(Z[te])
    pct = {}
    for s, g in D.groupby("site"):
        c, k = score[g.index[g.role == "case"]].iloc[0], score[g.index[g.role == "control"]]
        pct[s] = float((k < c).mean() + 0.5 * (k == c).mean())
    return pd.Series(pct)


if __name__ == "__main__":
    D = pd.read_csv(VAL / "ped_features.csv")
    D = D[D["site"].isin(D.loc[D.role == "case"].dropna(subset=["log_energy_balance"])["site"])].reset_index(drop=True)
    rng = np.random.default_rng(SEED)
    cols, rows = [], []
    for name, fam in FAMILIES:
        cols = cols + [c for c in fam if c in D and D[c].notna().any()]
        p = loco_percentiles(D, cols)
        boots = [p.sample(len(p), replace=True, random_state=int(rng.integers(1e9))).mean() for _ in range(2000)]
        rows.append({"step": name, "n_features": len(cols), "auc": float(p.mean()), "ci05": float(np.percentile(boots, 5)),
                     "ci95": float(np.percentile(boots, 95)), "sites_above_half": int((p > 0.5).sum()), "n_sites": int(len(p))})
        print(rows[-1], flush=True)
    out = {"curve": rows, "n_sites": rows[-1]["n_sites"], "seed": SEED,
           "reading": "AUC = probability that a real PED outranks an inhabited control of its own city (leave-one-city-out); "
                      "90 % bootstrap interval over sites."}
    (VAL / "data_scaling.json").write_text(json.dumps(out, indent=1))

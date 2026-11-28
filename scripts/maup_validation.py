"""MAUP on the external validation: does recognising real PEDs depend on the site scale? (K-052)

Same 16 real PED sites, same rule for controls (inhabited, built, ≥ 1.5 km, 30 per city, fixed seed),
site discs of k = 1 (7 r10 cells ≈ 10 ha), k = 2 (≈ 28 ha), k = 3 (≈ 55 ha), k = 4 (≈ 90 ha).
Two scores: (a) annual balance; (b) the 5 clean criteria of the PED score with their fixed weights
and directions (data/validation/ped_score_model.json), z-scored within city over that scale's candidates.
"""

import json
import re
from pathlib import Path

import h3
import numpy as np
import pandas as pd

from pedx.score import _z, candidate_discs, city_stats

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "data" / "validation"
GRID = ROOT / "data" / "cache" / "citygrid"
SEED = 20261108


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower().encode("ascii", "ignore").decode()).strip("_")


def pct(case, ctl):
    ctl = ctl[np.isfinite(ctl)]
    return float((ctl < case).mean() + 0.5 * (ctl == case).mean()) if np.isfinite(case) and ctl.size else np.nan


if __name__ == "__main__":
    M = json.loads((VAL / "ped_score_model.json").read_text())
    feats, w, dr = M["features"], np.array(M["meta"]["weights"]), np.array(M["meta"]["direction"])
    sites = json.loads((VAL / "ped_sites.json").read_text())
    rows = []
    for k in (1, 2, 3, 4):
        rng = np.random.default_rng(SEED)
        for s in sites:
            F = pd.read_csv(GRID / f"{slug(s['site'])}_r10.csv", index_col=0)
            site = h3.latlng_to_cell(s["lat"], s["lon"], 10)
            la0, lo0 = h3.cell_to_latlng(site)
            ok = F.index[(F["vul_pop_hrsl"] >= 20) & (F["ov_bld_footprint_m2"] > 0)]
            far = [c for c in ok if h3.great_circle_distance((la0, lo0), h3.cell_to_latlng(c), unit="km") >= 1.5]
            ctl = list(rng.choice(far, size=min(30, len(far)), replace=False))
            allc = candidate_discs(F, k=k)
            st = city_stats(allc, feats)
            C = candidate_discs(F, k=k, centres=[site] + ctl)
            Z = np.vstack([_z(r.to_dict(), st, feats) for _, r in C.iterrows()])
            sc = Z @ (w * dr)
            B = C["energy_balance"].to_numpy(float)
            rows.append({"k": k, "site": s["site"], "pct_balance": pct(B[0], B[1:]), "pct_score": pct(sc[0], sc[1:])})
        print(k, flush=True)
    R = pd.DataFrame(rows)
    area = {k: (1 + 3 * k * (k + 1)) * h3.average_hexagon_area(10, unit="m^2") / 1e4 for k in (1, 2, 3, 4)}
    S = R.groupby("k").agg(auc_balance=("pct_balance", "mean"), auc_score=("pct_score", "mean"),
                           above_half_balance=("pct_balance", lambda x: int((x > 0.5).sum())), above_half_score=("pct_score", lambda x: int((x > 0.5).sum())),
                           n=("site", "size")).reset_index()
    S["site_area_ha"] = S["k"].map(area)
    (VAL / "maup_validation.json").write_text(json.dumps({"summary": S.round(4).to_dict(orient="records"), "per_site": R.round(4).to_dict(orient="records")}, ensure_ascii=False, indent=1))
    print(S.round(3).to_string())

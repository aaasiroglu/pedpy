"""Classic MCDM vs the learned PED score on the real-PED case–control design (K-060).

Question (operations research): do classic multi-criteria methods — with objective weights (equal, CRITIC,
entropy) or with our evidence weights — rank the real PED site above the inhabited controls of its own city as
well as the PED score does? Same data, same within-city z-scores, same leave-one-city-out (LOCO) protocol as
scripts/build_atlas.py; the metric is the held-out case's percentile among its city's controls (mean = AUC).

* Criteria directions (benefit/cost) come from the training cities only (sign of the case–control effect d).
* Objective weights (CRITIC, entropy, equal) are computed on the held-out city's own decision matrix — no labels.
* Aggregations from pymcdm 1.4 (MIT; Kizielewicz et al. 2023): WSM, TOPSIS, VIKOR, PROMETHEE II, SPOTIS, MARCOS,
  COMET is omitted (its characteristic-object grid grows as 3^n with n criteria).
* Implementation check: pedx.mcdm (TOPSIS, CRITIC, entropy) against pymcdm on every city matrix.

    python scripts/mcdm_benchmark.py   → data/validation/mcdm_benchmark.json
"""

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from pymcdm import methods as pm
from pymcdm import normalizations as pn
from pymcdm import weights as pw
from scipy.stats import kendalltau, wilcoxon

from pedx import mcdm as px
from pedx.score import PEDScore, _z, candidate_discs, city_stats

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "data" / "validation"
GRID = ROOT / "data" / "cache" / "citygrid"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower().encode("ascii", "ignore").decode()).strip("_")


def load():
    sites = json.loads((VAL / "ped_sites.json").read_text())
    key_of = {s["site"]: slug(s["site"]) for s in sites}
    FEATS = json.loads((VAL / "feature_analysis.json").read_text())["clean_features"]
    stats = {k: city_stats(candidate_discs(pd.read_csv(GRID / f"{k}_r10.csv", index_col=0)), FEATS) for k in set(key_of.values())}
    D = pd.read_csv(VAL / "ped_features.csv")
    D["key"] = D["site"].map(key_of)
    D = D[D["site"].isin(D.loc[D.role == "case"].dropna(subset=["energy_balance"])["site"])].reset_index(drop=True)
    Z = np.vstack([_z(dict(zip(FEATS, r[:-1])), stats[r[-1]], FEATS) for r in D[FEATS + ["key"]].itertuples(index=False)])
    return FEATS, D, Z, (D["role"] == "case").astype(int).to_numpy()


def evidence(Z, y, keys_arr, train_keys):
    """Same as build_atlas.evidence: |d| of criteria with BH q < 0.10, directions = sign(d)."""
    dz = np.vstack([Z[(keys_arr == k) & (y == 1)][0] - Z[(keys_arr == k) & (y == 0)].mean(axis=0) for k in train_keys])
    d = dz.mean(axis=0)
    p = np.array([wilcoxon(dz[:, j]).pvalue if np.any(dz[:, j] != 0) else 1.0 for j in range(dz.shape[1])])
    o = np.argsort(p); q = p[o] * len(p) / (np.arange(len(p)) + 1); q = np.minimum.accumulate(q[::-1])[::-1]
    qq = np.empty_like(q); qq[o] = np.minimum(q, 1)
    w = np.where(qq < 0.10, np.abs(d), 0.0)
    return (w / w.sum() if w.sum() > 0 else np.full(len(d), 1 / len(d))), np.where(d >= 0, 1, -1)


def pct_of_case(pref, y, higher_better=True):
    s = pref if higher_better else -pref
    case, ctl = s[y == 1][0], s[y == 0]
    return float((ctl < case).mean() + 0.5 * (ctl == case).mean())


def main():
    FEATS, D, Z, y = load()
    keys_arr = D["key"].to_numpy()
    keys = list(dict.fromkeys(keys_arr))
    METHODS = {
        "WSM": (lambda: pm.WSM(), True), "TOPSIS": (lambda: pm.TOPSIS(), True), "VIKOR": (lambda: pm.VIKOR(), False),
        "PROMETHEE II": (lambda: pm.PROMETHEE_II("usual"), True), "MARCOS": (lambda: pm.MARCOS(), True),
        "SPOTIS": (None, False),  # needs bounds from the matrix
    }
    rows, checks = [], []
    for k in keys:
        tr_keys = [x for x in keys if x != k]
        tr, te = keys_arr != k, keys_arr == k
        w_ev, dr = evidence(Z, y, keys_arr, tr_keys)
        X, yy = Z[te], y[te]
        Xp = X - X.min(axis=0) + 1.0  # strictly positive copy (MARCOS ratios); min-max based methods are shift-invariant
        live = X.std(axis=0) > 1e-12  # criteria constant within the city carry no information
        Xl, drl = Xp[:, live], dr[live]
        weights = {"eşit": pw.equal_weights(Xl), "CRITIC": pw.critic_weights(Xl, drl), "entropi": pw.entropy_weights(Xl),
                   "kanıt (öğrenilmiş)": (w_ev[live] / w_ev[live].sum()) if w_ev[live].sum() > 0 else pw.equal_weights(Xl)}
        for wname, w in weights.items():
            for mname, (mk, hb) in METHODS.items():
                if mname == "SPOTIS":
                    pref = pm.SPOTIS(np.vstack([Xl.min(0), Xl.max(0)]).T)(Xl, w, drl)
                else:
                    pref = mk()(Xl, w, drl)
                rows.append({"city": k, "weights": wname, "method": mname, "pct": pct_of_case(np.asarray(pref, float), yy, hb)})
        # the PED score itself (logistic calibration of the evidence-weighted sum), for reference
        m = PEDScore.from_weights(FEATS, w_ev, dr.astype(float), Z[tr], y[tr])
        rows.append({"city": k, "weights": "kanıt (öğrenilmiş)", "method": "PED skoru (lojistik)", "pct": pct_of_case(X @ m.coef + m.intercept, yy)})
        # implementation check: pedx.mcdm vs pymcdm on this city's matrix
        ben = drl > 0
        t_px = px.topsis(Xl, weights["eşit"], ben)["score"]
        t_pm = pm.TOPSIS(pn.vector_normalization)(Xl, weights["eşit"], drl)
        c_px = px.critic_weights(Xl, ben)[0]
        e_px = px.entropy_weights(Xl, ben)[0]
        e_pm = weights["entropi"]  # pymcdm: sum-normalised raw matrix; pedx: direction-aware min-max first
        checks.append({"city": k, "topsis_max_abs_diff": float(np.abs(t_px - t_pm).max()), "topsis_kendall": float(kendalltau(t_px, t_pm)[0]),
                       "critic_max_abs_diff": float(np.abs(c_px - weights["CRITIC"]).max()),
                       "entropy_max_abs_diff": float(np.abs(e_px - e_pm).max())})
    R = pd.DataFrame(rows)
    S = (R.groupby(["method", "weights"])["pct"].agg(auc="mean", hit_top10=lambda s: int((s >= 0.9).sum()), n="size")
         .reset_index().sort_values("auc", ascending=False))
    C = pd.DataFrame(checks)
    print(S.round(3).to_string(index=False))
    print(C.describe().loc[["mean", "max"]].round(6).to_string())
    (VAL / "mcdm_benchmark.json").write_text(json.dumps({
        "summary": S.round(4).to_dict(orient="records"), "per_city": R.round(4).to_dict(orient="records"),
        "implementation_check": C.round(8).to_dict(orient="records"), "n_cities": len(keys), "n_criteria": len(FEATS),
        "protocol": "leave-one-city-out; directions from training cities; objective weights on the held-out city matrix",
        "library": "pymcdm 1.4.0 (MIT)"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

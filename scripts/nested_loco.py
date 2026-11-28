"""Nested leave-one-city-out: is the weighting scheme of the PED score chosen without peeking? (K-061)

K-060 found that equal weights (with directions learned from the training cities) ranked the real PEDs better
than the sparse evidence weights (0.88 vs 0.80), but that number was the best of 25 combinations — optimistic.
Here the *choice* of the scheme is itself inside the cross-validation:

  outer loop: hold out city k
      inner loop over the 15 training cities: for each candidate scheme, leave one training city out, fit on the
      other 14, score the left-out one → inner AUC per scheme
      pick the scheme with the best inner AUC (ties → the simpler scheme: fewer free parameters)
      fit that scheme on all 15 training cities → score city k
  nested AUC = mean percentile of the held-out PED over the 16 outer folds

Candidates are restricted to what the core contract allows (pedx.score.PEDScore.from_weights): a weighted sum of
within-city z-scores with fixed global weights, Platt-calibrated. Weight schemes:
  equal      w_j = 1/n, direction = sign(d) on training cities
  evidence   |d| of criteria with BH q < 0.10 (current core, K-050)
  CRITIC     on the pooled training z-matrix (direction-aware, pedx.mcdm)
  entropy    on the pooled training z-matrix (direction-aware, pedx.mcdm)

    python scripts/nested_loco.py   → data/validation/nested_loco.json
"""

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from mcdm_benchmark import load  # noqa: E402

from pedx import mcdm as px  # noqa: E402

SIMPLICITY = {"eşit": 0, "CRITIC": 1, "entropi": 1, "kanıt": 2}  # tie-break: fewer fitted quantities first


def effects(Z, y, keys_arr, train):
    dz = np.vstack([Z[(keys_arr == k) & (y == 1)][0] - Z[(keys_arr == k) & (y == 0)].mean(axis=0) for k in train])
    return dz


def scheme(name, Z, y, keys_arr, train):
    """(weights, directions) fitted on the training cities only."""
    dz = effects(Z, y, keys_arr, train)
    d = dz.mean(axis=0)
    dr = np.where(d >= 0, 1.0, -1.0)
    n = Z.shape[1]
    if name == "eşit":
        return np.full(n, 1 / n), dr
    if name == "kanıt":
        p = np.array([wilcoxon(dz[:, j]).pvalue if np.any(dz[:, j] != 0) else 1.0 for j in range(n)])
        o = np.argsort(p); q = p[o] * n / (np.arange(n) + 1); q = np.minimum.accumulate(q[::-1])[::-1]
        qq = np.empty_like(q); qq[o] = np.minimum(q, 1)
        w = np.where(qq < 0.10, np.abs(d), 0.0)
        return (w / w.sum() if w.sum() > 0 else np.full(n, 1 / n)), dr
    m = np.isin(keys_arr, train)
    ben = dr > 0
    w = (px.critic_weights if name == "CRITIC" else px.entropy_weights)(Z[m], ben)[0]
    return w, dr


def pct(Z, y, keys_arr, k, w, dr):
    """Percentile of city k's PED among its controls under score Σ w·dir·z (Platt is monotone, so ranks suffice)."""
    m = keys_arr == k
    s = Z[m] @ (w * dr)
    case, ctl = s[y[m] == 1][0], s[y[m] == 0]
    return float((ctl < case).mean() + 0.5 * (ctl == case).mean())


def main():
    FEATS, D, Z, y = load()
    keys_arr = D["key"].to_numpy()
    keys = list(dict.fromkeys(keys_arr))
    names = list(SIMPLICITY)
    plain = {s: {} for s in names}  # ordinary LOCO per scheme (for reference)
    nested, chosen, inner_tab = {}, {}, {}
    for k in keys:
        train = [x for x in keys if x != k]
        for s in names:
            w, dr = scheme(s, Z, y, keys_arr, train)
            plain[s][k] = pct(Z, y, keys_arr, k, w, dr)
        inner = {}
        for s in names:
            vals = []
            for j in train:
                inner_train = [x for x in train if x != j]
                w, dr = scheme(s, Z, y, keys_arr, inner_train)
                vals.append(pct(Z, y, keys_arr, j, w, dr))
            inner[s] = float(np.mean(vals))
        best = max(names, key=lambda s: (round(inner[s], 6), -SIMPLICITY[s]))
        chosen[k], inner_tab[k] = best, inner
        nested[k] = plain[best][k]  # fit on all training cities = the plain LOCO model of that scheme
        print(k, "inner:", {s: round(v, 3) for s, v in inner.items()}, "→", best, "outer pct", round(nested[k], 2), flush=True)
    auc = {s: float(np.mean(list(plain[s].values()))) for s in names}
    nested_auc = float(np.mean(list(nested.values())))
    tests = {s: float(wilcoxon([plain[s][k] for k in keys], [plain["kanıt"][k] for k in keys]).pvalue) for s in names if s != "kanıt"}
    counts = {s: sum(v == s for v in chosen.values()) for s in names}
    print("plain LOCO AUC", {s: round(v, 3) for s, v in auc.items()})
    print("nested AUC", round(nested_auc, 3), "chosen", counts, "wilcoxon vs kanıt", {s: round(v, 3) for s, v in tests.items()})
    out = {"plain_loco_auc": auc, "nested_auc": nested_auc, "chosen_per_fold": chosen, "chosen_counts": counts,
           "inner_auc": inner_tab, "outer_pct": nested, "plain_pct": plain, "wilcoxon_vs_evidence": tests,
           "n_cities": len(keys), "n_criteria": len(FEATS), "candidates": names,
           "rule": "adopt the nested winner as core only if it is chosen in the majority of folds and its plain LOCO AUC >= evidence"}
    (ROOT / "data" / "validation" / "nested_loco.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

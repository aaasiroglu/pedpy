"""Uncertainty of the headline numbers with n = 16 cities (K-065).

* 95% bootstrap intervals (cities resampled, 10 000 draws) for every reported AUC.
* Paired sign-flip permutation test (exact, 2^16) for the difference between weighting schemes.
* Duplicate check: within a city, log energy balance and log roof area per capita have identical z-scores
  (irradiance and per-capita demand are city constants), so the clean set holds 30 independent criteria, not 31.

    python scripts/uncertainty.py   → data/validation/uncertainty.json
"""

import itertools
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from mcdm_benchmark import load  # noqa: E402
from nested_loco import pct, scheme  # noqa: E402

RNG = np.random.default_rng(0)


def ci(v, n=10000):
    v = np.asarray(v); b = RNG.choice(v, (n, len(v))).mean(axis=1)
    return {"auc": float(v.mean()), "ci95": [float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))],
            "above_half": int((v > 0.5).sum()), "n": len(v)}


def signflip(a, b):
    d = np.asarray(a) - np.asarray(b); obs = abs(d.mean())
    signs = np.array(list(itertools.product([1, -1], repeat=len(d))))
    return float((np.abs((signs * d).mean(axis=1)) >= obs - 1e-12).mean())


def main():
    FEATS, D, Z, y = load()
    ka = D["key"].to_numpy(); keys = list(dict.fromkeys(ka))
    nl = json.loads((ROOT / "data/validation/nested_loco.json").read_text())
    P = {s: [nl["plain_pct"][s][k] for k in keys] for s in nl["candidates"]}
    P["iç içe seçim"] = [nl["outer_pct"][k] for k in keys]
    jb, jf = FEATS.index("log_energy_balance"), FEATS.index("log_footprint_per_capita_m2")
    P["yalnız enerji dengesi"] = [pct(Z, y, ka, k, np.eye(len(FEATS))[jb], np.ones(len(FEATS))) for k in keys]
    idx = [j for j in range(len(FEATS)) if j != jf]
    P["eşit, 30 ölçüt (yineleme çıkarıldı)"] = [pct(Z[:, idx], y, ka, k, *scheme("eşit", Z[:, idx], y, ka, [x for x in keys if x != k])) for k in keys]
    out = {"auc": {s: ci(v) for s, v in P.items()},
           "paired_signflip_p": {f"{a} − {b}": signflip(P[a], P[b]) for a, b in
                                 [("eşit", "kanıt"), ("eşit", "CRITIC"), ("eşit", "entropi"), ("eşit", "yalnız enerji dengesi"),
                                  ("eşit", "eşit, 30 ölçüt (yineleme çıkarıldı)")]},
           "duplicate": {"pair": ["log_energy_balance", "log_footprint_per_capita_m2"],
                         "corr_z": float(np.corrcoef(Z[:, jb], Z[:, jf])[0, 1]), "max_abs_diff_z": float(np.abs(Z[:, jb] - Z[:, jf]).max())},
           "n_cities": len(keys)}
    (ROOT / "data/validation/uncertainty.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for s, r in out["auc"].items():
        print(f"{s:38s} {r['auc']:.3f} [{r['ci95'][0]:.2f}, {r['ci95'][1]:.2f}] {r['above_half']}/{r['n']}")
    print(out["paired_signflip_p"]); print(out["duplicate"])


if __name__ == "__main__":
    main()

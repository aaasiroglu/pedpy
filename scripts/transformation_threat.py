"""Does the PED score learn "PED-suitable" or just "urban transformation area"? (K-064)

Threat: real PEDs were mostly sited where the municipality was redeveloping anyway (docks, old industry, airfields).
A score trained on them may only recognise redevelopment land. Tests, all on the same case–control data
(16 PEDs × 30 inhabited controls) and the same leave-one-city-out equal-weight score as the core:

 T1  transformation index T — built only from proxies that are NOT in the score: GHSL non-residential share,
     OSM construction land, WorldCover bare share, (minus) OSM residential land. Within-city mean rank.
     How well does T alone rank the real PED?  (if T ≈ score, the threat is real)
 T2  among controls only (no labels): correlation of the score with T.
 T3  conditional test: per city regress score on T over the controls, rank the PED's residual among control
     residuals; and rank the PED among the 10 controls closest to it in T.
 T4  what carries the score: per-feature share of the case–control gap, correlation of each feature with T,
     AUC of the score rebuilt without the T-loaded features, leave-one-family-out.
 T5  PED type (hand-labelled from project descriptions, see TYPE): new development on redevelopment land vs
     retrofit of an existing inhabited neighbourhood. A transformation detector should fail on retrofits.

    python scripts/transformation_threat.py   → data/validation/transformation_threat.json
"""

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import rankdata, spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from mcdm_benchmark import load  # noqa: E402
from nested_loco import pct, scheme  # noqa: E402

# a-priori grouping from the projects' own descriptions (not from our data) — to be confirmed with sources
TYPE = {"buiksloterham": "yeni", "zorrotzaurre": "yeni", "confluence": "yeni", "le_de_nantes": "yeni",
        "kalasatama": "yeni", "linnakaupunki": "yeni", "seestadt_aspern": "yeni", "fornebu": "yeni",
        "brunnshg": "yeni", "kera": "yeni", "rosendal": "yeni",
        "leppvaara": "mevcut", "coronacin": "mevcut", "fontaine_d_ouche": "mevcut", "kaukovainio": "mevcut",
        "paddepoel": "mevcut"}
RNG = np.random.default_rng(0)


def case_pct(v, y):
    case, ctl = v[y == 1][0], v[y == 0]
    return float((ctl < case).mean() + 0.5 * (ctl == case).mean())


def boot(vals, n=10000):
    v = np.asarray(vals)
    b = RNG.choice(v, (n, len(v))).mean(axis=1)
    return [float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))]


def summ(d, keys):
    v = [d[k] for k in keys]
    return {"auc": float(np.mean(v)), "ci95": boot(v), "n": len(v), "above_half": int(sum(x > 0.5 for x in v))}


def main():
    FEATS, D, Z, y = load()
    ka = D["key"].to_numpy()
    keys = list(dict.fromkeys(ka))
    fam = json.loads((ROOT / "data/validation/feature_analysis.json").read_text())["families"]
    prox = {
        "konut dışı yapı payı (GHSL)": (D["ghsl_nres_m2"] / D["ghsl_built_m2"].where(D["ghsl_built_m2"] > 0)).fillna(0).to_numpy(),
        "inşaat alanı (OSM)": D["lu_construction_m2"].fillna(0).to_numpy(),
        "çıplak alan payı (WorldCover)": D["env_wc_bare_share"].fillna(0).to_numpy(),
        "konut alanı azlığı (OSM)": -D["lu_residential_m2"].fillna(0).to_numpy(),
    }
    # within-city ranks (0..1) and the index T
    R = {p: np.zeros(len(D)) for p in prox}
    for k in keys:
        m = ka == k
        for p, v in prox.items():
            R[p][m] = (rankdata(v[m]) - 1) / (m.sum() - 1)
    T = np.mean(list(R.values()), axis=0)

    # LOCO equal-weight score for every row, and plain percentiles
    S = np.zeros(len(D)); W = {}
    for k in keys:
        w, dr = scheme("eşit", Z, y, ka, [x for x in keys if x != k])
        S[ka == k] = Z[ka == k] @ (w * dr); W[k] = dr
    jb = FEATS.index("log_energy_balance")
    per = {"skor": {}, "T": {}, "denge": {}, "skor|T artık": {}, "skor|T en yakın 10": {}, "denge|T artık": {},
           "denge|konut dışı pay artık": {}}
    per.update({p: {} for p in prox})
    rho_ctl = {}
    for k in keys:
        m = ka == k; yy = y[m]; s = S[m]; t = T[m]
        per["skor"][k] = case_pct(s, yy); per["T"][k] = case_pct(t, yy); per["denge"][k] = case_pct(Z[m][:, jb], yy)
        for p in prox:
            per[p][k] = case_pct(R[p][m], yy)
        c = yy == 0
        b = np.polyfit(t[c], s[c], 1)
        per["skor|T artık"][k] = case_pct(s - np.polyval(b, t), yy)
        e = Z[m][:, jb]; nr = R["konut dışı yapı payı (GHSL)"][m]
        per["denge|T artık"][k] = case_pct(e - np.polyval(np.polyfit(t[c], e[c], 1), t), yy)
        per["denge|konut dışı pay artık"][k] = case_pct(e - np.polyval(np.polyfit(nr[c], e[c], 1), nr), yy)
        near = np.argsort(np.abs(t[c] - t[yy == 1][0]))[:10]
        ctl = s[c][near]; cs = s[yy == 1][0]
        per["skor|T en yakın 10"][k] = float((ctl < cs).mean() + 0.5 * (ctl == cs).mean())
        rho_ctl[k] = float(spearmanr(s[c], t[c]).statistic)

    # T4: what carries the score
    dz = np.vstack([Z[(ka == k) & (y == 1)][0] - Z[(ka == k) & (y == 0)].mean(axis=0) for k in keys])
    d = dz.mean(axis=0); dr = np.where(d >= 0, 1.0, -1.0); gap = np.abs(d)
    ctl = y == 0
    rT = np.array([np.mean([spearmanr(Z[(ka == k) & ctl][:, j] * dr[j], T[(ka == k) & ctl]).statistic
                            if np.std(Z[(ka == k) & ctl][:, j]) > 0 else 0.0 for k in keys]) for j in range(len(FEATS))])
    feats = sorted([{"feature": f, "direction": int(dr[j]), "d": float(d[j]), "gap_share": float(gap[j] / gap.sum()),
                     "rho_T_controls": float(rT[j]), "family": next((a for a, b in fam.items() if f in b), "?")}
                    for j, f in enumerate(FEATS)], key=lambda r: -r["gap_share"])

    def loco_subset(idx):
        out = {}
        for k in keys:
            tr = [x for x in keys if x != k]
            w, dd = scheme("eşit", Z[:, idx], y, ka, tr)
            out[k] = pct(Z[:, idx], y, ka, k, w, dd)
        return out
    loaded = [j for j in range(len(FEATS)) if abs(rT[j]) >= 0.3]
    free = [j for j in range(len(FEATS)) if abs(rT[j]) < 0.3]
    per["skor, T-yüklü özellikler yok"] = loco_subset(free)
    per["skor, yalnız T-yüklü özellikler"] = loco_subset(loaded)
    fam_out = {}
    for a, b in fam.items():
        idx_in = [j for j, f in enumerate(FEATS) if f in b]
        if not idx_in:
            continue
        idx_out = [j for j in range(len(FEATS)) if j not in idx_in]
        fam_out[a] = {"n": len(idx_in), "gap_share": float(gap[idx_in].sum() / gap.sum()),
                      "auc_only": float(np.mean(list(loco_subset(idx_in).values()))),
                      "auc_without": float(np.mean(list(loco_subset(idx_out).values())))}

    groups = {g: [k for k in keys if TYPE[k] == g] for g in ("yeni", "mevcut")}
    res = {name: {"tümü": summ(v, keys), **{g: summ(v, ks) for g, ks in groups.items()}} for name, v in per.items()}
    out = {"summary": res, "percentiles": per, "rho_score_T_controls": {"mean": float(np.mean(list(rho_ctl.values()))), "per_city": rho_ctl},
           "features": feats, "T_loaded_features": [FEATS[j] for j in loaded], "families": fam_out, "type": TYPE,
           "notes": ["T yalnız skora girmeyen göstergelerden kurulur; şehir içi sıra ortalaması.",
                     "PED türü proje tanımlarından elle etiketlenmiştir; kaynakla doğrulanmalıdır.",
                     "GA: şehirler üzerinden bootstrap (10 000)."]}
    (ROOT / "data/validation/transformation_threat.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for name, r in res.items():
        print(f"{name:38s}", " | ".join(f"{g} {x['auc']:.2f} [{x['ci95'][0]:.2f},{x['ci95'][1]:.2f}] {x['above_half']}/{x['n']}" for g, x in r.items()))
    print("rho(skor,T) kontroller", round(out["rho_score_T_controls"]["mean"], 2))
    print("T-yüklü:", out["T_loaded_features"])
    for f in feats[:31]:
        print(f"  {f['feature']:28s} yön {f['direction']:+d} d {f['d']:+.2f} pay {f['gap_share']:.3f} rhoT {f['rho_T_controls']:+.2f}")
    for a, r in fam_out.items():
        print(f"  {a[:40]:40s} n {r['n']} pay {r['gap_share']:.2f} yalnız {r['auc_only']:.2f} çıkarınca {r['auc_without']:.2f}")


if __name__ == "__main__":
    main()

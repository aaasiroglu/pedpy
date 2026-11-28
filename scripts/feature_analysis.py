"""All data sources vs real PEDs: per-source association analysis, weighting schemes, SHAP (K-050).

Assumption under test: every layer of the lake may influence PED projects. For each of the 41
disc features (8 source families), on 16 real PED sites × 30 inhabited controls:

1. Association, within city (z-scores inside each city's 31 discs → climate/country removed):
   effect d = case z (mean over cities, 90 % bootstrap CI over cities), Wilcoxon signed-rank test
   of d against 0 across the 16 cities, Benjamini–Hochberg q (41 tests), point-biserial r.
2. Redundancy: Spearman correlation matrix of the features (controls, city-z pooled).
3. Weighting → PED score = Σ_j w_j · dir_j · z_j (weighted sum on z; MARCOS ≡ κ·WSM), compared by
   leave-one-city-out AUC. Directions and data-driven weights are computed WITHOUT the held-out city:
   equal · CRITIC · Entropy · evidence (|d|, q < 0.10) · learned logistic (all 41) · gradient boosting.
4. SHAP: TreeSHAP on gradient boosting (non-linear, interactions) and the exact linear SHAP of
   the logistic model (β_j (z_j − E z_j)); mean |SHAP| ranking per feature and per family.

    python scripts/feature_analysis.py      → data/validation/feature_analysis.json
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon

from pedx.mcdm.weighting import critic_weights, entropy_weights

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "data" / "validation"
SEED = 20261108
FAMILY = {
    "Enerji (PVGIS, UNSD, fizik)": ["energy_balance", "log_energy_balance", "energy_demand_res_kwh", "energy_pv_kwh"],
    "Bina (Overture)": ["ov_bld_n", "ov_bld_footprint_m2", "ov_gfa_m2", "footprint_coverage", "footprint_per_capita_m2",
                        "log_footprint_per_capita_m2", "gfa_per_capita_m2", "ov_floors_coverage", "ov_nonosm_share"],
    "Nüfus ve kırılganlık (Meta HRSL)": ["vul_pop_hrsl", "vul_elderly60_n", "vul_children0_5_n", "pop_density_per_ha", "elderly_share", "children_share"],
    "Uydu: Sentinel-2 ve Landsat": ["env_ndvi_mean", "env_ndbi_mean", "env_lst_mean_c", "env_lst_anomaly_c"],
    "Arazi örtüsü (ESA WorldCover)": ["env_wc_green_share", "env_wc_built_share", "env_wc_water_share", "env_wc_crop_share", "env_wc_bare_share"],
    "Arazi (Copernicus DEM)": ["env_elev_m", "env_slope_deg", "env_relief_m"],
    "Kentsel işlev (Overture mekânlar)": ["ov_places_n", "ov_places_categories", "places_per_1000"],
    "Altyapı (Overture: şebeke, EV, toplu taşıma)": ["ov_grid_assets_n", "ov_ev_chargers_n", "ov_generators_n", "ov_transit_stops_n",
                                                    "ov_bike_n", "transit_per_km2", "grid_assets_per_km2", "ev_chargers_per_km2", "bike_per_km2"],
}
LABEL = {
    "energy_balance": "Enerji dengesi", "log_energy_balance": "Enerji dengesi (log)", "energy_demand_res_kwh": "Konut talebi", "energy_pv_kwh": "Çatı FV üretimi",
    "ov_bld_n": "Bina sayısı", "ov_bld_footprint_m2": "Taban alanı", "ov_gfa_m2": "Brüt kat alanı (bilinen)", "footprint_coverage": "Yapı örtüsü",
    "footprint_per_capita_m2": "Kişi başı taban alanı", "log_footprint_per_capita_m2": "Kişi başı taban alanı (log)", "gfa_per_capita_m2": "Kişi başı kat alanı",
    "ov_floors_coverage": "Kat bilgisi tamlığı", "ov_nonosm_share": "OSM dışı bina payı", "vul_pop_hrsl": "Nüfus", "vul_elderly60_n": "60+ sayısı",
    "vul_children0_5_n": "0–5 yaş sayısı", "pop_density_per_ha": "Nüfus yoğunluğu", "elderly_share": "60+ payı", "children_share": "0–5 yaş payı",
    "env_ndvi_mean": "NDVI", "env_ndbi_mean": "NDBI", "env_lst_mean_c": "Yüzey sıcaklığı", "env_lst_anomaly_c": "Sıcaklık anomalisi",
    "env_wc_green_share": "Yeşil alan payı", "env_wc_built_share": "Yapılı alan payı", "env_wc_water_share": "Su yüzeyi payı",
    "env_wc_crop_share": "Tarım payı", "env_wc_bare_share": "Çıplak alan payı", "env_elev_m": "Yükseklik", "env_slope_deg": "Eğim",
    "env_relief_m": "Rölyef", "ov_places_n": "Mekân sayısı", "ov_places_categories": "Mekân çeşitliliği", "places_per_1000": "Kişi başı mekân",
    "ov_grid_assets_n": "Trafo sayısı", "ov_ev_chargers_n": "EV şarj sayısı", "ov_generators_n": "Jeneratör/santral", "ov_transit_stops_n": "Toplu taşıma durağı",
    "ov_bike_n": "Bisiklet park/kiralama", "transit_per_km2": "Durak yoğunluğu", "grid_assets_per_km2": "Trafo yoğunluğu",
    "ev_chargers_per_km2": "EV şarj yoğunluğu", "bike_per_km2": "Bisiklet yoğunluğu",
}
FEATS = [f for fam in FAMILY.values() for f in fam]
# may be CONSEQUENCES of the PED project itself (2021–23 imagery/maps of sites under construction or just built):
# excluded from the decision score to avoid reverse causality (kept in the association table, flagged)
SUSPECT = {"env_wc_bare_share", "ov_bike_n", "bike_per_km2", "ov_ev_chargers_n", "ev_chargers_per_km2", "ov_generators_n",
           "ov_gfa_m2", "gfa_per_capita_m2"}  # GFA: only buildings with mapped floors → mapping-completeness artefact (new PEDs are mapped in detail)
# lever-dependent duplicates: only the log form enters the score (the inverse acts on ln B)
DUPLICATE = {"energy_balance", "footprint_per_capita_m2", "energy_demand_res_kwh", "energy_pv_kwh"}  # demand = pop × const; PV = footprint × const (within city)
CLEAN = [f for f in FEATS if f not in SUSPECT | DUPLICATE]
FAM_OF = {f: k for k, fs in FAMILY.items() for f in fs}


def zwithin(D):
    out = []
    for _, g in D.groupby("site"):
        X = g[FEATS].astype(float)
        X = X.fillna(X.median()).fillna(0.0)
        sd = X.std(ddof=0).replace(0, np.nan)
        out.append(((X - X.mean()) / sd).fillna(0.0))
    return pd.concat(out).loc[D.index]


def bh(p):
    p = np.asarray(p, float)
    o = np.argsort(p)
    q = p[o] * len(p) / (np.arange(len(p)) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty_like(q)
    out[o] = np.minimum(q, 1)
    return out


def percentile_auc(D, score):
    pct = {}
    for s, g in D.groupby("site"):
        sc = score[g.index]
        case, ctl = sc[g["role"] == "case"].iloc[0], sc[g["role"] == "control"]
        pct[s] = float((ctl < case).mean() + 0.5 * (ctl == case).mean())
    return float(np.mean(list(pct.values()))), pct


def effects(Z, D, sites):
    rows = D["site"].isin(sites)
    cz = Z[rows & (D["role"] == "case")]
    return cz.mean(), cz


def main():
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression

    D = pd.read_csv(VAL / "ped_features.csv")
    D = D[D["site"].isin(D.loc[D.role == "case"].dropna(subset=["energy_balance"])["site"])].reset_index(drop=True)
    Z = zwithin(D)
    y = (D["role"] == "case").astype(int)
    sites = list(D["site"].unique())
    rng = np.random.default_rng(SEED)

    # ---- 1. association per feature
    d_mean, cz = effects(Z, D, sites)
    rows = []
    for f in FEATS:
        v = cz[f].to_numpy()
        boots = [rng.choice(v, len(v)).mean() for _ in range(2000)]
        try:
            p = float(wilcoxon(v).pvalue) if np.any(v != 0) else 1.0
        except ValueError:
            p = 1.0
        r = float(np.corrcoef(Z[f], y)[0, 1]) if Z[f].std() > 0 else 0.0
        rows.append({"feature": f, "label": LABEL.get(f, f), "family": FAM_OF[f], "effect_d": float(v.mean()),
                     "ci05": float(np.percentile(boots, 5)), "ci95": float(np.percentile(boots, 95)), "p": p, "r_pb": r,
                     "sites_positive": int((v > 0).sum()), "n_sites": int(len(v))})
    A = pd.DataFrame(rows)
    A["q_bh"] = bh(A["p"])

    # ---- 2. redundancy
    C = D["role"] == "control"
    rho = spearmanr(Z[C][FEATS].to_numpy()).correlation
    rho = np.nan_to_num(np.asarray(rho), nan=0.0)

    # ---- 3. weighting schemes, leave-one-city-out
    schemes = {k: pd.Series(np.nan, index=D.index) for k in ("Eşit ağırlık", "CRITIC", "Entropi", "Kanıt (|d|, q<0,10)",
                                                              "Kanıt, temiz (sonuç-şüpheli hariç)", "Öğrenilmiş lojistik", "Gradyan artırma")}
    ic = [FEATS.index(f) for f in CLEAN]
    W_full = {}
    for s in sites:
        tr, te = D["site"] != s, D["site"] == s
        d_tr, cz_tr = effects(Z, D, [x for x in sites if x != s])
        sign = np.sign(d_tr).replace(0, 1.0)
        X_tr = Z[tr][FEATS].to_numpy() * sign.to_numpy()
        ben = [True] * len(FEATS)
        w_eq = np.full(len(FEATS), 1 / len(FEATS))
        w_cr, _ = critic_weights(X_tr, ben)
        w_en, _ = entropy_weights(X_tr, ben)
        p_tr = [float(wilcoxon(cz_tr[f]).pvalue) if np.any(cz_tr[f] != 0) else 1.0 for f in FEATS]
        q_tr = bh(p_tr)
        w_ev = np.where(q_tr < 0.10, np.abs(d_tr.to_numpy()), 0.0)
        w_ev = w_ev / w_ev.sum() if w_ev.sum() > 0 else w_eq
        Xte = Z[te][FEATS].to_numpy() * sign.to_numpy()
        w_cl = np.zeros(len(FEATS))
        w_cl[ic] = np.where(q_tr[ic] < 0.10, np.abs(d_tr.to_numpy()[ic]), 0.0)
        w_cl = w_cl / w_cl.sum() if w_cl.sum() > 0 else w_eq
        for name, w in (("Eşit ağırlık", w_eq), ("CRITIC", w_cr), ("Entropi", w_en), ("Kanıt (|d|, q<0,10)", w_ev),
                        ("Kanıt, temiz (sonuç-şüpheli hariç)", w_cl)):
            schemes[name][te] = Xte @ w
        lr = LogisticRegression(C=0.5, class_weight="balanced", max_iter=5000).fit(Z[tr][FEATS], y[tr])
        schemes["Öğrenilmiş lojistik"][te] = lr.decision_function(Z[te][FEATS])
        gb = GradientBoostingClassifier(n_estimators=150, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=SEED)
        gb.fit(Z[tr][FEATS], y[tr], sample_weight=np.where(y[tr] == 1, (1 - y[tr]).sum() / y[tr].sum(), 1.0))
        schemes["Gradyan artırma"][te] = gb.decision_function(Z[te][FEATS])
    comp = []
    for k, sc in schemes.items():
        auc, pct = percentile_auc(D, sc)
        comp.append({"scheme": k, "auc_loco": auc, "sites_above_half": int(sum(v > 0.5 for v in pct.values())), "percentiles": pct})
    # full-data weights for display
    sign = np.sign(d_mean).replace(0, 1.0)
    Xall = Z[FEATS].to_numpy() * sign.to_numpy()
    W_full["CRITIC"] = critic_weights(Xall, [True] * len(FEATS))[0]
    W_full["Entropi"] = entropy_weights(Xall, [True] * len(FEATS))[0]
    w_ev = np.where(A["q_bh"] < 0.10, np.abs(A["effect_d"]), 0.0)
    W_full["Kanıt (|d|, q<0,10)"] = w_ev / w_ev.sum() if w_ev.sum() > 0 else np.full(len(FEATS), 1 / len(FEATS))
    w_cl = np.where((A["q_bh"] < 0.10) & A["feature"].isin(CLEAN), np.abs(A["effect_d"]), 0.0)
    W_full["Kanıt, temiz"] = w_cl / w_cl.sum()
    A["suspect_consequence"] = A["feature"].isin(SUSPECT)
    A["direction"] = np.sign(A["effect_d"]).replace(0, 1.0)

    # ---- 4. SHAP
    import shap

    lr = LogisticRegression(C=0.5, class_weight="balanced", max_iter=5000).fit(Z[FEATS], y)
    lin_shap = (Z[FEATS] - Z[FEATS].mean()).to_numpy() * lr.coef_[0]  # exact SHAP of a linear model (independent features)
    gb = GradientBoostingClassifier(n_estimators=150, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=SEED)
    gb.fit(Z[FEATS], y, sample_weight=np.where(y == 1, (1 - y).sum() / y.sum(), 1.0))
    tree_shap = shap.TreeExplainer(gb).shap_values(Z[FEATS])
    tree_shap = tree_shap[1] if isinstance(tree_shap, list) else tree_shap
    A["shap_linear_mean_abs"] = np.abs(lin_shap).mean(axis=0)
    A["shap_tree_mean_abs"] = np.abs(tree_shap).mean(axis=0)
    A["shap_tree_case_mean"] = tree_shap[y.to_numpy() == 1].mean(axis=0)
    A["coef_logistic"] = lr.coef_[0]
    for k, w in W_full.items():
        A[f"w_{k}"] = w
    fam = A.groupby("family").agg(n=("feature", "size"), max_abs_d=("effect_d", lambda s: float(s.abs().max())),
                                  n_q10=("q_bh", lambda s: int((s < 0.10).sum())), shap_tree=("shap_tree_mean_abs", "sum"),
                                  shap_linear=("shap_linear_mean_abs", "sum")).reset_index()
    fam["shap_tree_share"] = fam["shap_tree"] / fam["shap_tree"].sum()
    out = {"clean_features": CLEAN, "suspect": sorted(SUSPECT), "n_sites": len(sites), "n_rows": int(len(D)), "n_features": len(FEATS), "families": FAMILY,
           "features": A.round(5).to_dict(orient="records"), "family_summary": fam.round(5).to_dict(orient="records"),
           "schemes": comp, "corr": {"features": FEATS, "rho": np.round(rho, 3).tolist()},
           "notes": ["Etki d: gerçek PED sahasının kendi kentindeki 31 disk içinde z-puanı; 16 kentin ortalaması.",
                     "Wilcoxon işaret-sıra testi 16 kent üzerinden; q: Benjamini–Hochberg (41 test).",
                     "Ağırlık şemalarında yön ve veri tabanlı ağırlıklar dışarıda bırakılan kent olmadan hesaplanır.",
                     "Doğrusal SHAP = β_j (z_j − E z_j); ağaç SHAP = TreeSHAP (Lundberg vd. 2020).",
                     "Sonuç-şüpheli özellikler (çıplak alan, bisiklet, EV şarj, jeneratör) PED projesinin kendisinin izi olabilir; karar skoruna girmez."]}
    (VAL / "feature_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(A.sort_values("q_bh")[["label", "family", "effect_d", "ci05", "ci95", "q_bh", "shap_tree_mean_abs"]].round(3).head(15).to_string())
    print(pd.DataFrame(comp)[["scheme", "auc_loco", "sites_above_half"]].round(3).to_string())
    print(fam[["family", "n", "n_q10", "max_abs_d", "shap_tree_share"]].round(3).to_string())


if __name__ == "__main__":
    main()

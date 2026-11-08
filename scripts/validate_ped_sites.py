"""External validation against REAL Positive Energy Districts (case–control on city grids, K-041/K-043).

Question: does the model rank real PED / lighthouse sites above ordinary *inhabited, built-up*
locations of the same city — (a) with the physical balance alone, (b) with all raster and vector
layers together? Design fixed before results (docs/17):

* cases    — 16 real PED / SCC lighthouse districts (data/validation/ped_sites.json, OSM ids)
* grid     — pedx.citygrid: 16 × 16 km window per city, every layer on H3 r10 (HRSL, Overture,
             Sentinel-2, Landsat LST, Copernicus DEM, PVGIS, UNSD/OWID)
* sites    — k = 2 discs (19 cells ≈ 0.28 km²) around the site cell / around control cells
* controls — 30 per city, centre cell inhabited (HRSL ≥ 20 persons) and built (footprint > 0),
             ≥ 1.5 km from the site; fixed seed 20261108
* models   — (a) energy balance; (b) L2 logistic regression on within-city z-scores of intensive
             features, leave-one-city-out (the held-out city never informs its own score)
* metric   — case percentile among its controls; pooled mean = stratified AUC; sign test
* extra    — Caferağa (not a PED) is scored within Istanbul with the model fitted on all PED cities

    python scripts/validate_ped_sites.py [n_controls]
"""

import json
import math
import re
import sys
from math import comb
from pathlib import Path

import h3
import numpy as np
import pandas as pd

from pedx.citygrid import city_grid, disc_features

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "data" / "validation"
SEED = 20261108
DEV = {  # development type and programme (sources: docs/17)
    "Buiksloterham": ("brownfield", "ATELIER (H2020 SCC)"), "Zorrotzaurre": ("brownfield", "ATELIER (H2020 SCC)"),
    "Kera": ("brownfield", "SPARCS (H2020 SCC)"), "Leppävaara": ("existing", "SPARCS (H2020 SCC)"),
    "Fornebu": ("brownfield", "syn.ikia (H2020)"), "Kaukovainio": ("existing", "MAKING-CITY (H2020 SCC)"),
    "Paddepoel": ("existing", "MAKING-CITY (H2020 SCC)"), "Fontaine d'Ouche": ("existing", "RESPONSE (H2020 SCC)"),
    "Linnakaupunki": ("brownfield", "RESPONSE (H2020 SCC)"), "Confluence": ("brownfield", "Lyon Smart Community / Smarter Together"),
    "Seestadt Aspern": ("new", "PED Booklet 2020"), "Brunnshög": ("new", "PED Booklet 2020"),
    "Coronación": ("existing", "SmartEnCity (H2020 SCC)"), "Rosendal": ("new", "syn.ikia (H2020)"),
    "Kalasatama": ("brownfield", "mySMARTLife (H2020 SCC)"), "Île de Nantes": ("brownfield", "mySMARTLife (H2020 SCC)"),
}
FEATURES = ["log_energy_balance", "pop_density_per_ha", "footprint_coverage", "log_footprint_per_capita_m2", "places_per_1000",
            "elderly_share", "children_share", "env_ndvi_mean", "env_ndbi_mean", "env_lst_anomaly_c", "env_slope_deg",
            "env_relief_m", "ov_floors_coverage", "ov_nonosm_share", "ov_places_categories"]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower().encode("ascii", "ignore").decode()).strip("_")


def sample_controls(F: pd.DataFrame, site_cell: str, n: int, rng) -> list:
    la0, lo0 = h3.cell_to_latlng(site_cell)
    ok = F[(F["vul_pop_hrsl"] >= 20) & (F["ov_bld_footprint_m2"] > 0)].index
    far = [c for c in ok if h3.great_circle_distance((la0, lo0), h3.cell_to_latlng(c), unit="km") >= 1.5]
    return list(rng.choice(far, size=min(n, len(far)), replace=False)) if far else []


def city_rows(name, lat, lon, n, rng, role_case=True):
    F, prov = city_grid(lat, lon, slug(name))
    site_cell = h3.latlng_to_cell(lat, lon, 10)
    rows = []
    if role_case:
        rows.append({"role": "case", "centre": site_cell, **disc_features(F, site_cell)})
    rows += [{"role": "control", "centre": c, **disc_features(F, c)} for c in sample_controls(F, site_cell, n, rng)]
    for r in rows:
        r["log_energy_balance"] = math.log(r["energy_balance"]) if r.get("energy_balance", 0) and r["energy_balance"] > 0 else np.nan
        r["log_footprint_per_capita_m2"] = math.log(r["footprint_per_capita_m2"]) if r.get("footprint_per_capita_m2", 0) and r["footprint_per_capita_m2"] > 0 else np.nan
    return rows, prov


def zscore_within(df):
    X = df[FEATURES].astype(float)
    X = X.fillna(X.median())
    sd = X.std(ddof=0).replace(0, 1.0)
    return ((X - X.mean()) / sd).fillna(0.0)


def percentile(case, ctl):
    ctl = np.asarray([c for c in ctl if np.isfinite(c)])
    if not np.isfinite(case) or ctl.size == 0:
        return np.nan
    return float((ctl < case).mean() + 0.5 * (ctl == case).mean())


def sign_p(x):
    x = [v for v in x if np.isfinite(v)]
    k, m = sum(v > 0.5 for v in x), len(x)
    return sum(comb(m, i) for i in range(k, m + 1)) / 2**m if m else None


if __name__ == "__main__":
    from sklearn.linear_model import LogisticRegression

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    sites = json.loads((VAL / "ped_sites.json").read_text())
    rng = np.random.default_rng(SEED)
    allrows, provs = [], {}
    for s in sites:
        rows, prov = city_rows(s["site"], s["lat"], s["lon"], n, rng)
        for r in rows:
            r.update({"site": s["site"], "city": s["city"]})
        allrows += rows
        provs[s["site"]] = {"failures": prov.get("failures"), "timing_s": prov.get("timing_s"),
                            "sentinel2": prov.get("sentinel2"), "landsat_scenes": len((prov.get("landsat") or {}).get("scenes", []))}
        print(s["site"], "rows", len(rows), "fails", list((prov.get("failures") or {}).keys()), flush=True)
    D = pd.DataFrame(allrows)
    D.to_csv(VAL / "ped_features.csv", index=False)

    # z-scores within each city (removes climate/country/level differences → within-city contrast)
    Z = pd.concat([zscore_within(g) for _, g in D.groupby("site")]).loc[D.index]
    y = (D["role"] == "case").astype(int).to_numpy()
    model = lambda: LogisticRegression(C=0.5, class_weight="balanced", max_iter=2000)  # noqa: E731
    D["score_multi"] = np.nan
    for site in D["site"].unique():  # leave-one-city-out
        tr, te = D["site"] != site, D["site"] == site
        m = model().fit(Z[tr], y[tr])
        D.loc[te, "score_multi"] = m.decision_function(Z[te])
    res = []
    for site, g in D.groupby("site", sort=False):
        c, k = g[g.role == "case"].iloc[0], g[g.role == "control"]
        dev, prog = DEV.get(site, ("?", "?"))
        s0 = next(s for s in sites if s["site"] == site)
        res.append({"site": site, "city": c["city"], "osm": s0["osm"], "development": dev, "programme": prog,
                    "case_balance": c["energy_balance"], "case_population": c["vul_pop_hrsl"], "controls_n": int(len(k)),
                    "controls_median_balance": float(k["energy_balance"].median()),
                    "percentile": percentile(c["energy_balance"], k["energy_balance"]),
                    "percentile_multi": percentile(c["score_multi"], k["score_multi"])})
    R = pd.DataFrame(res)
    R.to_csv(VAL / "ped_validation.csv", index=False)
    full = model().fit(Z, y)
    coefs = sorted(zip(FEATURES, full.coef_[0]), key=lambda t: -abs(t[1]))

    # Caferağa within Istanbul (not a PED; scored by the model fitted on all PED cities)
    caf_rows, _ = city_rows("Caferağa Istanbul", 40.9857, 29.0245, n, np.random.default_rng(SEED))
    C = pd.DataFrame(caf_rows)
    Zc = zscore_within(C)
    sc = full.decision_function(Zc)
    caf = {"percentile_balance": percentile(C.iloc[0]["energy_balance"], C.iloc[1:]["energy_balance"]),
           "percentile_multi": percentile(sc[0], sc[1:]), "balance": C.iloc[0]["energy_balance"],
           "note": "HRSL population (common source); Caferağa is a candidate, not a realised PED"}
    summ = {"n_sites": int(R["percentile"].notna().sum()), "n_controls_per_site": n, "seed": SEED,
            "auc_pooled": float(R["percentile"].mean()), "sites_above_median": int((R["percentile"] > 0.5).sum()),
            "sign_test_p_one_sided": sign_p(R["percentile"]),
            "auc_multi_loco": float(R["percentile_multi"].mean()), "sites_above_median_multi": int((R["percentile_multi"] > 0.5).sum()),
            "sign_test_p_multi": sign_p(R["percentile_multi"]),
            "by_development": R.groupby("development")[["percentile", "percentile_multi"]].mean().round(3).to_dict(),
            "coefficients_full_fit": [{"feature": f, "coef": round(float(b), 3)} for f, b in coefs],
            "caferaga_in_istanbul": caf, "provenance": provs}
    (VAL / "ped_validation_summary.json").write_text(json.dumps(summ, indent=1, default=str))
    print(R.round(3).to_string())
    print(json.dumps({k: v for k, v in summ.items() if k != "provenance"}, indent=1, default=str))

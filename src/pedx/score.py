"""Total PED score: learned from real PEDs, exactly decomposable, differentiable and invertible (K-049).

Definition. For a candidate project site s (k = 2 H3 r10 disc ≈ 28 ha) in city c:

    z_i(s) = (x_i(s) − μ_ic) / σ_ic                    within-city standardisation (city = all inhabited candidates)
    logit(s) = β0 + Σ_i β_i z_i(s)                     L2 logistic regression, real PEDs vs inhabited controls
    S(s) = 100 · σ(logit(s))                            "PED likeness", 0–100

Properties (why it is a decision tool, not a black box)
* exact attribution:   logit = β0 + Σ_i c_i with c_i = β_i z_i     (no SHAP approximation needed)
* differentiable:      ∂S/∂x_i = 100 · S'(1−S') · β_i / σ_ic,  S' = S/100
* invertible (physics-coupled): the levers act on the energy balance B = A·u·η·Y / (P·d), feature
  x_b = ln B. Reaching a target score S* needs Δln B = (logit* − logit) · σ_bc / β_b, which is split
  over the levers in a fixed, documented order: roof utilisation u (≤ u_max), module efficiency η
  (≤ η_max), demand reduction by retrofit d (≤ d_cut_max). Closed form, no search.

The score says how much a site resembles the real PEDs Europe has built (reference class,
Flyvbjerg 2014); the physics (B ≥ 1) says whether it can balance on site. Both are reported.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .params import PARAMS

__all__ = ["SCORE_FEATURES", "candidate_discs", "city_stats", "PEDScore"]

SCORE_FEATURES = ["log_energy_balance", "pop_density_per_ha", "footprint_coverage", "log_footprint_per_capita_m2", "places_per_1000",
                  "elderly_share", "children_share", "env_ndvi_mean", "env_ndbi_mean", "env_lst_anomaly_c", "env_slope_deg",
                  "env_relief_m", "ov_floors_coverage", "ov_nonosm_share", "ov_places_categories",
                  "env_wc_green_share", "env_wc_water_share", "transit_per_km2", "grid_assets_per_km2", "ev_chargers_per_km2"]
LABELS_TR = {
    "log_energy_balance": "Enerji dengesi (log)", "pop_density_per_ha": "Nüfus yoğunluğu", "footprint_coverage": "Yapı örtüsü",
    "log_footprint_per_capita_m2": "Kişi başı çatı tabanı (log)", "places_per_1000": "Kişi başı mekân", "elderly_share": "60+ payı",
    "children_share": "0–5 yaş payı", "env_ndvi_mean": "NDVI (bitki)", "env_ndbi_mean": "NDBI (yapılaşma)", "env_lst_anomaly_c": "Yüzey sıcaklığı anomalisi",
    "env_slope_deg": "Eğim", "env_relief_m": "Rölyef", "ov_floors_coverage": "Kat bilgisi tamlığı", "ov_nonosm_share": "OSM dışı bina payı",
    "ov_places_categories": "Mekân çeşitliliği", "env_wc_green_share": "Yeşil alan payı", "env_wc_water_share": "Su yüzeyi payı",
    "transit_per_km2": "Toplu taşıma yoğunluğu", "grid_assets_per_km2": "Şebeke varlığı yoğunluğu", "ev_chargers_per_km2": "EV şarj yoğunluğu",
    "ov_bld_n": "Bina sayısı", "ov_gfa_m2": "Brüt kat alanı (bilinen)", "gfa_per_capita_m2": "Kişi başı kat alanı", "vul_pop_hrsl": "Nüfus",
    "vul_elderly60_n": "60+ sayısı", "vul_children0_5_n": "0–5 yaş sayısı",
    "ov_bld_footprint_m2": "Bina taban alanı", "env_lst_mean_c": "Yüzey sıcaklığı", "env_wc_built_share": "Yapılı alan payı (WorldCover)",
    "env_wc_crop_share": "Tarım alanı payı", "env_elev_m": "Yükselti", "ov_places_n": "Mekân sayısı",
    "ov_grid_assets_n": "Şebeke varlığı sayısı", "ov_transit_stops_n": "Toplu taşıma durağı sayısı",
}


def _log_or_nan(x):
    x = np.asarray(x, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(x > 0, np.log(x), np.nan)


def candidate_discs(F: pd.DataFrame, k: int = 2, centres: Optional[List[str]] = None, min_pop: float = 20.0) -> pd.DataFrame:
    """Disc features (same definitions as pedx.citygrid.disc_features) for many centres at once (vectorised)."""
    import h3

    from .citygrid import EXTENSIVE, INTENSIVE

    if centres is None:
        ok = (F.get("vul_pop_hrsl", 0) >= min_pop) & (F.get("ov_bld_footprint_m2", 0) > 0)
        centres = list(F.index[ok])
    pos = {c: i for i, c in enumerate(F.index)}
    n_disc = 1 + 3 * k * (k + 1)
    rows, cols = [], []
    for j, c in enumerate(centres):
        for d in h3.grid_disk(c, k):
            if d in pos:
                rows.append(j)
                cols.append(pos[d])
    rows, cols = np.asarray(rows), np.asarray(cols)
    out = pd.DataFrame(index=pd.Index(centres, name="centre"))
    for c in EXTENSIVE:
        if c in F:
            v = np.nan_to_num(F[c].to_numpy(float)[cols])
            out[c] = np.bincount(rows, weights=v, minlength=len(centres))
    for c in INTENSIVE:
        if c in F:
            v = F[c].to_numpy(float)[cols]
            ok = np.isfinite(v)
            s = np.bincount(rows[ok], weights=v[ok], minlength=len(centres))
            n = np.bincount(rows[ok], minlength=len(centres))
            out[c] = np.where(n > 0, s / np.maximum(n, 1), np.nan)
    res = h3.get_resolution(centres[0]) if centres else 10
    area_ha = n_disc * h3.average_hexagon_area(res, unit="m^2") / 1e4
    P, A = out["vul_pop_hrsl"], out["ov_bld_footprint_m2"]
    Pn = P.where(P > 0)
    out["pop_density_per_ha"] = P / area_ha
    out["footprint_coverage"] = A / (area_ha * 1e4)
    out["footprint_per_capita_m2"] = A / Pn
    out["places_per_1000"] = 1000 * out.get("ov_places_n", 0) / Pn
    out["elderly_share"] = out.get("vul_elderly60_n", 0) / Pn
    out["children_share"] = out.get("vul_children0_5_n", 0) / Pn
    if "ov_gfa_m2" in out:
        out["gfa_per_capita_m2"] = out["ov_gfa_m2"] / Pn
    km2 = area_ha / 100
    for c, nm in (("ov_transit_stops_n", "transit_per_km2"), ("ov_grid_assets_n", "grid_assets_per_km2"), ("ov_ev_chargers_n", "ev_chargers_per_km2")):
        if c in out:
            out[nm] = out[c] / km2
    if "osm_transit_n" in out:  # OSM stops are complete where Overture infrastructure is not (K-052)
        out["transit_per_km2"] = out["osm_transit_n"] / km2
    D = out.get("energy_demand_res_kwh")
    out["energy_balance"] = out.get("energy_pv_kwh") / D.where(D > 0) if D is not None else np.nan
    out["log_energy_balance"] = _log_or_nan(out["energy_balance"])
    out["log_footprint_per_capita_m2"] = _log_or_nan(out["footprint_per_capita_m2"])
    return out


def city_stats(C: pd.DataFrame, features: Optional[List[str]] = None) -> Dict[str, Dict[str, float]]:
    """Mean, sd and median of every score feature over the inhabited candidate sites of one city."""
    st = {}
    for f in (features or SCORE_FEATURES):
        v = C[f].astype(float) if f in C else pd.Series(dtype=float)
        v = v[np.isfinite(v)]
        sd = float(v.std(ddof=0)) if len(v) > 1 else 1.0
        st[f] = {"mean": float(v.mean()) if len(v) else 0.0, "sd": sd if sd > 0 else 1.0, "median": float(v.median()) if len(v) else 0.0}
    return st


def _z(x: Dict[str, float], st: Dict[str, Dict[str, float]], features: Optional[List[str]] = None) -> np.ndarray:
    z = []
    for f in (features or SCORE_FEATURES):
        v = x.get(f, np.nan)
        v = st[f]["median"] if v is None or not np.isfinite(v) else v
        z.append((v - st[f]["mean"]) / st[f]["sd"])
    return np.asarray(z)


@dataclass
class PEDScore:
    coef: np.ndarray
    intercept: float
    features: List[str] = field(default_factory=lambda: list(SCORE_FEATURES))
    meta: Dict[str, object] = field(default_factory=dict)

    # ------------------------------------------------------------ fit / io
    @classmethod
    def fit(cls, Z: np.ndarray, y: np.ndarray, C: float = 0.5, **meta) -> "PEDScore":
        from sklearn.linear_model import LogisticRegression

        m = LogisticRegression(C=C, class_weight="balanced", max_iter=5000).fit(Z, y)
        return cls(m.coef_[0].copy(), float(m.intercept_[0]), meta=dict(meta, C=C))

    def to_json(self, path: Path) -> None:
        Path(path).write_text(json.dumps({"features": self.features, "coef": [float(b) for b in self.coef],
                                          "intercept": self.intercept, "labels_tr": LABELS_TR, "meta": self.meta}, indent=1, default=str))

    @classmethod
    def from_weights(cls, features: List[str], weights: np.ndarray, direction: np.ndarray, Z: np.ndarray, y: np.ndarray,
                     **meta) -> "PEDScore":
        """MCDM form: S = 100·σ(a · Σ_j w_j dir_j z_j + b). Weights from the criteria (sum 1); a, b by Platt scaling
        (balanced) — a monotone calibration, so ranking = weighted sum and contributions stay exact."""
        from sklearn.linear_model import LogisticRegression

        wsm = Z @ (weights * direction)
        m = LogisticRegression(C=1e6, class_weight="balanced", max_iter=5000).fit(wsm.reshape(-1, 1), y)
        a, b = float(m.coef_[0][0]), float(m.intercept_[0])
        return cls(a * weights * direction, b, list(features),
                   meta=dict(meta, form="weighted sum + Platt", weights=[float(w) for w in weights],
                             direction=[float(d) for d in direction], platt_a=a, platt_b=b))

    @classmethod
    def from_json(cls, path: Path) -> "PEDScore":
        d = json.loads(Path(path).read_text())
        return cls(np.asarray(d["coef"]), float(d["intercept"]), d["features"], d.get("meta", {}))

    # ------------------------------------------------------------ forward
    def explain(self, x: Dict[str, float], st: Dict[str, Dict[str, float]]) -> Dict[str, object]:
        """Score, exact logit contributions and gradient for one site."""
        z = _z(x, st, self.features)
        contrib = self.coef * z
        logit = self.intercept + float(contrib.sum())
        p = 1 / (1 + math.exp(-logit))
        grad = {f: 100 * p * (1 - p) * b / st[f]["sd"] for f, b in zip(self.features, self.coef)}
        return {"score": 100 * p, "logit": logit, "intercept": self.intercept,
                "contributions": {f: float(c) for f, c in zip(self.features, contrib)},
                "z": {f: float(v) for f, v in zip(self.features, z)}, "gradient_per_unit": grad}

    # ------------------------------------------------------------ inverse (physics-coupled, closed form)
    def inverse(self, x: Dict[str, float], st: Dict[str, Dict[str, float]], target: float,
                u_max: Optional[float] = None, eta_max: Optional[float] = None, d_cut_max: float = 0.5) -> Dict[str, object]:
        """Smallest lever changes (u → η → d, in that order) that lift the score to ``target`` (0–100)."""
        u0, eta0 = PARAMS["roof_utilization"]["value"], PARAMS["module_efficiency"]["value"]
        u_max = PARAMS["roof_utilization"]["high"] if u_max is None else u_max
        eta_max = PARAMS["module_efficiency"]["high"] if eta_max is None else eta_max
        e = self.explain(x, st)
        ib = self.features.index("log_energy_balance")
        beta_b, sd_b = float(self.coef[ib]), st["log_energy_balance"]["sd"]
        B0 = x.get("energy_balance", np.nan)
        out = {"score_now": e["score"], "target": target, "balance_now": B0, "levers": {}, "feasible": False}
        if not np.isfinite(B0) or B0 <= 0 or beta_b <= 0:
            out["reason_tr"] = "Enerji dengesi tanımsız ya da modelde dengenin etkisi pozitif değil; enerji kaldıraçlarıyla skor değişmez."
            return out
        if e["score"] >= target:
            out.update(feasible=True, reason_tr="Saha zaten hedef skorun üstünde.", balance_needed=B0)
            return out
        t = min(max(target, 0.01), 99.99) / 100
        need = (math.log(t / (1 - t)) - e["logit"]) * sd_b / beta_b  # required Δ ln B
        f_needed = math.exp(need)
        f_u = min(f_needed, u_max / u0)
        f_eta = min(f_needed / f_u, eta_max / eta0)
        f_d = min(f_needed / (f_u * f_eta), 1 / (1 - d_cut_max))
        achieved = f_u * f_eta * f_d
        lnB = math.log(B0 * achieved)
        x2 = dict(x, log_energy_balance=lnB, energy_balance=B0 * achieved)
        out["levers"] = {"roof_utilization": {"from": u0, "to": u0 * f_u}, "module_efficiency": {"from": eta0, "to": eta0 * f_eta},
                         "demand_cut_share": {"from": 0.0, "to": 1 - 1 / f_d}}
        out.update(balance_needed=B0 * f_needed, balance_after=B0 * achieved, score_after=self.explain(x2, st)["score"],
                   feasible=achieved >= f_needed * (1 - 1e-9))
        if not out["feasible"]:
            out["reason_tr"] = ("Enerji kaldıraçları üst sınırda bile hedefe yetmiyor; skoru taşıyan öteki özellikler (yapı örtüsü, yeşil, su, işlev) "
                                "kentsel dönüşüm ölçeğinde değişiklik gerektirir.")
        return out


def evidence_weights(Z: np.ndarray, y: np.ndarray, keys: np.ndarray, train_keys, q_max: float = 0.10):
    """Criteria weights ∝ |effect d| of features with Benjamini–Hochberg q < q_max over the training cities (K-050).

    Z: z-scores (rows = sites, cols = criteria); y: 1 = real PED case; keys: city of each row.
    Effect d per city = case z − mean control z; Wilcoxon signed-rank across cities. Returns (w, direction, d, q).
    """
    from scipy.stats import wilcoxon

    keys = np.asarray(keys)
    dz = []
    for k in train_keys:
        m = keys == k
        if (y[m] == 1).sum() == 0:
            continue
        dz.append(Z[m & (y == 1)][0] - Z[m & (y == 0)].mean(axis=0))
    dz = np.vstack(dz)
    d = dz.mean(axis=0)
    p = np.array([wilcoxon(dz[:, j]).pvalue if np.any(dz[:, j] != 0) else 1.0 for j in range(dz.shape[1])])
    o = np.argsort(p)
    q = p[o] * len(p) / (np.arange(len(p)) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    qq = np.empty_like(q)
    qq[o] = np.minimum(q, 1)
    w = np.where(qq < q_max, np.abs(d), 0.0)
    w = w / w.sum() if w.sum() > 0 else np.full(len(d), 1 / len(d))
    return w, np.where(d >= 0, 1.0, -1.0), d, qq

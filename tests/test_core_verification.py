"""T1–T5 software verification tests plus equivalence and attribution properties.

These are *software verification* tests (does the code implement the stated
equations?), not scientific validation against observations (docs/07, E4).
"""

import math

import numpy as np
import pandas as pd
import pytest

from pedx import mcdm
from pedx._backend import smooth_min, tau_for_ssr_tolerance
from pedx._stats import kendall_tau_b, rankdata, spearman_rho
from pedx.energy import BuildingEnergyRecord, aggregate_to_cells, load_match
from pedx.index import contributions, energy_score, energy_values, rank_intervals
from pedx.synthetic import demand_profile, solar_irradiance

T = 8760


# ---------------------------------------------------------------- T1
def test_t1_ssr_one_when_generation_covers_every_hour():
    d = np.full(T, 2.0)
    g = d + 1.0
    m = load_match(g, d)
    assert m["ssr"] == pytest.approx(1.0)
    assert m["peak_relief"] == pytest.approx(1.0)
    assert m["balance"] == pytest.approx(1.5)


def test_t1_scr_nan_without_generation():
    m = load_match(np.zeros(T), np.ones(T))
    assert math.isnan(m["scr"])
    assert m["ssr"] == 0.0
    assert m["peak_relief"] == pytest.approx(0.0)


def test_t1_ssr_nan_without_demand():
    assert math.isnan(load_match(np.ones(10), np.zeros(10))["ssr"])


def test_negative_energy_rejected():
    with pytest.raises(ValueError):
        load_match(np.array([-1.0, 1.0]), np.ones(2))


# ---------------------------------------------------------------- T2
def test_t2_same_annual_totals_different_hourly_match():
    """Day- and night-shaped demand with identical totals must be separated by SSR."""
    g = solar_irradiance(41.0, seed=None) * 50.0
    total = g.sum()
    day = demand_profile(total, "day")
    night = demand_profile(total, "night")
    md, mn = load_match(g, day), load_match(g, night)
    assert md["balance"] == pytest.approx(mn["balance"]) == pytest.approx(1.0)
    assert md["ssr"] > mn["ssr"] + 0.3
    assert md["peak_relief"] > mn["peak_relief"]


# ---------------------------------------------------------------- T3
def test_t3_constant_column_gets_zero_weight():
    rng = np.random.default_rng(1)
    X = rng.uniform(1, 5, size=(12, 4))
    X[:, 2] = 3.0
    for fn in (mcdm.critic_weights, mcdm.entropy_weights):
        w, info = fn(X, [True, False, True, True])
        assert w[2] == 0.0
        assert w.sum() == pytest.approx(1.0)
        assert info["constant_mask"][2]


def test_t3_zero_trust_source_has_no_effect():
    wc = np.array([0.5, 0.3, 0.2])
    we = np.array([0.1, 0.1, 0.8])
    assert np.allclose(mcdm.fuse_weights(wc, we, alpha=1.0), wc)
    assert np.allclose(mcdm.fuse_weights(wc, we, alpha=0.0), we)


def test_bounded_simplex_projection():
    w = mcdm.project_bounded_simplex(np.array([0.9, 0.05, 0.05, 0.0]), lower=0.1, active=np.array([1, 1, 1, 0], bool))
    assert w.sum() == pytest.approx(1.0)
    assert w[3] == 0.0 and np.all(w[:3] >= 0.1 - 1e-12)


def test_bwm_linear_consistent_input_has_zero_xi():
    # fully consistent comparisons generated from w = (0.5, 0.3, 0.2): best=0, worst=2
    w_true = np.array([0.5, 0.3, 0.2])
    a_b = w_true[0] / w_true
    a_w = w_true / w_true[2]
    w, xi = mcdm.bwm_linear(a_b, a_w, best=0, worst=2)
    assert xi == pytest.approx(0.0, abs=1e-9)
    assert np.allclose(w, w_true, atol=1e-6)


# ---------------------------------------------------------------- T4'
def test_t4_marcos_equals_scaled_weighted_sum():
    rng = np.random.default_rng(0)
    X = rng.uniform(0.1, 10, (25, 6))
    w = rng.dirichlet(np.ones(6))
    ben = [True, True, False, True, False, True]
    r = mcdm.marcos(X, w, ben)
    assert np.allclose(r["f_k"], r["kappa"] * r["S"], rtol=1e-12)
    assert spearman_rho(r["f_k"], r["S"]) == pytest.approx(1.0)


def test_marcos_rejects_non_positive_values():
    X = np.array([[1.0, 0.0], [2.0, 1.0]])
    with pytest.raises(ValueError):
        mcdm.marcos(X, [0.5, 0.5], [True, False])


# ---------------------------------------------------------------- T5
def _buildings(n=30, seed=3):
    rng = np.random.default_rng(seed)
    irr = solar_irradiance(41.0)
    out = []
    for i in range(n):
        lat = 40.985 + rng.uniform(-0.004, 0.004)
        lon = 29.025 + rng.uniform(-0.004, 0.004)
        area = rng.uniform(80, 400)
        out.append(
            BuildingEnergyRecord.from_irradiance(
                f"b{i}", lat, lon, irr, demand_profile(rng.uniform(5e3, 6e4), rng.choice(["residential", "office"])),
                footprint_area_m2=area, usable_roof_area_m2=0.6 * area, installed_pv_area_m2=rng.uniform(0, 0.6 * area),
                pv_efficiency=0.2, performance_ratio=0.84,
            )
        )
    return out


@pytest.mark.parametrize("res", [8, 9, 10])
def test_t5_energy_totals_conserved_across_h3_resolutions(res):
    bs = _buildings()
    cells = aggregate_to_cells(bs, resolution=res)
    assert cells.generation_kwh.sum() == pytest.approx(sum(b.generation_kwh.sum() for b in bs))
    assert cells.demand_kwh.sum() == pytest.approx(sum(b.demand_kwh.sum() for b in bs))
    assert cells.attributes["n_buildings"].sum() == len(bs)


def test_t5_sharing_never_reduces_self_consumption():
    cells = aggregate_to_cells(_buildings(), resolution=10)
    assert np.all(cells.self_consumed("shared") >= cells.self_consumed("independent") - 1e-12)
    m_sh, m_in = cells.metrics("shared"), cells.metrics("independent")
    assert np.all(m_sh["ssr"] >= m_in["ssr"] - 1e-12)
    assert np.allclose(m_sh["demand_kwh"], m_in["demand_kwh"])


# ---------------------------------------------------------------- smooth relaxation bound
@pytest.mark.parametrize("tol", [0.05, 0.01, 0.001])
def test_soft_min_ssr_error_bound_holds(tol):
    g = solar_irradiance(41.0) * 40
    d = demand_profile(g.sum() * 0.8, "residential")
    tau = tau_for_ssr_tolerance(d, tol)
    exact = load_match(g, d)["ssr"]
    smooth = load_match(g, d, tau=tau)["ssr"]
    assert smooth <= exact + 1e-12
    assert exact - smooth <= tol + 1e-12


def test_smooth_min_is_exact_at_zero_temperature():
    x, y = np.array([1.0, 3.0]), np.array([2.0, 2.0])
    assert np.array_equal(smooth_min(x, y, 0.0), np.minimum(x, y))


# ---------------------------------------------------------------- readiness index & XAI
def test_contributions_are_exact_shapley_efficiency():
    rng = np.random.default_rng(5)
    V = pd.DataFrame(rng.uniform(0, 1, (10, 3)), columns=["v_balance", "v_ssr", "v_relief"])
    w = {"v_balance": 0.5, "v_ssr": 0.3, "v_relief": 0.2}
    phi = contributions(V, w)
    s = energy_score(V, w)
    assert np.allclose(phi.sum(axis=1), s - s.mean())


def test_absolute_index_has_no_rank_reversal():
    rng = np.random.default_rng(6)
    V = pd.DataFrame(rng.uniform(0, 1, (8, 3)), columns=["v_balance", "v_ssr", "v_relief"])
    s_all = energy_score(V)
    V2 = pd.concat([V, pd.DataFrame([[1.0, 1.0, 1.0]], columns=V.columns)], ignore_index=True)
    assert np.allclose(energy_score(V2)[:8], s_all)  # adding an alternative changes nothing


def test_rank_intervals_shape_and_probabilities():
    rng = np.random.default_rng(7)
    V = pd.DataFrame(rng.uniform(0, 1, (6, 3)), columns=["v_balance", "v_ssr", "v_relief"])
    r = rank_intervals(V, n_samples=500, top_k=2)
    assert r["p_first"].sum() == pytest.approx(1.0)
    assert np.all(r["rank_lo"] <= r["rank_hi"])


def test_energy_values_clip_balance():
    vals = energy_values({"balance": np.array([0.5, 2.0]), "ssr": np.array([0.2, 0.4]), "peak_relief": np.array([0, 0.1])})
    assert np.allclose(vals["v_balance"], [0.5, 1.0])


# ---------------------------------------------------------------- stats helpers
def test_stats_match_scipy():
    scipy_stats = pytest.importorskip("scipy.stats")
    rng = np.random.default_rng(8)
    x = rng.integers(0, 5, 30).astype(float)
    y = x + rng.normal(0, 1, 30)
    assert spearman_rho(x, y) == pytest.approx(scipy_stats.spearmanr(x, y).statistic)
    assert kendall_tau_b(x, y) == pytest.approx(scipy_stats.kendalltau(x, y).statistic)
    assert np.allclose(rankdata(x), scipy_stats.rankdata(x))

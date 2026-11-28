"""Graph (coalitions, boundary growth), policy XAI and inverse-engine verification."""

import itertools

import numpy as np
import pytest

from pedx.energy.aggregate import CellEnergy
from pedx.graph import (
    coalition_values,
    exhaustive_best_cluster,
    grow_ped_boundary,
    random_contiguous_growth,
    shapley_self_consumption,
)
from pedx.inverse import CellState, audit, score, simulate
from pedx.synthetic import day_shape, demand_profile, solar_irradiance
from pedx.xai import inverse_weight_stability

T = 24 * 28  # four weeks keeps tests fast


def _line_cells(n=5):
    """n cells on a line graph; even cells are PV-rich day users, odd cells night users."""
    irr = solar_irradiance(41.0, n_hours=T)
    G, D = [], []
    for i in range(n):
        if i % 2 == 0:
            G.append(irr * 60)
            D.append(demand_profile(irr.sum() * 60 * 0.6 * 8760 / T, "day", n_hours=T))
        else:
            G.append(irr * 5)
            D.append(demand_profile(irr.sum() * 60 * 0.6 * 8760 / T, "night", n_hours=T))
    G, D = np.array(G), np.array(D)
    ids = [f"c{i}" for i in range(n)]
    cells = CellEnergy(ids, G, D, np.minimum(G, D))
    adj = {ids[i]: [ids[j] for j in (i - 1, i + 1) if 0 <= j < n] for i in range(n)}
    return cells, adj


# ---------------------------------------------------------------- coalition game
def test_coalition_game_is_superadditive_and_shapley_efficient():
    cells, _ = _line_cells(5)
    v = coalition_values(cells.generation_kwh, cells.demand_kwh)
    n = 5
    for a, b in itertools.combinations(range(1 << n), 2):
        if a & b == 0 and a and b:
            assert v[a | b] >= v[a] + v[b] - 1e-9
    phi = shapley_self_consumption(cells.generation_kwh, cells.demand_kwh, cells.cell_ids)
    assert phi["shapley_kwh"].sum() == pytest.approx(v[-1])
    assert np.all(phi["sharing_gain_kwh"] >= -1e-9)  # individual rationality


def test_shapley_symmetry():
    g = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 0.0]])
    d = np.array([[0.0, 1.0], [0.0, 1.0], [1.0, 0.0]])
    phi = shapley_self_consumption(g, d)
    assert phi["shapley_kwh"].iloc[0] == pytest.approx(phi["shapley_kwh"].iloc[1])


# ---------------------------------------------------------------- boundary growth
def test_growth_prefers_complementary_neighbour():
    cells, adj = _line_cells(5)
    res = grow_ped_boundary(cells, adj, seed="c2", max_cells=3, balance_target=0.0)
    assert set(res.path["added"]) == {"c1", "c2", "c3"}
    assert res.path["complementarity"].iloc[1] > 0


def test_growth_matches_exhaustive_on_small_graph():
    cells, adj = _line_cells(5)
    greedy = grow_ped_boundary(cells, adj, seed="c0", max_cells=3, balance_target=0.0)
    exact = exhaustive_best_cluster(cells, adj, seed="c0", size=3, objective="ssr", balance_target=None)
    from pedx.graph import cluster_metrics

    assert cluster_metrics(cells, greedy.path["added"].tolist())["ssr"] == pytest.approx(exact["value"])


def test_random_growth_is_connected():
    cells, adj = _line_cells(5)
    m = random_contiguous_growth(cells, adj, "c2", 4, np.random.default_rng(0))
    assert len(m) == 4
    for c in m[1:]:
        assert any(c in adj[o] for o in m if o != c)


# ---------------------------------------------------------------- policy XAI
def test_inverse_weight_stability_beats_all_competitors():
    V = np.array([[0.9, 0.1, 0.5], [0.2, 0.8, 0.5], [0.5, 0.5, 0.6], [0.1, 0.1, 0.1]])
    w0 = np.array([0.6, 0.2, 0.2])
    out = inverse_weight_stability(V, w0, k=1)
    assert out["potentially_optimal"]
    s = V @ out["weights"]
    assert s[1] >= s.max() - 1e-7
    assert out["min_l2_shift"] > 0
    dominated = inverse_weight_stability(V, w0, k=3)
    assert not dominated["potentially_optimal"] and dominated["min_l2_shift"] == np.inf


# ---------------------------------------------------------------- inverse model
def _state(T_=T, **kw):
    irr = solar_irradiance(41.0, n_hours=T_)
    D = demand_profile(60000, "residential", n_hours=T_)
    upper = kw.pop("upper", {"pv": 300.0, "storage": 150.0, "shift": 0.2, "retrofit": 0.35})
    return CellState(
        "x", irr * 0.2 * 0.84, np.zeros(T_), D,
        envelope_load_kwh=0.3 * D, shift_shape=np.tile(day_shape("office"), T_ // 24) / (T_ // 24),
        upper=upper, unit_cost={"pv": 220.0, "storage": 350.0, "shift": 40000.0, "retrofit": 60000.0}, **kw,
    )


def test_simulation_conserves_energy_and_passes_audit():
    st = _state()
    a = audit(st, [200, 0.2, 80, 0.1])
    assert a["passed"], a["checks"]


def test_shift_preserves_annual_demand():
    st = _state()
    r0 = simulate(st, np.zeros(4))["indicators"]
    r1 = simulate(st, np.array([0, 0, 0, 0.2]))["indicators"]
    assert r1["demand_kwh"] == pytest.approx(r0["demand_kwh"])


def test_smooth_simulation_converges_to_exact():
    jnp = pytest.importorskip("jax.numpy")
    import jax

    jax.config.update("jax_enable_x64", True)
    st = _state()
    u = np.array([150.0, 0.1, 60.0, 0.1])
    exact = float(score(st, u))
    errs = [abs(float(score(st, jnp.asarray(u), tau=t)) - exact) for t in (1.0, 0.1, 0.01)]
    assert errs[0] >= errs[1] >= errs[2]
    assert errs[2] < 1e-3


def test_engine_budget_optimum_matches_grid_search():
    pytest.importorskip("jax")
    from pedx.inverse import InverseEngine

    st = _state(upper={"pv": 300.0, "storage": 150.0})
    eng = InverseEngine(st, steps=80)
    budget = 45000.0
    p = eng.maximize_score(budget)
    assert p.audit["passed"] and p.cost <= budget + 1e-6
    best = 0.0
    for pv in np.linspace(0, budget / 220, 30):
        for cap in np.linspace(0, min(150, (budget - 220 * pv) / 350), 8):
            best = max(best, float(score(st, np.array([pv, 0, cap, 0]))))
    assert p.score >= best - 5e-3


def test_engine_min_cost_pv_only_matches_bisection():
    pytest.importorskip("jax")
    from pedx.inverse import InverseEngine

    st = _state(upper={"pv": 400.0})
    eng = InverseEngine(st, steps=60)
    target = 0.25  # reachable: max with 400 m² is ~0.33 in this 4-week winter scenario
    out = eng.min_cost_for_target(target, rel_tol=0.005)
    assert out["feasible"]
    p = out["prescription"]
    assert p.score >= target - 1e-9 and p.audit["passed"]
    lo, hi = 0.0, 400.0  # ground truth: score is monotone in PV area
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if float(score(st, np.array([mid, 0, 0, 0]))) >= target:
            hi = mid
        else:
            lo = mid
    assert p.cost == pytest.approx(hi * 220.0, rel=0.02)


def test_engine_reports_infeasible_target():
    pytest.importorskip("jax")
    from pedx.inverse import InverseEngine

    eng = InverseEngine(_state(upper={"pv": 10.0}), steps=20)
    out = eng.min_cost_for_target(0.95)
    assert not out["feasible"]


def test_pareto_curve_is_monotone():
    pytest.importorskip("jax")
    from pedx.inverse import InverseEngine

    eng = InverseEngine(_state(upper={"pv": 300.0, "storage": 150.0}), steps=40)
    df = eng.pareto_curve([0, 20000, 40000, 80000])
    assert np.all(np.diff(df["score"].to_numpy()) >= -1e-9)
    assert df["audit_passed"].all()


def test_marginal_value_has_no_phantom_storage_value_without_pv():
    pytest.importorskip("jax")
    from pedx.inverse import InverseEngine

    eng = InverseEngine(_state(upper={"pv": 300.0, "storage": 150.0}), steps=5)
    mv = eng.marginal_value()
    assert mv["storage_per_1k_eur"] == pytest.approx(0.0, abs=1e-12)
    assert mv["pv_per_1k_eur"] > 0

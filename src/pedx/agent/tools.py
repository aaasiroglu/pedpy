"""Agent tools: every number the agent says comes from one of these functions (tool-grounded answers).

Schemas follow the JSON-schema function-calling convention so any OpenAI-compatible LLM (e.g. a local
Qwen3 served by Ollama or vLLM) can call them; the rule-based planner calls them directly.
"""

from __future__ import annotations

import math
import unicodedata
from typing import Dict, List, Optional

import numpy as np

from .knowledge import atlas, cite, literature, score_logit, sig100, validation

__all__ = ["TOOLS", "SCHEMAS", "resolve_area", "call"]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower().replace("ı", "i")).encode("ascii", "ignore").decode()
    return "".join(ch for ch in s if ch.isalnum() or ch == " ")


ALIASES = {"istanbul": "istanbul", "kadikoy": "kadikoy", "caferaga": "caferaa_istanbul", "moda": "caferaa_istanbul",
           "amsterdam": "buiksloterham", "bilbao": "zorrotzaurre", "espoo": "kera", "oslo": "fornebu", "baerum": "fornebu",
           "oulu": "kaukovainio", "groningen": "paddepoel", "dijon": "fontaine_d_ouche", "turku": "linnakaupunki", "lyon": "confluence",
           "wien": "seestadt_aspern", "viyana": "seestadt_aspern", "vienna": "seestadt_aspern", "aspern": "seestadt_aspern",
           "lund": "brunnshg", "vitoria": "coronacin", "uppsala": "rosendal", "helsinki": "kalasatama", "helsinki kalasatama": "kalasatama",
           "nantes": "le_de_nantes", "leppavaara": "leppvaara"}


def resolve_area(text: str) -> Optional[str]:
    t = _norm(text)
    keys = {c["key"]: c for c in atlas()["cities"]}
    for alias, key in sorted(ALIASES.items(), key=lambda kv: -len(kv[0])):
        if alias in t and key in keys:
            return key
    for c in atlas()["cities"]:
        for name in (c["site"], c["city"].split("·")[0]):
            n = _norm(name).strip()
            if n and n in t:
                return c["key"]
    return None


def _city(area: str) -> dict:
    for c in atlas()["cities"]:
        if c["key"] == area:
            return c
    raise KeyError(f"unknown area {area!r}; use list_areas")


def _cell_index(c: dict, cell: Optional[str]) -> int:
    if cell is None:
        cell = c["site_r9"]
    for i, r in enumerate(c["cells"]):
        if r[0] == cell:
            return i
    raise KeyError(f"cell {cell} is not a candidate site in {c['key']}")


def _pct(values: np.ndarray, v: float) -> float:
    return float((values < v).mean() + 0.5 * (values == v).mean())


def _logits(c: dict) -> np.ndarray:
    if "_logits" not in c:
        c["_logits"] = np.array([score_logit(r[4]) for r in c["cells"]])
    return c["_logits"]


def _report(c: dict, i: int) -> List[dict]:
    rep = atlas()["report"]
    vals = np.array([[np.nan if x is None else x for x in r[5]] for r in c["cells"]], dtype=float)
    out = []
    for j, m in enumerate(rep):
        v = vals[i, j]
        col = vals[:, j][np.isfinite(vals[:, j])]
        out.append({"key": m["key"], "label": m["label"], "section": m["section"], "unit": m["unit"], "value": None if not np.isfinite(v) else float(v),
                    "city_percentile": None if not np.isfinite(v) or col.size == 0 else _pct(col, v)})
    return out


# ---------------------------------------------------------------- tools
def list_areas() -> dict:
    rows = []
    for c in atlas()["cities"]:
        L = _logits(c)
        rows.append({"area": c["key"], "name": c["site"], "city": c["city"], "is_real_ped": c["is_ped"], "candidate_sites": len(c["cells"]),
                     "median_score": float(np.median(sig100(L))), "balanced_share": float(np.mean([r[1] >= 1 for r in c["cells"]]))})
    return {"areas": rows}


def applicability(area: str, cell: Optional[str] = None) -> dict:
    """Area of applicability (Meyer & Pebesma 2021): weighted distance in criteria space to the nearest training site."""
    M = atlas()["model"]
    aoa = M.get("aoa")
    c = _city(area)
    i = _cell_index(c, cell)
    if not aoa:
        return {"inside": None, "note": "no AoA reference in atlas"}
    T = np.asarray(aoa["train_z"], float)
    w = np.asarray(M["weights"], float)
    z = np.asarray(c["cells"][i][4], float)
    dist = float(np.sqrt(((T - z) ** 2 * w).sum(axis=1)).min())
    return {"distance": dist, "threshold": aoa["threshold"], "inside": dist <= aoa["threshold"],
            "note": "inside: the site resembles sites the model was validated on" if dist <= aoa["threshold"]
            else "outside: the site is unlike any validated site — treat the score with caution"}


def _aoa_mask(c: dict) -> np.ndarray:
    M = atlas()["model"]
    aoa = M.get("aoa")
    if not aoa:
        return np.ones(len(c["cells"]), bool)
    if "_aoa" not in c:
        T, w = np.asarray(aoa["train_z"], float), np.asarray(M["weights"], float)
        Zc = np.asarray([r[4] for r in c["cells"]], float)
        d = np.sqrt((((Zc[:, None, :] - T[None, :, :]) ** 2) * w).sum(axis=2)).min(axis=1)
        c["_aoa"] = d <= aoa["threshold"]
    return c["_aoa"]


SPECIAL_MAX = 50.0  # % of the site disc in OSM special land (aerodrome, industrial, military, port, rail yard); set a priori


def _residential_mask(c: dict):
    """Land-use sanity guard (K-054): a PED here is a residential/mixed district. Sites with more than SPECIAL_MAX % of
    their area in OSM special land (aerodromes, industrial estates, ports, military, rail yards) are not recommended.
    Found the hard way: HRSL assigns 1 757 people to the Istanbul Airport terminal, whose vast roofs then 'balance'
    them; neither GHSL NRES (4 % non-residential there) nor Overture land use (no aerodrome polygon) caught it."""
    keys = [m["key"] for m in atlas()["report"]]
    if "special_share" not in keys:
        return np.ones(len(c["cells"]), bool), False
    j = keys.index("special_share")
    v = np.array([np.nan if r[5][j] is None else r[5][j] for r in c["cells"]], float)
    return ~(v > SPECIAL_MAX), True


def find_sites(area: str, k: int = 5, objective: str = "score", require_balance: bool = False, min_population: int = 100,
               applicable_only: bool = True, residential_only: bool = True) -> dict:
    """Top-k candidate sites (~28 ha) by PED score or a report metric. By default only sites inside the model's area of
    applicability are recommended (Meyer & Pebesma 2021); the number excluded is reported."""
    c = _city(area)
    L = _logits(c)
    rep_keys = [m["key"] for m in atlas()["report"]]
    if objective == "score":
        val = L.copy()
    else:
        j = rep_keys.index(objective)
        val = np.array([np.nan if r[5][j] is None else r[5][j] for r in c["cells"]], dtype=float)
    ok = np.array([(r[2] >= min_population) and (not require_balance or r[1] >= 1) for r in c["cells"]]) & np.isfinite(val)
    inside = _aoa_mask(c)
    resm, covered = _residential_mask(c)
    n_nonres = int((ok & ~resm).sum()) if residential_only else 0
    if residential_only:
        ok &= resm
    n_outside = int((ok & ~inside).sum())
    if applicable_only:
        ok &= inside
    idx = np.argsort(-np.where(ok, val, -np.inf))[: int(k)]
    sites = []
    for i in idx:
        if not ok[i]:
            continue
        r = c["cells"][i]
        rep = _report(c, int(i))
        top = sorted([x for x in rep if x["city_percentile"] is not None and x["key"] != "nonosm_share"], key=lambda x: -x["city_percentile"])[:3]
        la, lo = _h3_center(r[0])
        sites.append({"cell": r[0], "lat": la, "lon": lo, "score": float(sig100(L[i])), "city_percentile": _pct(L, L[i]), "balance": r[1],
                      "population": r[2], "strengths": [f"{x['label']} (%{100 * x['city_percentile']:.0f})" for x in top],
                      "applicability": bool(inside[i])})
    return {"area": area, "name": c["site"], "objective": objective, "require_balance": require_balance, "sites": sites,
            "n_candidates": int(ok.sum()), "n_outside_applicability": n_outside, "applicable_only": applicable_only,
            "n_non_residential_excluded": n_nonres, "landuse_guard_active": residential_only and covered}


def _h3_center(cell: str):
    import h3

    return h3.cell_to_latlng(cell)


def assess_site(area: str, cell: Optional[str] = None) -> dict:
    """Score, exact contributions, physics and the full site report (city percentiles) for one candidate site."""
    A = atlas()
    M = A["model"]
    c = _city(area)
    i = _cell_index(c, cell)
    r = c["cells"][i]
    L = _logits(c)
    contrib = {f: float(b * z) for f, b, z in zip(M["features"], M["coef"], r[4])}
    from ..params import PARAMS

    thr = c["kwh_per_capita"] / (PARAMS["roof_utilization"]["value"] * PARAMS["module_efficiency"]["value"] * c["pv_yield"]) if c.get("kwh_per_capita") and c.get("pv_yield") else None
    return {"area": area, "name": c["site"], "cell": r[0], "score": float(sig100(L[i])), "city_percentile": _pct(L, L[i]),
            "balance": r[1], "population": r[2], "footprint_m2": r[3], "footprint_per_capita_m2": r[3] / max(r[2], 1),
            "threshold_footprint_per_capita_m2": thr, "contributions": contrib, "labels": M["labels_tr"],
            "report": _report(c, i), "applicability": applicability(area, r[0]), "is_real_ped_site": c["is_ped"] and r[0] == c["site_r9"]}


def inverse(area: str, cell: Optional[str] = None, target: float = 70.0) -> dict:
    """Smallest lever change (roof use → module efficiency → demand cut) to reach a target score; closed form."""
    M = atlas()["model"]
    c = _city(area)
    i = _cell_index(c, cell)
    r = c["cells"][i]
    L0 = score_logit(r[4])
    ib = M["features"].index("log_energy_balance")
    sd, beta = c["stats"]["log_energy_balance"]["sd"], M["coef"][ib]
    from ..params import PARAMS

    u0, umax = PARAMS["roof_utilization"]["value"], PARAMS["roof_utilization"]["high"]
    e0, emax, cutmax = PARAMS["module_efficiency"]["value"], PARAMS["module_efficiency"]["high"], 0.5
    if sig100(L0) >= target:
        return {"feasible": True, "score_now": float(sig100(L0)), "note": "already above target"}
    t = min(max(target, 0.01), 99.99) / 100
    need = math.exp((math.log(t / (1 - t)) - L0) * sd / beta)
    fu = min(need, umax / u0)
    fe = min(need / fu, emax / e0)
    fd = min(need / (fu * fe), 1 / (1 - cutmax))
    got = fu * fe * fd
    z2 = list(r[4])
    z2[ib] += math.log(got) / sd
    return {"score_now": float(sig100(L0)), "target": target, "feasible": got >= need * (1 - 1e-9), "roof_utilization": u0 * fu,
            "module_efficiency": e0 * fe, "demand_cut": 1 - 1 / fd, "balance_now": r[1], "balance_after": r[1] * got,
            "balance_needed": r[1] * need, "score_after": float(sig100(score_logit(z2)))}


def compare_areas(a: str, b: str) -> dict:
    rows = {x["area"]: x for x in list_areas()["areas"]}
    return {"a": rows[a], "b": rows[b]}


def validation_summary() -> dict:
    v = validation()
    s = v.get("ped_validation_summary", {})
    return {"auc_balance": s.get("auc_pooled"), "sites_above_median": s.get("sites_above_median"), "n_sites": s.get("n_sites"),
            "auc_density_matched": s.get("auc_matched"), "auc_ped_score_loco": atlas()["model"].get("auc_loco"),
            "maup": (v.get("maup_validation") or {}).get("summary"), "scaling": (v.get("data_scaling") or {}).get("curve"),
            "schemes": (v.get("feature_analysis") or {}).get("schemes")}


def literature_search(query: str, k: int = 5) -> dict:
    q = set(_norm(query).split())
    hits = []
    for tid, t in literature().items():
        for ref in t["refs"]:
            words = set(_norm(ref + " " + t["title"]).split())
            s = len(q & words)
            if s:
                hits.append((s, tid, t["title"], ref))
    hits.sort(key=lambda x: -x[0])
    themes = sorted({h[1] for h in hits[:k]})
    return {"query": query, "references": [f"[{h[1]}] {h[3]}" for h in hits[:k]],
            "trends": {tid: literature()[tid]["trend"] for tid in themes}}


TOOLS = {"list_areas": list_areas, "find_sites": find_sites, "assess_site": assess_site, "inverse": inverse,
         "compare_areas": compare_areas, "validation": validation_summary, "applicability": applicability, "literature": literature_search}

_AREA = {"type": "string", "description": "area key from list_areas (e.g. istanbul, kadikoy, caferaa_istanbul, confluence)"}
SCHEMAS = [
    {"name": "list_areas", "description": "List analysable areas (real PED cities and Turkish pilots) with median PED score.", "parameters": {"type": "object", "properties": {}}},
    {"name": "find_sites", "description": "Find the best ~28 ha candidate sites in an area by PED score or by a report metric.",
     "parameters": {"type": "object", "properties": {"area": _AREA, "k": {"type": "integer"}, "objective": {"type": "string"},
                                                     "require_balance": {"type": "boolean"}}, "required": ["area"]}},
    {"name": "assess_site", "description": "Full assessment of one site: score, exact contributions, physics, 36-metric report.",
     "parameters": {"type": "object", "properties": {"area": _AREA, "cell": {"type": "string"}}, "required": ["area"]}},
    {"name": "inverse", "description": "Minimum roof/efficiency/demand change to reach a target PED score.",
     "parameters": {"type": "object", "properties": {"area": _AREA, "cell": {"type": "string"}, "target": {"type": "number"}}, "required": ["area"]}},
    {"name": "compare_areas", "description": "Compare two areas.", "parameters": {"type": "object", "properties": {"a": _AREA, "b": _AREA}, "required": ["a", "b"]}},
    {"name": "validation", "description": "Validation evidence: AUC vs real PEDs, MAUP, data scaling, weighting schemes.", "parameters": {"type": "object", "properties": {}}},
    {"name": "applicability", "description": "Is the site within the model's area of applicability?", "parameters": {"type": "object", "properties": {"area": _AREA, "cell": {"type": "string"}}, "required": ["area"]}},
    {"name": "literature", "description": "Search the project's literature map.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
]


def call(name: str, args: Dict) -> dict:
    out = TOOLS[name](**args)
    out["_citations"] = cite(name)
    return out

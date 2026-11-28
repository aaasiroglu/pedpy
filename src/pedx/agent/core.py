"""pedx-agent: a tool-grounded planning agent for PED / urban-transformation decisions (K-054).

Loop (ReAct; Yao et al. 2023): question → plan (thought) → tool calls (action) → observations → answer.
Two planners share the same tools and answer composer:

* ``rule``  — deterministic Turkish/English intent parser; offline, reproducible, always available.
* ``llm``   — any OpenAI-compatible chat endpoint with tool calling (e.g. a local Qwen3-8B on Ollama/vLLM:
              PEDX_LLM_BASE_URL=http://localhost:11434/v1, PEDX_LLM_MODEL=qwen3:8b). The LLM only chooses tools and
              arguments; the answer text is composed from tool observations.

Grounding guard (against hallucination; Ji et al. 2023): if an LLM narrative is requested, every number in it must
appear in the observations, otherwise the narrative is discarded and the template answer is returned.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Dict, List, Optional, Tuple

from .knowledge import atlas
from .tools import SCHEMAS, _norm, call, resolve_area

__all__ = ["plan_rule", "run", "compose"]

from .glossary import OBJECTIVE_TERMS, match_objective, match_places, wants_balance  # noqa: E402

OBJECTIVES = [(v, k) for k, v in OBJECTIVE_TERMS.items()]  # kept for callers; the glossary is the source (K-058)


def _has(t: str, phrase: str) -> bool:
    """Whole-word / whole-phrase match (Turkish suffixes allowed after the stem: 'kadikoyde' matches 'kadikoy')."""
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase), t) is not None


def _target(t: str):
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*puan", t) or re.search(r"hedef\D{0,12}(\d+(?:[.,]\d+)?)", t)
    return float(m.group(1).replace(",", ".")) if m else 70.0


def _k(t: str) -> int:
    m = re.search(r"(?:en (?:iyi|uygun)|top|best)\D{0,10}(\d{1,2})|(\d{1,2})\s*(?:saha|aday|yer|site)", t)
    n = next((g for g in (m.groups() if m else ()) if g), None)
    return max(1, min(20, int(n))) if n else 5


def _number(t: str, default=None):
    m = re.search(r"(\d+(?:[.,]\d+)?)", t)
    return float(m.group(1).replace(",", ".")) if m else default


def plan_rule(q: str) -> Tuple[List[Tuple[str, dict]], str]:
    """Return (plan, thought). Deterministic; covers the decision questions of the thesis."""
    t = _norm(q)
    areas = [k for _, k, _ in match_places(q)]  # aliases + data gazetteer (K-058)
    if not areas:
        for chunk in re.split(r"\bile\b|\bve\b|\bvs\b|\bversus\b|,", t):
            a = resolve_area(chunk)
            if a and a not in areas:
                areas.append(a)
    area = areas[0] if areas else None
    if any(_has(t, w) for w in ("dogrula", "guvenilir", "auc", "validation", "kanit", "ne kadar dogru")):
        return [("validation", {})], "Soru modelin güvenilirliği hakkında: doğrulama kanıtı çağrılıyor."
    if any(_has(t, w) for w in ("literatur", "kaynak", "makale", "reference", "atif")):
        return [("literature", {"query": q})], "Literatür sorusu: proje literatür haritasında arama yapılıyor."
    if any(_has(t, w) for w in ("karsilastir", "kiyasla", "compare", "fark")) and len(areas) >= 2:
        return [("compare_areas", {"a": areas[0], "b": areas[1]})], f"İki alan karşılaştırılıyor: {areas[0]} ve {areas[1]}."
    if any(_has(t, w) for w in ("hangi alan", "alanlar", "liste", "list")) or area is None:
        return [("list_areas", {})], "Alan belirtilmedi ya da liste istendi: analiz edilebilir alanlar listeleniyor."
    target = None
    if any(_has(t, w) for w in ("hedef", "ne gerek", "nasil ulas", "kac puan", "puana", "target", "yukselt", "artir")):
        target = _target(t)
    mo = match_objective(q)
    objective = mo[0] if mo else "score"
    k = _k(t)
    plan = [("find_sites", {"area": area, "k": k, "objective": objective, "require_balance": wants_balance(q) or _has(t, "pozitif")})]
    thought = f"{area} alanında en uygun {k} saha aranıyor (sıralama: {objective})."
    if any(_has(t, w) for w in ("neden", "acikla", "why", "explain", "rapor", "analiz")) or target is not None:
        plan.append(("assess_site", {"area": area, "cell": "@best"}))
        thought += " En iyi saha ayrıntılı açıklanacak."
    if target is not None:
        plan.append(("inverse", {"area": area, "cell": "@best", "target": target}))
        thought += f" Hedef puan {target:.0f} için tersine analiz yapılacak."
    return plan, thought


def _llm_plan(q: str) -> Optional[Tuple[List[Tuple[str, dict]], str]]:
    from .llm import plan_llm

    return plan_llm(q)


VALID_TOOLS = {"list_areas", "find_sites", "assess_site", "inverse", "compare_areas", "validation", "applicability", "literature"}


def repair(plan: List[Tuple[str, dict]]) -> List[Tuple[str, dict]]:
    """Deterministic plan repair for LLM plans (K-055): a step that refers to the best site must be preceded by
    find_sites in the same area; 'best'/'en iyi' spellings are normalised to '@best'."""
    out, have_find = [], set()
    for name, args in plan:
        args = dict(args or {})
        if str(args.get("cell", "")).lower().strip("@ ") in ("best", "en iyi", "en_iyi"):
            args["cell"] = "@best"
        if args.get("cell") == "@best" and args.get("area") and args["area"] not in have_find:
            out.append(("find_sites", {"area": args["area"], "k": 5, "objective": "score"}))
            have_find.add(args["area"])
        if name == "find_sites" and args.get("area"):
            have_find.add(args["area"])
        out.append((name, args))
    return out


def _sanitize(plan: List[Tuple[str, dict]]) -> List[Tuple[str, dict]]:
    """Drop unknown tools / arguments an LLM may invent (schema guard); keep the order."""
    import inspect

    from .tools import TOOLS

    out = []
    for name, args in plan:
        if name not in VALID_TOOLS:
            continue
        sig = inspect.signature(TOOLS[name]).parameters
        out.append((name, {k: v for k, v in (args or {}).items() if k in sig}))
    return out


def _pct(x):
    return "—" if x is None else f"%{100 * x:.0f}"


def compose(q: str, trace: List[dict]) -> str:
    """Turkish answer from observations only (no free numbers)."""
    out = []
    for step in trace:
        o, name = step["observation"], step["action"]
        if "error" in o:
            out.append(f"⚠️ {name}: {o['error']}")
        elif name == "find_sites":
            s = o["sites"]
            out.append(f"**{o['name']}** içinde {o['n_candidates']} aday saha incelendi; {'PED puanına' if o['objective'] == 'score' else o['objective'] + ' göstergesine'} göre en iyi {len(s)} saha:"
                       + (f" ({o['n_outside_applicability']} saha, modelin doğrulandığı sahalara benzemediği için önerilmedi: uygulanabilirlik alanı dışı.)" if o.get("n_outside_applicability") else "")
                       + (f" ({o['n_non_residential_excluded']} saha, alanının yarısından fazlası havalimanı, sanayi, liman ya da askeri arazi olduğu için elendi; OSM, yoksa Overture havalimanı kümeleri.)" if o.get("n_non_residential_excluded") else ""))
            for i, x in enumerate(s, 1):
                warn = " ⚠️ uygulanabilirlik alanı dışında" if x["applicability"] is False else ""
                out.append(f"{i}. `{x['cell']}`: PED puanı {x['score']:.0f} (kent içi {_pct(x['city_percentile'])}), denge {x['balance']:.2f}, "
                           f"{x['population']} kişi; öne çıkan: {', '.join(x['strengths'])}{warn}")
        elif name == "assess_site":
            con = sorted(o["contributions"].items(), key=lambda kv: -abs(kv[1]))
            out.append(f"**Saha `{o['cell']}`**: PED puanı {o['score']:.0f}, kent içi yüzdelik {_pct(o['city_percentile'])}, yıllık denge {o['balance']:.2f} "
                       f"(kişi başı çatı tabanı {o['footprint_per_capita_m2']:.1f} m², eşik {o['threshold_footprint_per_capita_m2']:.1f} m²).")
            out.append("Puanı oluşturanlar: " + "; ".join(f"{o['labels'].get(f, f)} {v:+.2f}" for f, v in con))
            rep = [x for x in o["report"] if x["city_percentile"] is not None]
            hi = sorted(rep, key=lambda x: -x["city_percentile"])[:3]
            lo = sorted(rep, key=lambda x: x["city_percentile"])[:3]
            out.append("Kentinde öne çıkan: " + ", ".join(f"{x['label']} {_pct(x['city_percentile'])}" for x in hi) +
                       ". Geride kalan: " + ", ".join(f"{x['label']} {_pct(x['city_percentile'])}" for x in lo) + ".")
            a = o["applicability"]
            if a.get("inside") is False:
                out.append("⚠️ Bu saha, modelin doğrulandığı sahalara benzemiyor (uygulanabilirlik alanı dışında); puan dikkatle okunmalı.")
        elif name == "inverse":
            if o.get("note"):
                out.append(f"Saha zaten hedefin üstünde (puan {o['score_now']:.0f}).")
            else:
                out.append(f"Hedef {o['target']:.0f} için: çatı kullanımı %{100 * o['roof_utilization']:.0f}, modül verimi %{100 * o['module_efficiency']:.1f}, "
                           f"talep azaltımı %{100 * o['demand_cut']:.0f} → denge {o['balance_now']:.2f} → {o['balance_after']:.2f}, puan {o['score_after']:.0f}"
                           + (" ✓" if o["feasible"] else " — enerji kaldıraçları yetmiyor; kentsel dönüşüm ölçeğinde değişiklik gerekir (yapı örtüsü, yeşil, işlev)."))
        elif name == "compare_areas":
            a, b = o["a"], o["b"]
            out.append(f"**{a['name']}**: PED puanı medyanı {a['median_score']:.0f}, dengedeki saha payı {_pct(a['balanced_share'])} · "
                       f"**{b['name']}**: {b['median_score']:.0f}, {_pct(b['balanced_share'])}.")
        elif name == "list_areas":
            out.append("Analiz edilebilir alanlar: " + "; ".join(f"{x['name']} ({'gerçek PED' if x['is_real_ped'] else 'pilot'}, medyan {x['median_score']:.0f})" for x in o["areas"]))
        elif name == "validation":
            out.append(f"Gerçek PED doğrulaması: yalnız denge AUC {o['auc_balance']:.2f} ({o['sites_above_median']}/{o['n_sites']} saha kontrollerin medyanı üstünde); "
                       f"nüfus yoğunluğu eşlemeli {o['auc_density_matched']:.2f}; PED puanı (kent dışarıda) {o['auc_ped_score_loco']:.2f}.")
        elif name == "literature":
            out.append("Literatür: " + " | ".join(o["references"][:5]) if o["references"] else "Literatür haritasında eşleşme bulunamadı.")
        elif name == "applicability":
            out.append(f"Uygulanabilirlik: {'içinde' if o.get('inside') else 'dışında'} (uzaklık {o.get('distance', 0):.2f}, eşik {o.get('threshold', 0):.2f}).")
    return "\n".join(out)


def run(q: str, planner: str = "auto") -> Dict:
    plan, thought, used = None, "", "rule"
    if planner in ("auto", "llm"):
        try:
            r = _llm_plan(q)
            if r and _sanitize(r[0]):
                plan, thought, used = repair(_sanitize(r[0])), r[1], "llm"
        except Exception as exc:  # noqa: BLE001
            thought = f"LLM planlayıcı kullanılamadı ({type(exc).__name__}); kural tabanlı planlayıcıya geçildi. "
    if plan is None:
        plan, t2 = plan_rule(q)
        thought += t2
    trace, best = [], None
    for name, args in plan:
        args = dict(args)
        if args.get("cell") == "@best":
            args["cell"] = best
        try:
            obs = call(name, args)
        except Exception as exc:  # noqa: BLE001
            obs = {"error": f"{type(exc).__name__}: {exc}"}
        if name == "find_sites" and obs.get("sites"):
            best = obs["sites"][0]["cell"]
        trace.append({"action": name, "args": args, "observation": obs})
    citations = sorted({c for s in trace for c in s["observation"].get("_citations", [])})
    return {"question": q, "planner": used, "thought": thought, "plan": [{"tool": n, "args": a} for n, a in plan],
            "trace": trace, "answer": compose(q, trace), "citations": citations,
            "areas_available": [c["key"] for c in atlas()["cities"]]}

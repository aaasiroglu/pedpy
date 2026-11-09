"""pedx-agent: planner intents and tool grounding (K-054). Uses the committed atlas (web/data/atlas.json)."""

import json
import re
from pathlib import Path

import pytest

ATLAS = Path(__file__).resolve().parents[1] / "web" / "data" / "atlas.json"
pytestmark = pytest.mark.skipif(not ATLAS.exists(), reason="atlas not built")
h3 = pytest.importorskip("h3")


def test_planner_intents():
    from pedx.agent.core import plan_rule

    p, _ = plan_rule("İstanbul'da PED için en uygun 3 sahayı bul ve en iyisini açıkla, 70 puana ne gerekir?")
    assert [n for n, _ in p] == ["find_sites", "assess_site", "inverse"]
    assert p[0][1]["area"] == "istanbul" and p[0][1]["k"] == 3 and p[0][1]["objective"] == "score" and p[2][1]["target"] == 70.0
    assert plan_rule("Kadıköy ile Lyon'u karşılaştır")[0][0] == ("compare_areas", {"a": "kadikoy", "b": "confluence"})
    assert plan_rule("Model ne kadar güvenilir?")[0][0][0] == "validation"
    assert plan_rule("Kadıköy'de kentsel dönüşüm için aday sahalar")[0][0][1]["objective"] == "construction_share"
    assert plan_rule("en iyisini açıkla İstanbul")[0][0][1]["objective"] == "score"  # 'isi' inside 'iyisini' must not trigger heat


def test_answer_numbers_are_grounded_in_observations():
    from pedx.agent import run

    r = run("Kadıköy'de PED için en uygun 3 sahayı bul ve en iyisini açıkla, 60 puana ne gerekir?", planner="rule")
    obs = json.dumps([s["observation"] for s in r["trace"]], ensure_ascii=False, default=str)
    nums_obs = {round(float(x), 1) for x in re.findall(r"-?\d+\.\d+|-?\d+", obs)}
    for x in re.findall(r"(?<![\w`])-?\d+(?:\.\d+)?", r["answer"]):
        v = float(x)
        # every number in the answer is an observation value (possibly scaled to %, rounded) or a step index
        assert any(abs(v - o) <= 0.51 or abs(v - 100 * o) <= 0.51 or v <= 20 for o in nums_obs), x
    assert r["citations"], "answers carry literature citations"


def test_find_sites_respects_guards_and_k():
    from pedx.agent.tools import find_sites

    o = find_sites("istanbul", k=4)
    assert len(o["sites"]) == 4 and all(s["applicability"] for s in o["sites"])
    assert o["n_outside_applicability"] >= 0 and "n_non_residential_excluded" in o


def test_inverse_reaches_target_when_feasible():
    from pedx.agent.tools import find_sites, inverse

    cell = find_sites("kadikoy", k=40)["sites"][-1]["cell"]
    o = inverse("kadikoy", cell, target=50.0)
    if o.get("feasible") and not o.get("note"):
        assert o["score_after"] == pytest.approx(50.0, abs=1e-6)


def test_qwen_tool_call_parsing_and_plan_repair():
    from pedx.agent.core import _sanitize, repair
    from pedx.agent.llm import parse_tool_calls, system_prompt

    text = '<think>\n</think>\n<tool_call>\n{"name": "inverse", "arguments": {"area": "kadikoy", "cell": "best", "target": 85}}\n</tool_call>' \
           '<tool_call>{"name": "made_up_tool", "arguments": {}}</tool_call><tool_call>{bad json}</tool_call>'
    calls = parse_tool_calls(text)
    assert calls == [("inverse", {"area": "kadikoy", "cell": "best", "target": 85}), ("made_up_tool", {})]
    plan = repair(_sanitize(calls))  # unknown tool dropped; best-site step gets its find_sites
    assert [n for n, _ in plan] == ["find_sites", "inverse"] and plan[1][1]["cell"] == "@best"
    sp = system_prompt()
    assert "<tools>" in sp and "istanbul" in sp and "third_places_per_1000" in sp and "Never answer with numbers" in sp


def test_react_intent_guard_drops_unrequested_inverse(monkeypatch):
    """K-056: Qwen3-8B invented target scores; inverse must not run unless the user asked for a target."""
    from pedx.agent import llm

    class Fake:
        def __init__(self):
            self.turn = 0

        def create_chat_completion(self, messages, **kw):
            self.turn += 1
            txt = ('<tool_call>{"name": "find_sites", "arguments": {"area": "kadikoy", "k": 2}}</tool_call>'
                   '<tool_call>{"name": "inverse", "arguments": {"area": "kadikoy", "cell": "@best", "target": 70}}</tool_call>') if self.turn == 1 else "DONE"
            return {"choices": [{"message": {"content": txt}}]}

    monkeypatch.setattr(llm, "_llama", lambda path: Fake())
    calls, _ = llm.react_gguf("Kadıköy'de en uygun sahaları göster", "x.gguf")
    assert [n for n, _ in calls] == ["find_sites"]
    calls, _ = llm.react_gguf("Kadıköy'de 70 puana ne gerekir?", "x.gguf")
    assert [n for n, _ in calls] == ["find_sites", "inverse"] and calls[1][1]["cell"] != "@best"

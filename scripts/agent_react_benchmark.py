"""Multi-turn ReAct planner benchmark (K-056): does seeing tool results help Qwen3-8B (and 4B)?

Same 40 dev + 30 held-out questions and gold labels as scripts/agent_llm_benchmark.py. The *effective plan* is the list of
executed tool calls with leading exploration calls (list_areas) removed when other calls follow — exploration is
legitimate in ReAct. Scored like the single-shot benchmark; additionally: number of tool calls, extra calls beyond
the gold plan length (scope creep), and wall time per question (4 CPU cores, llama.cpp, Q4_K_M).

    PEDX_REACT_RUNS="data/models/Qwen3-8B-Q4_K_M.gguf:dev+heldout,data/models/Qwen3-4B-Q4_K_M.gguf:heldout" python scripts/agent_react_benchmark.py
"""

import json
import os
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from agent_benchmark import INTENTS  # noqa: E402
from agent_llm_benchmark import HELDOUT, HELDOUT2, score  # noqa: E402

from pedx.agent.llm import react_gguf  # noqa: E402


def effective(calls):
    i = 0
    while i < len(calls) - 1 and calls[i][0] == "list_areas":
        i += 1
    return calls[i:]


def gold_len(tool, extra):
    return 2 if isinstance(extra, float) else 1  # find_sites + inverse for target questions; one call otherwise


if __name__ == "__main__":
    runs = [r.split(":") for r in os.environ.get("PEDX_REACT_RUNS", "").split(",") if r]
    sets = {"dev": ("geliştirme (40)", INTENTS), "heldout": ("bağımsız (30)", HELDOUT), "heldout2": ("bağımsız-2 (30)", HELDOUT2)}
    out_path = ROOT / "data" / "validation" / "agent_react_benchmark.json"
    rows = json.loads(out_path.read_text())["per_question"] if out_path.exists() else []
    for path, which in runs:
        name = Path(path).stem + " · ReAct" + os.environ.get("PEDX_REACT_LABEL", "")
        for key in which.split("+"):
            sname, items = sets[key]
            for q, tool, area, extra in items:
                if any(r["planner"] == name and r["q"] == q for r in rows):
                    continue
                t = time.time()
                try:
                    calls, _ = react_gguf(q, path, max_turns=4)
                except Exception as exc:  # noqa: BLE001
                    calls = []
                    print("ERR", exc, flush=True)
                eff = effective(calls)
                sc = score(eff, tool, area, extra)
                rows.append({"planner": name, "set": sname, "q": q, "seconds": time.time() - t, "n_calls": len(calls),
                             "extra_calls": max(0, len(eff) - gold_len(tool, extra)), "explored": len(calls) - len(eff),
                             "plan": json.dumps(calls, ensure_ascii=False), **sc})
                print(name, sname, f"{rows[-1]['seconds']:5.1f}s", "OK " if sc["all_ok"] else "XX ", q[:55], "→", json.dumps(calls, ensure_ascii=False)[:150], flush=True)
                out_path.write_text(json.dumps({"per_question": rows}, ensure_ascii=False, indent=1))  # checkpoint
    R = pd.DataFrame(rows)
    S = R.groupby(["planner", "set"]).agg(tool=("tool_ok", "mean"), area=("area_ok", "mean"), arg=("arg_ok", "mean"), exact=("all_ok", "mean"),
                                          calls=("n_calls", "mean"), extra=("extra_calls", "mean"), explored=("explored", "mean"),
                                          sec_per_q=("seconds", "mean"), n=("q", "size")).reset_index()
    print(S.round(3).to_string())
    out_path.write_text(json.dumps({"summary": S.round(4).to_dict(orient="records"), "per_question": rows,
                                    "hardware": f"{os.cpu_count()} CPU cores, no GPU (llama.cpp, Q4_K_M)", "max_turns": 4}, ensure_ascii=False, indent=1))

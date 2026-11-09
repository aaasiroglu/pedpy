"""LLM planners for pedx-agent (K-055): local Qwen3 (GGUF via llama.cpp) or any OpenAI-compatible endpoint.

The LLM only produces a *plan* — tool names and arguments. It never writes the answer; the answer is composed
from tool observations (pedx.agent.core.compose). Prompt = Qwen3 / Hermes tool-calling format with the area
catalogue and objective vocabulary as context (retrieval of the domain vocabulary, not of numbers).

    PEDX_LLM_GGUF=/path/Qwen3-8B-Q4_K_M.gguf        local, CPU (llama-cpp-python)
    PEDX_LLM_BASE_URL=http://localhost:11434/v1      OpenAI-compatible server (Ollama, vLLM), with PEDX_LLM_MODEL
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from functools import lru_cache
from typing import List, Optional, Tuple

from .knowledge import atlas
from .tools import SCHEMAS

__all__ = ["system_prompt", "parse_tool_calls", "plan_gguf", "plan_openai", "plan_llm"]


def system_prompt() -> str:
    areas = "; ".join(f"{c['key']} = {c['site']} ({c['city'].split('·')[0].strip()})" for c in atlas()["cities"])
    objectives = "; ".join(f"{m['key']} = {m['label']}" for m in atlas()["report"])
    tools = "\n".join(json.dumps({"type": "function", "function": s}, ensure_ascii=False) for s in SCHEMAS)
    return f"""You are pedx-agent, a planning agent for Positive Energy District (PED) and urban-transformation decisions.
Your only job is to choose tool calls. Never answer with numbers or facts yourself.

Areas (use the key): {areas}.
Ranking objectives for find_sites (use the key; default "score" = PED score): {objectives}.
Rules:
- Best/most suitable sites in an area → find_sites(area, k, objective). Use k from the question (default 5).
- Explain / why / analyse the best site → also assess_site(area, cell="@best").
- A target score ("70 puana ne gerekir", "reach 60") → also inverse(area, cell="@best", target).
- "Only self-sufficient / balanced" sites → find_sites(..., require_balance=true).
- Compare two areas → compare_areas(a, b). Reliability / validation / AUC → validation(). Literature, sources, references → literature(query).
- Which areas exist → list_areas().

# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{tools}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{{"name": <function-name>, "arguments": <args-json-object>}}
</tool_call>"""


def parse_tool_calls(text: str) -> List[Tuple[str, dict]]:
    calls = []
    for blob in re.findall(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", text, flags=re.S):
        try:
            d = json.loads(blob)
            calls.append((d["name"], d.get("arguments") or {}))
        except (json.JSONDecodeError, KeyError):
            continue
    return calls


@lru_cache(maxsize=2)
def _llama(path: str):
    from llama_cpp import Llama

    return Llama(model_path=path, n_ctx=8192, n_threads=os.cpu_count() or 4, verbose=False)


def plan_gguf(q: str, path: Optional[str] = None) -> Optional[Tuple[List[Tuple[str, dict]], str]]:
    path = path or os.environ.get("PEDX_LLM_GGUF")
    if not path:
        return None
    llm = _llama(path)
    out = llm.create_chat_completion(messages=[{"role": "system", "content": system_prompt()},
                                               {"role": "user", "content": q + " /no_think"}],
                                     temperature=0.0, max_tokens=400)
    text = out["choices"][0]["message"]["content"] or ""
    calls = parse_tool_calls(text)
    return (calls, f"Qwen3 planı ({os.path.basename(path)})") if calls else None


def plan_openai(q: str) -> Optional[Tuple[List[Tuple[str, dict]], str]]:
    base, model = os.environ.get("PEDX_LLM_BASE_URL"), os.environ.get("PEDX_LLM_MODEL")
    if not base or not model:
        return None
    body = {"model": model, "temperature": 0, "messages": [{"role": "system", "content": system_prompt()}, {"role": "user", "content": q}],
            "tools": [{"type": "function", "function": s} for s in SCHEMAS], "tool_choice": "auto"}
    rq = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                                headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ.get("PEDX_LLM_API_KEY", "none")})
    with urllib.request.urlopen(rq, timeout=180) as r:  # noqa: S310
        msg = json.load(r)["choices"][0]["message"]
    calls = [(c["function"]["name"], json.loads(c["function"]["arguments"] or "{}")) for c in msg.get("tool_calls") or []]
    if not calls and msg.get("content"):
        calls = parse_tool_calls(msg["content"])
    return (calls, f"LLM planı ({model})") if calls else None


def plan_llm(q: str):
    return plan_openai(q) or plan_gguf(q)

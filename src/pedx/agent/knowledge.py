"""Knowledge the agent reasons over: the atlas (17+ areas, scored candidate sites), validation results and the
literature map (docs/20). Everything is read from files the pipeline produced — the agent invents nothing.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import numpy as np

ROOT = Path(__file__).resolve().parents[3]

# which literature backs which tool (theme id, reference numbers in docs/20) — shown with every answer
TOOL_CITATIONS = {
    "find_sites": [("T11", [1, 9]), ("T7", [1, 2, 9]), ("T1", [5, 6])],
    "assess_site": [("T6", [1, 3, 4]), ("T2", [5, 10]), ("T10", [1, 4])],
    "inverse": [("T6", [9]), ("T7", [12, 13]), ("T2", [9, 4])],
    "compare_areas": [("T8", [1, 2]), ("T12", [1, 4]), ("T3", [4])],
    "validation": [("T8", [4, 5, 6, 12]), ("T11", [1])],
    "applicability": [("T8", [6, 7])],
    "literature": [],
    "list_areas": [("T1", [5, 11])],
}


@lru_cache(maxsize=1)
def atlas() -> dict:
    return json.loads((ROOT / "web" / "data" / "atlas.json").read_text())


@lru_cache(maxsize=1)
def validation() -> dict:
    v = ROOT / "data" / "validation"
    out = {}
    for name in ("ped_validation_summary", "maup_validation", "data_scaling", "feature_analysis"):
        p = v / f"{name}.json"
        if p.exists():
            d = json.loads(p.read_text())
            if name == "feature_analysis":
                d = {"schemes": d["schemes"], "family_summary": d["family_summary"]}
            if name == "ped_validation_summary":
                d = {k: v for k, v in d.items() if k != "provenance"}
            out[name] = d
    return out


@lru_cache(maxsize=1)
def literature() -> Dict[str, dict]:
    """Parse docs/20 into {T1: {title, trend, refs: [..]}}."""
    text = (ROOT / "docs" / "20_q1_literatur_ve_trendler.md").read_text()
    themes = {}
    for block in re.split(r"\n## (?=T\d+ ·)", text)[1:]:
        head, _, body = block.partition("\n")
        tid, _, title = head.partition(" · ")
        trend = re.search(r"\*\*Trend:\*\*(.*?)(?:\n\*\*pedx|\n\n\d)", body, flags=re.S)
        refs = [re.sub(r"\s+", " ", r).strip() for r in re.findall(r"^\d+\.\s+(.*)$", body, flags=re.M)]
        themes[tid.strip()] = {"title": title.strip(), "trend": re.sub(r"\s+", " ", trend.group(1)).strip() if trend else "", "refs": refs}
    return themes


def cite(tool: str) -> List[str]:
    lit = literature()
    out = []
    for tid, idx in TOOL_CITATIONS.get(tool, []):
        refs = lit.get(tid, {}).get("refs", [])
        out += [f"[{tid}] {refs[i - 1]}" for i in idx if 0 < i <= len(refs)]
    return out


def score_logit(z: List[float]) -> float:
    M = atlas()["model"]
    return M["intercept"] + float(np.dot(M["coef"], z))


def sig100(x: float) -> float:
    return 100.0 / (1.0 + np.exp(-x))

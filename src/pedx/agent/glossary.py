"""Domain glossary for pedx-agent planners (K-058): place names → area, phrases → ranking objective.

Two parts, one source for the rule planner, the LLM planners and the web port:

* **Place gazetteer** (``gazetteer.json``) — built from data by ``scripts/build_gazetteer.py``: Overture divisions
  (ODbL) and Wikidata place items (CC0) inside each area window, assigned to the nearest pilot site. A gazetteer
  name only matches a capitalised word in the question ("Moda civarında"), so common words that are also
  neighbourhood names ("kültür", "güven", "site") do not trigger it. Hand-written aliases (city names) win.
* **Objective vocabulary** (``OBJECTIVE_TERMS``) — written by hand from the report metric definitions
  (pedx.report.REPORT) in Turkish and English; documented in docs/21 §E.

For the LLM the glossary is *retrieved*, not dumped: only the entries that match the question are appended to the
user message (retrieval-augmented planning; Lewis et al. 2020), so the 8k context is not spent on 6 000 names.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

__all__ = ["OBJECTIVE_TERMS", "BALANCE_TERMS", "gazetteer", "match_places", "match_objective", "wants_balance", "hint_text"]

# metric key → phrases (normalised: lower case, ascii, no punctuation). Longest phrase wins across metrics.
OBJECTIVE_TERMS: Dict[str, Tuple[str, ...]] = {
    "construction_share": ("kentsel donusum", "donusum", "insaat", "yenileme", "construction", "redevelopment", "regeneration", "urban renewal"),
    "social_infra_per_1000": ("sosyal altyapi", "sosyal donati", "sosyal", "social infrastructure"),
    "culture_ha": ("kultur", "miras", "tarih", "culture", "cultural", "heritage"),
    "green_share": ("yesil", "parklar", "park alan", "parks", "green", "greenest"),
    "third_places_per_1000": ("ucuncu mekan", "kafe", "kahvehane", "kahve", "cay bahcesi", "third place", "cafe", "coffee"),
    "education_per_1000": ("egitim", "okul", "universite", "education", "school"),
    "health_per_1000": ("saglik", "hastane", "health", "hospital", "clinic"),
    "finance_ha": ("finans", "banka", "emlak", "finance", "financial", "bank"),
    "plaza_m2_per_1000": ("meydan", "yaya", "plaza", "square", "pedestrian"),
    "elderly_share": ("yasli", "kirilgan", "elderly", "older", "oldest population", "ageing"),
    "children_share": ("cocuk", "children", "kids"),
    "transit_per_km2": ("toplu tasima", "metro", "otobus", "ulasim", "transit", "public transport", "buses", "bus stop", "tram"),
    "night_ha": ("gece", "nightlife", "night"),
    "env_lst_anomaly_c": ("isi adasi", "kentsel isi", "sicaklik", "en sicak", "sicak", "heat island", "hottest"),
}
# "can cover its own electricity" = balance ≥ 1 is a filter on the PED score ranking, not a separate objective
BALANCE_TERMS = ("kendi elektrigini", "kendi enerjisini", "kendine yeten", "oz yeterli", "dengede", "pozitif enerji",
                 "self sufficient", "selfsufficient", "energy positive", "net positive", "cover its own")

_DATA = Path(__file__).with_name("gazetteer.json")


def _norm(s: str) -> str:
    from .tools import _norm as n

    return n(s)


def _has(t: str, phrase: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase), t) is not None


@lru_cache(maxsize=1)
def gazetteer() -> Dict[str, dict]:
    return json.loads(_DATA.read_text())["names"] if _DATA.exists() else {}


def _words(q: str) -> List[Tuple[str, bool]]:
    """(normalised word, starts with a capital letter) for every word; apostrophes split Turkish suffixes."""
    return [(_norm(w), w[:1].isupper()) for w in re.findall(r"[^\W\d_]+", q)]


def match_places(q: str) -> List[Tuple[str, str, str]]:
    """[(matched name, area key, source)] in question order. Curated aliases first, then the data gazetteer."""
    from .tools import ALIASES

    words, out, used = _words(q), [], set()
    G = gazetteer()
    max_len = 4
    i = 0
    while i < len(words):
        hit = None
        for L in range(max_len, 0, -1):
            span = words[i:i + L]
            if len(span) < L:
                continue
            name = " ".join(w for w, _ in span)
            if name in ALIASES:
                hit = (L, name, ALIASES[name], "alias")
                break
            if name in G and span[0][1]:  # gazetteer names only on a capitalised word
                hit = (L, name, G[name]["area"], f"gazetteer: {G[name]['name']}")
                break
        if hit:
            L, name, key, src = hit
            if key not in used:
                out.append((name, key, src))
                used.add(key)
            i += L
        else:
            i += 1
    return out


def match_objective(q: str) -> Optional[Tuple[str, str]]:
    """(metric key, matched phrase) for the longest objective phrase in the question, or None.
    Place names are removed first ("Caferağa" must not read as "cafe")."""
    place = {w for n, _, _ in match_places(q) for w in n.split()}
    t = " ".join(w for w, _ in _words(q) if w not in place)
    best = None
    for key, phrases in OBJECTIVE_TERMS.items():
        for p in phrases:
            if _has(t, p) and (best is None or len(p) > len(best[1])):
                best = (key, p)
    return best


def wants_balance(q: str) -> bool:
    t = " ".join(w for w, _ in _words(q))  # hyphens split like the web port: "energy-positive" → "energy positive"
    return any(_has(t, p) for p in BALANCE_TERMS)


def hint_text(q: str) -> str:
    """Glossary lines for the LLM user message (only what matches this question)."""
    lines = [f'"{n}" → area {k}' + (f" ({s})" if s != "alias" else "") for n, k, s in match_places(q)]
    obj = match_objective(q)
    if obj:
        lines.append(f'"{obj[1]}" → find_sites objective {obj[0]}')
    if wants_balance(q):
        lines.append('"self-sufficient / covers its own electricity" → find_sites objective score with require_balance=true')
    return ("\n\nGlossary matches (use these keys):\n" + "\n".join("- " + x for x in lines)) if lines else ""

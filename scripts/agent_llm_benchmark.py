"""Planner comparison (K-055): rule-based vs local Qwen3 (GGUF, llama.cpp, CPU) on two question sets.

* dev set      — the 40 questions written together with the rule planner (scripts/agent_benchmark.INTENTS)
* held-out set — 30 questions written BEFORE any planner was run on them and never used to tune the rule planner:
                 paraphrases, English, indirect wording ("Moda", "kahvehane", "metro ve otobüs").
Metrics: first-tool, area, argument (objective / target) and exact-plan accuracy; seconds per question.

    PEDX_QWEN_MODELS="data/models/Qwen3-4B-Q4_K_M.gguf,data/models/Qwen3-8B-Q4_K_M.gguf" python scripts/agent_llm_benchmark.py
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

from pedx.agent.core import _sanitize, plan_rule, repair  # noqa: E402
from pedx.agent.llm import plan_gguf  # noqa: E402

# (question, gold first tool, gold area (str or set of accepted keys or None), gold objective (str) or target (float) or None)
HELDOUT = [
    ("Which neighbourhoods in Istanbul look most like real positive energy districts? Give me 4.", "find_sites", "istanbul", "score"),
    ("Kadıköy'de güneş enerjisiyle kendi elektriğini karşılayabilecek yerleri göster", "find_sites", "kadikoy", "score"),
    ("Lyon ile Viyana arasında PED potansiyeli bakımından fark var mı?", "compare_areas", "confluence", None),
    ("Bu modelin sonuçlarına neden güveneyim?", "validation", None, None),
    ("How reliable is the PED score?", "validation", None, None),
    ("Helsinki'deki en yaşlı nüfusa sahip mahalleleri listele", "find_sites", "kalasatama", "elderly_share"),
    ("Moda civarında kahvehane ve kafe kültürü güçlü noktalar", "find_sites", "caferaa_istanbul", "third_places_per_1000"),
    ("Find areas in Bilbao with the most construction activity", "find_sites", "zorrotzaurre", "construction_share"),
    ("İstanbul'un en sıcak, ısı adası etkisi en güçlü sahaları", "find_sites", "istanbul", "env_lst_anomaly_c"),
    ("Which cities can you analyse?", "list_areas", None, None),
    ("Hangi şehirler sistemde var?", "list_areas", None, None),
    ("Kadıköy'deki en iyi adayın puanını 85'e çıkarmak için hangi müdahaleler gerekir?", "find_sites", "kadikoy", 85.0),
    ("Uppsala için en uygun 2 aday sahayı bul ve gerekçelendir", "find_sites", "rosendal", "score"),
    ("Give me the three greenest candidate sites in Vienna", "find_sites", "seestadt_aspern", "green_share"),
    ("Nantes ve Amsterdam'ı kıyasla", "compare_areas", "le_de_nantes", None),
    ("Dasimetrik haritalama hakkında kaynak var mı?", "literature", None, None),
    ("Reference class forecasting literature", "literature", None, None),
    ("İstanbul'da metro ve otobüs erişimi en iyi 5 yer", "find_sites", "istanbul", "transit_per_km2"),
    ("Turku'da sağlık hizmetine yakın aday sahalar", "find_sites", "linnakaupunki", "health_per_1000"),
    ("Oulu'da çocuk nüfusu yüksek alanlar", "find_sites", "kaukovainio", "children_share"),
    ("Dijon'da finansal hizmetlerin yoğunlaştığı yerler", "find_sites", "fontaine_d_ouche", "finance_ha"),
    ("Espoo'da PED için en uygun saha hangisi, neden?", "find_sites", {"kera", "leppvaara"}, "score"),
    ("Lund'da hedef 75 puan için ne yapmalıyız?", "find_sites", "brunnshg", 75.0),
    ("İstanbul'da eğitim kurumlarının yoğun olduğu sahalar", "find_sites", "istanbul", "education_per_1000"),
    ("Vitoria-Gasteiz'de meydan ve yaya alanı bol yerler", "find_sites", "coronacin", "plaza_m2_per_1000"),
    ("Show me Groningen's best PED candidates", "find_sites", "paddepoel", "score"),
    ("Kadıköy ile İstanbul geneli arasında fark nedir?", "compare_areas", "kadikoy", None),
    ("PED skoru nasıl doğrulandı, AUC değeri nedir?", "validation", None, None),
    ("Explainable AI references", "literature", None, None),
    ("Caferağa'da gece hayatı canlı sahalar", "find_sites", "caferaa_istanbul", "night_ha"),
]


# Held-out set 2 (K-058): written after the glossary was built but BEFORE any planner was run on it. Set 1 was used
# to diagnose the glossary's four target errors, so it is no longer independent. Mostly neighbourhood names (not
# city names) and paraphrased objectives. Gold area = the most specific pilot window containing the place; a set
# where two pilot windows are equally right (a Kadıköy neighbourhood is in both the Caferağa and Kadıköy windows).
KDK = {"caferaa_istanbul", "kadikoy"}
HELDOUT2 = [
    ("Bahariye çevresinde PED'e en uygun 3 saha", "find_sites", KDK, "score"),
    ("Kalamış'ta yeşil alanı bol yerler", "find_sites", KDK, "green_share"),
    ("Beşiktaş ve çevresinde gece hayatının canlı olduğu yerler", "find_sites", "istanbul", "night_ha"),
    ("Üsküdar'da yaşlıların yoğun yaşadığı sahalar", "find_sites", "istanbul", "elderly_share"),
    ("Fenerbahçe'de güneşten kendi enerjisini üretip yetebilecek sahalar", "find_sites", KDK, "score"),
    ("Where in Kallio are the hottest blocks?", "find_sites", "kalasatama", "env_lst_anomaly_c"),
    ("Vallila'da toplu taşıma erişimi iyi sahalar", "find_sites", "kalasatama", "transit_per_km2"),
    ("Croix-Rousse'ta kültürel miras yoğun yerler", "find_sites", "confluence", "culture_ha"),
    ("Best PED candidates near Part-Dieu", "find_sites", "confluence", "score"),
    ("Deusto'da yeniden yapılanma ve inşaat faaliyeti olan alanlar", "find_sites", "zorrotzaurre", "construction_share"),
    ("Tapiola'da en iyi 4 PED adayı", "find_sites", {"kera", "leppvaara"}, "score"),
    ("Amsterdam-Noord'da çocuklu ailelerin yaşadığı sahalar", "find_sites", "buiksloterham", "children_share"),
    ("Lysaker'de hangi sahalar PED olabilir, neden?", "find_sites", "fornebu", "score"),
    ("Tuira'da sağlık tesislerine yakın yerler", "find_sites", "kaukovainio", "health_per_1000"),
    ("Selwerd'deki okul ve eğitim yoğunluğu yüksek sahalar", "find_sites", "paddepoel", "education_per_1000"),
    ("Donaustadt'ta kafe ve buluşma mekânı zengin yerler", "find_sites", "seestadt_aspern", "third_places_per_1000"),
    ("Klostergården çevresinde PED için en uygun saha", "find_sites", "brunnshg", "score"),
    ("Lakua'da meydanı ve yaya alanı olan sahalar", "find_sites", "coronacin", "plaza_m2_per_1000"),
    ("Luthagen'de en iyi adayın puanını 80'e çıkarmak için ne lazım?", "find_sites", "rosendal", 80.0),
    ("Chantenay'da bankacılık ve finans yoğun yerler", "find_sites", "le_de_nantes", "finance_ha"),
    ("Port Arthur'da sosyal donatısı güçlü sahalar", "find_sites", "linnakaupunki", "social_infra_per_1000"),
    ("Moda ile Lyon'u kıyasla", "compare_areas", KDK, None),
    ("Göztepe ile Kalasatama arasındaki fark", "compare_areas", KDK, None),
    ("Rasimpaşa'da hedef 65 puan için ne yapılmalı?", "find_sites", KDK, 65.0),
    ("Kadıköy'de ısınan, sıcaklık anomalisi yüksek sahalar", "find_sites", "kadikoy", "env_lst_anomaly_c"),
    ("Show sites in Kadıköy that could be energy-positive on their own", "find_sites", "kadikoy", "score"),
    ("Hangi bölgeleri inceleyebiliyorsun?", "list_areas", None, None),
    ("Bu skorun doğruluğu nasıl test edildi?", "validation", None, None),
    ("Kentsel ısı adası literatürü", "literature", None, None),
    ("İstanbul'da kentsel yenileme potansiyeli yüksek sahalar", "find_sites", "istanbul", "construction_share"),
]


def score(plan, tool, area, extra):
    if not plan:
        return dict(tool_ok=False, area_ok=False, arg_ok=False, all_ok=False)
    t0, a0 = plan[0]
    got_area = a0.get("area") or a0.get("a")
    area_ok = area is None or (got_area in area if isinstance(area, set) else got_area == area)
    if isinstance(extra, str):
        arg_ok = a0.get("objective", "score") == extra
    elif isinstance(extra, float):
        inv = [a for n, a in plan if n == "inverse"]
        arg_ok = bool(inv) and abs(float(inv[0].get("target", -1)) - extra) < 1e-9
    else:
        arg_ok = True
    return dict(tool_ok=t0 == tool, area_ok=area_ok, arg_ok=arg_ok, all_ok=t0 == tool and area_ok and arg_ok)


def evaluate(name, planner, items):
    rows = []
    for q, tool, area, extra in items:
        t = time.time()
        try:
            plan = planner(q)
        except Exception as exc:  # noqa: BLE001
            plan = []
            print("ERR", name, q, exc, flush=True)
        dt = time.time() - t
        rows.append({"planner": name, "q": q, "seconds": dt, "plan": json.dumps(plan, ensure_ascii=False), **score(plan, tool, area, extra)})
        print(name, f"{dt:5.1f}s", "OK " if rows[-1]["all_ok"] else "XX ", q[:60], "→", json.dumps(plan, ensure_ascii=False)[:140], flush=True)
    return rows


if __name__ == "__main__":
    models = [m for m in os.environ.get("PEDX_QWEN_MODELS", "").split(",") if m]
    planners = {"kural tabanlı": lambda q: plan_rule(q)[0]}
    sets = {"geliştirme (40)": INTENTS, "bağımsız (30)": HELDOUT, "bağımsız-2 (30)": HELDOUT2}
    rows = []
    for sname, items in sets.items():
        for r in evaluate("kural tabanlı", planners["kural tabanlı"], items):
            rows.append({**r, "set": sname})
    for m in models:  # one LLM call per question; raw and repaired plans scored from the same output
        name = Path(m).stem
        cache = {}

        def raw(q, path=m, cache=cache):
            cache[q] = _sanitize((plan_gguf(q, path) or ([], ""))[0])
            return cache[q]
        for sname, items in sets.items():
            for r in evaluate(name, raw, items):
                rows.append({**r, "set": sname})
            for r in evaluate(name + " + plan onarımı", lambda q, cache=cache: repair(cache.get(q, [])), items):
                rows.append({**r, "set": sname})
    R = pd.DataFrame(rows)
    S = R.groupby(["planner", "set"]).agg(tool=("tool_ok", "mean"), area=("area_ok", "mean"), arg=("arg_ok", "mean"),
                                          exact=("all_ok", "mean"), sec_per_q=("seconds", "mean"), n=("q", "size")).reset_index()
    print(S.round(3).to_string())
    out = ROOT / "data" / "validation" / "agent_llm_benchmark.json"
    out.write_text(json.dumps({"summary": S.round(4).to_dict(orient="records"), "per_question": R.to_dict(orient="records"),
                               "hardware": f"{os.cpu_count()} CPU cores, no GPU (llama.cpp, Q4_K_M)"}, ensure_ascii=False, indent=1))

"""pedx-agent benchmark (K-054): can the agent find real PEDs it has never seen, and does it understand the questions?

A. Site-finding task, leave-one-city-out. For each of the 16 real-PED cities the criteria weights, directions and
   calibration are re-derived WITHOUT that city (pedx.score.evidence_weights), every inhabited candidate site of the
   city (k = 2 disc around each H3 r9 centre) is scored, and the agent's top-5 recommendations are compared with the
   real PED site:
     * percentile of the real site's candidate in the agent's ranking (1 = ranked first)
     * hit@10 %: real site among the top 10 % of candidates
     * distance [km] from the real site to the nearest of the agent's top 5, vs. 5 random inhabited candidates
       (2 000 draws; fixed seed) — the gain over chance (Hand 2006: compare with a naive baseline).
B. Intent task: 40 Turkish planning questions with a gold tool / area / objective; planner accuracy.
"""

import json
import re
from pathlib import Path

import h3
import numpy as np
import pandas as pd

from pedx.agent.core import plan_rule
from pedx.score import _z, candidate_discs, city_stats, evidence_weights, PEDScore

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "data" / "validation"
GRID = ROOT / "data" / "cache" / "citygrid"
SEED = 20261108


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower().encode("ascii", "ignore").decode()).strip("_")


def site_finding():
    FA = json.loads((VAL / "feature_analysis.json").read_text())
    feats = FA["clean_features"]
    sites = json.loads((VAL / "ped_sites.json").read_text())
    D = pd.read_csv(VAL / "ped_features.csv")
    key_of = {s["site"]: slug(s["site"]) for s in sites}
    D["key"] = D["site"].map(key_of)
    D = D[D["site"].isin(D.loc[D.role == "case"].dropna(subset=["energy_balance"])["site"])].reset_index(drop=True)
    grids, stats, cands = {}, {}, {}
    for s in sites:
        k = slug(s["site"])
        F = pd.read_csv(GRID / f"{k}_r10.csv", index_col=0)
        allc = candidate_discs(F)
        stats[k] = city_stats(allc, feats)
        inhabited = F.index[(F["vul_pop_hrsl"] >= 20) & (F["ov_bld_footprint_m2"] > 0)]
        centres = [h3.cell_to_center_child(p, 10) for p in sorted({h3.cell_to_parent(x, 9) for x in inhabited})]
        C = candidate_discs(F, centres=centres)
        C = C[(C["vul_pop_hrsl"] >= 100) & (C["ov_bld_footprint_m2"] > 0) & np.isfinite(C["log_energy_balance"])]
        cands[k] = C
    Z = np.vstack([_z(dict(zip(feats, r[:-1])), stats[r[-1]], feats) for r in D[feats + ["key"]].itertuples(index=False)])
    y = (D["role"] == "case").astype(int).to_numpy()
    keys = D["key"].to_numpy()
    rng = np.random.default_rng(SEED)
    rows = []
    for s in sites:
        k = slug(s["site"])
        train = [x for x in np.unique(keys) if x != k]
        tr = keys != k
        w, dr, _, _ = evidence_weights(Z[tr], y[tr], keys[tr], train)
        m = PEDScore.from_weights(feats, w, dr, Z[tr], y[tr])
        C = cands[k]
        Zc = np.vstack([_z(r.to_dict(), stats[k], feats) for _, r in C.iterrows()])
        sc = Zc @ m.coef + m.intercept
        order = np.argsort(-sc)
        site_r9 = h3.cell_to_parent(h3.latlng_to_cell(s["lat"], s["lon"], 10), 9)
        cent = [h3.cell_to_parent(c, 9) for c in C.index]
        if site_r9 not in cent:
            continue
        j = cent.index(site_r9)
        rank = int(np.where(order == j)[0][0])
        pct = 1 - rank / len(order)
        ll = np.array([h3.cell_to_latlng(c) for c in C.index])
        dist = lambda idx: min(h3.great_circle_distance((s["lat"], s["lon"]), tuple(ll[i]), unit="km") for i in idx)  # noqa: E731
        d_agent = dist(order[:5])
        d_rand = float(np.mean([dist(rng.choice(len(order), 5, replace=False)) for _ in range(2000)]))
        rows.append({"site": s["site"], "candidates": len(order), "rank": rank + 1, "percentile": pct, "hit10": pct >= 0.9,
                     "dist_top5_km": d_agent, "dist_random5_km": d_rand})
        print(rows[-1], flush=True)
    R = pd.DataFrame(rows)
    return R, {"n_cities": int(len(R)), "mean_percentile": float(R["percentile"].mean()), "hit10": int(R["hit10"].sum()),
               "median_dist_agent_km": float(R["dist_top5_km"].median()), "median_dist_random_km": float(R["dist_random5_km"].median()),
               "cities_agent_closer": int((R["dist_top5_km"] < R["dist_random5_km"]).sum())}


INTENTS = [  # question → (tool of first step, area, objective or target)
    ("İstanbul'da PED için en uygun 5 sahayı bul", "find_sites", "istanbul", "score"),
    ("Kadıköy'de en iyi 3 aday saha hangileri?", "find_sites", "kadikoy", "score"),
    ("Caferağa'da PED'e en uygun yerleri öner", "find_sites", "caferaa_istanbul", "score"),
    ("Lyon Confluence'ta en uygun sahalar", "find_sites", "confluence", "score"),
    ("Viyana'da PED adayı sahaları bul", "find_sites", "seestadt_aspern", "score"),
    ("Helsinki'de en iyi 10 saha", "find_sites", "kalasatama", "score"),
    ("Amsterdam için aday sahalar", "find_sites", "buiksloterham", "score"),
    ("Kadıköy'de kentsel dönüşüm için aday sahalar", "find_sites", "kadikoy", "construction_share"),
    ("İstanbul'da sosyal altyapısı güçlü sahaları bul", "find_sites", "istanbul", "social_infra_per_1000"),
    ("Kadıköy'de kültür ve miras açısından öne çıkan yerler", "find_sites", "kadikoy", "culture_ha"),
    ("İstanbul'da yeşil alanı yüksek sahalar", "find_sites", "istanbul", "green_share"),
    ("Caferağa'da üçüncü mekân, kafe yoğun sahalar", "find_sites", "caferaa_istanbul", "third_places_per_1000"),
    ("İstanbul'da toplu taşıma erişimi yüksek sahalar", "find_sites", "istanbul", "transit_per_km2"),
    ("Kadıköy'de yaşlı nüfusu kırılgan sahalar", "find_sites", "kadikoy", "elderly_share"),
    ("İstanbul'da ısı adası en yüksek sahalar", "find_sites", "istanbul", "env_lst_anomaly_c"),
    ("Kadıköy'de eğitim tesisi yoğun sahalar", "find_sites", "kadikoy", "education_per_1000"),
    ("İstanbul'da finans ve emlak yoğun sahalar", "find_sites", "istanbul", "finance_ha"),
    ("Kadıköy'de meydan ve yaya alanı olan sahalar", "find_sites", "kadikoy", "plaza_m2_per_1000"),
    ("Kadıköy'de dengede olan pozitif sahalar", "find_sites", "kadikoy", "score"),
    ("İstanbul'da gece yaşamı yoğun yerler", "find_sites", "istanbul", "night_ha"),
    ("Kadıköy ile Lyon'u karşılaştır", "compare_areas", "kadikoy", None),
    ("İstanbul ve Helsinki karşılaştır", "compare_areas", "istanbul", None),
    ("Caferağa ile Kadıköy arasındaki fark", "compare_areas", "caferaa_istanbul", None),
    ("Bilbao ile Nantes'ı kıyasla", "compare_areas", "zorrotzaurre", None),
    ("Model ne kadar güvenilir?", "validation", None, None),
    ("Doğrulama sonuçları nedir, AUC kaç?", "validation", None, None),
    ("Bu sonuçlar gerçek PED'lerle doğrulandı mı?", "validation", None, None),
    ("MAUP konusunda literatür kaynakları", "literature", None, None),
    ("Açıklanabilir yapay zekâ için kaynak öner", "literature", None, None),
    ("Otonom CBS makale önerisi", "literature", None, None),
    ("Hangi alanları analiz edebilirsin?", "list_areas", None, None),
    ("Alanları listele", "list_areas", None, None),
    ("İstanbul'da en iyi sahayı açıkla", "find_sites", "istanbul", "score"),
    ("Kadıköy'de en uygun sahayı bul, neden uygun?", "find_sites", "kadikoy", "score"),
    ("Caferağa'da puanı 70'e çıkarmak için ne gerekir?", "find_sites", "caferaa_istanbul", 70.0),
    ("Kadıköy'de en iyi saha için hedef 80 puan", "find_sites", "kadikoy", 80.0),
    ("İstanbul'da 60 puana nasıl ulaşırım?", "find_sites", "istanbul", 60.0),
    ("Uppsala'da aday sahaları analiz et", "find_sites", "rosendal", "score"),
    ("Oslo Fornebu'da en uygun 2 saha", "find_sites", "fornebu", "score"),
    ("Dijon'da sağlık tesisi yoğun sahalar", "find_sites", "fontaine_d_ouche", "health_per_1000"),
]


def intents():
    rows = []
    for q, tool, area, extra in INTENTS:
        plan, _ = plan_rule(q)
        t0, a0 = plan[0][0], plan[0][1]
        got_area = a0.get("area") or a0.get("a")
        ok_extra = True
        if isinstance(extra, str):
            ok_extra = a0.get("objective") == extra
        elif isinstance(extra, float):
            inv = [a for n, a in plan if n == "inverse"]
            ok_extra = bool(inv) and abs(inv[0]["target"] - extra) < 1e-9
        rows.append({"q": q, "tool_ok": t0 == tool, "area_ok": area is None or got_area == area, "arg_ok": ok_extra,
                     "all_ok": t0 == tool and (area is None or got_area == area) and ok_extra, "got": [n for n, _ in plan], "got_args": a0})
    R = pd.DataFrame(rows)
    return R, {"n": int(len(R)), "tool_acc": float(R["tool_ok"].mean()), "area_acc": float(R["area_ok"].mean()),
               "arg_acc": float(R["arg_ok"].mean()), "exact": float(R["all_ok"].mean())}


if __name__ == "__main__":
    RA, SA = site_finding()
    RI, SI = intents()
    print(json.dumps(SA, indent=1), json.dumps(SI, indent=1))
    print(RI[~RI["all_ok"]][["q", "got", "got_args"]].to_string())
    (VAL / "agent_benchmark.json").write_text(json.dumps({"site_finding": {"summary": SA, "per_city": RA.round(4).to_dict(orient="records")},
                                                          "intent": {"summary": SI, "per_question": RI.drop(columns=["got_args"]).to_dict(orient="records")}},
                                                         ensure_ascii=False, indent=1, default=str))

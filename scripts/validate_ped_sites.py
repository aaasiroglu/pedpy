"""External validation against REAL Positive Energy Districts (case–control, K-041).

Question: does the on-demand model rank real PED / lighthouse sites above ordinary urban
locations of the same city? Design (fixed before seeing results, no tuning on the outcome):

* cases    — real PED and Smart-City lighthouse districts (JPI Urban Europe PED Booklet 2020;
             Gollner et al. 2020; SCC1 lighthouse projects). Site geometry = OSM object found by
             name (data/validation/ped_sites.json records the OSM id → reproducible).
* controls — N random populated points 1.5–8 km from the site, same city, same code path
             (same population source, climate, country demand) → within-city comparison.
* metric   — percentile of the site's annual balance among its controls; pooled mean percentile
             = stratified AUC (Mann–Whitney); one-sided sign test against 0.5.
* strata   — development type: brownfield/new vs. retrofit of existing stock. A high score of a
             brownfield site measured on its pre-development state partly reflects few residents,
             which is reported, not hidden.

    python scripts/validate_ped_sites.py [n_controls]
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from pedx.service import assess_point

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "data" / "validation"
DEV = {  # development type and programme (sources in docs/17_ped_dogrulama.md)
    "Buiksloterham": ("brownfield", "ATELIER (H2020 SCC)"), "Zorrotzaurre": ("brownfield", "ATELIER (H2020 SCC)"),
    "Kera": ("brownfield", "SPARCS (H2020 SCC)"), "Leppävaara": ("existing", "SPARCS (H2020 SCC)"),
    "Brainport Smart District": ("new", "PED Booklet 2020"), "Fornebu": ("brownfield", "syn.ikia (H2020)"),
    "Kaukovainio": ("existing", "MAKING-CITY (H2020 SCC)"), "Paddepoel": ("existing", "MAKING-CITY (H2020 SCC)"),
    "Fontaine d'Ouche": ("existing", "RESPONSE (H2020 SCC)"), "Linnakaupunki": ("brownfield", "RESPONSE (H2020 SCC)"),
    "Confluence": ("brownfield", "Lyon Smart Community / Smarter Together"), "Seestadt Aspern": ("new", "PED Booklet 2020"),
    "Brunnshög": ("new", "PED Booklet 2020"), "Annelinn": ("existing", "SmartEnCity (H2020 SCC)"),
    "Coronación": ("existing", "SmartEnCity (H2020 SCC)"), "Rosendal": ("new", "syn.ikia (H2020)"),
    "Kalasatama": ("brownfield", "mySMARTLife (H2020 SCC)"), "Île de Nantes": ("brownfield", "mySMARTLife (H2020 SCC)"),
    "Bergedorf": ("existing", "mySMARTLife (H2020 SCC)"), "Sluppen": ("brownfield", "+CityxChange (H2020 SCC)"),
}


def controls(lat, lon, n, rng):
    pts = []
    for _ in range(n):
        r = math.sqrt(rng.uniform(1.5**2, 8.0**2)) * 1000
        a = rng.uniform(0, 2 * math.pi)
        pts.append((lat + r * math.cos(a) / 111_320, lon + r * math.sin(a) / (111_320 * math.cos(math.radians(lat)))))
    return pts


def run(lat, lon):
    r = assess_point(lat, lon, k=2, with_resilience=False, with_dem=False)
    s = r["summary"]
    e = s.get("explanation", {})
    return {"balance": e.get("balance"), "population": s.get("population"), "footprint_m2": s.get("footprint_m2"),
            "pop_source": r["provenance"].get("population", {}).get("source"), "failures": ";".join(r["failures"])}


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    sites = json.loads((VAL / "ped_sites.json").read_text())
    rng = np.random.default_rng(20261108)  # fixed seed → reproducible control sample
    rows = []
    for s in sites:
        dev, prog = DEV.get(s["site"], ("?", "?"))
        case = run(s["lat"], s["lon"])
        ctl = [run(la, lo) for la, lo in controls(s["lat"], s["lon"], n, rng)]
        cb = np.array([c["balance"] for c in ctl if c["balance"] is not None and (c["population"] or 0) > 50], dtype=float)
        pct = float((cb < case["balance"]).mean() + 0.5 * (cb == case["balance"]).mean()) if case["balance"] is not None and cb.size else None
        rows.append({"site": s["site"], "city": s["city"], "osm": s["osm"], "development": dev, "programme": prog,
                     "case_balance": case["balance"], "case_population": case["population"], "pop_source": case["pop_source"],
                     "controls_n": int(cb.size), "controls_median_balance": float(np.median(cb)) if cb.size else None,
                     "percentile": pct, "failures": case["failures"]})
        print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(VAL / "ped_validation.csv", index=False)
    ok = df.dropna(subset=["percentile"])
    from math import comb

    k_hi = int((ok["percentile"] > 0.5).sum())
    m = len(ok)
    p_sign = sum(comb(m, i) for i in range(k_hi, m + 1)) / 2**m if m else None
    summ = {"n_sites": m, "auc_pooled": float(ok["percentile"].mean()) if m else None, "sites_above_median": k_hi,
            "sign_test_p_one_sided": p_sign, "by_development": ok.groupby("development")["percentile"].agg(["mean", "count"]).round(3).to_dict(),
            "n_controls_per_site": n, "seed": 20261108}
    (VAL / "ped_validation_summary.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))

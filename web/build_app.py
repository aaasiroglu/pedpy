"""Assemble web/pedx_app.html: a single self-contained page (presentation + thesis outline + MVP).

Inputs: web/data/{cells,boundary,buildings,streets}.geojson, web/data/summary.json (built by
scripts/build_features.py), web/vendor/leaflet.css, web/app_template.html, web/app_main.js.
Run:  python web/build_app.py
"""

from __future__ import annotations

import json
from pathlib import Path

import h3

W = Path(__file__).resolve().parent
D = W / "data"
ROOT = W.parent

SOURCES = [
    ["Mahalle sınırı, binalar, POI, yaya ağı, duraklar", "OpenStreetMap (Overpass API)", "ODbL 1.0", "G1"],
    ["Nüfus", "JRC GHS-POP R2023A, E2020, 3″ (Schiavina vd., 2023)", "CC BY 4.0", "G1"],
    ["Konut elektriği (ulusal, 2023)", "UN Statistics Division, Energy Statistics Database (UNdata)", "atıfla serbest", "G1"],
    ["Ülke nüfusu, kişi başı talep", "UN WPP ve Ember, Our World in Data", "CC BY 4.0", "G1"],
    ["Saatlik PV üretimi (2023)", "EU JRC PVGIS 5.3 (SARAH-3, ERA5)", "AB yeniden kullanım", "G1"],
    ["Morfometri", "momepy (Fleischmann, 2019)", "BSD-3", "G1"],
    ["İstanbul kişi başı net tüketim", "TEDAŞ 2023 Sektör Raporu, Tablo 7", "yalnızca doğrulama", "G2"],
    ["Caferağa nüfusu (2020)", "Kadıköy Belediyesi / TÜİK ADNKS", "yalnızca doğrulama", "G2"],
]

REFS = [
    "Alpagut, B., Lopez Romo, A., Hernández, P., Tabanoğlu, O., & Hermoso Martinez, N. (2021). A GIS-based multicriteria assessment for identification of positive energy districts boundary in cities. <i>Energies, 14</i>(22), 7517. https://doi.org/10.3390/en14227517",
    "Boeing, G. (2017). OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks. <i>Computers, Environment and Urban Systems, 65</i>, 126–139. https://doi.org/10.1016/j.compenvurbsys.2017.05.004",
    "Brozovsky, J., Gustavsen, A., & Gaitani, N. (2021). Zero emission neighbourhoods and positive energy districts – A state-of-the-art review. <i>Sustainable Cities and Society, 72</i>, 103013. https://doi.org/10.1016/j.scs.2021.103013",
    "Bruck, A., Díaz Ruano, S., & Auer, H. (2022). One piece of the puzzle towards 100 positive energy districts (PEDs) across Europe by 2025: An open-source approach to unveil favourable locations of PV-based PEDs from a techno-economic perspective. <i>Energy, 254</i>, 124152.",
    "Demirel, H., Koçyiğit, A., Alpagut, B., & Muhcu, D. (2025). Evaluating the solar energy potential for positive energy districts (PED) through advanced 3D geographic information system (GIS) analysis. <i>Open Research Europe, 5</i>, 81.",
    "Diakoulaki, D., Mavrotas, G., & Papayannakis, L. (1995). Determining objective weights in multiple criteria problems: The CRITIC method. <i>Computers &amp; Operations Research, 22</i>(7), 763–770. https://doi.org/10.1016/0305-0548(94)00059-H",
    "Fleischmann, M. (2019). momepy: Urban morphology measuring toolkit. <i>Journal of Open Source Software, 4</i>(43), 1807.",
    "Flyvbjerg, B. (2014). What you should know about megaprojects and why: An overview. <i>Project Management Journal, 45</i>(2), 6–19. https://doi.org/10.1002/pmj.21409",
    "Gagnon, P., Margolis, R., Melius, J., Phillips, C., &amp; Elmore, R. (2016). <i>Rooftop solar photovoltaic technical potential in the United States: A detailed assessment</i> (NREL/TP-6A20-65298). National Renewable Energy Laboratory.",
    "Hersbach, H., et al. (2020). The ERA5 global reanalysis. <i>Quarterly Journal of the Royal Meteorological Society, 146</i>, 1999–2049. https://doi.org/10.1002/qj.3803",
    "Krangsås, S. G., Steemers, K., Konstantinou, T., et al. (2021). Positive energy districts: Identifying challenges and interdependencies. <i>Sustainability, 13</i>, 10551.",
    "Labreuche, C., &amp; Fossier, S. (2018). Explaining multi-criteria decision aiding models with an extended Shapley value. <i>Proceedings of IJCAI 2018</i>.",
    "Lundberg, S. M., &amp; Lee, S.-I. (2017). A unified approach to interpreting model predictions. <i>Advances in Neural Information Processing Systems, 30</i>, 4765–4774.",
    "Luthander, R., Widén, J., Nilsson, D., &amp; Palm, J. (2015). Photovoltaic self-consumption in buildings: A review. <i>Applied Energy, 142</i>, 80–94. https://doi.org/10.1016/j.apenergy.2014.12.028",
    "Salom, J., Marszal, A. J., Widén, J., Candanedo, J., &amp; Lindberg, K. B. (2014). Analysis of load match and grid interaction indicators in net zero energy buildings with simulated and monitored data. <i>Applied Energy, 136</i>, 119–131. https://doi.org/10.1016/j.apenergy.2014.09.018",
    "Schiavina, M., Freire, S., Carioli, A., &amp; MacManus, K. (2023). <i>GHS-POP R2023A – GHS population grid multitemporal (1975–2030)</i>. European Commission, Joint Research Centre.",
    "Schneider, S., Zelger, T., Sengl, D., &amp; Baptista, J. (2023). A quantitative positive energy district definition with contextual targets. <i>Buildings, 13</i>(5), 1210.",
    "Stević, Ž., Pamučar, D., Puška, A., &amp; Chatterjee, P. (2020). Sustainable supplier selection in healthcare industries using a new MCDM method: MARCOS. <i>Computers &amp; Industrial Engineering, 140</i>, 106231. https://doi.org/10.1016/j.cie.2019.106231",
    "Wachter, S., Mittelstadt, B., &amp; Russell, C. (2018). Counterfactual explanations without opening the black box: Automated decisions and the GDPR. <i>Harvard Journal of Law &amp; Technology, 31</i>(2).",
    "Xie, A., &amp; Zou, L. (2025). A comparative study on the performance of MARCOS method and weighted sum method. <i>IAENG International Journal of Applied Mathematics, 55</i>(4), 911–917.",
    "Zhang, X., Penaka, S. R., Giriraj, S., Sánchez, M. N., Civiero, P., &amp; Vandevyvere, H. (2021). Characterizing positive energy district (PED) through a preliminary review of 60 existing projects in Europe. <i>Buildings, 11</i>(8), 318.",
]


def _round_geo(gj: dict, nd: int = 5) -> dict:
    def r(c):
        return [r(x) for x in c] if isinstance(c[0], list) else [round(c[0], nd), round(c[1], nd)]
    for f in gj["features"]:
        f["geometry"]["coordinates"] = r(f["geometry"]["coordinates"])
    return gj


def _agent_kb() -> dict:
    """Literature map (docs/20) and tool → citation map for the in-browser pedx-agent."""
    import sys

    sys.path.insert(0, str(ROOT / "src"))
    from pedx.agent.knowledge import TOOL_CITATIONS, literature

    bench = ROOT / "data" / "validation" / "agent_benchmark.json"
    llm = ROOT / "data" / "validation" / "agent_llm_benchmark.json"
    return {"themes": literature(), "tool_citations": {k: [[t, i] for t, i in v] for k, v in TOOL_CITATIONS.items()},
            "benchmark": json.loads(bench.read_text()) if bench.exists() else None,
            "llm_benchmark": (json.loads(llm.read_text())["summary"] if llm.exists() else None)}


def _ped_validation() -> dict:
    """Real-PED case–control results (scripts/validate_ped_sites.py), if they have been run."""
    v = ROOT / "data" / "validation"
    if not (v / "ped_validation.csv").exists():
        return {}
    import pandas as pd

    rows = pd.read_csv(v / "ped_validation.csv").replace({float("nan"): None}).to_dict(orient="records")
    sc = v / "data_scaling.json"
    return {"rows": rows, "summary": json.loads((v / "ped_validation_summary.json").read_text()),
            "scaling": json.loads(sc.read_text()) if sc.exists() else None}


def main() -> None:
    cells = json.loads((D / "cells.geojson").read_text())
    summary = json.loads((D / "summary.json").read_text())
    p = summary["provenance"]
    y = p["inputs"]["pv_yield_kwh_per_kwp_2023"]
    pr = p["params"]
    agg, ids = {}, []
    for f in cells["features"]:
        q = f["properties"]
        c = q["cell"]
        ids.append(c)
        fp = q.get("built_footprint_m2") or 0.0
        agg[c] = {
            "pop": q.get("demo_population") or 0.0, "dem": q.get("energy_demand_res_kwh") or 0.0, "fp": fp,
            "pv": fp * pr["roof_utilization"]["value"] * pr["module_efficiency"]["value"] * y,
            "pvl": fp * pr["roof_utilization"]["low"] * pr["module_efficiency"]["low"] * y,
            "pvh": fp * pr["roof_utilization"]["high"] * pr["module_efficiency"]["high"] * y,
            "ha": h3.cell_area(c, unit="m^2") / 1e4,
        }
    present = set(ids)
    adj = {c: sorted(n for n in h3.grid_disk(c, 1) if n != c and n in present) for c in ids}
    district = {"n": len(ids), "fp": sum(a["fp"] for a in agg.values()), "pop": sum(a["pop"] for a in agg.values())}
    bundle = {
        "features_analysis": json.loads((ROOT / "data" / "validation" / "feature_analysis.json").read_text())
        if (ROOT / "data" / "validation" / "feature_analysis.json").exists() else None,
        "agent_kb": _agent_kb(),
        "scales": json.loads((D / "scales.json").read_text()) if (D / "scales.json").exists() else None,
        "atlas": json.loads((D / "atlas.json").read_text()) if (D / "atlas.json").exists() else None,
        "ped_validation": _ped_validation(), "cells": cells, "summary": summary, "agg": agg, "adj": adj, "district": district,
        "boundary": json.loads((D / "boundary.geojson").read_text()),
        "buildings": _round_geo(json.loads((D / "buildings.geojson").read_text())),
        "streets": json.loads((D / "streets.geojson").read_text()),
        "sources": SOURCES, "refs": REFS,
    }
    html = (W / "app_template.html").read_text()
    html = html.replace("/*LEAFLET_CSS*/", (W / "vendor" / "leaflet.css").read_text())
    html = html.replace("/*DATA*/", "window.PEDX=" + json.dumps(bundle, ensure_ascii=False, separators=(",", ":")) + ";")
    html = html.replace("/*APP_JS*/", (W / "app_main.js").read_text())
    out = W / "pedx_app.html"
    out.write_text(html)
    print(f"{out} ({out.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()

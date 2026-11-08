"""Build the data of the web demo (web/data/) for Caferağa from GLOBAL OPEN data only.

Inputs (G1, globally available, open licence) – see docs/11_veri_kaynaklari.md:
  OSM boundary (relation 9441032) and buildings      ODbL 1.0
  JRC GHS-POP R2023A, epoch 2020, 3 arc-second       CC BY 4.0
  UNSD Energy Statistics (UNdata): households, 2023  free reuse with citation
  UN WPP population via Our World in Data, 2023      CC BY 4.0
  EU JRC PVGIS 5.3 hourly PV per kWp, 2023            EU reuse policy (free, attribution)

Local data (G2) are used ONLY in the validation block.
No synthetic or placeholder value enters any output; the hourly demand shape
is a documented data gap, so hourly indicators are not shown in this version.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from pedx.export import buildings_geojson, cells_geojson, rings_geojson, write_json
from pedx.ingest import parse_buildings
from pedx.ingest.global_data import boundary_rings, parse_pvgis_pv, parse_undata_table, points_in_polygon, population_by_cell
from pedx.spatial import assign_cells

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SRC = RAW / "sources"
OUT = ROOT / "web" / "data"
RES = 10

# Parameters: value, low, high, source (all cited; low/high = documented ranges for sensitivity)
PARAMS = {
    "roof_utilization": {
        "value": 0.26, "low": 0.26, "high": 0.50,
        "source": "Gagnon et al. (2016) NREL/TP-6A20-65298: 26% of small-building roof area suitable (US); "
                  "upper bound to be replaced by Demirel et al. (2025) 3D analysis (G2)",
    },
    "module_efficiency": {
        "value": 0.20, "low": 0.17, "high": 0.25,
        "source": "Fraunhofer ISE Photovoltaics Report: commercial Si module efficiency rose from ~17% to just under 25% over the last decade",
    },
}


def main() -> None:
    # --- boundary
    b = boundary_rings(json.loads((RAW / "caferaga_boundary_overpass.json").read_text()))
    lats = [p[0] for r in b["outer"] for p in r]
    lons = [p[1] for r in b["outer"] for p in r]
    bbox = (min(lats), min(lons), max(lats), max(lons))

    # --- buildings inside boundary (centroid test)
    bpay = json.loads((RAW / "caferaga_buildings_boundary_bbox.json").read_text())
    bld = parse_buildings(bpay)
    bld = bld[points_in_polygon(bld["lat"], bld["lon"], b["outer"], b["inner"])].copy()
    bld["cell"] = assign_cells(bld["lat"], bld["lon"], RES)

    # --- population per cell (GHS-POP 2020)
    tif = SRC / "ghs_pop" / "GHS_POP_E2020_GLOBE_R2023A_4326_3ss_V1_0_R5_C21.tif"
    pop = population_by_cell(tif, bbox, RES, mask=b)

    # --- national residential electricity per capita (UNSD households / UN population), 2023
    hh = parse_undata_table((SRC / "undata_tr_1231.html").read_text(encoding="utf-8", errors="ignore"))
    hh_2023_kwh = float(hh.loc[hh["year"] == 2023, "value"].iloc[0]) * 1e6  # million kWh → kWh
    owid = pd.read_csv(SRC / "owid-energy-data.csv", usecols=["country", "year", "population", "electricity_demand_per_capita"])
    tr = owid[(owid["country"] == "Turkey")].set_index("year")
    pop_tr_2023 = float(tr.loc[2023, "population"])
    res_kwh_per_cap = hh_2023_kwh / pop_tr_2023

    # --- PV yield (PVGIS 2023, kWh per kWp)
    pv = parse_pvgis_pv(json.loads((SRC / "pvgis_pv_caferaga_2023.json").read_text()))
    yield_kwh_kwp = float(pv["pv_kwh_per_kwp"].sum())
    monthly_pv = pv["pv_kwh_per_kwp"].groupby(pv.index.month).sum()

    # --- cell table
    g = bld.groupby("cell").agg(n_buildings=("osm_id", "size"), footprint_m2=("footprint_area_m2", "sum"),
                                levels_known=("levels", lambda s: float(s.notna().mean())))
    cells = g.join(pop, how="outer").fillna({"n_buildings": 0, "footprint_m2": 0.0, "population": 0.0})
    u, eta = PARAMS["roof_utilization"], PARAMS["module_efficiency"]
    cells["demand_res_kwh"] = cells["population"] * res_kwh_per_cap
    for tag, uf, ef in (("", u["value"], eta["value"]), ("_low", u["low"], eta["low"]), ("_high", u["high"], eta["high"])):
        kwp = cells["footprint_m2"] * uf * ef
        cells[f"pv_kwh{tag}"] = kwp * yield_kwh_kwp
        cells[f"balance{tag}"] = np.where(cells["demand_res_kwh"] > 0, cells[f"pv_kwh{tag}"] / cells["demand_res_kwh"], np.nan)
    cells["pv_kwp"] = cells["footprint_m2"] * u["value"] * eta["value"]
    # inverse (physical): footprint share that must carry PV for an annual balance of 1
    denom = cells["footprint_m2"] * eta["value"] * yield_kwh_kwp
    cells["roof_share_needed"] = np.where(denom > 0, cells["demand_res_kwh"] / denom, np.nan)
    from pedx.spatial import cell_area_m2

    cells["cell_area_ha"] = [cell_area_m2(c) / 1e4 for c in cells.index]
    cells["pop_density_per_ha"] = cells["population"] / cells["cell_area_ha"]
    cells = cells[(cells["n_buildings"] > 0) | (cells["population"] > 0)]

    total = {
        "n_buildings": int(len(bld)),
        "n_cells": int(len(cells)),
        "population_ghs_2020": float(cells["population"].sum()),
        "demand_res_kwh": float(cells["demand_res_kwh"].sum()),
        "pv_kwh": float(cells["pv_kwh"].sum()),
        "pv_kwh_low": float(cells["pv_kwh_low"].sum()),
        "pv_kwh_high": float(cells["pv_kwh_high"].sum()),
        "footprint_m2": float(cells["footprint_m2"].sum()),
        "share_levels_known": float(bld["levels"].notna().mean()),
        "share_height_missing": float((bld["height_source"] == "missing").mean()),
        "share_start_year_known": float(bld["start_year"].notna().mean()),
    }
    total["balance"] = total["pv_kwh"] / total["demand_res_kwh"]
    total["balance_low"] = total["pv_kwh_low"] / total["demand_res_kwh"]
    total["balance_high"] = total["pv_kwh_high"] / total["demand_res_kwh"]

    validation = [
        {
            "item": "Caferağa nüfusu",
            "global_open_G1": round(total["population_ghs_2020"]),
            "local_G2": 21421,
            "unit": "kişi (2020)",
            "g1_source": "JRC GHS-POP R2023A E2020, OSM sınırı içinde toplam",
            "g2_source": "Kadıköy Belediyesi 'Anlat Kadıköy' (TÜİK ADNKS 2020); İBB/TÜİK resmî tablosuyla teyit edilecek",
            "rel_diff": round(total["population_ghs_2020"] / 21421 - 1, 4),
        },
        {
            "item": "Kişi başı toplam elektrik tüketimi",
            "global_open_G1": round(float(tr.loc[2022, "electricity_demand_per_capita"])),
            "local_G2": 2678,
            "unit": "kWh/kişi (2022)",
            "g1_source": "Ember via OWID (Türkiye ulusal ortalaması)",
            "g2_source": "TEDAŞ 2023 Sektör Raporu, Tablo 7 (İstanbul, net tüketim)",
            "rel_diff": round(float(tr.loc[2022, "electricity_demand_per_capita"]) / 2678 - 1, 4),
            "note": "Ulusal ortalama sanayi yükünü içerir; İstanbul'un net kişi başı tüketimi daha düşük. Konut payı için G2 verisi (EPİAŞ/İBB) bekleniyor.",
        },
    ]

    provenance = {
        "generated": pd.Timestamp.now("UTC").isoformat(),
        "h3_resolution": RES,
        "boundary": {"osm_id": b["osm_id"], "name": b["tags"].get("name"), "wikidata": b["tags"].get("wikidata")},
        "inputs": {
            "residential_kwh_per_capita_2023": res_kwh_per_cap,
            "households_electricity_TR_2023_kwh": hh_2023_kwh,
            "population_TR_2023": pop_tr_2023,
            "pv_yield_kwh_per_kwp_2023": yield_kwh_kwp,
            "pvgis_mounting": json.loads((SRC / "pvgis_pv_caferaga_2023.json").read_text())["inputs"]["mounting_system"],
        },
        "params": PARAMS,
        "gaps": [
            "Saatlik konut talep şekli: küresel, açık lisanslı kaynak henüz seçilmedi → SSR, tepe rahatlaması, Shapley ve batarya bu sürümde gösterilmiyor.",
            "Hizmet sektörü talebi (UNSD 'commercial and public services') henüz mekâna dağıtılmadı → denge yalnızca konut elektriği içindir.",
            "Gölgeleme ve çatı geometrisi modellenmedi → çatı kullanım katsayısı aralığıyla (0,26–0,50) temsil ediliyor.",
        ],
    }

    OUT.mkdir(parents=True, exist_ok=True)
    write_json(cells_geojson(cells.round(4)), OUT / "cells.geojson")
    write_json(rings_geojson(b["outer"], b["inner"], {"name": b["tags"].get("name"), "osm_id": b["osm_id"]}), OUT / "boundary.geojson")
    write_json(buildings_geojson(bpay, bld["osm_id"]), OUT / "buildings.geojson")
    write_json({"total": total, "validation": validation, "provenance": provenance,
                "monthly_pv_kwh_per_kwp": {int(k): float(v) for k, v in monthly_pv.items()}}, OUT / "summary.json")
    # single JS bundle so the page also works from file:// and as a self-contained artifact
    bundle = {name: json.loads((OUT / f"{name}.{ext}").read_text()) for name, ext in
              (("cells", "geojson"), ("boundary", "geojson"), ("buildings", "geojson"), ("summary", "json"))}
    (OUT / "demo_data.js").write_text("window.PEDX_DATA=" + json.dumps(bundle, ensure_ascii=False, separators=(",", ":")) + ";")
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in total.items()}, ensure_ascii=False, indent=1))
    print("residential kWh/cap", round(res_kwh_per_cap, 1), "PV kWh/kWp", round(yield_kwh_kwp, 1))
    print(json.dumps(validation, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

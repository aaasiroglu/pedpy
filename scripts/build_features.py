"""Build the H3 hex feature store and web-demo data for Caferağa from GLOBAL OPEN data only.

Pipeline (docs/13_sistem_mimarisi.md):
  L0 raw inputs (data/raw, fetched by scripts/fetch_data.py)
  L1 parsing + provenance
  L2 hex feature store (energy, built, demography, poi) — registered features only
  L3 physics engine (annual balance, inverse roof share) + exact XAI decomposition
  L4 export → web/data (GeoJSON + JS bundle) and data/processed (CSV + catalogue)

Local datasets are used ONLY in the validation block (G2). No synthetic values.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from pedx._stats import spearman_rho
from pedx.export import buildings_geojson, cells_geojson, rings_geojson, write_json
from pedx.features import FAMILIES, building_features, catalog_frame, demography_features, poi_features, validate_columns
from pedx.ingest import parse_buildings, parse_pois
from pedx.ingest.global_data import boundary_rings, parse_pvgis_pv, parse_undata_table, points_in_polygon, population_by_cell
from pedx.spatial import assign_cells, cell_area_m2

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SRC = RAW / "sources"
OUT_WEB = ROOT / "web" / "data"
OUT_PROC = ROOT / "data" / "processed"
RES = 10

from pedx.params import PARAMS  # noqa: E402  (shared with pedx.service)


def main() -> None:
    # ---------------- L1: parse inputs
    b = boundary_rings(json.loads((RAW / "caferaga_boundary_overpass.json").read_text()))
    lats = [p[0] for r in b["outer"] for p in r]
    lons = [p[1] for r in b["outer"] for p in r]
    bbox = (min(lats), min(lons), max(lats), max(lons))

    bpay = json.loads((RAW / "caferaga_buildings_boundary_bbox.json").read_text())
    bld = parse_buildings(bpay)
    bld = bld[points_in_polygon(bld["lat"], bld["lon"], b["outer"], b["inner"])].copy()
    bld["cell"] = assign_cells(bld["lat"], bld["lon"], RES)

    pois = parse_pois(json.loads((RAW / "caferaga_pois_full.json").read_text()))
    pois = pois[points_in_polygon(pois["lat"], pois["lon"], b["outer"], b["inner"])].copy()
    pois["cell"] = assign_cells(pois["lat"], pois["lon"], RES)

    pop = population_by_cell(SRC / "ghs_pop" / "GHS_POP_E2020_GLOBE_R2023A_4326_3ss_V1_0_R5_C21.tif", bbox, RES, mask=b)

    hh = parse_undata_table((SRC / "undata_tr_1231.html").read_text(encoding="utf-8", errors="ignore"))
    hh_2023_kwh = float(hh.loc[hh["year"] == 2023, "value"].iloc[0]) * 1e6
    owid = pd.read_csv(SRC / "owid-energy-data.csv", usecols=["country", "year", "population", "electricity_demand_per_capita"])
    tr = owid[owid["country"] == "Turkey"].set_index("year")
    res_kwh_per_cap = hh_2023_kwh / float(tr.loc[2023, "population"])

    pvj = json.loads((SRC / "pvgis_pv_caferaga_2023.json").read_text())
    pv = parse_pvgis_pv(pvj)
    yield_kwh_kwp = float(pv["pv_kwh_per_kwp"].sum())

    # ---------------- L2: hex feature store
    cells = sorted(set(bld["cell"]) | set(pop.index) | set(pois["cell"]))
    area_ha = pd.Series({c: cell_area_m2(c) / 1e4 for c in cells})
    F_built = building_features(bld, area_ha)
    F_demo = demography_features(pop, area_ha, F_built["built_footprint_m2"])
    F_poi = poi_features(pois, area_ha, pop)
    from pedx.features.morphology import buildings_gdf, morphology_features

    F_morph = morphology_features(buildings_gdf(bpay, bld["osm_id"]), bld.set_index("osm_id")["cell"])
    from pedx.features import poi_family
    from pedx.features.accessibility import accessibility_features, walk_graph

    G = walk_graph(json.loads((RAW / "caferaga_walk_network.json").read_text()))
    allpois = parse_pois(json.loads((RAW / "caferaga_pois_full.json").read_text()))  # POIs of the boundary bbox; cells near the bbox edge undercount (known edge effect → buffered POI fetch, S2)
    allpois["family"] = [poi_family(k, v) for k, v in zip(allpois["key"], allpois["value"])]
    stops = pd.DataFrame([{"lat": e["lat"], "lon": e["lon"]} for e in json.loads((RAW / "caferaga_transit_stops.json").read_text())["elements"] if "lat" in e])
    F_acc = accessibility_features(G, cells, allpois, stops, area_ha)
    from pedx.features.accessibility import network_complexity_features

    F_net = network_complexity_features(json.loads((RAW / "caferaga_walk_network.json").read_text()), G, cells, area_ha)
    eo_csv = SRC / "eo_h3r10_caferaga.csv"  # produced by scripts/fetch_eo.py (Landsat, Sentinel-2, Copernicus DEM)
    F_eo = pd.read_csv(eo_csv, index_col=0) if eo_csv.exists() else pd.DataFrame(index=pd.Index(cells, name="cell"))
    # ---- data lake: GHSL built-up rasters → H3 (zonal engine)
    from pedx.datalake import ghsl_tile_path, zonal_h3

    gh = SRC / "ghsl"
    z = lambda prod, stat: zonal_h3(ghsl_tile_path(prod, 40.986, 29.028, gh), bbox, RES, stat, mask=b)  # noqa: E731
    F_ghsl = pd.DataFrame({
        "ghsl_built_surface_m2": z("built_s_2020", "sum"), "ghsl_nres_surface_m2": z("built_s_nres_2020", "sum"),
        "ghsl_volume_m3": z("built_v_2020", "sum"), "ghsl_nres_volume_m3": z("built_v_nres_2020", "sum"),
        "ghsl_agbh_m": z("built_h_agbh_2018", "mean"),
    })
    F_ghsl["ghsl_nres_share"] = F_ghsl["ghsl_nres_surface_m2"] / F_ghsl["ghsl_built_surface_m2"].where(F_ghsl["ghsl_built_surface_m2"] > 0)
    F_ghsl["ghsl_mean_height_m"] = F_ghsl["ghsl_volume_m3"] / F_ghsl["ghsl_built_surface_m2"].where(F_ghsl["ghsl_built_surface_m2"] > 0)
    # ---- vulnerability & resilience (K-039): HRSL age groups, GHSL built-up epochs, OSM facilities
    from pedx.datalake.vulnerability import parse_resilience, resilience_features, vulnerability_features

    hrsl_csv = SRC / "hrsl_h3r10_caferaga.csv"  # produced by scripts/fetch_layers.py
    epochs = {y: z(f"built_s_{y}", "sum") for y in (1975, 1990, 2000) if ghsl_tile_path(f"built_s_{y}", 40.986, 29.028, gh).exists()}
    epochs[2020] = F_ghsl["ghsl_built_surface_m2"]
    if hrsl_csv.exists():
        H = pd.read_csv(hrsl_csv, index_col=0)
        F_vul = vulnerability_features(H, F_eo.get("env_lst_anomaly_c"), epochs, population=F_demo["demo_population"])
    else:
        F_vul = pd.DataFrame(index=pd.Index(cells, name="cell"))
    res_json = RAW / "caferaga_resilience.json"
    F_res = resilience_features(cells, parse_resilience(json.loads(res_json.read_text()))) if res_json.exists() else pd.DataFrame(index=pd.Index(cells, name="cell"))
    ov_csv = SRC / "overture_h3r10_caferaga.csv"  # produced by scripts/fetch_layers.py
    F_ov = pd.read_csv(ov_csv, index_col=0) if ov_csv.exists() else pd.DataFrame(index=pd.Index(cells, name="cell"))
    F = pd.DataFrame(index=pd.Index(cells, name="cell")).join([F_built, F_demo, F_poi, F_morph, F_acc, F_ghsl, F_net, F_eo, F_vul, F_res, F_ov])
    F["osm_vs_ghsl_surface"] = F["built_footprint_m2"] / F["ghsl_built_surface_m2"].where(F["ghsl_built_surface_m2"] > 0)
    for c in ("built_n_buildings", "built_footprint_m2", "demo_population", "poi_total") + tuple(x for x in F if x.startswith("poi_n_")):
        F[c] = F[c].fillna(0.0)

    # ---------------- L3: physics engine (annual) + exact XAI decomposition
    F = F.copy()  # de-fragment after the many joins
    u, eta = PARAMS["roof_utilization"], PARAMS["module_efficiency"]
    F["energy_demand_res_kwh"] = F["demo_population"] * res_kwh_per_cap
    for tag, uf, ef in (("", u["value"], eta["value"]), ("_low", u["low"], eta["low"]), ("_high", u["high"], eta["high"])):
        pvk = F["built_footprint_m2"] * uf * ef * yield_kwh_kwp
        if tag == "":
            F["energy_pv_kwh"] = pvk
        F[f"energy_balance{tag}"] = np.where(F["energy_demand_res_kwh"] > 0, pvk / F["energy_demand_res_kwh"], np.nan)
    F["energy_pv_kwp"] = F["built_footprint_m2"] * u["value"] * eta["value"]
    denom = F["built_footprint_m2"] * eta["value"] * yield_kwh_kwp
    F["energy_roof_share_needed"] = np.where(denom > 0, F["energy_demand_res_kwh"] / denom, np.nan)
    # ln B = ln(A u eta Y) - ln(P d)  →  Δln B_i = Δln A_i − Δln P_i  (exact, vs. district geometric mean)
    ok = (F["built_footprint_m2"] > 0) & (F["demo_population"] > 0)
    lnA, lnP = np.log(F.loc[ok, "built_footprint_m2"]), np.log(F.loc[ok, "demo_population"])
    F["xai_logbal_built"] = (lnA - lnA.mean()).reindex(F.index)
    F["xai_logbal_population"] = (-(lnP - lnP.mean())).reindex(F.index)
    F = F[(F["built_n_buildings"] > 0) | (F["demo_population"] > 0)]
    # ---- hex signature embedding over all G1 input features (not energy outputs)
    from pedx.features.embedding import pca_embedding

    emb_cols = [c for c in F.columns if not c.startswith(("energy_", "xai_"))]
    E, emb_info = pca_embedding(F, emb_cols, k=5)
    F = F.join(E)
    validate_columns(F.columns)

    # ---------------- exploratory associations (NOT causal): Spearman of every feature with the balance
    target = "energy_balance"
    # definitional components of the target are excluded (balance ∝ footprint / population)
    definitional = {"demo_m2_footprint_per_capita", "built_footprint_m2", "demo_population", "demo_density_per_ha", "osm_vs_ghsl_surface",
                    # re-based on demo_population (count = GHS-POP × HRSL share) → carry the target's denominator
                    "vul_elderly60_n", "vul_children0_5_n", "vul_youth15_24_n", "vul_women15_49_n", "vul_dependent_n",
                    "vul_heat_exposed_vulnerable", "ov_bld_footprint_m2"}
    assoc = []
    for c in F.columns:
        if c.startswith(("energy_", "xai_", "emb_")) or c in definitional:  # emb_* contain target components
            continue
        m = F[[c, target]].dropna()
        if len(m) >= 10 and m[c].nunique() > 2:
            assoc.append({"feature": c, "rho": round(spearman_rho(m[c], m[target]), 3), "n": int(len(m))})
    assoc = sorted(assoc, key=lambda r: -abs(r["rho"]))

    # ---------------- totals, validation (G2), provenance
    T = {
        "n_buildings": int(len(bld)), "n_cells": int(len(F)), "n_pois": int(len(pois)),
        "population_ghs_2020": float(F["demo_population"].sum()),
        "demand_res_kwh": float(F["energy_demand_res_kwh"].sum()), "pv_kwh": float(F["energy_pv_kwh"].sum()),
        "footprint_m2": float(F["built_footprint_m2"].sum()),
        "share_levels_known": float(bld["levels"].notna().mean()),
        "share_start_year_known": float(bld["start_year"].notna().mean()),
        "ghsl_built_surface_m2": float(F["ghsl_built_surface_m2"].sum()), "ghsl_volume_m3": float(F["ghsl_volume_m3"].sum()),
        "ghsl_nres_surface_m2": float(F["ghsl_nres_surface_m2"].sum()),
        "elderly60": float(F.get("vul_elderly60_n", pd.Series(dtype=float)).sum()),
        "children0_5": float(F.get("vul_children0_5_n", pd.Series(dtype=float)).sum()),
        "youth15_24": float(F.get("vul_youth15_24_n", pd.Series(dtype=float)).sum()),
        "overture_places": float(F.get("ov_places_n", pd.Series(dtype=float)).sum()),
    }
    T["balance"] = T["pv_kwh"] / T["demand_res_kwh"]
    pvsum = {tag: float((F["built_footprint_m2"] * uf * ef * yield_kwh_kwp).sum()) for tag, uf, ef in
             (("low", u["low"], eta["low"]), ("high", u["high"], eta["high"]))}
    T["balance_low"], T["balance_high"] = pvsum["low"] / T["demand_res_kwh"], pvsum["high"] / T["demand_res_kwh"]
    pc_2022 = float(tr.loc[2022, "electricity_demand_per_capita"])
    validation = [
        {"item": "Caferağa nüfusu", "global_open_G1": round(T["population_ghs_2020"]), "local_G2": 21421, "unit": "kişi (2020)",
         "g1_source": "JRC GHS-POP R2023A E2020, OSM sınırı içinde toplam",
         "g2_source": "Kadıköy Belediyesi 'Anlat Kadıköy' (TÜİK ADNKS 2020); İBB/TÜİK resmî tablosuyla teyit edilecek",
         "rel_diff": round(T["population_ghs_2020"] / 21421 - 1, 4)},
        {"item": "Caferağa nüfusu (Meta HRSL)", "global_open_G1": round(float(F["vul_pop_hrsl"].sum())) if "vul_pop_hrsl" in F else None,
         "local_G2": 21421, "unit": "kişi", "g1_source": "Meta Data for Good HRSL general (1″), OSM sınırı içinde toplam",
         "g2_source": "TÜİK ADNKS 2020 (Kadıköy Belediyesi aktarımı)",
         "rel_diff": round(float(F["vul_pop_hrsl"].sum()) / 21421 - 1, 4) if "vul_pop_hrsl" in F else None,
         "note": "HRSL nüfusu yerleşim pikseline dağıtır; ticari çekirdekte (çarşı) konutsuz binalara da nüfus düşer → nüfus tabanı GHS-POP."},
        {"item": "Kişi başı toplam elektrik tüketimi", "global_open_G1": round(pc_2022), "local_G2": 2678, "unit": "kWh/kişi (2022)",
         "g1_source": "Ember via OWID (Türkiye ulusal ortalaması)", "g2_source": "TEDAŞ 2023 Sektör Raporu, Tablo 7 (İstanbul, net tüketim)",
         "rel_diff": round(pc_2022 / 2678 - 1, 4),
         "note": "Ulusal ortalama sanayi yükünü içerir; konut payı için G2 verisi (EPİAŞ/İBB) bekleniyor."},
    ]
    cat = catalog_frame().reset_index()
    catalog = {"families": FAMILIES, "features": cat.to_dict(orient="records")}
    provenance = {
        "generated": pd.Timestamp.now("UTC").isoformat(), "h3_resolution": RES,
        "boundary": {"osm_id": b["osm_id"], "name": b["tags"].get("name"), "wikidata": b["tags"].get("wikidata")},
        "inputs": {"residential_kwh_per_capita_2023": res_kwh_per_cap, "households_electricity_TR_2023_kwh": hh_2023_kwh,
                   "population_TR_2023": float(tr.loc[2023, "population"]), "pv_yield_kwh_per_kwp_2023": yield_kwh_kwp,
                   "pvgis_mounting": pvj["inputs"]["mounting_system"]},
        "params": PARAMS,
        "gaps": [
            "Saatlik konut talep şekli: küresel ve açık kaynak seçimi bekliyor → SSR, tepe rahatlaması, Shapley ve batarya bu sürümde yok.",
            "Hizmet sektörü talebi (UNSD 'commercial and public services') henüz mekâna dağıtılmadı → denge yalnızca konut elektriği içindir.",
            "Gölgeleme ve çatı geometrisi modellenmedi → çatı kullanım katsayısı aralığıyla (0,26–0,50) temsil ediliyor.",
            "Ekonomi, çevre, iklim, görüntü ve sosyal katmanlar katalogda 'planlanan' durumunda (docs/13, docs/14).",
            "Yürüme erişimi: POI'ler yalnızca mahalle sınırlayıcı kutusundan çekildi; kenar hücrelerde 800 m erişim eksik sayılıyor (S2'de tamponlu sorgu).",
            "HRSL yaş payları sayım birimi (ilçe) içinde sabittir → mahalle içi yaş farkı gösterilmez; yaşlı/çocuk sayıları GHS-POP × pay olarak verilir.",
            "OSM'de İstanbul afet toplanma alanı (emergency=assembly_point) yok → toplanma alanına uzaklık boş; İBB toplanma alanları G2 doğrulamasında.",
        ],
    }

    # ---------------- L4: export
    OUT_WEB.mkdir(parents=True, exist_ok=True)
    OUT_PROC.mkdir(parents=True, exist_ok=True)
    F.round(5).to_csv(OUT_PROC / "caferaga_h3r10_features.csv")
    cat.to_csv(OUT_PROC / "feature_catalog.csv", index=False)
    write_json(cells_geojson(F.round(5)), OUT_WEB / "cells.geojson")
    write_json(rings_geojson(b["outer"], b["inner"], {"name": b["tags"].get("name"), "osm_id": b["osm_id"]}), OUT_WEB / "boundary.geojson")
    write_json(buildings_geojson(bpay, bld["osm_id"]), OUT_WEB / "buildings.geojson")
    # ---------------- hourly demand components (K-034): Demand.ninja on ERA5 2023
    from pedx.demand import era5_to_ninja_inputs, weather_driven_demand

    dn = weather_driven_demand(era5_to_ninja_inputs(json.loads((SRC / "openmeteo_era5_caferaga_2023.json").read_text())))
    dn_monthly = dn.groupby(dn.index.month)[["heating_demand", "cooling_demand"]].sum()
    demand_status = {
        "weather_model": "Demand.ninja (Staffell, Pfenninger & Johnson 2023), ERA5 2023 via Open-Meteo",
        "monthly_heating_index": {int(k): round(float(v), 2) for k, v in dn_monthly["heating_demand"].items()},
        "monthly_cooling_index": {int(k): round(float(v), 2) for k, v in dn_monthly["cooling_demand"].items()},
        "national_load": "EPİAŞ gerçek zamanlı tüketim 2023 — hesap gerekli (scripts/fetch_epias.py); bekleniyor",
    }
    from pedx.datalake import catalog_frame as lake_catalog

    lake = lake_catalog().reset_index().to_dict(orient="records")
    eo_prov = json.loads(eo_csv.with_suffix(".json").read_text()) if eo_csv.with_suffix(".json").exists() else {}
    lay_json = SRC / "layers_caferaga.json"
    if lay_json.exists():
        eo_prov.update(json.loads(lay_json.read_text()))
    summary = {"embedding": emb_info, "eo_provenance": eo_prov, "datalake": lake, "demand_status": demand_status, "definitional_excluded": sorted(definitional), "total": T, "validation": validation, "provenance": provenance, "catalog": catalog, "associations": assoc[:20],
               "monthly_pv_kwh_per_kwp": {int(k): float(v) for k, v in pv["pv_kwh_per_kwp"].groupby(pv.index.month).sum().items()}}
    write_json(summary, OUT_WEB / "summary.json")
    print(f"cells={T['n_cells']} buildings={T['n_buildings']} pois={T['n_pois']} pop={T['population_ghs_2020']:.0f} "
          f"balance={T['balance']:.2f} ({T['balance_low']:.2f}-{T['balance_high']:.2f}) features={F.shape[1]}")
    print("top associations:", assoc[:6])


if __name__ == "__main__":
    main()

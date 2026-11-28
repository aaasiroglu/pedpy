"""Multi-scale PED accounting for Caferağa: building, urban block, H3 r11 / r10 / r9 (K-052, MAUP).

Outputs
* data/processed/multiscale_caferaga.json  — MAUP summary per scale (+ consistency check)
* web/data/scales.json                      — per-unit balance for blocks and H3 r11/r10/r9, building PV
"""

import json
from pathlib import Path

import h3
import numpy as np
import pandas as pd

from pedx.export import write_json
from pedx.ingest import parse_buildings
from pedx.ingest.global_data import boundary_rings, points_in_polygon
from pedx.params import PARAMS
from pedx.scales import aggregate, blocks_from_streets, dasymetric_buildings, maup_summary

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def main():
    S = json.loads((ROOT / "web" / "data" / "summary.json").read_text())
    d = S["provenance"]["inputs"]["residential_kwh_per_capita_2023"]
    Y = S["provenance"]["inputs"]["pv_yield_kwh_per_kwp_2023"]
    u, eta = PARAMS["roof_utilization"]["value"], PARAMS["module_efficiency"]["value"]
    b = boundary_rings(json.loads((RAW / "caferaga_boundary_overpass.json").read_text()))
    bpay = json.loads((RAW / "caferaga_buildings_boundary_bbox.json").read_text())
    bld = parse_buildings(bpay)
    bld = bld[points_in_polygon(bld["lat"], bld["lon"], b["outer"], b["inner"])].copy()
    for r in (9, 10, 11):
        bld[f"r{r}"] = [h3.latlng_to_cell(la, lo, r) for la, lo in zip(bld["lat"], bld["lon"])]
    F = pd.read_csv(ROOT / "data" / "processed" / "caferaga_h3r10_features.csv", index_col=0)
    B = dasymetric_buildings(bld, F["demo_population"], zone_col="r10")
    # urban blocks
    import geopandas as gpd

    blocks = blocks_from_streets(json.loads((RAW / "caferaga_walk_network.json").read_text()), b["outer"])
    pts = gpd.GeoDataFrame(B[["osm_id"]], geometry=gpd.points_from_xy(B["lon"], B["lat"]), crs="EPSG:4326")
    j = gpd.sjoin(pts, blocks[["block_id", "geometry"]], how="left", predicate="within")
    B["block"] = j.groupby(level=0)["block_id"].first().reindex(B.index).fillna("street_or_open")
    B["building"] = B["osm_id"]
    units = {}
    for name, col in (("Yapı adası", "block"), ("H3 r11 (~0,2 ha)", "r11"), ("H3 r10 (~1,5 ha)", "r10"), ("H3 r9 (~10 ha)", "r9")):
        g = aggregate(B, col, d, Y, u, eta)
        if col == "block":  # buildings outside closed blocks (open edges at the boundary) form one pseudo-unit, kept for the total
            g["area_ha"] = blocks.set_index("block_id")["area_m2"].reindex(g.index) / 1e4
        elif col.startswith("r"):
            g["area_ha"] = [h3.cell_area(c, unit="m^2") / 1e4 for c in g.index]
        units[name] = g
    M = maup_summary({k: (v.drop(index="street_or_open", errors="ignore") if k == "Yapı adası" else v) for k, v in units.items()})
    M.loc[M["scale"] == "Yapı adası", "total_balance"] = float(units["Yapı adası"]["pv_kwh"].sum() / units["Yapı adası"]["demand_kwh"].sum())
    # Spearman between scales on a common support: r10 cells vs mean of their r11 children / blocks (by building majority)
    r10 = units["H3 r10 (~1,5 ha)"]["balance"]
    blk_of_cell = B.groupby("r10")["block"].agg(lambda s: s.value_counts().index[0])
    blk_bal = units["Yapı adası"]["balance"].drop(index="street_or_open", errors="ignore").reindex(blk_of_cell.values)
    rho_block_r10 = float(pd.Series(blk_bal.values, index=blk_of_cell.index).corr(r10.reindex(blk_of_cell.index), method="spearman"))
    out = {"inputs": {"kwh_per_capita": d, "pv_yield": Y, "u": u, "eta": eta},
           "population_total_ghs": float(F["demo_population"].sum()), "population_allocated": float(B["pop"].sum()),
           "unallocated_population": B.attrs["unallocated_population"], "zones_without_buildings": B.attrs["zones_without_buildings"],
           "n_blocks": int(len(blocks)), "buildings_in_streets_or_open": int((B["block"] == "street_or_open").sum()),
           "spearman_block_vs_r10": rho_block_r10, "maup": M.round(4).to_dict(orient="records"),
           "note": "Bina ölçeğinde denge, nüfus taban alanına orantılı dağıtıldığı için bölge dengesine eşittir; bilgi taşımaz, raporlanmaz."}
    (ROOT / "data" / "processed" / "multiscale_caferaga.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    # web layers
    blk = blocks.merge(units["Yapı adası"][["pop", "footprint_m2", "pv_kwh", "demand_kwh", "balance"]], left_on="block_id", right_index=True, how="left")
    blk["geometry"] = blk.geometry.simplify(0.00001)
    feats = json.loads(blk[["block_id", "pop", "footprint_m2", "pv_kwh", "demand_kwh", "balance", "area_m2", "geometry"]].round(4).to_json())
    web = {"blocks": feats}
    for r in (9, 11):
        g = units[f"H3 r{r} (~0,2 ha)" if r == 11 else "H3 r9 (~10 ha)"]
        web[f"r{r}"] = [[c, round(float(v), 3) if np.isfinite(v) else None, round(float(p), 1), round(float(pv))] for c, v, p, pv in
                        zip(g.index, g["balance"], g["pop"], g["pv_kwh"])]
    web["building"] = {o: [round(float(p)), round(float(q), 2)] for o, p, q in zip(B["osm_id"], B["footprint_area_m2"] * u * eta * Y, B["pop"])}  # [PV kWh, dasymetric population]
    web["maup"] = out["maup"]
    write_json(web, ROOT / "web" / "data" / "scales.json")
    print(M.round(3).to_string())
    print({k: v for k, v in out.items() if k not in ("maup",)})


if __name__ == "__main__":
    main()

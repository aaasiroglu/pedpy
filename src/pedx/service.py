"""On-demand assessment for any point on Earth: "tıkla → hesapla" (K-040).

Hybrid architecture (docs/13 §8):
* **Prepared layer** — global datasets that are only distributed as large tiles (GHS-POP, GHSL
  built-up) are cached per tile (``make prepare``); the Overture row-group index is cached per
  release. Nothing is precomputed per hexagon, so no stale global table has to be maintained.
* **On click** — the AOI (H3 disk of ``k`` rings around the clicked cell) is assessed from sources
  that support windowed reads: Overture GeoParquet row groups, Meta HRSL COGs, Copernicus DEM COG,
  PVGIS (point API), Overpass (small buffered bbox), UNSD/OWID country statistics (cached).
  Population comes from GHS-POP when its tile is cached, otherwise from HRSL (flagged; G2 shows
  HRSL over-counts commercial cores). Every source is wrapped: a failure is reported in
  ``failures``; nothing is ever filled with synthetic values.

Physics = the batch pipeline's (pedx.params): PV = A·u·η·Y, demand = P·d, balance B = PV/demand.
Exact explanation: B ≥ 1 ⇔ A/P ≥ d/(u·η·Y) — the clicked area's roof area per person is compared
with the threshold its climate (Y) and country (d) impose.
"""

from __future__ import annotations

import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .params import PARAMS

__all__ = ["aoi_cells", "aoi_bbox", "country_of", "residential_kwh_per_capita", "pv_yield", "explain_balance", "assess_point"]

UA = {"User-Agent": "pedx-research (open-data thesis pipeline)"}
OVERPASS = "https://overpass-api.de/api/interpreter"
DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "data" / "cache"


# ---------------------------------------------------------------- geometry
def aoi_cells(lat: float, lon: float, resolution: int = 10, k: int = 3) -> List[str]:
    import h3

    return sorted(h3.grid_disk(h3.latlng_to_cell(lat, lon, resolution), k))


def aoi_bbox(cells: List[str], pad_deg: float = 0.0) -> Tuple[float, float, float, float]:
    import h3

    pts = np.array([p for c in cells for p in h3.cell_to_boundary(c)])
    return (float(pts[:, 1].min() - pad_deg), float(pts[:, 0].min() - pad_deg),
            float(pts[:, 1].max() + pad_deg), float(pts[:, 0].max() + pad_deg))


# ---------------------------------------------------------------- small cached fetchers
def _get(url: str, data: Optional[bytes] = None, timeout: int = 120, tries: int = 3) -> bytes:
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=UA), timeout=timeout) as r:  # noqa: S310
                return r.read()
        except Exception:  # noqa: BLE001
            if i == tries - 1:
                raise
            time.sleep(3 * 2**i)
    raise RuntimeError("unreachable")


def _cached_json(path: Path, make: Callable[[], dict]) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    obj = make()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj))
    return obj


def country_of(lat: float, lon: float, cache: Path = DEFAULT_CACHE) -> dict:
    """ISO codes and name of the country containing the point (OSM admin_level=2 via Overpass is_in)."""
    key = f"{round(lat, 1)}_{round(lon, 1)}"  # ~10 km cache cells; border-adjacent points may need a finer key

    def make():
        q = f'[out:json][timeout:60];is_in({lat},{lon})->.a;rel(pivot.a)["admin_level"="2"];out tags;'
        els = json.loads(_get(OVERPASS, urllib.parse.urlencode({"data": q}).encode()))["elements"]
        if not els:
            raise LookupError("no country polygon at this point")
        t = els[0]["tags"]
        return {"name": t.get("name:en", t.get("name")), "iso2": t.get("ISO3166-1:alpha2", t.get("ISO3166-1")),
                "iso3": t.get("ISO3166-1:alpha3"), "m49": t.get("ISO3166-1:numeric"), "osm_relation": els[0]["id"]}

    return _cached_json(cache / "country" / f"pt_{key}.json", make)


def _owid(cache: Path) -> pd.DataFrame:
    local = Path(__file__).resolve().parents[2] / "data" / "raw" / "sources" / "owid-energy-data.csv"
    path = local if local.exists() else cache / "owid-energy-data.csv"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_get("https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv", timeout=300))
    return pd.read_csv(path, usecols=["country", "iso_code", "year", "population", "electricity_demand_per_capita"])


def residential_kwh_per_capita(country: dict, cache: Path = DEFAULT_CACHE) -> dict:
    """Household electricity per person: UNSD households (trID 1231) / OWID population, latest common year.

    Fallback when UNSD has no series: OWID total electricity demand per capita, flagged as an
    upper bound (includes industry and services) — never silently mixed.
    """
    from .ingest.global_data import UNDATA_TRANSACTIONS, UNDATA_URL, parse_undata_table

    def make():
        ow = _owid(cache)
        ow = ow[ow["iso_code"] == country.get("iso3")].set_index("year")
        if ow.empty:
            raise LookupError(f"OWID has no series for {country.get('iso3')}")
        if country.get("m49"):
            try:
                html = _get(UNDATA_URL.format(tr=UNDATA_TRANSACTIONS["households"], cr=int(country["m49"]))).decode("utf-8", "ignore")
                un = parse_undata_table(html)
                un = un[un["year"].isin(ow.index[ow["population"].notna()])]
                if not un.empty:
                    y = int(un["year"].max())
                    v = float(un.loc[un["year"] == y, "value"].iloc[0]) * 1e6 / float(ow.loc[y, "population"])
                    return {"kwh_per_capita": v, "year": y, "basis": "households",
                            "source": "UNSD Energy Statistics (households, GWh) / OWID population"}
            except Exception:  # noqa: BLE001
                pass
        s = ow["electricity_demand_per_capita"].dropna()
        return {"kwh_per_capita": float(s.iloc[-1]), "year": int(s.index[-1]), "basis": "total_upper_bound",
                "source": "OWID (Ember) total electricity demand per capita — upper bound for residential"}

    return _cached_json(cache / "country" / f"demand_{country.get('iso3')}.json", make)


def pv_yield(lat: float, lon: float, cache: Path = DEFAULT_CACHE) -> dict:
    """Annual AC yield of 1 kWp (crystalline Si, optimal angles, building-integrated, 14 % loss), PVGIS 5.3."""
    la, lo = round(lat * 20) / 20, round(lon * 20) / 20  # 0.05° cache grid (≈ 5 km)

    def make():
        q = urllib.parse.urlencode({"lat": la, "lon": lo, "peakpower": 1, "loss": 14, "mountingplace": "building",
                                    "optimalangles": 1, "outputformat": "json"})
        d = json.loads(_get("https://re.jrc.ec.europa.eu/api/v5_3/PVcalc?" + q))
        return {"kwh_per_kwp": float(d["outputs"]["totals"]["fixed"]["E_y"]), "lat": la, "lon": lo,
                "radiation_db": d["inputs"]["meteo_data"].get("radiation_db"), "source": "EU JRC PVGIS 5.3 PVcalc"}

    return _cached_json(cache / "pvgis" / f"{la}_{lo}.json", make)


# ---------------------------------------------------------------- explanation and verdict
def explain_balance(A: float, P: float, d: float, Y: float, u: float, eta: float, u_max: float) -> dict:
    """Exact, closed-form explanation of the annual balance and of the levers that would close it."""
    if P <= 0:
        return {"balance": None, "verdict": "no_population", "text_tr": "Bu alanda yerleşik nüfus yok: konut PED'i tanımsız."}
    B = A * u * eta * Y / (P * d)
    thr = d / (u * eta * Y)  # m² footprint per person needed at the base utilisation
    out = {"balance": B, "footprint_per_capita_m2": A / P, "threshold_footprint_per_capita_m2": thr,
           "roof_utilization_needed": (P * d) / (A * eta * Y) if A > 0 else None,
           "demand_cut_needed_at_u_max": max(0.0, 1 - A * u_max * eta * Y / (P * d)),
           "log_terms": {"ln_footprint_per_capita": math.log(A / P) if A > 0 else None, "ln_u_eta_Y": math.log(u * eta * Y),
                         "ln_demand_per_capita": -math.log(d)}}
    if B >= 1:
        out["verdict"], out["text_tr"] = "ped_candidate", (
            f"Yıllık denge {B:.2f} ≥ 1: kişi başı {A / P:.1f} m² çatı tabanı, eşik {thr:.1f} m². Taban varsayımlarla PED adayı.")
    elif out["roof_utilization_needed"] is not None and out["roof_utilization_needed"] <= u_max:
        out["verdict"], out["text_tr"] = "conditional_roof", (
            f"Denge {B:.2f}. Çatı kullanımı %{100 * u:.0f} → %{100 * out['roof_utilization_needed']:.0f} çıkarılırsa yıllık denge sağlanır "
            f"(kişi başı {A / P:.1f} m², eşik {thr:.1f} m²).")
    else:
        cut = out["demand_cut_needed_at_u_max"]
        out["verdict"] = "conditional_demand" if cut <= 0.5 else "not_on_site"
        out["text_tr"] = (f"Denge {B:.2f}. Çatıların %{100 * u_max:.0f}'i kullanılsa bile talebin %{100 * cut:.0f} azaltılması gerekir"
                          + ("." if cut <= 0.5 else " → yerinde üretimle olmaz; bölge dışı yenilenebilir (sanal PED) ya da komşu fazla üreten hücrelerle küme gerekir."))
    return out


# ---------------------------------------------------------------- main entry point
def assess_point(lat: float, lon: float, k: int = 3, resolution: int = 10, cache: Path = DEFAULT_CACHE,
                 with_resilience: bool = True, with_dem: bool = True) -> dict:
    """Assess the H3 disk around (lat, lon) from global open data, fetched and computed on demand."""
    from .datalake import overture as ov
    from .datalake.raster import ghsl_tile_path
    from .spatial.h3grid import cell_area_m2

    t0 = time.time()
    cells = aoi_cells(lat, lon, resolution, k)
    bbox = aoi_bbox(cells)
    F = pd.DataFrame(index=pd.Index(cells, name="cell"))
    F["area_ha"] = [cell_area_m2(c) / 1e4 for c in cells]
    prov: Dict[str, object] = {}
    failures: Dict[str, str] = {}
    timing: Dict[str, float] = {}

    def step(name: str, fn: Callable[[], None]) -> None:
        t = time.time()
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failures[name] = f"{type(exc).__name__}: {exc}"[:300]
        timing[name] = round(time.time() - t, 2)

    ctx: Dict[str, object] = {}

    def s_country():
        ctx["country"] = country_of(lat, lon, cache)
        ctx["demand"] = residential_kwh_per_capita(ctx["country"], cache)

    def s_pv():
        ctx["pv"] = pv_yield(lat, lon, cache)

    def s_population():
        tif = ghsl_tile_path("pop_2020", lat, lon, cache / "ghsl")
        local = Path(__file__).resolve().parents[2] / "data" / "raw" / "sources" / "ghs_pop" / tif.name
        tif = local if local.exists() else tif
        if tif.exists():
            from .ingest.global_data import population_by_cell

            w, s, e, n = bbox
            F["population"] = population_by_cell(tif, (s, w, n, e), resolution).reindex(cells).fillna(0.0)
            prov["population"] = {"source": "JRC GHS-POP R2023A E2020 (cached tile)", "tile": tif.name}
        else:
            F["population"] = F["vul_pop_hrsl"]
            prov["population"] = {"source": "Meta HRSL general (GHS-POP tile not prepared → `make prepare`)",
                                  "caveat": "G2 Caferağa: HRSL +65 % vs TÜİK; commercial cores over-counted"}

    def s_hrsl():
        from .datalake.vulnerability import hrsl_h3

        H, prov["hrsl"] = hrsl_h3(bbox, resolution)
        for c in H:
            F[c] = H[c].reindex(cells).fillna(0.0)

    def s_buildings():
        df, prov["overture_buildings"] = ov.read_bbox("buildings", "building", bbox, ["id", "height", "num_floors", "sources"], cache_dir=cache)
        B = ov.building_features(df, cells, resolution)
        for c in B:
            F[c] = B[c]
        F["ov_bld_footprint_m2"] = F["ov_bld_footprint_m2"].fillna(0.0)

    def s_places():
        df, prov["overture_places"] = ov.read_bbox("places", "place", bbox, ["id", "confidence", "basic_category", "taxonomy", "sources"], cache_dir=cache)
        P = ov.place_features(df, cells, resolution)
        for c in P:
            F[c] = P[c]

    def s_dem():
        from .datalake.eo import dem_h3

        D, prov["dem"] = dem_h3(bbox, resolution)
        for c in D:
            F[c] = D[c].reindex(cells)

    def s_resilience():
        from .datalake.vulnerability import RESILIENCE_KINDS, parse_resilience, resilience_features

        w, s, e, n = aoi_bbox(cells, pad_deg=0.02)
        bb = f"{s},{w},{n},{e}"
        am = "|".join(v for (kk, v) in RESILIENCE_KINDS.values() if kk == "amenity")
        q = (f'[out:json][timeout:90];(nwr["emergency"="assembly_point"]({bb});nwr["amenity"~"^({am})$"]({bb});'
             f'nwr["healthcare"~"^(hospital|clinic)$"]({bb}););out tags center;')
        T = parse_resilience(json.loads(_get(OVERPASS, urllib.parse.urlencode({"data": q}).encode(), timeout=120)))
        R = resilience_features(cells, T)
        for c in R:
            F[c] = R[c]
        prov["osm_resilience"] = {"source": "OpenStreetMap via Overpass", "n_facilities": int(len(T)), "bbox_pad_deg": 0.02}

    from concurrent.futures import ThreadPoolExecutor

    jobs = {"country_demand": s_country, "pvgis": s_pv, "hrsl": s_hrsl, "overture_buildings": s_buildings, "overture_places": s_places}
    if with_dem:
        jobs["dem"] = s_dem
    if with_resilience:
        jobs["osm_resilience"] = s_resilience
    with ThreadPoolExecutor(len(jobs)) as ex:  # independent I/O-bound sources run concurrently
        list(ex.map(lambda kv: step(*kv), jobs.items()))
    step("population", s_population)  # needs HRSL when the GHS-POP tile is not prepared

    u, eta = PARAMS["roof_utilization"], PARAMS["module_efficiency"]
    summary: Dict[str, object] = {"lat": lat, "lon": lon, "k": k, "resolution": resolution, "n_cells": len(cells),
                                  "area_ha": float(F["area_ha"].sum())}
    have = all(x in ctx for x in ("demand", "pv")) and "population" in F and "ov_bld_footprint_m2" in F
    if have:
        d, Y = ctx["demand"]["kwh_per_capita"], ctx["pv"]["kwh_per_kwp"]
        F["energy_demand_res_kwh"] = F["population"] * d
        F["energy_pv_kwh"] = F["ov_bld_footprint_m2"] * u["value"] * eta["value"] * Y
        F["energy_balance"] = F["energy_pv_kwh"] / F["energy_demand_res_kwh"].where(F["energy_demand_res_kwh"] > 0)
        A, P = float(F["ov_bld_footprint_m2"].sum()), float(F["population"].sum())
        summary["explanation"] = explain_balance(A, P, d, Y, u["value"], eta["value"], u["high"])
        summary["balance_range"] = [A * u["low"] * eta["low"] * Y / (P * d) if P else None,
                                    A * u["high"] * eta["high"] * Y / (P * d) if P else None]
        summary["cells_ped_share"] = float((F["energy_balance"] >= 1).mean())
        summary.update({"population": P, "footprint_m2": A, "demand_kwh": P * d, "pv_kwh": float(F["energy_pv_kwh"].sum()),
                        "inputs": {"kwh_per_capita": ctx["demand"], "pv_yield": ctx["pv"], "country": ctx["country"], "params": PARAMS}})
    else:
        summary["explanation"] = {"verdict": "insufficient_data", "text_tr": "Gerekli kaynaklardan biri alınamadı (bkz. failures); sentetik değerle doldurulmadı."}
    for g in ("vul_elderly60_n", "vul_children0_5_n", "vul_youth15_24_n"):
        if g in F and "vul_pop_hrsl" in F and F["vul_pop_hrsl"].sum() > 0:
            share = float(F[g].sum() / F["vul_pop_hrsl"].sum())
            summary[g.replace("_n", "_share")] = share
            if "population" in F:
                summary[g] = share * float(F["population"].sum())
    if "ov_places_n" in F:
        summary["places"] = float(F["ov_places_n"].sum())
    if "ov_nonosm_share" in F:
        summary["nonosm_footprint_share"] = float(np.nanmean(F["ov_nonosm_share"])) if F["ov_nonosm_share"].notna().any() else None
    for c in ("res_hospital_dist_m", "res_fire_station_dist_m"):
        if c in F:
            summary[c.replace("_m", "_median_m")] = float(F[c].median())
    timing["total"] = round(time.time() - t0, 2)
    return {"summary": summary, "cells": F.reset_index().replace({np.nan: None}).to_dict(orient="records"),
            "provenance": prov, "failures": failures, "timing_s": timing}

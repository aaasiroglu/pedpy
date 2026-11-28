"""Unified global PED inventory → data/inventory/ped_sites.csv (K-071).

Inputs (all already in data/inventory or data/validation, each with its own source record):
  ped_database_2026.csv   PED Database, 114 sites (primary: newest and structured)
  ped_booklet_2020.csv    PED Booklet Feb 2020, 61 projects (+ ped_sites_global.csv: OSM geocoding)
  ped_sites.json          the 16 validation sites (H2020 SCC lighthouse districts, docs/17)
  ped_candidates_class_c.csv  sourced non-European / non-PED-labelled candidates
Matching: a booklet project or a core site joins a database site when they share the country and a
distinctive name token (city words and generic words excluded), or when they lie within 1.5 km.
Manual decisions go to ped_merge_overrides.csv (booklet_no or core site → db_id or 'none').

    python scripts/build_ped_sites.py
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pedx.store import manifest, schema  # noqa: E402

INV, VAL = ROOT / "data" / "inventory", ROOT / "data" / "validation"
GENERIC = {"project", "city", "district", "districts", "making", "atelier", "cityxchange", "smart", "energy", "positive", "ped",
           "campus", "area", "case", "provided", "rhc", "dhc", "zen", "pilot", "the", "and", "new", "towards", "demo", "lab",
           "living", "neighbourhood", "neighbourhoods", "program", "sparcs", "pocityf", "response", "stardust", "sinfonia",
           "replicate", "mysmartlife", "smartencity", "heating", "cool", "ways", "using", "low", "grade", "heat", "within",
           "knowledge", "axis", "urban", "open", "planning", "under", "community", "kommune", "residential", "buildings"}
COUNTRY = {"The Netherlands": "Netherlands", "Czechia": "Czech Republic", "UK": "United Kingdom"}
CORE_COUNTRY = {"Amsterdam": "Netherlands", "Bilbao": "Spain", "Espoo": "Finland", "Bærum": "Norway", "Oulu": "Finland",
                "Groningen": "Netherlands", "Dijon": "France", "Turku": "Finland", "Lyon": "France", "Wien": "Austria",
                "Lund": "Sweden", "Vitoria-Gasteiz": "Spain", "Uppsala": "Sweden", "Helsinki": "Finland", "Nantes": "France"}
# incomplete database records (no fields filled) carry the city in their name only
NAME_COUNTRY = {"Barcelona": "Spain", "Bologna": "Italy", "Leon": "Spain", "Maia": "Portugal", "Tartu": "Estonia"}
PHASE = {"planning phase": "planning", "implementation phase": "implementation", "in operation": "operation", "completed": "completed"}


def tokens(*xs):
    s = " ".join(str(x) for x in xs if isinstance(x, str))
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return set(re.findall(r"[a-z]{3,}", s))


def km(la1, lo1, la2, lo2):
    if any(pd.isna(v) for v in (la1, lo1, la2, lo2)):
        return np.inf
    p = np.pi / 180
    a = np.sin((la2 - la1) * p / 2) ** 2 + np.cos(la1 * p) * np.cos(la2 * p) * np.sin((lo2 - lo1) * p / 2) ** 2
    return 12742 * np.arcsin(np.sqrt(a))


def area_m2(v):
    """'1,280,000' / '330.000' / '485' / '0.5' → m² (thousands separators removed only in d{1,3}([.,]ddd)+ form)."""
    if not isinstance(v, str) or not v.strip():
        return np.nan
    v = v.strip().split()[0]
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", v):
        return float(re.sub(r"[.,]", "", v))
    try:
        return float(v.replace(",", "."))
    except ValueError:
        return np.nan


def booklet_ha(s):
    if not isinstance(s, str):
        return np.nan
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:ha\b|hectare)", s, re.I) or re.search(r"\bHa:\s*(\d+(?:[.,]\d+)?)", s)
    if m:
        return float(m.group(1).replace(",", "."))
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*km\s*[²2]", s, re.I)
    return float(m.group(1).replace(",", ".")) * 100 if m else np.nan


def structure(s):
    if not isinstance(s, str) or not s.strip():
        return "unknown"
    t = s.lower()
    flags = {"new": "newly built" in t, "existing": "existing" in t, "mixed": "mixed" in t}
    if flags["mixed"] or (flags["new"] and flags["existing"]):
        return "mixed"
    return "new" if flags["new"] else ("existing" if flags["existing"] else "unknown")


def db_class(c):
    c = str(c)
    if "PED case study" in c:
        return "A"
    if "PED relevant" in c:
        return "B"
    if "PED Lab" in c:
        return "Lab"
    return "B"


def best_match(tok_site, tok_city, country, la, lo, db):
    cand = db[db.country == country]
    best, score = None, 0
    for r in cand.itertuples():
        distinct = (tok_site & r.tok) - GENERIC - tok_city - r.tok_city
        near = km(la, lo, r.lat, r.lon) < 1.5
        s = len(distinct) * 2 + (1 if tok_city & r.tok_city else 0) + (3 if near else 0)
        if (distinct or near) and s > score:
            best, score = r.db_id, s
    return best


def main():
    db = pd.read_csv(INV / "ped_database_2026.csv")
    bk = pd.read_csv(INV / "ped_booklet_2020.csv")
    geo = pd.read_csv(INV / "ped_sites_global.csv")
    core = json.loads((VAL / "ped_sites.json").read_text())
    cc = pd.read_csv(INV / "ped_candidates_class_c.csv")
    ov_p = INV / "ped_merge_overrides.csv"
    ov = pd.read_csv(ov_p, dtype=str) if ov_p.exists() else pd.DataFrame(columns=["key", "db_id", "note"])
    ov = dict(zip(ov["key"], ov["db_id"]))

    db["country"] = db["country"].replace(COUNTRY)
    db["tok"] = [tokens(n) for n in db["name"]]
    db["tok_city"] = [tokens(c) for c in db["city"]]
    rows, alias = {}, {}
    for r in db.itertuples():
        rows[r.db_id] = {"site_id": f"PEDDB-{r.db_id}", "name": r.name, "city": r.city if isinstance(r.city, str) else None,
                         "country": r.country if isinstance(r.country, str) else None, "lat": r.lat, "lon": r.lon,
                         "coord_src": ("missing" if pd.isna(r.lat) or pd.isna(r.lon) else
                                       "database_corrected" if isinstance(r.coord_note, str) and "swapped" in r.coord_note else "database"),
                         "ped_class": db_class(r.category), "phase": PHASE.get(str(r.phase).lower(), "unknown"), "structure": "unknown",
                         "area_ha": area_m2(r.ground_area_m2) / 1e4, "boundary_type": r.boundary.split(";")[0] if isinstance(r.boundary, str) else None,
                         "financing": r.financing if isinstance(r.financing, str) else None,
                         "ownership_land": r.ownership_land if isinstance(r.ownership_land, str) else None, "in_core16": False,
                         "sources": f"PED Database #{r.db_id}", "url": r.url}
    # database entries without a country (incomplete records) take it from a booklet or core match later, else 'unknown'
    first_geo = geo.sort_values("id").groupby("booklet_no").first()
    log = []
    for r in bk.itertuples():
        g = first_geo.loc[r.no] if r.no in first_geo.index else None
        country = COUNTRY.get(r.country, r.country) if isinstance(r.country, str) else None
        if country is None:
            country = next((c for c in ("Netherlands", "Finland") if c in str(r.place)), None)
        la, lo = (g.lat, g.lon) if g is not None and g.level in ("site_polygon", "site_point") else (np.nan, np.nan)
        key = f"booklet-{r.no}"
        m = ov.get(key, best_match(tokens(r.place, r.project, r.project_name, g.site_name if g is not None else None),
                                   tokens(r.place), country, la, lo, db))
        m = None if m in (None, "none") or (isinstance(m, float) and np.isnan(m)) else int(m)
        ha = booklet_ha(r.size_raw)
        if m is not None:
            e = rows[m]
            e["sources"] += f"; PED Booklet 2020 #{r.no}"
            e["structure"] = structure(r.structure) if e["structure"] == "unknown" else e["structure"]
            if pd.isna(e["area_ha"]) and not np.isnan(ha):
                e["area_ha"] = ha
            if e["country"] is None:
                e["country"] = country
            log.append((key, f"→ PEDDB-{m}", r.place, r.project))
            continue
        coord = "osm_site" if not np.isnan(la) else "osm_city"
        if np.isnan(la) and g is not None and g.level == "city":
            la, lo = g.lat, g.lon
        rows[f"b{r.no}"] = {"site_id": f"BKL-{r.no:02d}", "name": f"{r.place} – {r.project}" if isinstance(r.project, str) else str(r.place), "city": r.place, "country": country or "unknown",
                            "lat": la, "lon": lo, "coord_src": coord if not np.isnan(la) else "missing",
                            "ped_class": "A" if r.category == "PED" else "B",
                            "phase": {"implemented/in operation": "operation", "implementation": "implementation", "planning": "planning"}.get(r.stage, "unknown"),
                            "structure": structure(r.structure), "area_ha": ha, "boundary_type": None,
                            "financing": r.financing if isinstance(r.financing, str) else None, "ownership_land": None, "in_core16": False,
                            "sources": f"PED Booklet 2020 #{r.no}", "url": r.website if isinstance(r.website, str) else None}
    for i, s in enumerate(core, 1):
        country = CORE_COUNTRY[s["city"]]
        key = f"core-{s['site']}"
        m = ov.get(key, best_match(tokens(s["site"]), tokens(s["city"]), country, s["lat"], s["lon"], db))
        if isinstance(m, str) and m.startswith("BKL-"):
            hit = next(k for k, v in rows.items() if v["site_id"] == m)
            rows[hit].update(in_core16=True, lat=s["lat"], lon=s["lon"], coord_src="core16", name=f'{s["site"]} ({rows[hit]["name"]})')
            rows[hit]["sources"] += "; core-16 validation set (docs/17)"
            log.append((key, f"→ {m}", s["site"], s["city"]))
            continue
        m = None if m in (None, "none") or (isinstance(m, float) and np.isnan(m)) else int(m)
        if m is not None:
            rows[m]["in_core16"] = True
            rows[m]["sources"] += "; core-16 validation set (docs/17)"
            log.append((key, f"→ PEDDB-{m}", s["site"], s["city"]))
            continue
        hit = next((k for k, v in rows.items() if str(k).startswith("b") and s["site"].split()[0].lower() in v["name"].lower()), None)
        if hit:
            rows[hit]["in_core16"] = True
            rows[hit]["sources"] += "; core-16 validation set (docs/17)"
            if rows[hit]["coord_src"] != "osm_site":
                rows[hit].update(lat=s["lat"], lon=s["lon"], coord_src="core16")
            log.append((key, f"→ {rows[hit]['site_id']}", s["site"], s["city"]))
            continue
        rows[key] = {"site_id": f"SCC-{i:02d}", "name": s["site"], "city": s["city"], "country": country, "lat": s["lat"], "lon": s["lon"],
                     "coord_src": "core16", "ped_class": "A", "phase": "unknown", "structure": "unknown", "area_ha": np.nan,
                     "boundary_type": None, "financing": None, "ownership_land": None, "in_core16": True,
                     "sources": f"core-16 validation set (docs/17); OSM {s['osm']}", "url": None}
    for i, r in enumerate(cc.itertuples(), 1):
        rows[f"c{i}"] = {"site_id": f"C-{i:02d}", "name": r.name, "city": r.city if isinstance(r.city, str) else None, "country": r.country,
                         "lat": np.nan, "lon": np.nan, "coord_src": "missing", "ped_class": "C", "phase": "unknown", "structure": "unknown",
                         "area_ha": np.nan, "boundary_type": None, "financing": None, "ownership_land": None, "in_core16": False,
                         "sources": f"class C candidate: {r.source}", "url": None}
    out = pd.DataFrame(rows.values())
    miss = out["country"].isna()
    out.loc[miss, "country"] = out.loc[miss, "name"].map(lambda n: NAME_COUNTRY.get(str(n).split(",")[0].strip()))
    out["country"] = out["country"].fillna("unknown")
    out["in_core16"] = out["in_core16"].astype(bool)
    out = out.sort_values(["ped_class", "country", "name"]).reset_index(drop=True)
    problems = schema.validate(out, "ped_sites")
    f = INV / "ped_sites.csv"
    out.to_csv(f, index=False, encoding="utf-8")
    stats = {"by_class": out.ped_class.value_counts().to_dict(), "by_coord_src": out.coord_src.value_counts().to_dict(),
             "countries": int(out.country.nunique()), "in_core16": int(out.in_core16.sum()),
             "with_area": int(out.area_ha.notna().sum()), "booklet_merged_into_database": sum(1 for k, *_ in log if k.startswith("booklet"))}
    manifest.register("inventory/ped_sites", f, "ped_sites", schema.PED_SITES.version, len(out), inputs=[
        {"source": "ped_database", "file": "data/inventory/ped_database_2026.csv", "licence": "public web pages; attributes only, no personal data"},
        {"source": "ped_booklet_2020", "file": "data/inventory/ped_booklet_2020.csv", "licence": "JPI Urban Europe publication"},
        {"source": "osm_nominatim", "file": "data/inventory/ped_sites_global.csv", "licence": "ODbL 1.0"},
        {"source": "core16", "file": "data/validation/ped_sites.json", "licence": "ODbL 1.0 (OSM ids)"},
        {"source": "class_c", "file": "data/inventory/ped_candidates_class_c.csv", "licence": "cited sources"}],
        params={"match": "same country and distinctive name token, or ≤1.5 km", "overrides": ov_p.name if ov_p.exists() else None}, stats=stats)
    pd.DataFrame(log, columns=["key", "merged_into", "name", "detail"]).to_csv(INV / "ped_merge_log.csv", index=False)
    print(len(out), "sites;", stats)
    print("schema:", problems or "ok")


if __name__ == "__main__":
    main()

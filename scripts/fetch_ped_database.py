"""Global PED inventory, step 3: the PED Database (COST PED-EU-NET, IEA EBC Annex 83, JPI UE / DUT). (K-069)

Source: https://peddatabase.dutpartnership.eu  (public WordPress REST listing + one public page per case).
Only site attributes are kept. Contact names and e-mail addresses on the pages are personal data and are
NOT stored. Pages are cached under data/cache/peddb/ (not in git); one request every 1.5 s.

    python scripts/fetch_ped_database.py   → data/inventory/ped_database_2026.csv
"""

import csv
import html
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache" / "peddb"
BASE = "https://peddatabase.dutpartnership.eu"
UA = "Mozilla/5.0 (pedx-research; MSc thesis, Istanbul Technical University)"
CODE = re.compile(r"^([ABC]\dP\d{3}[a-z]?)\s*:\s*(.*)$")
KEEP = {"A1P003": "category", "A1P004": "targets", "A1P005": "phase", "A1P006": "start", "A1P007": "end", "A1P012": "country",
        "A1P013": "city", "A1P014": "climate", "A1P015": "boundary", "A1P016": "ownership_case", "A1P017": "ownership_land",
        "A1P020": "ground_area_m2", "A1P025": "cost_mil_eur", "A2P020": "res_share_onsite"}


def get(url, path):
    if not path.exists():
        for attempt in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=90) as r:
                    path.write_bytes(r.read()); time.sleep(1.5); break
            except Exception:
                time.sleep(5 * (attempt + 1))
    return path.read_text(encoding="utf-8") if path.exists() else ""


def coord(v):
    """Decimal degrees from '19°05'33.6"' or '19.0927' (comma decimals accepted)."""
    v = v.strip().replace(",", ".")
    m = re.match(r"^(-?\d+)[°º]\s*(\d+)['′]\s*([\d.]+)", v)
    if m:
        d = abs(int(m.group(1))) + int(m.group(2)) / 60 + float(m.group(3)) / 3600
        return round(-d if v.startswith("-") or re.search(r"[WS]\s*$", v) else d, 6)
    m = re.match(r"^-?\d+(\.\d+)?", v)
    return round(float(m.group(0)), 6) if m else None


def parse(page):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S)
    L = [x.strip() for x in html.unescape(re.sub(r"<[^>]+>", "\n", t)).split("\n") if x.strip()]
    rec, fin, i = {}, [], 0
    while i < len(L):
        m = CODE.match(L[i])
        if not m:
            i += 1; continue
        code, label = m.group(1), m.group(2)
        vals, j = [], i + 1
        while j < len(L) and not CODE.match(L[j]) and not L[j].startswith("Contact person"):
            if L[j] not in vals and L[j].rstrip(".:") != label.rstrip(".:"):
                vals.append(L[j])
            j += 1
        if code == "A1P011":
            for k, x in enumerate(vals):
                if x.lower().startswith("x coord") and k + 1 < len(vals): rec["lon"] = coord(vals[k + 1])
                if x.lower().startswith("y coord") and k + 1 < len(vals): rec["lat"] = coord(vals[k + 1])
        elif code.startswith("A1P022") and len(code) == 7:
            fin.append(re.sub(r"^Financing\s*[–-]\s*", "", label))
        elif code in KEEP and vals and KEEP[code] not in rec:
            rec[KEEP[code]] = "; ".join(vals)[:400]
        i = j
    rec["financing"] = "; ".join(x for x in dict.fromkeys(fin) if not x.lower().startswith("add the value"))
    if "category" in rec:
        rec["category"] = rec["category"].replace("PED Lab.", "PED Lab").replace("; PED/PED relevant case study.", "")
    # the form's X (longitude) and Y (latitude) fields are often filled the other way round: swap when only the
    # swapped pair is a plausible European position, and say so
    la, lo = rec.get("lat"), rec.get("lon")
    ok = lambda a, b: a is not None and b is not None and 34 <= a <= 72 and -30 <= b <= 45
    if la is not None and lo is not None and not ok(la, lo) and ok(lo, la):
        rec["lat"], rec["lon"], rec["coord_note"] = lo, la, "lat/lon swapped in source; corrected"
    elif not ok(la, lo):
        rec["coord_note"] = "missing or implausible in source"
    return rec


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    cases = []
    for p in (1, 2, 3):
        s = get(f"{BASE}/wp-json/wp/v2/case-studies?per_page=100&page={p}", CACHE / f"list_{p}.json")
        try:
            d = json.loads(s)
        except Exception:
            break
        if not isinstance(d, list) or not d:
            break
        cases += d
    rows = []
    for c in cases:
        rec = parse(get(c["link"], CACHE / f'{c["slug"]}.html'))
        rec.update({"db_id": c["id"], "name": html.unescape(c["title"]["rendered"]), "url": c["link"], "modified": c["modified"][:10],
                    "source": "PED Database (PED-EU-NET, Annex 83, JPI UE/DUT)"})
        rows.append(rec); print(rec["db_id"], rec["name"], "|", rec.get("category"), "|", rec.get("country"), rec.get("lat"), rec.get("lon"), flush=True)
    cols = ["db_id", "name", "city", "country", "category", "phase", "start", "end", "lat", "lon", "coord_note", "boundary", "ground_area_m2",
            "ownership_case", "ownership_land", "financing", "cost_mil_eur", "targets", "res_share_onsite", "climate", "url", "modified", "source"]
    with (ROOT / "data" / "inventory" / "ped_database_2026.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print(len(rows), "cases")


if __name__ == "__main__":
    main()

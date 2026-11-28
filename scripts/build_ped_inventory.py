"""Global PED inventory, step 1: parse the JPI Urban Europe PED Booklet (Gollner et al., Feb 2020). (K-068)

Source: "Europe towards Positive Energy Districts — first update, February 2020", JPI Urban Europe,
https://jpi-urbaneurope.eu/wp-content/uploads/2020/06/PED-Booklet-Update-Feb-2020_2.pdf  (61 projects:
29 with a declared PED ambition, 32 "towards PED"). Every field is copied from the booklet's "General
information" table of each project; nothing is inferred.

    pdftotext -layout PED-Booklet-Update-Feb-2020_2.pdf booklet.txt
    python scripts/build_ped_inventory.py booklet.txt   → data/inventory/ped_booklet_2020.csv
"""

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {"City": "city_raw", "Project name": "project_name", "Project status": "status_raw", "Project start": "period",
          "Project website": "website", "Size of project area": "size_raw", "Building structure": "structure_raw",
          "Land use": "land_use", "Financing": "financing", "Contact": None}
HEAD = re.compile(r"^\s{0,3}(\d{1,2})\s{2,}(\S.*?)\s*$")


def ticked(raw):
    """Options followed by a ticked box (☒/☑/x) in 'a ☐ b ☒ c ☐' strings."""
    out = [m.group(1).strip(" ,;") for m in re.finditer(r"([^☐☒☑]+?)\s*[☒☑]", raw)]
    return "; ".join(out)


def main(txt):
    lines = Path(txt).read_text(encoding="utf-8").splitlines()
    toc_end = next(i for i, l in enumerate(lines) if l.strip() == "PED FRAMEWORK DEFINITION" and i > 200)
    toc, cat, stage = {}, None, None
    for l in lines[:toc_end]:
        t = re.sub(r"\.{3,}.*", "", l).strip()
        if t.startswith("PED PROJECTS"): cat = "PED"
        elif t.startswith("TOWARDS POSITIVE"): cat = "Towards PED"
        elif t.startswith("IMPLEMENTED"): stage = "implemented/in operation"
        elif t.startswith("IN IMPLEMENTATION"): stage = "implementation"
        elif t.startswith("IN PLANNING"): stage = "planning"
        m = re.match(r"^(\d{1,2})\s+(\S.*)$", t)
        if m and cat:
            toc[int(m.group(1))] = {"no": int(m.group(1)), "title": m.group(2).strip(), "category": cat, "stage": stage}
    # body: 'General information' blocks, in order
    starts = [i for i, l in enumerate(lines) if l.strip().lower() == "general information" and i > toc_end]
    rows = []
    for n, s in enumerate(starts, 1):
        end = next((i for i in range(s, min(s + 80, len(lines))) if lines[i].strip().startswith("Overview")), s + 40)
        rec, key = dict(toc.get(n, {"no": n})), None
        for l in lines[s + 1:end]:
            if not l.strip():
                continue
            hit = next((k for k in FIELDS if l.strip().startswith(k)), None)
            if hit:
                key = FIELDS[hit]
                val = re.split(r"\s{2,}", l.strip(), maxsplit=1)
                val = val[1] if len(val) > 1 else ""
                if hit == "Project start":
                    val = re.sub(r"^[–-]\s*end\s*", "", val)
                if key: rec[key] = val.strip()
            elif key and l.startswith(" " * 10):
                rec[key] = (rec.get(key, "") + " " + l.strip()).strip()
        rec["status"] = ticked(rec.get("status_raw", "")); rec["structure"] = ticked(rec.get("structure_raw", ""))
        t = rec.get("title", "")
        m = re.match(r"^(.*?),\s*([^,–-]+?)\s*[–-]\s*(.*)$", t)
        rec["place"], rec["country"], rec["project"] = (m.group(1).strip(), m.group(2).strip(), m.group(3).strip()) if m else (t, "", "")
        rec["source"] = "PED Booklet Feb 2020 (JPI Urban Europe), project no. %d" % n
        rows.append(rec)
    cols = ["no", "category", "stage", "place", "country", "project", "project_name", "status", "period", "structure", "size_raw",
            "land_use", "financing", "website", "source"]
    out = ROOT / "data" / "inventory" / "ped_booklet_2020.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print(len(toc), "toc entries;", len(rows), "blocks →", out)
    return rows


if __name__ == "__main__":
    main(sys.argv[1])

"""pedx v0 demonstration: Caferağa (Kadıköy, Istanbul).

Run:  python examples/v0_caferaga.py [--resolution 10] [--offline]

Data (all free and open):
* buildings  – OpenStreetMap via Overpass (cached in data/raw/), © OSM contributors, ODbL
* irradiance – EU JRC PVGIS 5.3 (SARAH-3), year 2019, horizontal plane

If a source is unreachable the script falls back to clearly labelled
SYNTHETIC data and says so in every output. Results go to results/v0/.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pedx.ingest import buildings_query, fetch_overpass, parse_buildings
from pedx.ingest.pvgis import fetch_pvgis_hourly
from pedx.pipeline import assess
from pedx.synthetic import solar_irradiance

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "results" / "v0"
BBOX = (40.981, 29.021, 40.991, 29.035)  # approx. Caferağa; replace with İBB neighbourhood polygon
CENTER = (40.986, 29.028)


def md_table(df: pd.DataFrame, index: bool = True) -> str:
    """Minimal Markdown table (avoids the optional `tabulate` dependency)."""
    d = df.reset_index() if index else df
    cols = [str(c) for c in d.columns]
    fmt = lambda v: f"{v:.3f}" if isinstance(v, (float, np.floating)) else str(v)  # noqa: E731
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in d.itertuples(index=False)]
    return "\n".join(lines)


def load_irradiance(offline: bool):
    try:
        if offline and not (RAW / "pvgis_caferaga_2019.json").exists():
            raise RuntimeError("offline")
        df = fetch_pvgis_hourly(*CENTER, year=2019, cache=RAW / "pvgis_caferaga_2019.json")
        return df["irradiance_kw_m2"].to_numpy(), "PVGIS 5.3 SARAH-3, 2019 (gözlem tabanlı)"
    except Exception as exc:  # noqa: BLE001
        return solar_irradiance(CENTER[0]), f"SENTETİK ışınım ({type(exc).__name__})"


def synthetic_buildings(n: int = 400, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    s, w, nn, e = BBOX
    return pd.DataFrame(
        {
            "osm_id": [f"synthetic/{i}" for i in range(n)],
            "lat": rng.uniform(s, nn, n),
            "lon": rng.uniform(w, e, n),
            "footprint_area_m2": rng.lognormal(np.log(180), 0.5, n),
            "building": rng.choice(["apartments", "residential", "commercial", "office"], n, p=[0.55, 0.25, 0.12, 0.08]),
            "levels": np.where(rng.random(n) < 0.6, rng.integers(2, 8, n), np.nan),
            "height_m": np.nan,
            "height_source": "missing",
            "start_year": np.nan,
            "roof_shape": None,
        }
    )


def load_buildings(offline: bool):
    cache = RAW / "caferaga_buildings_overpass.json"
    try:
        if offline and not cache.exists():
            raise RuntimeError("offline")
        payload = fetch_overpass(buildings_query(BBOX), cache=cache)
        df = parse_buildings(payload)
        if df.empty:
            raise RuntimeError("no buildings returned")
        return df, f"OpenStreetMap ({len(df)} bina)"
    except Exception as exc:  # noqa: BLE001
        return synthetic_buildings(), f"SENTETİK bina katmanı ({type(exc).__name__}) — OSM erişimi sağlanınca yeniden çalıştırın"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resolution", type=int, default=10)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--n-prescribe", type=int, default=3)
    args = ap.parse_args()

    irr, irr_src = load_irradiance(args.offline)
    bld, bld_src = load_buildings(args.offline)
    print(f"Işınım: {irr_src}\nBinalar: {bld_src}")
    res = assess(bld, irr, resolution=args.resolution, n_prescribe=args.n_prescribe)

    OUT.mkdir(parents=True, exist_ok=True)
    res.scores.to_csv(OUT / "cell_scores.csv")
    res.rank_uncertainty.to_csv(OUT / "rank_uncertainty.csv")
    res.contributions.to_csv(OUT / "contributions.csv")
    res.boundary_path.to_csv(OUT / "boundary_path.csv", index=False)
    res.shapley.to_csv(OUT / "boundary_shapley.csv")
    res.prescriptions.to_csv(OUT / "prescriptions_pareto.csv", index=False)
    res.data_quality.to_csv(OUT / "data_quality.csv")
    res.assumptions.to_csv(OUT / "assumptions.csv")

    top = res.scores.head(10)[["balance", "ssr", "peak_relief", "readiness"]].join(res.rank_uncertainty)
    summary = {
        "irradiance_source": irr_src,
        "building_source": bld_src,
        "h3_resolution": args.resolution,
        "n_cells": int(len(res.scores)),
        "n_cells_balance_ge_1": int((res.scores["balance"] >= 1).sum()),
        "boundary_cells": res.boundary_cells,
        "boundary_is_ped": bool(len(res.boundary_cells) and res.boundary_path.set_index("added").loc[res.boundary_cells[-1], "balance"] >= 1),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    md = [
        "# pedx v0 — Caferağa çıktı özeti",
        "",
        f"- Işınım: **{irr_src}**",
        f"- Binalar: **{bld_src}**",
        "- Talep profilleri: **SENTETİK** (gerçek veri gelene kadar; docs/07 C1)",
        f"- H3 çözünürlüğü: {args.resolution}; hücre sayısı: {summary['n_cells']}; yıllık denge ≥ 1 olan hücre: {summary['n_cells_balance_ge_1']}",
        "",
        "## İlk 10 hücre (teknik potansiyel senaryosu) ve sıra belirsizliği",
        "",
        md_table(top),
        "",
        "## PEB sınır büyütme yolu",
        "",
        md_table(res.boundary_path, index=False),
        "",
        "## Sınırdaki hücrelerin öz-tüketime Shapley katkısı (graf-XAI)",
        "",
        md_table(res.shapley),
        "",
        "## En düşük skorlu hücreler için bütçe–skor Pareto eğrisi (mevcut durumdan)",
        "",
        md_table(res.prescriptions, index=False) if not res.prescriptions.empty else "_(çalıştırılmadı)_",
        "",
        "## Veri kalitesi",
        "",
        md_table(res.data_quality),
        "",
        "> Varsayımların tamamı `assumptions.csv` içinde; `varsayim` durumundakiler İBB ve literatür verisiyle değiştirilecek.",
    ]
    (OUT / "OZET.md").write_text("\n".join(md))
    print(f"Çıktılar: {OUT}")


if __name__ == "__main__":
    main()

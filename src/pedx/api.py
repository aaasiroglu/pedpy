"""Local HTTP API for on-demand assessment: ``uvicorn pedx.api:app --port 8766`` (``make api``).

GET /health                      → {"ok": true, "version": ...}
GET /assess?lat=..&lon=..&k=3    → pedx.service.assess_point(...) + GeoJSON of the hexagons

The single-file web app (web/pedx_app.html) detects this API on 127.0.0.1:8766 and then evaluates
any clicked point on Earth live; without it, the app shows the precomputed Caferağa study area.
"""

from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .service import assess_point

app = FastAPI(title="pedx — on-demand PED suitability", version=__version__)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


def _geojson(cells):
    import h3

    feats = []
    for r in cells:
        ring = [[lon, lat] for lat, lon in h3.cell_to_boundary(r["cell"])]
        feats.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring + ring[:1]]}, "properties": r})
    return {"type": "FeatureCollection", "features": feats}


@app.get("/health")
def health():
    return {"ok": True, "version": __version__}


@app.get("/assess")
def assess(lat: float = Query(..., ge=-85, le=85), lon: float = Query(..., ge=-180, le=180),
           k: int = Query(3, ge=0, le=6), resolution: int = Query(10, ge=8, le=11),
           resilience: bool = True, dem: bool = True):
    r = assess_point(lat, lon, k=k, resolution=resolution, with_resilience=resilience, with_dem=dem)
    r["geojson"] = _geojson(r.pop("cells"))
    return r


@app.get("/score")
def score(lat: float = Query(..., ge=-85, le=85), lon: float = Query(..., ge=-180, le=180), target: float = Query(70, ge=1, le=99)):
    """Total PED score for the ~28 ha site centred on (lat, lon): city grid (built once, ~1 min) → city stats → model."""
    from pathlib import Path

    import h3
    import numpy as np

    from .citygrid import city_grid
    from .score import PEDScore, candidate_discs, city_stats

    model_path = Path(__file__).resolve().parents[2] / "data" / "validation" / "ped_score_model.json"
    model = PEDScore.from_json(model_path)
    F, prov = city_grid(lat, lon, f"pt_{lat:.2f}_{lon:.2f}".replace("-", "m").replace(".", "p"))
    st = city_stats(candidate_discs(F))
    x = candidate_discs(F, centres=[h3.latlng_to_cell(lat, lon, 10)]).iloc[0].to_dict()
    x = {k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in x.items()}
    xf = {k: (np.nan if v is None else v) for k, v in x.items()}
    from .report import REPORT, report_metrics

    area_ha = 19 * h3.average_hexagon_area(10, unit="m^2") / 1e4
    allc = candidate_discs(F)
    R_all = report_metrics(allc, area_ha)
    R_site = report_metrics(candidate_discs(F, centres=[h3.latlng_to_cell(lat, lon, 10)]), area_ha).iloc[0]
    report = []
    for m in REPORT:
        v, col = R_site[m["key"]], R_all[m["key"]].dropna()
        pct = float((col < v).mean() + 0.5 * (col == v).mean()) if np.isfinite(v) and len(col) else None
        report.append({**m, "value": None if not np.isfinite(v) else float(v), "city_percentile": pct})
    return {"site": x, "report": report, "explain": model.explain(xf, st), "inverse": model.inverse(xf, st, target),
            "model": {"auc_loco": model.meta.get("auc_loco"), "n_cases": model.meta.get("n_cases")},
            "city": {"country": (prov.get("country") or {}).get("name"), "failures": prov.get("failures"), "timing_s": prov.get("timing_s")}}

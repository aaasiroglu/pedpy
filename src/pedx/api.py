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

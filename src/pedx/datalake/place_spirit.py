"""Urban function profile and "spirit of place" layers per H3 cell (K-051).

From open, global, keyless sources only:

* Overture places (Meta, Foursquare OS Places, Microsoft, AllThePlaces; CDLA-Permissive-2.0):
  social, financial, education, culture, heritage, faith, health, daily needs, food, night life,
  retail, office, crafts/production, tourism, sport, public administration, parks.
* Overture base/land_use (ODbL): plazas and pedestrian areas (squares), parks/gardens, construction
  sites (active transformation), religious, residential and commercial land.
* Wikidata (CC0) via SPARQL box search: notable items, collective attention (sum of Wikipedia
  sitelinks), registered heritage (P1435), town squares (Q174782).
* Wikidata items with an image (P18): photographed notable places (always on).
* Wikimedia Commons (CC BY-SA and other free licences) geotagged media: photographic attention —
  where people choose to take and share pictures (cf. Seresinhe et al. 2017). Opt-in (PEDX_COMMONS=1):
  the API rate-limits shared egress IPs.

Indices (computed on a site disc; each documented with its literature anchor)
* functional mix (Shannon entropy of groups; Jacobs 1961)
* third places per 1 000 people (cafés, bars, social venues; Oldenburg 1989)
* social infrastructure per 1 000 people (community, library, education, health, faith, parks; Klinenberg 2018)
* cultural capital per ha (culture + heritage + education; Florida 2002 / Bourdieu)
* genius loci attention (Wikidata sitelinks + Commons photos per ha; Norberg-Schulz 1980)
* transformation signal (construction land share)

Online reviews (Google, Tripadvisor, Yelp) are NOT used: their terms forbid collection and they are
personal data (KVKK/GDPR). Open text (Wikipedia/Wikivoyage) and open images (Commons, Mapillary
with a key) are the admissible substitutes.
"""

from __future__ import annotations

import json
import math
import time
import urllib.parse
import urllib.request
from typing import Iterable, Tuple

import numpy as np
import pandas as pd

__all__ = ["PLACE_GROUPS", "place_profile", "landuse_profile", "wikidata_items", "commons_photos", "per_cell_points"]

UA = {"User-Agent": "pedx-research/0.6 (open-data thesis pipeline; https://github.com/aaasiroglu/pedpy)"}
BBox = Tuple[float, float, float, float]

# (top level, second level or None) → group. First match wins; order matters.
PLACE_GROUPS = [
    ("pl_night", ("food_and_drink", "alcoholic_beverage_venue")), ("pl_night", ("arts_and_entertainment", "nightlife_venue")),
    ("pl_heritage", ("cultural_and_historic", "historic_site")),
    ("pl_faith", ("cultural_and_historic", "place_of_worship")), ("pl_faith", ("cultural_and_historic", "religious_organization")),
    ("pl_culture", ("cultural_and_historic", None)), ("pl_culture", ("arts_and_entertainment", "museum")),
    ("pl_culture", ("arts_and_entertainment", "performing_arts_venue")), ("pl_culture", ("arts_and_entertainment", "arts_and_crafts_space")),
    ("pl_culture", ("education", "library")),
    ("pl_education", ("education", None)),
    ("pl_social", ("community_and_government", "social_or_community_service")), ("pl_social", ("community_and_government", "civic_organization")),
    ("pl_social", ("community_and_government", "public_facility")),
    ("pl_public", ("community_and_government", None)),
    ("pl_finance", ("services_and_business", "financial_service")), ("pl_finance", ("services_and_business", "real_estate_service")),
    ("pl_office", ("services_and_business", "professional_service")), ("pl_office", ("services_and_business", "corporate_or_business_office")),
    ("pl_office", ("services_and_business", "b2b_service")), ("pl_office", ("services_and_business", "legal_service")),
    ("pl_office", ("services_and_business", "media_service")), ("pl_office", ("services_and_business", "design_service")),
    ("pl_crafts", ("services_and_business", None)),
    ("pl_health", ("health_care", None)),
    ("pl_daily", ("shopping", "food_and_beverage_store")), ("pl_daily", ("shopping", "convenience_store")),
    ("pl_third", ("food_and_drink", "non_alcoholic_beverage_venue")), ("pl_third", ("food_and_drink", "casual_eatery")),
    ("pl_food", ("food_and_drink", None)),
    ("pl_retail", ("shopping", None)),
    ("pl_tourism", ("lodging", None)), ("pl_tourism", ("travel_and_transportation", "travel_service")),
    ("pl_park", ("sports_and_recreation", "park")), ("pl_sport", ("sports_and_recreation", None)),
    ("pl_personal", ("lifestyle_services", None)), ("pl_arts", ("arts_and_entertainment", None)),
]
GROUP_NAMES = sorted({g for g, _ in PLACE_GROUPS} | {"pl_other"})
LANDUSE = {"lu_plaza_m2": {("pedestrian", "plaza"), ("pedestrian", "pedestrian")},
           "lu_green_m2": {("park", None), ("horticulture", None), ("recreation", "playground"), ("managed", "grass"), ("protected", None)},
           "lu_construction_m2": {("construction", None)}, "lu_religious_m2": {("religious", None)},
           "lu_residential_m2": {("residential", None)}, "lu_commercial_m2": {("developed", "commercial"), ("developed", "retail")}}


def _group(h) -> str:
    if h is None or len(h) == 0:
        return "pl_other"
    top, second = h[0], (h[1] if len(h) > 1 else None)
    for g, (t, s) in PLACE_GROUPS:
        if t == top and (s is None or s == second):
            return g
    return "pl_other"


def per_cell_points(lat, lon, cells, resolution: int, weights=None, name: str = "n") -> pd.Series:
    from ..spatial.h3grid import assign_cells

    cells = list(cells)
    if len(lat) == 0:
        return pd.Series(0.0, index=pd.Index(cells, name="cell"), name=name)
    s = pd.Series(np.ones(len(lat)) if weights is None else np.asarray(weights, float), index=assign_cells(lat, lon, resolution))
    return s.groupby(level=0).sum().reindex(cells).fillna(0.0).rename(name)


def place_profile(df: pd.DataFrame, cells: Iterable[str], resolution: int, min_confidence: float = 0.5) -> pd.DataFrame:
    """Counts of Overture places per functional group per cell."""
    import shapely

    cells = list(cells)
    d = df[pd.to_numeric(df["confidence"], errors="coerce") >= min_confidence]
    g = [_group(t.get("hierarchy") if isinstance(t, dict) else None) for t in d["taxonomy"]]
    geom = d["geometry"].to_numpy()
    lat, lon = shapely.get_y(geom), shapely.get_x(geom)
    out = pd.DataFrame(index=pd.Index(cells, name="cell"))
    for name in GROUP_NAMES:
        m = np.asarray([x == name for x in g])
        out[name] = per_cell_points(lat[m], lon[m], cells, resolution, name=name)
    return out


def landuse_profile(df: pd.DataFrame, cells: Iterable[str], resolution: int) -> pd.DataFrame:
    """Area [m²] of plazas/pedestrian zones, green, construction, religious, residential, commercial land per cell (by centroid)."""
    import shapely

    cells = list(cells)
    out = pd.DataFrame(index=pd.Index(cells, name="cell"))
    if df.empty:
        for k in LANDUSE:
            out[k] = 0.0
        return out
    geom = df["geometry"].to_numpy()
    cen = shapely.centroid(geom)
    lat, lon = shapely.get_y(cen), shapely.get_x(cen)
    lat0 = np.radians(np.nanmean(lat))
    kk = np.pi / 180 * 6_371_008.8
    area = shapely.area(shapely.transform(geom, lambda xy: np.c_[xy[:, 0] * kk * np.cos(lat0), xy[:, 1] * kk]))
    sub, cls = df["subtype"].to_numpy(), df["class"].to_numpy()
    for k, rules in LANDUSE.items():
        m = np.asarray([any(s == r[0] and (r[1] is None or c == r[1]) for r in rules) for s, c in zip(sub, cls)])
        out[k] = per_cell_points(lat[m], lon[m], cells, resolution, weights=area[m], name=k)
    return out


def _get(url: str, timeout: int = 120, tries: int = 4) -> bytes:
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:  # noqa: S310
                return r.read()
        except Exception:  # noqa: BLE001
            if i == tries - 1:
                raise
            time.sleep(3 * 2**i)
    raise RuntimeError("unreachable")


def wikidata_items(bbox: BBox) -> pd.DataFrame:
    """Every Wikidata item with coordinates inside the bbox: sitelinks, heritage designation, town square."""
    w, s, e, n = bbox
    q = f"""SELECT ?item ?lat ?lon ?sl (SAMPLE(?h) AS ?her) (SAMPLE(?q) AS ?sq) (SAMPLE(?img) AS ?pic) WHERE {{
      SERVICE wikibase:box {{ ?item wdt:P625 ?c . bd:serviceParam wikibase:cornerSouthWest "Point({w} {s})"^^geo:wktLiteral .
        bd:serviceParam wikibase:cornerNorthEast "Point({e} {n})"^^geo:wktLiteral . }}
      ?item wikibase:sitelinks ?sl . OPTIONAL {{ ?item wdt:P1435 ?h }} OPTIONAL {{ ?item wdt:P31 wd:Q174782 . BIND(1 AS ?q) }}
      OPTIONAL {{ ?item wdt:P18 ?img }}
      BIND(geof:latitude(?c) AS ?lat) BIND(geof:longitude(?c) AS ?lon) }} GROUP BY ?item ?lat ?lon ?sl"""
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"})
    b = json.loads(_get(url, timeout=180))["results"]["bindings"]
    return pd.DataFrame([{"lat": float(x["lat"]["value"]), "lon": float(x["lon"]["value"]), "sitelinks": int(x["sl"]["value"]),
                          "heritage": int("her" in x), "square": int("sq" in x), "photo": int("pic" in x)} for x in b])


def commons_photos(bbox: BBox, tile_deg: float = 0.03, sleep: float = 1.0) -> Tuple[pd.DataFrame, dict]:
    """Geotagged Wikimedia Commons files (namespace 6) by bbox tiles of ``tile_deg`` (API limit 500 per tile).

    Polite client (Wikimedia API etiquette): one request per ``sleep`` seconds, serial, identifying
    User-Agent, back-off on rate limits. A tile that still fails raises — a partial layer is never
    silently written as zeros.
    """
    w, s, e, n = bbox
    rows, saturated, tiles = [], 0, 0
    lat = s
    while lat < n:
        lon = w
        while lon < e:
            bb = f"{min(lat + tile_deg, n)}|{lon}|{lat}|{min(lon + tile_deg, e)}"  # top|left|bottom|right
            url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
                {"action": "query", "list": "geosearch", "gsbbox": bb, "gsnamespace": 6, "gslimit": 500, "format": "json", "maxlag": 5})
            for i in range(6):
                try:
                    r = json.loads(_get(url, timeout=60, tries=1))["query"]["geosearch"]
                    break
                except Exception:  # noqa: BLE001  (rate limit page is not JSON) → back off
                    if i == 5:
                        raise RuntimeError(f"Commons tile failed after retries: {bb}")
                    time.sleep(10 * (i + 1))
            tiles += 1
            saturated += int(len(r) >= 500)
            rows += [(x["lat"], x["lon"]) for x in r]
            time.sleep(sleep)
            lon += tile_deg
        lat += tile_deg
    df = pd.DataFrame(rows, columns=["lat", "lon"]).drop_duplicates()
    return df, {"tiles": tiles, "saturated_tiles": saturated, "photos": int(len(df)), "tile_deg": tile_deg,
                "note": "tiles with 500 results are lower bounds (API cap)"}

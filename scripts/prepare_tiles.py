"""Prepare a region for on-demand assessment: cache the GHSL tiles that are only distributed as zips.

    python scripts/prepare_tiles.py LAT LON        (make prepare LAT=.. LON=..)

Downloads (once) the 3″ WGS84 tiles containing the point: GHS-POP 2020 (~120 MB zip) and
GHS-BUILT-S 2020 into data/cache/ghsl. Overture and HRSL need no preparation (windowed reads).
"""

import sys
from pathlib import Path

from pedx.datalake.raster import fetch_ghsl_tile

CACHE = Path(__file__).resolve().parents[1] / "data" / "cache" / "ghsl"

if __name__ == "__main__":
    lat, lon = float(sys.argv[1]), float(sys.argv[2])
    CACHE.mkdir(parents=True, exist_ok=True)
    for prod in ("pop_2020", "built_s_2020"):
        print(prod, "→", fetch_ghsl_tile(prod, lat, lon, CACHE))

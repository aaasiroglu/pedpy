"""pedx.store — the thesis data infrastructure (K-071, docs/32).

Three tiers, one rule each:
  raw/cache  downloaded as-is, never edited, never in git (data/raw, data/cache)
  products   standard tables with a written schema (data/inventory, data/lake/<area>/)
  manifest   every product registered with rows, checksum, inputs, licences and code version (data/manifest.json)

``schema`` holds the contracts, ``manifest`` the registry, ``buildings`` and ``units`` the building and
urban-block layers. ``scripts/check_data.py`` validates everything that is registered.
"""

from .schema import SCHEMAS, validate  # noqa: F401

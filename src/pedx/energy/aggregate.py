"""Building → H3-cell aggregation with explicit energy-sharing modes.

``shared``       buildings in a cell pool generation and demand every hour
                 (virtual/collective self-consumption scenario)
``independent``  every building self-consumes on its own; cell self-consumption
                 is the sum of building-level ``min(G, D)``

Totals of generation and demand are conserved exactly in both modes (T5).
Whether intra-cell sharing is legally possible is a *scenario* question
(see docs/07, C4), not something the model assumes silently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from .load_match import load_match
from .records import BuildingEnergyRecord

__all__ = ["CellEnergy", "aggregate_to_cells"]

SHARING_MODES = ("shared", "independent")


@dataclass
class CellEnergy:
    """Hourly energy of a set of cells (rows) over T steps (columns)."""

    cell_ids: List[str]
    generation_kwh: np.ndarray  # (n, T)
    demand_kwh: np.ndarray  # (n, T)
    independent_self_consumed_kwh: np.ndarray  # (n, T) sum of building-level min(G, D)
    dt_hours: float = 1.0
    attributes: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __post_init__(self) -> None:
        n = len(self.cell_ids)
        if len(set(self.cell_ids)) != n:
            raise ValueError("cell_ids must be unique")
        for name in ("generation_kwh", "demand_kwh", "independent_self_consumed_kwh"):
            arr = np.asarray(getattr(self, name), dtype=float)
            if arr.ndim != 2 or arr.shape[0] != n:
                raise ValueError(f"{name} must have shape (n_cells, T)")
            setattr(self, name, arr)

    @property
    def index(self) -> Dict[str, int]:
        return {c: i for i, c in enumerate(self.cell_ids)}

    def self_consumed(self, sharing: str = "shared") -> np.ndarray:
        if sharing not in SHARING_MODES:
            raise ValueError(f"sharing must be one of {SHARING_MODES}")
        if sharing == "shared":
            return np.minimum(self.generation_kwh, self.demand_kwh)
        return self.independent_self_consumed_kwh

    def metrics(self, sharing: str = "shared", cvar_q: float = 0.99) -> pd.DataFrame:
        """Load-matching indicators per cell as a DataFrame indexed by cell id."""
        sc = None if sharing == "shared" else self.self_consumed(sharing)
        m = load_match(self.generation_kwh, self.demand_kwh, self.dt_hours, cvar_q=cvar_q, self_consumed_kwh=sc)
        df = pd.DataFrame({k: np.atleast_1d(v) for k, v in m.items()}, index=pd.Index(self.cell_ids, name="cell"))
        if not self.attributes.empty:
            df = df.join(self.attributes)
        return df

    def subset(self, cells: Sequence[str]) -> "CellEnergy":
        idx = [self.index[c] for c in cells]
        attrs = self.attributes.loc[list(cells)] if not self.attributes.empty else pd.DataFrame()
        return CellEnergy(
            list(cells),
            self.generation_kwh[idx],
            self.demand_kwh[idx],
            self.independent_self_consumed_kwh[idx],
            self.dt_hours,
            attrs,
        )


def aggregate_to_cells(
    buildings: Sequence[BuildingEnergyRecord],
    resolution: Optional[int] = None,
    cell_of: Optional[Dict[str, str]] = None,
) -> CellEnergy:
    """Aggregate building records into cells.

    Cells come from ``cell_of`` (building_id → cell id) if given, otherwise
    from the H3 cell of each building centroid at ``resolution``.
    """
    if not buildings:
        raise ValueError("no buildings given")
    steps = {b.n_steps for b in buildings}
    dts = {b.dt_hours for b in buildings}
    if len(steps) != 1 or len(dts) != 1:
        raise ValueError("all buildings must share the same series length and dt_hours")
    if cell_of is None:
        if resolution is None:
            raise ValueError("give either resolution (H3) or cell_of")
        from ..spatial.h3grid import assign_cells

        cells = assign_cells([b.lat for b in buildings], [b.lon for b in buildings], resolution)
    else:
        missing = [b.building_id for b in buildings if b.building_id not in cell_of]
        if missing:
            raise KeyError(f"no cell for buildings: {missing[:5]}")
        cells = [cell_of[b.building_id] for b in buildings]

    cell_ids = sorted(set(cells))
    pos = {c: i for i, c in enumerate(cell_ids)}
    rows = np.array([pos[c] for c in cells])
    G = np.stack([b.generation_kwh for b in buildings])
    D = np.stack([b.demand_kwh for b in buildings])
    n, T = len(cell_ids), G.shape[1]
    Gc, Dc, SCi = np.zeros((n, T)), np.zeros((n, T)), np.zeros((n, T))
    np.add.at(Gc, rows, G)
    np.add.at(Dc, rows, D)
    np.add.at(SCi, rows, np.minimum(G, D))

    attrs = pd.DataFrame(
        {
            "cell": cells,
            "n_buildings": 1,
            "footprint_area_m2": [b.footprint_area_m2 for b in buildings],
            "usable_roof_area_m2": [b.usable_roof_area_m2 for b in buildings],
            "installed_pv_area_m2": [b.installed_pv_area_m2 for b in buildings],
        }
    ).groupby("cell").sum()
    return CellEnergy(cell_ids, Gc, Dc, SCi, dt_hours=dts.pop(), attributes=attrs.loc[cell_ids])

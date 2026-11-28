"""Building-level hourly energy records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence, Union

import numpy as np

__all__ = ["BuildingEnergyRecord"]

ArrayLike = Union[np.ndarray, Sequence[float]]


@dataclass
class BuildingEnergyRecord:
    """Hourly PV generation and electricity demand of one building.

    Energy arrays are in kWh per time step of ``dt_hours``. ``lat``/``lon``
    (WGS84, building centroid) are used to assign the building to an H3 cell.
    """

    building_id: str
    lat: float
    lon: float
    generation_kwh: np.ndarray
    demand_kwh: np.ndarray
    footprint_area_m2: float
    usable_roof_area_m2: float
    installed_pv_area_m2: float = 0.0
    dt_hours: float = 1.0
    construction_year: Optional[int] = None
    height_m: Optional[float] = None
    usage_type: str = "residential"
    attributes: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.generation_kwh = np.asarray(self.generation_kwh, dtype=float).ravel()
        self.demand_kwh = np.asarray(self.demand_kwh, dtype=float).ravel()
        g, d = self.generation_kwh, self.demand_kwh
        if g.shape != d.shape:
            raise ValueError(f"[{self.building_id}] generation ({g.size}) and demand ({d.size}) lengths differ")
        if not (np.all(np.isfinite(g)) and np.all(np.isfinite(d))):
            raise ValueError(f"[{self.building_id}] energy series contain NaN/inf")
        if np.any(g < 0) or np.any(d < 0):
            raise ValueError(f"[{self.building_id}] energy series must be non-negative")
        if self.dt_hours <= 0:
            raise ValueError("dt_hours must be positive")
        if min(self.footprint_area_m2, self.usable_roof_area_m2, self.installed_pv_area_m2) < 0:
            raise ValueError("areas must be non-negative")
        if self.installed_pv_area_m2 > self.usable_roof_area_m2 + 1e-9:
            raise ValueError(f"[{self.building_id}] installed PV area exceeds usable roof area")
        if not (-90 <= self.lat <= 90 and -180 <= self.lon <= 180):
            raise ValueError(f"[{self.building_id}] invalid coordinates")

    @classmethod
    def from_irradiance(
        cls,
        building_id: str,
        lat: float,
        lon: float,
        irradiance_kw_m2: ArrayLike,
        demand_kwh: ArrayLike,
        footprint_area_m2: float,
        usable_roof_area_m2: float,
        installed_pv_area_m2: float,
        pv_efficiency: float,
        performance_ratio: float,
        shading: Union[float, ArrayLike] = 1.0,
        dt_hours: float = 1.0,
        **kwargs,
    ) -> "BuildingEnergyRecord":
        """``G_t = I_t * A_pv * eta * PR * s_t * dt`` with ``I_t`` in kW/m² and ``s_t`` in [0, 1]."""
        for name, val in {"pv_efficiency": pv_efficiency, "performance_ratio": performance_ratio}.items():
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        irr = np.asarray(irradiance_kw_m2, dtype=float).ravel()
        s = np.broadcast_to(np.asarray(shading, dtype=float), irr.shape)
        if np.any(irr < 0) or np.any((s < 0) | (s > 1)):
            raise ValueError("irradiance must be >= 0 and shading in [0, 1]")
        gen = irr * installed_pv_area_m2 * pv_efficiency * performance_ratio * s * dt_hours
        rec = cls(
            building_id=building_id,
            lat=lat,
            lon=lon,
            generation_kwh=gen,
            demand_kwh=demand_kwh,
            footprint_area_m2=footprint_area_m2,
            usable_roof_area_m2=usable_roof_area_m2,
            installed_pv_area_m2=installed_pv_area_m2,
            dt_hours=dt_hours,
            **kwargs,
        )
        rec.attributes.setdefault("pv_yield_kwh_per_m2", irr * pv_efficiency * performance_ratio * s * dt_hours)
        return rec

    @property
    def n_steps(self) -> int:
        return int(self.generation_kwh.size)

    @property
    def annual_generation_kwh(self) -> float:
        return float(self.generation_kwh.sum() * 8760.0 / (self.n_steps * self.dt_hours))

    @property
    def annual_demand_kwh(self) -> float:
        return float(self.demand_kwh.sum() * 8760.0 / (self.n_steps * self.dt_hours))

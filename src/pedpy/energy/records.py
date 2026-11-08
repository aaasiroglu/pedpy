"""Building-level hourly energy records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

import numpy as np

__all__ = ["BuildingEnergyRecord"]

ArrayLike = Union[np.ndarray, list, tuple]


@dataclass
class BuildingEnergyRecord:
    """Hourly PV generation and demand of a single building.

    All energy arrays are in kWh per time step of length ``dt_hours``. The
    record carries the geometric/typological attributes needed for the
    block-level criteria (C1 roof yield, C5 thermal proxy).
    """

    building_id: str
    block_id: str
    generation_kwh: np.ndarray
    demand_kwh: np.ndarray
    footprint_area_m2: float
    gross_roof_area_m2: float
    dt_hours: float = 1.0
    construction_year: Optional[int] = None
    height_m: Optional[float] = None
    av_ratio: Optional[float] = None  # envelope area / heated volume [1/m]
    usage_type: str = "residential"
    extra: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.generation_kwh = np.asarray(self.generation_kwh, dtype=float).ravel()
        self.demand_kwh = np.asarray(self.demand_kwh, dtype=float).ravel()
        if self.generation_kwh.shape != self.demand_kwh.shape:
            raise ValueError(
                f"[{self.building_id}] generation ({self.generation_kwh.size}) and "
                f"demand ({self.demand_kwh.size}) series lengths differ"
            )
        if np.any(self.generation_kwh < 0) or np.any(self.demand_kwh < 0):
            raise ValueError(f"[{self.building_id}] energy series must be non-negative")
        if not np.all(np.isfinite(self.generation_kwh)) or not np.all(np.isfinite(self.demand_kwh)):
            raise ValueError(f"[{self.building_id}] energy series contain NaN/inf")
        if self.dt_hours <= 0:
            raise ValueError("dt_hours must be positive")
        if self.footprint_area_m2 < 0 or self.gross_roof_area_m2 < 0:
            raise ValueError("areas must be non-negative")

    # ------------------------------------------------------------------ factories
    @classmethod
    def from_power_kw_m2(
        cls,
        building_id: str,
        block_id: str,
        footprint_area_m2: float,
        gross_roof_area_m2: float,
        roof_utilization_factor: float,
        pv_efficiency: float,
        performance_ratio: float,
        hourly_power_kw_m2: ArrayLike,
        demand_kwh: ArrayLike,
        dt_hours: float = 1.0,
        scalar_shading: float = 1.0,
        hourly_shading: Optional[ArrayLike] = None,
        **attributes,
    ) -> "BuildingEnergyRecord":
        """Build a record from plane-of-array irradiance.

        ``G_t = I_t * A_roof * f_util * eta * PR * s_t * dt``

        where ``I_t`` is the irradiance in kW/m², ``s_t`` the shading factor
        (``scalar_shading`` times the optional ``hourly_shading`` series, both
        in [0, 1]; 1 = unshaded).
        """
        for name, val in {
            "roof_utilization_factor": roof_utilization_factor,
            "pv_efficiency": pv_efficiency,
            "performance_ratio": performance_ratio,
            "scalar_shading": scalar_shading,
        }.items():
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {val}")
        irr = np.asarray(hourly_power_kw_m2, dtype=float).ravel()
        if np.any(irr < 0):
            raise ValueError("irradiance must be non-negative")
        shade = np.full(irr.shape, float(scalar_shading))
        if hourly_shading is not None:
            hs = np.asarray(hourly_shading, dtype=float).ravel()
            if hs.shape != irr.shape:
                raise ValueError("hourly_shading must match the irradiance length")
            if np.any((hs < 0) | (hs > 1)):
                raise ValueError("hourly_shading must be in [0, 1]")
            shade = shade * hs
        usable_area = gross_roof_area_m2 * roof_utilization_factor
        gen = irr * usable_area * pv_efficiency * performance_ratio * shade * dt_hours
        return cls(
            building_id=building_id,
            block_id=block_id,
            generation_kwh=gen,
            demand_kwh=demand_kwh,
            footprint_area_m2=footprint_area_m2,
            gross_roof_area_m2=gross_roof_area_m2,
            dt_hours=dt_hours,
            **attributes,
        )

    # ---------------------------------------------------------------- properties
    @property
    def n_steps(self) -> int:
        return int(self.generation_kwh.size)

    @property
    def annualization_factor(self) -> float:
        """Factor converting the series total to a per-year value."""
        return 8760.0 / (self.n_steps * self.dt_hours)

    @property
    def annual_generation_kwh(self) -> float:
        return float(self.generation_kwh.sum() * self.annualization_factor)

    @property
    def annual_demand_kwh(self) -> float:
        return float(self.demand_kwh.sum() * self.annualization_factor)

    @property
    def net_annual_balance_kwh(self) -> float:
        return self.annual_generation_kwh - self.annual_demand_kwh

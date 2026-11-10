"""Synthetic profiles for tests, examples and controlled experiments.

Everything here is SYNTHETIC and must never be reported as observed data.
Shapes are simple, documented and deterministic (given a seed), so that
verification tests (T1–T5, inverse-solver checks) have known ground truth.
"""

from __future__ import annotations

import numpy as np

__all__ = ["solar_irradiance", "demand_profile", "day_shape"]

HOURS = 8760


def solar_irradiance(lat_deg: float = 41.0, n_hours: int = HOURS, clearness: float = 0.75, seed: int | None = 0) -> np.ndarray:
    """Hourly irradiance on a horizontal plane [kW/m²], from solar geometry.

    ``G = 1.0 * clearness * sin(elevation)^1.15`` with optional day-to-day
    cloudiness noise (multiplicative, mean 1). Standard declination and
    hour-angle formulas; solar time = clock time.
    """
    t = np.arange(n_hours)
    doy = t // 24 + 1
    hour = t % 24 + 0.5
    decl = np.deg2rad(23.45) * np.sin(2 * np.pi * (284 + doy) / 365.0)
    lat = np.deg2rad(lat_deg)
    ha = np.deg2rad(15.0 * (hour - 12.0))
    sin_el = np.sin(lat) * np.sin(decl) + np.cos(lat) * np.cos(decl) * np.cos(ha)
    g = clearness * np.clip(sin_el, 0, None) ** 1.15
    if seed is not None:
        rng = np.random.default_rng(seed)
        daily = np.clip(rng.normal(1.0, 0.25, size=n_hours // 24 + 1), 0.2, 1.3)
        g = g * daily[t // 24]
    return g


def day_shape(kind: str) -> np.ndarray:
    """24-value normalised (sum = 1) daily load shape."""
    h = np.arange(24)
    if kind == "residential":
        s = 0.4 + 0.5 * np.exp(-((h - 8) ** 2) / 4) + 1.0 * np.exp(-((h - 20) ** 2) / 6)
    elif kind == "office":
        s = 0.15 + 1.0 * ((h >= 8) & (h <= 18))
    elif kind == "night":
        s = 0.2 + 1.0 * ((h >= 19) | (h <= 2))
    elif kind == "day":
        s = 0.05 + 1.0 * ((h >= 9) & (h <= 16))
    else:
        raise ValueError(f"unknown shape {kind!r}")
    return s / s.sum()


def demand_profile(annual_kwh: float, kind: str = "residential", n_hours: int = HOURS, weekend_factor: float = 1.0) -> np.ndarray:
    """Hourly demand [kWh] with total ``annual_kwh * n_hours / 8760`` and the given daily shape."""
    shape = np.tile(day_shape(kind), n_hours // 24 + 1)[:n_hours]
    if weekend_factor != 1.0:
        weekend = ((np.arange(n_hours) // 24) % 7) >= 5
        shape = np.where(weekend, shape * weekend_factor, shape)
    total = annual_kwh * n_hours / 8760.0
    return shape / shape.sum() * total

"""Array-backend helpers and smooth (differentiable) relaxations.

Every physics function in pedx is written once against an *array namespace*
``xp`` that is either :mod:`numpy` or :mod:`jax.numpy`, chosen from the input
arrays. NumPy gives exact, fast forward evaluation; JAX gives gradients through
the very same code path (used by :mod:`pedx.inverse`).

Smooth relaxations
------------------
``smooth_min(x, y, tau)`` is the log-sum-exp soft minimum

    softmin_tau(x, y) = -tau * log(exp(-x/tau) + exp(-y/tau))

It is exact for ``tau == 0`` and satisfies the *provable* bound

    min(x, y) - tau*ln2 <= softmin_tau(x, y) <= min(x, y).

Summed over T time steps, the self-consumed energy therefore deviates from its
exact value by at most ``T * tau * ln2``. :func:`tau_for_ssr_tolerance` turns a
user-facing tolerance on SSR into the corresponding ``tau``.
"""

from __future__ import annotations

import math

import numpy as np

__all__ = [
    "get_xp",
    "is_jax_array",
    "smooth_min",
    "smooth_relu",
    "smooth_clip01",
    "tau_for_ssr_tolerance",
]


def is_jax_array(a) -> bool:
    mod = type(a).__module__
    return mod.startswith("jax") or mod.startswith("jaxlib")


def get_xp(*arrays):
    """Return ``jax.numpy`` if any argument is a JAX array/tracer, else NumPy."""
    for a in arrays:
        if is_jax_array(a):
            import jax.numpy as jnp

            return jnp
    return np


def smooth_min(x, y, tau: float = 0.0):
    """Element-wise (soft) minimum; exact when ``tau == 0``."""
    xp = get_xp(x, y)
    if tau == 0:
        return xp.minimum(x, y)
    return -tau * xp.logaddexp(-x / tau, -y / tau)


def smooth_relu(x, tau: float = 0.0):
    """``max(x, 0)``; softplus relaxation when ``tau > 0`` (upper bound, error <= tau*ln2)."""
    xp = get_xp(x)
    if tau == 0:
        return xp.maximum(x, 0.0)
    return tau * xp.logaddexp(x / tau, 0.0)


def smooth_clip01(z, sharpness: float = 0.0):
    """Clip to [0, 1]; smooth version ``(sp(k z) - sp(k(z-1))) / k`` when ``sharpness > 0``."""
    xp = get_xp(z)
    if sharpness == 0:
        return xp.clip(z, 0.0, 1.0)
    k = sharpness
    return (xp.logaddexp(k * z, 0.0) - xp.logaddexp(k * (z - 1.0), 0.0)) / k


def tau_for_ssr_tolerance(demand_kwh, ssr_tolerance: float) -> float:
    """Largest ``tau`` guaranteeing ``|SSR_smooth - SSR_exact| <= ssr_tolerance``.

    From the soft-min bound: ``|ΔSSR| <= T*tau*ln2 / sum(D) = tau*ln2 / mean(D)``.
    """
    if ssr_tolerance <= 0:
        return 0.0
    mean_d = float(np.mean(np.asarray(demand_kwh)))
    if mean_d <= 0:
        raise ValueError("demand must have a positive mean")
    return ssr_tolerance * mean_d / math.log(2.0)

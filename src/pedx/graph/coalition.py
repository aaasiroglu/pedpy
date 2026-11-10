"""Energy-sharing coalitions of cells and their exact Shapley attribution.

The characteristic function is the hourly self-consumed energy of a coalition
that pools generation and demand:

    v(S) = Σ_t min( Σ_{i∈S} G_i,t , Σ_{i∈S} D_i,t )

``v`` is *not additive* – hourly complementarity makes ``v(S ∪ T)`` exceed
``v(S) + v(T)`` – which is exactly why classical additive regionalisation
objectives do not fit PED boundary design (docs/07, E3). It is superadditive,
because ``min(a+b, c+d) >= min(a, c) + min(b, d)``; hence every Shapley value is
individually rational: ``phi_i >= v({i})``.

The Shapley value answers the graph-XAI question *"how much of the cluster's
self-sufficiency is due to cell i?"* and doubles as a fair benefit-sharing key
for energy communities.
"""

from __future__ import annotations

from math import factorial
from typing import Sequence

import numpy as np
import pandas as pd

__all__ = ["coalition_values", "shapley_self_consumption"]


def _membership(n: int) -> np.ndarray:
    masks = np.arange(1 << n, dtype=np.int64)
    return ((masks[:, None] >> np.arange(n)[None, :]) & 1).astype(np.float64)


def coalition_values(G: np.ndarray, D: np.ndarray, chunk: int = 256) -> np.ndarray:
    """``v(S)`` for all ``2^n`` coalitions (index = bitmask over rows of G/D)."""
    G = np.asarray(G, float)
    D = np.asarray(D, float)
    if G.shape != D.shape or G.ndim != 2:
        raise ValueError("G and D must have the same (n, T) shape")
    n = G.shape[0]
    M = _membership(n)
    out = np.empty(M.shape[0])
    for s in range(0, M.shape[0], chunk):
        Mc = M[s : s + chunk]
        out[s : s + chunk] = np.minimum(Mc @ G, Mc @ D).sum(axis=1)
    return out


def shapley_self_consumption(
    G: np.ndarray,
    D: np.ndarray,
    names: Sequence[str] | None = None,
    max_players: int = 14,
) -> pd.DataFrame:
    """Exact Shapley values of the self-consumption game (``n <= max_players``).

    Returns per cell: ``shapley_kwh``, ``standalone_kwh`` (= v({i})),
    ``sharing_gain_kwh`` (= phi - standalone, >= 0) and ``share`` of v(N).
    """
    G = np.asarray(G, float)
    n = G.shape[0]
    if n > max_players:
        raise ValueError(f"exact Shapley limited to {max_players} players (got {n}); 2^n coalitions are enumerated")
    v = coalition_values(G, D)
    masks = np.arange(1 << n)
    sizes = np.array([bin(m).count("1") for m in masks])
    weight = np.array([factorial(s) * factorial(n - s - 1) / factorial(n) for s in range(n)])
    phi = np.empty(n)
    for i in range(n):
        bit = 1 << i
        without = masks[(masks & bit) == 0]
        phi[i] = float((weight[sizes[without]] * (v[without | bit] - v[without])).sum())
    standalone = v[1 << np.arange(n)]
    total = v[-1]
    idx = pd.Index(list(names) if names is not None else range(n), name="cell")
    return pd.DataFrame(
        {
            "shapley_kwh": phi,
            "standalone_kwh": standalone,
            "sharing_gain_kwh": phi - standalone,
            "share": phi / total if total > 0 else np.nan,
        },
        index=idx,
    )

"""Explainability layer of pedx.

* :func:`contributions`            exact additive attribution of the readiness score
* :func:`rank_intervals`           rank uncertainty under weight uncertainty (SMAA-style)
* :func:`inverse_weight_stability` minimal policy change that alters the leader
* :func:`shapley_self_consumption` graph-XAI: each cell's share of cluster self-sufficiency
* ``InverseEngine.marginal_value`` gradient XAI: score gain per € for each physical lever
"""

from ..graph.coalition import shapley_self_consumption
from ..index.readiness import contributions, rank_intervals
from .policy import inverse_weight_stability

__all__ = ["contributions", "inverse_weight_stability", "rank_intervals", "shapley_self_consumption"]

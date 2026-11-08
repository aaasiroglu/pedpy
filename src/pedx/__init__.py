"""pedx – explainable, physics-coupled decision support for Positive Energy Districts.

Core idea: compute hourly energy balances of buildings from open data,
aggregate them on H3 hexagons, score cells with an *absolute* PED readiness
index, explain the scores, grow PED boundaries on the hexagon graph, and solve
inverse problems in the space of physical interventions.

Subpackages
-----------
energy    building records, hourly load matching, H3 aggregation
spatial   H3 indexing and adjacency
index     absolute readiness index, exact contributions, rank intervals
mcdm      set-relative views: CRITIC, Entropy, BWM, WSM, MARCOS, TOPSIS
graph     coalition game, exact Shapley, PED boundary growth and baselines
inverse   physics-coupled intervention model and differentiable inverse engine
xai       explainability entry points
synthetic documented synthetic profiles for tests and examples
"""

__version__ = "0.1.0.dev0"

from . import energy, graph, index, mcdm, spatial, synthetic, xai  # noqa: F401

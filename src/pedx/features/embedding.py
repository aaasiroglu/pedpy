"""Hex "signature" embedding: PCA over all standardised G1 features of a cell (K-037).

Every cell becomes a point in a low-dimensional space that summarises *all* raster and vector
layers (built form, morphology, POI, mobility, environment). Components are interpretable through
their loadings (top features per component are reported) — an explainable alternative to opaque
image embeddings; image/VLM embeddings can be appended as further columns later.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

__all__ = ["pca_embedding"]


def pca_embedding(F: pd.DataFrame, cols: Sequence[str], k: int = 5) -> Tuple[pd.DataFrame, Dict[str, object]]:
    X = F[list(cols)].astype(float)
    keep = [c for c in X if X[c].notna().sum() >= max(5, len(X) // 2) and X[c].std(skipna=True) > 1e-9 * max(1.0, abs(X[c].mean()))]  # drop constant layers
    X = X[keep]
    X = X.fillna(X.median())
    Z = (X - X.mean()) / X.std(ddof=0)
    U, S, Vt = np.linalg.svd(Z.to_numpy(), full_matrices=False)
    k = min(k, Vt.shape[0])
    scores = U[:, :k] * S[:k]
    var = S**2 / (S**2).sum()
    emb = pd.DataFrame(scores, index=F.index, columns=[f"emb_pca_{i + 1}" for i in range(k)])
    loadings: List[Dict[str, object]] = []
    for i in range(k):
        v = pd.Series(Vt[i], index=keep)
        top = v.reindex(v.abs().sort_values(ascending=False).index[:6])
        loadings.append({"component": f"emb_pca_{i + 1}", "explained_variance": round(float(var[i]), 4),
                         "top_loadings": [{"feature": f, "loading": round(float(l), 3)} for f, l in top.items()]})
    return emb, {"n_features": len(keep), "features": keep, "components": loadings}

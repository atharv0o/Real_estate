from __future__ import annotations

import hashlib
from typing import Iterable

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore


_MODEL = None
_DIMENSION = 384


def _load_model():
    global _MODEL
    if _MODEL is None and SentenceTransformer is not None:
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def _fallback_embedding(text: str, dim: int = _DIMENSION) -> np.ndarray:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    seed_values = list(digest) * ((dim // len(digest)) + 1)
    vector = np.array(seed_values[:dim], dtype="float32")
    norm = np.linalg.norm(vector)
    return vector if norm == 0 else vector / norm


def get_embeddings(texts: Iterable[str]):
    items = list(texts)
    model = _load_model()
    if model is not None:
        return model.encode(items)
    return np.array([_fallback_embedding(text) for text in items], dtype="float32")

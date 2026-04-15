from __future__ import annotations

from typing import Any

import numpy as np

from rag_engine.embeddings.embedder import get_embeddings
from rag_engine.embeddings.vector_store import VectorStore


def _normalize_location(value: Any) -> str:
    return str(value or "").strip().lower()


def retrieve(query, vector_store: VectorStore, user_location: str | None = None):
    query_embedding = get_embeddings([query])[0]
    candidate_indices = list(range(len(vector_store.texts)))

    if user_location:
        normalized_user_location = _normalize_location(user_location)
        exact_matches = [
            index
            for index, metadata in enumerate(vector_store.metadata)
            if _normalize_location(metadata.get("location")) == normalized_user_location
        ]
        if not exact_matches:
            exact_matches = [
                index
                for index, metadata in enumerate(vector_store.metadata)
                if normalized_user_location and normalized_user_location in _normalize_location(metadata.get("location"))
            ]

        if exact_matches:
            candidate_indices = exact_matches

    if not candidate_indices:
        return []

    embeddings = vector_store._embeddings[candidate_indices]
    if len(embeddings) == 0:
        return []

    distances = np.linalg.norm(embeddings - query_embedding, axis=1)
    top_indices = np.argsort(distances)[: min(5, len(candidate_indices))]
    return [vector_store.texts[candidate_indices[index]] for index in top_indices]
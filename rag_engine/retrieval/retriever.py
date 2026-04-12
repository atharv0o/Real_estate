from __future__ import annotations

from rag_engine.embeddings.embedder import get_embeddings


def retrieve(query, vector_store):
    query_embedding = get_embeddings([query])[0]
    return vector_store.search(query_embedding)

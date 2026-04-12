from __future__ import annotations

import os
from pathlib import Path

from rag_engine.embeddings.embedder import get_embeddings
from rag_engine.embeddings.vector_store import VectorStore
from rag_engine.generation.llm_client import generate_response
from rag_engine.generation.prompt_templates import build_prompt
from rag_engine.retrieval.retriever import retrieve


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = Path(os.getenv("VECTOR_INDEX_PATH", PROJECT_ROOT / "rag_engine" / "storage" / "property_index.faiss"))
METADATA_PATH = Path(os.getenv("VECTOR_METADATA_PATH", PROJECT_ROOT / "rag_engine" / "storage" / "property_documents.json"))
VECTOR_DIM = int(os.getenv("VECTOR_DIM", "384"))
DEFAULT_DOCS = [
    "Land prices in Pune micro-markets vary by road connectivity and title clarity.",
    "Registry verified land parcels are typically more trustworthy for due diligence workflows.",
    "Plots near transport corridors often carry higher redevelopment potential.",
]

_vector_store: VectorStore | None = None
_last_loaded_signature: tuple[float, float] | None = None


def _file_signature() -> tuple[float, float]:
    index_mtime = INDEX_PATH.stat().st_mtime if INDEX_PATH.exists() else 0.0
    metadata_mtime = METADATA_PATH.stat().st_mtime if METADATA_PATH.exists() else 0.0
    return (index_mtime, metadata_mtime)


def _build_default_store() -> VectorStore:
    store = VectorStore(dim=VECTOR_DIM, index_path=INDEX_PATH, metadata_path=METADATA_PATH)
    if not store.texts:
        embeddings = get_embeddings(DEFAULT_DOCS)
        store.upsert(
            ids=[f"default-{index}" for index in range(len(DEFAULT_DOCS))],
            embeddings=embeddings,
            texts=DEFAULT_DOCS,
            metadata=[{"source": "bootstrap"} for _ in DEFAULT_DOCS],
        )
    return store


def refresh_vector_store(force: bool = False) -> VectorStore:
    global _vector_store, _last_loaded_signature

    signature = _file_signature()
    if force or _vector_store is None or _last_loaded_signature != signature:
        _vector_store = _build_default_store()
        _last_loaded_signature = _file_signature()
    return _vector_store


def run_rag(query):
    vector_store = refresh_vector_store()
    docs = retrieve(query, vector_store)
    prompt = build_prompt(query, docs)
    return generate_response(prompt)

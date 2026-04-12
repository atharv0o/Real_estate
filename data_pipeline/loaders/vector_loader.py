from __future__ import annotations

import requests

from data_pipeline.config import PipelineSettings
from rag_engine.embeddings.embedder import get_embeddings
from rag_engine.embeddings.vector_store import VectorStore
from rag_engine.pipeline.rag_pipeline import refresh_vector_store
from shared.logger import get_logger


logger = get_logger(__name__)


def _build_document(record: dict) -> str:
    description = str(record.get("description") or "").strip()
    location = str(record.get("location") or "").strip()
    title = str(record.get("title") or "").strip()
    return "\n".join(part for part in [title, location, description] if part)


def load_vectors(records: list[dict], settings: PipelineSettings) -> int:
    if not records:
        return 0

    texts = [_build_document(record) for record in records]
    ids = [record["source_record_hash"] for record in records]
    metadata = [
        {
            "title": record["title"],
            "location": record["location"],
            "price_numeric": record.get("price_numeric"),
            "source": record["source"],
            "lat": record.get("lat"),
            "lng": record.get("lng"),
        }
        for record in records
    ]

    embeddings = get_embeddings(texts)
    vector_store = VectorStore(
        dim=settings.vector_dim,
        index_path=settings.vector_index_path,
        metadata_path=settings.vector_metadata_path,
    )
    vector_store.upsert(ids=ids, embeddings=embeddings, texts=texts, metadata=metadata)
    refresh_vector_store(force=True)
    _notify_rag_service(settings)
    logger.info("Stored %s vector documents.", len(texts))
    return len(texts)


def _notify_rag_service(settings: PipelineSettings) -> None:
    if not settings.rag_refresh_url:
        return
    try:
        response = requests.post(settings.rag_refresh_url, timeout=5)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("RAG refresh endpoint call failed: %s", exc)

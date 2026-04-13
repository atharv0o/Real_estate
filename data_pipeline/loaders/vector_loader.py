from __future__ import annotations

import requests

from data_pipeline.config import PipelineSettings
from data_pipeline.logging_utils import get_logger


logger = get_logger(__name__)


def _build_document(record: dict) -> str:
    description = str(record.get("description") or "").strip()
    location = str(record.get("location") or "").strip()
    title = str(record.get("title") or "").strip()
    return "\n".join(part for part in [title, location, description] if part)


def load_vectors(records: list[dict], settings: PipelineSettings) -> int:
    if not records:
        return 0

    _notify_rag_service(settings)
    logger.info("Requested RAG refresh for %s records.", len(records))
    return len(records)


def _notify_rag_service(settings: PipelineSettings) -> None:
    if not settings.rag_refresh_url:
        return
    try:
        response = requests.post(settings.rag_refresh_url, timeout=5)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("RAG refresh endpoint call failed: %s", exc)

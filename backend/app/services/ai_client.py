from __future__ import annotations

import os
from typing import Any

import requests

from app.core.logging import get_logger


RAG_API = os.getenv("RAG_API", "http://127.0.0.1:8001").rstrip("/")
RAG_URL = os.getenv("RAG_QUERY_URL", f"{RAG_API}/rag-query")
logger = get_logger(__name__)


def ask_ai(
    query: str,
    *,
    location: str | None = None,
    property_context: dict[str, Any] | None = None,
) -> dict:
    try:
        payload: dict[str, Any] = {"query": query}
        if location:
            payload["location"] = location
        if property_context:
            payload["property_context"] = property_context

        logger.debug(
            "Sending RAG request: location=%s has_property_context=%s",
            location,
            bool(property_context),
        )
        response = requests.post(RAG_URL, json=payload, timeout=5)
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {"answer": str(payload)}
    except Exception as exc:
        return {"error": str(exc)}

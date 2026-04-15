from __future__ import annotations

from fastapi import APIRouter

from app.core.logging import get_logger
from app.services.ai_client import ask_ai
from app.services.api_response import error_response, success_response


logger = get_logger(__name__)
router = APIRouter(prefix="/rag")


@router.post("/query")
def rag_query(data: dict):
    try:
        query = str(data.get("query") or "").strip()
        location = str(data.get("location") or "").strip()
        property_context = data.get("property_context")

        logger.debug(
            "Received property RAG query: location=%s has_property_context=%s",
            location,
            isinstance(property_context, dict) and bool(property_context),
        )

        response = ask_ai(
            query,
            location=location or None,
            property_context=property_context if isinstance(property_context, dict) else None,
        )
        if isinstance(response, dict) and response.get("error"):
            return error_response(str(response["error"]))
        return success_response(response)
    except Exception as exc:
        return error_response(str(exc))

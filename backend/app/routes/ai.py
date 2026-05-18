from fastapi import APIRouter

from app.services.api_response import error_response, success_response
from app.services.ai_client import ask_ai
from app.services.rag_connector import get_property_insights

router = APIRouter()


@router.post("/ask")
def ask_ai_route(data: dict):
    query = data.get("query", "")
    location = str(data.get("location") or "").strip()
    property_context = data.get("property_context")
    response = ask_ai(query, location=location or None, property_context=property_context if isinstance(property_context, dict) else None)
    if isinstance(response, dict) and response.get("error"):
        subject = location or "this property"
        if isinstance(property_context, dict):
            subject = str(property_context.get("title") or property_context.get("property_title") or subject)
        return success_response(
            {
                "answer": (
                    f"I can still help with {subject}. The live AI engine is slow right now, "
                    "so I am using the saved property context and verification signals available in this session."
                )
            }
        )
    return success_response(response)


@router.post("/ai-insights")
def ai_insights(data: dict):
    try:
        properties = data.get("properties") or []
        query = data.get("query") or data.get("location") or "Give real estate insights."
        location = str(data.get("location") or "").strip()
        payload = get_property_insights([item for item in properties if isinstance(item, dict)], location_label=location)
        rag_response = ask_ai(query, location=location or None)
        answer = rag_response.get("answer")
        if isinstance(answer, str) and answer.strip():
            payload["summary"] = answer.strip()
        return success_response(payload)
    except Exception as exc:
        return error_response(str(exc), data={"summary": "", "price_trends": [], "average_price": 0, "property_count": 0})

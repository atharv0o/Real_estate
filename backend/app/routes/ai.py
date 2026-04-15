from fastapi import APIRouter

from app.services.api_response import error_response, success_response
from app.services.ai_client import ask_ai
from app.services.rag_connector import get_property_insights

router = APIRouter()


@router.post("/ask")
def ask_ai_route(data: dict):
    query = data.get("query", "")
    return success_response(ask_ai(query))


@router.post("/ai-insights")
def ai_insights(data: dict):
    try:
        properties = data.get("properties") or []
        query = data.get("query") or data.get("location") or "Give real estate insights."
        payload = get_property_insights([item for item in properties if isinstance(item, dict)])
        rag_response = ask_ai(query)
        answer = rag_response.get("answer")
        if isinstance(answer, str) and answer.strip():
            payload["summary"] = answer.strip()
        return success_response(payload)
    except Exception as exc:
        return error_response(str(exc), data={"summary": "", "price_trends": [], "average_price": 0, "property_count": 0})

from statistics import mean

from fastapi import APIRouter

from app.services.api_response import error_response, success_response
from app.services.ai_client import ask_ai

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
        rag_response = ask_ai(query)
        answer = rag_response.get("answer") or rag_response.get("error") or "No AI summary available."

        numeric_prices = [
            float(item["price_numeric"])
            for item in properties
            if isinstance(item, dict) and item.get("price_numeric") is not None
        ]
        average_price = round(mean(numeric_prices), 2) if numeric_prices else 0.0
        price_trends = [
            {
                "label": item.get("title", f"Property {index + 1}")[:24],
                "value": float(item.get("price_numeric") or 0),
            }
            for index, item in enumerate(properties[:6])
            if isinstance(item, dict)
        ]

        payload = {
            "summary": answer,
            "price_trends": price_trends,
            "average_price": average_price,
            "property_count": len(properties),
        }
        return success_response(payload)
    except Exception as exc:
        return error_response(str(exc), data={"summary": "", "price_trends": [], "average_price": 0, "property_count": 0})

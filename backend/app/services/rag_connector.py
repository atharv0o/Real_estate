from __future__ import annotations

import os
import statistics
from typing import Any

import requests

from app.core.logging import get_logger

logger = get_logger(__name__)

RAG_API = os.getenv("RAG_API", "http://localhost:8001").rstrip("/")
RAG_QUERY_URL = os.getenv("RAG_QUERY_URL", f"{RAG_API}/rag-query")
RAG_REFRESH_URL = os.getenv("RAG_REFRESH_URL", f"{RAG_API}/refresh-index")


def call_rag(query: str) -> dict:
    response = requests.post(RAG_QUERY_URL, json={"query": query}, timeout=5)
    response.raise_for_status()
    return response.json()


def refresh_rag_index() -> dict:
    response = requests.post(RAG_REFRESH_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def get_property_insights(properties: list[dict[str, Any]]) -> dict[str, Any]:
    if not properties:
        return {
            "avg_price": 0,
            "average_price": 0.0,
            "price_trend": "flat",
            "investment_score": 0.0,
            "summary": "No properties in scope for insights.",
            "price_trends": [],
            "property_count": 0,
        }

    prices: list[float] = []
    for p in properties:
        try:
            v = float(p.get("price_numeric") or 0)
            if v > 0:
                prices.append(v)
        except (TypeError, ValueError):
            continue

    avg_price = int(statistics.mean(prices)) if prices else 0
    half = max(1, len(prices) // 2)
    first_avg = statistics.mean(prices[:half]) if len(prices) > 1 else avg_price
    second_avg = statistics.mean(prices[half:]) if len(prices) > 1 else avg_price
    if second_avg > first_avg * 1.05:
        price_trend = "increasing"
    elif second_avg < first_avg * 0.95:
        price_trend = "decreasing"
    else:
        price_trend = "flat"

    density = min(len(properties) / 50.0, 1.0)
    price_dispersion = (statistics.pstdev(prices) / avg_price) if len(prices) > 1 and avg_price else 0.5
    investment_score = round(min(10.0, 4.0 + density * 4.0 + (1.0 - min(price_dispersion, 1.0)) * 2.0), 1)

    price_trends = [
        {"label": f"P{i + 1}", "value": int(prices[i])}
        for i in range(min(6, len(prices)))
    ]

    summary = (
        f"Sample of {len(properties)} listings: average ask ₹{avg_price:,}. "
        f"Trend appears {price_trend} within this slice. Investment score {investment_score}/10."
    )

    try:
        rag_payload = call_rag(
            f"Summarize real-estate investment outlook for this micro-market in 2 sentences. "
            f"Average price {avg_price}, {len(properties)} comps, trend {price_trend}."
        )
        ans = rag_payload.get("answer")
        if isinstance(ans, str) and ans.strip():
            summary = ans.strip()
    except Exception as exc:
        logger.warning("RAG insight enrichment failed, using local summary: %s", exc)

    return {
        "avg_price": avg_price,
        "average_price": float(avg_price),
        "price_trend": price_trend,
        "investment_score": investment_score,
        "summary": summary,
        "price_trends": price_trends,
        "property_count": len(properties),
    }

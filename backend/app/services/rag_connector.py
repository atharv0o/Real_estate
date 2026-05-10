from __future__ import annotations

import hashlib
import json
import os
import statistics
from typing import Any

import requests

from app.core.logging import get_logger
from app.services.search_cache import get_cached, make_cache_key, set_cached

logger = get_logger(__name__)

RAG_API = os.getenv("RAG_API", "http://localhost:8001").rstrip("/")
RAG_QUERY_URL = os.getenv("RAG_QUERY_URL", f"{RAG_API}/rag-query")
RAG_REFRESH_URL = os.getenv("RAG_REFRESH_URL", f"{RAG_API}/refresh-index")
INSIGHT_CACHE_TTL_SECONDS = float(os.getenv("SEARCH_CACHE_TTL_SECONDS", "300"))


def call_rag(query: str, *, location: str | None = None, property_context: dict[str, Any] | None = None) -> dict:
    payload: dict[str, Any] = {"query": query}
    if location:
        payload["location"] = location
    if property_context:
        payload["property_context"] = property_context

    logger.debug("Calling RAG API with location=%s has_property_context=%s", location, bool(property_context))
    response = requests.post(RAG_QUERY_URL, json=payload, timeout=5)
    response.raise_for_status()
    return response.json()


def refresh_rag_index() -> dict:
    response = requests.post(RAG_REFRESH_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def _property_signature(properties: list[dict[str, Any]], location_label: str) -> str:
    rows = []
    for item in properties:
        rows.append(
            {
                "id": item.get("id"),
                "external_id": item.get("external_id"),
                "title": item.get("title"),
                "price_numeric": item.get("price_numeric"),
                "location": item.get("location"),
                "lat": item.get("lat"),
                "lng": item.get("lng"),
            }
        )
    serialized = json.dumps({"location": location_label, "rows": rows}, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _local_property_insights(properties: list[dict[str, Any]], location_label: str = "") -> dict[str, Any]:
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
        f"Sample of {len(properties)} listings: average ask Rs. {avg_price:,}. "
        f"Trend appears {price_trend} within this slice. Investment score {investment_score}/10."
    )

    return {
        "avg_price": avg_price,
        "average_price": float(avg_price),
        "price_trend": price_trend,
        "investment_score": investment_score,
        "summary": summary,
        "price_trends": price_trends,
        "property_count": len(properties),
    }


def get_property_insights(
    properties: list[dict[str, Any]],
    location_label: str = "",
    *,
    enrich_with_rag: bool = True,
) -> dict[str, Any]:
    signature = _property_signature(properties, location_label)
    cache_key = make_cache_key("ai:insights", {"signature": signature})
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    payload = _local_property_insights(properties, location_label)
    if enrich_with_rag and properties:
        try:
            rag_payload = call_rag(
                f"Summarize real-estate investment outlook for this micro-market in 2 sentences. "
                f"Average price {payload.get('avg_price', 0)}, {len(properties)} comps, trend {payload.get('price_trend', 'flat')}.",
                location=location_label or None,
                property_context={
                    "location": location_label,
                    "property_count": len(properties),
                    "average_price": payload.get("avg_price", 0),
                    "price_trend": payload.get("price_trend", "flat"),
                },
            )
            ans = rag_payload.get("answer")
            if isinstance(ans, str) and ans.strip():
                payload["summary"] = ans.strip()
        except Exception as exc:
            logger.warning("RAG insight enrichment failed, using local summary: %s", exc)

    set_cached(cache_key, payload, ttl_seconds=INSIGHT_CACHE_TTL_SECONDS)
    return payload

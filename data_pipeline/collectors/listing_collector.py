from __future__ import annotations

from typing import Any

import requests

from data_pipeline.config import PipelineSettings
from shared.logger import get_logger


logger = get_logger(__name__)


DEFAULT_LISTINGS: list[dict[str, Any]] = [
    {
        "title": "Highway Frontage Plot",
        "price": "₹4,500,000",
        "location": "Sector 21, Pune, Maharashtra",
        "area_sqft": 2400,
        "source": "simulated_portal",
        "description": "Corner residential plot near the ring road with clear title.",
    },
    {
        "title": "Agricultural Land Parcel",
        "price": "3200000",
        "location": "Shirwal, Satara, Maharashtra",
        "area_sqft": 18000,
        "source": "simulated_portal",
        "description": "Fertile agricultural land with road touch access and borewell.",
    },
    {
        "title": "Commercial Redevelopment Site",
        "price": "$125000",
        "location": "Baner, Pune, Maharashtra",
        "area_sqft": 3200,
        "source": "simulated_broker_feed",
        "description": "Commercial redevelopment parcel close to the metro corridor.",
    },
    {
        "title": "Commercial Redevelopment Site",
        "price": "$125,000",
        "location": "Baner, Pune, Maharashtra",
        "area_sqft": 3200,
        "source": "simulated_broker_feed",
        "description": "Duplicate broker entry for the same commercial redevelopment parcel.",
    },
]


def _normalize_listing(item: dict[str, Any], default_source: str = "external_feed") -> dict[str, Any]:
    return {
        "title": str(item.get("title", "")).strip(),
        "price": str(item.get("price", "")).strip(),
        "location": str(item.get("location", "")).strip(),
        "area_sqft": item.get("area_sqft"),
        "source": str(item.get("source") or default_source).strip(),
        "description": str(item.get("description", "")).strip(),
    }


def collect_listings(settings: PipelineSettings) -> list[dict[str, Any]]:
    if not settings.listing_source_url:
        logger.info("LISTING_SOURCE_URL not configured, using simulated listing feed.")
        return [_normalize_listing(item, default_source="simulated_feed") for item in DEFAULT_LISTINGS]

    try:
        response = requests.get(settings.listing_source_url, timeout=settings.listing_request_timeout)
        response.raise_for_status()
        payload = response.json()
        items = payload.get("listings", payload) if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            raise ValueError("Listing source response must be a JSON list or {listings: []}.")
        normalized = [_normalize_listing(item) for item in items if isinstance(item, dict)]
        logger.info("Collected %s listing records from %s.", len(normalized), settings.listing_source_url)
        return normalized
    except Exception as exc:
        logger.warning("Listing source fetch failed: %s. Falling back to simulated data.", exc)
        return [_normalize_listing(item, default_source="simulated_feed") for item in DEFAULT_LISTINGS]

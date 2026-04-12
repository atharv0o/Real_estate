from __future__ import annotations

import hashlib

from app.services.geo_service import get_location_coordinates


def resolve_location(query: str) -> dict:
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("Location query is required")

    stored = get_location_coordinates(normalized_query)
    if stored:
        return {
            "query": normalized_query,
            "label": stored["location"],
            "lat": stored["lat"],
            "lng": stored["lng"],
            "source": "database",
        }

    digest = hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()
    lat = round(18.5204 + (int(digest[:8], 16) % 1000) / 10000, 6)
    lng = round(73.8567 + (int(digest[8:16], 16) % 1000) / 10000, 6)
    return {
        "query": normalized_query,
        "label": normalized_query,
        "lat": lat,
        "lng": lng,
        "source": "fallback",
    }

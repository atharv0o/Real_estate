from __future__ import annotations

import hashlib
import os
from typing import Any

import requests

from app.core.logging import get_logger
from app.services.search_cache import get_cached, make_cache_key, set_cached
from app.services.geo_service import get_location_coordinates
from app.services.search_index import resolve_location_from_index

logger = get_logger(__name__)


def _resolve_with_google_geocoding(query: str) -> dict[str, Any] | None:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_GEOCODING_API_KEY")
    if not api_key:
        return None

    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": query, "key": api_key},
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        logger.warning("Google geocoding lookup failed for %s: %s", query, exc)
        return None

    results = payload.get("results") or []
    if payload.get("status") != "OK" or not results:
        return None

    first = results[0]
    location = first.get("geometry", {}).get("location", {})
    lat = location.get("lat")
    lng = location.get("lng")
    if lat is None or lng is None:
        return None

    return {
        "query": query,
        "label": first.get("formatted_address") or query,
        "lat": round(float(lat), 6),
        "lng": round(float(lng), 6),
        "source": "google_geocoding",
    }


def resolve_location(query: str) -> dict:
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("Location query is required")

    cache_key = make_cache_key("location:resolve", {"query": normalized_query.lower()})
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    logger.debug("Resolving location=%s", normalized_query)
    stored = None
    try:
        stored = get_location_coordinates(normalized_query)
    except Exception as exc:
        logger.warning("Location lookup via database failed, using deterministic fallback: %s", exc)

    if stored:
        payload = {
            "query": normalized_query,
            "label": stored["location"],
            "lat": stored["lat"],
            "lng": stored["lng"],
            "source": "database",
        }
        set_cached(cache_key, payload, ttl_seconds=1800)
        return payload

    try:
        dataset_match = resolve_location_from_index(normalized_query)
    except Exception as exc:
        logger.warning("Location lookup via dataset failed, using deterministic fallback: %s", exc)
        dataset_match = None

    if dataset_match:
        set_cached(cache_key, dataset_match, ttl_seconds=1800)
        return dataset_match

    google_match = None
    try:
        google_match = _resolve_with_google_geocoding(normalized_query)
    except Exception as exc:
        logger.warning("Location lookup via Google geocoding failed, using deterministic fallback: %s", exc)

    if google_match:
        set_cached(cache_key, google_match, ttl_seconds=1800)
        return google_match

    digest = hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()
    lat = round(18.5204 + (int(digest[:8], 16) % 1000) / 10000, 6)
    lng = round(73.8567 + (int(digest[8:16], 16) % 1000) / 10000, 6)
    payload = {
        "query": normalized_query,
        "label": normalized_query,
        "lat": lat,
        "lng": lng,
        "source": "fallback",
    }
    set_cached(cache_key, payload, ttl_seconds=1800)
    return payload

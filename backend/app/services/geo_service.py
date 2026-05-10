from __future__ import annotations

from app.core.logging import get_logger
from app.db.postgres import fetch_all_dicts, fetch_one_dict
from app.services.search_cache import get_cached, make_cache_key, set_cached

logger = get_logger(__name__)


def get_coordinates(query: str) -> dict:
    """Resolve a free-text location query to lat/lng (DB-backed or deterministic fallback)."""
    from app.services.maps_service import resolve_location

    logger.debug("Resolving coordinates for query=%s", query)
    result = resolve_location(query)
    logger.debug("Resolved coordinates for query=%s -> %s", query, result.get("source"))
    return result


def get_property_coordinates(property_id: int | None = None, external_id: str | None = None) -> dict | None:
    if property_id is None and external_id is None:
        raise ValueError("property_id or external_id is required")

    logger.debug("Fetching property coordinates property_id=%s external_id=%s", property_id, external_id)
    if property_id is not None:
        return fetch_one_dict(
            """
            SELECT id, external_id, title, location, latitude AS lat, longitude AS lng
            FROM land_listings
            WHERE id = %s
            """,
            (property_id,),
        )

    return fetch_one_dict(
        """
        SELECT id, external_id, title, location, latitude AS lat, longitude AS lng
        FROM land_listings
        WHERE external_id = %s
        """,
        (external_id,),
    )


def get_location_coordinates(location: str) -> dict | None:
    logger.debug("Fetching location coordinates for location=%s", location)
    cache_key = make_cache_key("geo:location", {"location": location.strip().lower()})
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    rows = fetch_all_dicts(
        """
        SELECT latitude AS lat, longitude AS lng
        FROM land_listings
        WHERE location = %s
          AND latitude IS NOT NULL
          AND longitude IS NOT NULL
        """,
        (location,),
    )
    if not rows:
        return None
    lat = sum(row["lat"] for row in rows) / len(rows)
    lng = sum(row["lng"] for row in rows) / len(rows)
    payload = {"location": location, "lat": round(lat, 6), "lng": round(lng, 6)}
    set_cached(cache_key, payload, ttl_seconds=1800)
    return payload

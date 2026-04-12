from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt
from typing import Any

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover
    from fuzzywuzzy import fuzz  # type: ignore


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    return 2 * radius_km * atan2(sqrt(a), sqrt(1 - a))


def deduplicate_records(
    records: list[dict[str, Any]],
    title_similarity_threshold: int = 90,
    location_distance_threshold_km: float = 0.35,
) -> list[dict[str, Any]]:
    deduplicated: list[dict[str, Any]] = []

    for record in records:
        is_duplicate = False
        for existing in deduplicated:
            title_score = fuzz.token_sort_ratio(record.get("title", ""), existing.get("title", ""))
            if title_score < title_similarity_threshold:
                continue
            record_lat = record.get("lat")
            record_lng = record.get("lng")
            existing_lat = existing.get("lat")
            existing_lng = existing.get("lng")
            if None in {record_lat, record_lng, existing_lat, existing_lng}:
                continue
            distance_km = _haversine_km(float(record_lat), float(record_lng), float(existing_lat), float(existing_lng))
            if distance_km <= location_distance_threshold_km:
                is_duplicate = True
                break
        if not is_duplicate:
            deduplicated.append(record)

    return deduplicated

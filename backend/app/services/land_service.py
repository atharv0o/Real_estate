from __future__ import annotations

from backend.app.db.postgres import fetch_all_dicts
from backend.app.services.geo_utils import haversine


def get_all_land_records(limit: int = 100, offset: int = 0) -> list[dict]:
    return fetch_all_dicts(
        """
        SELECT
            id,
            external_id,
            title,
            price_display AS price,
            price_numeric,
            location,
            area_sqft,
            source,
            description,
            owner,
            registration_id,
            verified_status,
            latitude AS lat,
            longitude AS lng,
            blockchain_verified,
            blockchain_hash,
            blockchain_tx_id,
            created_at,
            updated_at
        FROM land_listings
        ORDER BY updated_at DESC
        LIMIT %s OFFSET %s
        """,
        (limit, offset),
    )


def search_land_records(lat: float, lng: float, radius_km: float) -> list[dict]:
    rows = fetch_all_dicts(
        """
        SELECT
            id,
            external_id,
            title,
            price_display AS price,
            price_numeric,
            location,
            area_sqft,
            source,
            description,
            owner,
            registration_id,
            verified_status,
            latitude AS lat,
            longitude AS lng,
            blockchain_verified,
            blockchain_hash,
            blockchain_tx_id
        FROM land_listings
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY updated_at DESC
        """
    )

    matches: list[dict] = []
    for row in rows:
        distance = haversine(lat, lng, row["lat"], row["lng"])
        if distance <= radius_km:
            row["distance_km"] = round(distance, 2)
            matches.append(row)

    matches.sort(key=lambda item: item["distance_km"])
    return matches

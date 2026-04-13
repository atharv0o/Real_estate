from __future__ import annotations

from app.db.postgres import fetch_all_dicts, fetch_one_dict
from app.services.geo_utils import haversine


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


def filter_land_records(
    lat: float,
    lng: float,
    radius_km: float,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[dict]:
    records = search_land_records(lat=lat, lng=lng, radius_km=radius_km)
    filtered: list[dict] = []
    for record in records:
        price_numeric = record.get("price_numeric")
        if min_price is not None and price_numeric is not None and float(price_numeric) < min_price:
            continue
        if max_price is not None and price_numeric is not None and float(price_numeric) > max_price:
            continue
        filtered.append(record)
    return filtered


def get_land_record(property_id: str) -> dict | None:
    if property_id.isdigit():
        record = fetch_one_dict(
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
            WHERE id = %s
            """,
            (int(property_id),),
        )
        if record:
            return record

    return fetch_one_dict(
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
        WHERE external_id = %s
        """,
        (property_id,),
    )

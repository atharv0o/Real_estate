from __future__ import annotations

import json
from pathlib import Path

from app.core.logging import get_logger
from app.db.postgres import fetch_all_dicts, fetch_one_dict
from app.services.geo_utils import haversine

logger = get_logger(__name__)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_PROPERTIES_PATH = _REPO_ROOT / "backend" / "data" / "properties.json"


def _load_json_properties() -> list[dict]:
    if not _PROPERTIES_PATH.is_file():
        return []
    with _PROPERTIES_PATH.open(encoding="utf-8") as file:
        data = json.load(file)
    return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []


def get_all_land_records(limit: int = 100, offset: int = 0) -> list[dict]:
    try:
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
                blockchain_tx_id,
                created_at,
                updated_at
            FROM land_listings
            ORDER BY updated_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        if rows:
            return rows
    except Exception as exc:
        logger.warning("Listing fetch from database failed, using JSON fallback: %s", exc)

    records = _load_json_properties()
    return records[offset : offset + limit]


def search_land_records(lat: float, lng: float, radius_km: float) -> list[dict]:
    try:
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
    except Exception as exc:
        logger.warning("Nearby search from database failed, using JSON fallback: %s", exc)
        rows = _load_json_properties()

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
    try:
        record = None
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
            WHERE external_id = %s
            """,
            (property_id,),
        )
        if record:
            return record
    except Exception as exc:
        logger.warning("Property detail lookup from database failed, using JSON fallback: %s", exc)

    for record in _load_json_properties():
        if str(record.get("external_id") or "") == property_id:
            return record
        if property_id.isdigit() and str(record.get("id") or "") == property_id:
            return record
    return None

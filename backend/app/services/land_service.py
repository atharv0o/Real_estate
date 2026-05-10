from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.db.postgres import fetch_all_dicts, fetch_one_dict
from app.services.geo_utils import haversine
from app.services.search_cache import get_cached, make_cache_key, set_cached
from app.services.search_index import load_properties_from_json as load_indexed_properties

logger = get_logger(__name__)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_PROPERTIES_PATH = _REPO_ROOT / "backend" / "data" / "properties.json"


def _load_json_properties() -> list[dict[str, Any]]:
    return load_indexed_properties(_PROPERTIES_PATH)


def _coordinate_bounds(lat: float, lng: float, radius_km: float) -> tuple[float, float, float, float]:
    lat_delta = radius_km / 111.32
    lng_scale = max(math.cos(math.radians(lat)), 0.15)
    lng_delta = radius_km / (111.32 * lng_scale)
    return lat - lat_delta, lat + lat_delta, lng - lng_delta, lng + lng_delta


def get_all_land_records(limit: int = 100, offset: int = 0) -> list[dict]:
    cache_key = make_cache_key("land:list", {"limit": int(limit), "offset": int(offset)})
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

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
            set_cached(cache_key, rows, ttl_seconds=180)
            return rows
    except Exception as exc:
        logger.warning("Listing fetch from database failed, using JSON fallback: %s", exc)

    records = _load_json_properties()
    payload = records[offset : offset + limit]
    set_cached(cache_key, payload, ttl_seconds=180)
    return payload


def search_land_records(
    lat: float,
    lng: float,
    radius_km: float,
    *,
    min_price: float | None = None,
    max_price: float | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    cache_key = make_cache_key(
        "land:search",
        {
            "lat": round(float(lat), 6),
            "lng": round(float(lng), 6),
            "radius_km": round(float(radius_km), 3),
            "min_price": min_price,
            "max_price": max_price,
            "limit": int(limit),
            "offset": int(offset),
        },
    )
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    lat_min, lat_max, lng_min, lng_max = _coordinate_bounds(lat, lng, radius_km)
    query = [
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
              AND latitude BETWEEN %s AND %s
              AND longitude BETWEEN %s AND %s
        """
    ]
    params: list[Any] = [lat_min, lat_max, lng_min, lng_max]
    if min_price is not None:
        query.append("  AND price_numeric >= %s")
        params.append(min_price)
    if max_price is not None:
        query.append("  AND price_numeric <= %s")
        params.append(max_price)
    query.append("ORDER BY updated_at DESC")
    try:
        rows = fetch_all_dicts(
            "\n".join(query),
            tuple(params),
        )
    except Exception as exc:
        logger.warning("Nearby search from database failed, using JSON fallback: %s", exc)
        rows = _load_json_properties()

    matches: list[dict] = []
    for row in rows:
        try:
            plat = float(row["lat"])
            plng = float(row["lng"])
        except (TypeError, ValueError):
            continue

        distance = haversine(lat, lng, plat, plng)
        if distance <= radius_km:
            row["distance_km"] = round(distance, 2)
            matches.append(row)

    matches.sort(key=lambda item: item["distance_km"])
    paged = matches[offset : offset + limit]
    set_cached(cache_key, paged, ttl_seconds=180)
    return paged


def filter_land_records(
    lat: float,
    lng: float,
    radius_km: float,
    min_price: float | None = None,
    max_price: float | None = None,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    records = search_land_records(
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
        offset=offset,
    )
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
    cache_key = make_cache_key("land:detail", {"property_id": property_id})
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

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
            set_cached(cache_key, record, ttl_seconds=600)
            return record
    except Exception as exc:
        logger.warning("Property detail lookup from database failed, using JSON fallback: %s", exc)

    for record in _load_json_properties():
        if str(record.get("external_id") or "") == property_id:
            set_cached(cache_key, record, ttl_seconds=600)
            return record
        if property_id.isdigit() and str(record.get("id") or "") == property_id:
            set_cached(cache_key, record, ttl_seconds=600)
            return record
    return None

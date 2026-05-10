from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.services.property_service import get_filtered_properties
from app.services.search_cache import get_cached, make_cache_key, set_cached
from app.services.search_index import load_properties_from_json as load_indexed_properties, search_indexed_properties

logger = get_logger(__name__)


def _ensure_pipeline_imports() -> tuple[Any, Any, Any, Any]:
    try:
        from data_pipeline.config import PipelineSettings
        from data_pipeline.loaders.db_loader import upsert_records
        from data_pipeline.loaders.vector_loader import load_vectors
        from data_pipeline.processors.property_processor import process_properties as pipeline_process_properties
    except ImportError as exc:
        logger.warning("Optional data_pipeline package is unavailable: %s", exc)
        return None, None, None, None

    return PipelineSettings, pipeline_process_properties, upsert_records, load_vectors


def load_properties_from_json(path: Path | None = None) -> list[dict[str, Any]]:
    return load_indexed_properties(path)


def filter_properties_by_location(
    properties: list[dict[str, Any]],
    lat: float,
    lng: float,
    radius_km: float,
    *,
    area: str = "",
    city: str = "",
    district: str = "",
    pincode: str = "",
) -> list[dict[str, Any]]:
    if not properties:
        return []

    indexed = search_indexed_properties(
        lat,
        lng,
        radius_km,
        area=area,
        city=city,
        district=district,
        pincode=pincode,
        properties=properties,
        limit=max(1, len(properties)),
        offset=0,
    )
    return [dict(item) for item in indexed.get("properties", [])]


def clean_and_deduplicate(properties: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _, pipeline_process_properties, _, _ = _ensure_pipeline_imports()
    if pipeline_process_properties is None:
        return properties
    return pipeline_process_properties(properties)


def process_and_store(properties: list[dict[str, Any]]) -> dict[str, Any]:
    PipelineSettings, pipeline_process_properties, upsert_records, load_vectors = _ensure_pipeline_imports()
    if pipeline_process_properties is None or PipelineSettings is None:
        return {"upserted": 0, "vector_notify_count": 0, "skipped": True}

    rows = pipeline_process_properties(properties)
    inserted = 0
    if rows and upsert_records is not None:
        try:
            upsert_records(rows, batch_size=100)
            inserted = len(rows)
        except Exception as exc:
            logger.warning("Property upsert skipped because database sync failed: %s", exc)

    vectors = 0
    if rows and load_vectors is not None:
        try:
            settings = PipelineSettings.load()
            vectors = load_vectors(rows, settings)
        except Exception as exc:
            logger.warning("Vector refresh skipped because downstream indexing failed: %s", exc)

    return {"upserted": inserted, "vector_notify_count": vectors}


def search_properties_from_json(
    lat: float,
    lng: float,
    radius: float,
    *,
    min_price: float | None = None,
    max_price: float | None = None,
    area: str = "",
    city: str = "",
    district: str = "",
    pincode: str = "",
    limit: int = 25,
    offset: int = 0,
    page: int | None = None,
) -> dict[str, Any]:
    cache_key = make_cache_key(
        "search:json",
        {
            "lat": round(float(lat), 6),
            "lng": round(float(lng), 6),
            "radius": round(float(radius), 3),
            "min_price": min_price,
            "max_price": max_price,
            "area": area.strip().lower(),
            "city": city.strip().lower(),
            "district": district.strip().lower(),
            "pincode": pincode.strip().lower(),
            "limit": int(limit),
            "offset": int(offset),
            "page": page,
        },
    )
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    result = search_indexed_properties(
        lat,
        lng,
        radius,
        min_price=min_price,
        max_price=max_price,
        area=area,
        city=city,
        district=district,
        pincode=pincode,
        limit=limit,
        offset=offset,
        page=page,
    )
    payload = {
        "count": result.get("count", 0),
        "total_count": result.get("total_count", 0),
        "limit": result.get("limit", int(limit)),
        "offset": result.get("offset", int(offset)),
        "page": result.get("page", page or 1),
        "properties": [dict(item) for item in result.get("properties", [])],
    }
    set_cached(cache_key, payload, ttl_seconds=300)
    return payload


def get_properties(
    lat: float,
    lng: float,
    radius: float,
    min_price: float | None = None,
    max_price: float | None = None,
    *,
    area: str = "",
    city: str = "",
    district: str = "",
    pincode: str = "",
    limit: int = 25,
    offset: int = 0,
    page: int | None = None,
) -> dict:
    cache_key = make_cache_key(
        "search:properties",
        {
            "lat": round(float(lat), 6),
            "lng": round(float(lng), 6),
            "radius": round(float(radius), 3),
            "min_price": min_price,
            "max_price": max_price,
            "area": area.strip().lower(),
            "city": city.strip().lower(),
            "district": district.strip().lower(),
            "pincode": pincode.strip().lower(),
            "limit": int(limit),
            "offset": int(offset),
            "page": page,
        },
    )
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    try:
        payload = get_filtered_properties(
            lat=lat,
            lng=lng,
            radius_km=radius,
            min_price=min_price,
            max_price=max_price,
            limit=limit,
            offset=offset,
            area=area,
            city=city,
            district=district,
            pincode=pincode,
            page=page,
        )
        if payload.get("properties"):
            set_cached(cache_key, payload, ttl_seconds=300)
            return payload
    except Exception as exc:
        logger.warning("Database-backed property search failed, using JSON fallback: %s", exc)

    fallback = search_properties_from_json(
        lat=lat,
        lng=lng,
        radius=radius,
        min_price=min_price,
        max_price=max_price,
        area=area,
        city=city,
        district=district,
        pincode=pincode,
        limit=limit,
        offset=offset,
        page=page,
    )
    set_cached(cache_key, fallback, ttl_seconds=300)
    return fallback

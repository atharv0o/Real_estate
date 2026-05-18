from __future__ import annotations

import time
from copy import deepcopy

from fastapi import APIRouter, BackgroundTasks, Query

from app.core.logging import get_logger
from app.models.request_models import SearchRequest
from app.services.api_response import error_response, success_response
from app.services.blockchain_service import compute_record_hash, get_cached_verification, verify_property_with_hash
from app.services.data_service import get_properties, process_and_store, search_properties_from_json
from app.services.geo_service import get_coordinates
from app.services.search_cache import get_cached, make_cache_key, set_cached
from app.services.maps_service import resolve_location
from app.services.rag_connector import get_property_insights

router = APIRouter()
logger = get_logger(__name__)

_MAX_LIMIT = 100


def _normalize_pagination(limit: int | None, offset: int | None, page: int | None) -> tuple[int, int, int]:
    safe_limit = max(1, min(int(limit or 25), _MAX_LIMIT))
    safe_offset = max(0, int(offset or 0))
    safe_page = int(page or 1)
    if safe_page > 1 and safe_offset == 0:
        safe_offset = (safe_page - 1) * safe_limit
    return safe_limit, safe_offset, max(1, safe_page)


def _refresh_blockchain_cache(properties: list[dict]) -> None:
    for prop in properties:
        try:
            verify_property_with_hash(
                str(prop.get("title") or ""),
                str(prop.get("location") or ""),
                str(prop.get("price") or prop.get("price_numeric") or ""),
            )
        except Exception:
            continue


def _refresh_insight_cache(properties: list[dict], location_label: str) -> None:
    try:
        get_property_insights(properties, location_label=location_label, enrich_with_rag=True)
    except Exception:
        pass


@router.get("/search")
def search(
    lat: float,
    lng: float,
    radius: float,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    page: int = Query(default=1, ge=1),
):
    try:
        safe_limit, safe_offset, safe_page = _normalize_pagination(limit, offset, page)
        return success_response(get_properties(lat, lng, radius, limit=safe_limit, offset=safe_offset, page=safe_page))
    except Exception as exc:
        return error_response(str(exc))


@router.post("/search")
def post_search(body: SearchRequest, background_tasks: BackgroundTasks):
    try:
        safe_limit, safe_offset, safe_page = _normalize_pagination(body.limit, body.offset, body.page)
        query_cache_key = make_cache_key(
            "search:response",
            {
                "area": body.area.strip().lower(),
                "city": body.city.strip().lower(),
                "district": body.district.strip().lower(),
                "pincode": body.pincode.strip().lower(),
                "land_area_code": body.land_area_code.strip().lower(),
                "radius": round(float(body.radius), 3),
                "min_price": body.min_price,
                "max_price": body.max_price,
                "limit": safe_limit,
                "offset": safe_offset,
                "page": safe_page,
            },
        )
        cached = get_cached(query_cache_key)
        if cached is not None:
            return success_response(cached)

        total_started = time.perf_counter()
        # Land/area codes are identifiers, not geocoding terms. Including them in
        # the indexed location lookup can send otherwise valid searches to the
        # deterministic fallback coordinates when the code tokens collide poorly.
        query = f"{body.area}, {body.city}, {body.district}".strip().strip(",")
        geocode_started = time.perf_counter()
        coords = get_coordinates(query)
        geocode_ms = (time.perf_counter() - geocode_started) * 1000.0
        lat = float(coords["lat"])
        lng = float(coords["lng"])

        payload = search_properties_from_json(
            lat,
            lng,
            body.radius,
            min_price=body.min_price,
            max_price=body.max_price,
            area=body.area,
            city=body.city,
            district=body.district,
            pincode=body.pincode,
            limit=safe_limit,
            offset=safe_offset,
            page=safe_page,
        )
        if not payload.get("properties"):
            payload = get_properties(
                lat,
                lng,
                body.radius,
                min_price=body.min_price,
                max_price=body.max_price,
                area=body.area,
                city=body.city,
                district=body.district,
                pincode=body.pincode,
                limit=safe_limit,
                offset=safe_offset,
                page=safe_page,
            )
        props = [dict(p) for p in payload.get("properties", [])]

        for p in props:
            verification_hash = compute_record_hash(
                str(p.get("title") or ""),
                str(p.get("location") or ""),
                str(p.get("price") or p.get("price_numeric") or ""),
            )
            verification = get_cached_verification(verification_hash)
            p["verification_hash"] = verification_hash
            p["blockchain_verified"] = bool(verification.get("verified")) if verification else False

        insights = get_property_insights(props, location_label=str(coords.get("label") or ""), enrich_with_rag=False)
        summary_hint = str(insights.get("summary") or "")
        for idx, p in enumerate(props[:5]):
            p["ai_summary"] = summary_hint if idx == 0 else (p.get("ai_summary") or "")

        background_tasks.add_task(process_and_store, deepcopy(props))
        background_tasks.add_task(_refresh_blockchain_cache, deepcopy(props))
        background_tasks.add_task(_refresh_insight_cache, deepcopy(props), str(coords.get("label") or ""))

        response_data = {
            "coordinates": coords,
            "properties": props,
            "insights": insights,
            "count": len(props),
            "total_count": int(payload.get("total_count", len(props))),
            "limit": safe_limit,
            "offset": safe_offset,
            "page": safe_page,
            "store": {"upserted": len(props), "vector_notify_count": 0},
        }
        set_cached(query_cache_key, response_data, ttl_seconds=180)
        total_ms = (time.perf_counter() - total_started) * 1000.0
        logger.info(
            "SEARCH PERFORMANCE | geocode: %.2fms | total: %.2fms | results=%s",
            geocode_ms,
            total_ms,
            len(props),
        )
        return success_response(response_data)
    except Exception as exc:
        return error_response(str(exc))


@router.get("/land/search")
def land_search(
    lat: float,
    lng: float,
    radius: float = Query(default=5.0, gt=0),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    page: int = Query(default=1, ge=1),
):
    try:
        safe_limit, safe_offset, safe_page = _normalize_pagination(limit, offset, page)
        payload = get_properties(
            lat,
            lng,
            radius,
            min_price=min_price,
            max_price=max_price,
            limit=safe_limit,
            offset=safe_offset,
            page=safe_page,
        )
        return success_response(payload["properties"])
    except Exception as exc:
        return error_response(str(exc), data=[])


@router.get("/location")
def location(query: str):
    try:
        return success_response(resolve_location(query))
    except Exception as exc:
        return error_response(str(exc))

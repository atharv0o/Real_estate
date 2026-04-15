from __future__ import annotations

from copy import deepcopy

from fastapi import APIRouter, Query

from app.models.request_models import SearchRequest
from app.services.api_response import error_response, success_response
from app.services.blockchain_service import verify_property_with_hash
from app.services.data_service import (
    filter_properties_by_location,
    get_properties,
    load_properties_from_json,
    process_and_store,
    search_properties_from_json,
)
from app.services.geo_service import get_coordinates
from app.services.maps_service import resolve_location
from app.services.rag_connector import get_property_insights

router = APIRouter()


@router.get("/search")
def search(lat: float, lng: float, radius: float):
    try:
        return success_response(get_properties(lat, lng, radius))
    except Exception as exc:
        return error_response(str(exc))


@router.post("/search")
def post_search(body: SearchRequest):
    try:
        query = f"{body.area}, {body.city}, {body.district}, {body.pincode}".strip().strip(",")
        coords = get_coordinates(query)
        lat = float(coords["lat"])
        lng = float(coords["lng"])

        catalog = load_properties_from_json()
        filtered = filter_properties_by_location(
            catalog,
            lat,
            lng,
            body.radius,
            area=body.area,
            city=body.city,
            district=body.district,
            pincode=body.pincode,
        )

        if body.min_price is not None:
            filtered = [p for p in filtered if float(p.get("price_numeric") or 0) >= float(body.min_price)]
        if body.max_price is not None:
            filtered = [p for p in filtered if float(p.get("price_numeric") or 0) <= float(body.max_price)]

        store_info = process_and_store(deepcopy(filtered))

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
        )
        if not payload.get("properties"):
            payload = get_properties(lat, lng, body.radius, min_price=body.min_price, max_price=body.max_price)
        props = [dict(p) for p in payload.get("properties", [])]

        for p in props:
            v = verify_property_with_hash(
                str(p.get("title") or ""),
                str(p.get("location") or ""),
                str(p.get("price") or p.get("price_numeric") or ""),
            )
            p["blockchain_verified"] = bool(v.get("verified"))
            p["verification_hash"] = str(v.get("hash") or "")

        insights = get_property_insights(props)
        summary_hint = str(insights.get("summary") or "")
        for idx, p in enumerate(props[:5]):
            p["ai_summary"] = summary_hint if idx == 0 else (p.get("ai_summary") or "")

        return success_response(
            {
                "coordinates": coords,
                "properties": props,
                "insights": insights,
                "count": len(props),
                "store": store_info,
            }
        )
    except Exception as exc:
        return error_response(str(exc))


@router.get("/land/search")
def land_search(
    lat: float,
    lng: float,
    radius: float = Query(default=5.0, gt=0),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
):
    try:
        payload = get_properties(lat, lng, radius, min_price=min_price, max_price=max_price)
        return success_response(payload["properties"])
    except Exception as exc:
        return error_response(str(exc), data=[])


@router.get("/location")
def location(query: str):
    try:
        return success_response(resolve_location(query))
    except Exception as exc:
        return error_response(str(exc))

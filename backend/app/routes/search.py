from fastapi import APIRouter, Query

from app.services.api_response import error_response, success_response
from app.services.data_service import get_properties
from app.services.maps_service import resolve_location

router = APIRouter()


@router.get("/search")
def search(lat: float, lng: float, radius: float):
    try:
        return success_response(get_properties(lat, lng, radius))
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

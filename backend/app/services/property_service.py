from __future__ import annotations

from app.services.land_service import filter_land_records, get_all_land_records, get_land_record, search_land_records


def list_properties(limit: int = 100, offset: int = 0) -> list[dict]:
    return get_all_land_records(limit=limit, offset=offset)


def get_nearby_properties(lat: float, lng: float, radius_km: float) -> dict:
    properties = search_land_records(lat=lat, lng=lng, radius_km=radius_km)
    return {"count": len(properties), "properties": properties}


def get_filtered_properties(
    lat: float,
    lng: float,
    radius_km: float,
    min_price: float | None = None,
    max_price: float | None = None,
) -> dict:
    properties = filter_land_records(
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        min_price=min_price,
        max_price=max_price,
    )
    return {"count": len(properties), "properties": properties}


def get_property_details(property_id: str) -> dict | None:
    return get_land_record(property_id)

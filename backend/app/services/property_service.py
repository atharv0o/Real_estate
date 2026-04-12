from __future__ import annotations

from app.services.land_service import get_all_land_records, search_land_records


def list_properties(limit: int = 100, offset: int = 0) -> list[dict]:
    return get_all_land_records(limit=limit, offset=offset)


def get_nearby_properties(lat: float, lng: float, radius_km: float) -> dict:
    properties = search_land_records(lat=lat, lng=lng, radius_km=radius_km)
    return {"count": len(properties), "properties": properties}

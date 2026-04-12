from __future__ import annotations

from app.services.property_service import get_nearby_properties


def get_properties(lat: float, lng: float, radius: float) -> dict:
    return get_nearby_properties(lat=lat, lng=lng, radius_km=radius)

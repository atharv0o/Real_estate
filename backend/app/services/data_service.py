from __future__ import annotations

from app.services.property_service import get_filtered_properties


def get_properties(
    lat: float,
    lng: float,
    radius: float,
    min_price: float | None = None,
    max_price: float | None = None,
) -> dict:
    return get_filtered_properties(
        lat=lat,
        lng=lng,
        radius_km=radius,
        min_price=min_price,
        max_price=max_price,
    )

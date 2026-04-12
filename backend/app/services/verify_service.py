from __future__ import annotations

from app.services.blockchain_service import verify_property as verify_land_property


def verify_property(data: dict) -> dict:
    return verify_land_property(data)

from __future__ import annotations

import os

import requests

from app.core.logging import get_logger


logger = get_logger(__name__)
BLOCKCHAIN_API = os.getenv("BLOCKCHAIN_API", "http://127.0.0.1:8002").rstrip("/")


def verify_land_record(data: dict, service_url: str | None = None, enabled: bool = True) -> dict:
    if not enabled:
        return {"verified": False, "skipped": True, "reason": "blockchain hook disabled"}

    target_url = service_url or f"{BLOCKCHAIN_API}/verify"
    try:
        response = requests.post(target_url, json=data, timeout=10)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            return payload
        return {"verified": False, "error": "unexpected_blockchain_response"}
    except Exception as exc:
        logger.warning("Blockchain verification request failed: %s", exc)
        return {"verified": False, "error": str(exc)}


def verify_property(data: dict) -> dict:
    return verify_land_record(data)

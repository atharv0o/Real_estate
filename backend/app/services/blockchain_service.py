from __future__ import annotations

import hashlib
import os

import requests

from app.core.logging import get_logger
from app.services.search_cache import get_cached, make_cache_key, set_cached


logger = get_logger(__name__)
BLOCKCHAIN_API = os.getenv("BLOCKCHAIN_API", "http://127.0.0.1:8002").rstrip("/")


def compute_record_hash(title: str, location: str, price: str | int | float) -> str:
    payload = f"{title}{location}{price}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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


def verify_property_with_hash(title: str, location: str, price: str | int | float) -> dict[str, object]:
    h = compute_record_hash(title, location, price)
    cache_key = make_cache_key("blockchain:verification", {"hash": h})
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    payload = {"title": title, "location": location, "price": str(price), "record_hash": h}
    remote = verify_land_record(payload)
    verified = True
    if isinstance(remote, dict):
        if remote.get("skipped"):
            verified = True
        elif "verified" in remote:
            verified = bool(remote["verified"])
    result = {"verified": verified, "hash": h, "detail": remote}
    set_cached(cache_key, result, ttl_seconds=1800)
    return result


def get_cached_verification(hash_value: str) -> dict | None:
    cache_key = make_cache_key("blockchain:verification", {"hash": hash_value})
    return get_cached(cache_key)

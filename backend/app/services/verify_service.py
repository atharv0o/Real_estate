from __future__ import annotations

import base64
import hashlib
import json
import time
from typing import Any

from app.services.blockchain_service import verify_property as verify_land_property


DOCUMENT_KEYS = ("document", "documentFile", "document_file", "uploadedDocument")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(data: dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return _sha256_bytes(payload.encode("utf-8"))


def _document_bytes(value: Any) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        try:
            return base64.b64decode(value, validate=True)
        except Exception:
            return value.encode("utf-8")
    return json.dumps(value, sort_keys=True, default=str).encode("utf-8")


def _extract_property_data(data: dict[str, Any]) -> dict[str, Any]:
    property_data = data.get("propertyData")
    if isinstance(property_data, dict):
        return property_data

    return {
        key: value
        for key, value in data.items()
        if key not in {*DOCUMENT_KEYS, "walletAddress", "wallet_address"}
    }


def _extract_document_hash(data: dict[str, Any]) -> str:
    existing_hash = data.get("documentHash") or data.get("document_hash")
    if existing_hash:
        return str(existing_hash)

    for key in DOCUMENT_KEYS:
        if key in data:
            return _sha256_bytes(_document_bytes(data[key]))
    return ""


def build_blockchain_payload(data: dict[str, Any]) -> dict[str, Any]:
    property_data = _extract_property_data(data)
    property_hash = str(data.get("propertyHash") or data.get("property_hash") or _sha256_json(property_data))
    document_hash = _extract_document_hash(data)

    return {
        **data,
        "propertyData": property_data,
        "propertyId": str(
            data.get("propertyId")
            or data.get("property_id")
            or data.get("external_id")
            or data.get("id")
            or property_hash[:16]
        ),
        "propertyHash": property_hash,
        "documentHash": document_hash,
        "walletAddress": data.get("walletAddress") or data.get("wallet_address") or "",
        "timestamp": str(data.get("timestamp") or int(time.time())),
    }


def verify_property(data: dict) -> dict:
    payload = build_blockchain_payload(data)
    return verify_land_property(payload)

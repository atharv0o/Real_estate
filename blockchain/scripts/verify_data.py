from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdk.algo_client import get_app_id, get_indexer_client  # noqa: E402


PROOF_KEYS = {
    "propertyId",
    "propertyHash",
    "documentHash",
    "walletAddress",
    "timestamp",
}


def _decode_state_value(item: dict[str, Any]) -> tuple[str, str] | None:
    key = base64.b64decode(item.get("key", "")).decode("utf-8")
    if key not in PROOF_KEYS:
        return None

    value = item.get("value", {})
    value_type = value.get("type")
    if value_type == 1:
        decoded_value = base64.b64decode(value.get("bytes", "")).decode("utf-8")
    else:
        decoded_value = str(value.get("uint", ""))
    return key, decoded_value


def fetch_verification_record(app_id: int | None = None) -> dict[str, str]:
    resolved_app_id = app_id or get_app_id()
    if resolved_app_id is None:
        raise RuntimeError("APP_ID is required to fetch verification proof")

    response = get_indexer_client().applications(resolved_app_id)
    global_state = (
        response.get("application", {})
        .get("params", {})
        .get("global-state", [])
    )

    record: dict[str, str] = {}
    for item in global_state:
        decoded = _decode_state_value(item)
        if decoded:
            key, value = decoded
            record[key] = value
    return record


def verify_hashes(
    expected_property_hash: str,
    expected_document_hash: str = "",
    app_id: int | None = None,
) -> dict[str, Any]:
    try:
        record = fetch_verification_record(app_id)
        property_match = record.get("propertyHash") == expected_property_hash
        document_match = (
            not expected_document_hash
            or record.get("documentHash") == expected_document_hash
        )
        return {
            "verified": property_match and document_match,
            "property_hash_match": property_match,
            "document_hash_match": document_match,
            "record": record,
        }
    except Exception as exc:
        return {"verified": False, "error": str(exc)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify property proof hashes stored on Algorand TestNet")
    parser.add_argument("--property-hash", required=True)
    parser.add_argument("--document-hash", default="")
    parser.add_argument("--app-id", type=int)
    args = parser.parse_args()

    result = verify_hashes(args.property_hash, args.document_hash, args.app_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

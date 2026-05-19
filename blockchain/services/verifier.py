from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from algosdk import account, mnemonic, transaction
from algosdk.error import AlgodHTTPError, AlgodRequestError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdk.algo_client import get_algod_client, get_app_id


load_dotenv(ROOT.parent / ".env")
load_dotenv(ROOT / ".env")


def _sha256_json(data: dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _private_key_from_env() -> str | None:
    phrase = os.getenv("ALGORAND_MNEMONIC", "").strip()
    if not phrase:
        return None
    return mnemonic.to_private_key(phrase)


def _address_from_private_key(private_key: str) -> str:
    return account.address_from_private_key(private_key)


def _string_value(data: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        value = data.get(key)
        if value is not None:
            return str(value)
    return default


def _bounded_value(value: str, limit: int = 128) -> str:
    return value[:limit]


def build_verification_record(data: dict[str, Any]) -> dict[str, str]:
    property_data = data.get("propertyData")
    if not isinstance(property_data, dict):
        property_data = {
            key: value
            for key, value in data.items()
            if key
            not in {
                "propertyHash",
                "property_hash",
                "documentHash",
                "document_hash",
                "walletAddress",
                "wallet_address",
                "timestamp",
            }
        }

    property_hash = _string_value(data, "propertyHash", "property_hash", "record_hash")
    if not property_hash:
        property_hash = _sha256_json(property_data)

    property_id = _string_value(
        data,
        "propertyId",
        "property_id",
        "external_id",
        "id",
        default=property_hash[:16],
    )

    return {
        "propertyId": _bounded_value(property_id),
        "propertyHash": _bounded_value(property_hash),
        "documentHash": _bounded_value(_string_value(data, "documentHash", "document_hash")),
        "walletAddress": _bounded_value(_string_value(data, "walletAddress", "wallet_address")),
        "timestamp": _bounded_value(_string_value(data, "timestamp", default=str(int(time.time())))),
    }


def store_verification(record: dict[str, str], retries: int = 2) -> dict[str, Any]:
    app_id = get_app_id()
    if app_id is None:
        return {
            "verified": False,
            "configured": False,
            "error": "APP_ID is not configured for blockchain verification",
        }

    private_key = _private_key_from_env()
    if private_key is None:
        return {
            "verified": False,
            "configured": False,
            "error": "ALGORAND_MNEMONIC is not configured",
        }

    algod_client = get_algod_client()
    sender = _address_from_private_key(private_key)
    app_args = [
        record["propertyId"].encode("utf-8"),
        record["propertyHash"].encode("utf-8"),
        record["documentHash"].encode("utf-8"),
        record["walletAddress"].encode("utf-8"),
        record["timestamp"].encode("utf-8"),
    ]

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            params = algod_client.suggested_params()
            txn = transaction.ApplicationNoOpTxn(
                sender=sender,
                sp=params,
                index=app_id,
                app_args=app_args,
            )
            signed_txn = txn.sign(private_key)
            tx_id = algod_client.send_transaction(signed_txn)
            transaction.wait_for_confirmation(algod_client, tx_id, 4)
            return {
                "verified": True,
                "configured": True,
                "app_id": app_id,
                "explorer_app_url": f"https://testnet.algoexplorer.io/application/{app_id}",
                "tx_id": tx_id,
                "explorer_tx_url": f"https://testnet.algoexplorer.io/tx/{tx_id}",
                "record": record,
                "hash": record["propertyHash"],
            }
        except (AlgodHTTPError, AlgodRequestError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(0.75 * (attempt + 1))
                continue
            break

    return {
        "verified": False,
        "configured": True,
        "app_id": app_id,
        "error": str(last_error) if last_error else "unknown blockchain error",
        "record": record,
        "hash": record["propertyHash"],
    }


def verify_property(data: dict[str, Any]) -> dict[str, Any]:
    record = build_verification_record(data)
    return store_verification(record)

from __future__ import annotations

import hashlib
import re
from typing import Any

from shared.logger import get_logger


logger = get_logger(__name__)

PRICE_PATTERN = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")
REQUIRED_FIELDS = ("title", "price", "location", "source", "description")


def _parse_price(raw_price: Any) -> float | None:
    if raw_price is None:
        return None
    if isinstance(raw_price, (int, float)):
        return float(raw_price)
    match = PRICE_PATTERN.search(str(raw_price))
    if not match:
        return None
    return float(match.group(0).replace(",", ""))


def _valid_coordinates(lat: Any, lng: Any) -> bool:
    try:
        lat_value = float(lat)
        lng_value = float(lng)
    except (TypeError, ValueError):
        return False
    return -90 <= lat_value <= 90 and -180 <= lng_value <= 180


def validate_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    clean_records: list[dict[str, Any]] = []
    rejected_records: list[dict[str, Any]] = []

    for record in records:
        missing = [field for field in REQUIRED_FIELDS if not str(record.get(field, "")).strip()]
        parsed_price = _parse_price(record.get("price"))
        coordinates_valid = _valid_coordinates(record.get("lat"), record.get("lng"))
        if missing or parsed_price is None or not coordinates_valid:
            rejected_records.append(
                {
                    "record": record,
                    "errors": {
                        "missing_fields": missing,
                        "price_valid": parsed_price is not None,
                        "coordinates_valid": coordinates_valid,
                    },
                }
            )
            continue

        normalized = dict(record)
        normalized["price_numeric"] = parsed_price
        normalized["lat"] = float(record["lat"])
        normalized["lng"] = float(record["lng"])
        normalized["area_sqft"] = float(record["area_sqft"]) if record.get("area_sqft") is not None else None
        stable_key = "|".join(
            [
                normalized["title"].strip().lower(),
                normalized["location"].strip().lower(),
                str(normalized["source"]).strip().lower(),
                str(normalized.get("registration_id") or "").strip().lower(),
            ]
        )
        normalized["source_record_hash"] = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()
        normalized["external_id"] = normalized.get("external_id") or normalized["source_record_hash"][:16]
        normalized["raw_payload"] = {
            "collector_source": normalized.get("source"),
            "registry_owner": normalized.get("owner"),
            "verified_status": normalized.get("verified_status"),
        }
        clean_records.append(normalized)

    logger.info("Validated %s clean records and rejected %s records.", len(clean_records), len(rejected_records))
    return clean_records, rejected_records

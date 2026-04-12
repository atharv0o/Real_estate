from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apscheduler.schedulers.blocking import BlockingScheduler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_pipeline.bootstrap import ensure_project_root
from data_pipeline.collectors.listing_collector import collect_listings
from data_pipeline.config import PipelineSettings
from data_pipeline.loaders.db_loader import upsert_records
from data_pipeline.loaders.vector_loader import load_vectors
from data_pipeline.processors.geo_encoder import GeoEncoder
from shared.logger import get_logger

ensure_project_root()

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover
    from fuzzywuzzy import fuzz  # type: ignore


logger = get_logger(__name__)
PRICE_NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")


def _parse_price_to_int(raw_price: Any) -> int | None:
    if raw_price is None:
        return None
    if isinstance(raw_price, (int, float)):
        value = int(float(raw_price))
        return value if value > 0 else None

    text = str(raw_price).replace(",", " ").strip()
    if not text:
        return None

    numbers = PRICE_NUMBER_PATTERN.findall(text)
    if not numbers:
        return None

    base = float(numbers[0])
    lowered = text.lower()
    multiplier = 1
    if "crore" in lowered or re.search(r"\bcr\b", lowered):
        multiplier = 10_000_000
    elif "lakh" in lowered or "lac" in lowered:
        multiplier = 100_000
    elif base < 10_000 and len(numbers) > 1:
        base = float("".join(number.replace(".", "") for number in numbers))
    value = int(base * multiplier)
    return value if value > 0 else None


def _parse_area_sqft(raw_area: Any) -> float | None:
    if raw_area is None:
        return None
    if isinstance(raw_area, (int, float)):
        value = float(raw_area)
    else:
        match = re.search(r"\d[\d,.]*", str(raw_area))
        if not match:
            return None
        value = float(match.group(0).replace(",", ""))
    return value if 100 <= value <= 5_000_000 else None


def _build_clean_record(record: dict[str, Any]) -> dict[str, Any] | None:
    title = str(record.get("title") or "").strip()
    location = str(record.get("location") or "").strip()
    description = str(record.get("description") or "").strip()
    source = str(record.get("source") or "").strip()
    price_numeric = _parse_price_to_int(record.get("price"))
    area_sqft = _parse_area_sqft(record.get("area_sqft"))

    try:
        lat = float(record.get("lat"))
        lng = float(record.get("lng"))
    except (TypeError, ValueError):
        return None

    if not title or not location or not source or price_numeric is None:
        return None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    if area_sqft is None:
        return None

    stable_key = f"{title.strip().lower()}|{location.strip().lower()}|{price_numeric}"
    source_record_hash = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()
    payload = dict(record.get("raw_payload") or {})
    payload.update(
        {
            "detail_url": record.get("detail_url"),
            "coordinate_source": record.get("coordinate_source"),
            "scraped_location": location,
        }
    )

    return {
        "external_id": record.get("external_id") or source_record_hash[:16],
        "title": title,
        "price": str(record.get("price") or price_numeric),
        "price_numeric": price_numeric,
        "location": location,
        "area_sqft": area_sqft,
        "source": source,
        "description": description,
        "owner": None,
        "registration_id": None,
        "verified_status": False,
        "lat": lat,
        "lng": lng,
        "source_record_hash": source_record_hash,
        "raw_payload": payload,
    }


def _deduplicate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduplicated: list[dict[str, Any]] = []
    exact_seen: set[tuple[str, str, int]] = set()

    for record in records:
        exact_key = (record["title"].lower(), record["location"].lower(), int(record["price_numeric"]))
        if exact_key in exact_seen:
            continue

        duplicate = False
        record_fingerprint = f"{record['title']} {record['location']} {record['price_numeric']}"
        for existing in deduplicated:
            existing_fingerprint = f"{existing['title']} {existing['location']} {existing['price_numeric']}"
            if fuzz.token_sort_ratio(record_fingerprint, existing_fingerprint) > 90:
                duplicate = True
                break
        if duplicate:
            continue

        exact_seen.add(exact_key)
        deduplicated.append(record)

    return deduplicated


def run_pipeline() -> dict[str, Any]:
    settings = PipelineSettings.load()
    geo_encoder = GeoEncoder(settings)
    summary: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "total_pages_scraped": 0,
        "raw_listings_found": 0,
        "valid_listings": 0,
        "coordinates_extracted": 0,
        "inserted_into_db": 0,
        "sent_to_rag": 0,
        "errors": [],
    }

    collector_result = collect_listings(settings, geo_encoder)
    summary["total_pages_scraped"] = collector_result.total_pages_scraped
    summary["raw_listings_found"] = collector_result.raw_listings_found
    summary["coordinates_extracted"] = collector_result.coordinates_extracted
    summary["errors"].extend(collector_result.errors)

    strict_records = []
    for record in collector_result.listings:
        clean_record = _build_clean_record(record)
        if clean_record:
            strict_records.append(clean_record)

    deduplicated = _deduplicate_records(strict_records)
    summary["valid_listings"] = len(deduplicated)

    if deduplicated:
        try:
            persisted = upsert_records(deduplicated, batch_size=50)
            summary["inserted_into_db"] = len(persisted)
        except Exception as exc:
            logger.exception("DB load failed.")
            summary["errors"].append(f"db_load_failed: {exc}")

        try:
            summary["sent_to_rag"] = load_vectors(deduplicated, settings)
        except Exception as exc:
            logger.exception("Vector loading failed.")
            summary["errors"].append(f"vector_load_failed: {exc}")

    summary["completed_at"] = datetime.now(timezone.utc).isoformat()
    logger.info(
        "OK %s pages scraped | %s raw listings found | %s valid | %s with coordinates | %s inserted | %s sent to RAG",
        summary["total_pages_scraped"],
        summary["raw_listings_found"],
        summary["valid_listings"],
        summary["coordinates_extracted"],
        summary["inserted_into_db"],
        summary["sent_to_rag"],
    )
    return summary


def run_scheduled_pipeline() -> None:
    settings = PipelineSettings.load()
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(run_pipeline, "interval", minutes=settings.scheduler_interval_minutes, max_instances=1)
    logger.info("Starting scheduled pipeline every %s minutes.", settings.scheduler_interval_minutes)
    scheduler.start()


def main() -> None:
    parser = argparse.ArgumentParser(description="Land data pipeline scheduler")
    parser.add_argument("--schedule", action="store_true", help="Run continuously on the configured interval.")
    args = parser.parse_args()

    if args.schedule:
        run_scheduled_pipeline()
        return

    print(run_pipeline())


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apscheduler.schedulers.blocking import BlockingScheduler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.blockchain_service import verify_land_record
from data_pipeline.bootstrap import ensure_project_root
from data_pipeline.collectors.govt_registry_collector import collect_registry_records
from data_pipeline.collectors.listing_collector import collect_listings
from data_pipeline.config import PipelineSettings
from data_pipeline.loaders.db_loader import update_blockchain_status, upsert_records
from data_pipeline.loaders.vector_loader import load_vectors
from data_pipeline.processors.deduplicator import deduplicate_records
from data_pipeline.processors.geo_encoder import GeoEncoder
from data_pipeline.processors.validator import validate_records
from shared.logger import get_logger

ensure_project_root()

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover
    from fuzzywuzzy import fuzz  # type: ignore


logger = get_logger(__name__)


def _enrich_with_registry(listings: list[dict], registry_records: list[dict]) -> list[dict]:
    enriched_records: list[dict] = []

    for listing in listings:
        best_match: dict | None = None
        best_score = 0
        for registry_record in registry_records:
            title_score = fuzz.token_sort_ratio(listing["title"], registry_record["title"])
            location_score = fuzz.token_sort_ratio(listing["location"], registry_record["location"])
            combined_score = int((title_score + location_score) / 2)
            if combined_score > best_score:
                best_score = combined_score
                best_match = registry_record

        merged = dict(listing)
        if best_match and best_score >= 85:
            merged.update(
                {
                    "owner": best_match.get("owner"),
                    "registration_id": best_match.get("registration_id"),
                    "verified_status": best_match.get("verified_status"),
                }
            )
        else:
            merged.update({"owner": None, "registration_id": None, "verified_status": False})
        enriched_records.append(merged)

    return enriched_records


def _geocode_records(records: list[dict], geo_encoder: GeoEncoder) -> list[dict]:
    geocoded: list[dict] = []
    for record in records:
        try:
            coordinates = geo_encoder.encode(record["location"])
            geocoded.append({**record, **coordinates})
        except Exception as exc:
            logger.warning("Geocoding failed for %s: %s", record.get("title"), exc)
            geocoded.append(record)
    return geocoded


def run_pipeline() -> dict[str, Any]:
    settings = PipelineSettings.load()
    geo_encoder = GeoEncoder(settings)
    summary: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "collected": 0,
        "deduplicated": 0,
        "validated": 0,
        "rejected": 0,
        "db_upserted": 0,
        "vectors_loaded": 0,
        "blockchain_verified": 0,
        "errors": [],
    }

    try:
        listings = collect_listings(settings)
        registry = collect_registry_records()
        summary["collected"] = len(listings)
    except Exception as exc:
        logger.exception("Collection stage failed.")
        summary["errors"].append(f"collection_failed: {exc}")
        return summary

    try:
        enriched = _enrich_with_registry(listings, registry)
        geocoded = _geocode_records(enriched, geo_encoder)
        deduplicated = deduplicate_records(geocoded)
        summary["deduplicated"] = len(deduplicated)
    except Exception as exc:
        logger.exception("Processing stage failed.")
        summary["errors"].append(f"processing_failed: {exc}")
        return summary

    clean_records: list[dict] = []
    try:
        clean_records, rejected = validate_records(deduplicated)
        summary["validated"] = len(clean_records)
        summary["rejected"] = len(rejected)
    except Exception as exc:
        logger.exception("Validation stage failed.")
        summary["errors"].append(f"validation_failed: {exc}")

    if clean_records:
        try:
            persisted = upsert_records(clean_records)
            summary["db_upserted"] = len(persisted)
        except Exception as exc:
            summary["errors"].append(f"db_load_failed: {exc}")

        try:
            summary["vectors_loaded"] = load_vectors(clean_records, settings)
        except Exception as exc:
            logger.exception("Vector loading failed.")
            summary["errors"].append(f"vector_load_failed: {exc}")

        if settings.enable_blockchain_hook:
            for record in clean_records:
                try:
                    result = verify_land_record(record, service_url=settings.blockchain_service_url, enabled=True)
                    if result.get("verified"):
                        summary["blockchain_verified"] += 1
                    update_blockchain_status(record["source_record_hash"], result)
                except Exception as exc:
                    logger.warning("Blockchain verification failed for %s: %s", record.get("title"), exc)
                    summary["errors"].append(f"blockchain_failed:{record.get('external_id')}:{exc}")

    summary["completed_at"] = datetime.now(timezone.utc).isoformat()
    logger.info("Pipeline run summary: %s", summary)
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

from __future__ import annotations

from typing import Any

from psycopg2.extras import Json, RealDictCursor, execute_batch

from data_pipeline.db.postgres import get_connection, initialize_database
from data_pipeline.logging_utils import get_logger


logger = get_logger(__name__)

UPSERT_SQL = """
INSERT INTO land_listings (
    external_id,
    title,
    price_display,
    price_numeric,
    location,
    area_sqft,
    source,
    description,
    owner,
    registration_id,
    verified_status,
    latitude,
    longitude,
    source_record_hash,
    listing_payload
)
VALUES (
    %(external_id)s,
    %(title)s,
    %(price)s,
    %(price_numeric)s,
    %(location)s,
    %(area_sqft)s,
    %(source)s,
    %(description)s,
    %(owner)s,
    %(registration_id)s,
    %(verified_status)s,
    %(lat)s,
    %(lng)s,
    %(source_record_hash)s,
    %(listing_payload)s
)
ON CONFLICT (title, location, price_numeric) DO UPDATE
SET
    external_id = EXCLUDED.external_id,
    price_display = EXCLUDED.price_display,
    area_sqft = EXCLUDED.area_sqft,
    source = EXCLUDED.source,
    description = EXCLUDED.description,
    owner = EXCLUDED.owner,
    registration_id = EXCLUDED.registration_id,
    verified_status = EXCLUDED.verified_status,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    source_record_hash = EXCLUDED.source_record_hash,
    listing_payload = EXCLUDED.listing_payload,
    updated_at = NOW();
"""


def upsert_records(records: list[dict[str, Any]], batch_size: int = 50) -> list[dict[str, Any]]:
    if not records:
        return []

    initialize_database()
    connection = get_connection()

    try:
        with connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                _ensure_upsert_constraints(cursor)
                payloads = []
                for record in records:
                    payload = dict(record)
                    payload["listing_payload"] = Json(record.get("raw_payload", {}))
                    payloads.append(payload)

                execute_batch(cursor, UPSERT_SQL, payloads, page_size=batch_size)
                cursor.execute(
                    """
                    SELECT id, external_id, title, location, price_numeric, source_record_hash
                    FROM land_listings
                    WHERE source_record_hash = ANY(%s)
                    ORDER BY updated_at DESC
                    """,
                    ([record["source_record_hash"] for record in records],),
                )
                return [dict(row) for row in cursor.fetchall()]
    except Exception:
        connection.rollback()
        logger.exception("PostgreSQL upsert failed; transaction rolled back.")
        raise
    finally:
        connection.close()


def _ensure_upsert_constraints(cursor: Any) -> None:
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_land_listings_title_location_price_unique
        ON land_listings (title, location, price_numeric);
        """
    )


def update_blockchain_status(source_record_hash: str, verification_result: dict[str, Any]) -> None:
    initialize_database()
    connection = get_connection()
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE land_listings
                    SET blockchain_verified = %s,
                        blockchain_hash = %s,
                        blockchain_tx_id = %s,
                        updated_at = NOW()
                    WHERE source_record_hash = %s
                    """,
                    (
                        bool(verification_result.get("verified")),
                        verification_result.get("hash"),
                        verification_result.get("tx_id"),
                        source_record_hash,
                    ),
                )
    except Exception:
        connection.rollback()
        logger.exception("Failed to update blockchain status for record hash %s.", source_record_hash)
        raise
    finally:
        connection.close()

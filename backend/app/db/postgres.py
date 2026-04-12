from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

from shared.logger import get_logger


logger = get_logger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


def _database_settings() -> dict[str, Any]:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return {"dsn": database_url}

    return {
        "host": os.getenv("POSTGRES_HOST", os.getenv("PGHOST", "127.0.0.1")),
        "port": int(os.getenv("POSTGRES_PORT", os.getenv("PGPORT", "5432"))),
        "dbname": os.getenv("POSTGRES_DB", os.getenv("PGDATABASE", "real_estate")),
        "user": os.getenv("POSTGRES_USER", os.getenv("PGUSER", "postgres")),
        "password": os.getenv("POSTGRES_PASSWORD", os.getenv("PGPASSWORD", "postgres")),
    }


def get_connection():
    settings = _database_settings()
    if "dsn" in settings:
        return psycopg2.connect(settings["dsn"])
    return psycopg2.connect(**settings)


def initialize_database() -> None:
    connection = get_connection()
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS land_listings (
                        id SERIAL PRIMARY KEY,
                        external_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        price_display TEXT NOT NULL,
                        price_numeric NUMERIC(14, 2) NOT NULL,
                        location TEXT NOT NULL,
                        area_sqft NUMERIC(14, 2),
                        source TEXT NOT NULL,
                        description TEXT NOT NULL,
                        owner TEXT,
                        registration_id TEXT,
                        verified_status BOOLEAN DEFAULT FALSE,
                        latitude DOUBLE PRECISION,
                        longitude DOUBLE PRECISION,
                        source_record_hash TEXT NOT NULL UNIQUE,
                        listing_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                        blockchain_verified BOOLEAN DEFAULT FALSE,
                        blockchain_hash TEXT,
                        blockchain_tx_id TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_land_listings_location
                    ON land_listings (location);
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_land_listings_coordinates
                    ON land_listings (latitude, longitude);
                    """
                )
    finally:
        connection.close()


def fetch_all_dicts(query: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
    initialize_database()
    connection = get_connection()
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def fetch_one_dict(query: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
    initialize_database()
    connection = get_connection()
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    finally:
        connection.close()


@contextmanager
def transaction() -> Iterator[Any]:
    initialize_database()
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        logger.exception("Database transaction failed and was rolled back.")
        raise
    finally:
        connection.close()

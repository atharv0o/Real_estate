from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import psycopg2
from dotenv import load_dotenv


SERVICE_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(SERVICE_ROOT / ".env")


def _database_settings() -> dict[str, Any]:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return {"dsn": database_url}

    return {
        "host": os.getenv("POSTGRES_HOST", os.getenv("PGHOST", "127.0.0.1")),
        "port": int(os.getenv("POSTGRES_PORT", os.getenv("PGPORT", "5432"))),
        "dbname": os.getenv("POSTGRES_DB", os.getenv("PGDATABASE", "realestate")),
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
    finally:
        connection.close()

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Any

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

from rag_engine.embeddings.embedder import get_embeddings
from rag_engine.embeddings.vector_store import VectorStore
from rag_engine.generation.llm_client import generate_response
from rag_engine.generation.prompt_templates import build_prompt
from rag_engine.retrieval.retriever import retrieve


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
INDEX_PATH = Path(os.getenv("VECTOR_INDEX_PATH", PROJECT_ROOT / "rag_engine" / "storage" / "property_index.faiss"))
METADATA_PATH = Path(os.getenv("VECTOR_METADATA_PATH", PROJECT_ROOT / "rag_engine" / "storage" / "property_documents.json"))
VECTOR_DIM = int(os.getenv("VECTOR_DIM", "384"))
DEFAULT_DOCS = [
    "Land prices vary by micro-market connectivity, demand, and title clarity.",
    "Registry verified land parcels are typically more trustworthy for due diligence workflows.",
    "Plots near transport corridors often carry higher redevelopment potential.",
]

logger = logging.getLogger(__name__)
_vector_store: VectorStore | None = None
_last_loaded_signature: tuple[float, float] | None = None


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


def _fetch_database_documents() -> list[dict[str, Any]]:
    settings = _database_settings()
    try:
        if "dsn" in settings:
            connection = psycopg2.connect(settings["dsn"])
        else:
            connection = psycopg2.connect(**settings)
    except Exception:
        return []

    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    source_record_hash,
                    title,
                    location,
                    description,
                    price_numeric,
                    source,
                    latitude,
                    longitude
                FROM land_listings
                ORDER BY updated_at DESC
                LIMIT 2000
                """
            )
            return [dict(row) for row in cursor.fetchall()]
    except Exception:
        return []
    finally:
        connection.close()


def _file_signature() -> tuple[float, float]:
    index_mtime = INDEX_PATH.stat().st_mtime if INDEX_PATH.exists() else 0.0
    metadata_mtime = METADATA_PATH.stat().st_mtime if METADATA_PATH.exists() else 0.0
    return (index_mtime, metadata_mtime)


def _build_default_store() -> VectorStore:
    store = VectorStore(dim=VECTOR_DIM, index_path=INDEX_PATH, metadata_path=METADATA_PATH)
    database_rows = _fetch_database_documents()
    if database_rows:
        texts = [
            "\n".join(
                part
                for part in [
                    str(row.get("title") or "").strip(),
                    str(row.get("location") or "").strip(),
                    str(row.get("description") or "").strip(),
                ]
                if part
            )
            for row in database_rows
        ]
        embeddings = get_embeddings(texts)
        store.upsert(
            ids=[str(row.get("source_record_hash") or f"row-{index}") for index, row in enumerate(database_rows)],
            embeddings=embeddings,
            texts=texts,
            metadata=[
                {
                    "title": row.get("title"),
                    "location": row.get("location"),
                    "price_numeric": row.get("price_numeric"),
                    "source": row.get("source"),
                    "lat": row.get("latitude"),
                    "lng": row.get("longitude"),
                }
                for row in database_rows
            ],
        )
    elif not store.texts:
        embeddings = get_embeddings(DEFAULT_DOCS)
        store.upsert(
            ids=[f"default-{index}" for index in range(len(DEFAULT_DOCS))],
            embeddings=embeddings,
            texts=DEFAULT_DOCS,
            metadata=[{"source": "bootstrap"} for _ in DEFAULT_DOCS],
        )
    return store


def refresh_vector_store(force: bool = False) -> VectorStore:
    global _vector_store, _last_loaded_signature

    signature = _file_signature()
    if force or _vector_store is None or _last_loaded_signature != signature:
        _vector_store = _build_default_store()
        _last_loaded_signature = _file_signature()
    return _vector_store


def run_rag(query, location: str | None = None, property_context: dict[str, Any] | str | None = None):
    vector_store = refresh_vector_store()
    logger.debug(
        "Running RAG query: location=%s has_property_context=%s",
        location,
        bool(property_context),
    )
    docs = retrieve(query, vector_store, user_location=location)
    property_context_text = None
    if isinstance(property_context, dict):
        property_context_text = "\n".join(
            f"{key}: {value}" for key, value in property_context.items() if value not in (None, "")
        )
    elif isinstance(property_context, str) and property_context.strip():
        property_context_text = property_context.strip()

    context_docs = list(docs)
    if property_context_text:
        context_docs = [property_context_text, *context_docs]

    prompt = build_prompt(query, context_docs, location=location, property_context=property_context_text)
    return generate_response(prompt)

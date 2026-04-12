from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from data_pipeline.bootstrap import ensure_project_root


PROJECT_ROOT = ensure_project_root()
load_dotenv(PROJECT_ROOT / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class PipelineSettings:
    google_maps_api_key: str | None
    listing_source_url: str | None
    listing_request_timeout: int
    enable_blockchain_hook: bool
    blockchain_service_url: str
    rag_refresh_url: str | None
    scheduler_interval_minutes: int
    vector_dim: int
    vector_index_path: Path
    vector_metadata_path: Path
    geocoding_seed_lat: float
    geocoding_seed_lng: float
    log_level: str

    @classmethod
    def load(cls) -> "PipelineSettings":
        storage_root = PROJECT_ROOT / "rag_engine" / "storage"
        storage_root.mkdir(parents=True, exist_ok=True)
        return cls(
            google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY"),
            listing_source_url=os.getenv("LISTING_SOURCE_URL"),
            listing_request_timeout=int(os.getenv("LISTING_REQUEST_TIMEOUT", "10")),
            enable_blockchain_hook=_as_bool(os.getenv("ENABLE_BLOCKCHAIN_HOOK"), default=False),
            blockchain_service_url=os.getenv("BLOCKCHAIN_SERVICE_URL", "http://127.0.0.1:8002/verify"),
            rag_refresh_url=os.getenv("RAG_REFRESH_URL", "http://127.0.0.1:8001/refresh-index"),
            scheduler_interval_minutes=int(os.getenv("PIPELINE_SCHEDULE_MINUTES", "60")),
            vector_dim=int(os.getenv("VECTOR_DIM", "384")),
            vector_index_path=Path(os.getenv("VECTOR_INDEX_PATH", storage_root / "property_index.faiss")),
            vector_metadata_path=Path(os.getenv("VECTOR_METADATA_PATH", storage_root / "property_documents.json")),
            geocoding_seed_lat=float(os.getenv("GEOCODING_SEED_LAT", "18.5204")),
            geocoding_seed_lng=float(os.getenv("GEOCODING_SEED_LNG", "73.8567")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

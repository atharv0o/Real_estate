from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.services.geo_utils import haversine
from app.services.property_service import get_filtered_properties

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_PROPERTIES_PATH = _REPO_ROOT / "backend" / "data" / "properties.json"
_json_cache: list[dict[str, Any]] | None = None
_json_mtime: float | None = None
logger = get_logger(__name__)


def _ensure_pipeline_imports() -> tuple[Any, Any, Any, Any]:
    try:
        from data_pipeline.config import PipelineSettings
        from data_pipeline.loaders.db_loader import upsert_records
        from data_pipeline.loaders.vector_loader import load_vectors
        from data_pipeline.processors.property_processor import process_properties as pipeline_process_properties
    except ImportError as exc:
        logger.warning("Optional data_pipeline package is unavailable: %s", exc)
        return None, None, None, None

    return PipelineSettings, pipeline_process_properties, upsert_records, load_vectors


def load_properties_from_json(path: Path | None = None) -> list[dict[str, Any]]:
    global _json_cache, _json_mtime
    target = path or _PROPERTIES_PATH
    if not target.is_file():
        return []

    mtime = target.stat().st_mtime
    if _json_cache is not None and _json_mtime == mtime:
        return _json_cache

    with target.open(encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, list):
        return []
    _json_cache = [x for x in data if isinstance(x, dict)]
    _json_mtime = mtime
    return _json_cache


def filter_properties_by_location(
    properties: list[dict[str, Any]],
    lat: float,
    lng: float,
    radius_km: float,
    *,
    area: str = "",
    city: str = "",
    district: str = "",
    pincode: str = "",
) -> list[dict[str, Any]]:
    area_l = area.strip().lower()
    city_l = city.strip().lower()
    district_l = district.strip().lower()
    pin_l = pincode.strip()

    out: list[dict[str, Any]] = []
    for p in properties:
        try:
            plat = float(p.get("lat"))
            plng = float(p.get("lng"))
        except (TypeError, ValueError):
            continue

        dist_km = haversine(lat, lng, plat, plng)
        if dist_km > radius_km:
            continue

        hay = " ".join(
            str(p.get(k) or "")
            for k in (
                "title",
                "location",
                "address",
                "city",
                "district",
                "normalized_location",
                "search_text",
                "pincode",
            )
        ).lower()

        if area_l and area_l not in hay:
            continue
        if city_l and city_l not in hay:
            continue
        if district_l and district_l not in hay:
            continue
        if pin_l and pin_l and pin_l not in str(p.get("pincode") or "") and pin_l not in hay:
            continue

        row = dict(p)
        row["distance_km"] = round(dist_km, 3)
        out.append(row)

    out.sort(key=lambda x: float(x.get("distance_km") or 9e9))
    return out


def clean_and_deduplicate(properties: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _, pipeline_process_properties, _, _ = _ensure_pipeline_imports()
    if pipeline_process_properties is None:
        return properties
    return pipeline_process_properties(properties)


def process_and_store(properties: list[dict[str, Any]]) -> dict[str, Any]:
    PipelineSettings, pipeline_process_properties, upsert_records, load_vectors = _ensure_pipeline_imports()
    if pipeline_process_properties is None or PipelineSettings is None:
        return {"upserted": 0, "vector_notify_count": 0, "skipped": True}

    rows = pipeline_process_properties(properties)
    inserted = 0
    if rows and upsert_records is not None:
        try:
            upsert_records(rows, batch_size=100)
            inserted = len(rows)
        except Exception as exc:
            logger.warning("Property upsert skipped because database sync failed: %s", exc)

    vectors = 0
    if rows and load_vectors is not None:
        try:
            settings = PipelineSettings.load()
            vectors = load_vectors(rows, settings)
        except Exception as exc:
            logger.warning("Vector refresh skipped because downstream indexing failed: %s", exc)

    return {"upserted": inserted, "vector_notify_count": vectors}


def search_properties_from_json(
    lat: float,
    lng: float,
    radius: float,
    *,
    min_price: float | None = None,
    max_price: float | None = None,
    area: str = "",
    city: str = "",
    district: str = "",
    pincode: str = "",
) -> dict[str, Any]:
    catalog = load_properties_from_json()
    filtered = filter_properties_by_location(
        catalog,
        lat,
        lng,
        radius,
        area=area,
        city=city,
        district=district,
        pincode=pincode,
    )

    priced: list[dict[str, Any]] = []
    for item in filtered:
        price_numeric = item.get("price_numeric")
        try:
            value = float(price_numeric) if price_numeric is not None else None
        except (TypeError, ValueError):
            value = None

        if min_price is not None and value is not None and value < float(min_price):
            continue
        if max_price is not None and value is not None and value > float(max_price):
            continue
        priced.append(item)

    return {"count": len(priced), "properties": priced}


def get_properties(
    lat: float,
    lng: float,
    radius: float,
    min_price: float | None = None,
    max_price: float | None = None,
) -> dict:
    try:
        payload = get_filtered_properties(
            lat=lat,
            lng=lng,
            radius_km=radius,
            min_price=min_price,
            max_price=max_price,
        )
        if payload.get("properties"):
            return payload
    except Exception as exc:
        logger.warning("Database-backed property search failed, using JSON fallback: %s", exc)

    return search_properties_from_json(
        lat=lat,
        lng=lng,
        radius=radius,
        min_price=min_price,
        max_price=max_price,
    )

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.services.geo_service import get_location_coordinates

logger = get_logger(__name__)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_PROPERTIES_PATH = _REPO_ROOT / "backend" / "data" / "properties.json"


def _load_json_properties() -> list[dict[str, Any]]:
    if not _PROPERTIES_PATH.is_file():
        return []
    with _PROPERTIES_PATH.open(encoding="utf-8") as file:
        data = json.load(file)
    return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []


def _resolve_from_json(query: str) -> dict[str, Any] | None:
    tokens = [token.strip().lower() for token in query.split(",") if token.strip()]
    if not tokens:
        return None

    matches: list[dict[str, Any]] = []
    for record in _load_json_properties():
        try:
            lat = float(record.get("lat"))
            lng = float(record.get("lng"))
        except (TypeError, ValueError):
            continue

        haystacks = [
            str(record.get("title") or "").lower(),
            str(record.get("location") or "").lower(),
            str(record.get("address") or "").lower(),
            str(record.get("city") or "").lower(),
            str(record.get("district") or "").lower(),
            str(record.get("state") or "").lower(),
            str(record.get("pincode") or "").lower(),
            str(record.get("normalized_location") or "").lower(),
            str(record.get("search_text") or "").lower(),
        ]
        text = " ".join(haystacks)
        score = sum(1 for token in tokens if token in text)
        if score == 0:
            continue
        if score == len(tokens) or score >= 2 or len(tokens) == 1:
            matches.append({"lat": lat, "lng": lng, "score": score, "record": record})

    if not matches:
        return None

    matches.sort(key=lambda item: item["score"], reverse=True)
    top_score = matches[0]["score"]
    top = matches[: min(200, len(matches))]
    top = [item for item in top if item["score"] == top_score]

    avg_lat = round(sum(item["lat"] for item in top) / len(top), 6)
    avg_lng = round(sum(item["lng"] for item in top) / len(top), 6)
    label = str(top[0]["record"].get("city") or top[0]["record"].get("location") or query)
    return {
        "query": query,
        "label": label,
        "lat": avg_lat,
        "lng": avg_lng,
        "source": "dataset",
        "match_count": len(top),
    }


def resolve_location(query: str) -> dict:
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("Location query is required")

    stored = None
    try:
        stored = get_location_coordinates(normalized_query)
    except Exception as exc:
        logger.warning("Location lookup via database failed, using deterministic fallback: %s", exc)

    if stored:
        return {
            "query": normalized_query,
            "label": stored["location"],
            "lat": stored["lat"],
            "lng": stored["lng"],
            "source": "database",
        }

    try:
        dataset_match = _resolve_from_json(normalized_query)
    except Exception as exc:
        logger.warning("Location lookup via dataset failed, using deterministic fallback: %s", exc)
        dataset_match = None

    if dataset_match:
        return dataset_match

    digest = hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()
    lat = round(18.5204 + (int(digest[:8], 16) % 1000) / 10000, 6)
    lng = round(73.8567 + (int(digest[8:16], 16) % 1000) / 10000, 6)
    return {
        "query": normalized_query,
        "label": normalized_query,
        "lat": lat,
        "lng": lng,
        "source": "fallback",
    }

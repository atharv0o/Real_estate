from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Iterable

from app.core.logging import get_logger
from app.services.geo_utils import haversine
from app.services.search_cache import get_cached, make_cache_key, set_cached

logger = get_logger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PROPERTIES_PATH = _REPO_ROOT / "backend" / "data" / "properties.json"
_INDEX_LOCK = RLock()
_INDEX_GRID_SIZE_DEGREES = float(os.getenv("SEARCH_GRID_SIZE_DEGREES", "0.02"))
_MAX_PAGE_SIZE = int(os.getenv("SEARCH_MAX_PAGE_SIZE", "100"))
_SEARCH_RESULT_TTL_SECONDS = float(os.getenv("SEARCH_CACHE_TTL_SECONDS", "300"))


@dataclass(slots=True)
class SearchIndex:
    properties: list[dict[str, Any]]
    searchable_text: list[str]
    city_index: dict[str, set[int]]
    district_index: dict[str, set[int]]
    pincode_index: dict[str, set[int]]
    location_index: dict[str, set[int]]
    token_index: dict[str, set[int]]
    bucket_index: dict[tuple[int, int], set[int]]
    coordinates: list[tuple[float, float] | None]
    file_mtime: float
    file_size: int


@dataclass(slots=True)
class SearchBenchmarkResult:
    legacy_ms: float
    optimized_ms: float
    improvement_pct: float
    candidate_count: int
    result_count: int


_SEARCH_INDEX: SearchIndex | None = None


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _tokenize(value: str) -> list[str]:
    tokens: list[str] = []
    token = []
    for char in value.lower():
        if char.isalnum():
            token.append(char)
            continue
        if token:
            next_token = "".join(token)
            if next_token:
                tokens.append(next_token)
            token = []
    if token:
        next_token = "".join(token)
        if next_token:
            tokens.append(next_token)
    return tokens


def _bucket_for(lat: float, lng: float, grid_size: float = _INDEX_GRID_SIZE_DEGREES) -> tuple[int, int]:
    return (math.floor(lat / grid_size), math.floor(lng / grid_size))


def _records_from_path(path: Path) -> tuple[list[dict[str, Any]], float, int]:
    if not path.is_file():
        return [], 0.0, 0

    stat = path.stat()
    import json

    with path.open(encoding="utf-8-sig") as file:
        data = json.load(file)
    if not isinstance(data, list):
        return [], stat.st_mtime, stat.st_size

    records = [item for item in data if isinstance(item, dict)]
    return records, stat.st_mtime, stat.st_size


def _index_records(records: list[dict[str, Any]], *, file_mtime: float, file_size: int) -> SearchIndex:
    searchable_text: list[str] = []
    city_index: dict[str, set[int]] = {}
    district_index: dict[str, set[int]] = {}
    pincode_index: dict[str, set[int]] = {}
    location_index: dict[str, set[int]] = {}
    token_index: dict[str, set[int]] = {}
    bucket_index: dict[tuple[int, int], set[int]] = {}
    coordinates: list[tuple[float, float] | None] = []

    for idx, record in enumerate(records):
        title = _normalize_text(record.get("title"))
        location = _normalize_text(record.get("location"))
        address = _normalize_text(record.get("address"))
        city = _normalize_text(record.get("city"))
        district = _normalize_text(record.get("district"))
        state = _normalize_text(record.get("state"))
        pincode = _normalize_text(record.get("pincode"))
        normalized_location = _normalize_text(record.get("normalized_location"))
        search_text = _normalize_text(
            " ".join(
                value
                for value in (title, location, address, city, district, state, pincode, normalized_location, _normalize_text(record.get("search_text")))
                if value
            )
        )
        searchable_text.append(search_text)

        for key, index in (
            (city, city_index),
            (district, district_index),
            (pincode, pincode_index),
            (location, location_index),
        ):
            if not key:
                continue
            index.setdefault(key, set()).add(idx)

        for token in _tokenize(search_text):
            token_index.setdefault(token, set()).add(idx)

        try:
            lat = float(record.get("lat"))
            lng = float(record.get("lng"))
            coordinates.append((lat, lng))
            bucket_index.setdefault(_bucket_for(lat, lng), set()).add(idx)
        except (TypeError, ValueError):
            coordinates.append(None)

    return SearchIndex(
        properties=records,
        searchable_text=searchable_text,
        city_index=city_index,
        district_index=district_index,
        pincode_index=pincode_index,
        location_index=location_index,
        token_index=token_index,
        bucket_index=bucket_index,
        coordinates=coordinates,
        file_mtime=file_mtime,
        file_size=file_size,
    )


def _load_index(force_reload: bool = False) -> SearchIndex:
    global _SEARCH_INDEX
    with _INDEX_LOCK:
        path = _PROPERTIES_PATH
        if not path.is_file():
            empty = SearchIndex([], [], {}, {}, {}, {}, {}, {}, [], 0.0, 0)
            _SEARCH_INDEX = empty
            return empty

        stat = path.stat()
        if _SEARCH_INDEX is not None and not force_reload:
            if _SEARCH_INDEX.file_mtime == stat.st_mtime and _SEARCH_INDEX.file_size == stat.st_size:
                return _SEARCH_INDEX

        records, mtime, size = _records_from_path(path)
        index = _index_records(records, file_mtime=mtime, file_size=size)
        _SEARCH_INDEX = index
        logger.info("Built property search index with %s records", len(records))
        return index


def build_search_index() -> SearchIndex:
    return _load_index(force_reload=False)


def refresh_search_index() -> SearchIndex:
    return _load_index(force_reload=True)


def warm_search_structures() -> SearchIndex:
    return build_search_index()


def load_properties_from_json(path: Path | None = None) -> list[dict[str, Any]]:
    if path is None or path == _PROPERTIES_PATH:
        return build_search_index().properties

    records, _, _ = _records_from_path(path)
    return records


def _candidate_ids_from_filters(
    index: SearchIndex,
    *,
    area: str = "",
    city: str = "",
    district: str = "",
    pincode: str = "",
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float | None = None,
) -> set[int]:
    candidate_ids: set[int] | None = None

    def _merge(existing: set[int] | None, incoming: Iterable[int]) -> set[int]:
        incoming_set = set(incoming)
        if not incoming_set:
            return existing or set()
        if existing is None:
            return incoming_set
        if not existing:
            return incoming_set
        return existing & incoming_set

    if city:
        candidate_ids = _merge(candidate_ids, index.city_index.get(_normalize_text(city), set()))
    if district:
        candidate_ids = _merge(candidate_ids, index.district_index.get(_normalize_text(district), set()))
    if pincode:
        pin = _normalize_text(pincode)
        pin_ids = index.pincode_index.get(pin, set())
        if pin_ids:
            if candidate_ids is None:
                candidate_ids = set(pin_ids)
            else:
                narrowed = candidate_ids & pin_ids
                if narrowed:
                    candidate_ids = narrowed

    tokens = [token for token in _tokenize(_normalize_text(area)) if token]
    if tokens:
        token_matches: set[int] | None = None
        for token in tokens:
            token_ids = index.token_index.get(token)
            if not token_ids:
                continue
            token_matches = token_ids if token_matches is None else token_matches & token_ids
        if token_matches:
            candidate_ids = _merge(candidate_ids, token_matches)

    if lat is not None and lng is not None and radius_km is not None:
        span = max(1, int(math.ceil(radius_km / max(_INDEX_GRID_SIZE_DEGREES * 111.32, 0.25))))
        base_lat, base_lng = _bucket_for(lat, lng)
        nearby: set[int] = set()
        for lat_bucket in range(base_lat - span, base_lat + span + 1):
            for lng_bucket in range(base_lng - span, base_lng + span + 1):
                nearby.update(index.bucket_index.get((lat_bucket, lng_bucket), set()))
        candidate_ids = _merge(candidate_ids, nearby)

    if candidate_ids is None:
        return set(range(len(index.properties)))
    return candidate_ids


def _matches_text_filters(
    text: str,
    *,
    area: str = "",
    city: str = "",
    district: str = "",
    pincode: str = "",
    record: dict[str, Any] | None = None,
) -> bool:
    if area:
        area_norm = _normalize_text(area)
        if area_norm and area_norm not in text:
            return False
    if city:
        city_norm = _normalize_text(city)
        if city_norm and city_norm not in text:
            return False
    if district:
        district_norm = _normalize_text(district)
        if district_norm and district_norm not in text:
            return False
    if pincode:
        pin_norm = _normalize_text(pincode)
        if pin_norm:
            record_pin = _normalize_text(record.get("pincode") if record else "")
            has_location_filter = bool(area or city or district)
            if not has_location_filter and record_pin and pin_norm not in record_pin:
                return False
    return True


def _search_records(
    records: list[dict[str, Any]],
    *,
    lat: float,
    lng: float,
    radius_km: float,
    area: str = "",
    city: str = "",
    district: str = "",
    pincode: str = "",
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for record in records:
        try:
            plat = float(record.get("lat"))
            plng = float(record.get("lng"))
        except (TypeError, ValueError):
            continue

        price_raw = record.get("price_numeric")
        try:
            price_value = float(price_raw) if price_raw is not None else None
        except (TypeError, ValueError):
            price_value = None

        if min_price is not None and price_value is not None and price_value < float(min_price):
            continue
        if max_price is not None and price_value is not None and price_value > float(max_price):
            continue

        distance_km = haversine(lat, lng, plat, plng)
        if distance_km > radius_km:
            continue

        hay = _normalize_text(
            " ".join(
                str(record.get(k) or "")
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
            )
        )
        if not _matches_text_filters(hay, area=area, city=city, district=district, pincode=pincode, record=record):
            continue

        row = dict(record)
        row["distance_km"] = round(distance_km, 3)
        matches.append(row)

    matches.sort(key=lambda item: float(item.get("distance_km") or 9e9))
    return matches


def _search_with_global_index(
    index: SearchIndex,
    *,
    lat: float,
    lng: float,
    radius_km: float,
    area: str = "",
    city: str = "",
    district: str = "",
    pincode: str = "",
    min_price: float | None = None,
    max_price: float | None = None,
) -> tuple[list[dict[str, Any]], int, int, float, float]:
    start_total = time.perf_counter()
    candidate_started = time.perf_counter()
    candidate_ids = _candidate_ids_from_filters(
        index,
        area=area,
        city=city,
        district=district,
        pincode=pincode,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
    )
    candidate_ms = (time.perf_counter() - candidate_started) * 1000.0

    distance_started = time.perf_counter()
    matches: list[dict[str, Any]] = []
    for idx in candidate_ids:
        record = index.properties[idx]
        coord = index.coordinates[idx]
        if coord is None:
            continue
        plat, plng = coord

        price_raw = record.get("price_numeric")
        try:
            price_value = float(price_raw) if price_raw is not None else None
        except (TypeError, ValueError):
            price_value = None

        if min_price is not None and price_value is not None and price_value < float(min_price):
            continue
        if max_price is not None and price_value is not None and price_value > float(max_price):
            continue

        distance_km = haversine(lat, lng, plat, plng)
        if distance_km > radius_km:
            continue

        text = index.searchable_text[idx]
        if not _matches_text_filters(text, area=area, city=city, district=district, pincode=pincode, record=record):
            continue

        row = dict(record)
        row["distance_km"] = round(distance_km, 3)
        matches.append(row)
    distance_ms = (time.perf_counter() - distance_started) * 1000.0

    matches.sort(key=lambda item: float(item.get("distance_km") or 9e9))
    total_ms = (time.perf_counter() - start_total) * 1000.0
    logger.info(
        "SEARCH PERFORMANCE | candidate filtering: %.2fms | haversine: %.2fms | total: %.2fms | candidates=%s | results=%s",
        candidate_ms,
        distance_ms,
        total_ms,
        len(candidate_ids),
        len(matches),
    )
    return matches, len(candidate_ids), len(matches), candidate_ms, distance_ms


def _paginate(records: list[dict[str, Any]], *, limit: int, offset: int) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit), _MAX_PAGE_SIZE))
    safe_offset = max(0, int(offset))
    return records[safe_offset : safe_offset + safe_limit]


def search_indexed_properties(
    lat: float,
    lng: float,
    radius_km: float,
    *,
    area: str = "",
    city: str = "",
    district: str = "",
    pincode: str = "",
    min_price: float | None = None,
    max_price: float | None = None,
    limit: int = 25,
    offset: int = 0,
    page: int | None = None,
    properties: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if properties is None:
        safe_limit = max(1, min(int(limit), _MAX_PAGE_SIZE))
    else:
        safe_limit = max(1, int(limit))
    safe_offset = max(0, int(offset))
    if page is not None and page > 0 and safe_offset == 0:
        safe_offset = (int(page) - 1) * safe_limit

    cache_key = None
    index: SearchIndex | None = None
    if properties is None:
        index = build_search_index()
        cache_key = make_cache_key(
            "search:indexed",
            {
                "lat": round(float(lat), 6),
                "lng": round(float(lng), 6),
                "radius_km": round(float(radius_km), 3),
                "area": area.strip().lower(),
                "city": city.strip().lower(),
                "district": district.strip().lower(),
                "pincode": pincode.strip().lower(),
                "min_price": min_price,
                "max_price": max_price,
                "limit": safe_limit,
                "offset": safe_offset,
                "page": page,
                "mtime": index.file_mtime,
            },
        )
        cached = get_cached(cache_key)
        if cached is not None:
            return cached

    if properties is None:
        assert index is not None
        matches, candidate_count, result_count, _, _ = _search_with_global_index(
            index,
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            area=area,
            city=city,
            district=district,
            pincode=pincode,
            min_price=min_price,
            max_price=max_price,
        )
    else:
        matches = _search_records(
            [row for row in properties if isinstance(row, dict)],
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            area=area,
            city=city,
            district=district,
            pincode=pincode,
            min_price=min_price,
            max_price=max_price,
        )

    paged = _paginate(matches, limit=safe_limit, offset=safe_offset)
    payload = {
        "count": len(paged),
        "total_count": len(matches),
        "limit": safe_limit,
        "offset": safe_offset,
        "page": (safe_offset // safe_limit) + 1,
        "properties": paged,
    }
    if cache_key is not None:
        set_cached(cache_key, payload, ttl_seconds=_SEARCH_RESULT_TTL_SECONDS)
    return payload


def resolve_location_from_index(query: str) -> dict[str, Any] | None:
    normalized_query = _normalize_text(query)
    if not normalized_query:
        return None

    index = build_search_index()
    tokens = [token for token in _tokenize(normalized_query) if token]
    if not tokens:
        return None

    candidate_ids: set[int] | None = None
    for token in tokens:
        token_ids = index.token_index.get(token)
        if not token_ids:
            continue
        candidate_ids = token_ids if candidate_ids is None else candidate_ids & token_ids

    if candidate_ids is None or not candidate_ids:
        return None

    scored: list[tuple[int, int]] = []
    for idx in candidate_ids:
        hay = index.searchable_text[idx]
        score = sum(1 for token in tokens if token in hay)
        if score:
            scored.append((score, idx))

    if not scored:
        return None

    scored.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    top_score = scored[0][0]
    top_indices = [idx for score, idx in scored[:200] if score == top_score]
    coords = [index.coordinates[idx] for idx in top_indices if index.coordinates[idx] is not None]
    if not coords:
        return None

    avg_lat = round(sum(lat for lat, _ in coords) / len(coords), 6)
    avg_lng = round(sum(lng for _, lng in coords) / len(coords), 6)
    first_record = index.properties[top_indices[0]]
    label = str(first_record.get("city") or first_record.get("location") or query)
    return {
        "query": query,
        "label": label,
        "lat": avg_lat,
        "lng": avg_lng,
        "source": "dataset_index",
        "match_count": len(top_indices),
    }


def benchmark_search(
    *,
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float = 5.0,
    area: str = "",
    city: str = "",
    district: str = "",
    pincode: str = "",
    min_price: float | None = None,
    max_price: float | None = None,
) -> dict[str, Any]:
    index = build_search_index()
    if not index.properties:
        return {
            "legacy_ms": 0.0,
            "optimized_ms": 0.0,
            "improvement_pct": 0.0,
            "candidate_count": 0,
            "result_count": 0,
        }

    sample = next((row for row in index.properties if isinstance(row.get("lat"), (int, float)) and isinstance(row.get("lng"), (int, float))), index.properties[0])
    sample_lat = float(lat if lat is not None else sample.get("lat") or 0.0)
    sample_lng = float(lng if lng is not None else sample.get("lng") or 0.0)

    legacy_started = time.perf_counter()
    legacy_results = _search_records(
        index.properties,
        lat=sample_lat,
        lng=sample_lng,
        radius_km=radius_km,
        area=area or str(sample.get("city") or ""),
        city=city or str(sample.get("city") or ""),
        district=district or str(sample.get("district") or ""),
        pincode=pincode or str(sample.get("pincode") or ""),
        min_price=min_price,
        max_price=max_price,
    )
    legacy_ms = (time.perf_counter() - legacy_started) * 1000.0

    optimized_started = time.perf_counter()
    optimized = search_indexed_properties(
        sample_lat,
        sample_lng,
        radius_km,
        area=area or str(sample.get("city") or ""),
        city=city or str(sample.get("city") or ""),
        district=district or str(sample.get("district") or ""),
        pincode=pincode or str(sample.get("pincode") or ""),
        min_price=min_price,
        max_price=max_price,
        limit=25,
        offset=0,
    )
    optimized_ms = (time.perf_counter() - optimized_started) * 1000.0

    improvement_pct = 0.0
    if legacy_ms > 0:
        improvement_pct = max(0.0, round(((legacy_ms - optimized_ms) / legacy_ms) * 100.0, 2))

    result = SearchBenchmarkResult(
        legacy_ms=round(legacy_ms, 2),
        optimized_ms=round(optimized_ms, 2),
        improvement_pct=improvement_pct,
        candidate_count=int(optimized.get("total_count", len(optimized.get("properties", [])))),
        result_count=len(optimized.get("properties", [])),
    )
    logger.info(
        "SEARCH BENCHMARK | legacy: %.2fms | optimized: %.2fms | improvement: %.2f%% | results=%s",
        result.legacy_ms,
        result.optimized_ms,
        result.improvement_pct,
        result.result_count,
    )
    return {
        "legacy_ms": result.legacy_ms,
        "optimized_ms": result.optimized_ms,
        "improvement_pct": result.improvement_pct,
        "candidate_count": result.candidate_count,
        "result_count": result.result_count,
    }

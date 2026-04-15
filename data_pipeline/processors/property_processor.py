from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from typing import Any

from data_pipeline.logging_utils import get_logger

logger = get_logger(__name__)

PRICE_NUMBER_PATTERN = re.compile(r"[\d,.]+")
WORD_SPLIT = re.compile(r"\W+")


try:
    from rapidfuzz import fuzz as _fuzz
except ImportError:  # pragma: no cover
    try:
        from fuzzywuzzy import fuzz as _fuzz  # type: ignore
    except ImportError:
        _fuzz = None


def _parse_price_to_int(raw_price: Any) -> int | None:
    if raw_price is None:
        return None
    if isinstance(raw_price, (int, float)):
        v = int(float(raw_price))
        return v if v > 0 else None
    text = str(raw_price).replace(",", "").strip()
    if not text:
        return None
    lowered = text.lower()
    if "crore" in lowered or re.search(r"\bcr\b", lowered):
        m = re.search(r"([\d.]+)\s*(?:crore|cr)", lowered)
        if not m:
            return None
        return int(float(m.group(1)) * 10_000_000)
    if "lac" in lowered or "lakh" in lowered:
        m = re.search(r"([\d.]+)\s*(?:lac|lakh)", lowered)
        if m:
            return int(float(m.group(1)) * 100_000)
        nums = PRICE_NUMBER_PATTERN.findall(text)
        if not nums:
            return None
        return int(float(nums[0].replace(",", "")) * 100_000)
    nums = PRICE_NUMBER_PATTERN.findall(text)
    if not nums:
        return None
    v = int(float(nums[0].replace(",", "")))
    return v if v > 0 else None


def _parse_area_sqft(raw: Any) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        value = float(raw)
    else:
        m = re.search(r"[\d,.]+", str(raw))
        if not m:
            return None
        value = float(m.group(0).replace(",", ""))
    return value if 50 <= value <= 5_000_000 else None


def _enrich_text_fields(rec: dict[str, Any]) -> None:
    title = str(rec.get("title") or "").strip()
    loc = str(rec.get("location") or "").strip()
    addr = str(rec.get("address") or "").strip()
    city = str(rec.get("city") or "").strip()
    dist = str(rec.get("district") or "").strip()
    state = str(rec.get("state") or "").strip()
    pin = str(rec.get("pincode") or "").strip()

    parts = [title, addr, city, dist, state, pin]
    rec["search_text"] = " ".join(p for p in parts if p)
    rec["normalized_location"] = loc.lower() if loc else " ".join(parts).lower()
    words = [w for w in WORD_SPLIT.split(rec["search_text"].lower()) if len(w) > 2]
    rec["keywords"] = list(dict.fromkeys(words))[:50]


def _normalize_record(rec: dict[str, Any]) -> dict[str, Any] | None:
    out = deepcopy(rec)
    title = str(out.get("title") or "").strip()
    location = str(out.get("location") or "").strip()
    if not title or not location:
        return None

    src = str(out.get("source") or "json_catalog").strip() or "json_catalog"
    out["source"] = src

    price_numeric = out.get("price_numeric")
    if price_numeric is not None:
        try:
            price_numeric = int(float(price_numeric))
        except (TypeError, ValueError):
            price_numeric = None
    if price_numeric is None:
        price_numeric = _parse_price_to_int(out.get("price"))
    if price_numeric is None or price_numeric <= 0:
        return None

    area_sqft = out.get("area_sqft")
    if area_sqft is not None:
        try:
            area_sqft = float(area_sqft)
        except (TypeError, ValueError):
            area_sqft = None
    if area_sqft is None:
        area_sqft = _parse_area_sqft(out.get("builtup_area") or out.get("carpet_area"))
    if area_sqft is None:
        return None

    try:
        lat = float(out.get("lat"))
        lng = float(out.get("lng"))
    except (TypeError, ValueError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None

    out["price_numeric"] = price_numeric
    out["price"] = str(out.get("price") or price_numeric)
    out["area_sqft"] = float(area_sqft)
    out["lat"] = lat
    out["lng"] = lng
    out["description"] = str(out.get("description") or title).strip()

    ext = str(out.get("external_id") or "").strip()
    if not ext:
        ext = hashlib.sha256(f"{title}|{location}|{price_numeric}".encode()).hexdigest()[:16]
        out["external_id"] = ext

    _enrich_text_fields(out)
    return out


def _to_upsert_row(normalized: dict[str, Any]) -> dict[str, Any]:
    title = normalized["title"]
    location = normalized["location"]
    price_numeric = int(normalized["price_numeric"])
    stable_key = f"{title.strip().lower()}|{location.strip().lower()}|{price_numeric}"
    source_record_hash = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()
    payload = {k: v for k, v in normalized.items() if k not in {"raw_payload"}}
    payload["processed_via"] = "property_processor"

    return {
        "external_id": normalized["external_id"],
        "title": title,
        "price": normalized["price"],
        "price_numeric": price_numeric,
        "location": location,
        "area_sqft": float(normalized["area_sqft"]),
        "source": normalized["source"],
        "description": normalized["description"],
        "owner": normalized.get("owner"),
        "registration_id": normalized.get("registration_id"),
        "verified_status": bool(normalized.get("verified_status", False)),
        "lat": float(normalized["lat"]),
        "lng": float(normalized["lng"]),
        "source_record_hash": source_record_hash,
        "raw_payload": payload,
    }


def _deduplicate_upsert_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduplicated: list[dict[str, Any]] = []
    exact_seen: set[tuple[str, str, int]] = set()

    for record in rows:
        exact_key = (record["title"].lower(), record["location"].lower(), int(record["price_numeric"]))
        if exact_key in exact_seen:
            continue

        duplicate = False
        if _fuzz is not None:
            fp = f"{record['title']} {record['location']} {record['price_numeric']}"
            for existing in deduplicated:
                efp = f"{existing['title']} {existing['location']} {existing['price_numeric']}"
                if _fuzz.token_sort_ratio(fp, efp) > 90:
                    duplicate = True
                    break
        if duplicate:
            continue

        exact_seen.add(exact_key)
        deduplicated.append(record)

    return deduplicated


def process_properties(properties: list[dict]) -> list[dict]:
    """
    Normalize, validate, enrich, deduplicate JSON catalog rows into DB upsert payloads
    (same shape as data_pipeline.loaders.db_loader.upsert_records expects).
    """
    normalized: list[dict[str, Any]] = []
    for raw in properties:
        n = _normalize_record(raw if isinstance(raw, dict) else {})
        if n:
            normalized.append(n)

    upsert_rows = [_to_upsert_row(n) for n in normalized]
    out = _deduplicate_upsert_rows(upsert_rows)
    logger.info("property_processor: %s in -> %s upsert rows", len(properties), len(out))
    return out

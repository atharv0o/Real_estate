from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_pipeline.bootstrap import ensure_project_root
from data_pipeline.config import PipelineSettings

ensure_project_root()

try:
    from rapidfuzz import fuzz as _fuzz
except ImportError:  # pragma: no cover
    try:
        from fuzzywuzzy import fuzz as _fuzz  # type: ignore
    except ImportError:
        _fuzz = None


def _deduplicate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduplicated: list[dict[str, Any]] = []
    exact_seen: set[tuple[str, str, int]] = set()

    for record in records:
        exact_key = (record["title"].lower(), record["location"].lower(), int(record["price_numeric"]))
        if exact_key in exact_seen:
            continue

        duplicate = False
        if _fuzz is not None:
            record_fingerprint = f"{record['title']} {record['location']} {record['price_numeric']}"
            for existing in deduplicated:
                existing_fingerprint = f"{existing['title']} {existing['location']} {existing['price_numeric']}"
                if _fuzz.token_sort_ratio(record_fingerprint, existing_fingerprint) > 90:
                    duplicate = True
                    break
        if duplicate:
            continue

        exact_seen.add(exact_key)
        deduplicated.append(record)

    return deduplicated

PIPELINE_ROOT = Path(__file__).resolve().parent
DATASET_DIR = PIPELINE_ROOT / "dataset"
BACKEND_PROPERTIES = PROJECT_ROOT / "backend" / "data" / "properties.json"

PRICE_NUMBER_PATTERN = re.compile(r"[\d,.]+")
RATE_PER_SQFT_PATTERN = re.compile(r"₹\s*([\d,]+)/sq\.?\s*ft", re.IGNORECASE)
BED_PATTERN = re.compile(r"(\d+)\s*Bedroom", re.IGNORECASE)
BATH_PATTERN = re.compile(r"(\d+)\s*Bathroom", re.IGNORECASE)


def _parse_price_numeric(raw: Any) -> int | None:
    if raw is None or (isinstance(raw, str) and not str(raw).strip()):
        return None
    if isinstance(raw, (int, float)):
        v = int(float(raw))
        return v if v > 0 else None
    text = str(raw).replace(",", "").strip()
    if not text:
        return None
    lowered = text.lower()
    multiplier = 1
    if "crore" in lowered or re.search(r"\bcr\b", lowered):
        multiplier = 10_000_000
        m = re.search(r"([\d.]+)\s*(?:crore|cr)", lowered)
        if not m:
            return None
        base = float(m.group(1))
    elif "lac" in lowered or "lakh" in lowered:
        multiplier = 100_000
        m = re.search(r"([\d.]+)\s*(?:lac|lakh|l\b)", lowered)
        if not m:
            nums = PRICE_NUMBER_PATTERN.findall(text)
            if not nums:
                return None
            base = float(nums[0].replace(",", ""))
        else:
            base = float(m.group(1))
    else:
        nums = PRICE_NUMBER_PATTERN.findall(text)
        if not nums:
            return None
        base = float(nums[0].replace(",", ""))
        if base < 100_000 and multiplier == 1 and ("lac" not in lowered and "crore" not in lowered):
            return None
    value = int(base * multiplier)
    return value if value > 0 else None


def _parse_rate_per_sqft(rate_col: str) -> float:
    if not rate_col:
        return 0.0
    m = RATE_PER_SQFT_PATTERN.search(rate_col.replace(",", ""))
    if m:
        return float(m.group(1).replace(",", ""))
    m = re.search(r"([\d,]+)\s*/\s*sq", rate_col, re.I)
    if m:
        return float(m.group(1).replace(",", ""))
    return 0.0


def _parse_sqft_from_blob(text: str, kind: str) -> tuple[float, float, float]:
    """Returns (primary_area_sqft, builtup, carpet) — best-effort."""
    if not text:
        return 0.0, 0.0, 0.0
    t = text.replace("\n", " ")
    builtup = 0.0
    carpet = 0.0
    plot_sqft = 0.0

    for m in re.finditer(r"Carpet area:?\s*([\d,.]+)", t, re.I):
        carpet = max(carpet, float(m.group(1).replace(",", "")))
    for m in re.finditer(r"Built\s*Up area:?\s*([\d,.]+)", t, re.I):
        builtup = max(builtup, float(m.group(1).replace(",", "")))
    for m in re.finditer(r"Super\s*Built\s*up\s*area\s*([\d,.]+)", t, re.I):
        builtup = max(builtup, float(m.group(1).replace(",", "")))
    for m in re.finditer(r"Plot area\s*([\d,.]+)", t, re.I):
        v = float(m.group(1).replace(",", ""))
        if kind == "house" and v < 800:
            v = v * 9.0
        plot_sqft = max(plot_sqft, v)

    primary = max(builtup, carpet, plot_sqft)
    if primary < 1 and t:
        m = re.search(r"(\d[\d,.]*)\s*\(", t)
        if m:
            v = float(m.group(1).replace(",", ""))
            if kind == "house" and v < 800:
                v = v * 9.0
            primary = v
    return primary, builtup, carpet


def _count_from_cell(cell: str, pattern: re.Pattern[str]) -> int:
    if not cell:
        return 0
    m = pattern.search(cell)
    if not m:
        return 0
    if "no balcony" in cell.lower():
        return 0
    g1, g2 = m.group(1), m.group(2) if m.lastindex and m.lastindex > 1 else None
    if g1:
        return int(g1)
    if g2:
        return int(g2)
    return 0


def _balconies_from_cell(cell: str) -> int:
    if not cell:
        return 0
    low = cell.lower()
    if "no balcony" in low:
        return 0
    m = re.search(r"(\d+)\+", cell)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*Balcon", cell, re.I)
    if m:
        return int(m.group(1))
    return 0


def _parse_address_parts(address: str) -> dict[str, str]:
    out = {
        "city": "",
        "district": "",
        "state": "",
        "country": "India",
        "pincode": "",
    }
    if not address:
        return out
    parts = [p.strip() for p in address.split(",") if p.strip()]
    if not parts:
        return out
    last = parts[-1].lower()
    if last in ("india",):
        parts = parts[:-1]
    if parts:
        tail = parts[-1].lower()
        if tail in ("haryana", "maharashtra", "delhi", "uttar pradesh", "karnataka"):
            out["state"] = parts[-1]
            parts = parts[:-1]
    if parts:
        last_part = parts[-1]
        lp = last_part.lower()
        if "gurgaon" in lp or "gurugram" in lp:
            out["city"] = "Gurugram"
            out["district"] = "Gurugram"
        elif "faridabad" in lp:
            out["city"] = "Faridabad"
            out["district"] = "Faridabad"
        else:
            out["city"] = last_part
            out["district"] = last_part
    m = re.search(r"\b(\d{6})\b", address)
    if m:
        out["pincode"] = m.group(1)
    return out


def _infer_ownership(description: str) -> str:
    low = description.lower()
    if "freehold" in low:
        return "freehold"
    if "leasehold" in low:
        return "leasehold"
    return "unknown"


def _furnishing_from_details(cell: str) -> str:
    if not cell or cell.strip() in ("", "[]"):
        return "unfurnished"
    low = cell.lower()
    if "fully" in low and "furnish" in low:
        return "fully-furnished"
    if "semi" in low and "furnish" in low:
        return "semi-furnished"
    if "unfurnished" in low:
        return "unfurnished"
    if "no " in low and "modular" not in low:
        return "unfurnished"
    return "semi-furnished"


def _jitter_latlng(address: str, city_key: str) -> tuple[float, float]:
    centroids = {
        "gurgaon": (28.4595, 77.0266),
        "faridabad": (28.4089, 77.3178),
        "default": (28.4595, 77.0266),
    }
    base_lat, base_lng = centroids.get(city_key, centroids["default"])
    h = hashlib.sha256(address.encode("utf-8")).digest()
    ix = int.from_bytes(h[:4], "big") / 0xFFFFFFFF
    iy = int.from_bytes(h[4:8], "big") / 0xFFFFFFFF
    return base_lat + (ix - 0.5) * 0.08, base_lng + (iy - 0.5) * 0.08


def _city_key_from_address(address: str) -> str:
    a = address.lower()
    if "faridabad" in a:
        return "faridabad"
    return "gurgaon"


def _row_to_listing(row: dict[str, str], kind: str) -> dict[str, Any] | None:
    title = (row.get("property_name") or "").strip()
    address = (row.get("address") or "").strip()
    prop_id = (row.get("property_id") or "").strip()
    if not title or not prop_id:
        return None

    price_raw = row.get("price") or ""
    price_numeric = _parse_price_numeric(price_raw)
    if price_numeric is None:
        return None

    area_blob = f"{row.get('areaWithType') or ''} {row.get('area') or ''}"
    area_sqft, builtup, carpet = _parse_sqft_from_blob(area_blob, kind)
    if area_sqft < 100:
        area_sqft = max(area_sqft, 100.0)

    rate_col = row.get("rate") or ""
    price_per_sqft = _parse_rate_per_sqft(rate_col)
    if price_per_sqft <= 0 and area_sqft > 0:
        price_per_sqft = round(price_numeric / area_sqft, 2)

    parts = _parse_address_parts(address)
    city_key = _city_key_from_address(address)
    lat, lng = _jitter_latlng(address, city_key)

    desc = (row.get("description") or "").strip() or title
    society = (row.get("society") or "").strip()
    location_label = ", ".join(x for x in (society, address) if x)

    bed = _count_from_cell(row.get("bedRoom") or "", BED_PATTERN)
    bath = _count_from_cell(row.get("bathroom") or "", BATH_PATTERN)
    bal = _balconies_from_cell(row.get("balcony") or "")

    now = datetime.now(timezone.utc).isoformat()
    stable = f"{prop_id}|{kind}|{title.lower()}|{address.lower()}|{price_numeric}"
    source_record_hash = hashlib.sha256(stable.encode("utf-8")).hexdigest()

    listing_type = "sale"
    transaction_type = "resale" if "resale" in desc.lower() else "unknown"

    full: dict[str, Any] = {
        "external_id": prop_id,
        "title": title,
        "description": desc,
        "source": "csv_import",
        "price": str(price_raw).strip() or str(price_numeric),
        "price_numeric": price_numeric,
        "price_per_sqft": price_per_sqft,
        "property_type": "flat" if kind == "flat" else "house",
        "listing_type": listing_type,
        "transaction_type": transaction_type,
        "area_sqft": int(round(area_sqft)) if area_sqft else 0,
        "builtup_area": int(round(builtup)) if builtup else 0,
        "carpet_area": int(round(carpet)) if carpet else 0,
        "bedrooms": bed,
        "bathrooms": bath,
        "balconies": bal,
        "furnishing": _furnishing_from_details(row.get("furnishDetails") or ""),
        "facing": (row.get("facing") or "").strip() or "unknown",
        "age_of_property": (row.get("agePossession") or "").strip() or "unknown",
        "ownership_type": _infer_ownership(desc),
        "location": location_label,
        "address": address,
        "city": parts["city"],
        "district": parts["district"],
        "state": parts["state"] or "Haryana",
        "country": parts["country"],
        "pincode": parts["pincode"],
        "lat": round(lat, 6),
        "lng": round(lng, 6),
        "avg_price_locality": 0,
        "price_trend": "unknown",
        "demand_score": 0,
        "supply_score": 0,
        "source_record_hash": source_record_hash,
        "verified_status": False,
        "embedding_vector_id": None,
        "summary": desc[:280] + ("…" if len(desc) > 280 else ""),
        "tags": [],
        "search_text": " ".join(x for x in (title, address, parts["city"], parts["district"], parts["state"], parts["pincode"]) if x),
        "normalized_location": location_label.lower(),
        "keywords": [w for w in re.split(r"\W+", f"{title} {address} {parts['city']} {parts['district']}".lower()) if len(w) > 2][:40],
        "created_at": now,
        "updated_at": now,
        "scraped_at": now,
        "data_quality_score": 0.75 if parts["city"] else 0.55,
        "csv_kind": kind,
        "link": row.get("link") or "",
        "society": society,
        "floor_info": row.get("floorNum") or row.get("noOfFloor") or "",
        "nearby_locations": row.get("nearbyLocations") or "",
        "features": row.get("features") or "",
        "rating": row.get("rating") or "",
    }

    try:
        if full["nearby_locations"]:
            full["tags"] = ast.literal_eval(full["nearby_locations"])[:30]
    except (ValueError, SyntaxError):
        full["tags"] = []

    return full


def _listing_to_db_record(full: dict[str, Any]) -> dict[str, Any]:
    raw = {k: v for k, v in full.items()}
    return {
        "external_id": full["external_id"],
        "title": full["title"],
        "price": full["price"],
        "price_numeric": full["price_numeric"],
        "location": full["location"],
        "area_sqft": float(full["area_sqft"]),
        "source": full["source"],
        "description": full["description"],
        "owner": None,
        "registration_id": None,
        "verified_status": False,
        "lat": float(full["lat"]),
        "lng": float(full["lng"]),
        "source_record_hash": full["source_record_hash"],
        "raw_payload": raw,
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: (v or "").strip() if v else "" for k, v in row.items()})
    return rows


def run_import(*, limit: int | None, json_out: bool, db_load: bool) -> dict[str, Any]:
    settings = PipelineSettings.load()
    _ = settings  # reserved for future geocoding toggle

    flats_path = DATASET_DIR / "flats.csv"
    houses_path = DATASET_DIR / "houses.csv"
    if not flats_path.is_file():
        raise FileNotFoundError(flats_path)
    if not houses_path.is_file():
        raise FileNotFoundError(houses_path)

    listings: list[dict[str, Any]] = []
    for path, kind in ((flats_path, "flat"), (houses_path, "house")):
        for row in _read_csv(path):
            rec = _row_to_listing(row, kind)
            if rec:
                listings.append(rec)
            if limit is not None and len(listings) >= limit:
                break
        if limit is not None and len(listings) >= limit:
            break

    db_records = [_listing_to_db_record(x) for x in listings]
    deduped = _deduplicate_records(db_records)

    summary = {
        "csv_rows_loaded": len(listings),
        "after_dedupe": len(deduped),
        "inserted_into_db": 0,
        "json_written": str(BACKEND_PROPERTIES) if json_out else None,
    }

    if json_out:
        BACKEND_PROPERTIES.parent.mkdir(parents=True, exist_ok=True)
        json_payloads = [dict(r["raw_payload"]) for r in deduped]
        with BACKEND_PROPERTIES.open("w", encoding="utf-8") as f:
            json.dump(json_payloads, f, ensure_ascii=False, indent=2)

    if db_load and deduped:
        from data_pipeline.loaders.db_loader import upsert_records

        persisted = upsert_records(deduped, batch_size=100)
        summary["inserted_into_db"] = len(persisted)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Import flats/houses CSV into land_listings and/or properties.json")
    parser.add_argument("--limit", type=int, default=None, help="Max listings total (for testing)")
    parser.add_argument("--no-db", action="store_true", help="Skip PostgreSQL upsert")
    parser.add_argument("--no-json", action="store_true", help="Skip writing backend/data/properties.json")
    args = parser.parse_args()
    result = run_import(limit=args.limit, json_out=not args.no_json, db_load=not args.no_db)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

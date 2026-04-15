from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from html import unescape
from typing import Any, Iterable
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from data_pipeline.config import PipelineSettings
from data_pipeline.logging_utils import get_logger
from data_pipeline.processors.geo_encoder import GeoEncoder


logger = get_logger(__name__)

MAX_LISTINGS = 300
MIN_TARGET_LISTINGS = 200
AREA_PATTERN = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(sq\.?\s*ft|sqft|square\s*feet)", re.IGNORECASE)
PRICE_FRAGMENT_PATTERN = re.compile(r"(?:rs\.?|inr)?\s*[\d,.]+\s*(?:cr|crore|lac|lakh)?", re.IGNORECASE)
COORDINATE_PATTERNS = [
    re.compile(r'"(?:lat|latitude)"\s*:\s*"?(-?\d{1,3}\.\d+)"?', re.IGNORECASE),
    re.compile(r'"(?:lng|lon|longitude)"\s*:\s*"?(-?\d{1,3}\.\d+)"?', re.IGNORECASE),
]
MAP_COORDINATE_PATTERNS = [
    re.compile(r"[?&](?:lat|latitude)=(-?\d{1,3}\.\d+)", re.IGNORECASE),
    re.compile(r"[?&](?:lng|lon|longitude)=(-?\d{1,3}\.\d+)", re.IGNORECASE),
    re.compile(r"@(-?\d{1,3}\.\d+),(-?\d{1,3}\.\d+)", re.IGNORECASE),
    re.compile(r"(-?\d{1,3}\.\d+),(-?\d{1,3}\.\d+)", re.IGNORECASE),
]
HEADER_ROTATION = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.4 Safari/605.1.15",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.8",
        "Connection": "keep-alive",
    },
]


@dataclass(frozen=True)
class SourceConfig:
    name: str
    city: str
    url: str
    max_pages: int


@dataclass
class CollectorResult:
    listings: list[dict[str, Any]]
    total_pages_scraped: int
    raw_listings_found: int
    coordinates_extracted: int
    errors: list[str]


SOURCE_CONFIGS = [
    SourceConfig(
        name="magicbricks_pune",
        city="Pune",
        url="https://www.magicbricks.com/residential-plots-land-for-sale-in-pune-pppfs",
        max_pages=6,
    ),
    SourceConfig(
        name="99acres_mumbai",
        city="Mumbai",
        url="https://www.99acres.com/plots-land-in-mumbai-ffid",
        max_pages=6,
    ),
    SourceConfig(
        name="magicbricks_bangalore",
        city="Bangalore",
        url="https://www.magicbricks.com/residential-plots-land-for-sale-in-bangalore-pppfs",
        max_pages=4,
    ),
]


def collect_listings(settings: PipelineSettings, geo_encoder: GeoEncoder) -> CollectorResult:
    session = _build_session()
    listings: list[dict[str, Any]] = []
    total_pages_scraped = 0
    raw_listings_found = 0
    coordinates_extracted = 0
    errors: list[str] = []
    seen_detail_urls: set[str] = set()

    for source in SOURCE_CONFIGS:
        if len(listings) >= MAX_LISTINGS:
            break

        for page_number in range(1, source.max_pages + 1):
            if len(listings) >= MAX_LISTINGS:
                break

            page_url = _page_url(source.url, page_number)
            html = _fetch_html(session, page_url, settings)
            if not html:
                errors.append(f"{source.name}:page_{page_number}:fetch_failed")
                continue

            total_pages_scraped += 1
            candidates = _extract_listing_candidates(html, source)
            raw_listings_found += len(candidates)

            if not candidates and page_number > 1:
                break

            for candidate in candidates:
                if len(listings) >= MAX_LISTINGS:
                    break

                detail_url = candidate.get("detail_url")
                if detail_url and detail_url in seen_detail_urls:
                    continue
                if detail_url:
                    seen_detail_urls.add(detail_url)

                enriched = _enrich_listing_with_coordinates(candidate, session, settings, geo_encoder, source.city)
                if not enriched:
                    continue
                coordinates_extracted += 1
                listings.append(enriched)

        if len(listings) >= MIN_TARGET_LISTINGS:
            break

    logger.info(
        "Collector summary: %s pages scraped, %s raw listings, %s coordinate-resolved listings.",
        total_pages_scraped,
        raw_listings_found,
        coordinates_extracted,
    )
    return CollectorResult(
        listings=listings,
        total_pages_scraped=total_pages_scraped,
        raw_listings_found=raw_listings_found,
        coordinates_extracted=coordinates_extracted,
        errors=errors,
    )


def _build_session() -> requests.Session:
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=2,
        status_forcelist=[403, 408, 429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )

    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # simulate real browser cookies behavior
    session.headers.update({
        "Connection": "keep-alive",
    })

    return session

def _page_url(base_url: str, page_number: int) -> str:
    if page_number <= 1:
        return base_url
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}page={page_number}"


import random

def _fetch_html(session: requests.Session, url: str, settings: PipelineSettings) -> str | None:
    for attempt in range(1, 6):
        headers = dict(random.choice(HEADER_ROTATION))

        # smarter referer (important for 99acres)
        headers["Referer"] = "https://www.google.com/"

        try:
            response = session.get(
                url,
                headers=headers,
                timeout=settings.listing_request_timeout,
            )

            # 🔥 handle 403 specifically
            if response.status_code == 403:
                logger.warning("403 blocked for %s (attempt %s)", url, attempt)

                # exponential backoff + jitter
                time.sleep(random.uniform(3, 6) * attempt)
                continue

            if response.status_code >= 400:
                raise requests.HTTPError(f"status={response.status_code}", response=response)

            # basic bot-detection fallback
            if "captcha" in response.text.lower() or "access denied" in response.text.lower():
                logger.warning("Bot detection triggered for %s", url)
                time.sleep(random.uniform(5, 10))
                continue

            return response.text

        except Exception as exc:
            logger.warning("Fetch failed for %s on attempt %s: %s", url, attempt, exc)
            time.sleep(random.uniform(2, 5) * attempt)

    return None


def _extract_listing_candidates(html: str, source: SourceConfig) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    combined = _merge_candidates(_extract_candidates_from_json(html, source) + _extract_candidates_from_html(soup, source))
    return [candidate for candidate in combined if _looks_like_plot_listing(candidate)]


def _extract_candidates_from_json(html: str, source: SourceConfig) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for payload in _extract_script_json_payloads(html):
        for node in _walk_nodes(payload):
            candidate = _candidate_from_node(node, source)
            if candidate:
                candidates.append(candidate)
    return candidates


def _extract_candidates_from_html(soup: BeautifulSoup, source: SourceConfig) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if "property" not in href.lower() and "detail" not in href.lower():
            continue
        container = anchor
        for _ in range(6):
            if container.parent is None:
                break
            container = container.parent
        text_blob = container.get_text(" ", strip=True)
        title = _first_non_empty(
            [
                anchor.get("title"),
                _extract_title_from_text(text_blob),
                anchor.get_text(" ", strip=True) if _looks_like_plot_title(anchor.get_text(" ", strip=True)) else None,
            ]
        )
        price = _extract_price_fragment(text_blob)
        location = _extract_location_fragment(text_blob, source.city)
        if not (title and price and location):
            continue
        candidates.append(
            {
                "title": title,
                "price": price,
                "location": location,
                "area_sqft": _extract_area_sqft(text_blob),
                "description": _extract_description_fragment(text_blob, title),
                "detail_url": urljoin(source.url, href),
                "source": source.name,
                "city": source.city,
                "raw_payload": {"html_snippet": text_blob[:1200]},
            }
        )
    return candidates


def _extract_script_json_payloads(html: str) -> Iterable[Any]:
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script"):
        script_text = script.string or script.get_text(" ", strip=True)
        if not script_text:
            continue

        script_type = (script.get("type") or "").lower()
        if script_type in {"application/ld+json", "application/json"}:
            payload = _safe_json_loads(script_text)
            if payload is not None:
                yield payload

        for marker in (
            "window.PAGE_MODEL",
            "window.__INITIAL_STATE__",
            "window.__PRELOADED_STATE__",
            "__NEXT_DATA__",
            "pageModel",
        ):
            if marker not in script_text:
                continue
            payload = _extract_json_after_marker(script_text, marker)
            if payload is not None:
                yield payload


def _extract_json_after_marker(script_text: str, marker: str) -> Any | None:
    marker_index = script_text.find(marker)
    if marker_index < 0:
        return None
    start = script_text.find("=", marker_index)
    if start < 0:
        start = marker_index + len(marker)
    snippet = script_text[start + 1 :].lstrip(" ;")
    decoder = json.JSONDecoder()
    for opening in ("{", "["):
        opening_index = snippet.find(opening)
        if opening_index < 0:
            continue
        try:
            payload, _ = decoder.raw_decode(snippet[opening_index:])
            return payload
        except Exception:
            continue
    return None


def _walk_nodes(node: Any) -> Iterable[dict[str, Any]]:
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk_nodes(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_nodes(item)


def _candidate_from_node(node: dict[str, Any], source: SourceConfig) -> dict[str, Any] | None:
    title = _first_non_empty([node.get("title"), node.get("propertyTitle"), node.get("heading"), node.get("name")])
    description = _first_non_empty(
        [node.get("description"), node.get("propertyDescription"), node.get("desc"), node.get("summary")]
    )
    location = _compose_location(
        node.get("location"),
        node.get("locality"),
        node.get("subLocalityName"),
        node.get("cityName"),
        node.get("city"),
        source.city,
    )
    price = _extract_price_value(node)
    if not (title and location and price):
        return None

    candidate = {
        "title": unescape(str(title)).strip(),
        "price": str(price).strip(),
        "location": unescape(str(location)).strip(),
        "area_sqft": _extract_area_value(node),
        "description": unescape(str(description or "")).strip(),
        "detail_url": _extract_detail_url(node, source.url),
        "source": source.name,
        "city": source.city,
        "raw_payload": {"node_keys": list(node.keys())[:50]},
    }
    coordinates = _extract_lat_lng_from_node(node)
    if coordinates:
        candidate.update(coordinates)
        candidate["coordinate_source"] = "listing_json"
    return candidate


def _extract_price_value(node: dict[str, Any]) -> str | None:
    for key in ("price", "priceDisplay", "priceLabel", "amount", "costText", "formattedPrice"):
        value = node.get(key)
        if isinstance(value, str):
            price = _extract_price_fragment(value)
            if price:
                return price
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, dict):
            nested = _first_non_empty(
                [value.get("displayValue"), value.get("label"), value.get("amount"), value.get("price")]
            )
            if nested:
                return str(nested)
    return None


def _extract_area_value(node: dict[str, Any]) -> float | None:
    for key in ("area_sqft", "area", "plotArea", "superArea", "landArea", "size"):
        value = node.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            area = _extract_area_sqft(value)
            if area is not None:
                return area
        if isinstance(value, dict):
            nested = _first_non_empty([value.get("value"), value.get("displayValue"), value.get("area")])
            if nested is not None:
                area = _extract_area_sqft(str(nested))
                if area is not None:
                    return area
    return None


def _extract_detail_url(node: dict[str, Any], base_url: str) -> str | None:
    for key in ("url", "detailUrl", "propertyDetailUrl", "listingUrl", "href", "seoUrl"):
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return urljoin(base_url, value.strip())
    return None


def _extract_lat_lng_from_node(node: dict[str, Any]) -> dict[str, float] | None:
    lat = _coerce_float(_first_non_empty([node.get("lat"), node.get("latitude"), node.get("centerLat")]))
    lng = _coerce_float(
        _first_non_empty([node.get("lng"), node.get("lon"), node.get("longitude"), node.get("centerLng")])
    )
    if lat is None or lng is None:
        return None
    return {"lat": lat, "lng": lng}


def _enrich_listing_with_coordinates(
    candidate: dict[str, Any],
    session: requests.Session,
    settings: PipelineSettings,
    geo_encoder: GeoEncoder,
    city: str,
) -> dict[str, Any] | None:
    listing = dict(candidate)
    coordinates = None

    if geo_encoder.validate_coordinates(listing.get("lat"), listing.get("lng")):
        coordinates = {"lat": float(listing["lat"]), "lng": float(listing["lng"]), "coordinate_source": "listing_json"}

    detail_url = listing.get("detail_url")
    if coordinates is None and detail_url:
        detail_html = _fetch_html(session, detail_url, settings)
        if detail_html:
            direct = _extract_direct_coordinates_from_html(detail_html)
            if direct:
                coordinates = {**direct, "coordinate_source": "detail_json"}
            if coordinates is None:
                map_coordinates = _extract_map_coordinates(detail_html, detail_url)
                if map_coordinates:
                    coordinates = {**map_coordinates, "coordinate_source": "map_link"}
            detail_description = _extract_detail_description(detail_html)
            if detail_description and not listing.get("description"):
                listing["description"] = detail_description

    if coordinates is None:
        resolved = geo_encoder.encode(listing.get("location", ""), city=city)
        if resolved:
            coordinates = {**resolved, "coordinate_source": resolved.get("geo_source", "geocoder")}

    if coordinates is None or not geo_encoder.validate_coordinates(coordinates.get("lat"), coordinates.get("lng")):
        return None

    listing["lat"] = float(coordinates["lat"])
    listing["lng"] = float(coordinates["lng"])
    listing["coordinate_source"] = coordinates.get("coordinate_source")
    listing.setdefault("description", "")
    return listing


def _extract_direct_coordinates_from_html(html: str) -> dict[str, float] | None:
    for payload in _extract_script_json_payloads(html):
        for node in _walk_nodes(payload):
            coordinates = _extract_lat_lng_from_node(node)
            if coordinates:
                return coordinates
    lat_match = COORDINATE_PATTERNS[0].search(html)
    lng_match = COORDINATE_PATTERNS[1].search(html)
    if lat_match and lng_match:
        return {"lat": float(lat_match.group(1)), "lng": float(lng_match.group(1))}
    return None


def _extract_map_coordinates(html: str, detail_url: str) -> dict[str, float] | None:
    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.find_all("a", href=True):
        anchor_text = anchor.get_text(" ", strip=True).lower()
        href = urljoin(detail_url, anchor["href"])
        if "map" not in anchor_text and "map" not in href.lower():
            continue
        coordinates = _parse_coordinates_from_url(href)
        if coordinates:
            return coordinates
    return _parse_coordinates_from_url(detail_url)


def _parse_coordinates_from_url(url: str) -> dict[str, float] | None:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    lat = _coerce_float(_first_non_empty(query.get("lat", []) + query.get("latitude", [])))
    lng = _coerce_float(_first_non_empty(query.get("lng", []) + query.get("lon", []) + query.get("longitude", [])))
    if lat is not None and lng is not None:
        return {"lat": lat, "lng": lng}
    for pattern in MAP_COORDINATE_PATTERNS:
        match = pattern.search(url)
        if match and len(match.groups()) == 2:
            return {"lat": float(match.group(1)), "lng": float(match.group(2))}
    return None


def _extract_detail_description(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    if meta and meta.get("content"):
        return meta["content"].strip()
    return ""


def _merge_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for candidate in candidates:
        title = str(candidate.get("title", "")).strip()
        location = str(candidate.get("location", "")).strip()
        price = str(candidate.get("price", "")).strip()
        if not title or not location or not price:
            continue
        key = (title.lower(), location.lower(), price.lower())
        if key in seen:
            continue
        seen.add(key)
        merged.append(candidate)
    return merged


def _looks_like_plot_listing(candidate: dict[str, Any]) -> bool:
    text = " ".join(
        [str(candidate.get("title", "")), str(candidate.get("description", "")), str(candidate.get("location", ""))]
    ).lower()
    return "plot" in text or "land" in text


def _looks_like_plot_title(value: str) -> bool:
    lowered = value.lower()
    return "plot" in lowered or "land" in lowered


def _extract_title_from_text(text: str) -> str | None:
    match = re.search(r"(Residential\s+Land\s*/\s*Plot\s+in\s+[^|]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _extract_description_fragment(text: str, title: str | None) -> str:
    fragment = text or ""
    if title and title in fragment:
        fragment = fragment.split(title, 1)[-1].strip()
    return fragment[:800]


def _extract_location_fragment(text: str, city: str) -> str | None:
    match = re.search(r"(?:Plot|Land)\s+in\s+([^|]+?)\b(?:Rs|INR|Plot Area|Owner|Updated|$)", text, re.IGNORECASE)
    if match:
        location = match.group(1).strip(" ,")
        if city.lower() not in location.lower():
            location = f"{location}, {city}"
        return location
    return city if city.lower() in text.lower() else None


def _extract_price_fragment(text: str) -> str | None:
    match = PRICE_FRAGMENT_PATTERN.search(text or "")
    return match.group(0).strip() if match else None


def _extract_area_sqft(text: str | None) -> float | None:
    if not text:
        return None
    match = AREA_PATTERN.search(text)
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def _compose_location(*values: Any) -> str | None:
    parts: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value is None:
            continue
        normalized = str(value).strip(" ,")
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        parts.append(normalized)
    return ", ".join(parts) if parts else None


def _first_non_empty(values: Iterable[Any]) -> Any | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if value not in (None, "", [], {}):
            return value
    return None


def _safe_json_loads(value: str) -> Any | None:
    try:
        return json.loads(value)
    except Exception:
        return None


def _coerce_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None

from __future__ import annotations

import time
from typing import Any

from data_pipeline.config import PipelineSettings
from data_pipeline.logging_utils import get_logger

try:
    from geopy.exc import GeocoderServiceError, GeocoderTimedOut
    from geopy.geocoders import Nominatim
except Exception:  # pragma: no cover
    GeocoderServiceError = Exception
    GeocoderTimedOut = Exception
    Nominatim = None  # type: ignore


logger = get_logger(__name__)

REAL_LOCALITY_COORDINATES: dict[str, dict[str, float]] = {
    "baner,pune": {"lat": 18.5590, "lng": 73.7868},
    "wakad,pune": {"lat": 18.5995, "lng": 73.7637},
    "hinjewadi,pune": {"lat": 18.5913, "lng": 73.7389},
    "andheri,mumbai": {"lat": 19.1197, "lng": 72.8468},
    "bandra,mumbai": {"lat": 19.0544, "lng": 72.8406},
    "thane,mumbai": {"lat": 19.2183, "lng": 72.9781},
    "whitefield,bangalore": {"lat": 12.9698, "lng": 77.7499},
    "sarjapur,bangalore": {"lat": 12.9008, "lng": 77.6838},
}
CITY_ALIASES = {
    "pune": "Pune",
    "mumbai": "Mumbai",
    "thane": "Mumbai",
    "bangalore": "Bangalore",
    "bengaluru": "Bangalore",
}


class GeoEncoder:
    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings
        self._geolocator = Nominatim(user_agent="real-estate-intel-pipeline/1.0") if Nominatim else None
        self._last_geocode_at = 0.0

    def encode(self, address: str, city: str | None = None) -> dict[str, Any] | None:
        normalized_address = str(address or "").strip()
        if not normalized_address:
            return None

        locality_match = self._lookup_locality(normalized_address, city)
        if locality_match:
            return {**locality_match, "geo_source": "locality_dictionary"}

        if not self._is_precise_location(normalized_address, city):
            return None

        geopy_coordinates = self._geocode_with_nominatim(normalized_address, city)
        if geopy_coordinates:
            return {**geopy_coordinates, "geo_source": "nominatim"}
        return None

    def validate_coordinates(self, lat: Any, lng: Any) -> bool:
        try:
            lat_value = float(lat)
            lng_value = float(lng)
        except (TypeError, ValueError):
            return False
        return -90 <= lat_value <= 90 and -180 <= lng_value <= 180

    def _lookup_locality(self, address: str, city: str | None = None) -> dict[str, float] | None:
        normalized_city = self._normalize_city(city or address)
        normalized_address = self._normalize_text(address)

        for locality_city, coordinates in REAL_LOCALITY_COORDINATES.items():
            locality, mapped_city = locality_city.split(",", 1)
            if locality not in normalized_address:
                continue
            if normalized_city and mapped_city != normalized_city:
                continue
            if self.validate_coordinates(coordinates["lat"], coordinates["lng"]):
                return dict(coordinates)
        return None

    def _geocode_with_nominatim(self, address: str, city: str | None = None) -> dict[str, float] | None:
        if not self._geolocator:
            logger.warning("geopy/Nominatim is unavailable; skipping geocode fallback for %s", address)
            return None

        query = self._build_query(address, city)
        self._rate_limit()
        try:
            result = self._geolocator.geocode(query, exactly_one=True, country_codes="in", timeout=self.settings.listing_request_timeout)
        except (GeocoderServiceError, GeocoderTimedOut, ValueError) as exc:
            logger.warning("Nominatim geocoding failed for '%s': %s", query, exc)
            return None

        if not result:
            return None

        coordinates = {"lat": float(result.latitude), "lng": float(result.longitude)}
        return coordinates if self.validate_coordinates(coordinates["lat"], coordinates["lng"]) else None

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_geocode_at
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        self._last_geocode_at = time.time()

    def _is_precise_location(self, address: str, city: str | None = None) -> bool:
        normalized = self._normalize_text(address)
        if "," in address:
            return True
        tokens = [token for token in normalized.split() if token]
        if len(tokens) < 2:
            return False
        if city:
            return True
        return any(locality in normalized for locality in ("baner", "wakad", "hinjewadi", "andheri", "bandra", "whitefield", "sarjapur"))

    def _build_query(self, address: str, city: str | None = None) -> str:
        city_name = self._normalize_city(city or address)
        components = [address]
        if city_name and city_name.lower() not in address.lower():
            components.append(city_name)
        components.extend(["India"])
        return ", ".join(component for component in components if component)

    def _normalize_city(self, value: str | None) -> str | None:
        if not value:
            return None
        normalized = self._normalize_text(value)
        for alias, city in CITY_ALIASES.items():
            if alias in normalized:
                return city.lower()
        return None

    def _normalize_text(self, value: str) -> str:
        return " ".join(str(value).strip().lower().replace(",", " ").split())

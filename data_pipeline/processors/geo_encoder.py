from __future__ import annotations

import hashlib
from typing import Any

import requests

from data_pipeline.config import PipelineSettings
from shared.logger import get_logger


logger = get_logger(__name__)


class GeoEncoder:
    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings

    def encode(self, address: str) -> dict[str, float]:
        if self.settings.google_maps_api_key:
            google_coordinates = self._geocode_with_google(address)
            if google_coordinates:
                return google_coordinates
        return self._mock_coordinates(address)

    def _geocode_with_google(self, address: str) -> dict[str, float] | None:
        try:
            response = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": address, "key": self.settings.google_maps_api_key},
                timeout=self.settings.listing_request_timeout,
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            results = payload.get("results", [])
            if not results:
                logger.warning("Google geocoding returned no results for address: %s", address)
                return None
            location = results[0]["geometry"]["location"]
            return {"lat": float(location["lat"]), "lng": float(location["lng"])}
        except Exception as exc:
            logger.warning("Google geocoding failed for '%s': %s", address, exc)
            return None

    def _mock_coordinates(self, address: str) -> dict[str, float]:
        digest = hashlib.sha256(address.encode("utf-8")).hexdigest()
        lat_offset = (int(digest[:8], 16) % 1000) / 10000
        lng_offset = (int(digest[8:16], 16) % 1000) / 10000
        lat = round(self.settings.geocoding_seed_lat + lat_offset, 6)
        lng = round(self.settings.geocoding_seed_lng + lng_offset, 6)
        logger.info("Using deterministic fallback coordinates for address: %s", address)
        return {"lat": lat, "lng": lng}

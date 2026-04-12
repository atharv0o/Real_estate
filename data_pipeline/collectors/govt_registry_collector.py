from __future__ import annotations

from shared.logger import get_logger


logger = get_logger(__name__)


DEFAULT_REGISTRY_DATA = [
    {
        "title": "Highway Frontage Plot",
        "owner": "Aarav Land Holdings LLP",
        "registration_id": "MH-PN-REG-1001",
        "location": "Sector 21, Pune, Maharashtra",
        "verified_status": True,
    },
    {
        "title": "Agricultural Land Parcel",
        "owner": "Shirwal Agro Estates",
        "registration_id": "MH-ST-REG-2044",
        "location": "Shirwal, Satara, Maharashtra",
        "verified_status": True,
    },
    {
        "title": "Commercial Redevelopment Site",
        "owner": "Baner Urban Infra Pvt Ltd",
        "registration_id": "MH-PN-REG-8890",
        "location": "Baner, Pune, Maharashtra",
        "verified_status": False,
    },
]


def collect_registry_records() -> list[dict]:
    logger.info("Loaded %s mock government registry records.", len(DEFAULT_REGISTRY_DATA))
    return [dict(record) for record in DEFAULT_REGISTRY_DATA]

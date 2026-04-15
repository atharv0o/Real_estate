import math

from app.core.logging import get_logger


logger = get_logger(__name__)


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius (km)
    logger.debug("Calculating haversine distance between (%s, %s) and (%s, %s)", lat1, lon1, lat2, lon2)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

from __future__ import annotations

from backend.app.db.postgres import fetch_all_dicts, fetch_one_dict


def get_property_coordinates(property_id: int | None = None, external_id: str | None = None) -> dict | None:
    if property_id is None and external_id is None:
        raise ValueError("property_id or external_id is required")

    if property_id is not None:
        return fetch_one_dict(
            """
            SELECT id, external_id, title, location, latitude AS lat, longitude AS lng
            FROM land_listings
            WHERE id = %s
            """,
            (property_id,),
        )

    return fetch_one_dict(
        """
        SELECT id, external_id, title, location, latitude AS lat, longitude AS lng
        FROM land_listings
        WHERE external_id = %s
        """,
        (external_id,),
    )


def get_location_coordinates(location: str) -> dict | None:
    rows = fetch_all_dicts(
        """
        SELECT latitude AS lat, longitude AS lng
        FROM land_listings
        WHERE location = %s
          AND latitude IS NOT NULL
          AND longitude IS NOT NULL
        """,
        (location,),
    )
    if not rows:
        return None
    lat = sum(row["lat"] for row in rows) / len(rows)
    lng = sum(row["lng"] for row in rows) / len(rows)
    return {"location": location, "lat": round(lat, 6), "lng": round(lng, 6)}

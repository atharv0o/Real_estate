import json
from app.services.geo_utils import haversine

DATA_FILE = "data/properties.json"

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def get_properties(lat, lng, radius):
    data = load_data()

    result = []

    for prop in data:
        distance = haversine(lat, lng, prop["lat"], prop["lng"])

        if distance <= radius:
            prop["distance_km"] = round(distance, 2)
            result.append(prop)

    return {
        "count": len(result),
        "properties": result
    }
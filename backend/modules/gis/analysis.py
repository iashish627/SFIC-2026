"""Basic geodesic proximity diagnostics; not a demand/cannibalization model."""
from math import radians, sin, cos, asin, sqrt
from typing import Iterable

def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    for lat, lon in ((lat1, lon1), (lat2, lon2)):
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("Invalid latitude/longitude")
    dlat, dlon = radians(lat2-lat1), radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 6371.0088 * 2 * asin(sqrt(min(1.0, a)))

def nearby_stations(origin: dict, stations: Iterable[dict], radii_km=(5, 10, 20)) -> dict:
    rows = []
    for station in stations:
        if station.get("station_id") == origin.get("station_id"):
            continue
        try:
            d = distance_km(float(origin["latitude"]), float(origin["longitude"]), float(station["latitude"]), float(station["longitude"]))
        except (KeyError, TypeError, ValueError):
            continue
        rows.append({**station, "distance_km": round(d, 3)})
    rows.sort(key=lambda row: row["distance_km"])
    return {"nearby": rows, "counts_within_km": {str(r): sum(row["distance_km"] <= r for row in rows) for r in radii_km}, "distance_method": "haversine_straight_line", "interpretation": "Proximity diagnostic only; not a validated catchment or proof of cannibalization."}

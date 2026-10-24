"""FastAPI GIS endpoints backed by sourced, provenance-labelled station CSV data."""
import csv
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .analysis import nearby_stations

router = APIRouter(prefix="/api/gis", tags=["GIS"])
DEFAULT_CSV = Path(__file__).resolve().parents[3] / "data" / "processed" / "stations.csv"


def load_stations():
    path = Path(os.getenv("CNG_STATIONS_CSV", str(DEFAULT_CSV)))
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        stations = []
        for row in csv.DictReader(f):
            try:
                lat, lon = float(row["latitude"]), float(row["longitude"])
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    stations.append({
                        **row,
                        "latitude": lat,
                        "longitude": lon,
                        "verified_gujarat_gas_station": str(
                            row.get("verified_gujarat_gas_station", "unknown")
                        ).lower() == "true",
                    })
            except (KeyError, TypeError, ValueError):
                continue
        return stations


def data_note(stations):
    provisional = sum(not row.get("verified_gujarat_gas_station", False) for row in stations)
    if not stations:
        return "No compatible coordinate CSV is loaded. No station records are fabricated."
    return (
        f"{len(stations)} mapped outlet/station record(s); {provisional} are not verified "
        "as currently operating Gujarat Gas CNG stations. Use as provisional candidates only."
    )


@router.get("/stations")
def get_stations():
    stations = load_stations()
    return {"items": stations, "count": len(stations), "data_note": data_note(stations)}


@router.get("/stations/{station_id}/nearby")
def get_nearby(station_id: str, radii_km: str = Query("5,10,20")):
    stations = load_stations()
    origin = next((s for s in stations if str(s.get("station_id")) == station_id), None)
    if origin is None:
        raise HTTPException(status_code=404, detail="Station not found in configured station dataset")
    try:
        radii = tuple(sorted({float(x.strip()) for x in radii_km.split(",") if x.strip()}))
        if not radii or any(x <= 0 or x > 100 for x in radii):
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=422, detail="radii_km must be comma-separated values between 0 and 100")
    return {"station_id": station_id, **nearby_stations(origin, stations, radii)}


@router.get("/candidate-analysis")
def candidate_analysis(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radii_km: str = Query("5,10,20"),
):
    """Rank mapped stations by straight-line distance to a proposed coordinate."""
    stations = load_stations()
    try:
        radii = tuple(sorted({float(x.strip()) for x in radii_km.split(",") if x.strip()}))
        if not radii or any(x <= 0 or x > 100 for x in radii):
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=422, detail="radii_km must be comma-separated values between 0 and 100")
    origin = {"station_id": "__candidate__", "latitude": latitude, "longitude": longitude}
    result = nearby_stations(origin, stations, radii)
    return {
        "candidate": {"latitude": latitude, "longitude": longitude},
        **result,
        "count": len(stations),
        "data_note": data_note(stations),
        "interpretation": "Straight-line proximity only; not road travel time, demand allocation, or validated cannibalization.",
    }

"""FastAPI GIS endpoints backed by sourced, provenance-labelled station CSV data."""
import csv
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .analysis import nearby_stations

router = APIRouter(prefix="/api/gis", tags=["GIS"])
REPO_ROOT = Path(__file__).resolve().parents[3]
# Prefer the 344-record Gujarat Gas directory extract when available locally.
# Otherwise fall back to the explicitly provisional public-outlet snapshot.
GUJARAT_GAS_344_CSV = REPO_ROOT / "member-3-forecasting" / "data" / "gujarat_gas_directory_344_records.csv"
PUBLIC_CSV = REPO_ROOT / "data" / "processed" / "stations.csv"
DEFAULT_CSV = GUJARAT_GAS_344_CSV if GUJARAT_GAS_344_CSV.exists() else PUBLIC_CSV


def load_stations():
    path = Path(os.getenv("CNG_STATIONS_CSV", str(DEFAULT_CSV)))
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        stations = []
        for row in csv.DictReader(f):
            try:
                lat_raw = row.get("latitude") or row.get("lat") or row.get("Latitude")
                lon_raw = row.get("longitude") or row.get("lon") or row.get("lng") or row.get("Longitude")
                lat, lon = float(lat_raw), float(lon_raw)
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    stations.append({
                        **row,
                        "station_id": row.get("station_id") or row.get("outlet_id") or row.get("id") or row.get("station_code") or row.get("name"),
                        "station_name": row.get("station_name") or row.get("name") or row.get("outlet_name") or row.get("station"),
                        "latitude": lat,
                        "longitude": lon,
                        "has_cng": row.get("has_cng", row.get("cng_available", row.get("CNG", "true"))),
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

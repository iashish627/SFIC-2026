"""FastAPI GIS endpoints backed by a sourced station CSV."""
import csv, os
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
                    stations.append({**row, "latitude": lat, "longitude": lon})
            except (KeyError, TypeError, ValueError):
                continue
        return stations

@router.get("/stations")
def get_stations():
    stations = load_stations()
    return {"items": stations, "count": len(stations), "data_note": "Empty results mean no compatible station CSV was found; no station data is fabricated."}

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

"""Gujarat-only GIS API with explicitly labelled synthetic capacity and sales."""
import csv
import os
from datetime import date
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from .analysis import nearby_stations

router = APIRouter(prefix="/api/gis", tags=["GIS"])
ROOT = Path(__file__).resolve().parents[3]
STATION_CSV = ROOT / "data" / "gujarat_gas_directory_344_geocoded.csv"
CAPACITY_CSV = ROOT / "data" / "synthetic_demo" / "station_capacity_344_synthetic.csv"
SALES_CSV = ROOT / "data" / "synthetic_demo" / "station_daily_sales_344_synthetic.csv"
# Keep compatibility with older placement, but never fall back to the 6,325-record public outlet dump.
LEGACY_STATION_CSVS = [
    ROOT / "member-3-forecasting" / "data" / "gujarat_gas_directory_344_geocoded.csv",
    ROOT / "member-3-forecasting" / "data" / "gujarat_gas_directory_344_records.csv",
]

def _read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def _number(value):
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None

def _selected_station_path():
    override = os.getenv("CNG_STATIONS_CSV")
    if override:
        return Path(override)
    if STATION_CSV.exists():
        return STATION_CSV
    for path in LEGACY_STATION_CSVS:
        if path.exists():
            return path
    return None

def load_stations():
    path = _selected_station_path()
    if path is None or not path.exists():
        return []
    capacities = {r.get("station_id"): r for r in _read_csv(CAPACITY_CSV)}
    sales_rows = _read_csv(SALES_CSV)
    sales_by_station = {}
    for row in sales_rows:
        sid = row.get("station_id")
        amount = _number(row.get("sales_kg"))
        if not sid or amount is None:
            continue
        bucket = sales_by_station.setdefault(sid, [])
        bucket.append((row.get("date", ""), amount, row.get("data_quality_label", "UNKNOWN")))
    stations = []
    for row in _read_csv(path):
        sid = row.get("station_id") or row.get("id")
        caprow = capacities.get(sid, {})
        sales = sorted(sales_by_station.get(sid, []), key=lambda x: x[0])
        last_30 = [x[1] for x in sales[-30:]]
        cap = _number(caprow.get("effective_capacity_kg_day"))
        avg_sales = sum(last_30) / len(last_30) if last_30 else None
        peak_sales = max(last_30) if last_30 else None
        lat = _number(row.get("latitude") or row.get("lat"))
        lon = _number(row.get("longitude") or row.get("lon") or row.get("lng"))
        item = {
            **row,
            "station_id": sid,
            "station_name": row.get("station_name") or row.get("name") or "Unnamed station",
            "latitude": lat,
            "longitude": lon,
            "has_cng": str(row.get("has_cng", "true")).lower() in ("true", "1", "yes", "y"),
            "verified_gujarat_gas_station": str(row.get("verified_gujarat_gas_station", "false")).lower() == "true",
            "capacity_kg_day": cap,
            "effective_capacity_kg_day": cap,
            "dispenser_count": _number(caprow.get("dispenser_count")),
            "avg_sales_kg_day_30d": round(avg_sales, 1) if avg_sales is not None else None,
            "peak_demand_kg_day": round(peak_sales, 1) if peak_sales is not None else None,
            "utilization": round(avg_sales / cap, 4) if avg_sales is not None and cap else None,
            "sales_data_status": "SYNTHETIC DEMO ESTIMATE" if sales else "MISSING",
            "capacity_data_status": "SYNTHETIC DEMO ESTIMATE" if cap else "MISSING",
            "data_quality_label": "SYNTHETIC_NOT_ACTUAL_SALES_OR_CAPACITY",
        }
        stations.append(item)
    return stations

def mapped_stations():
    return [s for s in load_stations() if s.get("latitude") is not None and s.get("longitude") is not None]

def data_note(stations):
    if not stations:
        return ("Gujarat 344-station dataset not found. Put the three bundle CSVs at the documented "
                "data/ paths; the API deliberately does not fall back to the broader public-outlet dump.")
    return (f"{len(stations)} records from the Gujarat 344-directory target list. "
            "Sales and capacity are synthetic estimates; coordinates may be approximate; current operation is unverified.")

@router.get("/stations")
def get_stations():
    stations = load_stations()
    return {"items": stations, "count": len(stations), "data_note": data_note(stations),
            "dataset_scope": "Gujarat 344-directory target list",
            "synthetic_data": True}

@router.get("/stations/{station_id}/nearby")
def get_nearby(station_id: str, radii_km: str = Query("5,10,20")):
    stations = mapped_stations()
    origin = next((s for s in stations if str(s.get("station_id")) == station_id), None)
    if origin is None:
        raise HTTPException(status_code=404, detail="Station not found in mapped Gujarat dataset")
    try:
        radii = tuple(sorted({float(x.strip()) for x in radii_km.split(",") if x.strip()}))
        if not radii or any(x <= 0 or x > 100 for x in radii): raise ValueError
    except ValueError:
        raise HTTPException(status_code=422, detail="radii_km must be comma-separated values between 0 and 100")
    return {"station_id": station_id, **nearby_stations(origin, stations, radii)}

@router.get("/candidate-analysis")
def candidate_analysis(latitude: float = Query(..., ge=-90, le=90),
                       longitude: float = Query(..., ge=-180, le=180),
                       radii_km: str = Query("5,10,20")):
    stations = mapped_stations()
    try:
        radii = tuple(sorted({float(x.strip()) for x in radii_km.split(",") if x.strip()}))
        if not radii or any(x <= 0 or x > 100 for x in radii): raise ValueError
    except ValueError:
        raise HTTPException(status_code=422, detail="radii_km must be comma-separated values between 0 and 100")
    origin = {"station_id": "__candidate__", "latitude": latitude, "longitude": longitude}
    return {"candidate": {"latitude": latitude, "longitude": longitude},
            **nearby_stations(origin, stations, radii), "count": len(stations),
            "data_note": data_note(stations),
            "interpretation": "Straight-line proximity only; not road travel time or validated commercial viability."}

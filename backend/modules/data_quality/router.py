"""Data freshness and completeness diagnostics for demo datasets."""
import csv
import os
from datetime import date
from pathlib import Path
from fastapi import APIRouter
from backend.modules.gis.router import load_stations as load_gis_stations

router = APIRouter(prefix="/api/health", tags=["Data Quality"])
ROOT = Path(__file__).resolve().parents[3]
DEMO = ROOT / "data" / "synthetic_demo"


def _read(name):
    path = DEMO / name
    if not path.exists():
        return {"exists": False, "rows": []}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return {"exists": True, "rows": list(csv.DictReader(handle))}


@router.get("/data")
def data_health():
    station_file = _read("stations.csv")
    sales_file = _read("daily_sales.csv")
    capacity_file = _read("station_capacity.csv")
    stations = station_file["rows"]
    sales = sales_file["rows"]
    capacities = capacity_file["rows"]
    station_ids = {row.get("station_id") for row in stations if row.get("station_id")}
    capacity_ids = {row.get("station_id") for row in capacities if row.get("station_id")}
    valid_sales = []
    missing_sales = 0
    invalid_sales = 0
    for row in sales:
        raw = row.get("sales_kg")
        if raw in (None, ""):
            missing_sales += 1
            continue
        try:
            amount = float(raw)
            date.fromisoformat(row["date"])
            if amount < 0:
                invalid_sales += 1
            elif row.get("quality_flag") == "ok":
                valid_sales.append(row)
        except (ValueError, TypeError, KeyError):
            invalid_sales += 1
    dates = sorted({row.get("date") for row in valid_sales if row.get("date")})
    last_date = date.fromisoformat(dates[-1]) if dates else None
    stale_days = (date.today() - last_date).days if last_date else None
    gis = load_gis_stations()
    source_path = os.getenv("CNG_STATIONS_CSV") or "default GIS source selection"
    return {
        "status": "healthy" if station_file["exists"] and sales_file["exists"] and capacity_file["exists"] else "incomplete",
        "provenance": "synthetic_demo",
        "layers": {
            "stations": {"available": station_file["exists"], "rows": len(stations), "unique_station_ids": len(station_ids)},
            "daily_sales": {"available": sales_file["exists"], "rows": len(sales), "valid_records": len(valid_sales), "missing_sales_records": missing_sales, "invalid_records": invalid_sales, "date_min": dates[0] if dates else None, "date_max": dates[-1] if dates else None, "stale_days_since_last_observation": stale_days},
            "capacity": {"available": capacity_file["exists"], "rows": len(capacities), "stations_without_capacity": len(station_ids - capacity_ids)},
            "gis": {"coordinate_valid_records": len(gis), "source_config": source_path, "verified_operator_records": sum(row.get("verified_gujarat_gas_station") is True for row in gis)},
        },
        "warnings": [
            "Demo sales and capacity are synthetic; they are not Gujarat Gas operational data.",
            "Missing sales records are not converted to zero.",
            "GIS records may be provisional and require source/coordinate review.",
            "File uploads are not implemented as a persistent ingestion workflow.",
        ],
    }

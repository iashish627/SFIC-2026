"""Accurate dashboard summary derived from repository demo data and GIS records."""
import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from fastapi import APIRouter
from backend.modules.gis.router import load_stations as load_gis_stations

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
ROOT = Path(__file__).resolve().parents[3]
DEMO = ROOT / "data" / "synthetic_demo"

def _read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))

def _valid_coordinate(value, low, high):
    try:
        number = float(value)
        return low <= number <= high
    except (TypeError, ValueError):
        return False

@router.get("/summary")
def dashboard_summary():
    """Return counts and chart series from available files; never invent missing data."""
    stations = _read_csv(DEMO / "stations.csv")
    capacities = _read_csv(DEMO / "station_capacity.csv")
    sales = _read_csv(DEMO / "daily_sales.csv")
    gis_stations = load_gis_stations()
    station_ids = {r.get("station_id") for r in stations if r.get("station_id")}
    capacity_ids = {r.get("station_id") for r in capacities if r.get("station_id")}
    located_ids = {r.get("station_id") for r in stations if r.get("station_id") and _valid_coordinate(r.get("latitude"), -90, 90) and _valid_coordinate(r.get("longitude"), -180, 180)}
    valid_sales = []
    for row in sales:
        if row.get("quality_flag") != "ok" or row.get("sales_kg") in (None, ""):
            continue
        try:
            amount = float(row["sales_kg"])
            parsed_date = date.fromisoformat(row["date"])
            if amount >= 0:
                valid_sales.append((parsed_date, row.get("station_id", ""), amount))
        except (TypeError, ValueError, KeyError):
            continue
    daily = defaultdict(float)
    district_counts = Counter()
    for row in stations:
        district = (row.get("district") or "").strip()
        if district:
            district_counts[district] += 1
    for day, _station_id, amount in valid_sales:
        daily[day.isoformat()] += amount
    daily_rows = [{"date": day, "sales_kg": round(value, 2)} for day, value in sorted(daily.items())]
    return {
        "provenance": "synthetic_demo",
        "data_note": "Dashboard metrics below are computed from the repository's synthetic demo CSVs; they are not Gujarat Gas operational data.",
        "stations": {"demo_total": len(station_ids), "with_capacity": len(station_ids & capacity_ids), "with_valid_coordinates": len(located_ids), "gis_records_loaded": len(gis_stations), "district_count": len(district_counts)},
        "sales": {"valid_record_count": len(valid_sales), "daily_totals": daily_rows[-42:], "date_min": min((d.isoformat() for d, _, _ in valid_sales), default=None), "date_max": max((d.isoformat() for d, _, _ in valid_sales), default=None)},
        "district_counts": dict(sorted(district_counts.items())),
    }

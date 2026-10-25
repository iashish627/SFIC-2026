"""Dashboard summaries for the Gujarat 344-directory prototype and synthetic demonstration data."""
import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from fastapi import APIRouter
from backend.modules.gis.router import load_stations

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
ROOT = Path(__file__).resolve().parents[3]
def read_csv(path):
    if not path.exists(): return []
    with path.open(newline="", encoding="utf-8-sig") as f: return list(csv.DictReader(f))

@router.get("/summary")
def dashboard_summary():
    stations = load_stations()
    sales = []
    for s in stations:
        # Station rows carry station-level 30-day summaries; detailed series is read separately.
        pass
    detail_path = ROOT / "data" / "synthetic_demo" / "station_daily_sales_344_synthetic.csv"
    rows = read_csv(detail_path)
    daily = defaultdict(float)
    valid = []
    for r in rows:
        try:
            d = date.fromisoformat(r["date"]); amount = float(r["sales_kg"])
            if amount >= 0:
                valid.append((d, r.get("station_id", ""), amount))
                daily[d.isoformat()] += amount
        except (ValueError, TypeError, KeyError): pass
    district_counts = Counter((s.get("district") or "").strip() for s in stations if (s.get("district") or "").strip())
    capacities = sum(s.get("capacity_kg_day") is not None for s in stations)
    located = sum(s.get("latitude") is not None and s.get("longitude") is not None for s in stations)
    utilisation_buckets = {"below_85": 0, "from_85_to_100": 0, "over_100": 0, "missing": 0}
    for station in stations:
        capacity = station.get("capacity_kg_day")
        sales_avg = station.get("avg_sales_kg_day_30d")
        try:
            if capacity is None or sales_avg is None or float(capacity) <= 0:
                utilisation_buckets["missing"] += 1
            else:
                ratio = float(sales_avg) / float(capacity)
                if ratio > 1:
                    utilisation_buckets["over_100"] += 1
                elif ratio >= 0.85:
                    utilisation_buckets["from_85_to_100"] += 1
                else:
                    utilisation_buckets["below_85"] += 1
        except (TypeError, ValueError, ZeroDivisionError):
            utilisation_buckets["missing"] += 1
    daily_rows = [{"date": d, "sales_kg": round(v, 1)} for d, v in sorted(daily.items())]
    return {
      "provenance": "synthetic_estimate",
      "data_note": "Gujarat 344-directory target list. Sales and capacity are synthetic estimates, not actual Gujarat Gas operational data.",
      "stations": {"demo_total": len(stations), "with_capacity": capacities, "with_valid_coordinates": located, "gis_records_loaded": len(stations), "district_count": len(district_counts), "utilisation_buckets": utilisation_buckets},
      "sales": {"valid_record_count": len(valid), "daily_totals": daily_rows[-42:], "daily_total_unit": "kg/day across all stations", "date_min": min((d.isoformat() for d,_,_ in valid), default=None), "date_max": max((d.isoformat() for d,_,_ in valid), default=None)},
      "district_counts": dict(sorted(district_counts.items()))
    }

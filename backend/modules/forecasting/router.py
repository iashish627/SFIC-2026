"""Transparent station-level demand forecast baselines from synthetic demo history."""
import csv
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/forecast", tags=["Demand Forecast"])
ROOT = Path(__file__).resolve().parents[3]
SALES_PATH = ROOT / "data" / "synthetic_demo" / "daily_sales.csv"
STATIONS_PATH = ROOT / "data" / "synthetic_demo" / "stations.csv"

def _load_history():
    grouped = defaultdict(dict)
    if not SALES_PATH.exists():
        return grouped
    with SALES_PATH.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row.get("quality_flag") != "ok" or not row.get("sales_kg"):
                continue
            try:
                day = date.fromisoformat(row["date"])
                amount = float(row["sales_kg"])
                if amount >= 0:
                    grouped[row["station_id"]][day] = amount
            except (ValueError, TypeError, KeyError):
                continue
    return grouped

def _load_station_names():
    names = {}
    if STATIONS_PATH.exists():
        with STATIONS_PATH.open(newline="", encoding="utf-8-sig") as handle:
            names = {r.get("station_id"): r.get("station_name", r.get("station_id")) for r in csv.DictReader(handle) if r.get("station_id")}
    return names

def _forecast(history, days):
    observed_days = sorted(history)
    values = [history[d] for d in observed_days]
    if not values:
        return {"method": "unavailable", "rows": [], "warning": "No valid historical sales are available for this station."}
    # Weekly seasonal-naive when the complete preceding week is available; otherwise a recent mean.
    rows = []
    last_day = observed_days[-1]
    for step in range(1, days + 1):
        target = last_day + timedelta(days=step)
        if len(values) >= 7:
            predicted = values[(len(values) - 7 + ((step - 1) % 7)) % len(values)]
            method = "seasonal_naive_7d"
        else:
            predicted = sum(values[-min(7, len(values)):]) / min(7, len(values))
            method = "moving_average_fallback"
        rows.append({"date": target.isoformat(), "predicted_demand_kg": round(max(0.0, predicted), 2)})
    return {"method": method, "rows": rows, "warning": "Baseline only. Data is synthetic and forecast accuracy has not been validated against a holdout period."}

@router.get("/stations")
def list_stations():
    history = _load_history()
    names = _load_station_names()
    stations = []
    for station_id in sorted(set(history) | set(names)):
        days = sorted(history.get(station_id, {}))
        stations.append({"station_id": station_id, "station_name": names.get(station_id, station_id), "valid_history_days": len(days), "history_start": days[0].isoformat() if days else None, "history_end": days[-1].isoformat() if days else None})
    return {"provenance": "synthetic_demo", "count": len(stations), "stations": stations, "warning": "Synthetic demo station records only; not operational Gujarat Gas data."}

@router.get("/weekly/{station_id}")
def weekly_forecast(station_id: str, weeks: int = Query(4, ge=1, le=5), model: str = Query("seasonal_naive", pattern="^(seasonal_naive|moving_average)$")):
    """Aggregate daily baseline predictions into weekly demand totals."""
    history = _load_history().get(station_id, {})
    if not history:
        raise HTTPException(status_code=404, detail="No valid sales history for this station in the configured demo dataset.")
    observed_days = sorted(history)
    values = [history[d] for d in observed_days]
    last_day = observed_days[-1]
    daily = []
    for step in range(1, weeks * 7 + 1):
        target = last_day + timedelta(days=step)
        if model == "seasonal_naive" and len(values) >= 7:
            # Use the value seven calendar days before the target when observed; otherwise use a recent mean.
            predicted = history.get(target - timedelta(days=7))
            if predicted is None:
                predicted = sum(values[-min(7, len(values)):]) / min(7, len(values))
        else:
            predicted = sum(values[-min(7, len(values)):]) / min(7, len(values))
        daily.append({"date": target.isoformat(), "predicted_demand_kg": round(max(0.0, predicted), 2)})
    weekly = []
    for index in range(weeks):
        chunk = daily[index * 7:(index + 1) * 7]
        weekly.append({"week": index + 1, "start_date": chunk[0]["date"], "end_date": chunk[-1]["date"], "predicted_demand_kg": round(sum(row["predicted_demand_kg"] for row in chunk), 2)})
    return {"station_id": station_id, "weeks": weeks, "model": model, "provenance": "synthetic_demo", "weekly_forecast": weekly, "warning": "Weekly totals are aggregates of a simple baseline over synthetic demo data; not operational forecasts."}

@router.get("/evaluate/{station_id}")
def evaluate_forecast(station_id: str, test_days: int = Query(14, ge=7, le=30), model: str = Query("seasonal_naive", pattern="^(seasonal_naive|moving_average)$")):
    """Time-ordered holdout evaluation on synthetic history; never reports training fit as accuracy."""
    history = _load_history().get(station_id, {})
    if not history:
        raise HTTPException(status_code=404, detail="No valid sales history for this station in the configured demo dataset.")
    dates = sorted(history)
    if len(dates) <= test_days:
        raise HTTPException(status_code=422, detail="Not enough history for the requested time-based holdout.")
    split = len(dates) - test_days
    train_dates, test_dates = dates[:split], dates[split:]
    train = {day: history[day] for day in train_dates}
    train_values = [train[day] for day in train_dates]
    actual, predicted = [], []
    for target in test_dates:
        if model == "seasonal_naive" and target - timedelta(days=7) in train:
            estimate = train[target - timedelta(days=7)]
        else:
            estimate = sum(train_values[-min(7, len(train_values)):]) / min(7, len(train_values))
        actual.append(history[target])
        predicted.append(max(0.0, estimate))
    mae = sum(abs(a-p) for a,p in zip(actual,predicted)) / len(actual)
    actual_total = sum(actual)
    wape = sum(abs(a-p) for a,p in zip(actual,predicted)) / actual_total * 100 if actual_total else None
    return {"station_id": station_id, "model": model, "split_type": "chronological_holdout", "train_days": len(train_dates), "test_days": len(test_dates), "train_end": train_dates[-1].isoformat(), "test_start": test_dates[0].isoformat(), "test_end": test_dates[-1].isoformat(), "mae_kg_day": round(mae, 2), "wape_pct": round(wape, 2) if wape is not None else None, "provenance": "synthetic_demo", "warning": "Metrics evaluate only this synthetic demo series. They do not establish real-world Gujarat Gas forecast accuracy."}

@router.get("/station/{station_id}")
def forecast_station(station_id: str, days: int = Query(14, ge=1, le=30), model: str = Query("seasonal_naive", pattern="^(seasonal_naive|moving_average)$")):
    history = _load_history().get(station_id, {})
    if not history:
        raise HTTPException(status_code=404, detail="No valid sales history for this station in the configured demo dataset.")
    observed_days = sorted(history)
    values = [history[d] for d in observed_days]
    rows = []
    last_day = observed_days[-1]
    for step in range(1, days + 1):
        target = last_day + timedelta(days=step)
        if model == "seasonal_naive" and len(values) >= 7:
            predicted = values[(len(values) - 7 + ((step - 1) % 7)) % len(values)]
            method = "seasonal_naive_7d"
        else:
            window = values[-min(7, len(values)):]
            predicted = sum(window) / len(window)
            method = "moving_average_7d" if model == "moving_average" else "moving_average_fallback"
        rows.append({"date": target.isoformat(), "predicted_demand_kg": round(max(0.0, predicted), 2)})
    return {"station_id": station_id, "days": days, "model": model, "method": method, "provenance": "synthetic_demo", "history": {"valid_days": len(values), "start": observed_days[0].isoformat(), "end": observed_days[-1].isoformat()}, "forecast": rows, "warning": "Baseline demonstration only. Synthetic data; no holdout validation or operational accuracy claim."}

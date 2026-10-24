"""CNG station demand forecast API; estimated values are not observed sales."""
from __future__ import annotations
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Literal
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

BASE_DIR = Path(__file__).resolve().parent.parent
STATIONS_CSV = Path(os.getenv("CNG_STATIONS_CSV", str(BASE_DIR / "data" / "stations.csv"))).expanduser()
SALES_CSV = Path(os.getenv("CNG_SALES_CSV", str(BASE_DIR / "data" / "daily_sales.csv"))).expanduser()
CORS_ORIGINS = [x.strip() for x in os.getenv("CNG_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if x.strip()]
app = FastAPI(title="CNG Demand Forecasting API", version="1.2.0")
# Make the repository root importable when launched from member-3-forecasting/.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from backend.modules.gis.router import router as gis_router
app.include_router(gis_router)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])

class ForecastRequest(BaseModel):
    station_ids: list[str] = Field(min_length=1)
    start_date: date
    days: int = Field(default=30, ge=1, le=30)
    mode: Literal["historical", "estimated"] = "estimated"
    base_demand_kg: float | None = Field(default=None, gt=0)
    @field_validator("station_ids")
    @classmethod
    def strip_ids(cls, value):
        cleaned = [x.strip() for x in value if x.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty station ID is required")
        return cleaned

class ScenarioRequest(BaseModel):
    station_ids: list[str] = Field(min_length=1)
    start_date: date
    end_date: date
    uplift_percentage: float = Field(ge=0, le=1000)
    base_demand_kg: float = Field(gt=0)

def read_stations() -> pd.DataFrame:
    if not STATIONS_CSV.is_file():
        raise HTTPException(status_code=503, detail="Station CSV not found. Configure CNG_STATIONS_CSV. Required columns: station_id, station_name.")
    df = pd.read_csv(STATIONS_CSV)
    if not {"station_id", "station_name"}.issubset(df.columns):
        raise HTTPException(status_code=500, detail="Station CSV must contain station_id and station_name columns.")
    df["station_id"] = df["station_id"].astype(str).str.strip()
    return df

def read_sales():
    if not SALES_CSV.is_file():
        return None
    df = pd.read_csv(SALES_CSV)
    if not {"station_id", "date", "sales_kg"}.issubset(df.columns):
        raise HTTPException(status_code=500, detail="Sales CSV must contain station_id,date,sales_kg columns.")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["sales_kg"] = pd.to_numeric(df["sales_kg"], errors="coerce")
    df = df.dropna(subset=["station_id", "date", "sales_kg"])
    if (df["sales_kg"] < 0).any():
        raise HTTPException(status_code=500, detail="Sales CSV contains negative sales_kg.")
    return df

@app.get("/")
def root():
    return {"name": "CNG Demand Forecasting API", "docs": "/docs", "note": "Historical mode requires observed sales; estimated mode is assumption-based."}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/v1/forecast/stations")
def stations():
    df = read_stations()
    return {"success": True, "total_count": int(len(df)), "stations": df.where(pd.notna(df), None).to_dict("records")}

@app.get("/api/v1/forecast/data-quality")
def data_quality():
    station_df = read_stations()
    sales_df = read_sales()
    return {"success": True, "stations_rows": int(len(station_df)), "stations_missing_ids": int(station_df["station_id"].eq("").sum()), "historical_sales_available": sales_df is not None and not sales_df.empty, "historical_sales_rows": 0 if sales_df is None else int(len(sales_df)), "note": "Station directory metadata is not historical demand data."}

def forecast_historical(sid: str, start: date, days: int, sales: pd.DataFrame) -> list[dict]:
    hist = sales[sales["station_id"].astype(str) == sid].groupby("date")["sales_kg"].mean().sort_index()
    if hist.empty:
        raise HTTPException(status_code=422, detail=f"No historical sales for station {sid}.")
    idx = pd.date_range(hist.index.min().normalize(), hist.index.max().normalize(), freq="D")
    hist = hist.reindex(idx)
    if hist.notna().sum() < 7:
        raise HTTPException(status_code=422, detail=f"Station {sid} needs at least 7 observed daily sales values.")
    hist = hist.interpolate(limit=2, limit_direction="both")
    result = []
    for i in range(days):
        d = pd.Timestamp(start) + pd.Timedelta(days=i)
        prior = d - pd.Timedelta(days=7)
        if prior in hist.index and pd.notna(hist.loc[prior]):
            pred, model = float(hist.loc[prior]), "seasonal_naive_7d"
        else:
            pred, model = float(hist.tail(7).mean()), "last_7_day_mean_fallback"
        result.append({"station_id": sid, "date": d.date().isoformat(), "predicted_demand_kg": round(max(0.0, pred), 2), "model": model, "data_type": "historical_forecast", "unit": "kg"})
    return result

@app.post("/api/v1/forecast/generate")
def generate_forecast(req: ForecastRequest):
    station_df = read_stations()
    unknown = sorted(set(req.station_ids) - set(station_df["station_id"].astype(str)))
    if unknown:
        raise HTTPException(status_code=404, detail={"message": "Unknown station IDs", "station_ids": unknown})
    sales = read_sales()
    if req.mode == "historical":
        if sales is None or sales.empty:
            raise HTTPException(status_code=422, detail="Historical forecast unavailable: configure CNG_SALES_CSV with genuine daily station sales.")
        rows = [row for sid in req.station_ids for row in forecast_historical(sid, req.start_date, req.days, sales)]
        return {"success": True, "mode": "historical", "forecast_data": rows, "metadata": {"source": "configured historical sales CSV", "horizon_days": req.days}}
    if req.base_demand_kg is None:
        raise HTTPException(status_code=422, detail="Estimated mode requires explicit base_demand_kg. This is an assumption, not observed sales.")
    rows = []
    multipliers = [0.9, 1.0, 1.0, 1.0, 1.1, 1.2, 0.8]
    for sid in req.station_ids:
        for i in range(req.days):
            d = req.start_date + timedelta(days=i)
            rows.append({"station_id": sid, "date": d.isoformat(), "predicted_demand_kg": round(req.base_demand_kg * multipliers[d.weekday()], 2), "model": "assumption_weekday_adjustment", "data_type": "estimated_demand", "unit": "kg"})
    return {"success": True, "mode": "estimated", "forecast_data": rows, "metadata": {"assumptions": {"base_demand_kg": req.base_demand_kg, "weekday_adjustment": True}, "warning": "Not calibrated to actual station sales; not validated demand."}}

@app.post("/api/v1/forecast/scenario/demand-shock")
@app.post("/api/v1/forecast/scenario/festival-surge")
def demand_shock(req: ScenarioRequest):
    if req.end_date < req.start_date:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date.")
    station_df = read_stations()
    unknown = sorted(set(req.station_ids) - set(station_df["station_id"].astype(str)))
    if unknown:
        raise HTTPException(status_code=404, detail={"message": "Unknown station IDs", "station_ids": unknown})
    rows, d = [], req.start_date
    while d <= req.end_date:
        for sid in req.station_ids:
            rows.append({"station_id": sid, "date": d.isoformat(), "baseline_demand_kg": req.base_demand_kg, "scenario_demand_kg": round(req.base_demand_kg * (1 + req.uplift_percentage / 100), 2), "uplift_percentage": req.uplift_percentage, "data_type": "hypothetical_scenario", "unit": "kg"})
        d += timedelta(days=1)
    return {"success": True, "scenario_data": rows, "metadata": {"assumptions": {"base_demand_kg": req.base_demand_kg, "uplift_percentage": req.uplift_percentage}, "warning": "Hypothetical scenario based on user-supplied baseline."}}

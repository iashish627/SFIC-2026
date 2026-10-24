"""FastAPI routes for demo inputs and the demand shock / A-B-C simulator."""
import csv
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.modules.simulation.engine import Station, run_simulation

router=APIRouter(prefix="/api/simulator",tags=["Demand Shock & Expansion Simulator"])
ROOT=Path(__file__).resolve().parents[3]
DEMO=ROOT/"data"/"synthetic_demo"

class StationInput(BaseModel):
    station_id: str
    baseline_kg_day: float=Field(ge=0)
    capacity_kg_day: float=Field(ge=0)

class SimulationRequest(BaseModel):
    stations: Optional[list[StationInput]]=None
    horizon_days: int=Field(default=30,ge=1,le=365)
    demand_uplift_pct: float=Field(default=0,ge=0,le=300)
    shock_days: list[int]=Field(default_factory=list,description="1-based day indexes in horizon")
    expand_station_id: Optional[str]=None
    added_capacity_kg_day: float=Field(default=0,ge=0)
    expansion_cost: float=Field(default=0,ge=0)
    new_site_potential_kg_day: float=Field(default=0,ge=0)
    new_site_capacity_kg_day: float=Field(default=0,ge=0)
    diversion_pct: float=Field(default=0,ge=0,le=100)
    new_site_cost: float=Field(default=0,ge=0)

def load_demo_stations():
    sales_path=DEMO/"daily_sales.csv"
    cap_path=DEMO/"station_capacity.csv"
    if not sales_path.exists() or not cap_path.exists():
        raise FileNotFoundError("Synthetic demo CSV files are missing")
    sales={}
    with sales_path.open(newline="",encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("sales_kg") and row.get("quality_flag")=="ok":
                try: sales.setdefault(row["station_id"],[]).append((row["date"],float(row["sales_kg"])))
                except (TypeError,ValueError): pass
    result=[]
    with cap_path.open(newline="",encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            values=sorted(sales.get(row["station_id"],[]))[-28:]
            if values:
                result.append(Station(row["station_id"],sum(v for _,v in values)/len(values),
                                      float(row["effective_capacity_kg_day"])))
    return result

@router.get("/demo-inputs")
def demo_inputs():
    """Recent valid synthetic-record averages; explicitly not an ML forecast."""
    try: stations=load_demo_stations()
    except (OSError,ValueError) as exc: raise HTTPException(500,str(exc)) from exc
    return {"provenance":"synthetic","baseline_method":"mean of up to last 28 valid synthetic daily sales records",
            "stations":[s.__dict__ for s in stations],
            "warning":"Illustrative synthetic data only; not an operational forecast."}

@router.post("/run")
def run(request: SimulationRequest):
    try:
        stations=([Station(s.station_id,s.baseline_kg_day,s.capacity_kg_day) for s in request.stations]
                  if request.stations is not None else load_demo_stations())
        return run_simulation(stations,horizon_days=request.horizon_days,
            demand_uplift_pct=request.demand_uplift_pct,shock_days=request.shock_days,
            expand_station_id=request.expand_station_id,added_capacity_kg_day=request.added_capacity_kg_day,
            expansion_cost=request.expansion_cost,new_site_potential_kg_day=request.new_site_potential_kg_day,
            new_site_capacity_kg_day=request.new_site_capacity_kg_day,diversion_pct=request.diversion_pct,
            new_site_cost=request.new_site_cost)
    except (ValueError,OSError) as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc

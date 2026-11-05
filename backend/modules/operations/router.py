"""Scenario-based hourly pressure model."""
from fastapi import APIRouter, HTTPException, Query
from backend.modules.gis.router import load_stations

router = APIRouter(prefix="/api/operations", tags=["Peak, Queue & Stock-out"])
HOURLY_PROFILE = [0.015,0.01,0.008,0.008,0.01,0.025,0.055,0.08,0.085,0.06,0.045,0.04,0.04,0.045,0.05,0.06,0.075,0.09,0.085,0.06,0.04,0.025,0.02,0.014]

def _station(station_id):
    return next((s for s in load_stations() if str(s.get("station_id")) == station_id), None)

@router.get("/stations")
def operational_stations():
    rows=[]
    for s in load_stations():
        if s.get("avg_sales_kg_day_30d") is not None and s.get("capacity_kg_day"):
            rows.append({"station_id":s["station_id"],"station_name":s["station_name"],"avg_sales_kg_day_30d":s["avg_sales_kg_day_30d"],"capacity_kg_day":s["capacity_kg_day"]})
    return {"stations":rows,"data_status":"synthetic_demo_inputs"}

@router.get("/queue-simulation/{station_id}")
def queue_simulation(station_id: str, peak_multiplier: float = Query(1.15, ge=0.5, le=3.0)):
    s=_station(station_id)
    if not s: raise HTTPException(status_code=404, detail="Station not found")
    demand=s.get("avg_sales_kg_day_30d"); capacity=s.get("capacity_kg_day")
    if demand is None or not capacity or capacity <= 0:
        raise HTTPException(status_code=422, detail="Station lacks demo demand/capacity inputs")
    demand=float(demand)*peak_multiplier; capacity=float(capacity); hourly_capacity=capacity/24.0
    cumulative_demand=cumulative_served=0.0; rows=[]; peak_excess=0.0; queue_pressure_hours=0; stockout_hour=None
    for hour,share in enumerate(HOURLY_PROFILE):
        arrival=demand*share; cumulative_demand+=arrival; remaining=max(0.0,capacity-cumulative_served)
        served=min(arrival,hourly_capacity,remaining); excess=max(0.0,arrival-hourly_capacity); unmet=max(0.0,arrival-served); cumulative_served+=served
        if excess>0: queue_pressure_hours+=1
        peak_excess=max(peak_excess,excess)
        if stockout_hour is None and cumulative_demand>capacity: stockout_hour=hour
        rows.append({"hour":hour,"forecast_demand_kg":round(arrival,1),"hourly_service_capacity_kg":round(hourly_capacity,1),"served_kg":round(served,1),"queue_pressure_kg":round(excess,1),"unserved_kg":round(unmet,1)})
    total_unserved=max(0.0,demand-capacity)
    risk="HIGH" if total_unserved>0 or peak_excess>hourly_capacity*0.5 else "MEDIUM" if queue_pressure_hours>=2 else "LOW"
    return {"station_id":station_id,"station_name":s["station_name"],"scenario":{"daily_baseline_demand_kg":round(float(s["avg_sales_kg_day_30d"]),1),"peak_multiplier":peak_multiplier,"scenario_demand_kg":round(demand,1),"daily_capacity_kg":round(capacity,1)},"summary":{"risk":risk,"queue_pressure_hours":queue_pressure_hours,"max_hourly_excess_kg":round(peak_excess,1),"stockout_risk":total_unserved>0,"stockout_hour":stockout_hour,"estimated_unserved_kg":round(total_unserved,1)},"hourly":rows,"method":"synthetic_hourly_profile + capacity_constraint","warning":"Scenario simulation using synthetic daily inputs and an assumed hourly profile. Queue pressure is a capacity-excess indicator, not measured queue length or customer waiting time."}

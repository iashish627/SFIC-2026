"""Transparent planning tools built on the prototype's forecast and GIS inputs.

All target, queue-risk and location scores are decision-support indicators, not observed
Gujarat Gas operational metrics. The response labels every proxy and assumption.
"""
from fastapi import APIRouter, Query
from backend.modules.gis.router import load_stations

router = APIRouter(prefix="/api/planner", tags=["Sales & Network Planner"])

@router.get("/sales-targets")
def sales_targets(
    target_growth_pct: float = Query(10, ge=0, le=100),
    horizon_days: int = Query(30, ge=7, le=365),
):
    stations = [s for s in load_stations() if s.get("avg_sales_kg_day_30d") is not None]
    rows=[]
    for s in stations:
        baseline=float(s["avg_sales_kg_day_30d"])
        forecast=baseline*horizon_days
        target=forecast*(1+target_growth_pct/100)
        rows.append({
            "station_id":s["station_id"], "station_name":s["station_name"],
            "forecast_sales_kg":round(forecast,1), "target_sales_kg":round(target,1),
            "target_gap_kg":round(target-forecast,1),
            "priority":"HIGH" if target-forecast>forecast*0.15 else "MEDIUM" if target_growth_pct>0 else "BASELINE"
        })
    rows.sort(key=lambda x:x["target_gap_kg"], reverse=True)
    return {
        "horizon_days":horizon_days, "target_growth_pct":target_growth_pct,
        "stations":rows,
        "provenance":"synthetic_demo_capacity_and_sales",
        "warning":"Targets are planner assumptions applied to synthetic demo baselines; they are not company sales targets."
    }

@router.get("/peak-risk")
def peak_risk():
    stations=load_stations(); rows=[]
    for s in stations:
        avg=s.get("avg_sales_kg_day_30d"); peak=s.get("peak_demand_kg_day"); cap=s.get("capacity_kg_day")
        if avg is None or cap in (None,0): continue
        utilization=avg/cap
        peak_util=(peak/cap) if peak is not None else utilization
        risk="HIGH" if peak_util>=0.9 else "MEDIUM" if peak_util>=0.75 else "LOW"
        rows.append({"station_id":s["station_id"],"station_name":s["station_name"],
            "avg_utilization_pct":round(utilization*100,1),"peak_day_utilization_pct":round(peak_util*100,1),
            "planning_risk":risk})
    rows.sort(key=lambda x:x["peak_day_utilization_pct"], reverse=True)
    return {"stations":rows,"indicator":"capacity-pressure proxy from synthetic daily data",
        "warning":"This does not predict hourly queues or stock-outs. Hourly throughput, queue length and supply data are required for operational queue modelling."}

"""Sales and network planning decision-support APIs.

All calculations are transparent prototype indicators built from the repository's demo
dataset. They support planning discussions and do not represent Gujarat Gas targets or
measured operational performance.
"""
import csv
from pathlib import Path
from fastapi import APIRouter, Query
from backend.modules.gis.router import load_stations, SALES_CSV, DEMO_SALES_CSV

router = APIRouter(prefix="/api/planner", tags=["Sales & Network Planner"])

def _period_days(period: str) -> int:
    return {"monthly": 30, "quarterly": 90, "yearly": 365}.get(period, 30)

def _sales_history():
    path = SALES_CSV if SALES_CSV.exists() else DEMO_SALES_CSV
    if not path.exists():
        return {}
    rows={}
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            try:
                sid=r.get("station_id")
                val=float(r.get("sales_kg"))
                if sid: rows.setdefault(sid,[]).append((r.get("date",""),val))
            except (TypeError,ValueError):
                pass
    return {k:[v for _,v in sorted(x)] for k,x in rows.items()}

@router.get("/sales-targets")
def sales_targets(
    target_growth_pct: float = Query(10, ge=0, le=100),
    period: str = Query("monthly", pattern="^(monthly|quarterly|yearly)$"),
):
    days=_period_days(period)
    rows=[]
    for s in load_stations():
        baseline=s.get("avg_sales_kg_day_30d")
        if baseline is None: continue
        forecast=float(baseline)*days
        target=forecast*(1+target_growth_pct/100)
        util=float(s.get("utilization") or 0)
        if util>=0.90: action="Protect capacity first; growth target may require expansion."
        elif util>=0.75: action="Target peak periods and monitor capacity."
        else: action="Prioritise sales growth; capacity headroom is available."
        rows.append({"station_id":s["station_id"],"station_name":s["station_name"],
            "forecast_sales_kg":round(forecast,1),"target_sales_kg":round(target,1),
            "target_gap_kg":round(target-forecast,1),"utilization_pct":round(util*100,1),
            "recommended_action":action,
            "priority":"HIGH" if util>=.9 or target-forecast>forecast*.15 else "MEDIUM"})
    rows.sort(key=lambda x:x["target_gap_kg"],reverse=True)
    return {"period":period,"period_days":days,"target_growth_pct":target_growth_pct,
        "stations":rows,"warning":"Targets are planner assumptions applied to synthetic demo baselines; they are not company sales targets."}

@router.get("/growth-opportunities")
def growth_opportunities(period: str = Query("monthly", pattern="^(monthly|quarterly|yearly)$")):
    days=_period_days(period); rows=[]
    for s in load_stations():
        avg=s.get("avg_sales_kg_day_30d"); cap=s.get("capacity_kg_day")
        if avg is None or not cap: continue
        headroom=max(0,float(cap)-float(avg))
        opportunity=headroom*days
        if headroom<=0: action="Do not push additional sales before resolving capacity pressure."
        elif headroom/float(cap)<.15: action="Focus on reliability and peak management; expansion review before aggressive growth."
        else: action="Prioritise local sales activation and fleet/customer acquisition while monitoring utilisation."
        rows.append({"station_id":s["station_id"],"station_name":s["station_name"],
            "period":period,"available_capacity_kg_day":round(headroom,1),
            "potential_headroom_kg":round(opportunity,1),"recommended_action":action})
    rows.sort(key=lambda x:x["potential_headroom_kg"],reverse=True)
    return {"period":period,"stations":rows,
        "method":"capacity_headroom_opportunity_proxy",
        "warning":"Opportunity is unused synthetic capacity, not guaranteed new customer demand."}

@router.get("/peak-risk")
def peak_risk():
    rows=[]
    for s in load_stations():
        avg=s.get("avg_sales_kg_day_30d"); peak=s.get("peak_demand_kg_day"); cap=s.get("capacity_kg_day")
        if avg is None or not cap: continue
        utilization=float(avg)/float(cap); peak_util=(float(peak)/float(cap)) if peak is not None else utilization
        risk="HIGH" if peak_util>=.9 else "MEDIUM" if peak_util>=.75 else "LOW"
        rows.append({"station_id":s["station_id"],"station_name":s["station_name"],
            "avg_utilization_pct":round(utilization*100,1),"peak_day_utilization_pct":round(peak_util*100,1),
            "planning_risk":risk})
    rows.sort(key=lambda x:x["peak_day_utilization_pct"],reverse=True)
    return {"stations":rows,"warning":"Daily capacity-pressure proxy. Use the hourly operations simulation for peak-hour scenarios."}

@router.get("/forecast-quality")
def forecast_quality():
    history=_sales_history(); output=[]
    for s in load_stations():
        vals=history.get(s.get("station_id"),[])
        if len(vals)<14: continue
        actual=vals[-7:]; train=vals[:-7]
        preds=[]
        for i in range(7):
            window=(train+actual[:i])[-7:]
            preds.append(sum(window)/len(window))
        errors=[abs(a-p) for a,p in zip(actual,preds)]
        mae=sum(errors)/len(errors)
        mape=sum(abs(a-p)/max(abs(a),1)*100 for a,p in zip(actual,preds))/len(actual)
        status="HIGH_ERROR" if mape>20 else "WATCH" if mape>10 else "GOOD"
        action=("Review data quality and add recent drivers before using this forecast for expansion."
                if status=="HIGH_ERROR" else "Monitor model; refresh forecast as new sales arrive."
                if status=="WATCH" else "Baseline error is within prototype threshold; continue monitoring.")
        output.append({"station_id":s["station_id"],"station_name":s["station_name"],
            "mae_kg_day":round(mae,2),"mape_pct":round(mape,2),"status":status,"recommended_action":action})
    output.sort(key=lambda x:x["mape_pct"],reverse=True)
    return {"stations":output,"method":"7-day rolling moving-average holdout",
        "warning":"Accuracy is evaluated on synthetic demo history and is not evidence of production forecast performance."}

@router.get("/recommendations")
def recommendations():
    rows=[]
    for s in load_stations():
        util=float(s.get("utilization") or 0)
        if s.get("capacity_kg_day") is None: continue
        if util>=.9: rec="EXPAND_OR_REBALANCE"; why="High utilisation leaves limited resilience during demand spikes."
        elif util>=.75: rec="MONITOR_PEAKS"; why="Capacity is tightening; inspect peak-hour scenarios before growth campaigns."
        else: rec="GROW_SALES"; why="Capacity headroom is available for measured sales growth."
        rows.append({"station_id":s["station_id"],"station_name":s["station_name"],"utilization_pct":round(util*100,1),
                     "recommendation":rec,"reason":why})
    rows.sort(key=lambda x:x["utilization_pct"],reverse=True)
    return {"stations":rows,"warning":"Rule-based recommendations use synthetic capacity and sales estimates."}

@router.get("/potential-impact")
def potential_impact():
    stations=load_stations()
    with_capacity=[s for s in stations if s.get("capacity_kg_day")]
    high=sum(1 for s in with_capacity if float(s.get("utilization") or 0)>=.9)
    return {"impacts":[
        {"area":"Brand trust","indicator":"Service reliability planning","description":"Flag capacity pressure before it becomes a repeated service disruption scenario."},
        {"area":"Capital efficiency","indicator":"Ranked investment screening","description":"Compare expansion pressure and candidate screening before committing capital."},
        {"area":"Pipeline gas utilisation","indicator":"Demand-capacity alignment","description":"Use sales targets and network demand outlook to plan utilisation rather than isolated station decisions."},
        {"area":"EV resilience","indicator":"Scenario stress testing","description":"Test long-term CNG expansion choices under baseline, moderate and accelerated EV transition assumptions."}],
        "network_context":{"stations_with_capacity":len(with_capacity),"high_capacity_pressure_stations":high},
        "warning":"Impact statements describe intended planning value, not measured business outcomes."}

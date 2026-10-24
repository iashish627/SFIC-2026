"""Transparent A/B/C CNG scenario engine. Demand and capacity inputs use kg/day."""
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class Station:
    station_id: str
    baseline_kg_day: float
    capacity_kg_day: float

def _nonnegative(name, value):
    value=float(value)
    if value < 0: raise ValueError(f"{name} must be >= 0")
    return value

def run_simulation(stations: Iterable[Station], horizon_days=30, demand_uplift_pct=0,
                   shock_days=(), expand_station_id=None, added_capacity_kg_day=0,
                   expansion_cost=0, new_site_potential_kg_day=0,
                   new_site_capacity_kg_day=0, diversion_pct=0, new_site_cost=0):
    """Compare all scenarios against one baseline; shock_days are 1-based horizon days."""
    rows=list(stations)
    if not rows: raise ValueError("At least one station is required")
    if not 1 <= int(horizon_days) <= 365: raise ValueError("horizon_days must be between 1 and 365")
    uplift=_nonnegative("demand_uplift_pct", demand_uplift_pct)
    if uplift > 300: raise ValueError("demand_uplift_pct must be <= 300")
    diversion=float(diversion_pct)
    if not 0 <= diversion <= 100: raise ValueError("diversion_pct must be between 0 and 100")
    added=_nonnegative("added_capacity_kg_day", added_capacity_kg_day)
    potential=_nonnegative("new_site_potential_kg_day", new_site_potential_kg_day)
    new_cap=_nonnegative("new_site_capacity_kg_day", new_site_capacity_kg_day)
    expansion_cost=_nonnegative("expansion_cost", expansion_cost)
    new_cost=_nonnegative("new_site_cost", new_site_cost)
    ids=[s.station_id for s in rows]
    if len(set(ids)) != len(ids): raise ValueError("station_id values must be unique")
    for s in rows:
        _nonnegative(f"{s.station_id} baseline_kg_day", s.baseline_kg_day)
        _nonnegative(f"{s.station_id} capacity_kg_day", s.capacity_kg_day)
    if expand_station_id is not None and expand_station_id not in ids:
        raise ValueError("expand_station_id not found in stations")
    shocks=set(int(d) for d in shock_days)
    if any(d < 1 or d > horizon_days for d in shocks):
        raise ValueError("shock_days must fall within the horizon (1-based)")
    daily=[]
    for day in range(1, horizon_days+1):
        factor=1+uplift/100 if day in shocks else 1
        for s in rows:
            daily.append({"day":day,"station_id":s.station_id,
                          "demand":s.baseline_kg_day*factor,"capacity":s.capacity_kg_day})
    demand=sum(x["demand"] for x in daily)
    capacity=sum(s.capacity_kg_day*horizon_days for s in rows)
    served=sum(min(x["demand"],x["capacity"]) for x in daily)
    unmet=max(0,demand-served)
    expanded=[{**x,"capacity":x["capacity"]+(added if x["station_id"]==expand_station_id else 0)} for x in daily]
    expanded_served=sum(min(x["demand"],x["capacity"]) for x in expanded)
    expanded_capacity=sum(x["capacity"] for x in expanded)
    # Estimate diversion as a share of new-site potential; allocate it proportionally across existing demand.
    diversion_total=min(potential*diversion/100, sum(s.baseline_kg_day for s in rows))*horizon_days
    baseline_per_day=sum(s.baseline_kg_day for s in rows)
    share=min(1,(diversion_total/horizon_days)/baseline_per_day) if baseline_per_day else 0
    existing_served=0
    existing_unmet=0
    for x in daily:
        remaining=max(0,x["demand"]*(1-share))
        existing_served += min(remaining,x["capacity"])
        existing_unmet += max(0,remaining-x["capacity"])
    new_sales=min(potential,new_cap)*horizon_days
    net_incremental=new_sales-diversion_total
    def item(name,d,sv,cap,um,cost,note):
        return {"scenario":name,"horizon_days":horizon_days,"forecast_demand_kg":round(d,2),
                "served_demand_kg":round(sv,2),"unmet_demand_kg":round(max(0,um),2),
                "capacity_kg_over_horizon":round(cap,2),
                "capacity_utilisation_pct":round(sv/cap*100 if cap else 0,2),
                "estimated_cost":round(cost,2),"assumptions":note}
    scenarios=[
      item("A_NO_CHANGE",demand,served,capacity,unmet,0,"Current capacity; common baseline and shocks."),
      item("B_EXPAND_EXISTING",demand,expanded_served,expanded_capacity,demand-expanded_served,expansion_cost,
           f"Adds {added:g} kg/day to {expand_station_id}; cost is user input."),
      item("C_BUILD_NEW",max(0,demand+potential*horizon_days-diversion_total),
           existing_served+new_sales,capacity+new_cap*horizon_days,
           existing_unmet+max(0,potential-new_cap)*horizon_days,new_cost,
           f"Potential {potential:g} kg/day; diversion assumption {diversion:g}%; costs are user inputs.")
    ]
    return {"unit":"kg","demand_unit":"kg/day","provenance":"synthetic_or_user_supplied_inputs",
            "horizon_days":horizon_days,"shock_days":sorted(shocks),"demand_uplift_pct_on_shock_days":uplift,
            "baseline":{"forecast_demand_kg":round(demand,2),"served_demand_kg":round(served,2),"unmet_demand_kg":round(unmet,2)},
            "new_site_metrics":{"new_site_sales_kg":round(new_sales,2),"estimated_diverted_demand_kg":round(diversion_total,2),
             "net_incremental_demand_kg":round(net_incremental,2)},
            "scenarios":scenarios,
            "warnings":["Synthetic demo inputs do not represent actual Gujarat Gas operations.",
             "Diversion, potential demand, costs and capacity additions are assumptions, not measured facts.",
             "This is a scenario calculator, not a validated financial or geographic site-selection model."]}

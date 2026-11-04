"""Transparent scenario-based EV transition planning layer.

This module does not predict actual EV adoption. It applies explicit user-selected
assumptions to a long-term CNG demand baseline so planners can stress-test
network expansion decisions.
"""
from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/ev-scenarios", tags=["EV Transition Scenarios"])

class EVScenarioRequest(BaseModel):
    scenario: Literal["baseline", "moderate", "accelerated"] = "baseline"
    horizon_years: int = Field(default=5, ge=1, le=10)
    baseline_demand_kg_day: float = Field(default=1000, ge=0)
    annual_cng_growth_pct: float = Field(default=3, ge=-20, le=50)
    annual_ev_displacement_pct: float | None = Field(default=None, ge=0, le=50)
    new_site_potential_kg_day: float = Field(default=900, ge=0)
    diversion_pct: float = Field(default=20, ge=0, le=100)

DEFAULT_DISPLACEMENT = {"baseline": 0.0, "moderate": 4.0, "accelerated": 9.0}

@router.get("/presets")
def presets():
    return {
        "scenarios": [
            {"id":"baseline","label":"Baseline","default_annual_ev_displacement_pct":0.0},
            {"id":"moderate","label":"Moderate EV Adoption","default_annual_ev_displacement_pct":4.0},
            {"id":"accelerated","label":"Accelerated Electrification","default_annual_ev_displacement_pct":9.0},
        ],
        "warning":"Scenario assumptions are illustrative and user-adjustable. They are not a forecast of actual EV adoption or Gujarat Gas sales."
    }

@router.post("/run")
def run_ev_scenario(request: EVScenarioRequest):
    displacement = request.annual_ev_displacement_pct
    if displacement is None:
        displacement = DEFAULT_DISPLACEMENT[request.scenario]
    projection=[]
    demand=request.baseline_demand_kg_day
    for year in range(1, request.horizon_years + 1):
        demand = demand * (1 + request.annual_cng_growth_pct / 100) * (1 - displacement / 100)
        projection.append({"year": year, "projected_cng_demand_kg_day": round(demand, 2)})
    final_demand = projection[-1]["projected_cng_demand_kg_day"] if projection else request.baseline_demand_kg_day
    gross_new_site = request.new_site_potential_kg_day * request.horizon_years * 365
    diverted = gross_new_site * request.diversion_pct / 100
    ev_factor = final_demand / request.baseline_demand_kg_day if request.baseline_demand_kg_day else 1
    ev_adjusted_incremental = max(0, (gross_new_site - diverted) * ev_factor)
    if ev_adjusted_incremental >= gross_new_site * 0.55:
        decision="Strong under selected scenario"
    elif ev_adjusted_incremental >= gross_new_site * 0.25:
        decision="Review assumptions before expansion"
    else:
        decision="Higher long-term demand sensitivity"
    return {
        "provenance":"hypothetical_scenario",
        "scenario":request.scenario,
        "horizon_years":request.horizon_years,
        "assumptions":{
            "baseline_demand_kg_day":request.baseline_demand_kg_day,
            "annual_cng_growth_pct":request.annual_cng_growth_pct,
            "annual_ev_displacement_pct":displacement,
            "diversion_pct":request.diversion_pct,
        },
        "projection":projection,
        "expansion_impact":{
            "gross_new_site_demand_kg":round(gross_new_site,2),
            "estimated_diverted_demand_kg":round(diverted,2),
            "ev_adjusted_net_incremental_demand_kg":round(ev_adjusted_incremental,2),
            "decision":decision,
        },
        "warning":"Scenario-based planning output only. Results depend on selected assumptions and are not a prediction of actual EV adoption, CNG sales or site profitability."
    }

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.modules.simulation.engine import Station,run_simulation
client=TestClient(app)

@pytest.fixture
def stations():
    return [Station("A",120,100),Station("B",80,100)]

def test_three_scenarios_share_baseline(stations):
    r=run_simulation(stations,horizon_days=10,expand_station_id="A",added_capacity_kg_day=30,
      new_site_potential_kg_day=50,new_site_capacity_kg_day=60,diversion_pct=20)
    assert [x["scenario"] for x in r["scenarios"]]==["A_NO_CHANGE","B_EXPAND_EXISTING","C_BUILD_NEW"]
    assert r["baseline"]["forecast_demand_kg"]==2000
    assert r["scenarios"][0]["forecast_demand_kg"]==r["scenarios"][1]["forecast_demand_kg"]

def test_shock_only_selected_days(stations):
    r=run_simulation(stations,horizon_days=4,demand_uplift_pct=50,shock_days=[2])
    assert r["baseline"]["forecast_demand_kg"]==900

def test_expansion_reduces_unmet_demand(stations):
    r=run_simulation(stations,horizon_days=1,expand_station_id="A",added_capacity_kg_day=30)
    assert r["scenarios"][1]["unmet_demand_kg"]<r["scenarios"][0]["unmet_demand_kg"]

def test_net_incremental_is_new_sales_minus_diversion(stations):
    r=run_simulation(stations,horizon_days=10,new_site_potential_kg_day=50,new_site_capacity_kg_day=40,diversion_pct=25)
    m=r["new_site_metrics"]
    assert m["new_site_sales_kg"]==400 and m["estimated_diverted_demand_kg"]==100
    assert m["net_incremental_demand_kg"]==300

def test_diversion_never_exceeds_new_site_sales_or_breaks_network_balance(stations):
    r=run_simulation(stations,horizon_days=10,demand_uplift_pct=50,shock_days=[2,3],
        new_site_potential_kg_day=20,new_site_capacity_kg_day=5,diversion_pct=100)
    m=r["new_site_metrics"]
    c=next(s for s in r["scenarios"] if s["scenario"]=="C_BUILD_NEW")
    assert m["estimated_diverted_demand_kg"] <= m["new_site_sales_kg"]
    assert abs(c["forecast_demand_kg"] - c["served_demand_kg"] - c["unmet_demand_kg"]) < 0.02

def test_diversion_is_capped_by_existing_network_demand(stations):
    r=run_simulation([Station("A",1,1)],horizon_days=5,
        new_site_potential_kg_day=100,new_site_capacity_kg_day=100,diversion_pct=100)
    m=r["new_site_metrics"]
    assert m["new_site_sales_kg"] == 500
    assert m["estimated_diverted_demand_kg"] == 5
    assert m["net_incremental_demand_kg"] == 495
    c=next(s for s in r["scenarios"] if s["scenario"]=="C_BUILD_NEW")
    assert abs(c["forecast_demand_kg"] - c["served_demand_kg"] - c["unmet_demand_kg"]) < 0.02

def test_rejects_invalid_shock_day(stations):
    with pytest.raises(ValueError): run_simulation(stations,horizon_days=5,shock_days=[6])

def test_rejects_negative_capacity():
    with pytest.raises(ValueError): run_simulation([Station("A",10,-1)])

def test_rejects_unknown_expansion_station(stations):
    with pytest.raises(ValueError): run_simulation(stations,expand_station_id="missing")

def test_api_demo_inputs():
    r=client.get("/api/simulator/demo-inputs")
    assert r.status_code==200 and r.json()["provenance"]=="synthetic"
    assert len(r.json()["stations"])==8

def test_api_run_returns_three_scenarios():
    r=client.post("/api/simulator/run",json={"horizon_days":30,"demand_uplift_pct":20,"shock_days":[4,5],
      "expand_station_id":"SYN-GJ-001","added_capacity_kg_day":300,"new_site_potential_kg_day":700,
      "new_site_capacity_kg_day":800,"diversion_pct":15})
    assert r.status_code==200,r.text
    assert len(r.json()["scenarios"])==3

def test_api_rejects_bad_shock():
    r=client.post("/api/simulator/run",json={"horizon_days":5,"shock_days":[6]})
    assert r.status_code==422

def test_capacity_utilisation_reflects_over_capacity_demand():
    result = run_simulation([Station("OVER", 150, 100)], horizon_days=1)
    baseline = result["scenarios"][0]
    assert baseline["served_demand_kg"] == 100
    assert baseline["unmet_demand_kg"] == 50
    assert baseline["capacity_utilisation_pct"] == 150

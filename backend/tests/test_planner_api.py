from fastapi.testclient import TestClient
from backend.main import app

client=TestClient(app)

def test_sales_target_planner_contract():
    r=client.get("/api/planner/sales-targets",params={"target_growth_pct":12,"horizon_days":30})
    assert r.status_code==200
    data=r.json()
    assert data["target_growth_pct"]==12
    assert "stations" in data

def test_peak_risk_is_transparent_proxy():
    r=client.get("/api/planner/peak-risk")
    assert r.status_code==200
    data=r.json()
    assert "warning" in data and "hourly queues" in data["warning"]

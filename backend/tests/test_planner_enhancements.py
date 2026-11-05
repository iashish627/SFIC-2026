from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_sales_targets_monthly():
    r=client.get("/api/planner/sales-targets",params={"period":"monthly","target_growth_pct":10})
    assert r.status_code==200
    assert r.json()["period"]=="monthly"

def test_growth_and_recommendations():
    assert client.get("/api/planner/growth-opportunities").status_code==200
    assert client.get("/api/planner/recommendations").status_code==200
    assert client.get("/api/planner/potential-impact").status_code==200

def test_forecast_quality_contract():
    r=client.get("/api/planner/forecast-quality")
    assert r.status_code==200
    assert "method" in r.json()

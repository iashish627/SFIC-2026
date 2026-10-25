from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_weekly_forecast_aggregates_daily_baseline():
    result = client.get("/api/forecast/weekly/SYN-GJ-001", params={"weeks": 4})
    assert result.status_code == 200
    body = result.json()
    assert len(body["weekly_forecast"]) == 4
    assert all(row["predicted_demand_kg"] >= 0 for row in body["weekly_forecast"])
    assert body["provenance"] == "synthetic_demo"

def test_time_based_evaluation_reports_holdout_metrics():
    result = client.get("/api/forecast/evaluate/SYN-GJ-001", params={"test_days": 14})
    assert result.status_code == 200
    body = result.json()
    assert body["split_type"] == "chronological_holdout"
    assert body["train_days"] > body["test_days"]
    assert body["mae_kg_day"] >= 0
    assert body["wape_pct"] is None or body["wape_pct"] >= 0
    assert "synthetic demo series" in body["warning"]

def test_evaluation_rejects_invalid_or_unavailable_history():
    assert client.get("/api/forecast/evaluate/NOT-A-STATION").status_code == 404
    assert client.get("/api/forecast/evaluate/SYN-GJ-001?test_days=40").status_code == 422

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_forecast_station_list_uses_synthetic_provenance():
    response = client.get("/api/forecast/stations")
    assert response.status_code == 200
    payload = response.json()
    assert payload["provenance"] == "synthetic_demo"
    assert payload["count"] == len(payload["stations"])
    assert payload["count"] == 8

def test_station_forecast_returns_requested_horizon_and_dates():
    stations = client.get("/api/forecast/stations").json()["stations"]
    station_id = stations[0]["station_id"]
    response = client.get(f"/api/forecast/station/{station_id}", params={"days": 10})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["forecast"]) == 10
    assert payload["forecast"][0]["date"] > payload["history"]["end"]
    assert all(row["predicted_demand_kg"] >= 0 for row in payload["forecast"])
    assert payload["provenance"] == "synthetic_demo"

def test_forecast_rejects_unknown_station_and_invalid_horizon():
    assert client.get("/api/forecast/station/NOT-A-STATION").status_code == 404
    assert client.get("/api/forecast/station/SYN-GJ-001?days=60").status_code == 422

def test_forecast_supports_moving_average_baseline():
    payload = client.get("/api/forecast/station/SYN-GJ-001", params={"days": 3, "model": "moving_average"}).json()
    assert payload["method"] == "moving_average_7d"
    assert len(payload["forecast"]) == 3

"""Cross-module smoke tests for the integrated hackathon demo."""
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]

def test_all_primary_api_modules_are_registered():
    assert client.get("/health").status_code == 200
    assert client.get("/api/gis/stations").status_code == 200
    assert client.get("/api/dashboard/summary").status_code == 200
    assert client.get("/api/forecast/stations").status_code == 200
    assert client.get("/api/simulator/demo-inputs").status_code == 200
    assert client.get("/api/health/data").status_code == 200

def test_simulator_and_forecast_work_on_same_demo_station():
    demo = client.get("/api/simulator/demo-inputs").json()
    assert demo["stations"]
    station_id = demo["stations"][0]["station_id"]
    forecast = client.get(f"/api/forecast/station/{station_id}", params={"days": 7})
    assert forecast.status_code == 200
    baseline = next(s for s in demo["stations"] if s["station_id"] == station_id)
    run = client.post("/api/simulator/run", json={
        "stations": [baseline],
        "horizon_days": 7,
        "demand_uplift_pct": 20,
        "shock_days": [3],
        "expand_station_id": station_id,
        "added_capacity_kg_day": 100,
        "new_site_potential_kg_day": 200,
        "new_site_capacity_kg_day": 180,
        "diversion_pct": 10,
    })
    assert run.status_code == 200, run.text
    payload = run.json()
    assert [s["scenario"] for s in payload["scenarios"]] == ["A_NO_CHANGE", "B_EXPAND_EXISTING", "C_BUILD_NEW"]
    assert payload["provenance"] == "synthetic_or_user_supplied_inputs"

def test_frontend_pages_are_connected_to_their_backend_routes():
    forecast_page = (ROOT / "frontend" / "forecast.html").read_text(encoding="utf-8")
    simulator_page = (ROOT / "frontend" / "simulator.html").read_text(encoding="utf-8")
    dashboard_page = (ROOT / "frontend" / "dashboard.html").read_text(encoding="utf-8")
    assert "/api/forecast/stations" in forecast_page
    assert "/api/forecast/station/" in forecast_page
    assert "/api/simulator/demo-inputs" in simulator_page
    assert "/api/scenarios/run" in simulator_page
    assert "/api/dashboard/summary" in dashboard_page

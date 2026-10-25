from fastapi.testclient import TestClient

from backend.main import app
import backend.modules.scenarios.router as scenario_store

client = TestClient(app)


def test_scenario_run_is_persisted_and_retrievable(monkeypatch, tmp_path):
    monkeypatch.setattr(scenario_store, "DB_PATH", tmp_path / "scenario_runs.sqlite3")
    request = {
        "stations": [
            {"station_id": "TEST-A", "baseline_kg_day": 120, "capacity_kg_day": 100},
            {"station_id": "TEST-B", "baseline_kg_day": 80, "capacity_kg_day": 100},
        ],
        "horizon_days": 7,
        "demand_uplift_pct": 20,
        "shock_days": [3],
        "expand_station_id": "TEST-A",
        "added_capacity_kg_day": 25,
        "new_site_potential_kg_day": 50,
        "new_site_capacity_kg_day": 45,
        "diversion_pct": 20,
        "expansion_cost": 1000,
        "new_site_cost": 2000,
    }
    response = client.post("/api/scenarios/run", json=request)
    assert response.status_code == 201, response.text
    payload = response.json()
    scenario_id = payload["scenario_id"]
    assert payload["status"] == "completed"
    assert payload["model_version"] == "scenario-engine-v1"
    assert len(payload["scenarios"]) == 3

    detail = client.get(f"/api/scenarios/{scenario_id}")
    assert detail.status_code == 200
    assert detail.json()["inputs"]["horizon_days"] == 7
    assert detail.json()["outputs"]["scenario_id"] == scenario_id

    listing = client.get("/api/scenarios?limit=10")
    assert listing.status_code == 200
    assert listing.json()["count"] == 1
    assert listing.json()["scenarios"][0]["scenario_id"] == scenario_id

    report = client.get(f"/api/scenarios/{scenario_id}/report.csv")
    assert report.status_code == 200
    assert "text/csv" in report.headers["content-type"]
    assert "A_NO_CHANGE" in report.text
    assert scenario_id in report.text


def test_saved_scenario_unknown_id_returns_404(monkeypatch, tmp_path):
    monkeypatch.setattr(scenario_store, "DB_PATH", tmp_path / "scenario_runs.sqlite3")
    assert client.get("/api/scenarios/does-not-exist").status_code == 404
    assert client.get("/api/scenarios/does-not-exist/report.csv").status_code == 404


def test_data_quality_and_network_forecast_contracts():
    quality = client.get("/api/health/data")
    assert quality.status_code == 200
    body = quality.json()
    assert body["provenance"] == "synthetic_demo"
    assert "daily_sales" in body["layers"]
    assert "missing_sales_records" in body["layers"]["daily_sales"]
    assert body["warnings"]

    network = client.get("/api/forecast/network", params={"days": 30})
    assert network.status_code == 200
    forecast = network.json()
    assert len(forecast["forecast"]) == 30
    assert forecast["stations_included"] > 0
    assert forecast["model_version"] == "baseline-v1"
    assert forecast["provenance"] == "synthetic_demo"


def test_station_forecast_includes_ordered_nonnegative_bounds():
    stations = client.get("/api/forecast/stations").json()["stations"]
    station_id = next(s["station_id"] for s in stations if s["valid_history_days"] > 0)
    response = client.get(f"/api/forecast/station/{station_id}", params={"days": 7})
    assert response.status_code == 200
    body = response.json()
    assert body["model_version"] == "baseline-v1"
    assert len(body["forecast"]) == 7
    for row in body["forecast"]:
        assert row["lower_bound_kg"] >= 0
        assert row["lower_bound_kg"] <= row["predicted_demand_kg"] <= row["upper_bound_kg"]

def test_weekly_and_holdout_forecast_endpoints():
    station_id = "SYN-GJ-001"
    weekly = client.get(f"/api/forecast/weekly/{station_id}", params={"weeks": 4})
    assert weekly.status_code == 200
    assert len(weekly.json()["weekly_forecast"]) == 4
    assert weekly.json()["provenance"] == "synthetic_demo"

    evaluation = client.get(f"/api/forecast/evaluate/{station_id}", params={"test_days": 14})
    assert evaluation.status_code == 200
    body = evaluation.json()
    assert body["split_type"] == "chronological_holdout"
    assert body["train_days"] > 0 and body["test_days"] == 14
    assert body["mae_kg_day"] >= 0 and body["rmse_kg_day"] >= 0
    assert "synthetic demo series" in body["warning"]


def test_remaining_pages_call_real_api_routes():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2] / "frontend"
    pages = {
        "stations.html": "/api/gis/stations",
        "sites.html": "/api/gis/candidate-analysis",
        "data.html": "/api/health/data",
        "reports.html": "/api/scenarios",
        "forecast.html": "/api/forecast/network",
        "simulator.html": "/api/scenarios/run",
    }
    for filename, route in pages.items():
        source = (root / filename).read_text(encoding="utf-8")
        assert route in source, f"{filename} is not connected to {route}"

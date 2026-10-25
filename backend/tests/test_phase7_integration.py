from datetime import date, timedelta

from fastapi.testclient import TestClient

from backend.main import app
import backend.modules.forecasting.router as forecasting

client = TestClient(app)


def test_all_primary_dashboard_modules_are_mounted_and_return_expected_contracts():
    assert client.get("/health").status_code == 200

    dashboard = client.get("/api/dashboard/summary")
    gis = client.get("/api/gis/stations")
    forecast = client.get("/api/forecast/stations")
    simulator = client.get("/api/simulator/demo-inputs")

    assert dashboard.status_code == 200
    assert dashboard.json()["provenance"] == "synthetic_demo"
    assert gis.status_code == 200
    assert gis.json()["count"] == len(gis.json()["items"])
    assert forecast.status_code == 200
    assert forecast.json()["provenance"] == "synthetic_demo"
    assert simulator.status_code == 200
    assert simulator.json()["provenance"] == "synthetic"
    assert len(simulator.json()["stations"]) > 0


def test_candidate_analysis_returns_proximity_not_a_fabricated_score():
    response = client.get(
        "/api/gis/candidate-analysis",
        params={"latitude": 22.3039, "longitude": 72.5850, "radii_km": "5,10,20"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "nearby" in payload
    assert "counts_within_km" in payload
    assert "interpretation" in payload
    assert "Straight-line proximity only" in payload["interpretation"]
    assert "not road travel time" in payload["interpretation"]
    assert "score" not in payload


def test_seasonal_naive_uses_exact_calendar_weekday_and_fallback_for_gap(monkeypatch):
    end = date(2026, 1, 14)
    # A history point exists exactly seven days before the first target date.
    history = {
        "TEST-STATION": {
            end - timedelta(days=6): 111.0,
            end - timedelta(days=2): 222.0,
            end: 333.0,
        }
    }
    monkeypatch.setattr(forecasting, "_load_history", lambda: history)
    response = client.get("/api/forecast/station/TEST-STATION", params={"days": 2})
    assert response.status_code == 200
    rows = response.json()["forecast"]
    assert rows[0]["date"] == (end + timedelta(days=1)).isoformat()
    assert rows[0]["predicted_demand_kg"] == 111.0
    assert rows[0]["method"] == "seasonal_naive_7d"
    # No matching point 7 calendar days before target day two: use recent-mean fallback.
    assert rows[1]["method"] == "moving_average_fallback_missing_weekday"
    assert rows[1]["predicted_demand_kg"] == 222.0

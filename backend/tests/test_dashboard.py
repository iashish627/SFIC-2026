from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dashboard_summary_is_explicitly_synthetic():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["provenance"] == "synthetic_demo"
    assert "not Gujarat Gas operational data" in body["data_note"]
    assert body["stations"]["demo_total"] == 8
    assert body["stations"]["with_capacity"] == 8
    assert body["stations"]["with_valid_coordinates"] == 8
    assert body["sales"]["valid_record_count"] > 0
    assert body["sales"]["daily_totals"]
    assert body["district_counts"]

def test_dashboard_summary_does_not_claim_candidate_rankings():
    body = client.get("/api/dashboard/summary").json()
    assert "candidate_sites" not in body
    assert "forecast_accuracy" not in body

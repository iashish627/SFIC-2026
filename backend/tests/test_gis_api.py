from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_gis_stations_endpoint_returns_contract():
    response = client.get("/api/gis/stations")
    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload and isinstance(payload["items"], list)
    assert payload["count"] == len(payload["items"])

def test_candidate_analysis_validates_coordinates():
    response = client.get("/api/gis/candidate-analysis", params={"latitude": 100, "longitude": 72})
    assert response.status_code == 422

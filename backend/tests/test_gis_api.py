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


def test_candidate_rank_uses_transparent_spacing_screen():
    response=client.post("/api/gis/rank-candidates",json={"minimum_spacing_km":5,"candidates":[{"name":"A","latitude":22.3039,"longitude":72.5850},{"name":"B","latitude":23.0225,"longitude":72.5714}]})
    assert response.status_code==200, response.text
    data=response.json()
    assert len(data["candidates"])==2
    assert data["method"]=="transparent_spacing_screen"
    assert "does not establish demand" in data["warning"]

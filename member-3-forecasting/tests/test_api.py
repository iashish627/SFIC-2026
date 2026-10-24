from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'


def test_horizon_over_30_rejected():
    response = client.post('/api/v1/forecast/generate', json={
        'station_ids': ['S1'], 'start_date': '2026-11-01', 'days': 90,
        'mode': 'estimated', 'base_demand_kg': 1000
    })
    assert response.status_code == 422


def test_invalid_uplift_rejected():
    response = client.post('/api/v1/forecast/scenario/demand-shock', json={
        'station_ids': ['S1'], 'start_date': '2026-11-01', 'end_date': '2026-11-02',
        'uplift_percentage': -10, 'base_demand_kg': 1000
    })
    assert response.status_code == 422

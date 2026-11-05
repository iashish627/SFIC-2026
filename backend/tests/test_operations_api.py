from fastapi.testclient import TestClient
from backend.main import app

client=TestClient(app)

def test_operational_station_list():
    r=client.get("/api/operations/stations")
    assert r.status_code==200
    assert isinstance(r.json()["stations"],list)

def test_queue_simulation_contract_when_demo_station_exists():
    stations=client.get("/api/operations/stations").json()["stations"]
    if not stations: return
    sid=stations[0]["station_id"]
    r=client.get(f"/api/operations/queue-simulation/{sid}",params={"peak_multiplier":1.2})
    assert r.status_code==200, r.text
    data=r.json()
    assert len(data["hourly"])==24
    assert "stockout_risk" in data["summary"]
    assert "not measured queue length" in data["warning"]

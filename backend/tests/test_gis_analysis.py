import pytest
from backend.modules.gis.analysis import distance_km, nearby_stations

def test_distance_same_point_is_zero():
    assert distance_km(21.1702, 72.8311, 21.1702, 72.8311) == pytest.approx(0)

def test_invalid_coordinates_raise():
    with pytest.raises(ValueError):
        distance_km(100, 0, 0, 0)

def test_nearby_counts_exclude_origin():
    origin = {"station_id": "a", "latitude": 21.0, "longitude": 72.0}
    stations = [origin, {"station_id": "b", "latitude": 21.01, "longitude": 72.0}]
    result = nearby_stations(origin, stations, (5, 10, 20))
    assert len(result["nearby"]) == 1
    assert result["counts_within_km"]["5"] == 1

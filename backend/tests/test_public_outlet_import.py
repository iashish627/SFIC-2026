from backend.scripts.import_public_outlets import normalize


def test_normalize_keeps_only_gujarat_and_marks_rows_provisional():
    rows = [
        {"state": "Gujarat", "id": "1", "name": "Outlet A", "lat": "21.1", "lon": "72.8", "has_cng": "1"},
        {"state": "Maharashtra", "id": "2", "name": "Outlet B", "lat": "19.0", "lon": "72.8", "has_cng": "1"},
        {"state": "Gujarat", "id": "3", "name": "Bad coords", "lat": "999", "lon": "72.8"},
    ]
    result = list(normalize(rows, "Gujarat"))
    assert len(result) == 1
    assert result[0]["station_id"] == "public-outlet-1"
    assert result[0]["latitude"] == 21.1
    assert result[0]["verified_gujarat_gas_station"] == "false"
    assert result[0]["source_url"].startswith("https://")


def test_normalize_deduplicates_same_id_and_coordinates():
    rows = [
        {"state": "Gujarat", "id": "1", "name": "Outlet A", "lat": "21.1", "lon": "72.8"},
        {"state": "Gujarat", "id": "1", "name": "Outlet A duplicate", "lat": "21.1", "lon": "72.8"},
    ]
    assert len(list(normalize(rows, "Gujarat"))) == 1

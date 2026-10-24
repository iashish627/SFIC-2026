# Run the integrated GIS API

From the repository root:

```bash
python -m pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Check `http://localhost:8000/docs` and `GET /api/gis/stations`.

## Load the public outlet discovery layer

To create a provisional candidate layer from the public CGD outlet mapping:

```bash
python backend/scripts/import_public_outlets.py
```

This downloads the public outlet table, filters rows whose state field identifies Gujarat, validates coordinates, and writes `data/processed/stations.csv`. The script preserves the source URL, outlet ID, CNG flag, operator/status fields when present, and marks every row `verified_gujarat_gas_station=false`.

This dataset is a public retail-outlet mapping. A CNG flag or CGD authorisation does not prove current operation, Gujarat Gas ownership/supply, capacity, or observed demand. Treat imported markers as **provisional candidates**, not company-confirmed stations. Verify against Gujarat Gas records and current ground truth before using for decisions.

For a different CSV, set `CNG_STATIONS_CSV` to a file with at least `station_id,station_name,latitude,longitude`; optional provenance columns are preserved. Without a compatible file the API returns zero stations rather than fabricating coordinates.

The React GIS panels use `VITE_API_BASE_URL` from `frontend/.env` (defaults to `http://localhost:8000`). The basemap uses OpenStreetMap tiles; proximity calculations are straight-line distances, not validated demand catchments or road travel times.

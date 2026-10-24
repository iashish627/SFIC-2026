# Run the integrated GIS API

From the repository root:

```bash
python -m pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Check `http://localhost:8000/docs` and `GET /api/gis/stations`.

Configure `CNG_STATIONS_CSV` to a source-verified CSV containing at least
`station_id,station_name,latitude,longitude`. Optional columns are preserved.
Without that file the API deliberately returns zero stations rather than
inventing coordinates. The React GIS panel uses `VITE_API_BASE_URL` from
`frontend/.env` (defaults to `http://localhost:8000`).

The map uses OpenStreetMap tiles. Its marker locations are only as reliable as
the configured input CSV; proximity circles are not validated catchments.

# Run the integrated GIS API

From the repository root:

```bash
python -m pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Check `http://localhost:8000/docs` and open `http://localhost:8000/api/gis/stations` to inspect the returned `items` and `count`.

In a second terminal, serve the static frontend from the repository root:

```bash
python -m http.server 5173 --directory frontend
```

Open `http://localhost:5173/map.html`. The map uses `http://localhost:8000/api/gis/stations` by default. Keep both terminals running. If the map shows fewer pins than source rows, that is expected when rows lack usable coordinates or fall outside the map's approximate Gujarat display outline.

## Load the public outlet discovery layer

To create a provisional candidate layer from the public CGD outlet mapping:

```bash
python backend/scripts/import_public_outlets.py
```

This downloads the public outlet table, filters rows whose state field identifies Gujarat, validates coordinates, and writes `data/processed/stations.csv`. The script preserves the source URL, outlet ID, CNG flag, operator/status fields when present, and marks every row `verified_gujarat_gas_station=false`.

This dataset is a public retail-outlet mapping. A CNG flag or CGD authorisation does not prove current operation, Gujarat Gas ownership/supply, capacity, or observed demand. Treat imported markers as **provisional candidates**, not company-confirmed stations. Verify against Gujarat Gas records and current ground truth before using for decisions.

For a different CSV, set `CNG_STATIONS_CSV` to a file with at least `station_id,station_name,latitude,longitude`; optional provenance columns are preserved. Without a compatible file the API returns zero stations rather than fabricating coordinates.

The React GIS panels use `VITE_API_BASE_URL` from `frontend/.env` (defaults to `http://localhost:8000`). The basemap uses OpenStreetMap tiles; proximity calculations are straight-line distances, not validated demand catchments or road travel times.

## Geocode the 344-record Gujarat Gas directory

The helper `backend/scripts/geocode_station_directory.py` preserves all input records and writes a separate geocoded CSV. It supports Google's Geocoding API using the official `googlemaps` Python client, and an explicit Nominatim fallback.

For Google geocoding, enable billing and the Geocoding API for a Google Cloud project, create a restricted server-side API key, and set it only in your shell (do not commit it):

PowerShell:
```powershell
$env:GOOGLE_MAPS_API_KEY = "YOUR_RESTRICTED_SERVER_SIDE_KEY"
python -m pip install -r backend/requirements.txt
python backend/scripts/geocode_station_directory.py --provider google
```

Without a Google key, automatic mode uses the public Nominatim fallback:
```powershell
python backend/scripts/geocode_station_directory.py --provider nominatim
```

Output: `member-3-forecasting/data/gujarat_gas_directory_344_geocoded.csv`. Rows are marked `needs_manual_review` when a geocoder returns a result. The top geocoding result can identify a neighborhood or road rather than the exact pump, so do not present those coordinates as verified station locations until reviewed. API usage can incur charges and is subject to Google Maps Platform terms. Keep keys out of source control.


## Map troubleshooting

- **Blank map or “API UNAVAILABLE”:** confirm FastAPI is running on port 8000 and open `http://localhost:8000/api/gis/stations` directly. Check browser DevTools Console and Network for failed requests.
- **Basemap missing but controls render:** check internet access to the tile provider. The map attempts to fall back from its Google-style public tile endpoint to OpenStreetMap tiles; the Google-style endpoint is best-effort, not an official guaranteed integration.
- **Only a subset of stations appears:** the API returns only coordinate-valid rows. The frontend further filters rows to positive CNG flags and an approximate Gujarat outline. This is not evidence that other directory rows do not exist; they may have missing coordinates or fall outside the coarse outline.
- **Unexpected data source:** inspect `CNG_STATIONS_CSV` in the backend process environment and check the default source priority documented in [GIS_INTEGRATION.md](GIS_INTEGRATION.md). Restart FastAPI after changing environment variables or source files.
- **Geocoded locations:** treat returned coordinates as candidates until manually reviewed. Never mark a station verified solely because a geocoder returned a match.

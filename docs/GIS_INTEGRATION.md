# GIS module integration

The GIS module is part of the existing FastAPI backend under `backend/modules/gis`. It loads a CSV-backed station layer and exposes it to the frontend and candidate-analysis workflows.

## API endpoints

### `GET /api/gis/stations`

Returns coordinate-backed station records.

Example response shape:

```json
{
  "items": [
    {
      "station_id": "station-001",
      "station_name": "Example outlet",
      "latitude": 22.30,
      "longitude": 73.18,
      "has_cng": "true",
      "verified_gujarat_gas_station": false
    }
  ],
  "count": 1,
  "data_note": "1 mapped outlet/station record(s); 1 are not verified as currently operating Gujarat Gas CNG stations. Use as provisional candidates only."
}
```

The example is illustrative, not a real station record. The API preserves source CSV columns and adds normalized station fields where possible. Rows with missing, non-numeric or out-of-range coordinates are skipped. A missing CSV returns an empty list; the API does not fabricate coordinates.

### `GET /api/gis/stations/{station_id}/nearby?radii_km=5,10,20`

Finds nearby mapped stations and returns distance/radius diagnostics for the selected station. The radius list is comma-separated, must contain positive values no greater than 100 km, and defaults to `5,10,20`. An unknown station ID returns HTTP 404; invalid radii return HTTP 422.

### `GET /api/gis/candidate-analysis?latitude=22.3&longitude=73.1&radii_km=5,10,20`

Evaluates straight-line proximity from a proposed coordinate to the loaded station layer. Latitude and longitude are validated to legal coordinate ranges. This endpoint does not calculate road travel time, observed demand, validated catchments or causal cannibalization.

## Data file selection and CSV schema

By default the backend selects the first existing file in this order:

1. `member-3-forecasting/data/gujarat_gas_directory_344_geocoded.csv`
2. `member-3-forecasting/data/gujarat_gas_directory_344_records.csv`
3. `data/processed/stations.csv`

Set `CNG_STATIONS_CSV` to override the selected path. The file must be accessible to the backend process.

Preferred headers are `station_id,station_name,latitude,longitude`. The loader also recognizes common aliases such as `id`, `outlet_id`, `name`, `outlet_name`, `lat`, `lon`, `lng`, and `Latitude/Longitude`. It preserves other columns such as `district`, `source`, `source_url`, and verification fields. CNG flags are read from `has_cng`, `cng_available`, or `CNG`; when no such field exists, the current loader defaults the flag to true for coordinate-backed directory rows.

The 344-record source file is not committed in this repository. To use it, put the file at the documented path or set `CNG_STATIONS_CSV` to its local path. The map can only plot records with coordinates; it cannot infer missing coordinates from a station name.

## Frontend map behaviour

- The map calls `GET /api/gis/stations` from `http://localhost:8000` by default.
- It filters for a positive CNG flag and coordinates inside an approximate Gujarat display outline.
- Pins without valid coordinates and pins outside that outline are not drawn.
- Clustered pins are orange for provisional candidates and green for records marked as verified.
- The “Verified operator stations” filter uses `verified_gujarat_gas_station=true`.
- The “Risk stations only” filter expects a `utilization` or `util` field and treats values at or above 1 as risk; if those fields are absent, the filter will show no records.
- The outline is a coarse UI filter, not an authoritative Gujarat polygon; use a validated administrative boundary dataset for exact state-boundary work.

## Mount the router

Include the router in the existing FastAPI app; do not create a second app if one already exists:

```python
from backend.modules.gis.router import router as gis_router
app.include_router(gis_router)
```

Adjust the import path to match the app entry point.

## Provenance and limitations

The public outlet import helper writes `data/processed/stations.csv`, retains available source identifiers/URLs and marks records as not verified Gujarat Gas stations. A public CNG flag or CGD authorisation does not prove current operation, Gujarat Gas ownership/supply, capacity or observed demand.

Geocoding results are candidate matches. A geocoder may return a road, neighbourhood or locality instead of the exact pump, so review results manually before marking a station verified. Keep source URLs, retrieval dates and review status with the records.

Distances are Haversine straight-line distances, not road distance or drive time. The 5/10/20 km radii are diagnostics, not validated customer catchments. Proximity alone does not establish cannibalization or prove a candidate site is commercially suitable.

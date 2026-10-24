# GIS module integration

This branch adds a starter GIS module under `backend/modules/gis`.

## Endpoints
- `GET /api/gis/stations` loads `data/processed/stations.csv` or the path in `CNG_STATIONS_CSV`.
- `GET /api/gis/stations/{station_id}/nearby?radii_km=5,10,20` returns nearby stations and radius counts.

Expected CSV headers: `station_id,station_name,latitude,longitude`. Extra columns are preserved. Invalid coordinate rows are skipped. No records are fabricated when the CSV is absent.

## Mount the router
In the existing FastAPI app entrypoint, add:

```python
from backend.modules.gis.router import router as gis_router
app.include_router(gis_router)
```

Adjust the import to match the actual app module path. Do not create a second FastAPI application if one already exists.

## Limitations
Distances are Haversine straight-line distances, not road distance or drive time. The 5/10/20 km radii are diagnostics, not validated customer catchments. Proximity alone does not establish cannibalization. Candidate scoring and simulator integration still need to be connected to the team's agreed API contracts. Use sourced station records and record provenance; a missing CSV returns an empty list rather than demo data.

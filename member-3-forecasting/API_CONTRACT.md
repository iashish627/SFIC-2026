# API Contract

Base URL: http://localhost:8000

- GET /health: health status.
- GET /api/v1/forecast/stations: station list from CNG_STATIONS_CSV.
- GET /api/v1/forecast/data-quality: input row counts and historical-sales readiness.
- POST /api/v1/forecast/generate: historical or estimated forecast.
- POST /api/v1/forecast/scenario/demand-shock: baseline versus uplift.
- POST /api/v1/forecast/scenario/festival-surge: same scenario calculation for a chosen date window.

Example forecast request:

    {
      "station_ids": ["STATION_001"],
      "start_date": "2026-11-01",
      "days": 30,
      "mode": "estimated",
      "base_demand_kg": 1200
    }

Estimated mode requires an explicit assumed baseline. Historical mode requires CNG_SALES_CSV with genuine observations and at least seven usable daily values per station. Required sales columns: station_id,date,sales_kg. Required station columns: station_id,station_name.

Scenario request:

    {
      "station_ids": ["STATION_001"],
      "start_date": "2026-11-01",
      "end_date": "2026-11-03",
      "uplift_percentage": 25,
      "base_demand_kg": 1200
    }

Unknown station IDs return 404; invalid inputs return 422. Results are labelled historical forecasts, estimates, or hypothetical scenarios. Source pack data is not embedded in this code folder.
# Member 3 — CNG Forecasting API

Standalone FastAPI service for the CNG Network Intelligence hackathon. It is separate from the frontend and can be integrated through JSON endpoints.

## Data integrity
The public station directory is not historical sales. Historical mode is available only when a genuine daily sales CSV is configured. Estimated mode requires an explicit assumed baseline and returns `estimated_demand`; it is not a validated Gujarat Gas demand forecast. No synthetic accuracy claim is made.

## Setup
Requires Python 3.11+.

```bash
cd member-3-forecasting
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` to inspect and try the endpoints.

## Configure data
Copy `.env.example` to `.env` and set these environment variables in your shell or environment manager:

- `CNG_STATIONS_CSV`: CSV containing at least `station_id,station_name`.
- `CNG_SALES_CSV`: optional genuine daily sales CSV containing `station_id,date,sales_kg`.
- `CNG_CORS_ORIGINS`: comma-separated frontend origins.

Paths are configurable. There are no developer-specific absolute Windows paths in the code. Keep private company data and credentials out of Git.

## Endpoints
- `GET /health`
- `GET /api/v1/forecast/stations`
- `GET /api/v1/forecast/data-quality`
- `POST /api/v1/forecast/generate`
- `POST /api/v1/forecast/scenario/demand-shock`
- `POST /api/v1/forecast/scenario/festival-surge`

Example estimated forecast request:

```json
{
  "station_ids": ["STATION_001"],
  "start_date": "2026-11-01",
  "days": 30,
  "mode": "estimated",
  "base_demand_kg": 1200
}
```

`base_demand_kg` is a user-supplied hypothetical assumption, not observed sales. Historical mode requires at least seven usable daily values for each requested station. See `API_CONTRACT.md` for request and response details.

## Tests
Run `pytest -q` from this folder. These tests validate API health and request validation; also test with a local station CSV before connecting a frontend.
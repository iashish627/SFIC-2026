# CNG Network Intelligence

**SFIC 2026 · Problem Statement PS000002**  
**Industry partner:** Gujarat Gas Company Limited  
**Platform:** Web application · React/Vite frontend · FastAPI backend

> **Prototype and data disclaimer:** This is a student hackathon decision-support prototype, not an official Gujarat Gas system. The 344-record station directory is a directory/locator dataset; capacity estimates and daily sales are synthetic demo data, not Gujarat Gas operational data. Forecasts and scenario outputs based on synthetic data are illustrative and are not evidence of real-world forecast accuracy or commercial site viability.

## Live demo

- **Frontend:** https://cng-network-intelligence-b82a.onrender.com
- **Backend API:** https://cng-network-intelligence-api.onrender.com
- **Interactive API docs:** https://cng-network-intelligence-api.onrender.com/docs
- **Backend health:** https://cng-network-intelligence-api.onrender.com/health
- **Data health / provenance:** https://cng-network-intelligence-api.onrender.com/api/health/data

The backend has been redeployed from the `main` branch. Use the data-health endpoint to confirm the dataset currently loaded by the running service; a successful deployment alone does not prove that all 344 station records were loaded. If the API reports fewer records, treat that as a deployment/data-loading issue rather than assuming the full dataset is active.

## What the prototype supports

- **Station explorer and map:** Search and inspect station records with usable coordinates, district/locality information and provenance fields.
- **Network dashboard:** Summary metrics and a network-wide daily sales series labelled as synthetic where applicable.
- **Demand forecasting:** Baseline station/network forecasts using available demo history. Forecast accuracy has not been validated against real station sales.
- **Geospatial analysis:** Nearby-station lookup, straight-line distance checks, and candidate-location proximity diagnostics.
- **A/B/C decision simulator:** Compare three options against the same demand baseline:
  1. No change.
  2. Expand an existing station.
  3. Build a new station.
- **Demand-shock scenarios:** Explore hypothetical festival/holiday uplift with explicit assumptions.
- **Scenario reports:** Run scenarios, inspect saved runs and export scenario CSV reports where supported by the API.

Features and outputs depend on data availability. Candidate-site proximity is a screening signal, not proof of demand or commercial viability.

## Technology

- **Frontend:** React, TypeScript and Vite, alongside static HTML navigation pages used by the hackathon prototype.
- **Backend:** Python and FastAPI.
- **Mapping:** Leaflet-based map experience.
- **Data files:** CSV station directory and clearly labelled synthetic capacity/sales demo data.
- **Scenario persistence:** Local SQLite in the current demo. This is not a production persistence architecture.

## Repository structure

```text
SFIC-2026/
├── frontend/                              # Web UI, map and dashboard pages
├── backend/
│   ├── modules/                           # GIS, dashboard, forecasting, scenarios
│   ├── tests/                             # Backend tests
│   └── db/schema.sql                      # PostgreSQL/PostGIS schema starter
├── data/
│   ├── gujarat_gas_directory_344_geocoded.csv
│   └── synthetic_demo/
│       ├── station_capacity_344_synthetic.csv
│       └── station_daily_sales_344_synthetic.csv
├── docs/                                  # Architecture, GIS integration and runbooks
└── README.md
```

## Data inventory and provenance

| File | Purpose | Data status |
|---|---|---|
| `data/gujarat_gas_directory_344_geocoded.csv` | 344-record Gujarat Gas directory target list for locator/GIS integration | Directory records; some coordinates are approximate |
| `data/synthetic_demo/station_capacity_344_synthetic.csv` | Station-wise capacity estimates for demo integration | **Synthetic** |
| `data/synthetic_demo/station_daily_sales_344_synthetic.csv` | 90 days of station-wise daily sales demo history | **Synthetic** |

- The 344-record directory is the target station list for this workflow. Do not merge the separate 1,510-outlet flagged dataset into this station locator.
- 328 coordinates are district/locality-level approximations, not exact station pins. Verify locations before relying on them for site-level decisions.
- A station directory is not historical sales data.
- Do not present synthetic capacity or sales as observed company data.
- No station-level CNG prices are included without a reliable dated source.
- Preserve source URLs, retrieval dates, units, transformation notes and verification status when updating datasets.

## Key API endpoints

Base URL for the hosted API: `https://cng-network-intelligence-api.onrender.com`

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service health |
| GET | `/api/health/data` | Loaded-data health and provenance |
| GET | `/api/dashboard/summary` | Dashboard metrics and daily sales series |
| GET | `/api/gis/stations` | Station records with valid coordinates |
| GET | `/api/gis/stations/{station_id}/nearby` | Nearby records by straight-line distance |
| GET | `/api/gis/candidate-analysis?latitude=22.3&longitude=72.5&radii_km=5,10,20` | Candidate-site proximity diagnostics |
| GET | `/api/forecast/stations` | Stations available for forecasting |
| GET | `/api/forecast/station/{station_id}?days=14&model=seasonal_naive` | Station forecast |
| GET | `/api/forecast/weekly/{station_id}` | Weekly station forecast |
| GET | `/api/forecast/evaluate/{station_id}` | Forecast evaluation endpoint |
| GET | `/api/forecast/network` | Network-level forecast |
| GET | `/api/simulator/demo-inputs` | Demo inputs for the simulator |
| POST | `/api/simulator/run` | Run A/B/C simulator |
| POST | `/api/scenarios/run` | Run and save a scenario |
| GET | `/api/scenarios` | List saved scenarios |
| GET | `/api/scenarios/{scenario_id}` | Scenario details |
| GET | `/api/scenarios/{scenario_id}/report.csv` | Download scenario report |

For the complete request/response schemas, open the interactive [FastAPI documentation](https://cng-network-intelligence-api.onrender.com/docs).

## Run locally

From the repository root, install backend dependencies and start the API:

```bash
python -m pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

In a second terminal, serve the frontend pages:

```bash
python -m http.server 5173 --directory frontend
```

Open `http://localhost:5173/map.html`. The map uses `http://localhost:8000/api/gis/stations` by default. Keep the backend running. If using a different API host, configure `window.CNG_GIS_API_BASE` before the map script loads, where supported by the page.

To build the Vite/React frontend:

```bash
cd frontend
npm install
npm run build
```

## GIS behaviour and limitations

- The locator supports district/locality and free-text search where the relevant fields are available.
- The 5 km, 10 km and 20 km controls use straight-line distance, not road distance.
- Only records with parseable latitude/longitude are returned/plotted.
- Nearby markers may be clustered; popups show available station identifiers, district, coordinates and provenance/verification details.
- The Gujarat outline is an approximate display filter, not an authoritative administrative boundary; edge locations may be omitted.
- The number shown on the map represents mapped records, not necessarily the total number of operational CNG stations in Gujarat.
- Candidate analysis is proximity screening, not a validated commercial ranking.

## Forecasting and simulator assumptions

- Baseline forecasts are illustrative when generated from synthetic demo history.
- Forecast evaluation on synthetic data does not establish accuracy on real station sales.
- A demand-shock scenario is hypothetical. Make the assumed uplift, duration and any capacity constraints visible in the result.
- Compare no change, existing-station expansion and new-station construction using the same demand baseline.
- Estimate net incremental demand separately from demand diverted from nearby existing stations.
- Use time-based holdout evaluation and metrics such as MAE/WAPE once suitable real historical observations are available.

## Validation

From the repository root:

```bash
python -m pytest backend/tests -q
```

The frontend build can be checked with `npm run build` from `frontend/`. Do not describe CI as passing unless the latest workflow run is green.

## Production-readiness gaps

Before any operational use, the project still needs verified station coordinates and operator/status attributes, real authorised station-level sales/capacity data, forecast backtesting, validated business assumptions, managed persistent storage, authentication/authorization, audit logging, reviewed database migrations, and deployment/data-loading monitoring. `backend/db/schema.sql` is a PostgreSQL/PostGIS schema starter; it is not automatically applied. Saved scenarios currently use local SQLite demo persistence and may not survive service restarts or scale across instances.

## Team responsibilities

| Role | Responsibility |
|---|---|
| Team leader | Coordination, architecture, integration and end-to-end checks |
| Member 2 — Data research | Station data, source tracking, validation and data dictionary |
| Member 3 — Forecasting | Forecast baselines, validation and forecast outputs |
| Member 4 — GIS | Coordinates, proximity/coverage analysis and candidate locations |
| Member 5 — Simulation | A/B/C scenarios, demand shocks, capacity and cannibalization assumptions |
| Backend | FastAPI endpoints and Python module integration |
| Frontend | Dashboard, map, charts, simulator and API connection |

---

Built as a student hackathon prototype for SFIC 2026.
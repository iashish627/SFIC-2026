# CNG Network Intelligence

**SFIC 2026 | Problem Statement PS000002**  
**Industry partner:** Gujarat Gas Company Limited  
**Project type:** Web-based CNG network intelligence and decision-support platform

## Overview
CNG Network Intelligence is a proposed hackathon decision-support platform combining station data, demand forecasts, geospatial analysis, and what-if scenarios. It is a prototype, not an official Gujarat Gas system, and does not claim access to Gujarat Gas internal sales or operational data.

## Problem We Aim to Address
CNG demand can vary by location, time, nearby stations, travel patterns, and station capacity. The project aims to help explore station-level demand and compare network decisions using transparent assumptions.

## Planned Features
- **Station explorer and map:** View station locations and available attributes.
- **Demand forecasting:** Daily/weekly station-level estimates when suitable historical data is available.
- **Geospatial analysis:** Explore proximity, coverage, and candidate locations.
- **What-if simulator:** Compare against the same demand baseline:
  1. No change.
  2. Expand an existing station.
  3. Build a new station.
- **Cannibalization estimate:** Separate potential diverted sales from net incremental demand.
- **Demand-shock scenarios:** Explore hypothetical festival/holiday uplift with explicit assumptions.
- **Decision support:** Show assumptions, uncertainty, data provenance, and comparisons.

These are planned capabilities; not all are implemented yet.

## Technology Plan
- **Frontend:** React, TypeScript, Vite
- **Backend:** Python, FastAPI
- **Geospatial tools:** Leaflet / React Leaflet; additional GIS tools as needed
- **Data:** CSV for the initial prototype; database integration can be added later

This is the intended stack, not a claim that all components are already configured.

## Repository Structure
```text
SFIC-2026/
├── frontend/                 # Web interface
├── backend/
│   ├── modules/              # Forecasting, GIS, simulation modules
│   └── tests/                # Backend tests
├── data/
│   ├── raw/                  # Source data and source details
│   ├── processed/            # Cleaned and validated data
│   └── synthetic_demo/       # Clearly labelled synthetic data
├── docs/                     # Architecture, data dictionary, API contracts
├── tests/                    # Integration and end-to-end tests
├── README.md
└── .gitignore
```

## Team Responsibilities
| Role | Main responsibility |
|---|---|
| Team leader | Coordination, architecture, contracts, integration, end-to-end checks |
| Member 2 — Data research | Station dataset, source tracking, validation, data dictionary |
| Member 3 — Forecasting | Forecast baselines, validation, forecast outputs |
| Member 4 — GIS | Coordinates, proximity/coverage analysis, candidate locations |
| Member 5 — Simulation | A/B/C scenarios, demand shocks, capacity checks, cannibalization assumptions |
| Member 6 — Backend | FastAPI endpoints and Python module integration |
| Member 7 — Frontend | Dashboard, map, charts, simulator, API connection |

## Data Quality and Responsible Use
- Public station directories can seed a station master, but coordinates, operator, and operating status should be checked.
- A station directory is **not** historical sales data.
- Do not invent Gujarat Gas internal sales, capacity, supply allocation, outages, queues, or company targets.
- Distinguish observed, externally sourced, inferred, forecast, hypothetical, and synthetic values.
- Synthetic data demonstrates software behaviour only; it does not establish real forecast accuracy or prove a site is suitable.
- Retain source URLs, retrieval dates, units, and transformation notes.
- Never commit credentials, API keys, personal data, or confidential company data.

## Core Metric Definitions
- **Capacity utilisation** = forecast demand / effective capacity, with consistent units and periods.
- **Estimated net incremental demand** = estimated new-site sales − estimated demand diverted from existing stations.
- **Forecast evaluation** should use a time-based holdout and metrics such as MAE and WAPE when actual historical observations exist.
- Scenario A, B, and C should use the same baseline and disclose assumptions.

Metrics are only as reliable as their input data and assumptions.

## Station Locator and Network Map / GIS Feature

The Network Map is a Leaflet-based station-locator experience inspired by public CNG locator pages: district and locality filters, station search/cards, map selection, and proximity analysis.

- Locator filters support district, city/locality, and free-text station/address search. Station cards can focus the map on a selected result.
- The 5 km, 10 km, and 20 km radius controls support preliminary proximity screening. Distances are straight-line distances, not road distances.
- Only records with valid latitude/longitude inside the approximate Gujarat display outline are plotted; records without usable coordinates are not plotted.
- Groups nearby markers into clusters. Marker colours distinguish verified operator records from provisional candidates.
- Station popups show available station identifiers, district, coordinates, source and verification status.
- Optional filters include risk stations and verified operator stations. Risk filtering depends on utilization fields being present in the data.
- The map's Gujarat outline is an approximate display filter, not an authoritative administrative boundary. Some edge areas may be omitted; do not use it as a legal/state-border GIS layer.
- The number shown on the map is the number of mapped records, not the total number of stations in Gujarat or the total directory size.

### Run locally

From the repository root, install backend dependencies and start FastAPI:

```bash
python -m pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

In a second terminal, serve the static frontend:

```bash
python -m http.server 5173 --directory frontend
```

Open `http://localhost:5173/map.html`. The map requests `http://localhost:8000/api/gis/stations` by default. Keep the backend running. If using another API host, configure `window.CNG_GIS_API_BASE` before the map script loads.

### GIS data source priority

The GIS backend selects the first available default file in this order:
1. `member-3-forecasting/data/gujarat_gas_directory_344_geocoded.csv`
2. `member-3-forecasting/data/gujarat_gas_directory_344_records.csv`
3. `data/processed/stations.csv` (public outlet mapping; provisional)

Override this with the `CNG_STATIONS_CSV` environment variable. Only rows with parseable latitude and longitude are returned by `GET /api/gis/stations`; rows without coordinates are skipped. The 344-record source file must be placed at one of the first two paths above to make the locator use that directory instead of the broader public-outlet fallback. Coordinates inferred from district/locality are approximate and must not be presented as precise station locations. Sales and capacity estimates are synthetic demo values, not Gujarat Gas operational records. Geocoding output is a candidate match and must be manually reviewed before calling a location verified. See [GIS integration](docs/GIS_INTEGRATION.md) and the [GIS runbook](docs/GIS_RUNBOOK.md) for API details, data provenance, geocoding and troubleshooting.

## Project Status
**Stage:** Integrated hackathon prototype. The dashboard, GIS map, station explorer, proximity analysis, baseline forecast, A/B/C demand-shock simulator, data provenance view and API-backed CSV exports are wired to the FastAPI backend. GitHub Actions validates backend tests and the Vite frontend build. This is not an operational Gujarat Gas system: sales/capacity demos are synthetic, public GIS records may be provisional, candidate-site results are proximity diagnostics only, forecast accuracy has not been holdout-validated, and uploads do not yet persist data.

---
Built as a student hackathon prototype for SFIC 2026.


## Integrated API endpoints

- `GET /health` — backend health.
- `GET /api/dashboard/summary` — dashboard metrics and daily sales series with synthetic provenance.
- `GET /api/gis/stations` — configured coordinate-valid station/outlet records.
- `GET /api/gis/stations/{station_id}/nearby` — nearby records by straight-line distance.
- `GET /api/gis/candidate-analysis?latitude=22.3&longitude=72.5&radii_km=5,10,20` — proximity diagnostics, not demand-based site ranking.
- `GET /api/forecast/stations` and `GET /api/forecast/station/{station_id}?days=14&model=seasonal_naive` — synthetic-history forecast baselines.
- `GET /api/simulator/demo-inputs` and `POST /api/simulator/run` — A/B/C expansion and demand-shock simulation.

## Validation

From the repository root, install `backend/requirements.txt` and run:

```bash
python -m pytest backend/tests -q
```

For the static HTML prototype, serve the `frontend/` directory on port 5173 and run FastAPI on port 8000. The Vite/React source in `frontend/src/` is also built by CI; the current hackathon navigation pages are static HTML and call the same API directly.


## Production database schema starter

`backend/db/schema.sql` documents a PostgreSQL/PostGIS target schema for station master, sales, effective-dated capacity, supply constraints, source provenance, candidate sites, forecasts, model evaluations, scenario runs, station impacts, site rankings and audit logs. It is a migration starter only and is **not automatically applied** by the hackathon demo. The running demo stores saved scenarios in local SQLite; before production, replace that adapter with managed PostgreSQL, apply reviewed migrations, and add server-side authentication/authorization and audit enforcement.

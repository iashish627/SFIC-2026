# CNG Network Intelligence

**SFIC 2026 · Problem Statement PS000002**  
**Industry partner:** Gujarat Gas Company Limited  
**Product:** Station-level CNG demand intelligence and network expansion decision-support prototype

CNG Network Intelligence is designed to help a City Gas Distribution (CGD) operator understand station-level demand, identify potential network gaps, and compare expansion decisions before committing resources.

The core workflow is:

**Station data → Demand forecast → GIS/network analysis → What-if simulation → Expansion decision**

> **Prototype disclaimer:** This is a student hackathon prototype, not an official Gujarat Gas system or an operational planning tool. The station directory is a research/locator dataset, not a verified live register of operating stations. Capacity and daily-sales files in the demo are synthetic. Forecasts, scenario outputs, cost estimates and site-screening results must be treated as illustrative unless supported by verified operational and commercial data.

## Live application

- **Frontend:** https://cng-network-intelligence-b82a.onrender.com
- **Backend API:** https://cng-network-intelligence-api.onrender.com
- **API documentation:** https://cng-network-intelligence-api.onrender.com/docs
- **Service health:** https://cng-network-intelligence-api.onrender.com/health
- **Loaded data health and provenance:** https://cng-network-intelligence-api.onrender.com/api/health/data

A successful Render deployment confirms that a deployment is live; it does not by itself confirm that every expected station record is loaded. Check the data-health endpoint and the station API before reporting a live station count.

### Backend URL behavior

The backend is an API service. Opening the base URL (`/`) in a browser may return `{"detail":"Not Found"}` because no root page is defined. This is expected behavior and does **not** by itself mean the backend is offline.

Use these endpoints to verify the service:

Use the deployed application interface and internal service monitoring to verify availability. A deployment should be considered fully verified only after the application's core workflows respond successfully.

## Business problem and product approach

CNG network expansion decisions require more than a map of existing stations. A decision-maker needs to understand where demand may grow, whether existing infrastructure can serve it, and whether a new station would create genuinely incremental demand or mainly divert sales from nearby stations.

This prototype brings together the following decision stages:

1. **Understand the network:** Explore station records, district/locality information and available coordinates.
2. **Estimate demand:** Generate station-level and network-level baseline forecasts from the available demo history.
3. **Identify spatial gaps:** Examine nearby stations and candidate locations using distance/proximity diagnostics.
4. **Stress-test demand:** Apply hypothetical festival/holiday demand-shock assumptions.
5. **Compare investment choices:** Evaluate no change, expansion of an existing station, and construction of a new station against a shared baseline.
6. **Review outputs:** Inspect scenario results and export scenario reports where supported.

The intended business outcome is a more structured, evidence-led expansion assessment. The prototype does not claim to make a final investment decision or establish commercial viability.

## Main modules

### 1. Network dashboard
Provides a consolidated view of the station dataset and available demo sales information. Metrics must retain their data provenance labels; synthetic sales are not actual company throughput.

### 2. Station explorer and GIS map
Supports station discovery and map-based inspection using available station identifiers, district/locality fields and coordinates. Nearby-station and candidate-location analysis use straight-line distance diagnostics, not road travel time or a full traffic/catchment model.

### 3. Demand forecasting
Provides station and network forecast endpoints, including weekly views and forecast evaluation routes. The current demo uses baseline forecasting with synthetic historical sales. Evaluation on synthetic data is not evidence of accuracy on real CNG demand.

### 4. Demand-shock and expansion simulator
The simulator is intended to compare three alternatives using a common demand baseline:

- **Option A — No change:** Continue with the existing network.
- **Option B — Expand an existing station:** Test a capacity expansion at an existing location.
- **Option C — Build a new station:** Test a proposed additional location.

Demand-shock scenarios can represent hypothetical festival/holiday uplift. The business analysis should distinguish net new demand from demand diverted away from nearby existing stations (cannibalization), and should expose assumptions and capacity constraints rather than presenting estimates as observed facts.

### 5. EV transition scenarios

The project includes an **EV Transition Scenario Planner** for stress-testing long-term CNG demand and expansion decisions. It uses explicit, user-adjustable assumptions rather than claiming to predict EV adoption or station-level CNG displacement.

The external market context is sourced from the [IBEF Electric Vehicle Industry page](https://www.ibef.org/industry/electric-vehicle). IBEF reports FY26 EV sales of 2.66 million units, 8.62% penetration of total automotive sales, nearly 87% of EV volumes from two- and three-wheelers, and 29,151 public charging stations as of December 2025.

**Important:** These national market indicators justify considering EV transition risk, but they do **not** establish a fixed demand-loss percentage for an individual Gujarat CNG station. The planner therefore labels its displacement rates as hypothetical scenario assumptions.


### 6. Scenario history and reports
Scenario endpoints support running scenarios, listing saved runs, retrieving scenario details and exporting CSV reports where available. The current demo uses local SQLite persistence; it is not a managed, production-grade shared database.

### 7. Supporting CNG information pages
The frontend also includes supplementary CNG-oriented information pages (such as CNG benefits, gas-price information, cost calculation and car-care content). These are supporting user-facing utilities/information, not the core station-demand forecasting or network-expansion decision engine. Any price or cost figures should be shown with a source, date and clear assumptions.

## Technology stack

- **Frontend:** React, TypeScript and Vite, with static HTML pages used in parts of the prototype.
- **Backend:** Python and FastAPI.
- **Geospatial experience:** Leaflet-based map.
- **Data exchange:** CSV datasets and JSON REST APIs.
- **Demo persistence:** SQLite for scenario records.
- **Database direction:** PostgreSQL/PostGIS schema starter is present; do not assume it is provisioned or used by the hosted demo unless deployment configuration confirms it.

## Repository layout

```text
SFIC-2026/
├── frontend/                         # Web interface, map and supporting pages
├── backend/
│   ├── modules/                      # Dashboard, GIS, forecasting, simulator/scenarios
│   ├── tests/                        # Backend tests
│   └── db/schema.sql                 # PostgreSQL/PostGIS schema starter
├── data/
│   ├── gujarat_gas_directory_344_geocoded.csv
│   └── synthetic_demo/
│       ├── station_capacity_344_synthetic.csv
│       └── station_daily_sales_344_synthetic.csv
├── docs/                             # Project design and supporting documentation
└── README.md
```

## Data inventory and limitations

| Dataset | Intended use | Provenance / limitation |
|---|---|---|
| `data/gujarat_gas_directory_344_geocoded.csv` | Station directory and GIS locator input | 344 directory records; not proof that every entry is currently operational |
| `data/synthetic_demo/station_capacity_344_synthetic.csv` | Demo capacity inputs for simulation | Synthetic estimates; not verified station capacity |
| `data/synthetic_demo/station_daily_sales_344_synthetic.csv` | Demo station-level daily sales history | Synthetic history; not Gujarat Gas sales observations |

Additional data notes:

- The 344-record directory is the station-list target used by this workflow. Keep it distinct from the separate 1,510-outlet flagged dataset.
- 328 coordinates are district/locality-level approximations rather than verified station-gate coordinates. They must not be treated as precise pins for site acquisition or final catchment decisions.
- A station directory does not provide historical throughput, traffic volume, queue length, operating status or installed dispensing capacity.
- Synthetic sales/capacity values are demo fixtures only. Never describe them as company data.
- The historical CNG DODO reference supplied for research is dated 9 July 2019. Its locations, eligibility criteria, fees, margins and commercial terms are historical references, not current offers or rules. Verify current conditions with the relevant authorized entity.
- Preserve source URLs, retrieval dates, units, transformations, coordinate confidence and verification status when adding or replacing data.

## API reference

Hosted base URL: `https://cng-network-intelligence-api.onrender.com`

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Backend service health |
| GET | `/api/health/data` | Loaded data status, counts and provenance |
| GET | `/api/dashboard/summary` | Dashboard summary |
| GET | `/api/gis/stations` | Station records with usable coordinates |
| GET | `/api/gis/stations/{station_id}/nearby` | Nearby station lookup |
| GET | `/api/gis/candidate-analysis` | Candidate-location proximity diagnostics |
| GET | `/api/forecast/stations` | Stations available for forecasting |
| GET | `/api/forecast/station/{station_id}` | Station-level forecast |
| GET | `/api/forecast/weekly/{station_id}` | Weekly station forecast |
| GET | `/api/forecast/evaluate/{station_id}` | Forecast evaluation |
| GET | `/api/forecast/network` | Network-level forecast |
| GET | `/api/simulator/demo-inputs` | Simulator demo inputs |
| POST | `/api/simulator/run` | Run A/B/C simulator |
| POST | `/api/scenarios/run` | Run and save a scenario |
| GET | `/api/ev-scenarios/presets` | EV scenario presets and external market context |
| POST | `/api/ev-scenarios/run` | Run assumption-based EV transition scenario |
| GET | `/api/scenarios` | List saved scenarios |
| GET | `/api/scenarios/{scenario_id}` | Retrieve a scenario |
| GET | `/api/scenarios/{scenario_id}/report.csv` | Export scenario report |

For request parameters, schemas and response examples, use the [interactive API documentation](https://cng-network-intelligence-api.onrender.com/docs).

## Run locally

From the repository root, install backend dependencies and start the API:

```bash
python -m pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

In another terminal, serve the frontend:

```bash
python -m http.server 5173 --directory frontend
```

Open `http://localhost:5173/map.html` for the map page. The map uses the local API at `http://localhost:8000` by default where configured.

To install and build the Vite frontend:

```bash
cd frontend
npm install
npm run build
```

## Security and deployment notes

The hosted prototype applies basic API hardening appropriate to a public hackathon demo:

- CORS is restricted to the configured frontend origin instead of allowing every website.
- API responses include security headers such as `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` and `Permissions-Policy`.
- Requests declaring bodies larger than 1 MB are rejected by the application middleware.
- The repository ignores common private-key and local secret files.
- Demo scenario persistence uses local SQLite and contains no authentication or user accounts.

This is **not a production security certification**. Before operational use, add managed authentication and authorization, rate limiting at the edge/application layer, centralized secret management, managed persistent storage, dependency vulnerability scanning, audit logging and formal security testing.

## GIS and modelling assumptions

- Proximity controls use straight-line distance, not road-network distance or travel time.
- Only records with usable latitude/longitude can be plotted or included in coordinate-based analysis.
- Approximate coordinates and the approximate Gujarat outline can produce false precision or omit edge cases.
- Candidate analysis is a screening aid, not a validated commercial site ranking.
- Baseline forecasts built from synthetic sales are illustrative only.
- Forecast evaluation on synthetic history does not establish out-of-sample performance on real station demand.
- Demand-shock uplift, capacity, cost and cannibalization parameters are assumptions unless explicitly linked to verified sources.
- Compare all three investment options against the same forecast baseline and state the assumptions behind every result.

## Validation

Run backend tests from the repository root:

```bash
python -m pytest backend/tests -q
```

Build the frontend from `frontend/`:

```bash
npm install
npm run build
```

Report CI as passing only when the latest relevant GitHub Actions workflow is green. A local test run and a hosted deployment are separate checks.

## Known gaps before operational use

The prototype needs verified station coordinates and operating status, authorized station-level sales/throughput history, measured station capacity, traffic/vehicle-flow and queue data, forecast backtesting on real observations, validated cost and commercial assumptions, a defensible road-network/catchment model, managed persistent storage, authentication/authorization, audit logging, and deployment/data-quality monitoring.

The PostgreSQL/PostGIS schema is a starter unless it is explicitly provisioned and connected. SQLite demo scenario persistence may be ephemeral on hosted infrastructure. Do not use the prototype as the sole basis for a real station investment, dealership application or site acquisition decision.

## Team workstreams

- **Data research:** Station sources, extraction, data dictionary, provenance and quality checks.
- **Forecasting / ML:** Baselines, feature preparation, time-aware evaluation and forecast outputs.
- **GIS / geospatial:** Coordinate validation, proximity/catchment analysis and candidate locations.
- **Simulation:** Demand shocks, capacity assumptions, option comparison and cannibalization logic.
- **Backend:** FastAPI routes, data loading, module integration and persistence.
- **Frontend:** Dashboard, station map, forecast views, simulator and reports.

---

Built for SFIC 2026, Gujarat Gas Company Limited problem statement PS000002.
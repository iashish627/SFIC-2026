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

## Initial Setup Status
The repository contains an initial folder skeleton. The frontend, backend, forecasting, GIS, and simulation implementations still need to be added. Detailed run commands will be added after app scaffolding.

## Project Status
**Stage:** Initial repository and project structure  
**Next milestones:** Set up the React frontend, create the FastAPI backend skeleton, prepare a sourced station dataset, and define shared module input/output contracts.

---
Built as a student hackathon prototype for SFIC 2026.

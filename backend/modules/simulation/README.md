# Demand Shock & Expansion Simulator

Compares **A — No change**, **B — expand an existing station**, and **C — build a new station** against the same baseline.

## API
Run from repository root: `uvicorn backend.main:app --reload --port 8000`
- `GET /api/simulator/demo-inputs`: returns synthetic station baselines and method.
- `POST /api/simulator/run`: returns all three scenarios.
- `GET /docs`: interactive API documentation.

Example POST body:
```json
{
  "horizon_days": 30,
  "demand_uplift_pct": 25,
  "shock_days": [10, 11, 12],
  "expand_station_id": "SYN-GJ-001",
  "added_capacity_kg_day": 400,
  "expansion_cost": 5000000,
  "new_site_potential_kg_day": 900,
  "new_site_capacity_kg_day": 1000,
  "diversion_pct": 20,
  "new_site_cost": 12000000
}
```
An optional `stations` array allows the forecasting module to pass its station baselines (kg/day) and capacities (kg/day). Shock day indexes are 1-based within the horizon. All costs are user-entered assumptions.

## Demo baseline
For each station, the API averages up to the latest 28 valid rows (`quality_flag=ok`) from `data/synthetic_demo/daily_sales.csv`; capacity comes from `station_capacity.csv`. Missing sales are skipped, not converted to zero. This is a transparent baseline, **not an ML forecast**.

## Limitations
Data is synthetic and does not represent Gujarat Gas operations. New-site demand and diversion are assumptions, not GIS-derived estimates. Costs are not inferred and no payback/NPV is claimed. The current engine does not model supply allocation, queues, hourly throughput or optimized candidate-site ranking.

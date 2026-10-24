# Synthetic Demo Sales & Capacity Data

> **IMPORTANT:** Every record in this folder is synthetic and generated for prototyping. These are NOT Gujarat Gas internal records and do not establish actual station sales, station capacity, operating status, forecast accuracy, or site viability. Station names and coordinates are illustrative map seeds only and must be verified before geographic claims.

## Files
- `stations.csv`: 8-row station master; join on stable `station_id`.
- `daily_sales.csv`: 90 days of synthetic daily sales (2026-07-01 through 2026-09-28), up to 720 station-day rows.
- `station_capacity.csv`: synthetic effective capacity in kg/day and validity dates.
- `data_dictionary.csv`: field definitions and units.

## Data handling
- Blank `sales_kg` with `missing_demo_record` means missing data, not zero.
- Compare sales and capacity only when station/date validity and units match.
- An illustrative demand surge is included on 2026-08-15 through 2026-08-17; do not treat it as measured festival uplift.
- Every row has `provenance_type=synthetic` and `source=generated_for_demo`.

## Intended use
Prototype the forecasting, GIS, capacity-pressure and A/B/C scenario workflows. Do not use these data to claim real-world accuracy or make actual investment recommendations.

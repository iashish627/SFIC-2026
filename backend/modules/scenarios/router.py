"""Persisted scenario runs for reproducible A/B/C comparisons.

SQLite is used as a zero-setup local-demo store. Production deployment should
replace this adapter with the configured PostgreSQL/PostGIS persistence layer.
"""
import csv
from contextlib import closing
import io
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response
from backend.modules.simulation.engine import Station, run_simulation
from backend.modules.simulation.router import SimulationRequest, load_demo_stations

router = APIRouter(prefix="/api/scenarios", tags=["Saved Scenarios"])
ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "data" / "processed" / "scenario_runs.sqlite3"


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("""
        CREATE TABLE IF NOT EXISTS scenario_runs (
            scenario_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL,
            provenance TEXT NOT NULL,
            inputs_json TEXT NOT NULL,
            outputs_json TEXT NOT NULL,
            model_version TEXT NOT NULL
        )
    """)
    connection.execute("CREATE INDEX IF NOT EXISTS idx_scenario_runs_created_at ON scenario_runs(created_at DESC)")
    return connection


def _decode(row):
    return {
        "scenario_id": row["scenario_id"],
        "created_at": row["created_at"],
        "status": row["status"],
        "provenance": row["provenance"],
        "model_version": row["model_version"],
        "inputs": json.loads(row["inputs_json"]),
        "outputs": json.loads(row["outputs_json"]),
    }


@router.post("/run", status_code=201)
def run_and_save_scenario(request: SimulationRequest):
    try:
        if request.stations is not None:
            stations = [Station(s.station_id, s.baseline_kg_day, s.capacity_kg_day) for s in request.stations]
        else:
            stations = load_demo_stations()
        outputs = run_simulation(
            stations,
            horizon_days=request.horizon_days,
            demand_uplift_pct=request.demand_uplift_pct,
            shock_days=request.shock_days,
            expand_station_id=request.expand_station_id,
            added_capacity_kg_day=request.added_capacity_kg_day,
            expansion_cost=request.expansion_cost,
            new_site_potential_kg_day=request.new_site_potential_kg_day,
            new_site_capacity_kg_day=request.new_site_capacity_kg_day,
            diversion_pct=request.diversion_pct,
            new_site_cost=request.new_site_cost,
        )
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    scenario_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = request.model_dump(mode="json")
    outputs["scenario_id"] = scenario_id
    outputs["created_at"] = created_at
    outputs["model_version"] = "scenario-engine-v1"
    outputs["status"] = "completed"
    with closing(_connect()) as connection:
        connection.execute(
            "INSERT INTO scenario_runs (scenario_id, created_at, status, provenance, inputs_json, outputs_json, model_version) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (scenario_id, created_at, "completed", outputs.get("provenance", "unknown"),
             json.dumps(inputs, sort_keys=True), json.dumps(outputs, sort_keys=True), "scenario-engine-v1"),
        )
        connection.commit()
        connection.commit()
    return {"scenario_id": scenario_id, "created_at": created_at, "status": "completed",
            "model_version": "scenario-engine-v1", "inputs": inputs, **outputs}


@router.get("")
def list_saved_scenarios(limit: int = 20):
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    with closing(_connect()) as connection:
        rows = connection.execute(
            "SELECT scenario_id, created_at, status, provenance, model_version, inputs_json, outputs_json FROM scenario_runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return {"count": len(rows), "scenarios": [
        {"scenario_id": row["scenario_id"], "created_at": row["created_at"], "status": row["status"],
         "provenance": row["provenance"], "model_version": row["model_version"],
         "horizon_days": json.loads(row["inputs_json"]).get("horizon_days"),
         "scenario_count": len(json.loads(row["outputs_json"]).get("scenarios", []))}
        for row in rows
    ], "storage": "local_sqlite_demo", "warning": "Local demo persistence only; use managed PostgreSQL for production or multi-instance deployment."}


@router.get("/{scenario_id}/report.csv")
def export_scenario_report(scenario_id: str):
    with closing(_connect()) as connection:
        row = connection.execute("SELECT * FROM scenario_runs WHERE scenario_id = ?", (scenario_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Saved scenario not found")
    saved = _decode(row)
    output = saved["outputs"]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=[
        "section", "scenario_id", "created_at", "model_version", "provenance",
        "scenario", "horizon_days", "forecast_demand_kg", "served_demand_kg",
        "unmet_demand_kg", "capacity_kg_over_horizon", "capacity_utilisation_pct",
        "estimated_cost", "assumptions", "new_site_sales_kg",
        "estimated_diverted_demand_kg", "net_incremental_demand_kg", "warning"
    ])
    writer.writeheader()
    writer.writerow({"section": "metadata", "scenario_id": scenario_id, "created_at": saved["created_at"],
                     "model_version": saved["model_version"], "provenance": saved["provenance"],
                     "horizon_days": output.get("horizon_days"), "warning": "Synthetic or user-supplied assumptions; not operational Gujarat Gas data."})
    for scenario in output.get("scenarios", []):
        writer.writerow({"section": "scenario", "scenario_id": scenario_id, "created_at": saved["created_at"],
                         "model_version": saved["model_version"], "provenance": saved["provenance"], **scenario})
    writer.writerow({"section": "new_site_metrics", "scenario_id": scenario_id, "created_at": saved["created_at"],
                     "model_version": saved["model_version"], "provenance": saved["provenance"],
                     **output.get("new_site_metrics", {})})
    filename = f"cng_scenario_{scenario_id}.csv"
    return Response(content=buffer.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/{scenario_id}")
def get_saved_scenario(scenario_id: str):
    with closing(_connect()) as connection:
        row = connection.execute("SELECT * FROM scenario_runs WHERE scenario_id = ?", (scenario_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Saved scenario not found")
    return _decode(row)

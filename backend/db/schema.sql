-- PostgreSQL/PostGIS production schema starter for CNG Network Intelligence.
-- Not automatically applied by the demo application. Review with the data owner
-- and run through a migration process before production use.
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS data_sources (
    source_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    origin_url TEXT,
    provenance_class TEXT NOT NULL CHECK (provenance_class IN ('observed','synthetic','public_directory','forecast','hypothetical','unknown')),
    licence_access_notes TEXT,
    imported_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS stations (
    station_id TEXT PRIMARY KEY,
    station_name TEXT NOT NULL,
    district TEXT,
    operating_status TEXT NOT NULL DEFAULT 'unknown',
    commissioned_at DATE,
    closed_at DATE,
    geom geometry(Point, 4326),
    coordinate_source_id BIGINT REFERENCES data_sources(source_id),
    coordinate_verified BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (closed_at IS NULL OR commissioned_at IS NULL OR closed_at >= commissioned_at)
);
CREATE INDEX IF NOT EXISTS stations_geom_gix ON stations USING GIST (geom);
CREATE INDEX IF NOT EXISTS stations_district_idx ON stations (district);

CREATE TABLE IF NOT EXISTS station_sales (
    sales_id BIGSERIAL PRIMARY KEY,
    station_id TEXT NOT NULL REFERENCES stations(station_id),
    sales_date DATE NOT NULL,
    kg_sold NUMERIC(14,3),
    observation_status TEXT NOT NULL CHECK (observation_status IN ('observed','missing','invalid','estimated')),
    source_id BIGINT REFERENCES data_sources(source_id),
    quality_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (station_id, sales_date, source_id),
    CHECK (kg_sold IS NULL OR kg_sold >= 0),
    CHECK (observation_status <> 'observed' OR kg_sold IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS station_sales_date_idx ON station_sales (sales_date);
CREATE INDEX IF NOT EXISTS station_sales_station_date_idx ON station_sales (station_id, sales_date DESC);

CREATE TABLE IF NOT EXISTS station_capacity (
    capacity_id BIGSERIAL PRIMARY KEY,
    station_id TEXT NOT NULL REFERENCES stations(station_id),
    effective_from DATE NOT NULL,
    effective_to DATE,
    practical_kg_per_day NUMERIC(14,3),
    availability_factor NUMERIC(6,5) NOT NULL DEFAULT 1.0,
    source_id BIGINT REFERENCES data_sources(source_id),
    CHECK (practical_kg_per_day IS NULL OR practical_kg_per_day >= 0),
    CHECK (availability_factor >= 0 AND availability_factor <= 1),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);
CREATE INDEX IF NOT EXISTS station_capacity_station_period_idx ON station_capacity (station_id, effective_from, effective_to);

CREATE TABLE IF NOT EXISTS supply_constraints (
    constraint_id BIGSERIAL PRIMARY KEY,
    station_id TEXT REFERENCES stations(station_id),
    scope TEXT NOT NULL CHECK (scope IN ('station','district','network')),
    effective_from TIMESTAMPTZ NOT NULL,
    effective_to TIMESTAMPTZ,
    available_kg_per_day NUMERIC(14,3),
    constraint_type TEXT NOT NULL,
    source_id BIGINT REFERENCES data_sources(source_id),
    assumptions JSONB NOT NULL DEFAULT '{}'::jsonb,
    CHECK (available_kg_per_day IS NULL OR available_kg_per_day >= 0)
);

CREATE TABLE IF NOT EXISTS vehicle_registrations (
    registration_id BIGSERIAL PRIMARY KEY,
    geography TEXT NOT NULL,
    period_start DATE NOT NULL,
    vehicle_category TEXT NOT NULL,
    count BIGINT CHECK (count >= 0),
    source_id BIGINT REFERENCES data_sources(source_id),
    UNIQUE (geography, period_start, vehicle_category, source_id)
);

CREATE TABLE IF NOT EXISTS calendar_events (
    event_id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    area TEXT,
    event_type TEXT NOT NULL,
    provenance_class TEXT NOT NULL CHECK (provenance_class IN ('observed','assumption','synthetic')),
    uplift_pct NUMERIC(7,3),
    source_id BIGINT REFERENCES data_sources(source_id),
    CHECK (end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS candidate_sites (
    candidate_id TEXT PRIMARY KEY,
    candidate_name TEXT,
    geom geometry(Point, 4326) NOT NULL,
    status TEXT NOT NULL DEFAULT 'proposed',
    feasibility_status TEXT NOT NULL DEFAULT 'unknown',
    access_notes TEXT,
    source_id BIGINT REFERENCES data_sources(source_id),
    input_assumptions JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS candidate_sites_geom_gix ON candidate_sites USING GIST (geom);

CREATE TABLE IF NOT EXISTS model_versions (
    model_version_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    model_type TEXT NOT NULL,
    features JSONB NOT NULL DEFAULT '[]'::jsonb,
    training_cutoff DATE,
    evaluation_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    artifact_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS forecasts (
    forecast_id BIGSERIAL PRIMARY KEY,
    station_id TEXT NOT NULL REFERENCES stations(station_id),
    origin_date DATE NOT NULL,
    target_date DATE NOT NULL,
    horizon_days INTEGER NOT NULL CHECK (horizon_days >= 1),
    yhat_kg NUMERIC(14,3) NOT NULL CHECK (yhat_kg >= 0),
    lower_kg NUMERIC(14,3),
    upper_kg NUMERIC(14,3),
    model_version_id BIGINT REFERENCES model_versions(model_version_id),
    source_id BIGINT REFERENCES data_sources(source_id),
    provenance_class TEXT NOT NULL CHECK (provenance_class IN ('forecast','synthetic','hypothetical')),
    CHECK (lower_kg IS NULL OR lower_kg >= 0),
    CHECK (upper_kg IS NULL OR upper_kg >= yhat_kg),
    CHECK (lower_kg IS NULL OR lower_kg <= yhat_kg)
);
CREATE INDEX IF NOT EXISTS forecasts_station_target_idx ON forecasts (station_id, target_date);

CREATE TABLE IF NOT EXISTS model_evaluations (
    evaluation_id BIGSERIAL PRIMARY KEY,
    model_version_id BIGINT REFERENCES model_versions(model_version_id),
    station_id TEXT REFERENCES stations(station_id),
    split_type TEXT NOT NULL,
    train_end DATE,
    test_start DATE NOT NULL,
    test_end DATE NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC(18,6),
    cohort TEXT,
    provenance_class TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (test_end >= test_start)
);

CREATE TABLE IF NOT EXISTS scenario_runs (
    scenario_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by TEXT,
    status TEXT NOT NULL CHECK (status IN ('running','completed','failed')),
    provenance_class TEXT NOT NULL,
    inputs_json JSONB NOT NULL,
    outputs_json JSONB,
    baseline_ref TEXT,
    model_version_id BIGINT REFERENCES model_versions(model_version_id),
    data_cutoff DATE,
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS scenario_runs_created_at_idx ON scenario_runs (created_at DESC);

CREATE TABLE IF NOT EXISTS scenario_station_impacts (
    impact_id BIGSERIAL PRIMARY KEY,
    scenario_id UUID NOT NULL REFERENCES scenario_runs(scenario_id) ON DELETE CASCADE,
    station_id TEXT REFERENCES stations(station_id),
    scenario_option TEXT NOT NULL CHECK (scenario_option IN ('A_NO_CHANGE','B_EXPAND_EXISTING','C_BUILD_NEW')),
    baseline_demand_kg NUMERIC(14,3),
    scenario_demand_kg NUMERIC(14,3),
    served_demand_kg NUMERIC(14,3),
    unmet_demand_kg NUMERIC(14,3),
    capacity_pressure_pct NUMERIC(10,3),
    impact_type TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS site_rankings (
    ranking_id BIGSERIAL PRIMARY KEY,
    candidate_id TEXT NOT NULL REFERENCES candidate_sites(candidate_id),
    run_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    score NUMERIC(7,3),
    criteria JSONB NOT NULL DEFAULT '{}'::jsonb,
    weights JSONB NOT NULL DEFAULT '{}'::jsonb,
    missing_evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    limitations TEXT,
    provenance_class TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id BIGSERIAL PRIMARY KEY,
    user_id TEXT,
    action TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id TEXT,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS audit_logs_occurred_at_idx ON audit_logs (occurred_at DESC);

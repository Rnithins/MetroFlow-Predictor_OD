-- ==============================================================================
-- MetroFlowNet Production Database Schema (PostgreSQL)
-- Architectural Data Hierarchy:
-- Country -> State -> District -> City -> Metro System -> Line -> Station -> Station Connection -> OD Flow
-- Strict Provenance: REALTIME | HISTORICAL | SIMULATED | PREDICTED
-- Strict Operational Statuses: OPERATIONAL | UNDER_CONSTRUCTION | PROPOSED | TEMPORARILY_UNAVAILABLE | UNKNOWN
-- ==============================================================================

-- 1. ENUM TYPES
DO $$ BEGIN
    CREATE TYPE operational_status AS ENUM (
        'OPERATIONAL',
        'UNDER_CONSTRUCTION',
        'PROPOSED',
        'TEMPORARILY_UNAVAILABLE',
        'UNKNOWN'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE data_provenance AS ENUM (
        'REALTIME',
        'HISTORICAL',
        'SIMULATED',
        'PREDICTED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE aggregation_interval AS ENUM (
        '5m',
        '10m',
        '15m',
        '30m',
        '60m'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE user_role AS ENUM (
        'admin',
        'metro_authority',
        'planner',
        'analyst',
        'researcher',
        'public_user'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. GEOGRAPHICAL HIERARCHY
CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    iso_code VARCHAR(3) UNIQUE NOT NULL, -- e.g. 'IND'
    name VARCHAR(100) NOT NULL,
    currency_code VARCHAR(10) DEFAULT 'INR',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS states (
    id SERIAL PRIMARY KEY,
    country_id INT NOT NULL REFERENCES countries(id) ON DELETE RESTRICT,
    state_code VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_state_code_country UNIQUE(state_code, country_id)
);

CREATE TABLE IF NOT EXISTS districts (
    id SERIAL PRIMARY KEY,
    state_id INT NOT NULL REFERENCES states(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    census_code VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_district_state UNIQUE(name, state_id)
);

CREATE TABLE IF NOT EXISTS cities (
    id SERIAL PRIMARY KEY,
    state_id INT NOT NULL REFERENCES states(id) ON DELETE CASCADE,
    district_id INT REFERENCES districts(id) ON DELETE SET NULL,
    city_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. TRANSIT SYSTEM & PHYSICAL INFRASTRUCTURE
CREATE TABLE IF NOT EXISTS metro_systems (
    id SERIAL PRIMARY KEY,
    city_id INT NOT NULL REFERENCES cities(id) ON DELETE RESTRICT,
    code VARCHAR(30) UNIQUE NOT NULL, -- e.g. 'DMRC', 'BMRCL', 'MMRC', 'MEGA'
    name VARCHAR(120) NOT NULL,       -- e.g. 'Delhi Metro', 'Namma Metro Bengaluru'
    authority_name VARCHAR(150),
    status operational_status NOT NULL DEFAULT 'OPERATIONAL',
    gtfs_feed_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metro_lines (
    id SERIAL PRIMARY KEY,
    metro_system_id INT NOT NULL REFERENCES metro_systems(id) ON DELETE CASCADE,
    line_code VARCHAR(30) UNIQUE NOT NULL,
    line_name VARCHAR(100) NOT NULL,
    color_hex VARCHAR(10),
    status operational_status NOT NULL DEFAULT 'OPERATIONAL',
    total_stations INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stations (
    id SERIAL PRIMARY KEY,
    metro_system_id INT NOT NULL REFERENCES metro_systems(id) ON DELETE CASCADE,
    line_id INT NOT NULL REFERENCES metro_lines(id) ON DELETE CASCADE,
    station_code VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    zone VARCHAR(50),
    is_interchange BOOLEAN DEFAULT FALSE,
    baseline_capacity INT NOT NULL DEFAULT 2000,
    status operational_status NOT NULL DEFAULT 'OPERATIONAL',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Physical Directed Network Graph Edges (Corridors between adjacent stations)
CREATE TABLE IF NOT EXISTS station_connections (
    id SERIAL PRIMARY KEY,
    from_station_id INT NOT NULL REFERENCES stations(id) ON DELETE CASCADE,
    to_station_id INT NOT NULL REFERENCES stations(id) ON DELETE CASCADE,
    line_id INT NOT NULL REFERENCES metro_lines(id) ON DELETE CASCADE,
    distance_meters INT NOT NULL,
    scheduled_travel_seconds INT NOT NULL,
    is_bidirectional BOOLEAN DEFAULT TRUE,
    status operational_status NOT NULL DEFAULT 'OPERATIONAL',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_station_connection UNIQUE(from_station_id, to_station_id, line_id)
);

-- 4. SMART CARD TRANSACTIONS (ANONYMIZED, ZERO PII)
CREATE TABLE IF NOT EXISTS smart_cards (
    id SERIAL PRIMARY KEY,
    card_id_hash VARCHAR(64) UNIQUE NOT NULL, -- SHA-256 pseudonymized hash. NEVER store raw card/user IDs
    card_type VARCHAR(30) DEFAULT 'Standard Commuter',
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS smart_card_trips (
    id BIGSERIAL PRIMARY KEY,
    smart_card_id INT REFERENCES smart_cards(id) ON DELETE SET NULL,
    origin_station_id INT NOT NULL REFERENCES stations(id),
    destination_station_id INT REFERENCES stations(id),
    tap_in_time TIMESTAMP WITH TIME ZONE NOT NULL,
    tap_out_time TIMESTAMP WITH TIME ZONE,
    travel_minutes DOUBLE PRECISION,
    fare_charged DOUBLE PRECISION,
    data_source data_provenance NOT NULL DEFAULT 'HISTORICAL',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. ORIGIN-DESTINATION (OD) AGGREGATED FLOW MATRICES
CREATE TABLE IF NOT EXISTS od_matrices (
    id BIGSERIAL PRIMARY KEY,
    metro_system_id INT NOT NULL REFERENCES metro_systems(id) ON DELETE CASCADE,
    origin_station_code VARCHAR(30) NOT NULL,
    destination_station_code VARCHAR(30) NOT NULL,
    time_bucket TIMESTAMP WITH TIME ZONE NOT NULL,
    time_interval aggregation_interval NOT NULL DEFAULT '15m',
    passenger_count INT NOT NULL DEFAULT 0,
    avg_dwell_minutes DOUBLE PRECISION DEFAULT 2.5,
    data_source data_provenance NOT NULL DEFAULT 'HISTORICAL',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_od_bucket UNIQUE(metro_system_id, origin_station_code, destination_station_code, time_bucket, time_interval, data_source)
);

-- 6. FEATURE STORES & MODEL REGISTRIES
CREATE TABLE IF NOT EXISTS features (
    id BIGSERIAL PRIMARY KEY,
    metro_system_id INT NOT NULL REFERENCES metro_systems(id) ON DELETE CASCADE,
    station_code VARCHAR(30) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    -- Temporal Representation features
    hour_of_day INT NOT NULL,
    day_of_week INT NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_peak_hour BOOLEAN NOT NULL,
    is_holiday BOOLEAN NOT NULL,
    lag_15m_count INT DEFAULT 0,
    lag_1h_count INT DEFAULT 0,
    lag_24h_count INT DEFAULT 0,
    -- Spatial / Network Graph features
    station_degree INT DEFAULT 2,
    is_interchange BOOLEAN DEFAULT FALSE,
    line_count INT DEFAULT 1,
    -- Contextual features
    temperature_celsius DOUBLE PRECISION,
    rainfall_mm DOUBLE PRECISION,
    weather_condition VARCHAR(50),
    event_multiplier DOUBLE PRECISION DEFAULT 1.0,
    data_source data_provenance NOT NULL DEFAULT 'HISTORICAL',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ml_models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- 'AFFN', 'HISTORICAL_AVG', 'LINEAR_REGRESSION', 'RANDOM_FOREST', 'LSTM', 'ST_GNN'
    version VARCHAR(50) UNIQUE NOT NULL,
    checkpoint_path VARCHAR(255),
    is_active BOOLEAN DEFAULT FALSE,
    mae DOUBLE PRECISION,
    rmse DOUBLE PRECISION,
    wape DOUBLE PRECISION,
    r2_score DOUBLE PRECISION,
    evaluation_dataset_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. PREDICTIONS (EXPLICITLY TAGGED FORECASTS)
CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL PRIMARY KEY,
    metro_system_id INT NOT NULL REFERENCES metro_systems(id) ON DELETE CASCADE,
    origin_station_code VARCHAR(30) NOT NULL,
    destination_station_code VARCHAR(30) NOT NULL,
    prediction_generated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    target_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    forecast_window VARCHAR(10) NOT NULL DEFAULT '15m',
    current_passengers INT NOT NULL,
    predicted_passenger_count INT NOT NULL,
    confidence_interval_lower INT,
    confidence_interval_upper INT,
    confidence_score DOUBLE PRECISION NOT NULL,
    congestion_level VARCHAR(20) NOT NULL,
    st_attention_weight DOUBLE PRECISION,
    ext_attention_weight DOUBLE PRECISION,
    model_id INT REFERENCES ml_models(id),
    model_version VARCHAR(50) NOT NULL,
    data_source data_provenance NOT NULL DEFAULT 'PREDICTED',
    is_forecast_disclaimer_acknowledged BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. CORRIDOR SEGMENT LOADS & ROUTING
CREATE TABLE IF NOT EXISTS route_segment_loads (
    id BIGSERIAL PRIMARY KEY,
    metro_system_id INT NOT NULL REFERENCES metro_systems(id) ON DELETE CASCADE,
    from_station_code VARCHAR(30) NOT NULL,
    to_station_code VARCHAR(30) NOT NULL,
    time_bucket TIMESTAMP WITH TIME ZONE NOT NULL,
    cumulative_passenger_flow INT NOT NULL DEFAULT 0,
    capacity_threshold INT NOT NULL DEFAULT 1500,
    utilization_percentage DOUBLE PRECISION,
    congestion_state VARCHAR(20) NOT NULL DEFAULT 'Low',
    data_source data_provenance NOT NULL DEFAULT 'PREDICTED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. SERVICE ALERTS, WEATHER & EVENTS
CREATE TABLE IF NOT EXISTS service_alerts (
    id SERIAL PRIMARY KEY,
    metro_system_id INT NOT NULL REFERENCES metro_systems(id) ON DELETE CASCADE,
    line_id INT REFERENCES metro_lines(id) ON DELETE SET NULL,
    station_id INT REFERENCES stations(id) ON DELETE SET NULL,
    alert_type VARCHAR(50) NOT NULL, -- 'HIGH_OD_DEMAND', 'HIGH_SEGMENT_LOAD', 'SERVICE_DISRUPTION', 'FEED_FAILURE'
    severity VARCHAR(20) NOT NULL DEFAULT 'INFO', -- 'INFO', 'WARNING', 'CRITICAL'
    title VARCHAR(200) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weather_records (
    id BIGSERIAL PRIMARY KEY,
    city_id INT NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    temperature_celsius DOUBLE PRECISION NOT NULL,
    rainfall_mm DOUBLE PRECISION DEFAULT 0.0,
    humidity_pct DOUBLE PRECISION,
    weather_condition VARCHAR(100),
    data_source data_provenance NOT NULL DEFAULT 'REALTIME',
    raw_provider VARCHAR(50) DEFAULT 'OpenWeatherMap',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS external_events (
    id SERIAL PRIMARY KEY,
    city_id INT NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
    event_name VARCHAR(150) NOT NULL,
    event_type VARCHAR(50), -- 'FESTIVAL', 'CRICKET_MATCH', 'CONCERT', 'PUBLIC_RALLY'
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    demand_multiplier DOUBLE PRECISION DEFAULT 1.25,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. AUTHENTICATION, RBAC & AUDITING
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(120),
    role user_role NOT NULL DEFAULT 'analyst',
    organization VARCHAR(150),
    job_title VARCHAR(100),
    commute_line VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    endpoint VARCHAR(200) NOT NULL,
    ip_address VARCHAR(50),
    payload JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_quality_logs (
    id BIGSERIAL PRIMARY KEY,
    metro_system_id INT REFERENCES metro_systems(id) ON DELETE CASCADE,
    pipeline_name VARCHAR(100) NOT NULL,
    records_processed INT NOT NULL,
    invalid_records INT NOT NULL DEFAULT 0,
    duplicate_records INT NOT NULL DEFAULT 0,
    imputed_records INT NOT NULL DEFAULT 0,
    quality_score DOUBLE PRECISION NOT NULL, -- 0.00 to 1.00
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- INDEXING FOR HIGH-THROUGHPUT ANALYTICS & OD LOOKUPS
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_stations_code ON stations(station_code);
CREATE INDEX IF NOT EXISTS idx_stations_system ON stations(metro_system_id);
CREATE INDEX IF NOT EXISTS idx_lines_system ON metro_lines(metro_system_id);
CREATE INDEX IF NOT EXISTS idx_connections_from_to ON station_connections(from_station_id, to_station_id);

CREATE INDEX IF NOT EXISTS idx_trips_tap_in ON smart_card_trips(tap_in_time);
CREATE INDEX IF NOT EXISTS idx_trips_orig_dest ON smart_card_trips(origin_station_id, destination_station_id);

CREATE INDEX IF NOT EXISTS idx_od_matrices_time_bucket ON od_matrices(time_bucket);
CREATE INDEX IF NOT EXISTS idx_od_matrices_pair ON od_matrices(origin_station_code, destination_station_code);
CREATE INDEX IF NOT EXISTS idx_od_matrices_interval ON od_matrices(time_interval);

CREATE INDEX IF NOT EXISTS idx_predictions_target_time ON predictions(target_timestamp);
CREATE INDEX IF NOT EXISTS idx_predictions_pair ON predictions(origin_station_code, destination_station_code);

CREATE INDEX IF NOT EXISTS idx_features_station_time ON features(station_code, timestamp);
CREATE INDEX IF NOT EXISTS idx_segment_loads_bucket ON route_segment_loads(time_bucket);
CREATE INDEX IF NOT EXISTS idx_weather_city_time ON weather_records(city_id, timestamp);

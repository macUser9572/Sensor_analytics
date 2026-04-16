-- ============================================================
-- Sensor Analytics – Database Schema (TimescaleDB)
-- Runs automatically on first container startup via
-- docker-entrypoint-initdb.d
-- ============================================================

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ────────────────────────────────────────────────────────────
-- 1. sensors – Master registry of all plant sensors
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sensors (
    id              VARCHAR(64)     PRIMARY KEY,
    name            VARCHAR(255)    NOT NULL,
    subsystem       VARCHAR(128)    NOT NULL,
    unit            VARCHAR(32)     NOT NULL,
    min_threshold   FLOAT8          NOT NULL,
    max_threshold   FLOAT8          NOT NULL,
    baseline_value  FLOAT8          NOT NULL
);

COMMENT ON TABLE sensors IS 'Master registry of all 500 power plant sensors';

-- ────────────────────────────────────────────────────────────
-- 2. readings – High-frequency time-series sensor data
--    Converted to a TimescaleDB hypertable for fast range
--    queries and automatic chunk management.
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS readings (
    time        TIMESTAMPTZ     NOT NULL,
    sensor_id   VARCHAR(64)     NOT NULL REFERENCES sensors(id),
    value       FLOAT8          NOT NULL
);

-- Convert to hypertable partitioned on the 'time' column
SELECT create_hypertable('readings', 'time', if_not_exists => TRUE);

-- Index for fast lookups by sensor within a time range
CREATE INDEX IF NOT EXISTS idx_readings_sensor_time
    ON readings (sensor_id, time DESC);

-- ────────────────────────────────────────────────────────────
-- 3. readings_1min – Continuous aggregate (1-minute rollups)
--    Automatically maintained by TimescaleDB as new data
--    arrives into the readings hypertable.
-- ────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS readings_1min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    sensor_id,
    AVG(value)   AS avg_value,
    MIN(value)   AS min_value,
    MAX(value)   AS max_value,
    COUNT(*)     AS sample_count
FROM readings
GROUP BY bucket, sensor_id
WITH NO DATA;

-- Refresh policy: keep the 1-min aggregate up to date
-- (refresh data older than 2 minutes, look back up to 1 hour)
SELECT add_continuous_aggregate_policy('readings_1min',
    start_offset  => INTERVAL '1 hour',
    end_offset    => INTERVAL '2 minutes',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE
);

-- ────────────────────────────────────────────────────────────
-- 4. alerts – Threshold breach alerts
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    sensor_id       VARCHAR(64)     NOT NULL REFERENCES sensors(id),
    value           FLOAT8          NOT NULL,
    threshold       FLOAT8          NOT NULL,
    severity        VARCHAR(16)     NOT NULL CHECK (severity IN ('warning', 'critical')),
    fired_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    acknowledged    BOOLEAN         NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_alerts_sensor
    ON alerts (sensor_id, fired_at DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_unacknowledged
    ON alerts (acknowledged, fired_at DESC)
    WHERE acknowledged = FALSE;

COMMENT ON TABLE alerts IS 'Threshold breach alerts with severity and ack tracking';

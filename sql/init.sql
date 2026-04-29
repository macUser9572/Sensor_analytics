CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Sensor metadata (500 sensors)
CREATE TABLE IF NOT EXISTS sensors (
  id             VARCHAR(10) PRIMARY KEY,
  name           TEXT NOT NULL,
  subsystem      VARCHAR(20) NOT NULL,
  unit           VARCHAR(10) NOT NULL,
  baseline_value FLOAT8 NOT NULL,
  min_threshold  FLOAT8 NOT NULL,
  max_threshold  FLOAT8 NOT NULL,
  noise_amplitude FLOAT8 NOT NULL DEFAULT 0.5,
  sampling_interval_ms INTEGER NOT NULL DEFAULT 10000
);

-- Time-series readings (hypertable)
CREATE TABLE IF NOT EXISTS readings (
  time       TIMESTAMPTZ NOT NULL,
  sensor_id  VARCHAR(10) NOT NULL REFERENCES sensors(id),
  value      FLOAT8 NOT NULL
);
SELECT create_hypertable('readings','time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_readings_sensor_time ON readings(sensor_id, time DESC);

-- 1-minute continuous aggregate
CREATE MATERIALIZED VIEW IF NOT EXISTS readings_1min
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 minute', time) AS bucket,
  sensor_id,
  avg(value)    AS mean,
  min(value)    AS min_val,
  max(value)    AS max_val,
  stddev(value) AS std_dev,
  count(*)      AS sample_count
FROM readings
GROUP BY bucket, sensor_id
WITH NO DATA;

-- Alerts table (6 alert types)
CREATE TABLE IF NOT EXISTS alerts (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sensor_id   VARCHAR(10) REFERENCES sensors(id),
  value       FLOAT8,
  threshold   FLOAT8,
  severity    VARCHAR(20) NOT NULL,
  alert_type  VARCHAR(30) NOT NULL,
  -- alert_type values:
  -- 'warning_threshold' | 'critical_threshold'
  -- 'sensor_fault' | 'sensor_uncertain'
  -- 'sensor_missing' | 'sensor_recovered'
  message     TEXT,
  fired_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at TIMESTAMPTZ,
  acknowledged BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_alerts_sensor ON alerts(sensor_id, fired_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_unacked ON alerts(acknowledged) WHERE acknowledged = FALSE;

-- Sensor health tracking (for watchdog)
CREATE TABLE IF NOT EXISTS sensor_health (
  sensor_id    VARCHAR(10) PRIMARY KEY REFERENCES sensors(id),
  last_seen    TIMESTAMPTZ,
  status       VARCHAR(20) NOT NULL DEFAULT 'unknown',
  -- status values: 'live' | 'stale' | 'fault' | 'missing' | 'uncertain' | 'unknown'
  quality_code VARCHAR(50),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

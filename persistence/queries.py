import json
import logging
from contextlib import asynccontextmanager
from datetime import timezone
from typing import Any

import redis.asyncio as redis

from config import settings
from database import engine
from simulator.registry import generate_sensor_registry


logger = logging.getLogger(__name__)
SENSOR_IDS = [sensor.id for sensor in generate_sensor_registry()]


async def get_sensor_history(sensor_id: str, minutes: int = 60) -> list[dict]:
    async with _asyncpg_connection() as conn:
        if minutes <= 60:
            rows = await conn.fetch(
                """
                SELECT
                    time_bucket('15 seconds', time) AS time,
                    avg(value) AS value,
                    min(value) AS min_val,
                    max(value) AS max_val
                FROM readings
                WHERE sensor_id = $1
                  AND time > NOW() - ($2 * INTERVAL '1 minute')
                GROUP BY time_bucket('15 seconds', time)
                ORDER BY time ASC
                """,
                sensor_id,
                minutes,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT bucket AS time, mean AS value, min_val, max_val
                FROM readings_1min
                WHERE sensor_id = $1
                  AND bucket > NOW() - ($2 * INTERVAL '1 minute')
                ORDER BY bucket ASC
                """,
                sensor_id,
                minutes,
            )

        return [
            {
                "time": _iso(row["time"]),
                "value": float(row["value"]) if row["value"] is not None else None,
                "min_val": _float_or_none(row["min_val"]),
                "max_val": _float_or_none(row["max_val"]),
            }
            for row in rows
        ]


async def get_all_current_readings(redis_client=None) -> list[dict]:
    owns_redis_client = redis_client is None
    if redis_client is None:
        redis_client = redis.from_url(settings.redis_url(), decode_responses=True)
    try:
        pipeline = redis_client.pipeline(transaction=False)
        for sensor_id in SENSOR_IDS:
            pipeline.zrange(f"sensor:{sensor_id}", -1, -1)
        results = await pipeline.execute()

        readings = []
        for rows in results:
            if not rows:
                continue
            try:
                readings.append(json.loads(rows[0]))
            except (TypeError, json.JSONDecodeError):
                logger.debug("Skipping malformed current reading from Redis")
        if len(readings) == len(SENSOR_IDS):
            return readings

        fallback = await _get_current_readings_from_timescale()
        by_id = {reading["id"]: reading for reading in fallback}
        for reading in readings:
            sensor_id = reading.get("id") or reading.get("sensor_id")
            if sensor_id:
                by_id[sensor_id] = reading
        return [by_id[sensor_id] for sensor_id in SENSOR_IDS if sensor_id in by_id]
    finally:
        if owns_redis_client:
            await redis_client.aclose()


async def get_sensor_compare(sensor_ids: list[str], minutes: int = 60) -> dict[str, list[dict]]:
    async with _asyncpg_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                time_bucket('15 seconds', time) AS bucket,
                sensor_id,
                avg(value) AS value,
                min(value) AS min_val,
                max(value) AS max_val
            FROM readings
            WHERE sensor_id = ANY($1::varchar[])
              AND time > NOW() - ($2 * INTERVAL '1 minute')
            GROUP BY bucket, sensor_id
            ORDER BY bucket ASC
            """,
            sensor_ids,
            minutes,
        )

        comparison: dict[str, list[dict]] = {sensor_id: [] for sensor_id in sensor_ids}
        for row in rows:
            comparison[row["sensor_id"]].append(
                {
                    "time": _iso(row["bucket"]),
                    "value": float(row["value"]) if row["value"] is not None else None,
                    "min_val": float(row["min_val"]) if row["min_val"] is not None else None,
                    "max_val": float(row["max_val"]) if row["max_val"] is not None else None,
                }
            )
        return comparison


async def get_subsystem_summary(subsystem: str, minutes: int = 60) -> dict[str, dict[str, Any]]:
    async with _asyncpg_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                s.id AS sensor_id,
                s.name,
                avg(r.mean) AS mean,
                min(r.min_val) AS min,
                max(r.max_val) AS max,
                avg(r.std_dev) AS std_dev
            FROM sensors s
            LEFT JOIN readings_1min r
              ON r.sensor_id = s.id
             AND r.bucket > NOW() - ($2 * INTERVAL '1 minute')
            WHERE lower(s.subsystem) = lower($1)
            GROUP BY s.id, s.name
            ORDER BY s.id
            """,
            subsystem,
            minutes,
        )

        return {
            row["sensor_id"]: {
                "sensor_id": row["sensor_id"],
                "name": row["name"],
                "mean": _float_or_none(row["mean"]),
                "min": _float_or_none(row["min"]),
                "max": _float_or_none(row["max"]),
                "std_dev": _float_or_none(row["std_dev"]),
            }
            for row in rows
        }


async def list_sensors() -> list[dict]:
    async with _asyncpg_connection() as conn:
        rows = await conn.fetch("SELECT * FROM sensors ORDER BY id")
        return [dict(row) for row in rows]


async def sensor_ids_exist(sensor_ids: list[str]) -> set[str]:
    async with _asyncpg_connection() as conn:
        rows = await conn.fetch("SELECT id FROM sensors WHERE id = ANY($1::varchar[])", sensor_ids)
        return {row["id"] for row in rows}


async def _get_current_readings_from_timescale() -> list[dict]:
    async with _asyncpg_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT ON (s.id)
                s.id,
                s.name,
                s.subsystem,
                r.value,
                s.unit,
                CASE
                    WHEN r.value >= s.max_threshold THEN 'critical'
                    WHEN r.value >= s.max_threshold * $1 THEN 'warning'
                    ELSE 'normal'
                END AS status,
                'good' AS quality,
                s.max_threshold,
                s.min_threshold,
                r.time AS timestamp
            FROM sensors s
            LEFT JOIN readings r ON r.sensor_id = s.id
            ORDER BY s.id, r.time DESC
            """,
            settings.warning_threshold_pct,
        )

        readings = []
        for row in rows:
            if row["value"] is None:
                continue
            readings.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "subsystem": row["subsystem"],
                    "value": float(row["value"]),
                    "unit": row["unit"],
                    "status": row["status"],
                    "quality": row["quality"],
                    "max_threshold": float(row["max_threshold"]),
                    "min_threshold": float(row["min_threshold"]),
                    "timestamp": _iso(row["timestamp"]),
                }
            )
        return readings


@asynccontextmanager
async def _asyncpg_connection():
    async with engine.connect() as conn:
        raw_connection = await conn.get_raw_connection()
        yield raw_connection.driver_connection


def _iso(value) -> str | None:
    if value is None:
        return None
    if getattr(value, "tzinfo", None) is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _float_or_none(value):
    return float(value) if value is not None else None

import logging

from sqlalchemy import text

from database import engine


logger = logging.getLogger(__name__)


def _serialize_sensor_registry(sensor_list) -> list[dict]:
    return [
        {
            "id": sensor.id,
            "name": sensor.name,
            "subsystem": sensor.subsystem,
            "unit": sensor.unit,
            "baseline_value": sensor.baseline_value,
            "min_threshold": sensor.min_threshold,
            "max_threshold": sensor.max_threshold,
            "noise_amplitude": sensor.noise_amplitude,
            "sampling_interval_ms": sensor.sampling_interval_ms,
        }
        for sensor in sensor_list
    ]


async def insert_sensor_registry(sensor_list) -> None:
    sensors = _serialize_sensor_registry(sensor_list)
    if not sensors:
        return

    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO sensors (
                    id, name, subsystem, unit, baseline_value, min_threshold,
                    max_threshold, noise_amplitude, sampling_interval_ms
                )
                VALUES (
                    :id, :name, :subsystem, :unit, :baseline_value,
                    :min_threshold, :max_threshold, :noise_amplitude,
                    :sampling_interval_ms
                )
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    subsystem = EXCLUDED.subsystem,
                    unit = EXCLUDED.unit,
                    baseline_value = EXCLUDED.baseline_value,
                    min_threshold = EXCLUDED.min_threshold,
                    max_threshold = EXCLUDED.max_threshold,
                    noise_amplitude = EXCLUDED.noise_amplitude,
                    sampling_interval_ms = EXCLUDED.sampling_interval_ms
                """
            ),
            sensors,
        )
    logger.info("Seeded %s sensor definitions", len(sensors))


async def ensure_sensor_registry_seeded(sensor_list) -> None:
    sensors = _serialize_sensor_registry(sensor_list)
    if not sensors:
        raise RuntimeError("Sensor registry is empty; refusing to start data storage")

    expected_ids = {sensor["id"] for sensor in sensors}

    async with engine.begin() as conn:
        rows = await conn.execute(text("SELECT id FROM sensors"))
        existing_ids = {row[0] for row in rows}
        missing_ids = expected_ids - existing_ids

        if missing_ids:
            logger.warning(
                "Database is missing %s sensor definitions; seeding registry before storage starts",
                len(missing_ids),
            )

        await conn.execute(
            text(
                """
                INSERT INTO sensors (
                    id, name, subsystem, unit, baseline_value, min_threshold,
                    max_threshold, noise_amplitude, sampling_interval_ms
                )
                VALUES (
                    :id, :name, :subsystem, :unit, :baseline_value,
                    :min_threshold, :max_threshold, :noise_amplitude,
                    :sampling_interval_ms
                )
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    subsystem = EXCLUDED.subsystem,
                    unit = EXCLUDED.unit,
                    baseline_value = EXCLUDED.baseline_value,
                    min_threshold = EXCLUDED.min_threshold,
                    max_threshold = EXCLUDED.max_threshold,
                    noise_amplitude = EXCLUDED.noise_amplitude,
                    sampling_interval_ms = EXCLUDED.sampling_interval_ms
                """
            ),
            sensors,
        )

        rows = await conn.execute(text("SELECT id FROM sensors"))
        seeded_ids = {row[0] for row in rows}

    missing_after_seed = expected_ids - seeded_ids
    if missing_after_seed:
        sample = ", ".join(sorted(missing_after_seed)[:10])
        raise RuntimeError(
            "Sensor registry seed verification failed; "
            f"{len(missing_after_seed)} sensor definitions are still missing: {sample}"
        )

    logger.info("Verified %s sensor definitions before starting data storage", len(expected_ids))

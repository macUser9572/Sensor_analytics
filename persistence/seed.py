import logging

from sqlalchemy import text

from database import engine


logger = logging.getLogger(__name__)


async def insert_sensor_registry(sensor_list) -> None:
    sensors = [
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


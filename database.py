from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings
from simulator.registry import generate_sensor_registry


SQL_INIT_PATH = Path(__file__).resolve().parent / "sql" / "init.sql"
DB_POOL_MIN_SIZE = 20
DB_POOL_MAX_SIZE = 50

engine = create_async_engine(
    settings.db_url(),
    echo=settings.app_debug,
    pool_size=DB_POOL_MIN_SIZE,
    max_overflow=DB_POOL_MAX_SIZE - DB_POOL_MIN_SIZE,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    sql = SQL_INIT_PATH.read_text(encoding="utf-8")
    async with engine.begin() as conn:
        raw_connection = await conn.get_raw_connection()
        await raw_connection.driver_connection.execute(sql)


async def seed_sensor_registry() -> None:
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
        for sensor in generate_sensor_registry()
    ]

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

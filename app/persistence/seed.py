import logging
from sqlalchemy import text
from app.database import engine
from app.simulator.sensor_registry import generate_sensors

logger = logging.getLogger(__name__)

async def insert_sensor_registry():
    sensors = generate_sensors()
    
    values = []
    for s in sensors:
        values.append({
            "id": s.id,
            "name": s.name,
            "subsystem": s.subsystem,
            "unit": s.unit,
            "min_threshold": s.min_threshold,
            "max_threshold": s.max_threshold,
            "baseline_value": s.baseline_value
        })
        
    try:
        async with engine.begin() as conn:
            stmt = text("""
                INSERT INTO sensors (id, name, subsystem, unit, min_threshold, max_threshold, baseline_value)
                VALUES (:id, :name, :subsystem, :unit, :min_threshold, :max_threshold, :baseline_value)
                ON CONFLICT (id) DO NOTHING
            """)
            await conn.execute(stmt, values)
        logger.info("Sensor registry seeded successfully.")
    except Exception as e:
        logger.error(f"Failed to seed sensor registry: {e}")

import json
import logging
from typing import List, Dict, Any
from sqlalchemy import text
from app.database import engine
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger(__name__)

async def get_sensor_history(sensor_id: str, minutes: int = 60) -> List[Dict[str, Any]]:
    try:
        async with engine.connect() as conn:
            if minutes > 60:
                stmt = text("""
                    SELECT bucket as time, avg_value as value
                    FROM readings_1min
                    WHERE sensor_id = :sensor_id 
                      AND bucket >= NOW() - make_interval(mins => :minutes)
                    ORDER BY bucket ASC
                """)
            else:
                stmt = text("""
                    SELECT time, value
                    FROM readings
                    WHERE sensor_id = :sensor_id 
                      AND time >= NOW() - make_interval(mins => :minutes)
                    ORDER BY time ASC
                """)
            
            result = await conn.execute(stmt, {"sensor_id": sensor_id, "minutes": minutes})
            rows = result.fetchall()
            return [{"time": row.time.isoformat() if hasattr(row.time, 'isoformat') else row.time, "value": row.value} for row in rows]
    except Exception as e:
        logger.error(f"Error querying sensor history: {e}")
        return []

async def get_all_current_readings() -> List[Dict[str, Any]]:
    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        subsystems = ["turbine", "boiler", "generator", "cooling", "transformer", "auxiliary"]
        pipeline = redis.pipeline()
        for sub in subsystems:
            key = f"buffer:subsystem:{sub}"
            pipeline.zrange(key, -1, -1)
        
        results = await pipeline.execute()
        readings = []
        for sub_result in results:
            if sub_result:
                payload = json.loads(sub_result[0])
                readings.extend(payload.get("readings", []))
        
        if readings:
            return readings
            
        # Fallback
        async with engine.connect() as conn:
            stmt = text("""
                SELECT DISTINCT ON (sensor_id) sensor_id as id, time, value
                FROM readings
                ORDER BY sensor_id, time DESC
            """)
            result = await conn.execute(stmt)
            return [dict(row._mapping) for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Error querying current readings: {e}")
        return []
    finally:
        await redis.close()

async def get_subsystem_summary(subsystem: str, minutes: int = 60) -> List[Dict[str, Any]]:
    try:
        async with engine.connect() as conn:
            stmt = text("""
                SELECT 
                    r.sensor_id,
                    s.name as sensor_name,
                    AVG(r.avg_value) as mean,
                    MIN(r.min_value) as min,
                    MAX(r.max_value) as max,
                    STDDEV(r.avg_value) as std_dev
                FROM readings_1min r
                JOIN sensors s ON r.sensor_id = s.id
                WHERE LOWER(s.subsystem) = LOWER(:subsystem) 
                  AND r.bucket >= NOW() - make_interval(mins => :minutes)
                GROUP BY r.sensor_id, s.name
            """)
            result = await conn.execute(stmt, {"subsystem": subsystem, "minutes": minutes})
            return [dict(row._mapping) for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Error querying subsystem summary: {e}")
        return []

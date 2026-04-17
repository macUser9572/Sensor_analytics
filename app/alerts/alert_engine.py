import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

import redis.asyncio as aioredis
from sqlalchemy import text

from app.config import settings
from app.database import engine

logger = logging.getLogger(__name__)

class AlertEngine:
    def __init__(self):
        # Maps sensor_id -> alert details dictionary for currently firing, unacknowledged alerts
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.redis = None

    async def start(self):
        self.redis = aioredis.from_url(settings.redis_url, decode_responses=True)

    async def stop(self):
        if self.redis:
            await self.redis.close()

    async def process_readings(self, readings: List[Dict[str, Any]]):
        """
        Process a batch of readings (typically 500 per tick).
        Called by SimulatorService after calculating the new values.
        """
        for r in readings:
            sensor_id = r["id"]
            status = r["status"]
            
            if status in ("warning", "critical"):
                if sensor_id not in self.active_alerts:
                    await self.fire_alert(r)
                else:
                    # Deduplication: Alert is already active.
                    # Just update the value in our cache.
                    self.active_alerts[sensor_id]["value"] = r["value"]
                    if self.active_alerts[sensor_id]["severity"] != status:
                        self.active_alerts[sensor_id]["severity"] = status
            elif status == "normal":
                if sensor_id in self.active_alerts:
                    await self.resolve_alert(sensor_id)

    async def fire_alert(self, reading: Dict[str, Any]):
        sensor_id = reading["id"]
        alert_id = str(uuid.uuid4())
        now_dt = datetime.now(timezone.utc)
        now_str = now_dt.isoformat()
        
        # Determine which threshold was breached. If value >= max_threshold, we use max_threshold.
        threshold = reading.get("max_threshold", 0.0)
        if reading.get("value", 0) < reading.get("min_threshold", 0.0):
            threshold = reading.get("min_threshold", 0.0)
            
        alert_record = {
            "id": alert_id,
            "sensor_id": sensor_id,
            "sensor_name": reading["name"],
            "subsystem": reading["subsystem"],
            "value": reading["value"],
            "threshold": threshold,
            "unit": reading["unit"],
            "severity": reading["status"],
            "fired_at": now_str,
            "acknowledged": False
        }
        
        # Cache immediately to prevent duplicates on the next tick
        self.active_alerts[sensor_id] = alert_record
        
        # Persist to DB
        try:
            async with engine.begin() as conn:
                stmt = text("""
                    INSERT INTO alerts (id, sensor_id, value, threshold, severity, fired_at, acknowledged)
                    VALUES (CAST(:id AS UUID), :sensor_id, :value, :threshold, :severity, :fired_at, :acknowledged)
                """)
                await conn.execute(stmt, {
                    "id": alert_id,
                    "sensor_id": sensor_id,
                    "value": alert_record["value"],
                    "threshold": alert_record["threshold"],
                    "severity": alert_record["severity"],
                    "fired_at": now_dt,
                    "acknowledged": False
                })
        except Exception as e:
            logger.error(f"Failed to persist alert to TimescaleDB: {e}")
            # Note: We continue execution to ensure real-time push still works
            
        # Push to WS via Redis "alerts" channel
        if self.redis:
            payload = {
                "event": "alert_fired",
                "alert": alert_record
            }
            try:
                await self.redis.publish("alerts", json.dumps(payload))
            except Exception as e:
                logger.error(f"Failed to publish alert to Redis: {e}")

    async def resolve_alert(self, sensor_id: str):
        if sensor_id not in self.active_alerts:
            return
            
        alert_record = self.active_alerts[sensor_id]
        alert_id = alert_record["id"]
        
        # Persist resolution
        try:
            async with engine.begin() as conn:
                stmt = text("""
                    UPDATE alerts 
                    SET acknowledged = TRUE
                    WHERE id = CAST(:id AS UUID)
                """)
                await conn.execute(stmt, {"id": alert_id})
        except Exception as e:
            logger.error(f"Failed to resolve alert in TimescaleDB: {e}")
            
        # Clean from cache
        del self.active_alerts[sensor_id]
        
        # Push resolution to WS
        if self.redis:
            alert_record["acknowledged"] = True
            payload = {
                "event": "alert_resolved",
                "alert": alert_record
            }
            try:
                await self.redis.publish("alerts", json.dumps(payload))
            except Exception as e:
                logger.error(f"Failed to publish alert resolution to Redis: {e}")

    async def manual_acknowledge(self, alert_id: str) -> bool:
        """Manually mark an alert as acknowledged and resolve it."""
        sensor_to_resolve = None
        for s_id, alert in self.active_alerts.items():
            if alert["id"] == str(alert_id):
                sensor_to_resolve = s_id
                break
                
        if sensor_to_resolve:
            await self.resolve_alert(sensor_to_resolve)
            return True
            
        # If it wasn't in active cache, maybe it's just in the DB
        try:
            async with engine.begin() as conn:
                stmt = text("""
                    UPDATE alerts 
                    SET acknowledged = TRUE
                    WHERE id = CAST(:id AS UUID) AND acknowledged = FALSE
                    RETURNING id
                """)
                result = await conn.execute(stmt, {"id": str(alert_id)})
                if result.rowcount > 0:
                    # We can't broadcast full alert_resolved easily without fetching,
                    # but we can try to fetch it if really needed.
                    return True
        except Exception as e:
            logger.error(f"Failed to manual acknowledge in DB: {e}")
            
        return False

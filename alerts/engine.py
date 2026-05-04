import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text

from simulator.models import SensorReading


logger = logging.getLogger(__name__)
TERMINAL_ALERT_TYPES = {"sensor_recovered"}

# Max concurrent DB connections used by the alert engine at any one time.
# Prevents pool exhaustion when many alerts fire/resolve in the same OPC-UA
# publish cycle.
_ALERT_DB_CONCURRENCY = 5


class AlertEngine:
    def __init__(self, redis_client, db_session_factory, sensor_registry):
        self.active_alerts: dict[str, dict] = {}
        self.redis = redis_client
        self.db_session_factory = db_session_factory
        self.registry = sensor_registry
        self._db_sem = asyncio.Semaphore(_ALERT_DB_CONCURRENCY)

    async def process_reading(self, reading: SensorReading) -> None:
        sensor_id = reading.sensor_id

        if reading.status in ("warning", "critical"):
            if sensor_id not in self.active_alerts:
                alert_type = f"{reading.status}_threshold"
                await self._fire_alert(reading, alert_type)
            elif self._is_threshold_alert(self.active_alerts[sensor_id]):
                self.active_alerts[sensor_id]["value"] = reading.value
                self.active_alerts[sensor_id]["severity"] = reading.status
                self.active_alerts[sensor_id]["alert_type"] = f"{reading.status}_threshold"

        elif reading.status == "normal":
            active = self.active_alerts.get(sensor_id)
            if active and self._is_threshold_alert(active):
                await self._resolve_alert(sensor_id)

    async def load_active_from_db(self) -> None:
        async with self.db_session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT
                        a.id::text AS id,
                        a.sensor_id,
                        s.name AS sensor_name,
                        s.subsystem,
                        a.value,
                        a.threshold,
                        s.unit,
                        a.alert_type,
                        a.severity,
                        a.message,
                        a.fired_at,
                        a.acknowledged
                    FROM alerts a
                    LEFT JOIN sensors s ON s.id = a.sensor_id
                    WHERE a.acknowledged = FALSE
                      AND a.resolved_at IS NULL
                      AND a.alert_type NOT IN ('sensor_recovered')
                    ORDER BY a.fired_at DESC
                    """
                ),
            )

            self.active_alerts = {}
            for row in result:
                alert = self._serialize_alert(dict(row._mapping))
                sensor_id = alert.get("sensor_id")
                if sensor_id and sensor_id not in self.active_alerts:
                    self.active_alerts[sensor_id] = alert
        logger.info("Recovered %s active alerts from database", len(self.active_alerts))

    async def register_external_alert(
        self,
        alert: dict,
        *,
        terminal: bool = False,
    ) -> None:
        sensor_id = alert.get("sensor_id")
        if not sensor_id:
            return
        if terminal or alert.get("alert_type") in TERMINAL_ALERT_TYPES:
            await self.clear_sensor_alert(sensor_id)
            return
        if sensor_id not in self.active_alerts:
            self.active_alerts[sensor_id] = alert

    async def clear_sensor_alert(self, sensor_id: str) -> None:
        alert = self.active_alerts.pop(sensor_id, None)
        if alert:
            await self._mark_resolved_in_db(alert["id"])

    async def acknowledge(self, alert_id: str) -> dict | None:
        alert = await self._fetch_alert(alert_id)
        if not alert:
            return None

        async with self.db_session_factory() as session:
            result = await session.execute(
                text(
                    """
                    UPDATE alerts
                    SET acknowledged = TRUE,
                        resolved_at = COALESCE(resolved_at, NOW())
                    WHERE id = CAST(:id AS UUID)
                    RETURNING id::text
                    """
                ),
                {"id": alert_id},
            )
            updated = result.first()
            await session.commit()
            if updated is None:
                return None

        sensor_id = alert.get("sensor_id")
        if sensor_id:
            self.active_alerts.pop(sensor_id, None)
        alert["acknowledged"] = True
        alert["resolved_at"] = datetime.now(timezone.utc).isoformat()
        await self.redis.publish("alerts", json.dumps({"event": "alert_resolved", "alert": alert}))
        return alert

    async def _fire_alert(self, reading: SensorReading, alert_type: str) -> None:
        alert = {
            "id": str(uuid4()),
            "sensor_id": reading.sensor_id,
            "sensor_name": reading.name,
            "subsystem": reading.subsystem,
            "value": reading.value,
            "threshold": reading.max_threshold,
            "unit": reading.unit,
            "alert_type": alert_type,
            "severity": "warning" if "warning" in alert_type else "critical",
            "message": f"{reading.name} {reading.status} threshold reached",
            "fired_at": datetime.now(timezone.utc).isoformat(),
            "acknowledged": False,
        }
        self.active_alerts[reading.sensor_id] = alert
        await self.redis.publish("alerts", json.dumps({"event": "alert_fired", "alert": alert}))
        asyncio.create_task(self._bg_persist_alert(alert))

    async def _resolve_alert(self, sensor_id: str) -> None:
        alert = self.active_alerts.pop(sensor_id, None)
        if not alert:
            return
        alert["resolved_at"] = datetime.now(timezone.utc).isoformat()
        alert["acknowledged"] = True
        await self.redis.publish("alerts", json.dumps({"event": "alert_resolved", "alert": alert}))
        asyncio.create_task(self._bg_mark_resolved(alert["id"]))

    async def _bg_persist_alert(self, alert: dict) -> None:
        async with self._db_sem:
            try:
                await self._persist_alert(alert)
            except Exception:
                logger.exception("Failed to persist alert %s to DB", alert.get("id"))

    async def _bg_mark_resolved(self, alert_id: str) -> None:
        async with self._db_sem:
            try:
                await self._mark_resolved_in_db(alert_id)
            except Exception:
                logger.exception("Failed to mark alert %s resolved in DB", alert_id)

    async def _persist_alert(self, alert: dict) -> None:
        async with self.db_session_factory() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO alerts (
                        id, sensor_id, value, threshold, severity, alert_type,
                        message, fired_at, acknowledged
                    )
                    VALUES (
                        CAST(:id AS UUID), :sensor_id, :value, :threshold, :severity,
                        :alert_type, :message, :fired_at, FALSE
                    )
                    """
                ),
                {
                    "id": alert["id"],
                    "sensor_id": alert["sensor_id"],
                    "value": alert.get("value"),
                    "threshold": alert.get("threshold"),
                    "severity": alert["severity"],
                    "alert_type": alert["alert_type"],
                    "message": alert.get("message"),
                    "fired_at": datetime.fromisoformat(alert["fired_at"]),
                },
            )
            await session.commit()

    async def _mark_resolved_in_db(self, alert_id: str) -> None:
        async with self.db_session_factory() as session:
            await session.execute(
                text(
                    """
                    UPDATE alerts
                    SET acknowledged = TRUE,
                        resolved_at = COALESCE(resolved_at, NOW())
                    WHERE id = CAST(:id AS UUID)
                    """
                ),
                {"id": alert_id},
            )
            await session.commit()

    async def _fetch_alert(self, alert_id: str) -> dict | None:
        async with self.db_session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT
                        a.id::text AS id,
                        a.sensor_id,
                        s.name AS sensor_name,
                        s.subsystem,
                        a.value,
                        a.threshold,
                        s.unit,
                        a.alert_type,
                        a.severity,
                        a.message,
                        a.fired_at,
                        a.resolved_at,
                        a.acknowledged
                    FROM alerts a
                    LEFT JOIN sensors s ON s.id = a.sensor_id
                    WHERE a.id = CAST(:id AS UUID)
                    """
                ),
                {"id": alert_id},
            )
            row = result.first()
            return self._serialize_alert(dict(row._mapping)) if row else None

    def _is_threshold_alert(self, alert: dict) -> bool:
        return alert.get("alert_type") in {"warning_threshold", "critical_threshold"}

    def _serialize_alert(self, alert: dict) -> dict:
        for key in ("fired_at", "resolved_at"):
            value = alert.get(key)
            if value is not None:
                if getattr(value, "tzinfo", None) is None:
                    value = value.replace(tzinfo=timezone.utc)
                alert[key] = value.isoformat()
        for key in ("value", "threshold"):
            if alert.get(key) is not None:
                alert[key] = float(alert[key])
        return alert

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text

from config import settings
from simulator.models import SensorDefinition


logger = logging.getLogger(__name__)


HEALTH_DB_WRITE_INTERVAL = 10.0  # seconds between routine "live" DB writes per sensor


_WATCHDOG_DB_CONCURRENCY = 5


class SensorWatchdog:
    def __init__(
        self,
        redis_client,
        db_session_factory,
        sensor_registry: dict[str, SensorDefinition] | None = None,
        alert_engine=None,
        should_emit_sensor_alert=None,
    ):
        self.redis = redis_client
        self.db_session_factory = db_session_factory
        self.registry = sensor_registry or {}
        self.alert_engine = alert_engine
        self.should_emit_sensor_alert = should_emit_sensor_alert or (
            lambda _sensor_id, _alert_type: True
        )
        self.last_seen: dict[str, float] = {}
        self.fault_sensors: set[str] = set()
        self.timeout = settings.watchdog_timeout_seconds
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_health_write: dict[str, float] = {}
        self._pending_health: dict[str, tuple[str, str | None]] = {}
        self._db_sem = asyncio.Semaphore(_WATCHDOG_DB_CONCURRENCY)

    async def heartbeat(self, sensor_id: str) -> None:
        now = time.time()
        self.last_seen[sensor_id] = now

        recovering = sensor_id in self.fault_sensors
        if recovering:
            self.fault_sensors.remove(sensor_id)
            await self._fire_recovery_alert(sensor_id)

        # Queue routine "live" writes for the watchdog loop. Awaiting a DB
        # round-trip here blocks the OPC-UA data-change hot path, which is
        # especially expensive when TimescaleDB is on another LAN machine.
        last_write = self._last_health_write.get(sensor_id, 0.0)
        if recovering:
            self._last_health_write[sensor_id] = now
            await self._update_health_db(sensor_id, "live")
        elif (now - last_write) >= HEALTH_DB_WRITE_INTERVAL:
            self._last_health_write[sensor_id] = now
            self._queue_health_update(sensor_id, "live")

    async def mark_fault(self, sensor_id: str, quality_code: str | None = None) -> None:
        now = time.time()
        already_faulted = sensor_id in self.fault_sensors
        self.fault_sensors.add(sensor_id)
        last_write = self._last_health_write.get(sensor_id, 0.0)
        if not already_faulted or (now - last_write) >= HEALTH_DB_WRITE_INTERVAL:
            self._last_health_write[sensor_id] = now
            self._queue_health_update(sensor_id, "fault", quality_code=quality_code)

    async def mark_uncertain(self, sensor_id: str, quality_code: str | None = None) -> None:
        now = time.time()
        self.last_seen[sensor_id] = now
        last_write = self._last_health_write.get(sensor_id, 0.0)
        if (now - last_write) >= HEALTH_DB_WRITE_INTERVAL:
            self._last_health_write[sensor_id] = now
            self._queue_health_update(sensor_id, "uncertain", quality_code=quality_code)

    async def check_loop(self) -> None:
        self._running = True
        while self._running:
            await asyncio.sleep(settings.watchdog_check_interval_seconds)
            await self._flush_pending_health_updates()
            now = time.time()
            for sensor_id, last in list(self.last_seen.items()):
                silence = now - last
                if silence > self.timeout and sensor_id not in self.fault_sensors:
                    try:
                        self.fault_sensors.add(sensor_id)
                        await self._fire_missing_alert(sensor_id, silence)
                        await self._update_health_db(sensor_id, "missing")
                    except Exception:
                        logger.exception("Watchdog failed while marking %s missing", sensor_id)

    async def _fire_missing_alert(self, sensor_id: str, silence_seconds: float) -> None:
        await self._publish_and_persist_alert(
            sensor_id=sensor_id,
            alert_type="sensor_missing",
            severity="critical",
            message=f"No data for {silence_seconds:.0f}s - sensor may be offline",
        )

    async def _fire_recovery_alert(self, sensor_id: str) -> None:
        await self._publish_and_persist_alert(
            sensor_id=sensor_id,
            alert_type="sensor_recovered",
            severity="info",
            message="Sensor data stream recovered",
        )

    async def _publish_and_persist_alert(
        self,
        sensor_id: str,
        alert_type: str,
        severity: str,
        message: str,
        value: float | None = None,
        threshold: float | None = None,
    ) -> None:
        terminal = alert_type == "sensor_recovered"
        if not terminal and not self.should_emit_sensor_alert(sensor_id, alert_type):
            return

        if self.alert_engine and not terminal and sensor_id in self.alert_engine.active_alerts:
            return

        meta = self.registry.get(sensor_id)
        alert = {
            "id": str(uuid4()),
            "sensor_id": sensor_id,
            "sensor_name": meta.name if meta else sensor_id,
            "subsystem": meta.subsystem if meta else None,
            "unit": meta.unit if meta else None,
            "value": value,
            "threshold": threshold,
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "fired_at": datetime.now(timezone.utc).isoformat(),
            "acknowledged": False,
        }
        payload = {"event": "alert_fired", "alert": alert}
        # Redis publish and in-memory state update happen immediately.
        # DB write is backgrounded to avoid blocking the OPC-UA hot path.
        await self.redis.publish("alerts", json.dumps(payload))
        asyncio.create_task(self._bg_insert_alert(alert, sensor_id, value, threshold, severity, alert_type, message))

        if self.alert_engine:
            await self.alert_engine.register_external_alert(alert, terminal=terminal)

    async def _bg_insert_alert(
        self,
        alert: dict,
        sensor_id: str,
        value: float | None,
        threshold: float | None,
        severity: str,
        alert_type: str,
        message: str,
    ) -> None:
        async with self._db_sem:
            try:
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
                            "sensor_id": sensor_id,
                            "value": value,
                            "threshold": threshold,
                            "severity": severity,
                            "alert_type": alert_type,
                            "message": message,
                            "fired_at": datetime.fromisoformat(alert["fired_at"]),
                        },
                    )
                    await session.commit()
            except Exception:
                logger.exception("Failed to persist watchdog alert %s to DB", alert.get("id"))

    def _queue_health_update(
        self,
        sensor_id: str,
        status: str,
        quality_code: str | None = None,
    ) -> None:
        self._pending_health[sensor_id] = (status, quality_code)

    async def _flush_pending_health_updates(self) -> None:
        if not self._pending_health:
            return

        pending = self._pending_health
        self._pending_health = {}
        rows = [
            {
                "sensor_id": sensor_id,
                "status": status,
                "quality_code": quality_code,
            }
            for sensor_id, (status, quality_code) in pending.items()
        ]

        try:
            await self._update_health_db_many(rows)
        except Exception:
            logger.exception("Failed to flush %s pending sensor_health updates", len(rows))
            self._pending_health = {**pending, **self._pending_health}

    async def _update_health_db(
        self,
        sensor_id: str,
        status: str,
        quality_code: str | None = None,
    ) -> None:
        await self._update_health_db_many(
            [
                {
                    "sensor_id": sensor_id,
                    "status": status,
                    "quality_code": quality_code,
                }
            ]
        )

    async def _update_health_db_many(self, rows: list[dict[str, str | None]]) -> None:
        if not rows:
            return

        async with self._db_sem:
            async with self.db_session_factory() as session:
                await session.execute(
                    text(
                        """
                        INSERT INTO sensor_health (
                            sensor_id, last_seen, status, quality_code, updated_at
                        )
                        VALUES (
                            :sensor_id,
                            CASE WHEN :status IN ('live', 'uncertain') THEN NOW() ELSE NULL END,
                            :status,
                            :quality_code,
                            NOW()
                        )
                        ON CONFLICT (sensor_id) DO UPDATE SET
                            last_seen = CASE
                                WHEN :status IN ('live', 'uncertain') THEN NOW()
                                ELSE sensor_health.last_seen
                            END,
                            status = EXCLUDED.status,
                            quality_code = EXCLUDED.quality_code,
                            updated_at = NOW()
                        """
                    ),
                    rows,
                )
                await session.commit()

    async def _initialise_last_seen_from_redis(self) -> None:
        async for key in self.redis.scan_iter(match="sensor:*"):
            if isinstance(key, bytes):
                key = key.decode()
            sensor_id = key.split(":", 1)[1]
            rows = await self.redis.zrange(key, -1, -1, withscores=True)
            if rows:
                self.last_seen[sensor_id] = float(rows[0][1])

    async def _initialise_health_rows(self) -> None:
        if not self.registry:
            return

        async with self.db_session_factory() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO sensor_health (sensor_id, status, updated_at)
                    VALUES (:sensor_id, 'unknown', NOW())
                    ON CONFLICT (sensor_id) DO NOTHING
                    """
                ),
                [{"sensor_id": sensor_id} for sensor_id in self.registry],
            )
            await session.commit()

    async def start(self) -> None:
        if self._task and not self._task.done():
            return

        await self._initialise_last_seen_from_redis()
        try:
            await self._initialise_health_rows()
        except Exception:
            logger.exception("Failed to initialise sensor_health rows")
        self._task = asyncio.create_task(self.check_loop(), name="bhel-sensor-watchdog")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self._flush_pending_health_updates()

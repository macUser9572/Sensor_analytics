import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text

from simulator.models import SensorDefinition, SensorReading


logger = logging.getLogger(__name__)


class DataChangeHandler:
    """
    Bridge asyncua data change callbacks into Redis Pub/Sub, rolling buffers,
    quality alerts, and watchdog heartbeats.
    """

    def __init__(
        self,
        redis_client,
        sensor_registry: dict[str, SensorDefinition],
        watchdog=None,
        db_session_factory=None,
        batch_writer=None,
        alert_engine=None,
    ):
        self.redis = redis_client
        self.registry = sensor_registry
        self.watchdog = watchdog
        self.db_session_factory = db_session_factory
        self.batch_writer = batch_writer
        self.alert_engine = alert_engine
        # Caches node.nodeid (str) → sensor_id to avoid a live OPC-UA round-trip
        # on every data change notification.
        self._node_name_cache: dict[str, str] = {}

    async def datachange_notification(self, node, val, data) -> None:
        try:
            status_code = data.monitored_item.Value.StatusCode
            node_id_str = str(node.nodeid)
            node_name = self._node_name_cache.get(node_id_str)
            if node_name is None:
                node_name = (await node.read_browse_name()).Name
                self._node_name_cache[node_id_str] = node_name
            meta = self.registry.get(node_name)
            if not meta:
                return

            if self._status_is_bad(status_code):
                await self._handle_sensor_fault(node_name, meta, str(status_code))
                return

            if self._status_is_uncertain(status_code):
                await self._handle_sensor_uncertain(node_name, meta, val, str(status_code))
                return

            if val is None:
                return

            if self.watchdog:
                await self.watchdog.heartbeat(node_name)
            await self._process_good_reading(node_name, meta, val)
        except Exception:
            logger.exception("Failed to process OPC-UA data change notification")

    async def _handle_sensor_fault(
        self,
        sensor_id: str,
        meta: SensorDefinition,
        quality_code: str,
    ) -> None:
        message = f"OPC-UA quality is bad for {sensor_id}: {quality_code}"
        await self._publish_and_persist_alert(
            sensor_id=sensor_id,
            alert_type="sensor_fault",
            severity="critical",
            message=message,
        )
        if self.watchdog:
            await self.watchdog.mark_fault(sensor_id, quality_code=quality_code)
        else:
            await self._update_health_db(sensor_id, "fault", quality_code=quality_code)

    async def _handle_sensor_uncertain(
        self,
        sensor_id: str,
        meta: SensorDefinition,
        val,
        quality_code: str | None = None,
    ) -> None:
        if val is not None:
            await self._publish_reading(sensor_id, meta, val, quality="uncertain")

        await self._publish_and_persist_alert(
            sensor_id=sensor_id,
            alert_type="sensor_uncertain",
            severity="warning",
            message=f"OPC-UA quality is uncertain for {sensor_id}: {quality_code}",
            value=float(val) if val is not None else None,
            threshold=meta.max_threshold,
        )

        if self.watchdog:
            await self.watchdog.mark_uncertain(sensor_id, quality_code=quality_code)
        else:
            await self._update_health_db(sensor_id, "uncertain", quality_code=quality_code)

    async def _process_good_reading(
        self,
        sensor_id: str,
        meta: SensorDefinition,
        val,
    ) -> None:
        await self._publish_reading(sensor_id, meta, val, quality="good")

    async def _publish_reading(
        self,
        sensor_id: str,
        meta: SensorDefinition,
        val,
        quality: str,
    ) -> None:
        pct = float(val) / meta.max_threshold if meta.max_threshold else 0.0
        status = "critical" if pct >= 1.0 else "warning" if pct >= 0.8 else "normal"
        timestamp_dt = datetime.now(timezone.utc)
        value = float(val)
        timestamp = timestamp_dt.isoformat()

        reading = {
            "id": sensor_id,
            "name": meta.name,
            "subsystem": meta.subsystem,
            "value": round(value, 3),
            "unit": meta.unit,
            "status": status,
            "quality": quality,
            "max_threshold": meta.max_threshold,
            "min_threshold": meta.min_threshold,
            "timestamp": timestamp,
        }

        sensor_reading = SensorReading(
            sensor_id=sensor_id,
            name=meta.name,
            subsystem=meta.subsystem,
            value=value,
            unit=meta.unit,
            status=status,
            timestamp=timestamp_dt,
            max_threshold=meta.max_threshold,
            min_threshold=meta.min_threshold,
            quality=quality,
        )

        if quality == "good" and self.batch_writer:
            try:
                await self.batch_writer.collect([sensor_reading])
            except Exception:
                logger.exception("Failed to collect reading for batch writer")

        if quality == "good" and self.alert_engine:
            try:
                await self.alert_engine.process_reading(sensor_reading)
            except Exception:
                logger.exception("Failed to process threshold alert")

        channel = f"subsystem:{meta.subsystem}"
        key = f"sensor:{sensor_id}"
        score = datetime.now(timezone.utc).timestamp()
        payload = json.dumps(
            {
                "subsystem": meta.subsystem,
                "timestamp": reading["timestamp"],
                "readings": [reading],
            }
        )
        async with self.redis.pipeline(transaction=False) as pipe:
            pipe.publish(channel, payload)
            pipe.zadd(key, {json.dumps(reading): score})
            pipe.zremrangebyscore(key, 0, score - 600)
            await pipe.execute()

    async def _publish_and_persist_alert(
        self,
        sensor_id: str,
        alert_type: str,
        severity: str,
        message: str,
        value: float | None = None,
        threshold: float | None = None,
    ) -> None:
        if self.watchdog:
            await self.watchdog._publish_and_persist_alert(
                sensor_id=sensor_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                value=value,
                threshold=threshold,
            )
            return

        alert = {
            "id": str(uuid4()),
            "sensor_id": sensor_id,
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "fired_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.redis.publish("alerts", json.dumps({"event": "alert_fired", "alert": alert}))

    async def _update_health_db(
        self,
        sensor_id: str,
        status: str,
        quality_code: str | None = None,
    ) -> None:
        if not self.db_session_factory:
            return
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
                {
                    "sensor_id": sensor_id,
                    "status": status,
                    "quality_code": quality_code,
                },
            )
            await session.commit()

    def _status_is_bad(self, status_code) -> bool:
        is_bad = getattr(status_code, "is_bad", None)
        if callable(is_bad):
            return bool(is_bad())
        return "bad" in str(status_code).lower()

    def _status_is_uncertain(self, status_code) -> bool:
        is_uncertain = getattr(status_code, "is_uncertain", None)
        if callable(is_uncertain):
            return bool(is_uncertain())
        return "uncertain" in str(status_code).lower()

import json
import logging
from typing import Any

from fastapi import WebSocket

from simulator.registry import generate_sensor_registry


logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active: set[WebSocket] = set()
        self._sensor_ids = [sensor.id for sensor in generate_sensor_registry()]

    async def connect(
        self,
        ws: WebSocket,
        redis_client,
        *,
        send_history: bool = True,
    ) -> None:
        await ws.accept()
        self.active.add(ws)

        if not send_history:
            return

        history = await self._load_history(redis_client)
        if history:
            await ws.send_text(json.dumps({"type": "history", "data": history}))

    async def disconnect(self, ws: WebSocket) -> None:
        self.active.discard(ws)

    async def broadcast(self, message: str) -> None:
        dead: set[WebSocket] = set()
        for ws in self.active.copy():
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        self.active -= dead

    async def _load_history(self, redis) -> dict[str, list[dict[str, Any]]]:
        pipeline = redis.pipeline(transaction=False)
        for sensor_id in self._sensor_ids:
            pipeline.zrange(f"sensor:{sensor_id}", -1, -1)

        try:
            results = await pipeline.execute()
        except Exception:
            logger.exception("Failed to load WebSocket history from Redis")
            return {}

        history: dict[str, list[dict[str, Any]]] = {}
        for sensor_id, rows in zip(self._sensor_ids, results):
            readings: list[dict[str, Any]] = []
            for row in rows:
                try:
                    payload = row.decode("utf-8") if isinstance(row, bytes) else row
                    readings.append(json.loads(payload))
                except (TypeError, json.JSONDecodeError):
                    logger.debug("Skipping malformed Redis history row for %s", sensor_id)
            if readings:
                history[sensor_id] = readings

        return history

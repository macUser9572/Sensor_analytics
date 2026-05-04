import asyncio
import json
import logging
from contextlib import suppress

import redis.asyncio as redis

from websocket.connection_manager import ConnectionManager


logger = logging.getLogger(__name__)

CHANNELS = [
    "subsystem:turbine",
    "subsystem:boiler",
    "subsystem:generator",
    "subsystem:cooling",
    "subsystem:transformer",
    "subsystem:auxiliary",
    "alerts",
]


class RedisSubscriber:
    def __init__(self, manager: ConnectionManager, alert_manager: ConnectionManager) -> None:
        self.sensor_manager = manager
        self.alert_manager = alert_manager
        self._task: asyncio.Task | None = None
        self._running = False
        self._subscribed = False

    async def start(self, redis_url: str) -> None:
        if self._task and not self._task.done():
            return
        self._running = True
        self._task = asyncio.create_task(self._listen(redis_url))

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    def is_subscribed(self) -> bool:
        return self._subscribed

    async def _listen(self, redis_url: str) -> None:
        while self._running:
            redis_client = None
            pubsub = None
            try:
                redis_client = redis.from_url(
                    redis_url,
                    decode_responses=False,
                    socket_keepalive=True,
                    socket_connect_timeout=5,
                    socket_timeout=10,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                pubsub = redis_client.pubsub()
                await pubsub.subscribe(*CHANNELS)
                self._subscribed = True
                logger.info("Redis subscriber listening on %s", ", ".join(CHANNELS))

                async for message in pubsub.listen():
                    if not self._running:
                        break
                    if message.get("type") != "message":
                        continue

                    channel = self._decode(message.get("channel"))
                    data = self._decode(message.get("data"))
                    if channel == "alerts":
                        await self.alert_manager.broadcast(data)
                    elif channel.startswith("subsystem:"):
                        await self.sensor_manager.broadcast(self._sensor_payload(data))

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._subscribed = False
                logger.error("Redis subscriber disconnected: %s. Reconnecting in 3s...", exc)
                await asyncio.sleep(3)
            finally:
                self._subscribed = False
                if pubsub is not None:
                    with suppress(Exception):
                        await pubsub.close()
                if redis_client is not None:
                    with suppress(Exception):
                        await redis_client.aclose()

    def _sensor_payload(self, data: str) -> str:
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            return data
        if isinstance(payload, dict) and "type" not in payload:
            payload = {"type": "update", **payload}
        return json.dumps(payload)

    def _decode(self, value) -> str:
        return value.decode("utf-8") if isinstance(value, bytes) else str(value)


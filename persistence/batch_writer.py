import asyncio
import logging
from contextlib import suppress

from config import settings


logger = logging.getLogger(__name__)


class BatchWriter:
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self._buffer: list[tuple] = []
        self._max_buffer_size = 100_000
        self._lock = asyncio.Lock()
        self._running = False
        self._task: asyncio.Task | None = None

    async def collect(self, readings):
        """Called by DataChangeHandler on every notification. O(1), never blocks."""
        async with self._lock:
            for reading in readings:
                self._buffer.append((reading.timestamp, reading.sensor_id, reading.value))
            if len(self._buffer) > self._max_buffer_size:
                self._buffer = self._buffer[-self._max_buffer_size :]

    async def flush(self):
        async with self._lock:
            if not self._buffer:
                return
            batch = self._buffer.copy()
            self._buffer.clear()

        try:
            async with self.db_session_factory() as session:
                connection = await session.connection()
                raw_connection = await connection.get_raw_connection()
                await raw_connection.driver_connection.executemany(
                    """
                    INSERT INTO readings (time, sensor_id, value)
                    VALUES ($1, $2, $3)
                    ON CONFLICT DO NOTHING
                    """,
                    batch,
                )
                await session.commit()
            logger.info("BatchWriter: flushed %s readings to TimescaleDB", len(batch))
        except Exception as exc:
            logger.error("BatchWriter flush failed: %s", exc)
            async with self._lock:
                combined = batch + self._buffer
                if len(combined) > self._max_buffer_size:
                    logger.warning(
                        "BatchWriter retry buffer exceeded %s readings; keeping newest readings",
                        self._max_buffer_size,
                    )
                self._buffer = combined[-self._max_buffer_size :]

    async def start(self):
        if self._task and not self._task.done():
            return
        self._running = True
        self._task = asyncio.create_task(self._flush_loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
        await self.flush()

    async def _flush_loop(self):
        while self._running:
            await asyncio.sleep(settings.batch_flush_interval_seconds)
            await self.flush()

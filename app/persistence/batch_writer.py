import asyncio
from collections import deque
import logging
from sqlalchemy import text
from app.database import engine
from app.config import settings

logger = logging.getLogger(__name__)

class BatchWriter:
    def __init__(self):
        self.buffer = deque()
        self.is_running = False
        self._task = None

    def collect(self, readings):
        """Append multiple readings to the buffer.
        Expected format per reading: {'time': datetime, 'sensor_id': str, 'value': float}
        """
        self.buffer.extend(readings)

    async def flush(self):
        if not self.buffer:
            return
            
        snapshot = list(self.buffer)
        self.buffer.clear()
        
        try:
            async with engine.begin() as conn:
                stmt = text("""
                    INSERT INTO readings (time, sensor_id, value)
                    VALUES (:time, :sensor_id, :value)
                """)
                await conn.execute(stmt, snapshot)
            logger.info(f"BatchWriter: Flushed {len(snapshot)} readings to TimescaleDB.")
        except Exception as e:
            logger.error(f"BatchWriter: Error flushing to DB: {e}")
            # If DB is unreachable, log and continue. We drop the batch for demo safety.

    async def _loop(self):
        while self.is_running:
            await asyncio.sleep(settings.batch_flush_interval_seconds)
            await self.flush()

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.flush()

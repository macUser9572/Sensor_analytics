import asyncio
import logging
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger(__name__)

class RedisSubscriber:
    def __init__(self, connection_manager):
        self.manager = connection_manager
        self.is_running = False
        self._task = None
        self.redis = None
        self.pubsub = None

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.redis = aioredis.from_url(settings.redis_url(), decode_responses=True)
        self.pubsub = self.redis.pubsub()
        self._task = asyncio.create_task(self._listen_loop())

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()

    async def _listen_loop(self):
        channels = [
            "subsystem:turbine", 
            "subsystem:boiler", 
            "subsystem:generator", 
            "subsystem:cooling", 
            "subsystem:transformer", 
            "subsystem:auxiliary"
        ]
        
        while self.is_running:
            try:
                await self.pubsub.subscribe(*channels)
                logger.info("Subscribed to Redis channels successfully")
                
                async for message in self.pubsub.listen():
                    if not self.is_running:
                        break
                    
                    if message["type"] == "message":
                        data = message["data"]
                        await self.manager.broadcast(data)
                        
            except Exception as e:
                if not self.is_running:
                    break
                logger.error(f"Redis Pub/Sub error: {e}. Reconnecting in 3 seconds...")
                await asyncio.sleep(3)

from fastapi import WebSocket
from typing import Set
import logging
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.redis = aioredis.from_url(settings.redis_url, decode_responses=True)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Send initial last-60s data to hydrate on connect
        try:
            subsystems = ["turbine", "boiler", "generator", "cooling", "transformer", "auxiliary"]
            pipeline = self.redis.pipeline()
            for sub in subsystems:
                key = f"buffer:subsystem:{sub}"
                pipeline.zrange(key, 0, -1)
            
            results = await pipeline.execute()
            # results is a list of lists of strings (JSON payloads)
            for sub_result in results:
                for payload_str in sub_result:
                    await websocket.send_text(payload_str)
        except Exception as e:
            logger.error(f"Error fetching initial WS buffer: {e}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        stale_connections = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception as e:
                # Catch general exceptions (e.g. client closed mid-send)
                stale_connections.add(connection)
        
        # Clean up failed connections silently to avoid memory leaks
        for connection in stale_connections:
            self.disconnect(connection)

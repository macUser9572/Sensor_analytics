from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
import logging

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = logging.getLogger(__name__)

@router.websocket("/live")
async def websocket_live(websocket: WebSocket):
    manager = websocket.app.state.ws_manager
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive with simple ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

import json
import asyncio
import redis.asyncio as aioredis
from app.config import settings

@router.websocket("/alerts")
async def websocket_alerts(websocket: WebSocket):
    await websocket.accept()
    
    simulator = websocket.app.state.simulator
    if simulator and hasattr(simulator, "alert_engine"):
        for alert in simulator.alert_engine.active_alerts.values():
            await websocket.send_text(json.dumps({
                "event": "alert_fired",
                "alert": alert
            }))
            
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("alerts")
    
    async def redis_listener():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await websocket.send_text(message["data"])
        except Exception as e:
            logger.error(f"Alerts redis listener error: {e}")
            
    async def ws_listener():
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
            
    try:
        listen_task = asyncio.create_task(redis_listener())
        ws_task = asyncio.create_task(ws_listener())
        
        done, pending = await asyncio.wait(
            [listen_task, ws_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        for task in pending:
            task.cancel()
    finally:
        await pubsub.close()
        await redis_client.close()

@router.get("/status")
async def websocket_status(request: Request):
    manager = request.app.state.ws_manager
    return {"active_connections": len(manager.active_connections)}

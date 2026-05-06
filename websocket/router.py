import asyncio
import json
import logging

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect

from websocket.connection_manager import ConnectionManager
from websocket.redis_subscriber import CHANNELS, RedisSubscriber


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])
live_manager = ConnectionManager()
alert_manager = ConnectionManager()
redis_subscriber = RedisSubscriber(live_manager, alert_manager)


@router.websocket("/live")
async def live_stream(ws: WebSocket) -> None:
    redis_client = ws.app.state.redis_client
    await live_manager.connect(ws, redis_client)
    try:
        while True:
            try:
                message = await asyncio.wait_for(ws.receive_text(), timeout=30)
                if message == "ping":
                    await ws.send_text("pong")
            except asyncio.TimeoutError:
                await ws.send_text("ping")
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.debug("Live WebSocket disconnected", exc_info=True)
    finally:
        await live_manager.disconnect(ws)


@router.websocket("/alerts")
async def alert_stream(ws: WebSocket) -> None:
    redis_client = ws.app.state.redis_client
    await alert_manager.connect(ws, redis_client, send_history=False)
    active_alerts = sorted(
        ws.app.state.alert_engine.active_alerts.values(),
        key=lambda alert: alert.get("fired_at", ""),
        reverse=True,
    )
    await ws.send_text(json.dumps({"type": "active_alerts", "data": active_alerts}))

    try:
        while True:
            try:
                message = await asyncio.wait_for(ws.receive_text(), timeout=30)
                if message == "ping":
                    await ws.send_text("pong")
            except asyncio.TimeoutError:
                await ws.send_text("ping")
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.debug("Alert WebSocket disconnected", exc_info=True)
    finally:
        await alert_manager.disconnect(ws)


@router.get("/status")
async def websocket_status(request: Request) -> dict:
    return {
        "live_connections": len(live_manager.active),
        "alert_connections": len(alert_manager.active),
        "redis_subscribed": redis_subscriber.is_subscribed(),
        "channels": CHANNELS,
    }

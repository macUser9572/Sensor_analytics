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

@router.websocket("/alerts")
async def websocket_alerts(websocket: WebSocket):
    # Skeleton endpoint for Phase 6 Alert stream
    await websocket.accept()
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass

@router.get("/status")
async def websocket_status(request: Request):
    manager = request.app.state.ws_manager
    return {"active_connections": len(manager.active_connections)}

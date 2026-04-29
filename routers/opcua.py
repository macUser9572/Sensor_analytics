from fastapi import APIRouter, HTTPException, Request

from config import settings


router = APIRouter(prefix="/opcua", tags=["opcua"])


@router.get("/nodes")
async def get_opcua_nodes(request: Request) -> list[str]:
    opc_server = getattr(request.app.state, "opc_server", None)
    if opc_server is None:
        raise HTTPException(status_code=503, detail="OPC-UA server is not running")
    return sorted(opc_server.sensor_nodes)


@router.get("/status")
async def get_opcua_status(request: Request):
    opc_server = getattr(request.app.state, "opc_server", None)
    opc_client = getattr(request.app.state, "opc_client", None)

    return {
        "server_running": bool(opc_server and opc_server.is_running()),
        "client_connected": bool(opc_client and opc_client.is_connected()),
        "opc_server_url": settings.OPC_SERVER_URL,
        "monitored_items": opc_client.monitored_items if opc_client else 0,
        "redis_host": settings.REDIS_HOST,
    }

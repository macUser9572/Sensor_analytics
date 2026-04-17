from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel
from sqlalchemy import text

from app.database import engine

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/")
async def list_alerts(
    acknowledged: Optional[bool] = Query(None),
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Returns recent alerts from TimescaleDB, most recent first"""
    try:
        async with engine.connect() as conn:
            query = "SELECT * FROM alerts"
            params = {"limit": limit}
            
            if acknowledged is not None:
                query += " WHERE acknowledged = :acknowledged"
                params["acknowledged"] = acknowledged
                
            query += " ORDER BY fired_at DESC LIMIT :limit"
            
            result = await conn.execute(text(query), params)
            return [dict(row._mapping) for row in result.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active")
async def active_alerts(request: Request) -> List[Dict[str, Any]]:
    """Returns only currently firing alerts (from active_alerts dict)"""
    simulator = request.app.state.simulator
    if not simulator or not hasattr(simulator, 'alert_engine'):
        return []
        
    return list(simulator.alert_engine.active_alerts.values())

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, request: Request):
    """Marks alert as acknowledged in DB and resolves it"""
    simulator = request.app.state.simulator
    if not simulator or not hasattr(simulator, 'alert_engine'):
        raise HTTPException(status_code=500, detail="Alert engine not ready")
        
    success = await simulator.alert_engine.manual_acknowledge(alert_id)
    if not success:
        # Might be already acknowledged or not found
        return {"status": "ignored", "message": "Alert not found or already acknowledged"}
        
    return {"status": "success", "message": "Alert acknowledged"}

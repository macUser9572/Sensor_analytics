from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/simulator", tags=["simulator"])

class FaultRequest(BaseModel):
    target_multiplier: float = 1.2

@router.get("/readings")
async def get_readings(request: Request):
    return request.app.state.simulator.get_current_readings()

@router.get("/sensors")
async def get_sensors(request: Request):
    return request.app.state.simulator.get_sensors_metadata()

@router.post("/fault/{sensor_id}")
async def trigger_fault(request: Request, sensor_id: str, payload: FaultRequest):
    try:
        request.app.state.simulator.trigger_fault(sensor_id, payload.target_multiplier)
        return {"message": f"Fault triggered on {sensor_id}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/fault/{sensor_id}")
async def resolve_fault(request: Request, sensor_id: str):
    request.app.state.simulator.resolve_fault(sensor_id)
    return {"message": f"Fault resolved on {sensor_id}"}

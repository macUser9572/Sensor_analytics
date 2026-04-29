from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field


router = APIRouter(prefix="/simulator", tags=["simulator"])


class FaultRequest(BaseModel):
    target_multiplier: float = Field(default=1.2, gt=0)


def _simulator(request: Request):
    simulator = getattr(request.app.state, "simulator", None)
    if simulator is None:
        raise HTTPException(status_code=503, detail="Simulator service is not running")
    return simulator


@router.get("/readings")
async def get_readings(request: Request):
    return [asdict(reading) for reading in _simulator(request).get_current_readings()]


@router.get("/sensors")
async def get_sensors(request: Request):
    return [asdict(sensor) for sensor in _simulator(request).sensors]


@router.post("/fault/{sensor_id}")
async def trigger_fault(request: Request, sensor_id: str, payload: FaultRequest):
    simulator = _simulator(request)
    try:
        simulator.trigger_fault(sensor_id, payload.target_multiplier)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "status": "ok",
        "sensor_id": sensor_id,
        "target_multiplier": payload.target_multiplier,
    }


@router.delete("/fault/{sensor_id}")
async def resolve_fault(request: Request, sensor_id: str):
    _simulator(request).resolve_fault(sensor_id)
    return {"status": "ok", "sensor_id": sensor_id}


@router.post("/fault/sensor-kill/{sensor_id}")
async def kill_sensor(request: Request, sensor_id: str):
    simulator = _simulator(request)
    try:
        simulator.kill_sensor(sensor_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "ok", "sensor_id": sensor_id, "publishing": "stopped"}


@router.delete("/fault/sensor-kill/{sensor_id}")
async def revive_sensor(request: Request, sensor_id: str):
    _simulator(request).revive_sensor(sensor_id)
    return {"status": "ok", "sensor_id": sensor_id, "publishing": "resumed"}


@router.get("/faults")
async def get_faults(request: Request):
    return _simulator(request).get_active_faults()

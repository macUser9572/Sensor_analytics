import json
from dataclasses import asdict
from datetime import datetime, timezone

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


@router.delete("/fault")
async def resolve_all_faults(request: Request):
    simulator = _simulator(request)
    resolved = simulator.resolve_all_faults()

    alert_engine = getattr(request.app.state, "alert_engine", None)
    if alert_engine:
        to_resolve = [
            sid for sid, a in list(alert_engine.active_alerts.items())
            if alert_engine._is_threshold_alert(a)
        ]
        for sensor_id in to_resolve:
            await alert_engine._resolve_alert(sensor_id)

    return {"status": "ok", "resolved": resolved}


@router.post("/fault/sensor-kill/{sensor_id}")
async def kill_sensor(request: Request, sensor_id: str):
    simulator = _simulator(request)
    try:
        simulator.kill_sensor(sensor_id)
        await _publish_sensor_fault(request, sensor_id)
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


async def _publish_sensor_fault(request: Request, sensor_id: str) -> None:
    simulator = _simulator(request)
    snapshot = simulator.fault_snapshot(sensor_id)
    redis_client = getattr(request.app.state, "redis_client", None)
    if redis_client is not None:
        score = datetime.now(timezone.utc).timestamp()
        payload = json.dumps(
            {
                "type": "update",
                "subsystem": snapshot["subsystem"],
                "timestamp": snapshot["timestamp"],
                "readings": [snapshot],
            }
        )
        async with redis_client.pipeline(transaction=False) as pipe:
            pipe.publish(f"subsystem:{snapshot['subsystem']}", payload)
            pipe.zadd(f"sensor:{sensor_id}", {json.dumps(snapshot): score})
            pipe.zremrangebyscore(f"sensor:{sensor_id}", 0, score - 600)
            await pipe.execute()

    watchdog = getattr(request.app.state, "watchdog", None)
    if watchdog is not None:
        await watchdog._publish_and_persist_alert(
            sensor_id=sensor_id,
            alert_type="sensor_fault",
            severity="critical",
            message="Demo sensor fault: publishing stopped instantly",
            value=snapshot["value"],
            threshold=snapshot["max_threshold"],
        )
        await watchdog.mark_fault(sensor_id, quality_code="demo_sensor_fault")

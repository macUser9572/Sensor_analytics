from fastapi import APIRouter, HTTPException, Query, Request, Response

from persistence import queries


router = APIRouter(prefix="/data", tags=["persistence"])


@router.get("/sensors")
async def list_sensors(response: Response):
    response.headers["Cache-Control"] = "max-age=300"
    return await queries.list_sensors()


@router.get("/sensors/current")
async def get_current_readings(request: Request):
    return await queries.get_all_current_readings(request.app.state.redis_client)


@router.get("/sensors/compare")
async def compare_sensors(
    ids: str = Query(..., description="Comma-separated sensor IDs"),
    minutes: int = 60,
):
    _validate_minutes(minutes)
    sensor_ids = [sensor_id.strip().upper() for sensor_id in ids.split(",") if sensor_id.strip()]
    if len(sensor_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 sensor IDs are required")
    if len(sensor_ids) > 10:
        raise HTTPException(status_code=400, detail="At most 10 sensor IDs can be compared")
    if len(set(sensor_ids)) != len(sensor_ids):
        raise HTTPException(status_code=400, detail="Sensor IDs must be unique")

    existing = await queries.sensor_ids_exist(sensor_ids)
    missing = sorted(set(sensor_ids) - existing)
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown sensor IDs: {', '.join(missing)}")

    return await queries.get_sensor_compare(sensor_ids, minutes)


@router.get("/sensors/{sensor_id}/history")
async def get_sensor_history(sensor_id: str, minutes: int = 60):
    _validate_minutes(minutes)
    existing = await queries.sensor_ids_exist([sensor_id.upper()])
    if sensor_id.upper() not in existing:
        raise HTTPException(status_code=404, detail=f"Unknown sensor ID: {sensor_id}")
    return await queries.get_sensor_history(sensor_id.upper(), minutes)


@router.get("/subsystems/{subsystem}/summary")
async def get_subsystem_summary(subsystem: str, minutes: int = 60):
    _validate_minutes(minutes)
    return await queries.get_subsystem_summary(subsystem, minutes)


def _validate_minutes(minutes: int) -> None:
    if minutes <= 0:
        raise HTTPException(status_code=400, detail="minutes must be greater than 0")
    if minutes > 1440:
        raise HTTPException(status_code=400, detail="minutes cannot exceed 1440 (24 hours)")

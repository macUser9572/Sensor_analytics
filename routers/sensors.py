from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from database import AsyncSessionLocal
from simulator.registry import generate_sensor_registry


router = APIRouter(prefix="/sensors", tags=["sensors"])
_registry = {sensor.id: sensor for sensor in generate_sensor_registry()}


@router.get("/{sensor_id}/health")
async def get_sensor_health(sensor_id: str):
    meta = _registry.get(sensor_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Sensor {sensor_id} not found")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(
                """
                SELECT sensor_id, last_seen, status, quality_code, updated_at
                FROM sensor_health
                WHERE sensor_id = :sensor_id
                """
            ),
            {"sensor_id": sensor_id},
        )
        row = result.mappings().first()

    if row is None:
        return {
            "sensor_id": sensor_id,
            "name": meta.name,
            "status": "unknown",
            "quality_code": None,
            "last_seen": None,
            "silence_seconds": None,
        }

    last_seen = row["last_seen"]
    if last_seen and last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=UTC)

    silence_seconds = None
    if last_seen:
        silence_seconds = (datetime.now(UTC) - last_seen).total_seconds()

    return {
        "sensor_id": sensor_id,
        "name": meta.name,
        "status": row["status"],
        "quality_code": row["quality_code"],
        "last_seen": last_seen.isoformat().replace("+00:00", "Z") if last_seen else None,
        "silence_seconds": round(silence_seconds, 1) if silence_seconds is not None else None,
    }

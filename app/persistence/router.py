from fastapi import APIRouter
from app.persistence import queries
from app.database import engine
from sqlalchemy import text

router = APIRouter(prefix="/data", tags=["persistence"])

@router.get("/sensors")
async def list_sensors():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT * FROM sensors ORDER BY id"))
        return [dict(row._mapping) for row in result.fetchall()]

@router.get("/sensors/current")
async def get_current_readings():
    return await queries.get_all_current_readings()

@router.get("/sensors/{sensor_id}/history")
async def get_sensor_history(sensor_id: str, minutes: int = 60):
    return await queries.get_sensor_history(sensor_id, minutes)

@router.get("/subsystems/{subsystem}/summary")
async def get_subsystem_summary(subsystem: str, minutes: int = 60):
    return await queries.get_subsystem_summary(subsystem, minutes)

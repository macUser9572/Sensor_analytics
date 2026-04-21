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

from fastapi import HTTPException
from fastapi.responses import Response
import csv
import io

@router.get("/export")
async def export_data(start_date: str, end_date: str):
    data = await queries.get_export_data(start_date, end_date)
    if not data:
        raise HTTPException(status_code=404, detail="timeline is not matching")
        
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["time", "sensor_id", "value"])
    for row in data:
        writer.writerow([row["time"], row["sensor_id"], row["value"]])
        
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=export_{start_date}_to_{end_date}.csv"}
    )

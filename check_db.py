import asyncio
from sqlalchemy import text
from app.database import engine

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, sensor_id, value, threshold, severity, fired_at FROM alerts WHERE sensor_id = 'T003' ORDER BY fired_at DESC"))
        rows = result.fetchall()
        print(f"Total rows for T003: {len(rows)}")
        for r in rows:
            print(f"Row: {r.id}, {r.sensor_id}, {r.value}, {r.threshold}, {r.severity}, {r.fired_at}")
            
asyncio.run(check())

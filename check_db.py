import asyncio
from app.database import engine
from sqlalchemy import text

async def inspect():
    async with engine.connect() as conn:
        stmt = text("SELECT time, sensor_id, value FROM readings ORDER BY time DESC LIMIT 5")
        result = await conn.execute(stmt)
        rows = result.fetchall()
        print("LATEST READINGS:")
        for r in rows:
            print(f"{r.time} (Type: {type(r.time)}) - Sensor: {r.sensor_id} - Value: {r.value}")

        stmt2 = text("SELECT count(*) FROM readings")
        res2 = await conn.execute(stmt2)
        print(f"Total count: {res2.scalar()}")

if __name__ == "__main__":
    asyncio.run(inspect())

"""
sensors.py – Placeholder router for sensor CRUD operations.

Will be fleshed out in the next iteration with:
  - GET  /sensors          (list all)
  - GET  /sensors/{id}     (single sensor)
  - POST /sensors          (register new sensor)
"""

from fastapi import APIRouter

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.get("/")
async def list_sensors():
    """Returns a placeholder response until the sensor service is built."""
    return {"message": "sensor list – coming soon"}

"""
alerts.py – Placeholder router for alert operations.

Will be fleshed out in the next iteration with:
  - GET  /alerts           (list active alerts)
  - POST /alerts/{id}/ack  (acknowledge an alert)
"""

from fastapi import APIRouter

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/")
async def list_alerts():
    """Returns a placeholder response until the alert service is built."""
    return {"message": "alert list – coming soon"}

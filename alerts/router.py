from datetime import timezone

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import text

from database import AsyncSessionLocal


router = APIRouter(prefix="/alerts", tags=["alerts"])
compat_router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


async def list_alerts_impl(
    acknowledged: bool = False,
    limit: int = 50,
    alert_type: str = "all",
) -> list[dict]:
    if limit <= 0 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 500")
    if alert_type not in {"all", "threshold", "sensor"}:
        raise HTTPException(status_code=400, detail="alert_type must be all, threshold, or sensor")

    query = """
        SELECT
            a.id::text AS id,
            a.sensor_id,
            s.name AS sensor_name,
            s.subsystem,
            a.value,
            a.threshold,
            s.unit,
            a.alert_type,
            a.severity,
            a.message,
            a.fired_at,
            a.resolved_at,
            a.acknowledged
        FROM alerts a
        LEFT JOIN sensors s ON s.id = a.sensor_id
        WHERE a.acknowledged = :acknowledged
    """
    params = {"acknowledged": acknowledged, "limit": limit}

    if alert_type == "threshold":
        query += " AND a.alert_type IN ('warning_threshold', 'critical_threshold')"
    elif alert_type == "sensor":
        query += " AND a.alert_type NOT IN ('warning_threshold', 'critical_threshold')"

    query += " ORDER BY a.fired_at DESC LIMIT :limit"

    async with AsyncSessionLocal() as session:
        result = await session.execute(text(query), params)
        return [_serialize_alert(dict(row._mapping)) for row in result]


async def active_alerts_impl(request: Request) -> list[dict]:
    return sorted(
        request.app.state.alert_engine.active_alerts.values(),
        key=lambda alert: alert.get("fired_at", ""),
        reverse=True,
    )


async def acknowledge_alert_impl(alert_id: str, request: Request) -> dict:
    alert = await request.app.state.alert_engine.acknowledge(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "success", "alert": alert}


async def delete_acknowledged_impl() -> dict:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(
                """
                DELETE FROM alerts
                WHERE acknowledged = TRUE
                  AND fired_at < NOW() - INTERVAL '24 hours'
                RETURNING id
                """
            )
        )
        deleted = len(result.fetchall())
        await session.commit()
    return {"deleted": deleted}


async def stats_impl(request: Request) -> dict:
    active = request.app.state.alert_engine.active_alerts.values()
    critical_active = 0
    warning_active = 0
    sensor_fault_active = 0
    sensor_missing_active = 0

    for alert in active:
        severity = alert.get("severity")
        alert_type = alert.get("alert_type")
        if severity == "critical":
            critical_active += 1
        if severity == "warning":
            warning_active += 1
        if alert_type == "sensor_fault":
            sensor_fault_active += 1
        if alert_type == "sensor_missing":
            sensor_missing_active += 1

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(
                """
                SELECT count(*) AS total_today
                FROM alerts
                WHERE fired_at >= date_trunc('day', NOW())
                """
            )
        )
        total_today = int(result.scalar_one())

    return {
        "total_today": total_today,
        "critical_active": critical_active,
        "warning_active": warning_active,
        "sensor_fault_active": sensor_fault_active,
        "sensor_missing_active": sensor_missing_active,
    }


@router.get("")
async def list_alerts(
    acknowledged: bool = False,
    limit: int = 50,
    alert_type: str = Query("all", pattern="^(all|threshold|sensor)$"),
):
    return await list_alerts_impl(acknowledged, limit, alert_type)


@router.get("/active")
async def active_alerts(request: Request):
    return await active_alerts_impl(request)


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, request: Request):
    return await acknowledge_alert_impl(alert_id, request)


@router.delete("/all-acknowledged")
async def delete_acknowledged():
    return await delete_acknowledged_impl()


@router.get("/stats")
async def alert_stats(request: Request):
    return await stats_impl(request)


@compat_router.get("")
async def compat_list_alerts(
    acknowledged: bool = False,
    limit: int = 50,
    alert_type: str = Query("all", pattern="^(all|threshold|sensor)$"),
):
    return await list_alerts_impl(acknowledged, limit, alert_type)


@compat_router.get("/active")
async def compat_active_alerts(request: Request):
    return await active_alerts_impl(request)


@compat_router.post("/{alert_id}/acknowledge")
async def compat_acknowledge_alert(alert_id: str, request: Request):
    return await acknowledge_alert_impl(alert_id, request)


@compat_router.delete("/all-acknowledged")
async def compat_delete_acknowledged():
    return await delete_acknowledged_impl()


@compat_router.get("/stats")
async def compat_alert_stats(request: Request):
    return await stats_impl(request)


def _serialize_alert(alert: dict) -> dict:
    for key in ("fired_at", "resolved_at"):
        value = alert.get(key)
        if value is not None:
            if getattr(value, "tzinfo", None) is None:
                value = value.replace(tzinfo=timezone.utc)
            alert[key] = value.isoformat()
    for key in ("value", "threshold"):
        if alert.get(key) is not None:
            alert[key] = float(alert[key])
    return alert


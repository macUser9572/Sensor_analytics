import asyncio
from datetime import UTC, datetime
from urllib.parse import urlparse

import redis.asyncio as redis
from fastapi import APIRouter
from minio import Minio
from sqlalchemy import text

from config import settings
from database import engine


router = APIRouter(tags=["health"])


async def _with_timeout(check, failure_status: str = "error"):
    try:
        return await asyncio.wait_for(check(), timeout=3)
    except Exception:
        return failure_status


async def _check_database() -> str:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return "ok"


async def _check_redis() -> str:
    client = redis.from_url(settings.redis_url(), decode_responses=True)
    try:
        await client.ping()
        return "ok"
    finally:
        await client.aclose()


async def _check_storage() -> str:
    def ping_minio() -> str:
        client = Minio(
            settings.minio_endpoint(),
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        client.list_buckets()
        return "ok"

    return await asyncio.to_thread(ping_minio)


async def _check_opc_bridge() -> str:
    parsed = urlparse(settings.expand(settings.opc_server_url))
    if not parsed.hostname or parsed.port is None:
        return "unknown"

    try:
        reader, writer = await asyncio.open_connection(parsed.hostname, parsed.port)
        writer.close()
        await writer.wait_closed()
        return "ok"
    except Exception:
        return "unknown"


@router.get("/health")
async def health_check():
    try:
        database_status, redis_status, storage_status, opc_status = await asyncio.gather(
            _with_timeout(_check_database),
            _with_timeout(_check_redis),
            _with_timeout(_check_storage),
            _with_timeout(_check_opc_bridge, failure_status="unknown"),
        )

        services = {
            "database": {"status": database_status, "host": settings.expand(settings.db_host)},
            "redis": {"status": redis_status, "host": settings.expand(settings.redis_host)},
            "storage": {"status": storage_status, "host": settings.expand(settings.minio_host)},
            "opc_bridge": {"status": opc_status},
        }
        status = "ok" if all(service["status"] == "ok" for service in services.values()) else "degraded"
    except Exception:
        services = {
            "database": {"status": "error", "host": settings.expand(settings.db_host)},
            "redis": {"status": "error", "host": settings.expand(settings.redis_host)},
            "storage": {"status": "error", "host": settings.expand(settings.minio_host)},
            "opc_bridge": {"status": "unknown"},
        }
        status = "degraded"

    return {
        "status": status,
        "services": services,
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }

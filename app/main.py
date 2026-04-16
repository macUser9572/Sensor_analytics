"""
main.py – FastAPI application entry point.

Handles:
  - Application lifespan (startup / shutdown)
  - CORS middleware
  - Router registration
  - Health-check endpoint for Redis, TimescaleDB, and MinIO
"""

from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from minio import Minio
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.routers import sensors, alerts


# ── Shared resources initialised at startup ─────────────────
redis_client: aioredis.Redis | None = None
minio_client: Minio | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application lifecycle.
    - On startup: opens Redis connection pool, creates MinIO client,
      and verifies the default bucket exists.
    - On shutdown: closes Redis pool and disposes the SQLAlchemy engine.
    """
    global redis_client, minio_client

    # ── Startup ─────────────────────────────────
    # Redis – async connection pool
    redis_client = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    # MinIO – synchronous client (official SDK has no async variant)
    minio_client = Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )

    # Ensure the default bucket exists
    if not minio_client.bucket_exists(settings.minio_bucket):
        minio_client.make_bucket(settings.minio_bucket)

    yield  # ← application runs here

    # ── Shutdown ────────────────────────────────
    if redis_client:
        await redis_client.close()
    await engine.dispose()


# ── FastAPI app instance ────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description="Real-time sensor analytics for power plant monitoring",
    version="0.1.0",
    lifespan=lifespan,
)


# ── CORS middleware ─────────────────────────────────────────
# Wide-open for the demo; lock this down for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Router registration ────────────────────────────────────
app.include_router(sensors.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")


# ── Health check ────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check():
    """
    Verifies connectivity to all backing services:
      - Redis   → PING command
      - Database → SELECT 1 via async engine
      - Storage  → MinIO bucket_exists check

    Returns a JSON object with the status of each service.
    """
    status = {
        "redis": "error",
        "database": "error",
        "storage": "error",
    }

    # ── Redis ───────────────────────────────────
    try:
        if redis_client and await redis_client.ping():
            status["redis"] = "ok"
    except Exception:
        pass

    # ── TimescaleDB ─────────────────────────────
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        status["database"] = "ok"
    except Exception:
        pass

    # ── MinIO ───────────────────────────────────
    try:
        if minio_client and minio_client.bucket_exists(settings.minio_bucket):
            status["storage"] = "ok"
    except Exception:
        pass

    return status

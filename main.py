from contextlib import asynccontextmanager
import asyncio
import logging
from uuid import uuid4

import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from alerts.engine import AlertEngine
from alerts.router import compat_router as alerts_compat_router
from alerts.router import router as alerts_router
from config import settings
from database import AsyncSessionLocal, engine, init_db
from failure.watchdog import SensorWatchdog
from persistence.batch_writer import BatchWriter
from persistence.router import router as persistence_router
from persistence.seed import insert_sensor_registry
from routers import health
from routers import opcua as opcua_router
from routers import sensors as sensors_router
from opcua.client import OPCUAClient
from opcua.handler import DataChangeHandler
from opcua.server import OPCUAServer
from simulator.router import router as simulator_router
from simulator.registry import generate_sensor_registry
from simulator.service import SimulatorService
from websocket.router import redis_subscriber, router as websocket_router


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        await insert_sensor_registry(generate_sensor_registry())
    except Exception:
        logger.exception("Database init failed; continuing service startup")

    app.state.simulator = SimulatorService()
    await app.state.simulator.start()
    app.state.opc_server = OPCUAServer(app.state.simulator)
    await app.state.opc_server.start()
    await asyncio.sleep(2)

    app.state.redis_client = redis.from_url(
        settings.redis_url(),
        decode_responses=True,
        socket_keepalive=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30,
    )
    sensor_registry = {sensor.id: sensor for sensor in app.state.simulator.registry}
    app.state.alert_engine = AlertEngine(
        app.state.redis_client,
        AsyncSessionLocal,
        sensor_registry,
    )
    await app.state.alert_engine.load_active_from_db()
    app.state.watchdog = SensorWatchdog(
        app.state.redis_client,
        AsyncSessionLocal,
        sensor_registry,
        alert_engine=app.state.alert_engine,
    )
    await app.state.watchdog.start()
    app.state.batch_writer = BatchWriter(AsyncSessionLocal)
    await app.state.batch_writer.start()
    await redis_subscriber.start(settings.redis_url())
    app.state.opc_handler = DataChangeHandler(
        app.state.redis_client,
        sensor_registry,
        watchdog=app.state.watchdog,
        db_session_factory=AsyncSessionLocal,
        batch_writer=app.state.batch_writer,
        alert_engine=app.state.alert_engine,
    )
    app.state.opc_client = OPCUAClient(app.state.opc_handler)
    await app.state.opc_client.start()

    try:
        yield
    finally:
        await redis_subscriber.stop()
        await app.state.opc_client.stop()
        await app.state.batch_writer.stop()
        await app.state.watchdog.stop()
        await app.state.opc_server.stop()
        await app.state.simulator.stop()
        await app.state.redis_client.aclose()
        await engine.dispose()


app = FastAPI(
    title="BHEL Plant Analytics API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(health.router)
app.include_router(opcua_router.router)
app.include_router(sensors_router.router)
app.include_router(simulator_router)
app.include_router(websocket_router)
app.include_router(persistence_router)
app.include_router(alerts_router)
app.include_router(alerts_compat_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.api_host, port=settings.api_port, reload=False)

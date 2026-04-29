import argparse
import asyncio
import sys
from pathlib import Path

import asyncpg
import redis
from dotenv import dotenv_values
from minio import Minio


REQUIRED_VARIABLES = [
    "M1_IP",
    "M2_IP",
    "M3_IP",
    "M4_IP",
    "OPC_PORT",
    "OPC_SERVER_URL",
    "OPC_NAMESPACE",
    "OPC_SERVER_NAME",
    "OPC_KEEPALIVE_COUNT",
    "OPC_PUBLISH_INTERVAL_MS",
    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_PASSWORD",
    "REDIS_BUFFER_SECONDS",
    "API_HOST",
    "API_PORT",
    "API_CORS_ORIGINS",
    "JWT_SECRET",
    "JWT_ALGORITHM",
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DATABASE_URL",
    "MINIO_HOST",
    "MINIO_PORT",
    "MINIO_ACCESS_KEY",
    "MINIO_SECRET_KEY",
    "MINIO_BUCKET",
    "SIMULATOR_TICK_MS",
    "FAULT_RAMP_STEP",
    "WARNING_THRESHOLD_PCT",
    "CRITICAL_THRESHOLD_PCT",
    "WATCHDOG_TIMEOUT_SECONDS",
    "WATCHDOG_CHECK_INTERVAL_SECONDS",
    "BATCH_FLUSH_INTERVAL_SECONDS",
    "REACT_API_BASE_URL",
    "REACT_WS_URL",
    "FLUTTER_API_BASE_URL",
    "FLUTTER_WS_URL",
]


def load_env() -> dict[str, str]:
    env_path = Path(".env")
    if not env_path.exists():
        raise FileNotFoundError("Missing .env. Copy .env.example to .env and set real LAN IPs.")

    values = {key: value or "" for key, value in dotenv_values(env_path, interpolate=True).items()}
    for key in ("REDIS_HOST", "DB_HOST", "MINIO_HOST"):
        values[key] = values.get(key, "").replace("${M2_IP}", values.get("M2_IP", ""))
        values[key] = values[key].replace("${M3_IP}", values.get("M3_IP", ""))
    values["OPC_SERVER_URL"] = values.get("OPC_SERVER_URL", "").replace(
        "${OPC_PORT}", values.get("OPC_PORT", "")
    )
    return values


def validate_required(values: dict[str, str]) -> list[str]:
    missing = []
    for key in REQUIRED_VARIABLES:
        if key == "REDIS_PASSWORD":
            continue
        if not values.get(key):
            missing.append(key)
    return missing


def check_redis(values: dict[str, str]) -> tuple[str, str, str, str]:
    host = values["REDIS_HOST"]
    port = values["REDIS_PORT"]
    try:
        client = redis.Redis(
            host=host,
            port=int(port),
            password=values.get("REDIS_PASSWORD") or None,
            socket_connect_timeout=3,
            socket_timeout=3,
            decode_responses=True,
        )
        client.ping()
        return ("redis", host, port, "OK")
    except Exception as exc:
        return ("redis", host, port, f"FAIL ({exc})")


async def check_timescaledb(values: dict[str, str]) -> tuple[str, str, str, str]:
    host = values["DB_HOST"]
    port = values["DB_PORT"]
    try:
        conn = await asyncpg.connect(
            host=host,
            port=int(port),
            user=values["DB_USER"],
            password=values["DB_PASSWORD"],
            database=values["DB_NAME"],
            timeout=3,
        )
        await conn.execute("SELECT 1")
        await conn.close()
        return ("timescaledb", host, port, "OK")
    except Exception as exc:
        return ("timescaledb", host, port, f"FAIL ({exc})")


def check_minio(values: dict[str, str]) -> tuple[str, str, str, str]:
    host = values["MINIO_HOST"]
    port = values["MINIO_PORT"]
    try:
        client = Minio(
            f"{host}:{port}",
            access_key=values["MINIO_ACCESS_KEY"],
            secret_key=values["MINIO_SECRET_KEY"],
            secure=values.get("MINIO_SECURE", "false").lower() == "true",
        )
        client.list_buckets()
        return ("minio", host, port, "OK")
    except Exception as exc:
        return ("minio", host, port, f"FAIL ({exc})")


def print_table(rows: list[tuple[str, str, str, str]]) -> None:
    headers = ("service", "IP", "port", "status")
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(str(value)))

    def fmt(row: tuple[str, str, str, str]) -> str:
        return " | ".join(str(value).ljust(widths[index]) for index, value in enumerate(row))

    print(fmt(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(fmt(row))


async def main() -> int:
    parser = argparse.ArgumentParser(description="Validate BHEL LAN deployment environment.")
    parser.add_argument("--service", choices=["redis", "timescaledb", "minio"], help="Check one service only.")
    args = parser.parse_args()

    try:
        values = load_env()
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1

    missing = validate_required(values)
    if missing:
        print("Missing required variables:")
        for key in missing:
            print(f"- {key}")
        return 1

    checks = {
        "redis": lambda: check_redis(values),
        "timescaledb": lambda: check_timescaledb(values),
        "minio": lambda: check_minio(values),
    }

    names = [args.service] if args.service else ["redis", "timescaledb", "minio"]
    rows = []
    for name in names:
        result = checks[name]()
        if asyncio.iscoroutine(result):
            result = await result
        rows.append(result)

    print_table(rows)
    return 0 if all(row[3] == "OK" for row in rows) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

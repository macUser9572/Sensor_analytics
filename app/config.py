"""
config.py – Centralised application settings.

Uses pydantic-settings to read from the .env file and environment
variables. Every service connection string is derived here so the
rest of the codebase never reads os.environ directly.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Reads configuration from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore env vars we don't declare
    )

    # ── App ─────────────────────────────────────
    app_name: str = "SensorAnalytics"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ── TimescaleDB / PostgreSQL ────────────────
    postgres_user: str = "sensor_admin"
    postgres_password: str = "sensor_pass_2026"
    postgres_db: str = "sensor_analytics"
    postgres_host: str = "timescaledb"
    postgres_port: int = 5432
    database_url: str = (
        "postgresql+asyncpg://sensor_admin:sensor_pass_2026"
        "@timescaledb:5432/sensor_analytics"
    )

    # ── Redis ───────────────────────────────────
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_url: str = "redis://redis:6379/0"

    # ── MinIO ───────────────────────────────────
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minio_admin"
    minio_secret_key: str = "minio_pass_2026"
    minio_secure: bool = False
    minio_bucket: str = "sensor-data"


# Singleton instance – import this wherever settings are needed
settings = Settings()

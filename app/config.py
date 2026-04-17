"""
config.py – Centralised application settings.

Uses pydantic-settings to read from the .env file and environment
variables. Every service connection string is derived here so the
rest of the codebase never reads os.environ directly.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Reads configuration from environment variables / .env file.

    All values are sourced from the .env file – no credentials are
    hardcoded here.  Fields without a default are **required** and
    will raise a validation error at startup if missing from .env.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore env vars we don't declare
    )

    # ── App ─────────────────────────────────────
    app_name: str
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ── TimescaleDB / PostgreSQL ────────────────
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int = 5432
    database_url: str

    # ── Redis ───────────────────────────────────
    redis_host: str
    redis_port: int = 6379
    redis_url: str

    # ── MinIO ───────────────────────────────────
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_secure: bool = False
    minio_bucket: str


# Singleton instance – import this wherever settings are needed
settings = Settings()

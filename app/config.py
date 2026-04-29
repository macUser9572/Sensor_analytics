"""
Central settings for every backend service.

All network addresses and service ports are loaded from environment variables
or `.env`. Application code should import the `settings` singleton and derive
service URLs through its helper methods.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Machine IPs
    m1_ip: str = Field(alias="M1_IP")
    m2_ip: str = Field(alias="M2_IP")
    m3_ip: str = Field(alias="M3_IP")
    m4_ip: str = Field(alias="M4_IP")

    # OPC-UA
    opc_server_url: str = Field(alias="OPC_SERVER_URL")
    opc_port: int = Field(alias="OPC_PORT")
    opc_namespace: str = Field(alias="OPC_NAMESPACE")
    opc_server_name: str = Field(alias="OPC_SERVER_NAME")
    opc_keepalive_count: int = Field(alias="OPC_KEEPALIVE_COUNT")
    opc_publish_interval_ms: int = Field(alias="OPC_PUBLISH_INTERVAL_MS")

    # Redis
    redis_host: str = Field(alias="REDIS_HOST")
    redis_port: int = Field(alias="REDIS_PORT")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")
    redis_buffer_seconds: int = Field(alias="REDIS_BUFFER_SECONDS")

    # FastAPI
    api_host: str = Field(alias="API_HOST")
    api_port: int = Field(alias="API_PORT")
    api_cors_origins: str = Field(alias="API_CORS_ORIGINS")
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(alias="JWT_ALGORITHM")
    app_name: str = Field(alias="APP_NAME")
    app_env: str = Field(alias="APP_ENV")
    app_debug: bool = Field(alias="APP_DEBUG")

    # TimescaleDB
    db_host: str = Field(alias="DB_HOST")
    db_port: int = Field(alias="DB_PORT")
    db_name: str = Field(alias="DB_NAME")
    db_user: str = Field(alias="DB_USER")
    db_password: str = Field(alias="DB_PASSWORD")
    database_url: str = Field(alias="DATABASE_URL")

    # MinIO
    minio_host: str = Field(alias="MINIO_HOST")
    minio_port: int = Field(alias="MINIO_PORT")
    minio_console_port: int = Field(alias="MINIO_CONSOLE_PORT")
    minio_access_key: str = Field(alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(alias="MINIO_BUCKET")
    minio_secure: bool = Field(alias="MINIO_SECURE")

    # Simulator
    simulator_tick_ms: int = Field(alias="SIMULATOR_TICK_MS")
    fault_ramp_step: float = Field(alias="FAULT_RAMP_STEP")

    # Alert thresholds
    warning_threshold_pct: float = Field(alias="WARNING_THRESHOLD_PCT")
    critical_threshold_pct: float = Field(alias="CRITICAL_THRESHOLD_PCT")
    watchdog_timeout_seconds: int = Field(alias="WATCHDOG_TIMEOUT_SECONDS")
    watchdog_check_interval_seconds: int = Field(alias="WATCHDOG_CHECK_INTERVAL_SECONDS")

    # Batch writer
    batch_flush_interval_seconds: int = Field(alias="BATCH_FLUSH_INTERVAL_SECONDS")

    # Client URLs
    react_api_base_url: str = Field(alias="REACT_API_BASE_URL")
    react_ws_url: str = Field(alias="REACT_WS_URL")
    flutter_api_base_url: str = Field(alias="FLUTTER_API_BASE_URL")
    flutter_ws_url: str = Field(alias="FLUTTER_WS_URL")

    def expand(self, value: str) -> str:
        replacements = {
            "${M1_IP}": self.m1_ip,
            "${M2_IP}": self.m2_ip,
            "${M3_IP}": self.m3_ip,
            "${M4_IP}": self.m4_ip,
            "${OPC_PORT}": str(self.opc_port),
            "${DB_USER}": self.db_user,
            "${DB_PASSWORD}": self.db_password,
            "${DB_PORT}": str(self.db_port),
            "${DB_NAME}": self.db_name,
        }
        for token, replacement in replacements.items():
            value = value.replace(token, replacement)
        return value

    def _expand(self, value: str) -> str:
        return self.expand(value)

    def redis_url(self) -> str:
        redis_host = self.expand(self.redis_host)
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{redis_host}:{self.redis_port}"

    def db_url(self) -> str:
        return self.expand(self.database_url)

    def minio_endpoint(self) -> str:
        return f"{self.expand(self.minio_host)}:{self.minio_port}"

    def opc_bind_url(self) -> str:
        return f"opc.tcp://{self.api_host}:{self.opc_port}"

    @property
    def OPC_PORT(self) -> int:
        return self.opc_port

    @property
    def OPC_SERVER_URL(self) -> str:
        return self.expand(self.opc_server_url)

    @property
    def OPC_SERVER_NAME(self) -> str:
        return self.opc_server_name

    @property
    def OPC_NAMESPACE(self) -> str:
        return self.opc_namespace

    @property
    def OPC_KEEPALIVE_COUNT(self) -> int:
        return self.opc_keepalive_count

    @property
    def SIMULATOR_TICK_MS(self) -> int:
        return self.simulator_tick_ms

    @property
    def REDIS_HOST(self) -> str:
        return self.expand(self.redis_host)

    def cors_origins(self) -> list[str]:
        return [self.expand(origin.strip()) for origin in self.api_cors_origins.split(",") if origin.strip()]


settings = Settings()

"""
database.py – Async SQLAlchemy engine and session management.

Provides:
  - `engine`       : the async engine bound to TimescaleDB
  - `async_session` : session factory
  - `get_db()`     : FastAPI dependency that yields a session
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

# ── Async engine ────────────────────────────────────────────
# Creates a connection pool to TimescaleDB using asyncpg.
engine = create_async_engine(
    settings.db_url(),
    echo=settings.app_debug,   # log SQL in dev mode
    pool_size=20,              # suitable for 500-sensor workload
    max_overflow=10,
    pool_pre_ping=True,        # verify connections before use
)

# ── Session factory ─────────────────────────────────────────
# Each call produces an independent async session.
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides an async database session.
    Automatically closes the session when the request finishes.
    """
    async with async_session() as session:
        yield session

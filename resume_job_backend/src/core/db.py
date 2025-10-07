from typing import Any, Iterable, Optional
import anyio
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from src.core.config import settings

_pool: Optional[ConnectionPool] = None


def _ensure_pool():
    global _pool
    if _pool is not None:
        return
    dsn = settings.get_db_dsn()
    if not dsn:
        raise RuntimeError("Database configuration missing. Please set POSTGRES_URL or individual POSTGRES_* vars.")
    # Create a small pool
    _pool = ConnectionPool(
        conninfo=dsn,
        kwargs={"autocommit": True},
        min_size=1,
        max_size=10,
        timeout=30,
        configure=lambda conn: conn.execute("SET application_name = 'resume_job_backend'"),
    )


def _sync_query(sql: str, params: Optional[Iterable[Any]] = None, fetch_one: bool = False):
    _ensure_pool()
    assert _pool is not None
    with _pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params or ())
            if fetch_one:
                row = cur.fetchone()
                return row
            rows = cur.fetchall()
            return rows


def _sync_execute(sql: str, params: Optional[Iterable[Any]] = None) -> int:
    _ensure_pool()
    assert _pool is not None
    with _pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.rowcount


# PUBLIC_INTERFACE
async def db_query(sql: str, params: Optional[Iterable[Any]] = None, fetch_one: bool = False):
    """Run a SELECT or RETURNING statement. Returns dict row(s)."""
    return await anyio.to_thread.run_sync(_sync_query, sql, params, fetch_one)


# PUBLIC_INTERFACE
async def db_execute(sql: str, params: Optional[Iterable[Any]] = None) -> int:
    """Run INSERT/UPDATE/DELETE without returning rows."""
    return await anyio.to_thread.run_sync(_sync_execute, sql, params)

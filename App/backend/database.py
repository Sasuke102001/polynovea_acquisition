"""
database.py
Async PostgreSQL connection pool via asyncpg.
Two pools: M2 (primary) + M3 (read-only, for tiered demo).
"""

import asyncpg
import json
import os
import ssl

_pool: asyncpg.Pool | None = None      # M2 primary pool
_m3_pool: asyncpg.Pool | None = None   # M3 read-only pool


async def _setup_connection(conn: asyncpg.Connection) -> None:
    """Register JSON/JSONB codecs so asyncpg returns Python objects, not raw strings."""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def init_pool() -> None:
    global _pool
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    _pool = await asyncpg.create_pool(
        host=os.getenv("PG_HOST"),
        port=int(os.getenv("PG_PORT", 5432)),
        database=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        ssl=ssl_ctx,
        min_size=2,
        max_size=10,
        command_timeout=30,
        init=_setup_connection,
    )


async def init_m3_pool() -> None:
    """Initialize M3 read-only pool for tiered demo (demo_level >= 2)."""
    global _m3_pool

    # Check if M3 credentials are configured
    m3_host = os.getenv("M3_PG_HOST")
    if not m3_host:
        # M3 optional — graceful degradation if not configured
        return

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    try:
        _m3_pool = await asyncpg.create_pool(
            host=m3_host,
            port=int(os.getenv("M3_PG_PORT", 5432)),
            database=os.getenv("M3_PG_DB"),
            user=os.getenv("M3_PG_USER"),
            password=os.getenv("M3_PG_PASSWORD"),
            ssl=ssl_ctx,
            min_size=1,
            max_size=5,
            command_timeout=30,
            init=_setup_connection,
        )
        print("[DB] M3 pool initialized successfully")
    except Exception as e:
        print(f"[DB] Warning: M3 pool failed to initialize — tiered demo level 2/3 unavailable: {e}")


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def close_m3_pool() -> None:
    global _m3_pool
    if _m3_pool:
        await _m3_pool.close()
        _m3_pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialised. Call init_pool() first.")
    return _pool


def get_m3_pool() -> asyncpg.Pool | None:
    """Get M3 pool. Returns None if not configured."""
    return _m3_pool

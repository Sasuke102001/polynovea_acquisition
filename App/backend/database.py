"""
database.py
Async PostgreSQL connection pool via asyncpg.
"""

import asyncpg
import json
import os
import ssl

_pool: asyncpg.Pool | None = None


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


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialised. Call init_pool() first.")
    return _pool



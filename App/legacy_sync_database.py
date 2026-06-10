"""
database.py
Thread-safe psycopg2 connection pool.
One pool per process, initialized at startup, closed at shutdown.
"""

import os
import psycopg2
import psycopg2.pool
import psycopg2.extras
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

_pool: psycopg2.pool.ThreadedConnectionPool | None = None


def _db_config() -> dict:
    return {
        'host':     os.getenv('PG_HOST',     'localhost'),
        'port':     int(os.getenv('PG_PORT', 5432)),
        'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
        'user':     os.getenv('PG_USER',     'polynovea_admin'),
        'password': os.getenv('PG_PASSWORD', ''),
        'sslmode':  'require',
    }


def init_pool() -> None:
    global _pool
    cfg = _db_config()
    min_conn = int(os.getenv('PG_POOL_MIN', 2))
    max_conn = int(os.getenv('PG_POOL_MAX', 10))
    _pool = psycopg2.pool.ThreadedConnectionPool(min_conn, max_conn, **cfg)


def close_pool() -> None:
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None


@contextmanager
def get_cursor(cursor_factory=psycopg2.extras.RealDictCursor):
    """Context manager: yields a dict-cursor, returns conn to pool on exit."""
    assert _pool is not None, 'DB pool not initialised — call init_pool() first'
    conn = _pool.getconn()
    try:
        with conn.cursor(cursor_factory=cursor_factory) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)

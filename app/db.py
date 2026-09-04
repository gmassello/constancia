from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.config import get_settings

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.sql"

_pool: AsyncConnectionPool | None = None


async def pool() -> AsyncConnectionPool:
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(get_settings().database_url, min_size=1, max_size=8, open=False)
        await _pool.open()
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def fetch(sql: str, params: Any = None) -> list[dict]:
    connections = await pool()
    async with connections.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(sql, params)
        return await cur.fetchall()


async def fetch_one(sql: str, params: Any = None) -> dict | None:
    rows = await fetch(sql, params)
    return rows[0] if rows else None


async def execute(sql: str, params: Any = None) -> None:
    connections = await pool()
    async with connections.connection() as conn, conn.cursor() as cur:
        await cur.execute(sql, params)


def to_vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(f"{v:.7f}" for v in embedding) + "]"


def init_schema() -> None:
    with psycopg.connect(get_settings().database_url, autocommit=True) as conn:
        conn.execute(SCHEMA_PATH.read_text())


if __name__ == "__main__":
    init_schema()
    print("schema ready")

from collections.abc import AsyncGenerator
from typing import Any

import asyncpg
from asyncpg import Pool

from app.config import Settings

pool: Pool | None = None
DatabaseConnection = Any


async def init_pool(settings: Settings) -> Pool:
    global pool

    if pool is None:
        pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=settings.db_pool_min,
            max_size=settings.db_pool_max,
        )

    return pool


async def close_pool() -> None:
    global pool

    if pool is not None:
        await pool.close()
        pool = None


async def get_connection() -> AsyncGenerator[DatabaseConnection, None]:
    if pool is None:
        raise RuntimeError("Database pool is not initialized.")

    async with pool.acquire() as connection:
        yield connection

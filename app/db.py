from collections.abc import AsyncGenerator, Mapping, Sequence
from typing import Protocol, cast

import asyncpg
from asyncpg import Pool, Record

from app.config import Settings

pool: Pool | None = None


class DatabaseConnection(Protocol):
    async def fetchrow(
        self,
        query: str,
        *args: object,
    ) -> Record | Mapping[str, object] | None: ...

    async def fetch(
        self,
        query: str,
        *args: object,
    ) -> Sequence[Record | Mapping[str, object]]: ...

    async def fetchval(
        self,
        query: str,
        *args: object,
    ) -> object: ...


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
        yield cast(DatabaseConnection, connection)

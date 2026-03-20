from __future__ import annotations

from asyncio import run
from pathlib import Path
from typing import Protocol, cast

from asyncpg import Pool

from app.config import get_settings
from app.db import close_pool, init_pool
from app.logging import configure_logging

INIT_SQL_PATH = Path(__file__).resolve().parent.parent / "init.sql"
BOOTSTRAP_LOCK_ID = 2_404_202_603_19


class BootstrapConnection(Protocol):
    async def execute(self, query: str, *args: object) -> str: ...

    async def fetchval(self, query: str, *args: object) -> object: ...


async def initialize_database(connection: BootstrapConnection) -> None:
    schema_sql = INIT_SQL_PATH.read_text(encoding="utf-8")
    await connection.fetchval("SELECT pg_advisory_lock($1)", BOOTSTRAP_LOCK_ID)
    try:
        await connection.execute(schema_sql)
    finally:
        await connection.fetchval("SELECT pg_advisory_unlock($1)", BOOTSTRAP_LOCK_ID)


async def initialize_database_pool(pool: Pool) -> None:
    async with pool.acquire() as connection:
        await initialize_database(cast(BootstrapConnection, connection))


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    pool = await init_pool(settings)
    try:
        await initialize_database_pool(pool)
    finally:
        await close_pool()


if __name__ == "__main__":
    run(main())

# ruff: noqa: E402

from __future__ import annotations

import asyncio
import os
import re
from collections.abc import Awaitable, Callable, Coroutine, Generator
from dataclasses import dataclass
from datetime import date, datetime
from json import dumps
from pathlib import Path
from typing import TypeVar
from urllib.parse import SplitResult, urlsplit, urlunsplit
from uuid import UUID

import asyncpg
import pytest
from asyncpg import Connection, Record
from fastapi.testclient import TestClient

DEFAULT_TEST_DATABASE_URL = "postgresql://signaldesk:signaldesk@localhost:5432/signaldesk_test"
os.environ.setdefault("DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
os.environ.setdefault("JWT_SECRET", "test-secret")

import signaldesk.config as config_module
import signaldesk.main as main_module
from signaldesk.config import Settings
from signaldesk.main import app
from signaldesk.middleware import limiter

INIT_SQL_PATH = Path(__file__).resolve().parent.parent / "init.sql"
T = TypeVar("T")


def run_async[T](awaitable: Coroutine[object, object, T]) -> T:
    return asyncio.run(awaitable)


def clear_database_schema(database_url: str) -> None:
    run_async(_clear_schema(database_url))


def _split_database_url(database_url: str) -> SplitResult:
    parsed = urlsplit(database_url)
    if not parsed.scheme or not parsed.netloc or not parsed.path:
        raise RuntimeError(f"Invalid DATABASE_URL for tests: {database_url!r}")
    return parsed


def _database_name(database_url: str) -> str:
    name = _split_database_url(database_url).path.lstrip("/")
    if not name:
        raise RuntimeError("DATABASE_URL must include a database name for tests.")
    return name


def _admin_database_url(database_url: str) -> str:
    parsed = _split_database_url(database_url)
    return urlunsplit(parsed._replace(path="/postgres"))


def _validate_test_database_name(database_name: str) -> None:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", database_name):
        raise RuntimeError(f"Unsafe test database name: {database_name!r}")
    if not database_name.endswith("_test"):
        raise RuntimeError(
            f"Refusing to run tests against non-test database {database_name!r}. "
            "Set DATABASE_URL to a dedicated *_test database.",
        )


async def _ensure_test_database_exists(database_url: str) -> None:
    database_name = _database_name(database_url)
    _validate_test_database_name(database_name)

    admin_connection = await asyncpg.connect(_admin_database_url(database_url))
    try:
        exists = await admin_connection.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            database_name,
        )
        if exists is None:
            await admin_connection.execute(f'CREATE DATABASE "{database_name}"')
    finally:
        await admin_connection.close()


async def _reset_schema(database_url: str) -> None:
    connection = await asyncpg.connect(database_url)
    try:
        await connection.execute("DROP SCHEMA IF EXISTS public CASCADE")
        await connection.execute("CREATE SCHEMA public")
        await connection.execute(INIT_SQL_PATH.read_text())
    finally:
        await connection.close()


async def _clear_schema(database_url: str) -> None:
    connection = await asyncpg.connect(database_url)
    try:
        await connection.execute("DROP SCHEMA IF EXISTS public CASCADE")
        await connection.execute("CREATE SCHEMA public")
    finally:
        await connection.close()


async def _truncate_test_data(database_url: str) -> None:
    connection = await asyncpg.connect(database_url)
    try:
        await connection.execute("TRUNCATE TABLE ai_summaries, feedback RESTART IDENTITY CASCADE")
    finally:
        await connection.close()


@dataclass
class DatabaseHelper:
    database_url: str

    async def _connect(self) -> Connection:
        return await asyncpg.connect(self.database_url)

    async def _run_with_connection(
        self,
        callback: Callable[[Connection], Awaitable[T]],
    ) -> T:
        connection = await self._connect()
        try:
            return await callback(connection)
        finally:
            await connection.close()

    def run_with_connection(
        self,
        callback: Callable[[Connection], Awaitable[T]],
    ) -> T:
        return run_async(self._run_with_connection(callback))

    def execute(self, query: str, *args: object) -> str:
        async def _execute(connection: Connection) -> str:
            return await connection.execute(query, *args)

        return self.run_with_connection(_execute)

    def fetchrow(self, query: str, *args: object) -> Record | None:
        async def _fetchrow(connection: Connection) -> Record | None:
            return await connection.fetchrow(query, *args)

        return self.run_with_connection(_fetchrow)

    def fetchval(self, query: str, *args: object) -> object:
        async def _fetchval(connection: Connection) -> object:
            return await connection.fetchval(query, *args)

        return self.run_with_connection(_fetchval)

    def user_id(self, username: str) -> UUID:
        user_id = self.fetchval("SELECT id FROM users WHERE username = $1", username)
        if not isinstance(user_id, UUID):
            raise RuntimeError(f"Expected seeded user {username!r} to exist in tests.")
        return user_id

    def current_date(self) -> date:
        value = self.fetchval("SELECT CURRENT_DATE")
        if not isinstance(value, date):
            raise RuntimeError("Expected CURRENT_DATE to return a date.")
        return value

    def compute_feedback_hash(self) -> str:
        row = self.fetchrow(
            """
            SELECT md5(string_agg(id::text || updated_at::text, ',' ORDER BY id)) AS hash
            FROM feedback
            """,
        )
        if row is None:
            raise RuntimeError("Expected feedback hash query to return a row.")
        value = row["hash"]
        if not isinstance(value, str):
            raise RuntimeError("Expected feedback hash query to return a string hash.")
        return value

    def seed_feedback(
        self,
        *,
        title: str,
        description: str,
        source: str,
        priority: str,
        status: str,
        created_by: UUID,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        idempotency_key: str | None = None,
    ) -> UUID:
        async def _seed(connection: Connection) -> UUID:
            row = await connection.fetchrow(
                """
                INSERT INTO feedback (
                    title,
                    description,
                    source,
                    priority,
                    status,
                    created_by,
                    idempotency_key,
                    created_at,
                    updated_at
                )
                VALUES (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6,
                    $7,
                    COALESCE($8, now()),
                    COALESCE($9, COALESCE($8, now()))
                )
                RETURNING id
                """,
                title,
                description,
                source,
                priority,
                status,
                created_by,
                idempotency_key,
                created_at,
                updated_at,
            )
            if row is None or not isinstance(row["id"], UUID):
                raise RuntimeError("Expected seeded feedback row to return a UUID.")
            return row["id"]

        return self.run_with_connection(_seed)

    def seed_ai_summary(
        self,
        *,
        insights: list[dict[str, object]],
        feedback_hash: str,
        feedback_count: int,
        model_used: str,
        generated_at: datetime,
    ) -> UUID:
        async def _seed(connection: Connection) -> UUID:
            row = await connection.fetchrow(
                """
                INSERT INTO ai_summaries (
                    insights,
                    feedback_hash,
                    feedback_count,
                    model_used,
                    generated_at
                )
                VALUES ($1::jsonb, $2, $3, $4, $5)
                RETURNING id
                """,
                dumps(insights),
                feedback_hash,
                feedback_count,
                model_used,
                generated_at,
            )
            if row is None or not isinstance(row["id"], UUID):
                raise RuntimeError("Expected seeded AI summary row to return a UUID.")
            return row["id"]

        return self.run_with_connection(_seed)


@pytest.fixture(scope="session")
def database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_TEST_DATABASE_URL)


@pytest.fixture(scope="session", autouse=True)
def initialized_test_database(database_url: str) -> Generator[None, None, None]:
    run_async(_ensure_test_database_exists(database_url))
    run_async(_reset_schema(database_url))
    yield


@pytest.fixture(autouse=True)
def reset_test_database(
    initialized_test_database: None,
    database_url: str,
) -> Generator[None, None, None]:
    del initialized_test_database
    run_async(_truncate_test_data(database_url))
    limiter._storage.reset()
    config_module.get_settings.cache_clear()
    yield
    limiter._storage.reset()
    config_module.get_settings.cache_clear()


@pytest.fixture(autouse=True)
def seeded_test_users(
    reset_test_database: None,
    database_url: str,
) -> None:
    del reset_test_database
    import signaldesk.seed as seed_module

    seed_module.seed_default_test_users(database_url)


@pytest.fixture
def settings(database_url: str) -> Settings:
    return Settings(
        database_url=database_url,
        jwt_secret="test-secret",
    )


@pytest.fixture
def db(database_url: str) -> DatabaseHelper:
    return DatabaseHelper(database_url)


@pytest.fixture
def client(
    monkeypatch: pytest.MonkeyPatch,
    database_url: str,
    initialized_test_database: None,
) -> Generator[TestClient, None, None]:
    del initialized_test_database
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("RATE_LIMIT_DEFAULT", "60/minute")
    monkeypatch.setenv("RATE_LIMIT_LOGIN", "10/minute")
    monkeypatch.setenv("RATE_LIMIT_AI_REFRESH", "5/minute")
    config_module.get_settings.cache_clear()
    monkeypatch.setattr(main_module, "start_periodic_ai_refresh", lambda settings: None)

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        config_module.get_settings.cache_clear()

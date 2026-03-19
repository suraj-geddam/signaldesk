import sys
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from passlib.context import CryptContext

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.main as main_module
from app.config import Settings, get_settings
from app.db import get_connection
from app.main import app

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class FakeConnection:
    def __init__(self) -> None:
        created_at = datetime(2026, 3, 19, tzinfo=UTC)
        admin_id = uuid4()
        member_id = uuid4()
        self.users_by_username = {
            "admin": {
                "id": admin_id,
                "username": "admin",
                "password_hash": password_context.hash("admin123"),
                "role": "admin",
                "created_at": created_at,
            },
            "member": {
                "id": member_id,
                "username": "member",
                "password_hash": password_context.hash("member123"),
                "role": "member",
                "created_at": created_at,
            },
        }
        self.users_by_id = {
            row["id"]: {
                "id": row["id"],
                "username": row["username"],
                "role": row["role"],
                "created_at": row["created_at"],
            }
            for row in self.users_by_username.values()
        }

    async def fetchval(self, query: str, *args: object) -> int:
        del query, args
        return 1

    async def fetchrow(self, query: str, *args: object) -> dict[str, object] | None:
        normalized_query = " ".join(query.split())
        if "FROM users WHERE username = $1" in normalized_query:
            return self.users_by_username.get(str(args[0]))
        if "FROM users WHERE id = $1" in normalized_query:
            user_id = args[0]
            if isinstance(user_id, UUID):
                return self.users_by_id.get(user_id)
        return None


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    settings = Settings(
        database_url="postgresql://signaldesk:signaldesk@localhost:5432/signaldesk",
        jwt_secret="test-secret",
    )
    fake_connection = FakeConnection()

    async def fake_init_pool(settings: Settings) -> None:
        del settings

    async def fake_close_pool() -> None:
        return None

    async def override_get_connection() -> AsyncGenerator[FakeConnection, None]:
        yield fake_connection

    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    monkeypatch.setattr(main_module, "init_pool", fake_init_pool)
    monkeypatch.setattr(main_module, "close_pool", fake_close_pool)

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_connection] = override_get_connection

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()

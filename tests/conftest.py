import sys
from collections.abc import AsyncGenerator, Generator, Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TypedDict, cast
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


class UserWithPasswordDict(TypedDict):
    id: UUID
    username: str
    password_hash: str
    role: str
    created_at: datetime


class UserDict(TypedDict):
    id: UUID
    username: str
    role: str
    created_at: datetime


class FeedbackDict(TypedDict):
    id: UUID
    title: str
    description: str
    source: str
    priority: str
    status: str
    created_by: UUID
    idempotency_key: str | None
    created_at: datetime
    updated_at: datetime


class FakeConnection:
    def __init__(self) -> None:
        created_at = datetime(2026, 3, 19, tzinfo=UTC)
        admin_id = uuid4()
        member_id = uuid4()
        self._clock_tick = 0
        self.users_by_username: dict[str, UserWithPasswordDict] = {
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
        self.users_by_id: dict[UUID, UserDict] = {
            row["id"]: {
                "id": row["id"],
                "username": row["username"],
                "role": row["role"],
                "created_at": row["created_at"],
            }
            for row in self.users_by_username.values()
        }
        self.feedback_by_id: dict[UUID, FeedbackDict] = {}
        self.feedback_by_idempotency_key: dict[str, UUID] = {}

    def _next_timestamp(self) -> datetime:
        timestamp = datetime(2026, 3, 19, tzinfo=UTC) + timedelta(minutes=self._clock_tick)
        self._clock_tick += 1
        return timestamp

    def _sorted_feedback(self) -> list[FeedbackDict]:
        return sorted(
            self.feedback_by_id.values(),
            key=lambda row: (row["created_at"], row["id"]),
            reverse=True,
        )

    def _filtered_feedback(
        self,
        normalized_query: str,
        args: tuple[object, ...],
        *,
        include_paging: bool,
    ) -> list[FeedbackDict]:
        index = 0
        rows = self._sorted_feedback()

        if "status = $" in normalized_query:
            status_value = str(args[index])
            rows = [row for row in rows if row["status"] == status_value]
            index += 1
        if "priority = $" in normalized_query:
            priority_value = str(args[index])
            rows = [row for row in rows if row["priority"] == priority_value]
            index += 1
        if "source = $" in normalized_query:
            source_value = str(args[index])
            rows = [row for row in rows if row["source"] == source_value]
            index += 1
        if "(title || ' ' || description) ILIKE" in normalized_query:
            search_value = str(args[index]).strip("%").lower()
            rows = [
                row
                for row in rows
                if search_value in f"{row['title']} {row['description']}".lower()
            ]
            index += 1

        if "ORDER BY CASE priority" in normalized_query:
            priority_rank = {"high": 1, "medium": 2, "low": 3}
            reverse = "END DESC" in normalized_query
            rows = sorted(
                rows,
                key=lambda row: (priority_rank[row["priority"]], row["created_at"]),
                reverse=reverse,
            )
        elif "ORDER BY created_at ASC" in normalized_query:
            rows = sorted(rows, key=lambda row: row["created_at"])
        else:
            rows = sorted(rows, key=lambda row: row["created_at"], reverse=True)

        if include_paging:
            limit_arg = args[index]
            offset_arg = args[index + 1]
            if not isinstance(limit_arg, int) or not isinstance(offset_arg, int):
                raise AssertionError("Paging arguments must be integers")
            limit = limit_arg
            offset = offset_arg
            rows = rows[offset : offset + limit]

        return list(rows)

    async def fetchval(self, query: str, *args: object) -> object:
        normalized_query = " ".join(query.split())
        if normalized_query == "SELECT 1":
            return 1
        if normalized_query.startswith("SELECT COUNT(*) FROM feedback"):
            return len(self._filtered_feedback(normalized_query, args, include_paging=False))
        if normalized_query == "DELETE FROM feedback WHERE id = $1 RETURNING id":
            feedback_id = args[0]
            if not isinstance(feedback_id, UUID):
                return None
            row = self.feedback_by_id.pop(feedback_id, None)
            if row is None:
                return None
            idempotency_key = row["idempotency_key"]
            if isinstance(idempotency_key, str):
                self.feedback_by_idempotency_key.pop(idempotency_key, None)
            return feedback_id
        raise AssertionError(f"Unhandled fetchval query: {normalized_query}")

    async def fetchrow(
        self,
        query: str,
        *args: object,
    ) -> Mapping[str, object] | None:
        normalized_query = " ".join(query.split())
        if "FROM users WHERE username = $1" in normalized_query:
            return self.users_by_username.get(str(args[0]))
        if "FROM users WHERE id = $1" in normalized_query:
            user_id = args[0]
            if isinstance(user_id, UUID):
                return self.users_by_id.get(user_id)
        if normalized_query.startswith("INSERT INTO feedback"):
            title, description, source, priority, status, created_by, idempotency_key = args
            if not isinstance(created_by, UUID):
                raise AssertionError("created_by must be a UUID")

            if isinstance(idempotency_key, str):
                existing_id = self.feedback_by_idempotency_key.get(idempotency_key)
                if existing_id is not None:
                    return None

            feedback_id = uuid4()
            timestamp = self._next_timestamp()
            idempotency_key_value = str(idempotency_key) if idempotency_key is not None else None
            row: FeedbackDict = {
                "id": feedback_id,
                "title": str(title),
                "description": str(description),
                "source": str(source),
                "priority": str(priority),
                "status": str(status),
                "created_by": created_by,
                "idempotency_key": idempotency_key_value,
                "created_at": timestamp,
                "updated_at": timestamp,
            }
            self.feedback_by_id[feedback_id] = row
            if idempotency_key_value is not None:
                self.feedback_by_idempotency_key[idempotency_key_value] = feedback_id
            return row
        if normalized_query == "SELECT * FROM feedback WHERE idempotency_key = $1":
            feedback_id = self.feedback_by_idempotency_key.get(str(args[0]))
            if feedback_id is None:
                return None
            return self.feedback_by_id[feedback_id]
        if normalized_query == "SELECT * FROM feedback WHERE id = $1":
            feedback_id = args[0]
            if isinstance(feedback_id, UUID):
                existing_row = self.feedback_by_id.get(feedback_id)
                if existing_row is not None:
                    return existing_row
            return None
        if (
            normalized_query.startswith("UPDATE feedback SET")
            and "created_by = $7" in normalized_query
        ):
            title, description, source, priority, status, feedback_id, created_by = args
            if not isinstance(feedback_id, UUID) or not isinstance(created_by, UUID):
                return None
            existing_row = self.feedback_by_id.get(feedback_id)
            if existing_row is None or existing_row["created_by"] != created_by:
                return None
            row = existing_row
            row.update(
                title=str(title),
                description=str(description),
                source=str(source),
                priority=str(priority),
                status=str(status),
                updated_at=self._next_timestamp(),
            )
            return row
        if (
            normalized_query.startswith("UPDATE feedback SET")
            and "WHERE id = $6" in normalized_query
        ):
            title, description, source, priority, status, feedback_id = args
            if not isinstance(feedback_id, UUID):
                return None
            existing_row = self.feedback_by_id.get(feedback_id)
            if existing_row is None:
                return None
            row = existing_row
            row.update(
                title=str(title),
                description=str(description),
                source=str(source),
                priority=str(priority),
                status=str(status),
                updated_at=self._next_timestamp(),
            )
            return row
        return None

    async def fetch(self, query: str, *args: object) -> list[Mapping[str, object]]:
        normalized_query = " ".join(query.split())
        if normalized_query.startswith("SELECT * FROM feedback"):
            return [
                cast(Mapping[str, object], row)
                for row in self._filtered_feedback(normalized_query, args, include_paging=True)
            ]
        raise AssertionError(f"Unhandled fetch query: {normalized_query}")


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

from collections.abc import Mapping
from uuid import UUID

from asyncpg import Record

from app.db import DatabaseConnection
from app.schemas import UserRow, UserRowWithPassword


def _record_to_dict(record: Record | Mapping[str, object]) -> dict[str, object]:
    return dict(record.items())


async def get_user_by_username(
    connection: DatabaseConnection,
    username: str,
) -> UserRowWithPassword | None:
    row = await connection.fetchrow(
        """
        SELECT id, username, password_hash, role, created_at
        FROM users
        WHERE username = $1
        """,
        username,
    )
    if row is None:
        return None

    return UserRowWithPassword.model_validate(_record_to_dict(row))


async def get_user_by_id(
    connection: DatabaseConnection,
    user_id: UUID,
) -> UserRow | None:
    row = await connection.fetchrow(
        """
        SELECT id, username, role, created_at
        FROM users
        WHERE id = $1
        """,
        user_id,
    )
    if row is None:
        return None

    return UserRow.model_validate(_record_to_dict(row))

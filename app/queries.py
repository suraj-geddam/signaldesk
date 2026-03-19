from collections.abc import Mapping
from uuid import UUID

from asyncpg import Record

from app.db import DatabaseConnection
from app.schemas import (
    FeedbackRow,
    Priority,
    SortBy,
    SortOrder,
    Source,
    Status,
    UserRow,
    UserRowWithPassword,
)


def _record_to_dict(record: Record | Mapping[str, object]) -> dict[str, object]:
    return dict(record.items())


def _feedback_from_record(record: Record | Mapping[str, object]) -> FeedbackRow:
    return FeedbackRow.model_validate(_record_to_dict(record))


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


async def create_feedback(
    connection: DatabaseConnection,
    *,
    title: str,
    description: str,
    source: Source,
    priority: Priority,
    status: Status,
    created_by: UUID,
    idempotency_key: str | None,
) -> FeedbackRow:
    row = await connection.fetchrow(
        """
        INSERT INTO feedback (
            id, title, description, source, priority, status, created_by, idempotency_key
        )
        VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (idempotency_key) DO NOTHING
        RETURNING *
        """,
        title,
        description,
        source,
        priority,
        status,
        created_by,
        idempotency_key,
    )
    if row is None and idempotency_key is not None:
        existing_row = await connection.fetchrow(
            "SELECT * FROM feedback WHERE idempotency_key = $1",
            idempotency_key,
        )
        if existing_row is None:
            raise RuntimeError("Expected feedback row for idempotency key.")
        return _feedback_from_record(existing_row)

    if row is None:
        raise RuntimeError("Feedback insert unexpectedly returned no row.")

    return _feedback_from_record(row)


async def get_feedback_by_id(
    connection: DatabaseConnection,
    feedback_id: UUID,
) -> FeedbackRow | None:
    row = await connection.fetchrow(
        "SELECT * FROM feedback WHERE id = $1",
        feedback_id,
    )
    if row is None:
        return None

    return _feedback_from_record(row)


async def update_feedback_as_member(
    connection: DatabaseConnection,
    *,
    feedback_id: UUID,
    created_by: UUID,
    title: str,
    description: str,
    source: Source,
    priority: Priority,
    status: Status,
) -> FeedbackRow | None:
    row = await connection.fetchrow(
        """
        UPDATE feedback SET title=$1, description=$2, source=$3, priority=$4, status=$5
        WHERE id = $6 AND created_by = $7
        RETURNING *
        """,
        title,
        description,
        source,
        priority,
        status,
        feedback_id,
        created_by,
    )
    if row is None:
        return None

    return _feedback_from_record(row)


async def update_feedback_as_admin(
    connection: DatabaseConnection,
    *,
    feedback_id: UUID,
    title: str,
    description: str,
    source: Source,
    priority: Priority,
    status: Status,
) -> FeedbackRow | None:
    row = await connection.fetchrow(
        """
        UPDATE feedback SET title=$1, description=$2, source=$3, priority=$4, status=$5
        WHERE id = $6
        RETURNING *
        """,
        title,
        description,
        source,
        priority,
        status,
        feedback_id,
    )
    if row is None:
        return None

    return _feedback_from_record(row)


async def delete_feedback(
    connection: DatabaseConnection,
    feedback_id: UUID,
) -> bool:
    deleted_id = await connection.fetchval(
        "DELETE FROM feedback WHERE id = $1 RETURNING id",
        feedback_id,
    )
    return deleted_id is not None


async def list_feedback(
    connection: DatabaseConnection,
    *,
    status: Status | None = None,
    priority: Priority | None = None,
    source: Source | None = None,
    search: str | None = None,
    sort_by: SortBy = SortBy.created_at,
    sort_order: SortOrder = SortOrder.desc,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[FeedbackRow], int]:
    conditions: list[str] = []
    params: list[object] = []
    idx = 1

    if status is not None:
        conditions.append(f"status = ${idx}")
        params.append(status)
        idx += 1
    if priority is not None:
        conditions.append(f"priority = ${idx}")
        params.append(priority)
        idx += 1
    if source is not None:
        conditions.append(f"source = ${idx}")
        params.append(source)
        idx += 1
    if search:
        conditions.append(f"(title || ' ' || description) ILIKE ${idx}")
        params.append(f"%{search}%")
        idx += 1

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    if sort_by == SortBy.priority:
        direction = "ASC" if sort_order == SortOrder.asc else "DESC"
        order_expr = f"""CASE priority
            WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3
            END {direction},
            created_at DESC"""
    else:
        order_expr = f"created_at {sort_order.value.upper()}"

    total = int(
        await connection.fetchval(
            f"SELECT COUNT(*) FROM feedback {where}",
            *params,
        )
    )

    data_params = [*params, per_page, (page - 1) * per_page]
    rows = await connection.fetch(
        f"""
        SELECT * FROM feedback {where}
        ORDER BY {order_expr}
        LIMIT ${idx} OFFSET ${idx + 1}
        """,
        *data_params,
    )

    return [_feedback_from_record(row) for row in rows], total

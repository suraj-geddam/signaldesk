from collections.abc import Mapping
from datetime import date
from json import dumps, loads
from uuid import UUID

from asyncpg import Record

from signaldesk.db import DatabaseConnection
from signaldesk.schemas import (
    AiSummaryRow,
    DailyTrend,
    DashboardResponse,
    FeedbackRow,
    Insight,
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


def _count_from_value(value: object) -> int:
    if not isinstance(value, int):
        raise RuntimeError("Dashboard query returned a non-integer count value.")

    return value


def _trend_from_record(record: Record | Mapping[str, object]) -> DailyTrend:
    data = _record_to_dict(record)
    raw_date = data["date"]
    if not isinstance(raw_date, date):
        raise RuntimeError("Dashboard trend query returned a non-date value.")

    return DailyTrend(
        date=raw_date.isoformat(),
        count=_count_from_value(data["count"]),
    )


def _ai_summary_from_record(record: Record | Mapping[str, object]) -> AiSummaryRow:
    data = _record_to_dict(record)
    raw_insights = data.get("insights")
    if isinstance(raw_insights, str):
        data["insights"] = loads(raw_insights)
    return AiSummaryRow.model_validate(data)


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
    statuses: list[Status] | None = None,
    priorities: list[Priority] | None = None,
    sources: list[Source] | None = None,
    search: str | None = None,
    sort_by: SortBy = SortBy.created_at,
    sort_order: SortOrder = SortOrder.desc,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[FeedbackRow], int]:
    conditions: list[str] = []
    params: list[object] = []
    idx = 1

    if statuses:
        placeholders = ", ".join(f"${idx + i}" for i in range(len(statuses)))
        conditions.append(f"status IN ({placeholders})")
        params.extend(statuses)
        idx += len(statuses)
    if priorities:
        placeholders = ", ".join(f"${idx + i}" for i in range(len(priorities)))
        conditions.append(f"priority IN ({placeholders})")
        params.extend(priorities)
        idx += len(priorities)
    if sources:
        placeholders = ", ".join(f"${idx + i}" for i in range(len(sources)))
        conditions.append(f"source IN ({placeholders})")
        params.extend(sources)
        idx += len(sources)
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

    total = _count_from_value(
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


async def get_dashboard(connection: DatabaseConnection) -> DashboardResponse:
    status_rows = await connection.fetch(
        "SELECT status, COUNT(*) AS count FROM feedback GROUP BY status",
    )
    priority_rows = await connection.fetch(
        "SELECT priority, COUNT(*) AS count FROM feedback GROUP BY priority",
    )
    trend_rows = await connection.fetch(
        """
        SELECT d::date AS date, COALESCE(COUNT(f.id), 0) AS count
        FROM generate_series(CURRENT_DATE - 6, CURRENT_DATE, '1 day') d
        LEFT JOIN feedback f ON f.created_at::date = d::date
        GROUP BY d::date
        ORDER BY d::date
        """
    )

    status_counts = {status.value: 0 for status in Status}
    for row in status_rows:
        data = _record_to_dict(row)
        status_key = str(data["status"])
        status_counts[status_key] = _count_from_value(data["count"])

    priority_counts = {priority.value: 0 for priority in Priority}
    for row in priority_rows:
        data = _record_to_dict(row)
        priority_key = str(data["priority"])
        priority_counts[priority_key] = _count_from_value(data["count"])

    return DashboardResponse(
        status_counts=status_counts,
        priority_counts=priority_counts,
        daily_trend=[_trend_from_record(row) for row in trend_rows],
    )


async def get_latest_summary(connection: DatabaseConnection) -> AiSummaryRow | None:
    row = await connection.fetchrow(
        "SELECT * FROM ai_summaries ORDER BY generated_at DESC LIMIT 1",
    )
    if row is None:
        return None

    return _ai_summary_from_record(row)


async def get_feedback_hash_and_count(connection: DatabaseConnection) -> tuple[str, int]:
    row = await connection.fetchrow(
        """
        SELECT COALESCE(
                   md5(string_agg(id::text || updated_at::text, ',' ORDER BY id)),
                   md5('')
               ) AS hash,
               COUNT(*) AS count
        FROM feedback
        """
    )
    if row is None:
        raise RuntimeError("Feedback hash query returned no row.")

    data = _record_to_dict(row)
    feedback_hash = data["hash"]
    feedback_count = data["count"]
    if not isinstance(feedback_hash, str):
        raise RuntimeError("Feedback hash query returned a non-string hash.")

    return feedback_hash, _count_from_value(feedback_count)


async def list_feedback_for_insights(
    connection: DatabaseConnection,
    limit: int,
) -> list[FeedbackRow]:
    rows = await connection.fetch(
        "SELECT * FROM feedback ORDER BY created_at DESC LIMIT $1",
        limit,
    )
    return [_feedback_from_record(row) for row in rows]


async def insert_ai_summary(
    connection: DatabaseConnection,
    *,
    insights: list[Insight],
    feedback_hash: str,
    feedback_count: int,
    model_used: str,
) -> AiSummaryRow:
    row = await connection.fetchrow(
        """
        INSERT INTO ai_summaries (insights, feedback_hash, feedback_count, model_used)
        VALUES ($1::jsonb, $2, $3, $4)
        RETURNING *
        """,
        dumps([insight.model_dump() for insight in insights]),
        feedback_hash,
        feedback_count,
        model_used,
    )
    if row is None:
        raise RuntimeError("AI summary insert unexpectedly returned no row.")

    return _ai_summary_from_record(row)

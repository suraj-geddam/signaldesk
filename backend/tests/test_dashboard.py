from datetime import UTC, datetime, time, timedelta

from fastapi.testclient import TestClient

from .conftest import DatabaseHelper


def auth_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_returns_grouped_counts(
    client: TestClient,
    db: DatabaseHelper,
) -> None:
    member_id = db.user_id("member")
    today = db.current_date()
    base_date = datetime.combine(today, time(12, 0), tzinfo=UTC)
    db.seed_feedback(
        title="New high priority",
        description="Fresh issue.",
        source="email",
        priority="high",
        status="new",
        created_by=member_id,
        created_at=base_date,
    )
    db.seed_feedback(
        title="Work in progress",
        description="Being handled.",
        source="chat",
        priority="medium",
        status="in_progress",
        created_by=member_id,
        created_at=base_date - timedelta(days=1),
    )
    db.seed_feedback(
        title="Closed item",
        description="Already done.",
        source="call",
        priority="low",
        status="done",
        created_by=member_id,
        created_at=base_date - timedelta(days=2),
    )

    response = client.get(
        "/dashboard",
        headers=auth_headers(client, "member", "member123"),
    )

    assert response.status_code == 200
    assert response.json()["status_counts"] == {
        "new": 1,
        "in_progress": 1,
        "done": 1,
    }
    assert response.json()["priority_counts"] == {
        "low": 1,
        "medium": 1,
        "high": 1,
    }


def test_dashboard_zero_fills_last_seven_days(
    client: TestClient,
    db: DatabaseHelper,
) -> None:
    member_id = db.user_id("member")
    current_day = db.current_date()
    today = datetime.combine(current_day, time(12, 0), tzinfo=UTC)
    db.seed_feedback(
        title="Today item",
        description="Current day feedback.",
        source="slack",
        priority="medium",
        status="new",
        created_by=member_id,
        created_at=today,
    )
    db.seed_feedback(
        title="Earlier item",
        description="Older feedback still in window.",
        source="email",
        priority="high",
        status="new",
        created_by=member_id,
        created_at=today - timedelta(days=3),
    )
    db.seed_feedback(
        title="Second older item",
        description="Same day as the older feedback.",
        source="call",
        priority="low",
        status="done",
        created_by=member_id,
        created_at=today - timedelta(days=3),
    )

    response = client.get(
        "/dashboard",
        headers=auth_headers(client, "admin", "admin123"),
    )

    assert response.status_code == 200
    expected = []
    for day_offset in range(6, -1, -1):
        day = current_day - timedelta(days=day_offset)
        count = 2 if day_offset == 3 else 1 if day_offset == 0 else 0
        expected.append({"date": day.isoformat(), "count": count})

    assert response.json()["daily_trend"] == expected

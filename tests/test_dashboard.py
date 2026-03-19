from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from tests.conftest import FakeConnection


def auth_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_returns_grouped_counts(
    client: TestClient,
    fake_connection: FakeConnection,
) -> None:
    member_id = fake_connection.users_by_username["member"]["id"]
    base_date = datetime(2026, 3, 19, tzinfo=UTC)
    fake_connection.seed_feedback(
        title="New high priority",
        description="Fresh issue.",
        source="email",
        priority="high",
        status="new",
        created_by=member_id,
        created_at=base_date,
    )
    fake_connection.seed_feedback(
        title="Work in progress",
        description="Being handled.",
        source="chat",
        priority="medium",
        status="in_progress",
        created_by=member_id,
        created_at=base_date - timedelta(days=1),
    )
    fake_connection.seed_feedback(
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
    fake_connection: FakeConnection,
) -> None:
    member_id = fake_connection.users_by_username["member"]["id"]
    today = datetime(2026, 3, 19, tzinfo=UTC)
    fake_connection.seed_feedback(
        title="Today item",
        description="Current day feedback.",
        source="slack",
        priority="medium",
        status="new",
        created_by=member_id,
        created_at=today,
    )
    fake_connection.seed_feedback(
        title="Earlier item",
        description="Older feedback still in window.",
        source="email",
        priority="high",
        status="new",
        created_by=member_id,
        created_at=today - timedelta(days=3),
    )
    fake_connection.seed_feedback(
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
    assert response.json()["daily_trend"] == [
        {"date": "2026-03-13", "count": 0},
        {"date": "2026-03-14", "count": 0},
        {"date": "2026-03-15", "count": 0},
        {"date": "2026-03-16", "count": 2},
        {"date": "2026-03-17", "count": 0},
        {"date": "2026-03-18", "count": 0},
        {"date": "2026-03-19", "count": 1},
    ]

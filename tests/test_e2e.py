from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

import app.insights as insights_module

from .conftest import FakeConnection


def login(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_backend_happy_path_covers_core_workflow(
    client: TestClient,
    fake_connection: FakeConnection,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generated_at = datetime(2026, 3, 19, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(insights_module, "utc_now", lambda: generated_at)

    member_headers = login(client, "member", "member123")
    admin_headers = login(client, "admin", "admin123")

    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok", "db": "connected"}

    me_response = client.get("/auth/me", headers=member_headers)
    assert me_response.status_code == 200
    assert me_response.json()["role"] == "member"

    create_response = client.post(
        "/feedback",
        json={
            "title": "SOC2 export requests",
            "description": "Customers want CSV and SOC2 export support.",
            "source": "email",
            "priority": "high",
        },
        headers=member_headers | {"Idempotency-Key": "e2e-create-feedback"},
    )
    assert create_response.status_code == 201
    feedback_id = create_response.json()["id"]
    assert create_response.json()["status"] == "new"

    list_response = client.get("/feedback", headers=member_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1
    assert list_response.json()["items"][0]["id"] == feedback_id

    get_response = client.get(f"/feedback/{feedback_id}", headers=member_headers)
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "SOC2 export requests"

    update_response = client.put(
        f"/feedback/{feedback_id}",
        json={
            "title": "SOC2 export requests",
            "description": "Customers want CSV and SOC2 export support.",
            "source": "email",
            "priority": "high",
            "status": "in_progress",
        },
        headers=member_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "in_progress"

    dashboard_response = client.get("/dashboard", headers=member_headers)
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["status_counts"] == {
        "new": 0,
        "in_progress": 1,
        "done": 0,
    }
    assert dashboard_response.json()["priority_counts"] == {
        "low": 0,
        "medium": 0,
        "high": 1,
    }

    placeholder_response = client.get("/feedback/insights", headers=member_headers)
    assert placeholder_response.status_code == 200
    assert placeholder_response.json() == {
        "insights": [],
        "stale": False,
        "message": "No insights generated yet.",
    }

    forbidden_refresh = client.post("/feedback/insights/refresh", headers=member_headers)
    assert forbidden_refresh.status_code == 403

    async def fake_run_generate_insights(settings: object) -> object:
        del settings
        return fake_connection.seed_ai_summary(
            insights=[
                {
                    "theme": "Export compliance workflows",
                    "confidence": 0.91,
                    "justification": (
                        "The created feedback item requests SOC2 and CSV export support."
                    ),
                }
            ],
            feedback_hash=fake_connection.compute_feedback_hash(),
            feedback_count=len(fake_connection.feedback_by_id),
            model_used="test-model",
            generated_at=generated_at,
        )

    monkeypatch.setattr(insights_module, "run_generate_insights", fake_run_generate_insights)

    refresh_response = client.post("/feedback/insights/refresh", headers=admin_headers)
    assert refresh_response.status_code == 202
    assert refresh_response.json() == {"message": "Refresh started"}

    insights_response = client.get("/feedback/insights", headers=member_headers)
    assert insights_response.status_code == 200
    assert insights_response.json()["stale"] is False
    assert insights_response.json()["feedback_count"] == 1
    assert insights_response.json()["model_used"] == "test-model"
    assert insights_response.json()["insights"] == [
        {
            "theme": "Export compliance workflows",
            "confidence": 0.91,
            "justification": "The created feedback item requests SOC2 and CSV export support.",
        }
    ]

    member_delete_response = client.delete(f"/feedback/{feedback_id}", headers=member_headers)
    assert member_delete_response.status_code == 403

    admin_delete_response = client.delete(f"/feedback/{feedback_id}", headers=admin_headers)
    assert admin_delete_response.status_code == 204

    deleted_lookup_response = client.get(f"/feedback/{feedback_id}", headers=admin_headers)
    assert deleted_lookup_response.status_code == 404

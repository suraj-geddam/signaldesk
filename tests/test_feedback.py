from uuid import uuid4

from fastapi.testclient import TestClient


def auth_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_feedback_returns_created_row(client: TestClient) -> None:
    response = client.post(
        "/feedback",
        json={
            "title": "Export to CSV",
            "description": "Customers want CSV exports from reports.",
            "source": "email",
            "priority": "high",
        },
        headers=auth_headers(client, "member", "member123"),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Export to CSV"
    assert body["status"] == "new"
    assert body["priority"] == "high"


def test_create_feedback_reuses_idempotency_key(client: TestClient) -> None:
    headers = auth_headers(client, "member", "member123") | {"Idempotency-Key": "same-key"}

    first_response = client.post(
        "/feedback",
        json={
            "title": "Slack alerts",
            "description": "Need Slack notifications for outages.",
            "source": "slack",
            "priority": "medium",
        },
        headers=headers,
    )
    second_response = client.post(
        "/feedback",
        json={
            "title": "Different body",
            "description": "This should not create a second row.",
            "source": "chat",
            "priority": "low",
        },
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert second_response.json()["id"] == first_response.json()["id"]
    assert second_response.json()["title"] == first_response.json()["title"]


def test_get_feedback_by_id_returns_row(client: TestClient) -> None:
    create_response = client.post(
        "/feedback",
        json={
            "title": "Audit log filters",
            "description": "Support filtering audit logs by actor.",
            "source": "call",
            "priority": "medium",
        },
        headers=auth_headers(client, "member", "member123"),
    )
    feedback_id = create_response.json()["id"]

    response = client.get(
        f"/feedback/{feedback_id}",
        headers=auth_headers(client, "member", "member123"),
    )

    assert response.status_code == 200
    assert response.json()["id"] == feedback_id


def test_list_feedback_supports_filters_and_sorting(client: TestClient) -> None:
    member_headers = auth_headers(client, "member", "member123")

    client.post(
        "/feedback",
        json={
            "title": "Priority high",
            "description": "First item.",
            "source": "email",
            "priority": "high",
        },
        headers=member_headers,
    )
    client.post(
        "/feedback",
        json={
            "title": "Priority low",
            "description": "Second item.",
            "source": "email",
            "priority": "low",
        },
        headers=member_headers,
    )

    response = client.get(
        "/feedback",
        params={"source": "email", "sort_by": "priority", "sort_order": "asc"},
        headers=member_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["priority"] for item in body["items"]] == ["high", "low"]


def test_member_can_update_own_feedback(client: TestClient) -> None:
    member_headers = auth_headers(client, "member", "member123")
    create_response = client.post(
        "/feedback",
        json={
            "title": "Original title",
            "description": "Original description.",
            "source": "other",
            "priority": "low",
        },
        headers=member_headers,
    )
    feedback_id = create_response.json()["id"]

    response = client.put(
        f"/feedback/{feedback_id}",
        json={
            "title": "Updated title",
            "description": "Updated description.",
            "source": "chat",
            "priority": "high",
            "status": "in_progress",
        },
        headers=member_headers,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated title"
    assert response.json()["status"] == "in_progress"


def test_member_cannot_update_another_users_feedback(client: TestClient) -> None:
    member_headers = auth_headers(client, "member", "member123")
    admin_headers = auth_headers(client, "admin", "admin123")
    create_response = client.post(
        "/feedback",
        json={
            "title": "Admin-owned row",
            "description": "Only admin should update this one.",
            "source": "call",
            "priority": "medium",
        },
        headers=admin_headers,
    )
    feedback_id = create_response.json()["id"]

    response = client.put(
        f"/feedback/{feedback_id}",
        json={
            "title": "Member attempted update",
            "description": "Should not be allowed.",
            "source": "chat",
            "priority": "high",
            "status": "done",
        },
        headers=member_headers,
    )

    assert response.status_code == 404


def test_member_cannot_delete_feedback(client: TestClient) -> None:
    member_headers = auth_headers(client, "member", "member123")
    create_response = client.post(
        "/feedback",
        json={
            "title": "Delete guard",
            "description": "Members should not delete this.",
            "source": "email",
            "priority": "medium",
        },
        headers=member_headers,
    )
    feedback_id = create_response.json()["id"]

    response = client.delete(f"/feedback/{feedback_id}", headers=member_headers)

    assert response.status_code == 403


def test_admin_can_delete_feedback(client: TestClient) -> None:
    member_headers = auth_headers(client, "member", "member123")
    admin_headers = auth_headers(client, "admin", "admin123")
    create_response = client.post(
        "/feedback",
        json={
            "title": "Admin delete",
            "description": "Admin should be able to delete this.",
            "source": "call",
            "priority": "high",
        },
        headers=member_headers,
    )
    feedback_id = create_response.json()["id"]

    delete_response = client.delete(f"/feedback/{feedback_id}", headers=admin_headers)
    get_response = client.get(f"/feedback/{feedback_id}", headers=admin_headers)

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_list_feedback_supports_search_and_pagination(client: TestClient) -> None:
    member_headers = auth_headers(client, "member", "member123")

    client.post(
        "/feedback",
        json={
            "title": "SOC2 export",
            "description": "Need exports for compliance reviews.",
            "source": "email",
            "priority": "high",
        },
        headers=member_headers,
    )
    client.post(
        "/feedback",
        json={
            "title": "SOC2 audit trail",
            "description": "Track changes during audits.",
            "source": "call",
            "priority": "medium",
        },
        headers=member_headers,
    )
    client.post(
        "/feedback",
        json={
            "title": "Dashboard polish",
            "description": "Not related to compliance.",
            "source": "chat",
            "priority": "low",
        },
        headers=member_headers,
    )

    response = client.get(
        "/feedback",
        params={"search": "soc2", "page": 1, "per_page": 1},
        headers=member_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1
    assert "SOC2" in body["items"][0]["title"]


def test_delete_nonexistent_feedback_returns_not_found(client: TestClient) -> None:
    response = client.delete(
        f"/feedback/{uuid4()}",
        headers=auth_headers(client, "admin", "admin123"),
    )

    assert response.status_code == 404

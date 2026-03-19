from fastapi.testclient import TestClient


def auth_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_request_id_is_generated_when_missing(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]


def test_request_id_header_is_propagated(client: TestClient) -> None:
    response = client.get(
        "/health",
        headers={"X-Request-ID": "req-from-client"},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-from-client"


def test_validation_errors_use_consistent_error_envelope(client: TestClient) -> None:
    response = client.post(
        "/feedback",
        json={
            "title": "Bad payload",
            "description": "",
            "source": "email",
            "priority": "high",
        },
        headers=auth_headers(client, "member", "member123"),
    )

    assert response.status_code == 422
    body = response.json()
    assert body["status_code"] == 422
    assert body["request_id"] == response.headers["x-request-id"]
    assert isinstance(body["detail"], list)


def test_http_exceptions_use_consistent_error_envelope(client: TestClient) -> None:
    response = client.delete(
        "/feedback/not-a-uuid",
        headers=auth_headers(client, "admin", "admin123"),
    )

    assert response.status_code == 422
    body = response.json()
    assert body["status_code"] == 422
    assert body["request_id"] == response.headers["x-request-id"]


def test_forbidden_error_uses_consistent_error_envelope(client: TestClient) -> None:
    response = client.post(
        "/feedback/insights/refresh",
        headers=auth_headers(client, "member", "member123"),
    )

    assert response.status_code == 403
    body = response.json()
    assert body == {
        "detail": "Admin access required",
        "request_id": response.headers["x-request-id"],
        "status_code": 403,
    }

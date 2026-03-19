import json

from fastapi.testclient import TestClient

import app.config as config_module


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


def test_default_rate_limit_is_enforced(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setenv("RATE_LIMIT_DEFAULT", "2/minute")
    config_module.get_settings.cache_clear()

    first = client.get("/health")
    second = client.get("/health")
    third = client.get("/health")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.json()["status_code"] == 429
    assert third.json()["request_id"] == third.headers["x-request-id"]


def test_login_rate_limit_is_enforced(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setenv("RATE_LIMIT_LOGIN", "2/minute")
    config_module.get_settings.cache_clear()

    first = client.post(
        "/auth/login",
        json={"username": "member", "password": "wrong"},
    )
    second = client.post(
        "/auth/login",
        json={"username": "member", "password": "wrong"},
    )
    third = client.post(
        "/auth/login",
        json={"username": "member", "password": "wrong"},
    )

    assert first.status_code == 401
    assert second.status_code == 401
    assert third.status_code == 429


def test_ai_refresh_rate_limit_is_enforced(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setenv("RATE_LIMIT_AI_REFRESH", "1/minute")
    config_module.get_settings.cache_clear()
    admin_headers = auth_headers(client, "admin", "admin123")

    first = client.post("/feedback/insights/refresh", headers=admin_headers)
    second = client.post("/feedback/insights/refresh", headers=admin_headers)

    assert first.status_code == 202
    assert second.status_code == 429


def test_request_logs_include_request_metadata(
    client: TestClient,
    caplog,
) -> None:
    caplog.set_level("INFO", logger="signaldesk.http")
    caplog.clear()

    response = client.get(
        "/health",
        headers={"X-Request-ID": "req-log-success"},
    )

    assert response.status_code == 200
    events = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "signaldesk.http"
    ]
    assert [event["event"] for event in events] == ["request_started", "request_finished"]
    assert events[0]["request_id"] == "req-log-success"
    assert events[0]["method"] == "GET"
    assert events[0]["path"] == "/health"
    assert events[1]["request_id"] == "req-log-success"
    assert events[1]["status_code"] == 200
    assert events[1]["duration_ms"] >= 0


def test_request_logs_include_error_status(
    client: TestClient,
    caplog,
) -> None:
    caplog.set_level("INFO", logger="signaldesk.http")
    caplog.clear()

    response = client.post(
        "/feedback/insights/refresh",
        headers=auth_headers(client, "member", "member123") | {"X-Request-ID": "req-log-error"},
    )

    assert response.status_code == 403
    events = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "signaldesk.http"
    ]
    assert events[-1]["event"] == "request_finished"
    assert events[-1]["request_id"] == "req-log-error"
    assert events[-1]["status_code"] == 403

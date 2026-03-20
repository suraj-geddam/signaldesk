from fastapi.testclient import TestClient


def test_login_returns_access_token(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"username": "member", "password": "member123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["role"] == "member"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"username": "member", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_protected_route_requires_token(client: TestClient) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_protected_route_returns_current_user(client: TestClient) -> None:
    login_response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = login_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["username"] == "admin"
    assert response.json()["role"] == "admin"

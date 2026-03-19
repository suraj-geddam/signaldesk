import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import app.insights as insights_module
from app.config import Settings
from tests.conftest import FakeConnection


class FakeParsedMessage:
    def __init__(self, parsed: object) -> None:
        self.parsed = parsed


class FakeChoice:
    def __init__(self, parsed: object) -> None:
        self.message = FakeParsedMessage(parsed)


class FakeCompletion:
    def __init__(self, parsed: object) -> None:
        self.choices = [FakeChoice(parsed)]


class SuccessfulCompletions:
    async def parse(self, **_: object) -> FakeCompletion:
        return FakeCompletion(
            insights_module.InsightGenerationResult(
                insights=[
                    insights_module.Insight(
                        theme="Export workflow pain",
                        confidence=0.92,
                        justification="Multiple customers asked for export support.",
                    )
                ]
            )
        )


class SuccessfulClient:
    def __init__(self) -> None:
        self.chat = type(
            "ChatNamespace",
            (),
            {"completions": SuccessfulCompletions()},
        )()


class FailingCompletions:
    async def parse(self, **_: object) -> FakeCompletion:
        raise RuntimeError("AI unavailable")


class FailingClient:
    def __init__(self) -> None:
        self.chat = type(
            "ChatNamespace",
            (),
            {"completions": FailingCompletions()},
        )()


class MalformedCompletions:
    async def parse(self, **_: object) -> FakeCompletion:
        return FakeCompletion(None)


class MalformedClient:
    def __init__(self) -> None:
        self.chat = type(
            "ChatNamespace",
            (),
            {"completions": MalformedCompletions()},
        )()


def auth_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_insights_without_summary_returns_placeholder(client: TestClient) -> None:
    response = client.get(
        "/feedback/insights",
        headers=auth_headers(client, "member", "member123"),
    )

    assert response.status_code == 200
    assert response.json() == {
        "insights": [],
        "stale": False,
        "message": "No insights generated yet.",
    }


def test_get_insights_with_fresh_summary_returns_cached_row(
    client: TestClient,
    fake_connection: FakeConnection,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generated_at = datetime(2026, 3, 19, 12, 0, tzinfo=UTC)
    fake_connection.seed_ai_summary(
        insights=[
            {
                "theme": "CSV exports",
                "confidence": 0.81,
                "justification": "Export requests appear repeatedly.",
            }
        ],
        feedback_hash="abc123",
        feedback_count=4,
        model_used="gpt-4o-mini",
        generated_at=generated_at,
    )
    monkeypatch.setattr(
        insights_module,
        "utc_now",
        lambda: generated_at + timedelta(minutes=5),
    )

    response = client.get(
        "/feedback/insights",
        headers=auth_headers(client, "member", "member123"),
    )

    assert response.status_code == 200
    assert response.json()["stale"] is False
    assert response.json()["feedback_count"] == 4
    assert response.json()["model_used"] == "gpt-4o-mini"
    assert response.json()["insights"][0]["theme"] == "CSV exports"


def test_get_insights_with_stale_summary_marks_response_stale(
    client: TestClient,
    fake_connection: FakeConnection,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generated_at = datetime(2026, 3, 19, 12, 0, tzinfo=UTC)
    fake_connection.seed_ai_summary(
        insights=[
            {
                "theme": "Notification gaps",
                "confidence": 0.76,
                "justification": "Alerts came up several times.",
            }
        ],
        feedback_hash="def456",
        feedback_count=2,
        model_used="gpt-4o-mini",
        generated_at=generated_at,
    )
    monkeypatch.setattr(
        insights_module,
        "utc_now",
        lambda: generated_at + timedelta(minutes=45),
    )

    response = client.get(
        "/feedback/insights",
        headers=auth_headers(client, "member", "member123"),
    )

    assert response.status_code == 200
    assert response.json()["stale"] is True


def test_generate_insights_skips_when_feedback_hash_is_unchanged(
    fake_connection: FakeConnection,
) -> None:
    settings = Settings(
        database_url="postgresql://signaldesk:signaldesk@localhost:5432/signaldesk",
        jwt_secret="test-secret",
    )
    member_id = fake_connection.users_by_username["member"]["id"]
    fake_connection.seed_feedback(
        title="Export to CSV",
        description="Need downloads.",
        source="email",
        priority="high",
        status="new",
        created_by=member_id,
        created_at=datetime(2026, 3, 19, 10, 0, tzinfo=UTC),
    )
    fake_connection.seed_ai_summary(
        insights=[
            {
                "theme": "Existing",
                "confidence": 0.5,
                "justification": "Existing cached insight.",
            }
        ],
        feedback_hash=fake_connection.compute_feedback_hash(),
        feedback_count=1,
        model_used="gpt-4o-mini",
        generated_at=datetime(2026, 3, 19, 10, 5, tzinfo=UTC),
    )

    inserted = asyncio.run(
        insights_module.generate_insights(
            fake_connection,
            settings,
            client=FailingClient(),
        )
    )

    assert inserted is None
    assert len(fake_connection.ai_summaries) == 1


def test_generate_insights_failure_does_not_overwrite_cached_summary(
    fake_connection: FakeConnection,
) -> None:
    settings = Settings(
        database_url="postgresql://signaldesk:signaldesk@localhost:5432/signaldesk",
        jwt_secret="test-secret",
    )
    member_id = fake_connection.users_by_username["member"]["id"]
    fake_connection.seed_feedback(
        title="Slack alerts",
        description="Need alert routing.",
        source="slack",
        priority="medium",
        status="new",
        created_by=member_id,
        created_at=datetime(2026, 3, 19, 9, 0, tzinfo=UTC),
    )
    fake_connection.seed_ai_summary(
        insights=[
            {
                "theme": "Cached summary",
                "confidence": 0.7,
                "justification": "Still valid fallback.",
            }
        ],
        feedback_hash="outdated-hash",
        feedback_count=1,
        model_used="gpt-4o-mini",
        generated_at=datetime(2026, 3, 19, 9, 5, tzinfo=UTC),
    )

    try:
        asyncio.run(
            insights_module.generate_insights(
                fake_connection,
                settings,
                client=FailingClient(),
            )
        )
    except RuntimeError as exc:
        assert "AI unavailable" in str(exc)
    else:
        raise AssertionError("Expected AI failure to propagate")

    assert len(fake_connection.ai_summaries) == 1
    assert fake_connection.ai_summaries[0]["insights"][0]["theme"] == "Cached summary"


def test_generate_insights_rejects_malformed_ai_response(
    fake_connection: FakeConnection,
) -> None:
    settings = Settings(
        database_url="postgresql://signaldesk:signaldesk@localhost:5432/signaldesk",
        jwt_secret="test-secret",
    )
    member_id = fake_connection.users_by_username["member"]["id"]
    fake_connection.seed_feedback(
        title="Audit exports",
        description="Need better exports.",
        source="call",
        priority="high",
        status="new",
        created_by=member_id,
        created_at=datetime(2026, 3, 19, 8, 0, tzinfo=UTC),
    )

    try:
        asyncio.run(
            insights_module.generate_insights(
                fake_connection,
                settings,
                client=MalformedClient(),
            )
        )
    except RuntimeError as exc:
        assert "parsed insights payload" in str(exc)
    else:
        raise AssertionError("Expected malformed AI response to fail")

    assert fake_connection.ai_summaries == []


def test_admin_refresh_endpoint_returns_accepted(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    async def fake_run_generate_insights(_: Settings) -> None:
        calls.append("called")

    monkeypatch.setattr(insights_module, "run_generate_insights", fake_run_generate_insights)

    response = client.post(
        "/feedback/insights/refresh",
        headers=auth_headers(client, "admin", "admin123"),
    )

    assert response.status_code == 202
    assert response.json() == {"message": "Refresh started"}
    assert calls == ["called"]

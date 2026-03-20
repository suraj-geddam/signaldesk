import asyncpg
import pytest
from fastapi.testclient import TestClient

import app.config as config_module
import app.main as main_module
from app.main import app
from tests.conftest import clear_database_schema, run_async


def test_database_bootstrap_is_idempotent(database_url: str) -> None:
    import app.bootstrap as bootstrap_module

    async def _exercise() -> None:
        connection = await asyncpg.connect(database_url)
        try:
            await connection.execute("DROP SCHEMA IF EXISTS public CASCADE")
            await connection.execute("CREATE SCHEMA public")
            await bootstrap_module.initialize_database(connection)
            await bootstrap_module.initialize_database(connection)

            user_count = await connection.fetchval("SELECT COUNT(*) FROM users")
            trigger_count = await connection.fetchval(
                """
                SELECT COUNT(*)
                FROM pg_trigger
                WHERE tgname = 'trg_feedback_updated_at'
                  AND tgrelid = 'feedback'::regclass
                """,
            )
        finally:
            await connection.close()

        assert user_count == 2
        assert trigger_count == 1

    run_async(_exercise())


def test_app_startup_bootstraps_an_empty_database(
    monkeypatch: pytest.MonkeyPatch,
    database_url: str,
) -> None:
    clear_database_schema(database_url)
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    config_module.get_settings.cache_clear()
    monkeypatch.setattr(main_module, "start_periodic_ai_refresh", lambda settings: None)

    try:
        with TestClient(app) as client:
            health_response = client.get("/health")
            assert health_response.status_code == 200
            assert health_response.json() == {"status": "ok", "db": "connected"}

            login_response = client.post(
                "/auth/login",
                json={"username": "member", "password": "member123"},
            )
            assert login_response.status_code == 200
    finally:
        config_module.get_settings.cache_clear()

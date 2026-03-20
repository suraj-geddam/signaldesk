from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    db_pool_min: int = 2
    db_pool_max: int = 10

    jwt_secret: str
    jwt_expiry_minutes: int = 1440

    openai_api_base: str = "http://localhost:8080/v1"
    openai_api_key: str = "not-needed"
    openai_model: str = "gpt-4o-mini"
    ai_refresh_interval_minutes: int = 30
    ai_max_feedback_items: int = 500
    ai_timeout_seconds: int = 30
    ai_max_retries: int = 3

    rate_limit_default: str = "60/minute"
    rate_limit_login: str = "10/minute"
    rate_limit_ai_refresh: str = "5/minute"

    cors_origins: str = "http://localhost:5173"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]

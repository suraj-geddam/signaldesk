import asyncio
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from openai import AsyncOpenAI
from pydantic import BaseModel

from app import db as db_module
from app.auth import get_current_user, require_admin
from app.config import Settings, get_settings
from app.db import DatabaseConnection, get_connection
from app.logging import get_logger
from app.middleware import limiter
from app.queries import (
    get_feedback_hash_and_count,
    get_latest_summary,
    insert_ai_summary,
    list_feedback_for_insights,
)
from app.schemas import Insight, InsightsResponse, UserRow

router = APIRouter(tags=["insights"])
logger = get_logger("signaldesk.insights")

INSIGHTS_PLACEHOLDER_MESSAGE = "No insights generated yet."
INSIGHTS_SYSTEM_PROMPT = """You are an analyst for a customer feedback triage tool.
You will be given a list of customer feedback items. Identify the top 3 recurring themes.

For each theme, provide:
- theme: a short descriptive label (3-8 words)
- confidence: a float between 0 and 1 indicating how strong the signal is
- justification: 1-2 sentences explaining the evidence, including approximate
  counts and which sources/priorities are most represented

Respond with a JSON object: { "insights": [...] }
If there are fewer than 3 clear themes, return fewer. If there is no meaningful
pattern, return an empty insights array."""


class InsightGenerationResult(BaseModel):
    insights: list[Insight]


def utc_now() -> datetime:
    return datetime.now(UTC)


def is_stale(generated_at: datetime, settings: Settings) -> bool:
    return utc_now() - generated_at > timedelta(minutes=settings.ai_refresh_interval_minutes)


def create_openai_client(settings: Settings) -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=settings.openai_api_base,
        api_key=settings.openai_api_key,
        timeout=settings.ai_timeout_seconds,
        max_retries=settings.ai_max_retries,
    )


def _format_feedback_items(feedback_items: list[Any]) -> str:
    lines: list[str] = []
    for index, item in enumerate(feedback_items, start=1):
        lines.append(
            f"{index}. [{item.priority.value.upper()}/{item.status.value}] "
            f"{item.title}: {item.description}"
        )
    return "\n".join(lines)


async def generate_insights(
    connection: DatabaseConnection,
    settings: Settings,
    *,
    client: Any | None = None,
) -> object | None:
    feedback_hash, feedback_count = await get_feedback_hash_and_count(connection)
    latest = await get_latest_summary(connection)
    if latest is not None and latest.feedback_hash == feedback_hash:
        return None
    if feedback_count == 0:
        return None

    feedback_items = await list_feedback_for_insights(connection, settings.ai_max_feedback_items)
    openai_client = client if client is not None else create_openai_client(settings)
    completion = await openai_client.chat.completions.parse(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": INSIGHTS_SYSTEM_PROMPT},
            {"role": "user", "content": _format_feedback_items(feedback_items)},
        ],
        response_format=InsightGenerationResult,
    )
    parsed = completion.choices[0].message.parsed
    if not isinstance(parsed, InsightGenerationResult):
        raise RuntimeError("OpenAI client returned no parsed insights payload.")

    return await insert_ai_summary(
        connection,
        insights=parsed.insights,
        feedback_hash=feedback_hash,
        feedback_count=feedback_count,
        model_used=settings.openai_model,
    )


async def run_generate_insights(settings: Settings) -> object | None:
    if db_module.pool is None:
        return None

    async with db_module.pool.acquire() as connection:
        return await generate_insights(connection, settings)


async def periodic_ai_refresh(settings: Settings) -> None:
    while True:
        try:
            if db_module.pool is not None:
                async with db_module.pool.acquire() as connection:
                    latest = await get_latest_summary(connection)
                if latest is None or is_stale(latest.generated_at, settings):
                    await run_generate_insights(settings)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("periodic_ai_refresh_failed")

        await asyncio.sleep(settings.ai_refresh_interval_minutes * 60)


def start_periodic_ai_refresh(settings: Settings) -> asyncio.Task[None] | None:
    if db_module.pool is None:
        raise RuntimeError("Database pool must be initialized before starting periodic AI refresh.")

    return asyncio.create_task(periodic_ai_refresh(settings))


@router.get(
    "/feedback/insights",
    response_model=InsightsResponse,
    response_model_exclude_none=True,
)
async def get_insights_endpoint(
    user: Annotated[UserRow, Depends(get_current_user)],
    connection: Annotated[DatabaseConnection, Depends(get_connection)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> InsightsResponse:
    del user
    latest = await get_latest_summary(connection)
    if latest is None:
        return InsightsResponse(
            insights=[],
            stale=False,
            message=INSIGHTS_PLACEHOLDER_MESSAGE,
        )

    return InsightsResponse(
        insights=latest.insights,
        feedback_count=latest.feedback_count,
        model_used=latest.model_used,
        generated_at=latest.generated_at,
        stale=is_stale(latest.generated_at, settings),
    )


@router.post(
    "/feedback/insights/refresh",
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit(lambda: get_settings().rate_limit_ai_refresh)
async def refresh_insights_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    user: Annotated[UserRow, Depends(require_admin)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    del request
    del user
    background_tasks.add_task(run_generate_insights, settings)
    return {"message": "Refresh started"}

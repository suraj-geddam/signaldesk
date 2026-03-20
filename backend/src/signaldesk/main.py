from asyncio import CancelledError, Task
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from signaldesk.auth import router as auth_router
from signaldesk.bootstrap import initialize_database_pool
from signaldesk.config import get_settings
from signaldesk.dashboard import router as dashboard_router
from signaldesk.db import close_pool, init_pool
from signaldesk.feedback import router as feedback_router
from signaldesk.health import router as health_router
from signaldesk.insights import router as insights_router
from signaldesk.insights import start_periodic_ai_refresh
from signaldesk.logging import configure_logging
from signaldesk.middleware import (
    http_exception_handler,
    limiter,
    rate_limit_exception_handler,
    request_id_middleware,
    validation_exception_handler,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    pool = await init_pool(settings)
    await initialize_database_pool(pool)
    periodic_task: Task[None] | None = start_periodic_ai_refresh(settings)

    try:
        yield
    finally:
        if periodic_task is not None:
            periodic_task.cancel()
            with suppress(CancelledError):
                await periodic_task
        await close_pool()


app = FastAPI(
    title="SignalDesk API",
    version="0.1.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(request_id_middleware)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(insights_router)
app.include_router(feedback_router)
app.include_router(health_router)

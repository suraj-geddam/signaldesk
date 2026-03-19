from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.auth import router as auth_router
from app.config import get_settings
from app.db import close_pool, init_pool
from app.feedback import router as feedback_router
from app.health import router as health_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    await init_pool(settings)

    try:
        yield
    finally:
        await close_pool()


app = FastAPI(
    title="SignalDesk API",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(auth_router)
app.include_router(feedback_router)
app.include_router(health_router)

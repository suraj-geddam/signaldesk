from typing import Annotated

from fastapi import APIRouter, Depends

from app.db import DatabaseConnection, get_connection
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    connection: Annotated[DatabaseConnection, Depends(get_connection)],
) -> HealthResponse:
    await connection.fetchval("SELECT 1")
    return HealthResponse(status="ok", db="connected")

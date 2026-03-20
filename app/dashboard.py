from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.db import DatabaseConnection, get_connection
from app.queries import get_dashboard
from app.schemas import DashboardResponse, UserRow

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def read_dashboard(
    user: Annotated[UserRow, Depends(get_current_user)],
    connection: Annotated[DatabaseConnection, Depends(get_connection)],
) -> DashboardResponse:
    return await get_dashboard(connection)

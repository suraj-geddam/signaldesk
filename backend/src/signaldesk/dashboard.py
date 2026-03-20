from typing import Annotated

from fastapi import APIRouter, Depends

from signaldesk.auth import get_current_user
from signaldesk.db import DatabaseConnection, get_connection
from signaldesk.queries import get_dashboard
from signaldesk.schemas import DashboardResponse, UserRow

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def read_dashboard(
    user: Annotated[UserRow, Depends(get_current_user)],
    connection: Annotated[DatabaseConnection, Depends(get_connection)],
) -> DashboardResponse:
    return await get_dashboard(connection)

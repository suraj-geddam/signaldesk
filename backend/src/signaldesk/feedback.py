from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status

from signaldesk.auth import get_current_user, require_admin
from signaldesk.db import DatabaseConnection, get_connection
from signaldesk.queries import (
    create_feedback,
    delete_feedback,
    get_feedback_by_id,
    list_feedback,
    update_feedback_as_admin,
    update_feedback_as_member,
)
from signaldesk.schemas import (
    FeedbackCreate,
    FeedbackListResponse,
    FeedbackResponse,
    FeedbackUpdate,
    Priority,
    SortBy,
    SortOrder,
    Source,
    Status,
    UserRow,
)

router = APIRouter(tags=["feedback"])


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_feedback_endpoint(
    payload: FeedbackCreate,
    user: Annotated[UserRow, Depends(get_current_user)],
    connection: Annotated[DatabaseConnection, Depends(get_connection)],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> FeedbackResponse:
    return await create_feedback(
        connection,
        title=payload.title,
        description=payload.description,
        source=payload.source,
        priority=payload.priority,
        status=payload.status,
        created_by=user.id,
        idempotency_key=idempotency_key,
    )


@router.get("/feedback", response_model=FeedbackListResponse)
async def list_feedback_endpoint(
    user: Annotated[UserRow, Depends(get_current_user)],
    connection: Annotated[DatabaseConnection, Depends(get_connection)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[Status | None, Query(alias="status")] = None,
    priority: Priority | None = None,
    source: Source | None = None,
    search: str | None = None,
    sort_by: SortBy = SortBy.created_at,
    sort_order: SortOrder = SortOrder.desc,
) -> FeedbackListResponse:
    items, total = await list_feedback(
        connection,
        status=status_filter,
        priority=priority,
        source=source,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page,
    )
    return FeedbackListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback_endpoint(
    feedback_id: UUID,
    user: Annotated[UserRow, Depends(get_current_user)],
    connection: Annotated[DatabaseConnection, Depends(get_connection)],
) -> FeedbackResponse:
    feedback = await get_feedback_by_id(connection, feedback_id)
    if feedback is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    return feedback


@router.put("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback_endpoint(
    feedback_id: UUID,
    payload: FeedbackUpdate,
    user: Annotated[UserRow, Depends(get_current_user)],
    connection: Annotated[DatabaseConnection, Depends(get_connection)],
) -> FeedbackResponse:
    if user.role.value == "admin":
        feedback = await update_feedback_as_admin(
            connection,
            feedback_id=feedback_id,
            title=payload.title,
            description=payload.description,
            source=payload.source,
            priority=payload.priority,
            status=payload.status,
        )
    else:
        feedback = await update_feedback_as_member(
            connection,
            feedback_id=feedback_id,
            created_by=user.id,
            title=payload.title,
            description=payload.description,
            source=payload.source,
            priority=payload.priority,
            status=payload.status,
        )

    if feedback is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    return feedback


@router.delete("/feedback/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback_endpoint(
    feedback_id: UUID,
    user: Annotated[UserRow, Depends(require_admin)],
    connection: Annotated[DatabaseConnection, Depends(get_connection)],
) -> Response:
    deleted = await delete_feedback(connection, feedback_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)

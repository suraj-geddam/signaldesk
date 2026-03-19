from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class Source(StrEnum):
    email = "email"
    call = "call"
    slack = "slack"
    chat = "chat"
    other = "other"


class Priority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class Status(StrEnum):
    new = "new"
    in_progress = "in_progress"
    done = "done"


class Role(StrEnum):
    admin = "admin"
    member = "member"


class SortBy(StrEnum):
    created_at = "created_at"
    priority = "priority"


class SortOrder(StrEnum):
    asc = "asc"
    desc = "desc"


class HealthResponse(BaseModel):
    status: str
    db: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role


class TokenPayload(BaseModel):
    sub: UUID
    role: Role
    exp: datetime


class UserRow(BaseModel):
    id: UUID
    username: str
    role: Role
    created_at: datetime


class UserRowWithPassword(UserRow):
    password_hash: str


class FeedbackCreate(BaseModel):
    title: str = Field(max_length=200)
    description: str = Field(min_length=1)
    source: Source
    priority: Priority
    status: Status = Status.new


class ErrorResponse(BaseModel):
    detail: str
    status_code: int
    request_id: str

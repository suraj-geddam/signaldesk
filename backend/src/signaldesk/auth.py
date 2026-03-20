from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from signaldesk.config import Settings, get_settings
from signaldesk.db import DatabaseConnection, get_connection
from signaldesk.middleware import limiter
from signaldesk.queries import get_user_by_id, get_user_by_username
from signaldesk.schemas import LoginRequest, LoginResponse, Role, TokenPayload, UserRow

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_ALGORITHM = "HS256"
AUTH_ERROR_HEADERS = {"WWW-Authenticate": "Bearer"}


def create_access_token(user: UserRow, settings: Settings) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expiry_minutes)
    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, settings: Settings) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
        return TokenPayload.model_validate(payload)
    except (JWTError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers=AUTH_ERROR_HEADERS,
        ) from exc


async def authenticate_user(
    connection: DatabaseConnection,
    username: str,
    password: str,
) -> UserRow | None:
    user = await get_user_by_username(connection, username)
    if user is None or not password_context.verify(password, user.password_hash):
        return None

    return UserRow(
        id=user.id,
        username=user.username,
        role=user.role,
        created_at=user.created_at,
    )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    connection: Annotated[DatabaseConnection, Depends(get_connection)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserRow:
    payload = decode_access_token(token, settings)
    user = await get_user_by_id(connection, payload.sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers=AUTH_ERROR_HEADERS,
        )

    return user


async def require_admin(user: Annotated[UserRow, Depends(get_current_user)]) -> UserRow:
    if user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return user


@router.post("/login", response_model=LoginResponse)
@limiter.limit(lambda: get_settings().rate_limit_login)
async def login(
    request: Request,
    credentials: LoginRequest,
    connection: Annotated[DatabaseConnection, Depends(get_connection)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    user = await authenticate_user(connection, credentials.username, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers=AUTH_ERROR_HEADERS,
        )

    return LoginResponse(
        access_token=create_access_token(user, settings),
        role=user.role,
    )


@router.get("/me", response_model=UserRow)
async def read_current_user(
    user: Annotated[UserRow, Depends(get_current_user)],
) -> UserRow:
    return user

from contextvars import ContextVar
from time import perf_counter
from uuid import uuid4

import structlog
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint

from app.config import get_settings
from app.logging import get_logger

request_id_var: ContextVar[str] = ContextVar("request_id", default="no-request")
logger = get_logger("signaldesk.http")


def _default_rate_limit() -> str:
    return get_settings().rate_limit_default


def _rate_limit_key(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        try:
            payload = jwt.get_unverified_claims(token)
        except JWTError:
            pass
        else:
            subject = payload.get("sub")
            if isinstance(subject, str):
                return f"user:{subject}"

    remote_address = get_remote_address(request)
    return f"ip:{remote_address}"


limiter = Limiter(
    key_func=_rate_limit_key,
    default_limits=[_default_rate_limit],
    headers_enabled=False,
    storage_uri="memory://",
)


def get_request_id() -> str:
    return request_id_var.get()


async def request_id_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    incoming_request_id = request.headers.get("X-Request-ID")
    request_id = incoming_request_id or str(uuid4())
    start = perf_counter()
    token = request_id_var.set(request_id)
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
    )
    try:
        response = await call_next(request)
    finally:
        structlog.contextvars.clear_contextvars()
        request_id_var.reset(token)

    structlog.contextvars.bind_contextvars(request_id=request_id)
    logger.info(
        "request_finished",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round((perf_counter() - start) * 1000, 3),
    )
    structlog.contextvars.clear_contextvars()
    response.headers["X-Request-ID"] = request_id
    return response


async def http_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise TypeError("HTTP exception handler received a non-HTTP exception.")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "request_id": get_request_id(),
        },
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise TypeError("Validation handler received a non-validation exception.")

    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "status_code": 422,
            "request_id": get_request_id(),
        },
    )


def rate_limit_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, RateLimitExceeded):
        raise TypeError("Rate-limit handler received a non-rate-limit exception.")

    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded: {exc.detail}",
            "status_code": 429,
            "request_id": get_request_id(),
        },
    )

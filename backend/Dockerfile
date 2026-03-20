FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY init.sql ./
RUN uv sync --frozen --no-dev

CMD ["sh", "-c", "uvicorn signaldesk.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

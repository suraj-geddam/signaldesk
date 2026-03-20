# SignalDesk

SignalDesk is a customer-feedback triage tool with a FastAPI backend, a React frontend, cached AI insights, and a Railway deployment target.

Currently live at https://signaldesk.up.railway.app/ (seeded with demo users and sample data).

Demo credentials: `admin / admin123`, `member / member123`.

## Features

- Feedback CRUD with text search, multi-value filters, pagination, sorting, and idempotent create
- JWT auth with `admin` and `member` roles
- Dashboard with status counts, priority counts, and a 7-day new-feedback trend
- Cached AI insights with stale-state detection and admin-triggered refresh
- Structured JSON logging, request IDs, per-route rate limiting, and consistent error envelopes
- Docker Compose local dev, CI via GitHub Actions, Railway deployment

## Architecture

```text
┌───────────────────────────┐
│  React + Vite + Tailwind  │
│  (Caddy in production)    │
└────────────┬──────────────┘
             │ HTTPS (JWT in Authorization header)
             v
┌───────────────────────────┐     ┌──────────────────────────┐
│  FastAPI                  │     │  OpenAI-compatible API    │
│  ├─ /auth/*               │────>│  (local llama/qwen or    │
│  ├─ /feedback/*           │     │   OpenAI in prod)        │
│  ├─ /dashboard            │     └──────────────────────────┘
│  ├─ /feedback/insights*   │
│  ├─ /health               │
│  ├─ middleware:            │
│  │   request IDs          │
│  │   structured logging   │
│  │   rate limiting        │
│  │   CORS                 │
│  │   error envelopes      │
│  └─ background tasks:     │
│      periodic AI refresh  │
└────────────┬──────────────┘
             │
             v
┌───────────────────────────┐
│  Postgres 16              │
│  ├─ users                 │
│  ├─ feedback              │
│  │   (pg_trgm GIN index)  │
│  └─ ai_summaries          │
└───────────────────────────┘
```

Repo layout:

```text
backend/
  src/signaldesk/   FastAPI app (src layout)
  tests/            pytest suite (runs against real Postgres)
  init.sql          schema bootstrap (idempotent, no migrations)
frontend/
  src/              React app
  e2e/              Playwright happy-path test
docker-compose.yml  local full-stack orchestration
.github/workflows/  CI (backend, frontend, e2e jobs)
```

## API

All endpoints except `/health` and `/auth/login` require a JWT token in the `Authorization: Bearer <token>` header.

Interactive OpenAPI docs are available at `/docs` when the backend is running.

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/login` | none | Returns `{access_token, token_type, role}` |
| `GET` | `/auth/me` | any | Returns the current user |

### Feedback

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/feedback` | any | Create feedback. Optional `Idempotency-Key` header for safe retries |
| `GET` | `/feedback` | any | List with pagination, search, filters, sorting (see query params below) |
| `GET` | `/feedback/{id}` | any | Get single feedback item |
| `PUT` | `/feedback/{id}` | any | Update. Members can only update their own; admins can update any |
| `DELETE` | `/feedback/{id}` | admin | Delete feedback |

List query params: `page`, `per_page` (max 100), `status`, `priority`, `source` (comma-separated for multi-value), `search` (ILIKE), `sort_by` (`created_at` or `priority`), `sort_order` (`asc` or `desc`).

### Dashboard

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/dashboard` | any | Status counts, priority counts, 7-day trend (zero-filled) |

### Insights

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/feedback/insights` | any | Latest cached insights with `stale` flag |
| `POST` | `/feedback/insights/refresh` | admin | Trigger background regeneration (returns `202`) |

The insights flow: a periodic background task checks whether the feedback hash has changed since the last generation and regenerates if stale. An admin can also force-refresh via the endpoint above. If the AI API is unavailable, the last cached summary is preserved and served with `stale: true`.

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | none | Returns `{status: "ok", db: "connected"}` if Postgres is reachable |

### Error contract

All error responses follow a consistent envelope:

```json
{
  "detail": "Human-readable message (or validation error array for 422s)",
  "status_code": 422,
  "request_id": "uuid"
}
```

Every response includes an `X-Request-ID` header. If the client sends one, it is propagated; otherwise one is generated.

### Rate limits

Defaults (configurable via env): `60/minute` general, `10/minute` login, `5/minute` AI refresh. Rate limiting keys on JWT subject when authenticated, or on client IP otherwise. Current storage is in-memory (per-process); see Tradeoffs.

## Local Setup

Prereqs: Docker with Compose, Node.js + npm, `uv`.

1. Copy env defaults:

```bash
cp .env.example .env
```

2. Start the local stack:

```bash
docker compose up --build -d
```

3. Seed local demo users:

```bash
cd backend
DATABASE_URL=postgresql://signaldesk:signaldesk@localhost:5432/signaldesk \
uv run python -m signaldesk.seed users --use-demo-passwords
```

4. Open the app:

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

Demo credentials after seeding: `admin / admin123`, `member / member123`.

## Local Development Commands

Backend:

```bash
cd backend
uv sync --all-groups
uv run ruff check .
uv run pyright
DATABASE_URL='postgresql://signaldesk:signaldesk@localhost:5432/signaldesk_test?sslmode=disable' \
uv run pytest --tb=short
```

Frontend:

```bash
cd frontend
npm install
npm test
npx tsc -b
```

Full-stack browser e2e:

```bash
docker compose up -d db backend frontend
cd frontend
npm run test:e2e
```

## Environment Variables

All backend config is via environment variables (loaded by pydantic-settings). Required variables have no default and must be set explicitly.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | yes | — | Postgres connection string |
| `JWT_SECRET` | yes | — | HMAC signing key for JWTs |
| `OPENAI_API_BASE` | no | `http://localhost:8080/v1` | OpenAI-compatible endpoint |
| `OPENAI_API_KEY` | no | `not-needed` | API key for the AI provider |
| `OPENAI_MODEL` | no | `gpt-4o-mini` | Model name for structured output |
| `AI_REFRESH_INTERVAL_MINUTES` | no | `30` | Periodic insight refresh cadence |
| `AI_MAX_FEEDBACK_ITEMS` | no | `500` | Max feedback items sent per generation |
| `AI_TIMEOUT_SECONDS` | no | `30` | HTTP timeout for AI calls |
| `AI_MAX_RETRIES` | no | `3` | Retry count for AI calls |
| `DB_POOL_MIN` | no | `2` | asyncpg pool minimum connections |
| `DB_POOL_MAX` | no | `10` | asyncpg pool maximum connections |
| `JWT_EXPIRY_MINUTES` | no | `1440` | Token lifetime (default 24h) |
| `RATE_LIMIT_DEFAULT` | no | `60/minute` | General rate limit |
| `RATE_LIMIT_LOGIN` | no | `10/minute` | Login rate limit |
| `RATE_LIMIT_AI_REFRESH` | no | `5/minute` | AI refresh rate limit |
| `CORS_ORIGINS` | no | `http://localhost:5173` | Comma-separated allowed origins |
| `LOG_LEVEL` | no | `INFO` | structlog level |

## Deployment

Railway is configured as a monorepo with three services: Postgres, backend (from `/backend`), and frontend (from `/frontend`).

- Backend config: `backend/railway.json`
- Frontend config: `frontend/railway.json`
- `watchPatterns` use monorepo-root paths (e.g., `/backend/src/**`) because Railway evaluates them from `/`, not from the service root
- Frontend production serving uses Caddy with gzip/zstd compression and SPA fallback, not the Vite dev server

Deploy checklist:

1. Create Railway Postgres, backend, and frontend services.
2. Set backend vars: `DATABASE_URL`, `JWT_SECRET`, `OPENAI_API_BASE`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `CORS_ORIGINS`.
3. Set frontend var: `VITE_API_BASE_URL=https://<backend-domain>`.
4. Seed users: `python -m signaldesk.seed users --admin-password '...' --member-password '...'`

## Tradeoffs

**Raw SQL over an ORM.** More explicit and easier to walk through in review. The dynamic WHERE clause in `list_feedback` builds parameterized queries safely but would get unwieldy with many more filters — an ORM or query builder would be the next step.

**Cached insights instead of on-demand AI calls.** Cheaper, more predictable latency, and the UI stays fast. The tradeoff is that insights can go stale between refreshes, which is surfaced via the `stale` flag and a frontend warning banner.

**In-memory rate limiting.** Fine for a single-process MVP. Limits are per-process, so horizontally scaled replicas each maintain independent counters. Production fix: Redis-backed storage via `slowapi`'s Redis URI option.

**SQL bootstrap instead of a migration framework.** The `init.sql` script uses `CREATE TABLE IF NOT EXISTS` and `DROP TRIGGER IF EXISTS` for idempotent re-runs. For a long-lived schema this would need Alembic-style versioned migrations.

**Text search via pg_trgm ILIKE.** Good enough for substring matching on a small dataset with the GIN index. Full-text search (tsvector/tsquery) would be the next step for relevance ranking and language-aware stemming.

**No separate frontend API client generation.** The frontend TypeScript types mirror the backend Pydantic models manually. For a larger team, OpenAPI codegen would keep them in sync automatically.

## One More Week

1. Redis-backed rate limiting and background job coordination (Celery or arq).
2. Proper SQL migrations via Alembic with deploy rollback safety.
3. Bulk feedback import tooling for seeding larger AI evaluation datasets.
4. Richer insights observability: refresh history, latency/error metrics, admin feedback on quality.
5. More browser e2e coverage: filter combinations, edit flows, stale-insight states, error recovery.
6. OpenAPI client codegen to keep frontend types in sync with the backend contract.

## Additional Docs

- [RUNBOOK.md](RUNBOOK.md)
- [AI_USAGE_DISCLOSURE.md](AI_USAGE_DISCLOSURE.md)
- [TEST_REPORT.md](TEST_REPORT.md)

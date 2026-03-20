# SignalDesk

SignalDesk is an customer-feedback triage tool with a FastAPI backend, a React frontend, cached AI insights, and a Railway deployment target.

Currently live at https://signaldesk.up.railway.app/ (seeded with demo users and sample data)

## Features

- Feedback CRUD with search, filters, pagination, sorting, and idempotent create
- JWT auth with `admin` and `member` roles
- Dashboard with status counts, priority counts, and a 7-day trend
- Cached AI insights with stale-state handling and admin-triggered refresh
- Structured JSON logging, request IDs, rate limiting, and consistent error envelopes
- Docker Compose for local development and Railway config for deployment

## Architecture

```text
React + Vite frontend
        |
        v
FastAPI backend
        |
        +--> Postgres
        |
        +--> OpenAI-compatible API
             - local: llama/qwen-style server via OPENAI_API_BASE
             - prod: OpenAI
```

Repo layout:

```text
backend/
  src/signaldesk/   FastAPI app
  tests/            backend tests
frontend/
  src/              React app
  e2e/              Playwright flow
docker-compose.yml  local full-stack orchestration
```

## Local Setup

Prereqs:

- Docker with Compose support
- Node.js + npm
- `uv`

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

Demo credentials after seeding:

- `admin / admin123`
- `member / member123`

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

## Environment

Backend config is driven by environment variables. The most important ones are:

- `DATABASE_URL`
- `JWT_SECRET`
- `OPENAI_API_BASE`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `CORS_ORIGINS`

Local dev defaults to an OpenAI-compatible server at `http://localhost:8080/v1`. Production should set `OPENAI_API_BASE=https://api.openai.com/v1` and provide a real `OPENAI_API_KEY`.

## Deployment

Railway is configured as a monorepo with three services:

- Postgres
- backend from `/backend`
- frontend from `/frontend`

Important details:

- backend config lives in `backend/railway.json`
- frontend config lives in `frontend/railway.json`
- `watchPatterns` are monorepo-rooted because Railway evaluates them from `/`, not from the service root directory
- frontend production serving uses Caddy, not the Vite dev server

Deploy-time checklist:

1. Create Railway Postgres, backend, and frontend services.
2. Set backend vars: `DATABASE_URL`, `JWT_SECRET`, `OPENAI_API_BASE`, `OPENAI_API_KEY`, `OPENAI_MODEL`.
3. Set frontend var: `VITE_API_BASE_URL=https://<backend-domain>`.
4. Set backend `CORS_ORIGINS=https://<frontend-domain>`.
5. Seed users explicitly with `python -m signaldesk.seed users ...`.

## Tradeoffs

- Raw SQL over an ORM: more explicit and easier to explain in a small codebase.
- Cached insights instead of on-demand AI calls: cheaper, more reliable, and keeps the UI fast.
- In-memory rate limiting: fine for a single-process MVP, but not ideal for horizontally scaled production.
- SQL bootstrap instead of a migration framework: fast for an MVP, but Alembic-style migrations would be better for long-lived schema evolution.

## One More Week

If I had one more week, I would prioritize:

1. Redis-backed rate limiting and background job coordination.
2. Proper SQL migrations and deploy rollback safety.
3. Bulk feedback seed/import tooling for larger AI evaluation datasets.
4. Better insights observability: refresh history view, latency/error metrics, richer admin feedback.
5. More browser-level QA coverage across filters, editing, and stale-insights states.

## Additional Docs

- [RUNBOOK.md](RUNBOOK.md)
- [AI_USAGE_DISCLOSURE.md](AI_USAGE_DISCLOSURE.md)
- [TEST_REPORT.md](TEST_REPORT.md)

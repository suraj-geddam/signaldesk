# Runbook

Operational reference for running, debugging, and maintaining SignalDesk.

## Services

| Service | Stack | Local port |
|---------|-------|------------|
| Backend | FastAPI + uvicorn | `8000` |
| Frontend | Vite dev / Caddy prod | `5173` (dev) |
| Database | Postgres 16 | `5432` |
| AI provider | OpenAI-compatible endpoint | configured via `OPENAI_API_BASE` |

## Common Commands

Start local stack:

```bash
docker compose up --build -d
```

Tail logs:

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

Reset local database (destroys all data):

```bash
docker compose down -v
docker compose up --build -d
```

Seed users:

```bash
cd backend
DATABASE_URL=postgresql://signaldesk:signaldesk@localhost:5432/signaldesk \
uv run python -m signaldesk.seed users --use-demo-passwords
```

## Observability

Backend logs are structured JSON via structlog. Every log line includes a `request_id` field that matches the `X-Request-ID` response header.

Key log events to watch:

| Event | Level | Meaning |
|-------|-------|---------|
| `request_started` | INFO | Incoming request (method, path) |
| `request_finished` | INFO | Completed request (status_code, duration_ms) |
| `insights_generation_started` | INFO | AI generation kicked off (feedback_count, model, force flag) |
| `insights_generation_succeeded` | INFO | AI generation completed (insight_count) |
| `insights_generation_skipped` | INFO | Skipped because feedback hash unchanged or no feedback exists |
| `insights_generation_failed` | ERROR | AI call failed (exception details in stack trace) |
| `periodic_ai_refresh_failed` | ERROR | Background refresh loop hit an error (non-fatal, loop continues) |

To trace a single request: search logs for the `request_id` value from the `X-Request-ID` response header.

To monitor AI health: filter for events starting with `insights_generation_`. A healthy system shows periodic `skipped` events (no new feedback) interspersed with `started` → `succeeded` pairs when feedback changes.

## Common Failure Modes

### Login fails on a fresh environment

Cause: users are not auto-seeded; the schema bootstrap creates tables but does not insert users.

Fix:

```bash
cd backend
DATABASE_URL=<db-url> uv run python -m signaldesk.seed users \
  --admin-password '<admin-password>' \
  --member-password '<member-password>'
```

### Frontend shows CORS errors in the browser console

Cause: backend `CORS_ORIGINS` does not include the frontend origin.

Fix:

- Local: `CORS_ORIGINS=http://localhost:5173`
- Railway: `CORS_ORIGINS=https://<frontend-domain>`
- Redeploy backend after changing.

### `/feedback/insights/refresh` returns `202` but insights never update

Diagnosis:

1. Check backend logs for `insights_generation_started` — if absent, the background task did not fire.
2. Check for `insights_generation_failed` — this means the AI call errored. The stack trace will show the cause.
3. Verify `OPENAI_API_BASE`, `OPENAI_API_KEY`, and `OPENAI_MODEL` are set correctly and the model supports structured output (chat completions with `response_format`).
4. Check that feedback items actually exist — generation is skipped when feedback count is zero.

Notes:

- Manual admin refresh always forces regeneration when feedback exists, even if the feedback hash is unchanged.
- Periodic refresh skips regeneration when the feedback hash is unchanged (optimization to avoid redundant AI calls).

### Railway push does not trigger a deploy

Check:

- Service root directory is correct in Railway settings.
- Service config path points to `/backend/railway.json` or `/frontend/railway.json`.
- `watchPatterns` use monorepo-root paths like `/backend/src/**`, not `src/**`.

### Backend tests cannot reach Postgres locally

Tests require a dedicated `_test` database. The test harness auto-creates it if it does not exist, but Postgres itself must be running:

```bash
docker compose up -d db
cd backend
DATABASE_URL='postgresql://signaldesk:signaldesk@localhost:5432/signaldesk_test?sslmode=disable' \
uv run pytest --tb=short
```

### Rate limiting behaves inconsistently across replicas

Cause: limiter storage is in-memory, so each process maintains its own counters independently.

Mitigation: acceptable for this single-process MVP. Production scale-out should move limiter state to Redis by changing the `storage_uri` in the Limiter constructor.

## Local Debugging

Health check:

```bash
curl http://localhost:8000/health
```

Login and capture token:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H 'content-type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

Create feedback:

```bash
curl -X POST http://localhost:8000/feedback \
  -H "Authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"title":"Test item","description":"Testing via curl","source":"other","priority":"medium"}'
```

Trigger insights refresh:

```bash
curl -X POST http://localhost:8000/feedback/insights/refresh \
  -H "Authorization: Bearer $TOKEN"
```

Read insights:

```bash
curl http://localhost:8000/feedback/insights \
  -H "Authorization: Bearer $TOKEN"
```

Backend quality checks:

```bash
cd backend
uv run ruff check .
uv run pyright
DATABASE_URL='postgresql://signaldesk:signaldesk@localhost:5432/signaldesk_test?sslmode=disable' \
uv run pytest --tb=short
```

Frontend quality checks:

```bash
cd frontend
npm test
npx tsc -b
npm run test:e2e  # requires docker compose stack running
```

## Config Rotation

### JWT secret

1. Generate a new secret.
2. Update backend `JWT_SECRET`.
3. Redeploy backend.

Effect: all existing sessions are invalidated immediately. Users must re-login.

### OpenAI key

1. Update backend `OPENAI_API_KEY`.
2. Redeploy backend.

Effect: only new AI refreshes use the new key. Cached summaries remain intact.

### Database credentials

1. Update `DATABASE_URL`.
2. Redeploy backend.
3. Reseed users only if pointing at a new empty database.

### CORS origins

Update when the frontend domain changes:

1. Update backend `CORS_ORIGINS`.
2. Redeploy backend.

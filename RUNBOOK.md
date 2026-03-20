# Runbook

This runbook covers the common operating and debugging paths for SignalDesk.

## Services

- Backend: FastAPI in `backend/src/signaldesk`
- Frontend: Vite/Caddy app in `frontend`
- Database: Postgres 16
- AI provider: OpenAI-compatible endpoint configured through env vars

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

Reset local database:

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

## Common Failure Modes

### Login fails on a fresh environment

Cause:

- users are not auto-seeded anymore

Fix:

```bash
cd backend
DATABASE_URL=<db-url> uv run python -m signaldesk.seed users \
  --admin-password '<admin-password>' \
  --member-password '<member-password>'
```

### Frontend shows CORS failures in the browser

Cause:

- backend `CORS_ORIGINS` does not include the frontend origin

Fix:

- local: `CORS_ORIGINS=http://localhost:5173`
- Railway: `CORS_ORIGINS=https://<frontend-domain>`
- redeploy backend

### `/feedback/insights/refresh` returns `202` but no insights appear

Check:

1. backend logs for `insights_generation_started`
2. backend logs for `insights_generation_succeeded` or `insights_generation_failed`
3. `OPENAI_API_BASE`, `OPENAI_API_KEY`, and `OPENAI_MODEL`
4. whether the configured model/server supports the expected OpenAI-compatible chat interface

Useful backend log events:

- `insights_generation_started`
- `insights_generation_skipped`
- `insights_generation_succeeded`
- `insights_generation_failed`
- `periodic_ai_refresh_failed`

Notes:

- manual admin refresh now forces regeneration when feedback exists
- periodic refresh still skips redundant work when the feedback hash is unchanged

### Railway push does not trigger deploy

Check:

- service root directory is correct
- service config path points to `/backend/railway.json` or `/frontend/railway.json`
- `watchPatterns` use monorepo-root paths like `/backend/src/**`, not `src/**`

### Backend tests cannot reach Postgres locally

Use a dedicated local test DB URL:

```bash
cd backend
DATABASE_URL='postgresql://signaldesk:signaldesk@localhost:5432/signaldesk_test?sslmode=disable' \
uv run pytest --tb=short
```

### Rate limiting behaves inconsistently across replicas

Cause:

- current limiter storage is in-memory, so limits are per-process

Mitigation:

- acceptable for this MVP
- production scale-out should move limiter state to Redis

## Local Debugging

Health check:

```bash
curl http://localhost:8000/health
```

Login:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H 'content-type: application/json' \
  -d '{"username":"member","password":"member123"}'
```

Manual insights refresh:

```bash
curl -X POST http://localhost:8000/feedback/insights/refresh \
  -H "Authorization: Bearer <admin-jwt>"
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
npm run test:e2e
```

## Config Rotation

### JWT secret

Rotate:

- generate a new secret
- update backend `JWT_SECRET`
- redeploy backend

Effect:

- all existing JWT sessions become invalid immediately

### OpenAI key

Rotate:

- update backend `OPENAI_API_KEY`
- redeploy backend

Effect:

- only new AI refreshes use the new key
- cached summaries remain intact

### Database credentials / URL

Rotate:

- update `DATABASE_URL`
- redeploy backend
- reseed users only if you are pointing at a new empty database

### CORS origins

Rotate when:

- frontend domain changes

Action:

- update backend `CORS_ORIGINS`
- redeploy backend

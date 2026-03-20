# Test Report

Final verification pass for the shipped SignalDesk MVP.

## Commands Run

Backend static analysis:

```bash
cd backend
uv run ruff check .        # linter
uv run pyright              # type checker
```

Backend tests (against real Postgres):

```bash
cd backend
DATABASE_URL='postgresql://signaldesk:signaldesk@localhost:5432/signaldesk_test?sslmode=disable' \
uv run pytest --tb=short
```

Frontend static analysis and unit tests:

```bash
cd frontend
npx tsc -b                  # type checker
npm test                    # vitest
```

Full-stack browser e2e:

```bash
docker compose up -d db backend frontend
cd frontend
npm run test:e2e            # playwright
```

## Results

Final local pass on March 20, 2026:

| Suite | Tool | Result |
|-------|------|--------|
| Backend lint | ruff | passed, 0 issues |
| Backend types | pyright | passed, 0 errors, 0 warnings |
| Backend tests | pytest | 39 passed |
| Frontend types | tsc | passed |
| Frontend tests | vitest | 27 passed |
| Browser e2e | playwright | 1 test, 1 passed |

Deployment verification (Railway):

- `/health` returned `ok`
- Login, feedback create, dashboard, insights view, and admin delete all exercised manually
- Insights refresh verified end-to-end: triggered refresh, confirmed OpenAI platform usage logs showed the prod call was actually made, verified new insights rendered in the UI

## Coverage Summary

No line-by-line coverage percentage is reported. Below is a summary of what the test suites exercise.

**Backend (39 tests across 8 test files):**

- Auth: login, token validation, `/auth/me`
- Feedback CRUD: create, get, list, update, delete
- Idempotency: duplicate idempotency key returns the original row
- Authorization: member cannot update other users' feedback, member cannot delete, admin can delete
- List: text search, pagination, multi-value filters, sorting by priority and created_at
- Dashboard: grouped status/priority counts, 7-day trend with zero-fill
- Insights: placeholder response, fresh cached summary, stale detection, hash-based skip, force regeneration, AI failure preservation, malformed AI response rejection, admin refresh endpoint, periodic refresh failure logging
- Middleware: request ID generation/propagation, validation error envelopes, HTTP error envelopes, rate limiting (default, login, AI refresh), structured request logging with metadata
- Deployment: idempotent schema bootstrap, app startup without pre-seeded users, explicit seed command

**Frontend (27 tests across 6 test files):**

- Login flow and protected-route redirect behavior
- Feedback table rendering, filter bar state management, modal interactions (detail view, edit mode)
- Dashboard metric card and trend chart rendering
- Insights page: empty state, stale warning, refresh polling, polling cleanup on unmount
- Error boundary smoke test
- Debounce hook behavior

**Browser e2e (1 Playwright test, 10 steps):**

- Member login → create feedback → verify table row → open detail modal → edit status → dashboard counts → insights empty state (member) → logout → admin login → admin insights refresh (with mocked GET to verify polling) → admin delete → verify empty table

## Known Gaps

- No line-by-line coverage percentage (no `--cov` flag configured)
- Browser e2e covers one happy path, not a regression matrix across filter/sort combinations or error recovery flows
- AI insights quality is validated functionally (structured output parsing, failure fallback) but not benchmarked against a large seeded dataset
- Rate limiting is tested at the unit level; no load testing of multi-instance production behavior

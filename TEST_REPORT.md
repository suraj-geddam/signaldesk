# Test Report

This report captures the final verification pass for the shipped SignalDesk MVP.

## Commands Run

Backend static checks:

```bash
cd backend
uv run ruff check .
uv run pyright
```

Backend tests:

```bash
cd backend
DATABASE_URL='postgresql://signaldesk:signaldesk@localhost:5432/signaldesk_test?sslmode=disable' \
uv run pytest --tb=short
```

Frontend tests:

```bash
cd frontend
npm test
npx tsc -b
```

Full-stack e2e:

```bash
docker compose up -d db backend frontend
cd frontend
npm run test:e2e
```

## Results

Final local pass on March 20, 2026:

- `backend`: `ruff` passed
- `backend`: `pyright` passed with `0 errors, 0 warnings`
- `backend`: `pytest` passed with `39 passed`
- `frontend`: `vitest` passed with `27 passed`
- `frontend`: `tsc -b` passed
- `frontend`: `playwright` passed with `1 passed`

Additional deployment verification:

- Railway backend health endpoint returned `ok`
- Railway login, feedback create, dashboard view, insights view, and admin delete were exercised manually
- Railway insights refresh was verified after the forced-refresh fix; OpenAI platform usage confirmed the prod call path was actually reached

## Rough Coverage Summary

Backend coverage areas exercised:

- auth login and `/auth/me`
- feedback create, list, get, update, delete
- idempotency behavior
- member/admin authorization rules
- dashboard aggregation
- insights placeholder, cached reads, stale handling, manual refresh, periodic refresh failure logging
- request IDs, handled validation/error envelopes, structured request logging, and rate limiting
- deployment/bootstrap behavior and explicit user seeding
- one API-level happy-path e2e flow across core backend functionality

Frontend coverage areas exercised:

- login flow and protected-route behavior
- feedback table rendering, filters, modal interactions, CRUD flow
- dashboard rendering
- insights empty state, stale state, refresh polling, and polling cleanup
- error boundary smoke coverage
- end-to-end browser flow across login, feedback, dashboard, insights page, and admin delete

## Known Gaps

- no line-by-line coverage percentage is reported
- browser e2e currently focuses on one happy-path flow, not a full regression matrix
- AI insights correctness is validated functionally, but not yet benchmarked against a large seeded dataset
- multi-instance production behavior is not load-tested; current rate limiting is still in-memory per process

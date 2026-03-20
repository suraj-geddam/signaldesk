# AI Usage Disclosure

AI tools were used during planning, implementation, review, and documentation. All code and configuration changes were manually inspected, tested, and in several cases corrected or rewritten before merge.

## Tools Used

- Claude on the web
- Codex / GPT-5.4 high

## Where AI Was Used

### Claude

- early planning and design discussion
- frontend-oriented implementation and design work
- review feedback and concern-spotting on completed slices

### Codex

- backend implementation and refactors
- tests, CI, Docker, and Railway deployment setup
- auth, feedback, dashboard, insights, middleware, packaging, and repo layout work
- debugging and follow-up fixes during deployment
- final project documentation

## Modified Or Corrected After AI Output

- default credential seeding was removed from schema bootstrap and replaced with an explicit seed command because public deploys should not expose baked-in demo users
- manual insights refresh was changed to force regeneration because the original cache-skip behavior made the UI look broken when an admin explicitly clicked refresh
- Railway watch patterns were corrected to monorepo-rooted paths because Railway evaluates them from `/`, not from the configured service root directory
- backend packaging was moved to `backend/src/signaldesk` to use a standard Python `src` layout and avoid import-path hacks
- several review concerns were accepted and fixed later, including stronger real-Postgres test coverage and better cleanup around frontend polling

## Rejected Or Not Accepted Blindly

- older assumptions in the initial HLD/LLD were not followed blindly when they conflicted with a cleaner implementation or production safety
- automated demo-user creation in production-facing environments was explicitly rejected
- any AI-generated change that did not pass local checks, CI, or real runtime verification was revised before merge

## Validation Process

- linting and type checking on backend and frontend
- backend pytest suite against Postgres
- frontend Vitest suite
- Playwright happy-path e2e against the Docker Compose stack
- manual verification against the Railway deployment

## Human Responsibility

The final merged code, deployment setup, and documentation were accepted only after manual review and validation. AI accelerated the work, but did not replace engineering judgment, testing, or debugging.

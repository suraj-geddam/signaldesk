# AI Usage Disclosure

AI tools were used during planning, implementation, review, and documentation.

## Tools Used

- Claude on the web
- Codex / GPT-5.4 high
- Claude Code / Claude Opus 4.6 high

## Workflow Steps

- Initial high level design (Claude on the web)
- Low level design for the backend (Claude on the web)
- CI & DB setup (Codex)
- Backend implementation (Codex)
- Low level design for the frontend (against stable backend) (Claude on the web)
- Frontend implementation (Claude Code)
- Review the repo parallely (Claude on the web)
- Non-frontend review fixes (Codex)
- Frontend fixes (Claude Code)
- Backend refactor (Codex)
- Deployment (assisted by Codex)
- Final documentation (assisted by Codex)

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

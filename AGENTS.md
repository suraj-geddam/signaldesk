# Agents

When working on this project, output any plans, intermediate artifacts, or working documents to the `internal-docs/` directory. This folder is gitignored and will not be pushed to the remote repository.

Keep changes grouped into small, human-readable commits rather than large batches of unrelated edits.

Once a baseline has been established, implement additional features on a feature branch instead of continuing directly on the baseline branch.

Do not create merge commits in this repository; keep history linear and use rebase-based workflows.

While this is still a one-person project, do not require pull requests for every completed feature branch.

When a feature branch is complete, first verify it works locally with appropriate checks (CI-equivalent tests and lightweight endpoint/manual checks such as `curl` where relevant), then rebase it onto `main` and merge it back to `main` without a merge commit.

After a feature branch has been merged into `main` and pushed, delete the merged feature branch locally and on the remote unless there is a specific reason to keep it.

Use Conventional Commits style for commit messages.

When creating commits from Codex, include the configured Codex co-author attribution or trailer if it is available so the commit history reflects agent authorship.

Follow TDD by default: write or adjust a failing test first, make it pass with the smallest viable change, then refactor if needed.

After a frontend exists, use the `agent-browser` command with the `agent-browser` and `dogfood` skills to verify end-to-end behavior before considering frontend features complete.

If implementation intentionally deviates from the LLD, record the deviation and the reason in `internal-docs/implementation-progress.md`.

import { execFileSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(frontendDir, "..");
const databaseUrl =
  process.env.E2E_CONTAINER_DATABASE_URL ??
  "postgresql://signaldesk:signaldesk@db:5432/signaldesk";

export default function globalSetup(): void {
  execFileSync(
    "docker",
    [
      "compose",
      "exec",
      "-T",
      "backend",
      "sh",
      "-lc",
      [
        `DATABASE_URL=${databaseUrl}`,
        "uv run python -m signaldesk.seed users",
        `--database-url ${databaseUrl}`,
        "--use-demo-passwords",
      ].join(" "),
    ],
    {
      cwd: repoRoot,
      env: process.env,
      stdio: "inherit",
    },
  );
}

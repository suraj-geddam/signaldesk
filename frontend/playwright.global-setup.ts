import { execFileSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(frontendDir, "..");
const databaseUrl =
  process.env.E2E_DATABASE_URL ??
  "postgresql://signaldesk:signaldesk@localhost:5432/signaldesk";

export default function globalSetup(): void {
  execFileSync(
    "uv",
    [
      "run",
      "python",
      "-m",
      "app.seed",
      "users",
      "--database-url",
      databaseUrl,
      "--use-demo-passwords",
    ],
    {
      cwd: repoRoot,
      env: {
        ...process.env,
        DATABASE_URL: databaseUrl,
      },
      stdio: "inherit",
    },
  );
}

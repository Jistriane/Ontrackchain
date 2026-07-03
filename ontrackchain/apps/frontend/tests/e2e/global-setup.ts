import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

const DEMO_ORGANIZATION_ID = "00000000-0000-0000-0000-000000000001";
const RESET_SQL = `
  DO $$
  BEGIN
    IF EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = 'public'
        AND table_name = 'organizations'
        AND column_name IN ('id', 'credits_available', 'credits_reserved', 'credits_used_total', 'updated_at')
      GROUP BY table_schema, table_name
      HAVING COUNT(DISTINCT column_name) = 5
    ) THEN
      UPDATE organizations
      SET credits_available = 1000.0000,
          credits_reserved = 0,
          credits_used_total = 0,
          updated_at = NOW()
      WHERE id = '${DEMO_ORGANIZATION_ID}';
    END IF;
  END
  $$;
`;

export default async function globalSetup() {
  if (process.env.ONTRACKCHAIN_E2E_RESET_STATE === "false") {
    return;
  }

  const workspaceRoot = resolve(__dirname, "../../../..");
  const composeFile = resolve(workspaceRoot, "docker-compose.yml");
  const allowNoPostgres = process.env.ONTRACKCHAIN_E2E_ALLOW_NO_POSTGRES === "true";
  const failOnResetError = process.env.CI === "true" && !allowNoPostgres;

  if (process.env.ONTRACKCHAIN_E2E_RESET_RATE_LIMIT !== "false") {
    try {
      execFileSync("docker", ["compose", "-f", composeFile, "restart", "traefik"], {
        cwd: workspaceRoot,
        stdio: "pipe"
      });
    } catch (error) {
      if (process.env.CI === "true") {
        throw error;
      }
      console.warn("[e2e global-setup] falha ao reiniciar traefik para resetar rate-limit; seguindo em frente.");
    }
  }

  if (process.env.ONTRACKCHAIN_E2E_ENSURE_WORKERS !== "false") {
    try {
      execFileSync("docker", ["compose", "-f", composeFile, "up", "-d", "investigation-worker"], {
        cwd: workspaceRoot,
        stdio: "pipe"
      });
    } catch (error) {
      if (process.env.CI === "true") {
        throw error;
      }
      console.warn("[e2e global-setup] falha ao garantir investigation-worker ativo; seguindo em frente.");
    }
  }

  try {
    execFileSync(
      "docker",
      [
        "compose",
        "-f",
        composeFile,
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        "ontrackchain",
        "-d",
        "ontrackchain",
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
        RESET_SQL
      ],
      {
        cwd: workspaceRoot,
        stdio: "pipe"
      }
    );
  } catch (error) {
    if (failOnResetError) {
      throw error;
    }

    const details =
      error instanceof Error && "stderr" in error && typeof (error as { stderr?: unknown }).stderr === "string"
        ? (error as { stderr: string }).stderr
        : "";
    console.warn(
      `[e2e global-setup] reset de estado no postgres falhou; seguindo sem reset (CI estrito desabilitado). ${details}`.trim()
    );
  }
}

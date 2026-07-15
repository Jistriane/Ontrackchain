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

type ComposeCommandOptions = {
  input?: string;
};

function runDockerCompose(workspaceRoot: string, composeFile: string, args: string[], options: ComposeCommandOptions = {}) {
  execFileSync("docker", ["compose", "-f", composeFile, ...args], {
    cwd: workspaceRoot,
    stdio: "pipe",
    ...options
  });
}

function readCommandStderr(error: unknown) {
  if (typeof error !== "object" || error === null || !("stderr" in error)) {
    return "";
  }

  const stderr = (error as { stderr?: unknown }).stderr;
  if (typeof stderr === "string") {
    return stderr;
  }
  if (stderr instanceof Buffer) {
    return stderr.toString("utf8");
  }
  return "";
}

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
      runDockerCompose(workspaceRoot, composeFile, ["restart", "traefik"]);
    } catch (error) {
      if (process.env.CI === "true") {
        throw error;
      }
      console.warn("[e2e global-setup] falha ao reiniciar traefik para resetar rate-limit; seguindo em frente.");
    }
  }

  if (process.env.ONTRACKCHAIN_E2E_ENSURE_FRONTEND !== "false") {
    try {
      runDockerCompose(workspaceRoot, composeFile, ["up", "-d", "frontend", "traefik"]);
    } catch (error) {
      if (process.env.CI === "true") {
        throw error;
      }
      console.warn("[e2e global-setup] falha ao garantir frontend/traefik ativos; seguindo em frente.");
    }
  }

  if (process.env.ONTRACKCHAIN_E2E_ENSURE_CORE_APIS !== "false") {
    try {
      runDockerCompose(workspaceRoot, composeFile, [
        "up",
        "-d",
        "auth-service",
        "compliance-api",
        "report-api",
        "investigation-api",
        "monitoring-api"
      ]);
    } catch (error) {
      if (process.env.CI === "true") {
        throw error;
      }
      console.warn("[e2e global-setup] falha ao garantir APIs centrais ativas; seguindo em frente.");
    }
  }

  if (process.env.ONTRACKCHAIN_E2E_ENSURE_WORKERS !== "false") {
    try {
      runDockerCompose(workspaceRoot, composeFile, ["up", "-d", "investigation-worker"]);
    } catch (error) {
      if (process.env.CI === "true") {
        throw error;
      }
      console.warn("[e2e global-setup] falha ao garantir investigation-worker ativo; seguindo em frente.");
    }
  }

  try {
    runDockerCompose(workspaceRoot, composeFile, [
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
    ]);
  } catch (error) {
    if (failOnResetError) {
      throw error;
    }

    const details = readCommandStderr(error);
    console.warn(
      `[e2e global-setup] reset de estado no postgres falhou; seguindo sem reset (CI estrito desabilitado). ${details}`.trim()
    );
  }
}

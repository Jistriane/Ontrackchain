import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

const DEMO_ORGANIZATION_ID = "00000000-0000-0000-0000-000000000001";
const RESET_SQL = `
  UPDATE organizations
  SET credits_available = 1000.0000,
      credits_reserved = 0,
      credits_used_total = 0,
      updated_at = NOW()
  WHERE id = '${DEMO_ORGANIZATION_ID}';
`;

export default async function globalSetup() {
  if (process.env.ONTRACKCHAIN_E2E_RESET_STATE === "false") {
    return;
  }

  const workspaceRoot = resolve(__dirname, "../../../..");
  const composeFile = resolve(workspaceRoot, "docker-compose.yml");

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
      stdio: "inherit"
    }
  );
}

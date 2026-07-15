import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

export const LINKED_USER_ID = "00000000-0000-0000-0000-000000000002";

const WORKSPACE_ROOT = resolve(__dirname, "../../../..");

function runPostgresPsql(script: string) {
  return execFileSync(
    "docker",
    ["compose", "exec", "-T", "postgres", "psql", "-U", "ontrackchain", "-d", "ontrackchain", "-At", "-F", "|"],
    {
      cwd: WORKSPACE_ROOT,
      input: script,
      encoding: "utf8"
    }
  );
}

export type ExternalIdentitySnapshot = {
  hadPreviousIdentity: boolean;
  previousLinkedUserId: string;
  previousEmailSnapshot: string;
  previousRoleSnapshot: string;
};

export function psqlExec(script: string) {
  return runPostgresPsql(script);
}

export function sqlLiteral(value: string) {
  return `'${value.replace(/'/g, "''")}'`;
}

export function readExternalIdentitySnapshot(orgId: string, externalUserId: string): ExternalIdentitySnapshot {
  const previousIdentityRaw = psqlExec(`
    SELECT
      COALESCE(user_id::text, '') || '|' || COALESCE(email_snapshot, '') || '|' || COALESCE(role_snapshot, '')
    FROM external_identities
    WHERE organization_id = ${sqlLiteral(orgId)}
      AND provider = 'keycloak'
      AND external_subject = ${sqlLiteral(externalUserId)}
    LIMIT 1;
  `).trim();

  const [previousLinkedUserId = "", previousEmailSnapshot = "", previousRoleSnapshot = ""] =
    previousIdentityRaw.split("|");
  return {
    hadPreviousIdentity: previousIdentityRaw.length > 0,
    previousLinkedUserId,
    previousEmailSnapshot,
    previousRoleSnapshot
  };
}

export function upsertExternalIdentityLink(
  orgId: string,
  externalUserId: string,
  emailSnapshot: string,
  roleSnapshot: string
) {
  psqlExec(`
    INSERT INTO external_identities (organization_id, provider, external_subject, user_id, email_snapshot, role_snapshot, last_seen_at)
    VALUES (
      ${sqlLiteral(orgId)},
      'keycloak',
      ${sqlLiteral(externalUserId)},
      ${sqlLiteral(LINKED_USER_ID)},
      ${sqlLiteral(emailSnapshot)},
      ${sqlLiteral(roleSnapshot)},
      NOW()
    )
    ON CONFLICT (provider, external_subject, organization_id)
    DO UPDATE SET
      user_id = EXCLUDED.user_id,
      email_snapshot = EXCLUDED.email_snapshot,
      role_snapshot = EXCLUDED.role_snapshot,
      last_seen_at = NOW();
  `);
}

export function restoreExternalIdentity(orgId: string, externalUserId: string, snapshot: ExternalIdentitySnapshot) {
  psqlExec(`
    DELETE FROM external_identities
    WHERE organization_id = ${sqlLiteral(orgId)}
      AND provider = 'keycloak'
      AND external_subject = ${sqlLiteral(externalUserId)};

    ${snapshot.hadPreviousIdentity
      ? `
    INSERT INTO external_identities (organization_id, provider, external_subject, user_id, email_snapshot, role_snapshot, last_seen_at)
    VALUES (
      ${sqlLiteral(orgId)},
      'keycloak',
      ${sqlLiteral(externalUserId)},
      ${snapshot.previousLinkedUserId ? sqlLiteral(snapshot.previousLinkedUserId) : "NULL"},
      ${snapshot.previousEmailSnapshot ? sqlLiteral(snapshot.previousEmailSnapshot) : "NULL"},
      ${snapshot.previousRoleSnapshot ? sqlLiteral(snapshot.previousRoleSnapshot) : "NULL"},
      NOW()
    );
    `
      : ""}
  `);
}

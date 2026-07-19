export const TEAM_ROLE_VALUES = [
  "ADMIN",
  "ANALYST",
  "COMPLIANCE_OFFICER",
  "LEGAL_REVIEWER",
  "REVIEWER",
  "BILLING_ADMIN"
] as const;

export type TeamRoleValue = (typeof TEAM_ROLE_VALUES)[number];

const TEAM_ROLE_ALIASES: Record<string, TeamRoleValue> = {
  OTK_ANALYST: "ANALYST",
  OTK_BILLING_ADMIN: "BILLING_ADMIN",
  OTK_COMPLIANCE_OFFICER: "COMPLIANCE_OFFICER",
  OTK_LEGAL_REVIEWER: "LEGAL_REVIEWER",
  OTK_REVIEWER: "REVIEWER"
};

export function isTeamRoleValue(value: string): value is TeamRoleValue {
  return TEAM_ROLE_VALUES.includes(value as TeamRoleValue);
}

export function normalizeTeamRoleValue(value: string | null | undefined): TeamRoleValue | null {
  const normalized = String(value ?? "").trim().toUpperCase();
  if (isTeamRoleValue(normalized)) {
    return normalized;
  }
  return TEAM_ROLE_ALIASES[normalized] ?? null;
}

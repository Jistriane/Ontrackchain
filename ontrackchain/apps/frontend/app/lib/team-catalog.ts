export const TEAM_ROLE_VALUES = [
  "ADMIN",
  "ANALYST",
  "COMPLIANCE_OFFICER",
  "LEGAL_REVIEWER",
  "REVIEWER",
  "BILLING_ADMIN"
] as const;

export type TeamRoleValue = (typeof TEAM_ROLE_VALUES)[number];

export function isTeamRoleValue(value: string): value is TeamRoleValue {
  return TEAM_ROLE_VALUES.includes(value as TeamRoleValue);
}

const BILLING_READ_ROLES = new Set(["ADMIN", "BILLING_ADMIN", "OTK_BILLING_ADMIN"]);
const ROS_COAF_REVIEW_ROLES = new Set([
  "ADMIN",
  "COMPLIANCE_OFFICER",
  "OTK_COMPLIANCE_OFFICER",
  "LEGAL_REVIEWER",
  "OTK_LEGAL_REVIEWER",
  "REVIEWER",
  "OTK_REVIEWER"
]);
const ROS_COAF_SUBMISSION_ROLES = new Set(["ADMIN", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"]);

export function normalizeAuthRole(role: string | null | undefined) {
  return String(role ?? "").trim().toUpperCase();
}

export function canReadBilling(role: string | null | undefined) {
  return BILLING_READ_ROLES.has(normalizeAuthRole(role));
}

export function canReviewRosCoaf(role: string | null | undefined) {
  return ROS_COAF_REVIEW_ROLES.has(normalizeAuthRole(role));
}

export function canSubmitRosCoaf(role: string | null | undefined) {
  return ROS_COAF_SUBMISSION_ROLES.has(normalizeAuthRole(role));
}

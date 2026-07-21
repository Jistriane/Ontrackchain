const BILLING_READ_ROLES = new Set(["ADMIN", "OTK_ADMIN", "BILLING_ADMIN", "OTK_BILLING_ADMIN"]);
const INVESTIGATION_OPERATION_ROLES = new Set(["ADMIN", "OTK_ADMIN", "ANALYST", "OTK_ANALYST"]);
const MONITORING_CORE_READ_ROLES = new Set(["ADMIN", "OTK_ADMIN", "ANALYST", "OTK_ANALYST", "AUDITOR", "OTK_AUDITOR", "VIEWER", "OTK_VIEWER", "TESTER", "OTK_TESTER"]);
const PRIVILEGED_ADMIN_READ_ROLES = new Set(["ADMIN", "OTK_ADMIN", "AUDITOR", "OTK_AUDITOR"]);
const PRIVILEGED_ADMIN_MUTATION_ROLES = new Set(["ADMIN", "OTK_ADMIN"]);
const MONITORING_TEST_TRIGGER_ROLES = new Set(["ADMIN", "OTK_ADMIN", "TESTER", "OTK_TESTER"]);
const COUNTERPARTY_CREATE_ROLES = new Set(["ADMIN", "OTK_ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"]);
const COUNTERPARTY_READ_ROLES = new Set([
  "ADMIN",
  "OTK_ADMIN",
  "ANALYST",
  "COMPLIANCE_OFFICER",
  "OTK_COMPLIANCE_OFFICER",
  "REVIEWER",
  "OTK_REVIEWER"
]);
const SANCTIONS_CHECK_ROLES = new Set(["ADMIN", "OTK_ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"]);
const SANCTIONS_TRIAGE_ROLES = new Set([
  "ADMIN",
  "OTK_ADMIN",
  "ANALYST",
  "COMPLIANCE_OFFICER",
  "OTK_COMPLIANCE_OFFICER",
  "REVIEWER",
  "OTK_REVIEWER"
]);
const PRIVILEGED_EXPORT_ROLES = new Set(["ADMIN", "OTK_ADMIN", "AUDITOR", "OTK_AUDITOR"]);
const REPORT_WRITE_ROLES = new Set(["ADMIN", "OTK_ADMIN", "ANALYST", "OTK_ANALYST"]);
const REPORT_DETAIL_ROLES = new Set(["ADMIN", "OTK_ADMIN", "AUDITOR", "OTK_AUDITOR", "ANALYST", "OTK_ANALYST"]);
const REPORT_DOWNLOAD_ROLES = new Set(["ADMIN", "OTK_ADMIN", "AUDITOR", "OTK_AUDITOR", "ANALYST", "OTK_ANALYST"]);
const TEAM_FEDERATED_IDENTITY_MANAGE_ROLES = new Set(["ADMIN", "OTK_ADMIN"]);
const BLOCK_EVALUATE_ROLES = new Set(["ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"]);
const BLOCK_LIFT_ROLES = new Set(["ADMIN", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"]);
const COUNTERPARTY_REVIEW_ROLES = new Set([
  "ADMIN",
  "COMPLIANCE_OFFICER",
  "OTK_COMPLIANCE_OFFICER",
  "REVIEWER",
  "OTK_REVIEWER"
]);
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

function normalizeAuthMethod(authMethod: string | null | undefined) {
  return String(authMethod ?? "").trim().toLowerCase();
}

function normalizeFlag(value: string | null | undefined) {
  return String(value ?? "").trim().toLowerCase();
}

type LegalReportAccessContext = {
  role: string | null | undefined;
  authMethod: string | null | undefined;
  mfaMode: string | null | undefined;
  mfaProviderHomologated: string | null | undefined;
  twoFactor: string | null | undefined;
};

export function canReadBilling(role: string | null | undefined) {
  return BILLING_READ_ROLES.has(normalizeAuthRole(role));
}

export function canOperateInvestigation(role: string | null | undefined) {
  return INVESTIGATION_OPERATION_ROLES.has(normalizeAuthRole(role));
}

export function canReadMonitoringCore(role: string | null | undefined) {
  return MONITORING_CORE_READ_ROLES.has(normalizeAuthRole(role));
}

export function canReadMonitoringAdmin(role: string | null | undefined) {
  return PRIVILEGED_ADMIN_READ_ROLES.has(normalizeAuthRole(role));
}

export function canManageMonitoringAdmin(role: string | null | undefined) {
  return PRIVILEGED_ADMIN_MUTATION_ROLES.has(normalizeAuthRole(role));
}

export function canReadInvestigationAdmin(role: string | null | undefined) {
  return PRIVILEGED_ADMIN_READ_ROLES.has(normalizeAuthRole(role));
}

export function canManageInvestigationAdmin(role: string | null | undefined) {
  return PRIVILEGED_ADMIN_MUTATION_ROLES.has(normalizeAuthRole(role));
}

export function canTriggerMonitoringTestAlert(role: string | null | undefined) {
  return MONITORING_TEST_TRIGGER_ROLES.has(normalizeAuthRole(role));
}

export function canCreateCounterparty(role: string | null | undefined) {
  return COUNTERPARTY_CREATE_ROLES.has(normalizeAuthRole(role));
}

export function canReadCounterparty(role: string | null | undefined) {
  return COUNTERPARTY_READ_ROLES.has(normalizeAuthRole(role));
}

export function canCheckSanctions(role: string | null | undefined) {
  return SANCTIONS_CHECK_ROLES.has(normalizeAuthRole(role));
}

export function canTriageSanctions(role: string | null | undefined) {
  return SANCTIONS_TRIAGE_ROLES.has(normalizeAuthRole(role));
}

export function canExportSensitiveEvidence(role: string | null | undefined) {
  return PRIVILEGED_EXPORT_ROLES.has(normalizeAuthRole(role));
}

export function canWriteReport(role: string | null | undefined) {
  return REPORT_WRITE_ROLES.has(normalizeAuthRole(role));
}

export function canReadReportDetail(role: string | null | undefined) {
  return REPORT_DETAIL_ROLES.has(normalizeAuthRole(role));
}

export function canDownloadReportArtifact(role: string | null | undefined) {
  return REPORT_DOWNLOAD_ROLES.has(normalizeAuthRole(role));
}

export function canManageFederatedIdentity(role: string | null | undefined) {
  return TEAM_FEDERATED_IDENTITY_MANAGE_ROLES.has(normalizeAuthRole(role));
}

export function canDownloadLegalReport(context: LegalReportAccessContext | null | undefined) {
  if (!context) {
    return true;
  }
  const role = normalizeAuthRole(context.role);
  if (role === "ADMIN" || role === "OTK_ADMIN" || !role) {
    return true;
  }
  if (!["jwt", "dev_jwt"].includes(normalizeAuthMethod(context.authMethod))) {
    return true;
  }

  return true;
}

export function canEvaluateBlock(role: string | null | undefined) {
  return BLOCK_EVALUATE_ROLES.has(normalizeAuthRole(role));
}

export function canLiftBlock(role: string | null | undefined) {
  return BLOCK_LIFT_ROLES.has(normalizeAuthRole(role));
}

export function canReviewCounterparty(role: string | null | undefined) {
  return COUNTERPARTY_REVIEW_ROLES.has(normalizeAuthRole(role));
}

export function canReviewRosCoaf(role: string | null | undefined) {
  return ROS_COAF_REVIEW_ROLES.has(normalizeAuthRole(role));
}

export function canSubmitRosCoaf(role: string | null | undefined) {
  return ROS_COAF_SUBMISSION_ROLES.has(normalizeAuthRole(role));
}

export const AUDIT_ACTION_VALUES = [
  "case_started",
  "case_completed",
  "case_failed",
  "report_generated",
  "report_downloaded",
  "compliance_risk_checked",
  "compliance_sanctions_checked",
  "preventive_block_evaluated",
  "coaf_report_generated",
  "coaf_report_approved",
  "coaf_report_rejected",
  "coaf_report_submitted_manual",
  "coaf_regulatory_dossier_downloaded",
  "evidence_manual_review_package_exported",
  "evidence_manual_review_package_signoff_requested",
  "evidence_manual_review_package_signoff_recorded",
  "evidence_manual_review_package_sealed",
  "evidence_manual_review_package_seal_revoked",
  "evidence_manual_review_package_seal_superseded",
  "evidence_manual_review_package_mfa_violation",
  "operational_alerts_exported",
  "authorization_denied"
] as const;

export type AuditActionValue = (typeof AUDIT_ACTION_VALUES)[number];

export const AUDIT_RESOURCE_TYPE_VALUES = [
  "case",
  "report",
  "operational_alerts",
  "audit_log",
  "ros_record",
  "evidence_package_seal"
] as const;

export type AuditResourceTypeValue = (typeof AUDIT_RESOURCE_TYPE_VALUES)[number];

export function isAuditActionValue(value: string): value is AuditActionValue {
  return AUDIT_ACTION_VALUES.includes(value as AuditActionValue);
}

export function isAuditResourceTypeValue(value: string): value is AuditResourceTypeValue {
  return AUDIT_RESOURCE_TYPE_VALUES.includes(value as AuditResourceTypeValue);
}

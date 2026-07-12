export const EVIDENCE_ACTION_VALUES = [
  "compliance_sanctions_checked",
  "preventive_block_lifted",
  "counterparty_created",
  "coaf_report_generated",
  "coaf_report_approved",
  "coaf_report_rejected",
  "coaf_report_submitted_manual",
  "coaf_regulatory_dossier_downloaded",
  "report_generated",
  "report_downloaded",
  "evidence_manual_review_package_exported",
  "compliance_due_diligence_checked",
  "compliance_source_of_funds_checked",
  "evidence_bundle_exported"
] as const;

export type EvidenceActionValue = (typeof EVIDENCE_ACTION_VALUES)[number];

export const EVIDENCE_RESOURCE_TYPE_VALUES = ["address", "case", "report", "ros_record", "preventive_block", "counterparty", "audit_log"] as const;

export type EvidenceResourceTypeValue = (typeof EVIDENCE_RESOURCE_TYPE_VALUES)[number];

export function isEvidenceActionValue(value: string): value is EvidenceActionValue {
  return EVIDENCE_ACTION_VALUES.includes(value as EvidenceActionValue);
}

export function isEvidenceResourceTypeValue(value: string): value is EvidenceResourceTypeValue {
  return EVIDENCE_RESOURCE_TYPE_VALUES.includes(value as EvidenceResourceTypeValue);
}

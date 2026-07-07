export const REPORT_FORMAL_DOSSIER_VALUE_KEYS = [
  "formal_report_dossier",
  "legal_report_dossier",
  "coaf_ready_report_dossier",
  "full_investigation_dossier",
  "controlled_operational",
  "restricted_regulatory",
  "restricted_legal",
  "controlled_investigation",
  "tenant_authenticated_context",
  "authenticated_regulatory_context",
  "jwt_admin_2fa_required",
  "enterprise_authenticated_context",
  "ops_review",
  "compliance_ops_signoff",
  "legal_compliance_signoff",
  "investigation_lead_signoff",
  "anchored_onchain",
  "pending_anchor",
  "download_audited",
  "download_not_audited",
  "hash_bound",
  "hash_missing",
  "tenant_operational_distribution",
  "regulatory_authority_distribution",
  "legal_restricted_distribution",
  "enterprise_internal_distribution",
  "operational_retention",
  "regulatory_extended_retention",
  "investigation_case_retention"
] as const;

export type ReportFormalDossierValue = (typeof REPORT_FORMAL_DOSSIER_VALUE_KEYS)[number];
export const REPORT_FORMAL_DOSSIER_SUMMARY_FIELDS = [
  "packageType",
  "classification",
  "accessPolicy",
  "signoffMode",
  "anchoringStatus",
  "downloadState",
  "custodyState",
  "distributionScope",
  "retentionClass"
] as const;

export type ReportFormalDossierSummaryField = (typeof REPORT_FORMAL_DOSSIER_SUMMARY_FIELDS)[number];

export function isReportFormalDossierValue(value: string): value is ReportFormalDossierValue {
  return REPORT_FORMAL_DOSSIER_VALUE_KEYS.includes(value as ReportFormalDossierValue);
}

export type ReportFormalDossierSource = {
  report_id: string;
  case_id: string;
  report_type_requested: string;
  report_type: string;
  created_at: string;
  file_hash_sha256: string;
  onchain_hash: string | null;
  content_type: string;
};

export type ReportFormalDossierSummary = {
  packageType: ReportFormalDossierValue;
  classification: ReportFormalDossierValue;
  accessPolicy: ReportFormalDossierValue;
  signoffMode: ReportFormalDossierValue;
  anchoringStatus: ReportFormalDossierValue;
  downloadState: ReportFormalDossierValue;
  custodyState: ReportFormalDossierValue;
  distributionScope: ReportFormalDossierValue;
  retentionClass: ReportFormalDossierValue;
};

export function buildReportFormalDossierFilename(reportId: string) {
  return `ontrackchain-report-dossier-${reportId}.json`;
}

export function deriveReportFormalDossierSummary(
  report: ReportFormalDossierSource,
  hasDownloadAudit: boolean
): ReportFormalDossierSummary {
  if (report.report_type === "legal_report") {
    return {
      packageType: "legal_report_dossier",
      classification: "restricted_legal",
      accessPolicy: "jwt_admin_2fa_required",
      signoffMode: "legal_compliance_signoff",
      anchoringStatus: report.onchain_hash ? "anchored_onchain" : "pending_anchor",
      downloadState: hasDownloadAudit ? "download_audited" : "download_not_audited",
      custodyState: report.file_hash_sha256 ? "hash_bound" : "hash_missing",
      distributionScope: "legal_restricted_distribution",
      retentionClass: "regulatory_extended_retention"
    };
  }

  if (report.report_type === "coaf_ready_report") {
    return {
      packageType: "coaf_ready_report_dossier",
      classification: "restricted_regulatory",
      accessPolicy: "authenticated_regulatory_context",
      signoffMode: "compliance_ops_signoff",
      anchoringStatus: report.onchain_hash ? "anchored_onchain" : "pending_anchor",
      downloadState: hasDownloadAudit ? "download_audited" : "download_not_audited",
      custodyState: report.file_hash_sha256 ? "hash_bound" : "hash_missing",
      distributionScope: "regulatory_authority_distribution",
      retentionClass: "regulatory_extended_retention"
    };
  }

  if (report.report_type === "full_investigation") {
    return {
      packageType: "full_investigation_dossier",
      classification: "controlled_investigation",
      accessPolicy: "enterprise_authenticated_context",
      signoffMode: "investigation_lead_signoff",
      anchoringStatus: report.onchain_hash ? "anchored_onchain" : "pending_anchor",
      downloadState: hasDownloadAudit ? "download_audited" : "download_not_audited",
      custodyState: report.file_hash_sha256 ? "hash_bound" : "hash_missing",
      distributionScope: "enterprise_internal_distribution",
      retentionClass: "investigation_case_retention"
    };
  }

  return {
    packageType: "formal_report_dossier",
    classification: "controlled_operational",
    accessPolicy: "tenant_authenticated_context",
    signoffMode: "ops_review",
    anchoringStatus: report.onchain_hash ? "anchored_onchain" : "pending_anchor",
    downloadState: hasDownloadAudit ? "download_audited" : "download_not_audited",
    custodyState: report.file_hash_sha256 ? "hash_bound" : "hash_missing",
    distributionScope: "tenant_operational_distribution",
    retentionClass: "operational_retention"
  };
}

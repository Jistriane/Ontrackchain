export type ManualPackageSealSignoff = {
  id: string;
  seal_id: string;
  organization_id: string;
  signer_role: string;
  signer_user_id: string | null;
  signer_display_name: string;
  decision: string;
  signoff_method: string;
  ticket_ref: string | null;
  notes: string | null;
  signed_at: string | null;
  metadata: Record<string, unknown>;
};

export type ManualPackageSeal = {
  seal_id: string;
  organization_id: string;
  package_kind: string;
  request_id: string;
  report_id: string | null;
  scope_id: string;
  manual_review_action: string;
  package_sha256: string;
  manifest_schema_version: string;
  classification: string;
  signoff_mode: string;
  seal_status: string;
  seal_format: string;
  signature_algorithm: string | null;
  kms_key_ref: string | null;
  certificate_fingerprint_sha256: string | null;
  certificate_bundle_ref: string | null;
  policy_version: string;
  sealed_at: string | null;
  sealed_by_user_id: string | null;
  revoked_at: string | null;
  superseded_by_seal_id: string | null;
  required_signers: string[];
  completed_signoffs: number;
  approved_required_signoffs: number;
  required_signoffs: number;
  signoffs: ManualPackageSealSignoff[];
  seal_envelope: Record<string, unknown>;
  verification_summary: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
};

function normalizeRole(role: string | null | undefined) {
  return String(role ?? "").trim().toUpperCase();
}

const MANUAL_PACKAGE_READ_ROLES = new Set([
  "ADMIN",
  "AUDITOR",
  "COMPLIANCE_OFFICER",
  "OTK_COMPLIANCE_OFFICER",
  "LEGAL_REVIEWER",
  "OTK_LEGAL_REVIEWER",
  "REVIEWER",
  "OTK_REVIEWER"
]);

const MANUAL_PACKAGE_SIGNER_ROLE_BINDINGS: Record<string, string[]> = {
  ADMIN: ["compliance_owner", "ops_owner", "legal_owner_optional"],
  COMPLIANCE_OFFICER: ["compliance_owner"],
  OTK_COMPLIANCE_OFFICER: ["compliance_owner"],
  LEGAL_REVIEWER: ["legal_owner_optional"],
  OTK_LEGAL_REVIEWER: ["legal_owner_optional"],
  REVIEWER: ["legal_owner_optional"],
  OTK_REVIEWER: ["legal_owner_optional"]
};

export function canReadManualPackageSeal(role: string | null | undefined) {
  return MANUAL_PACKAGE_READ_ROLES.has(normalizeRole(role));
}

export function canManageManualPackageSeal(role: string | null | undefined) {
  return normalizeRole(role) === "ADMIN";
}

export function canRecordManualPackageSignoff(role: string | null | undefined, signerRole: string | null | undefined) {
  const normalizedRole = normalizeRole(role);
  const normalizedSignerRole = String(signerRole ?? "").trim();
  if (!normalizedSignerRole) {
    return false;
  }
  return (MANUAL_PACKAGE_SIGNER_ROLE_BINDINGS[normalizedRole] ?? []).includes(normalizedSignerRole);
}

export function getPendingRequiredManualPackageSignerRoles(seal: ManualPackageSeal | null) {
  if (!seal) {
    return [] as string[];
  }

  const recordedRoles = new Set(seal.signoffs.map((signoff) => signoff.signer_role));
  return seal.required_signers.filter((role) => !recordedRoles.has(role));
}

export function getRecordableManualPackageSignerRoles(
  seal: ManualPackageSeal | null,
  role: string | null | undefined
) {
  if (!seal) {
    return [] as string[];
  }

  const normalizedRole = normalizeRole(role);
  const eligibleRoles = MANUAL_PACKAGE_SIGNER_ROLE_BINDINGS[normalizedRole] ?? [];
  if (!eligibleRoles.length) {
    return [] as string[];
  }

  const recordedRoles = new Set(seal.signoffs.map((signoff) => signoff.signer_role));
  const requiredSignerSet = new Set(seal.required_signers);

  const pendingRequired = eligibleRoles.filter((signerRole) => requiredSignerSet.has(signerRole) && !recordedRoles.has(signerRole));
  const optionalEligible = eligibleRoles.filter((signerRole) => !requiredSignerSet.has(signerRole) && !recordedRoles.has(signerRole));

  return [...pendingRequired, ...optionalEligible];
}

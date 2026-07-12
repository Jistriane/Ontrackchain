export type EvidenceManualReviewSnapshot = {
  provider: string;
  providerStatus: string;
  degradedReason: string;
  capabilityStatus: string;
  deliveryMode: string;
  requiresHumanReview: boolean;
  counterpartyContext: string;
  purpose: string;
  amount: number | null;
};

export type EvidenceManualPackageSummary = {
  packageType: string;
  sensitivity: string;
  workflow: string;
  accessPolicy: string;
  signoffMode: string;
  reviewMode: string;
  custodyState: string;
  anchoringStatus: string;
  scopeId: string;
  dossierFields: string[];
  checklist: string[];
};

export type EvidenceManualPackageEvidenceRequest = {
  request_id?: string | null;
  report_id?: string | null;
  resource_type?: string | null;
  resource_id?: string | null;
  limit?: number | null;
  include_audit_logs?: boolean;
  include_credit_ledger?: boolean;
  include_reports?: boolean;
};

export type EvidenceManualPackageScope = {
  request_id?: string | null;
  report_id?: string | null;
  address?: string | null;
  chain?: string | null;
  resource_id?: string | null;
};

export type EvidenceManualPackagePayload = {
  action: string;
  scope_id: string;
  evidence_request: EvidenceManualPackageEvidenceRequest;
  scope: EvidenceManualPackageScope;
  manual_review: {
    provider?: string | null;
    provider_status?: string | null;
    degraded_reason?: string | null;
    capability_status?: string | null;
    delivery_mode?: string | null;
    requires_human_review?: boolean;
    counterparty_context?: string | null;
    purpose?: string | null;
    amount?: number | null;
  };
  dossier: {
    package_type?: string | null;
    sensitivity?: string | null;
    workflow?: string | null;
    access_policy?: string | null;
    signoff_mode?: string | null;
    review_mode?: string | null;
    custody_state?: string | null;
    anchoring_status?: string | null;
    required_fields?: string[];
    analyst_checklist?: string[];
  };
  workspace_summary?: Record<string, unknown> | null;
};

export type EvidenceManualPackageDocument = {
  package_type: string;
  sensitivity: string | null;
  workflow: string | null;
  generated_at: string;
  scope: {
    request_id: string | null;
    report_id: string | null;
    address: string | null;
    chain: string | null;
    resource_id: string | null;
  };
  manual_review: {
    provider: string | null;
    provider_status: string | null;
    degraded_reason: string | null;
    capability_status: string | null;
    delivery_mode: string | null;
    requires_human_review: boolean;
    counterparty_context: string | null;
    purpose: string | null;
    amount: number | null;
  };
  dossier: {
    package_type: string | null;
    sensitivity: string | null;
    workflow: string | null;
    access_policy: string | null;
    signoff_mode: string | null;
    review_mode: string | null;
    custody_state: string | null;
    anchoring_status: string | null;
    required_fields: string[];
    analyst_checklist: string[];
  };
  workspace_summary: Record<string, unknown> | null;
  evidence_bundle: Record<string, unknown> | null;
  manifest: {
    schema_version: string;
    export_request_id: string;
    filename: string;
    hash_algorithm: string;
    payload_sha256: string;
    scope_sha256: string;
    manual_review_sha256: string;
    dossier_sha256: string;
    evidence_bundle_sha256: string | null;
    workspace_summary_sha256: string | null;
  };
  audit_log: {
    action: string;
    resource_type: string;
    resource_id: string | null;
    request_id: string | null;
    report_id: string | null;
    created_at: string;
    metadata: Record<string, unknown>;
  } | null;
};

export function buildManualReviewPackageFilename(action: string, scopeId: string) {
  if (action === "compliance_due_diligence_checked") {
    return `ontrackchain-manual-review-due-diligence-${scopeId}.json`;
  }
  return `ontrackchain-manual-review-source-of-funds-${scopeId}.json`;
}

export function deriveEvidenceManualPackageSummary(input: {
  action: string;
  review: EvidenceManualReviewSnapshot;
  scopeId: string;
  hasRequestId: boolean;
  hasReportId: boolean;
  hasFileHash: boolean;
}) {
  const isDueDiligence = input.action === "compliance_due_diligence_checked";
  return {
    packageType: isDueDiligence ? "due_diligence_manual_review_package" : "source_of_funds_manual_review_package",
    sensitivity: "restricted_regulatory",
    workflow: input.review.deliveryMode,
    accessPolicy: input.review.requiresHumanReview
      ? "regulated_ops_human_review_required"
      : "regulated_ops_authenticated_context",
    signoffMode: isDueDiligence ? "compliance_dd_signoff" : "compliance_sof_signoff",
    reviewMode: input.review.requiresHumanReview ? "human_signoff_required" : "assisted_review",
    custodyState: input.hasRequestId || input.hasReportId ? "chain_correlated" : "event_only",
    anchoringStatus: input.hasFileHash ? "hash_materialized_offchain" : "hash_pending",
    scopeId: input.scopeId,
    dossierFields: isDueDiligence
      ? ["provider_status", "degraded_reason", "counterparty_context", "address", "chain"]
      : ["provider_status", "degraded_reason", "purpose", "amount", "address", "chain"],
    checklist: isDueDiligence
      ? ["validate_counterparty", "attach_human_rationale", "confirm_relationship_origin"]
      : ["validate_declared_origin", "attach_documentary_evidence", "confirm_financial_rationale"]
  } satisfies EvidenceManualPackageSummary;
}

export function buildEvidenceManualPackagePayload(input: {
  action: string;
  summary: EvidenceManualPackageSummary;
  evidenceRequest: EvidenceManualPackageEvidenceRequest;
  scope: EvidenceManualPackageScope;
  manualReview: EvidenceManualReviewSnapshot;
  workspaceSummary?: Record<string, unknown> | null;
}) {
  return {
    action: input.action,
    scope_id: input.summary.scopeId,
    evidence_request: input.evidenceRequest,
    scope: input.scope,
    manual_review: {
      provider: input.manualReview.provider,
      provider_status: input.manualReview.providerStatus,
      degraded_reason: input.manualReview.degradedReason,
      capability_status: input.manualReview.capabilityStatus,
      delivery_mode: input.manualReview.deliveryMode,
      requires_human_review: input.manualReview.requiresHumanReview,
      counterparty_context: input.manualReview.counterpartyContext || null,
      purpose: input.manualReview.purpose || null,
      amount: input.manualReview.amount
    },
    dossier: {
      package_type: input.summary.packageType,
      sensitivity: input.summary.sensitivity,
      workflow: input.summary.workflow,
      access_policy: input.summary.accessPolicy,
      signoff_mode: input.summary.signoffMode,
      review_mode: input.summary.reviewMode,
      custody_state: input.summary.custodyState,
      anchoring_status: input.summary.anchoringStatus,
      required_fields: input.summary.dossierFields,
      analyst_checklist: input.summary.checklist
    },
    workspace_summary: input.workspaceSummary ?? null
  } satisfies EvidenceManualPackagePayload;
}

export function buildEvidenceManualPackageDocument(
  payload: EvidenceManualPackagePayload,
  evidenceBundle: Record<string, unknown> | null,
  generatedAt: string
) {
  return {
    package_type: payload.dossier.package_type ?? payload.action,
    sensitivity: payload.dossier.sensitivity ?? null,
    workflow: payload.dossier.workflow ?? null,
    generated_at: generatedAt,
    scope: {
      request_id: payload.scope.request_id ?? null,
      report_id: payload.scope.report_id ?? null,
      address: payload.scope.address ?? null,
      chain: payload.scope.chain ?? null,
      resource_id: payload.scope.resource_id ?? null
    },
    manual_review: {
      provider: payload.manual_review.provider ?? null,
      provider_status: payload.manual_review.provider_status ?? null,
      degraded_reason: payload.manual_review.degraded_reason ?? null,
      capability_status: payload.manual_review.capability_status ?? null,
      delivery_mode: payload.manual_review.delivery_mode ?? null,
      requires_human_review: payload.manual_review.requires_human_review ?? false,
      counterparty_context: payload.manual_review.counterparty_context ?? null,
      purpose: payload.manual_review.purpose ?? null,
      amount: payload.manual_review.amount ?? null
    },
    dossier: {
      package_type: payload.dossier.package_type ?? null,
      sensitivity: payload.dossier.sensitivity ?? null,
      workflow: payload.dossier.workflow ?? null,
      access_policy: payload.dossier.access_policy ?? null,
      signoff_mode: payload.dossier.signoff_mode ?? null,
      review_mode: payload.dossier.review_mode ?? null,
      custody_state: payload.dossier.custody_state ?? null,
      anchoring_status: payload.dossier.anchoring_status ?? null,
      required_fields: payload.dossier.required_fields ?? [],
      analyst_checklist: payload.dossier.analyst_checklist ?? []
    },
    workspace_summary: payload.workspace_summary ?? null,
    evidence_bundle: evidenceBundle,
    manifest: {
      schema_version: "",
      export_request_id: "",
      filename: "",
      hash_algorithm: "",
      payload_sha256: "",
      scope_sha256: "",
      manual_review_sha256: "",
      dossier_sha256: "",
      evidence_bundle_sha256: null,
      workspace_summary_sha256: null
    },
    audit_log: null
  } satisfies EvidenceManualPackageDocument;
}

function serializeCanonicalJson(value: unknown): string {
  return JSON.stringify(sortJsonValue(value));
}

function sortJsonValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((entry) => sortJsonValue(entry));
  }
  if (!value || typeof value !== "object") {
    return value;
  }

  return Object.keys(value as Record<string, unknown>)
    .sort()
    .reduce<Record<string, unknown>>((accumulator, key) => {
      accumulator[key] = sortJsonValue((value as Record<string, unknown>)[key]);
      return accumulator;
    }, {});
}

async function sha256Hex(value: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest))
    .map((entry) => entry.toString(16).padStart(2, "0"))
    .join("");
}

async function hashJson(value: unknown): Promise<string | null> {
  if (value === null) {
    return null;
  }
  return sha256Hex(serializeCanonicalJson(value));
}

export async function buildEvidenceManualPackageManifest(input: {
  payload: EvidenceManualPackagePayload,
  evidenceBundle: Record<string, unknown> | null,
  generatedAt: string,
  exportRequestId: string,
  filename: string
}) {
  const packageDocument = buildEvidenceManualPackageDocument(input.payload, input.evidenceBundle, input.generatedAt);
  const payloadDocument = {
    package_type: packageDocument.package_type,
    sensitivity: packageDocument.sensitivity,
    workflow: packageDocument.workflow,
    generated_at: packageDocument.generated_at,
    scope: packageDocument.scope,
    manual_review: packageDocument.manual_review,
    dossier: packageDocument.dossier,
    workspace_summary: packageDocument.workspace_summary,
    evidence_bundle: packageDocument.evidence_bundle
  };

  return {
    schema_version: "manual_review_package/v2",
    export_request_id: input.exportRequestId,
    filename: input.filename,
    hash_algorithm: "SHA-256",
    payload_sha256: await sha256Hex(serializeCanonicalJson(payloadDocument)),
    scope_sha256: await sha256Hex(serializeCanonicalJson(packageDocument.scope)),
    manual_review_sha256: await sha256Hex(serializeCanonicalJson(packageDocument.manual_review)),
    dossier_sha256: await sha256Hex(serializeCanonicalJson(packageDocument.dossier)),
    evidence_bundle_sha256: await hashJson(packageDocument.evidence_bundle),
    workspace_summary_sha256: await hashJson(packageDocument.workspace_summary)
  } satisfies EvidenceManualPackageDocument["manifest"];
}

export function buildEvidenceManualPackageAuditMetadata(input: {
  payload: EvidenceManualPackagePayload;
  manifest: EvidenceManualPackageDocument["manifest"];
  filename: string;
}) {
  return {
    scope_id: input.payload.scope_id,
    filename: input.filename,
    package_type: input.payload.dossier.package_type ?? input.payload.action,
    package_sha256: input.manifest.payload_sha256,
    evidence_bundle_sha256: input.manifest.evidence_bundle_sha256,
    workspace_summary_sha256: input.manifest.workspace_summary_sha256,
    scope_sha256: input.manifest.scope_sha256,
    manual_review_sha256: input.manifest.manual_review_sha256,
    dossier_sha256: input.manifest.dossier_sha256,
    hash_algorithm: input.manifest.hash_algorithm,
    manual_review_action: input.payload.action,
    provider: input.payload.manual_review.provider ?? null,
    provider_status: input.payload.manual_review.provider_status ?? null,
    degraded_reason: input.payload.manual_review.degraded_reason ?? null,
    capability_status: input.payload.manual_review.capability_status ?? null,
    delivery_mode: input.payload.manual_review.delivery_mode ?? null,
    requires_human_review: input.payload.manual_review.requires_human_review ?? false,
    counterparty_context: input.payload.manual_review.counterparty_context ?? null,
    purpose: input.payload.manual_review.purpose ?? null,
    amount: input.payload.manual_review.amount ?? null,
    case_id: (input.payload.workspace_summary?.case_id as string | null | undefined) ?? null,
    event_id: (input.payload.workspace_summary?.event_id as string | null | undefined) ?? null,
    workspace_status: (input.payload.workspace_summary?.status as string | null | undefined) ?? null,
    owner: (input.payload.workspace_summary?.owner as string | null | undefined) ?? null,
    source: (input.payload.workspace_summary?.source as string | null | undefined) ?? null,
    address: input.payload.scope.address ?? null,
    chain: input.payload.scope.chain ?? null
  } satisfies Record<string, unknown>;
}

export function finalizeEvidenceManualPackageDocument(
  packageDocument: EvidenceManualPackageDocument,
  manifest: EvidenceManualPackageDocument["manifest"],
  auditLog: EvidenceManualPackageDocument["audit_log"]
) {
  return {
    ...packageDocument,
    manifest,
    audit_log: auditLog
  } satisfies EvidenceManualPackageDocument;
}

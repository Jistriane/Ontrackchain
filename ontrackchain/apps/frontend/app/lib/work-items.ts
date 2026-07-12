export type WorkItemModule =
  | "alerts"
  | "sanctions"
  | "blocks"
  | "reports"
  | "ros_coaf"
  | "counterparties"
  | "evidence";

export type WorkItemResourceType =
  | "operational_alert"
  | "sanctions_screening"
  | "preventive_block"
  | "formal_report_case"
  | "ros_record"
  | "counterparty"
  | "evidence_event";

export type WorkItemPriority = "critical" | "high" | "normal";

export type WorkItemQueueStatus =
  | "UNDER_REVIEW"
  | "ESCALATED"
  | "READY"
  | "APPROVED"
  | "SUBMITTED"
  | "CLOSED"
  | "REJECTED";

export type WorkItemBaseMetadata = Record<string, unknown> & {
  case_id?: string;
  owner_label?: string;
  owner_user_id?: string;
  workspace_status?: string;
  local_workspace_status?: string;
  note?: string;
};

export type ReportWorkItemMetadata = WorkItemBaseMetadata & {
  target_address?: string;
  target_chain?: string;
  report_type?: string;
  report_id?: string;
};

export type EvidenceWorkItemMetadata = WorkItemBaseMetadata & {
  event_id?: string;
  audit_action?: string;
  audit_resource_type?: string;
  audit_resource_id?: string;
  request_id?: string;
  report_id?: string;
  file_hash_sha256?: string;
  provider?: string;
  provider_status?: string;
  degraded_reason?: string;
  capability_status?: string;
  delivery_mode?: string;
  origin_analysis_status?: string;
  requires_human_review?: boolean;
  counterparty_context_present?: boolean;
  counterparty_context?: string;
  purpose?: string;
  amount?: number;
  manual_review_action?: string;
  package_sha256?: string;
  filename?: string;
};

export type SanctionsWorkItemMetadata = WorkItemBaseMetadata & {
  workspace_id?: string;
  address?: string;
  chain?: string;
  lists?: string[];
  provider?: string;
  provider_status?: string;
  capability_status?: string;
  degraded_reason?: string;
  matched_lists?: string[];
  hit?: boolean;
  entity_name?: string;
  designation_date?: string;
  checked_at?: string;
  triage_note?: string;
  local_case_id?: string;
};

export type AlertsWorkItemMetadata = WorkItemBaseMetadata & {
  alertname?: string;
  receiver?: string;
  service?: string | null;
  severity?: string | null;
  status?: string;
  fingerprint?: string;
  first_received_at?: string;
  last_received_at?: string;
  delivery_count?: number;
  triage_status?: string;
  triaged_at?: string | null;
  triaged_by?: string | null;
  triage_note?: string | null;
  address?: string;
  report_id?: string;
  domain?: string;
  affected_domains?: string[];
  incident_commander?: string;
  containment_status?: string;
  suspected_root_cause?: string;
  confirmed_root_cause?: string;
  runbook_ref?: string;
  impact_summary?: string;
  corrective_actions?: string[];
  evidence_refs?: string[];
};

export type BlocksWorkItemMetadata = WorkItemBaseMetadata & {
  workspace_id?: string;
  local_block_status?: string;
  address?: string;
  chain?: string;
  entity_name?: string;
  entity_document?: string;
  local_case_id?: string;
  action?: string;
  requires_coaf_report?: boolean;
  decision_confidence?: number;
  regulatory_basis?: string[];
  matched_lists?: string[];
  evidence_hash?: string;
  block_id?: string;
  screened_at?: string;
  lifted_at?: string;
  lift_reason?: string;
};

export type CounterpartyWorkItemMetadata = WorkItemBaseMetadata & {
  counterparty_id?: string;
  legal_name?: string;
  counterparty_type?: string;
  document_type?: string;
  document_number?: string;
  wallet_chain?: string;
  wallet_address?: string;
  wallet_label?: string;
  risk_level?: number;
  kyc_status?: string;
  sanctions_cleared?: boolean;
  is_pep?: boolean;
  enhanced_dd_required?: boolean;
  next_review_date?: string;
  status?: string;
  created_at?: string;
  dd_review_status?: string;
  dd_review_note?: string;
  sof_description?: string;
  sof_document_ref?: string;
};

export type RosCoafWorkItemMetadata = WorkItemBaseMetadata & {
  ros_id?: string;
  ros_status?: string;
  ros_phase?: string;
  report_id?: string;
  created_at?: string;
  approved_at?: string;
  approval_2fa_verified?: boolean;
  submitted_at?: string;
  coaf_protocol_number?: string;
  coaf_receipt_hash?: string;
  rejection_reason?: string;
};

export type WorkItemResponse<TMetadata extends Record<string, unknown> = Record<string, unknown>> = {
  id: string;
  module: WorkItemModule;
  resource_type: WorkItemResourceType;
  resource_id: string;
  case_id: string | null;
  report_external_id?: string | null;
  owner_user_id?: string | null;
  assigned_by_user_id?: string | null;
  queue_status: WorkItemQueueStatus;
  priority: WorkItemPriority;
  due_at: string | null;
  sla_breached?: boolean;
  title?: string | null;
  note: string | null;
  metadata: TMetadata;
  created_at?: string;
  updated_at: string;
  last_activity_at: string;
};

export type WorkItemListResponse<TMetadata extends Record<string, unknown> = Record<string, unknown>> = {
  data: WorkItemResponse<TMetadata>[];
  page?: number;
  limit?: number;
  total?: number;
  has_more?: boolean;
};

export type CreateWorkItemRequest<TMetadata extends Record<string, unknown> = Record<string, unknown>> = {
  module: WorkItemModule;
  resource_type: WorkItemResourceType;
  resource_id: string;
  case_id?: string;
  report_external_id?: string;
  owner_user_id?: string;
  priority: WorkItemPriority;
  queue_status: WorkItemQueueStatus;
  due_at: string | null;
  title: string;
  note: string | null;
  metadata: TMetadata;
};

export type PatchWorkItemRequest<TMetadata extends Record<string, unknown> = Record<string, unknown>> = {
  owner_user_id?: string;
  priority: WorkItemPriority;
  queue_status: WorkItemQueueStatus;
  due_at: string | null;
  title: string;
  note: string | null;
  metadata: TMetadata;
};

type CanonicalWorkItemMetadataOptions = {
  resourceType: WorkItemResourceType;
  caseId?: string | null;
  ownerLabel?: string | null;
  ownerUserId?: string | null;
  workspaceStatus?: string | null;
  note?: string | null;
};

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const WORK_ITEM_STATUS_METADATA_KEYS: Record<WorkItemResourceType, string[]> = {
  operational_alert: ["workspace_status", "local_workspace_status"],
  sanctions_screening: ["workspace_status", "local_workspace_status"],
  preventive_block: ["workspace_status", "local_block_status", "local_workspace_status"],
  formal_report_case: ["workspace_status", "local_workspace_status"],
  ros_record: ["workspace_status", "ros_status"],
  counterparty: ["workspace_status", "local_workspace_status"],
  evidence_event: ["workspace_status", "local_workspace_status"]
};

function normalizeOptionalString(value: string | null | undefined): string {
  return value?.trim() ?? "";
}


function hashStringToUint32(input: string, seed: number): number {
  let hash = seed >>> 0;
  for (let index = 0; index < input.length; index += 1) {
    hash ^= input.charCodeAt(index);
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return hash >>> 0;
}

function buildDeterministicUuid(seedInput: string): string {
  const seeds = [0x811c9dc5, 0x9e3779b9, 0x85ebca6b, 0xc2b2ae35];
  const hex = seeds
    .map((seed) => hashStringToUint32(seedInput, seed).toString(16).padStart(8, "0"))
    .join("")
    .slice(0, 32)
    .split("");

  hex[12] = "5";
  const variantNibble = parseInt(hex[16] ?? "0", 16);
  hex[16] = ["8", "9", "a", "b"][variantNibble % 4] ?? "8";

  return `${hex.slice(0, 8).join("")}-${hex.slice(8, 12).join("")}-${hex.slice(12, 16).join("")}-${hex.slice(16, 20).join("")}-${hex.slice(20, 32).join("")}`;
}

export function isWorkItemUuidLike(value: string | null | undefined): value is string {
  return Boolean(value && UUID_PATTERN.test(value.trim()));
}

export function resolveWorkItemResourceId(
  resourceType: WorkItemResourceType,
  primaryId: string | null | undefined,
  ...fallbackIds: Array<string | null | undefined>
): string {
  const normalizedPrimaryId = primaryId?.trim() ?? "";
  if (isWorkItemUuidLike(normalizedPrimaryId)) {
    return normalizedPrimaryId;
  }

  const seedParts = [resourceType, normalizedPrimaryId, ...fallbackIds.map((value) => value?.trim() ?? "").filter(Boolean)];
  return buildDeterministicUuid(seedParts.join("::"));
}

export function readWorkItemMetadataString(
  metadata: Record<string, unknown>,
  ...keys: string[]
): string {
  for (const key of keys) {
    const value = metadata[key];
    if (typeof value === "string") {
      return value;
    }
  }
  return "";
}

export function readWorkItemMetadataStringArray(
  metadata: Record<string, unknown>,
  ...keys: string[]
): string[] {
  for (const key of keys) {
    const value = metadata[key];
    if (Array.isArray(value)) {
      return value.filter((entry): entry is string => typeof entry === "string");
    }
  }
  return [];
}

export function readWorkItemMetadataBoolean(
  metadata: Record<string, unknown>,
  ...keys: string[]
): boolean | null {
  for (const key of keys) {
    const value = metadata[key];
    if (typeof value === "boolean") {
      return value;
    }
  }
  return null;
}

export function readWorkItemMetadataNumber(
  metadata: Record<string, unknown>,
  ...keys: string[]
): number | null {
  for (const key of keys) {
    const value = metadata[key];
    if (typeof value === "number") {
      return value;
    }
  }
  return null;
}

export function resolveWorkItemOwnerDisplay(
  metadata: Record<string, unknown>,
  ownerUserId: string | null | undefined
): string {
  return readWorkItemMetadataString(metadata, "owner_label") || normalizeOptionalString(ownerUserId) || readWorkItemMetadataString(metadata, "owner_user_id");
}

export function resolveWorkItemWorkspaceStatus(
  metadata: Record<string, unknown>,
  resourceType: WorkItemResourceType,
  fallback?: string | null
): string {
  const keys = WORK_ITEM_STATUS_METADATA_KEYS[resourceType] ?? ["workspace_status"];
  return readWorkItemMetadataString(metadata, ...keys) || normalizeOptionalString(fallback);
}

export function withCanonicalWorkItemMetadata<TMetadata extends WorkItemBaseMetadata>(
  metadata: TMetadata,
  { resourceType, caseId, ownerLabel, ownerUserId, workspaceStatus, note }: CanonicalWorkItemMetadataOptions
): TMetadata {
  const nextMetadata = { ...metadata } as TMetadata & WorkItemBaseMetadata;
  const nextMetadataRecord = nextMetadata as Record<string, unknown>;
  const normalizedCaseId = normalizeOptionalString(caseId);
  const normalizedOwnerLabel = normalizeOptionalString(ownerLabel);
  const normalizedOwnerUserId = normalizeOptionalString(ownerUserId);
  const normalizedWorkspaceStatus = normalizeOptionalString(workspaceStatus);
  const normalizedNote = normalizeOptionalString(note);

  if (normalizedCaseId) {
    nextMetadata.case_id = normalizedCaseId;
    if (resourceType === "sanctions_screening" || resourceType === "preventive_block") {
      nextMetadataRecord["local_case_id"] = normalizedCaseId;
    }
  }

  if (normalizedOwnerLabel) {
    nextMetadata.owner_label = normalizedOwnerLabel;
  }

  if (normalizedOwnerUserId) {
    nextMetadata.owner_user_id = normalizedOwnerUserId;
  }

  if (normalizedWorkspaceStatus) {
    nextMetadata.workspace_status = normalizedWorkspaceStatus;

    if (
      resourceType === "sanctions_screening" ||
      resourceType === "formal_report_case" ||
      resourceType === "counterparty" ||
      resourceType === "evidence_event"
    ) {
      nextMetadata.local_workspace_status = normalizedWorkspaceStatus;
    }

    if (resourceType === "preventive_block") {
      nextMetadata.local_workspace_status = normalizedWorkspaceStatus;
      nextMetadataRecord["local_block_status"] = normalizedWorkspaceStatus;
    }

    if (resourceType === "ros_record") {
      nextMetadataRecord["ros_status"] = normalizedWorkspaceStatus;
    }
  }

  if (normalizedNote) {
    nextMetadata.note = normalizedNote;
  }

  return nextMetadata;
}

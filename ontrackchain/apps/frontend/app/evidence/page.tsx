"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

import { useI18n } from "../../components/i18n-provider";
import { WorkItemTimelinePanel } from "../../components/work-item-timeline-panel";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { formatDateTime as formatDate } from "../lib/date-format";
import {
  EVIDENCE_ACTION_VALUES,
  EVIDENCE_RESOURCE_TYPE_VALUES,
  isEvidenceActionValue,
  isEvidenceResourceTypeValue
} from "../lib/evidence-catalog";
import {
  buildEvidenceManualPackagePayload,
  buildManualReviewPackageFilename,
  deriveEvidenceManualPackageSummary
} from "../lib/evidence-manual-package";
import {
  canReadManualPackageSeal,
  canManageManualPackageSeal,
  canRecordManualPackageSignoff,
  getPendingRequiredManualPackageSignerRoles,
  type ManualPackageSeal
} from "../lib/manual-package-seal";
import { buildWorkItemTimelineLabels } from "../lib/work-item-timeline-labels";
import { useWorkItemTimeline } from "../lib/use-work-item-timeline";
import { fetchAuthContext, resolveOwnerUserId, type AuthContext } from "../lib/ownership";
import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import type { MessageKey } from "../lib/i18n";
import { formatTimelineEvent } from "../lib/work-item-timeline";
import { resolveHashContext } from "../lib/hash-context";
import {
  loadWorkspaceRecords,
  saveWorkspaceRecords,
  sortByLastActionAtDesc,
  toApiDueAt,
  toDateTimeLocalValue
} from "../lib/workspace-storage";
import {
  buildAuditLogQuery,
  extractAuditApiError,
  type AuditLogEntry,
  type AuditLogQueryFilters,
  type AuditLogsResponse
} from "../lib/audit-log";
import {
  isWorkItemUuidLike,
  isWorkItemUuidLike as isUuidLike,
  readWorkItemMetadataBoolean,
  readWorkItemMetadataNumber,
  readWorkItemMetadataString,
  resolveWorkItemOwnerDisplay,
  resolveWorkItemResourceId,
  resolveWorkItemWorkspaceStatus,
  type CreateWorkItemRequest,
  type EvidenceWorkItemMetadata,
  type PatchWorkItemRequest,
  type WorkItemListResponse,
  type WorkItemPriority,
  type WorkItemQueueStatus,
  type WorkItemResponse,
  withCanonicalWorkItemMetadata
} from "../lib/work-items";
import {
  buildOperationalContextLinks,
  type OperationalContextLink,
  inferLogOperationalContext
} from "../lib/operational-context";
type EvidenceFilters = AuditLogQueryFilters & {
  domain: string;
};

const DEFAULT_FILTERS: EvidenceFilters = {
  domain: "all",
  requestId: "",
  action: "",
  resourceType: "",
  reportId: "",
  resourceId: "",
  limit: "50"
};

const MANUAL_REVIEW_VALUE_LABEL_KEYS: Record<string, MessageKey> = {
  manual_review: "evidenceTrail.manualReview.values.manual_review",
  manual_review_pending: "evidenceTrail.manualReview.values.manual_review_pending",
  degraded: "evidenceTrail.manualReview.values.degraded",
  manual_review_required: "evidenceTrail.manualReview.values.manual_review_required"
};
const MANUAL_PACKAGE_VALUE_LABEL_KEYS: Record<string, MessageKey> = {
  due_diligence_manual_review_package: "evidenceTrail.manualPackage.values.due_diligence_manual_review_package",
  source_of_funds_manual_review_package: "evidenceTrail.manualPackage.values.source_of_funds_manual_review_package",
  restricted_regulatory: "evidenceTrail.manualPackage.values.restricted_regulatory",
  regulated_ops_human_review_required: "evidenceTrail.manualPackage.values.regulated_ops_human_review_required",
  regulated_ops_authenticated_context: "evidenceTrail.manualPackage.values.regulated_ops_authenticated_context",
  compliance_dd_signoff: "evidenceTrail.manualPackage.values.compliance_dd_signoff",
  compliance_sof_signoff: "evidenceTrail.manualPackage.values.compliance_sof_signoff",
  human_signoff_required: "evidenceTrail.manualPackage.values.human_signoff_required",
  assisted_review: "evidenceTrail.manualPackage.values.assisted_review",
  chain_correlated: "evidenceTrail.manualPackage.values.chain_correlated",
  event_only: "evidenceTrail.manualPackage.values.event_only",
  hash_materialized_offchain: "evidenceTrail.manualPackage.values.hash_materialized_offchain",
  hash_pending: "evidenceTrail.manualPackage.values.hash_pending",
  manual_review_pending: "evidenceTrail.manualPackage.values.manual_review_pending"
};
const MANUAL_PACKAGE_FIELD_LABEL_KEYS: Record<string, MessageKey> = {
  provider_status: "evidenceTrail.manualPackage.fields.provider_status",
  degraded_reason: "evidenceTrail.manualPackage.fields.degraded_reason",
  counterparty_context: "evidenceTrail.manualPackage.fields.counterparty_context",
  address: "evidenceTrail.manualPackage.fields.address",
  chain: "evidenceTrail.manualPackage.fields.chain",
  purpose: "evidenceTrail.manualPackage.fields.purpose",
  amount: "evidenceTrail.manualPackage.fields.amount"
};
const MANUAL_PACKAGE_CHECKLIST_LABEL_KEYS: Record<string, MessageKey> = {
  validate_counterparty: "evidenceTrail.manualPackage.checklistItems.validate_counterparty",
  attach_human_rationale: "evidenceTrail.manualPackage.checklistItems.attach_human_rationale",
  confirm_relationship_origin: "evidenceTrail.manualPackage.checklistItems.confirm_relationship_origin",
  validate_declared_origin: "evidenceTrail.manualPackage.checklistItems.validate_declared_origin",
  attach_documentary_evidence: "evidenceTrail.manualPackage.checklistItems.attach_documentary_evidence",
  confirm_financial_rationale: "evidenceTrail.manualPackage.checklistItems.confirm_financial_rationale"
};
const MANUAL_PACKAGE_SEAL_STATUS_LABEL_KEYS: Record<string, MessageKey> = {
  pending_signoff: "evidenceTrail.manualPackage.seal.values.pending_signoff",
  ready_to_seal: "evidenceTrail.manualPackage.seal.values.ready_to_seal",
  sealed: "evidenceTrail.manualPackage.seal.values.sealed",
  failed: "evidenceTrail.manualPackage.seal.values.failed",
  revoked: "evidenceTrail.manualPackage.seal.values.revoked",
  superseded: "evidenceTrail.manualPackage.seal.values.superseded"
};
const MANUAL_PACKAGE_SEAL_SIGNER_LABEL_KEYS: Record<string, MessageKey> = {
  compliance_owner: "evidenceTrail.manualPackage.seal.roles.compliance_owner",
  ops_owner: "evidenceTrail.manualPackage.seal.roles.ops_owner",
  legal_owner_optional: "evidenceTrail.manualPackage.seal.roles.legal_owner_optional"
};
const MANUAL_PACKAGE_SEAL_DECISION_LABEL_KEYS: Record<string, MessageKey> = {
  approved: "evidenceTrail.manualPackage.seal.decisions.approved",
  rejected: "evidenceTrail.manualPackage.seal.decisions.rejected"
};
const MANUAL_PACKAGE_SEAL_METHOD_LABEL_KEYS: Record<string, MessageKey> = {
  platform_authenticated_2fa: "evidenceTrail.manualPackage.seal.methods.platform_authenticated_2fa",
  governance_ticket: "evidenceTrail.manualPackage.seal.methods.governance_ticket"
};
const EVIDENCE_ACTION_LABEL_KEYS: Record<string, MessageKey> = {
  compliance_sanctions_checked: "evidenceTrail.values.actions.compliance_sanctions_checked",
  preventive_block_lifted: "evidenceTrail.values.actions.preventive_block_lifted",
  counterparty_created: "evidenceTrail.values.actions.counterparty_created",
  coaf_report_generated: "evidenceTrail.values.actions.coaf_report_generated",
  coaf_report_approved: "evidenceTrail.values.actions.coaf_report_approved",
  coaf_report_rejected: "evidenceTrail.values.actions.coaf_report_rejected",
  coaf_report_submitted_manual: "evidenceTrail.values.actions.coaf_report_submitted_manual",
  report_generated: "evidenceTrail.values.actions.report_generated",
  report_downloaded: "evidenceTrail.values.actions.report_downloaded",
  evidence_manual_review_package_exported: "evidenceTrail.values.actions.evidence_manual_review_package_exported",
  compliance_due_diligence_checked: "evidenceTrail.values.actions.compliance_due_diligence_checked",
  compliance_source_of_funds_checked: "evidenceTrail.values.actions.compliance_source_of_funds_checked",
  evidence_bundle_exported: "evidenceTrail.values.actions.evidence_bundle_exported"
};
const EVIDENCE_RESOURCE_TYPE_LABEL_KEYS: Record<string, MessageKey> = {
  address: "evidenceTrail.values.resourceTypes.address",
  case: "evidenceTrail.values.resourceTypes.case",
  report: "evidenceTrail.values.resourceTypes.report",
  ros_record: "evidenceTrail.values.resourceTypes.ros_record",
  preventive_block: "evidenceTrail.values.resourceTypes.preventive_block",
  counterparty: "evidenceTrail.values.resourceTypes.counterparty",
  audit_log: "evidenceTrail.values.resourceTypes.audit_log"
};

type WorkspacePriority = WorkItemPriority;
type WorkspaceStatus = "queued" | "reviewing" | "sealed";
type WorkspaceSource = "server" | "local";
type EvidenceWorkItemResponse = WorkItemResponse<EvidenceWorkItemMetadata>;
type EvidenceWorkItemListResponse = WorkItemListResponse<EvidenceWorkItemMetadata>;

type EvidenceWorkspaceRecord = {
  workItemId?: string;
  source: WorkspaceSource;
  eventId: string;
  action: string;
  resourceType: string;
  resourceId: string;
  caseId: string;
  requestId: string;
  reportId: string;
  fileHash: string;
  owner: string;
  priority: WorkspacePriority;
  localDeadline: string;
  workspaceStatus: WorkspaceStatus;
  note: string;
  lastActionAt: string;
};

type EvidenceDossierContext = {
  reportId: string;
  rosId: string;
  filename: string;
  dossierSha256: string;
};

type EvidenceHashContext = {
  primaryHash: string;
  sourceLabel: string;
  artifactTypeLabel: string;
};

type EvidenceManualPackageExportContext = {
  packageSha256: string;
  filename: string;
  createdAt: string | null;
};

const STORAGE_KEY = "otc-evidence-workspace";
const WORKSPACE_PAGE_LIMIT = 100;
const MANUAL_PACKAGE_CANONICAL_SIGNOFF_MODE = "compliance_ops_signoff";

const DOMAIN_PRESETS: Array<{
  id: string;
  label: MessageKey;
  description: MessageKey;
  action: string;
  resourceType: string;
  evidenceTypes: string[];
}> = [
  {
    id: "all",
    label: "evidenceTrail.domain.all",
    description: "evidenceTrail.domain.allDescription",
    action: "",
    resourceType: "",
    evidenceTypes: []
  },
  {
    id: "sanctions",
    label: "evidenceTrail.domain.sanctions",
    description: "evidenceTrail.domain.sanctionsDescription",
    action: "compliance_sanctions_checked",
    resourceType: "",
    evidenceTypes: ["SANCTIONS_CHECKED", "SANCTIONS_HIT"]
  },
  {
    id: "blocks",
    label: "evidenceTrail.domain.blocks",
    description: "evidenceTrail.domain.blocksDescription",
    action: "preventive_block_lifted",
    resourceType: "preventive_block",
    evidenceTypes: ["BLOCK_TRIGGERED", "BLOCK_LIFTED", "BLOCK_CONFIRMADO"]
  },
  {
    id: "counterparties",
    label: "evidenceTrail.domain.counterparties",
    description: "evidenceTrail.domain.counterpartiesDescription",
    action: "counterparty_created",
    resourceType: "counterparty",
    evidenceTypes: ["COUNTERPARTY_ONBOARDED", "COUNTERPARTY_UPDATED", "KYC_APPROVED"]
  },
  {
    id: "ros",
    label: "evidenceTrail.domain.ros",
    description: "evidenceTrail.domain.rosDescription",
    action: "coaf_report_generated",
    resourceType: "ros_record",
    evidenceTypes: ["COAF_ROS_GENERATED", "COAF_ROS_APPROVED", "COAF_ROS_REJECTED", "COAF_ROS_SUBMITTED_MANUAL"]
  },
  {
    id: "reports",
    label: "evidenceTrail.domain.reports",
    description: "evidenceTrail.domain.reportsDescription",
    action: "report_downloaded",
    resourceType: "report",
    evidenceTypes: ["REPORT_GENERATED", "REPORT_DOWNLOADED", "EVIDENCE_EXPORTED"]
  },
  {
    id: "due_diligence",
    label: "evidenceTrail.domain.dueDiligence",
    description: "evidenceTrail.domain.dueDiligenceDescription",
    action: "compliance_due_diligence_checked",
    resourceType: "address",
    evidenceTypes: ["MANUAL_REVIEW_REQUIRED", "DUE_DILIGENCE_CHECKED"]
  },
  {
    id: "source_of_funds",
    label: "evidenceTrail.domain.sourceOfFunds",
    description: "evidenceTrail.domain.sourceOfFundsDescription",
    action: "compliance_source_of_funds_checked",
    resourceType: "address",
    evidenceTypes: ["MANUAL_REVIEW_REQUIRED", "SOURCE_OF_FUNDS_CHECKED"]
  }
];

function isManualReviewAction(action: string) {
  return action === "compliance_due_diligence_checked" || action === "compliance_source_of_funds_checked";
}

function resolveManualReviewBaseAction(log: AuditLogEntry | null) {
  if (!log) {
    return null;
  }
  if (isManualReviewAction(log.action)) {
    return log.action;
  }
  if (log.action !== "evidence_manual_review_package_exported") {
    return null;
  }
  const metadata = log.metadata ?? {};
  const relatedAction = readWorkItemMetadataString(metadata, "manual_review_action");
  return isManualReviewAction(relatedAction) ? relatedAction : null;
}

function normalizeWorkspaceStatus(value: unknown): WorkspaceStatus | null {
  if (value === "queued" || value === "reviewing" || value === "sealed") {
    return value;
  }
  return null;
}

function loadWorkspace() {
  return loadWorkspaceRecords<EvidenceWorkspaceRecord>(STORAGE_KEY, (record) => {
    const eventId = typeof record.eventId === "string" ? record.eventId : "";
    const source: WorkspaceSource = record.source === "server" ? "server" : "local";
    return {
      workItemId: typeof record.workItemId === "string" ? record.workItemId : undefined,
      source,
      eventId,
      action: typeof record.action === "string" ? record.action : "",
      resourceType: typeof record.resourceType === "string" ? record.resourceType : "",
      resourceId: typeof record.resourceId === "string" ? record.resourceId : "",
      caseId: typeof record.caseId === "string" ? record.caseId : "",
      requestId: typeof record.requestId === "string" ? record.requestId : "",
      reportId: typeof record.reportId === "string" ? record.reportId : "",
      fileHash: typeof record.fileHash === "string" ? record.fileHash : "",
      owner: typeof record.owner === "string" ? record.owner : "",
      priority: record.priority === "critical" || record.priority === "high" || record.priority === "normal" ? record.priority : "normal",
      localDeadline: typeof record.localDeadline === "string" ? record.localDeadline : "",
      workspaceStatus: normalizeWorkspaceStatus(record.workspaceStatus) ?? "queued",
      note: typeof record.note === "string" ? record.note : "",
      lastActionAt: typeof record.lastActionAt === "string" ? record.lastActionAt : ""
    };
  });
}

function saveWorkspace(records: EvidenceWorkspaceRecord[]) {
  saveWorkspaceRecords(STORAGE_KEY, records);
}

function upsertWorkspaceRecord(
  current: EvidenceWorkspaceRecord[],
  next: Partial<EvidenceWorkspaceRecord> & { eventId: string }
) {
  const existing = current.find((entry) => entry.eventId === next.eventId);
  const base: EvidenceWorkspaceRecord =
    existing ?? {
      workItemId: next.workItemId,
      source: next.source ?? "local",
      eventId: next.eventId,
      action: "",
      resourceType: "",
      resourceId: "",
      caseId: "",
      requestId: "",
      reportId: "",
      fileHash: "",
      owner: "",
      priority: "normal",
      localDeadline: "",
      workspaceStatus: "queued",
      note: "",
      lastActionAt: ""
    };

  const merged: EvidenceWorkspaceRecord = {
    ...base,
    ...next,
    lastActionAt: next.lastActionAt ?? new Date().toISOString()
  };

  return sortByLastActionAtDesc([merged, ...current.filter((entry) => entry.eventId !== next.eventId)]);
}

function mergeWorkspaceRecords(serverRecords: EvidenceWorkspaceRecord[], localRecords: EvidenceWorkspaceRecord[]) {
  const merged = [...serverRecords];
  const seenEventIds = new Set(serverRecords.map((record) => record.eventId));
  const seenWorkItemIds = new Set(serverRecords.map((record) => record.workItemId).filter(Boolean));

  for (const record of localRecords) {
    if (seenEventIds.has(record.eventId)) {
      continue;
    }
    if (record.workItemId && seenWorkItemIds.has(record.workItemId)) {
      continue;
    }
    merged.push(record);
  }

  return sortByLastActionAtDesc(merged);
}

function mapQueueStatusToWorkspaceStatus(status: WorkItemQueueStatus): WorkspaceStatus {
  if (status === "READY" || status === "APPROVED" || status === "SUBMITTED" || status === "CLOSED") {
    return "sealed";
  }
  return "reviewing";
}

function mapWorkItemToWorkspaceRecord(item: EvidenceWorkItemResponse): EvidenceWorkspaceRecord {
  const metadata = item.metadata ?? {};
  const eventId = readWorkItemMetadataString(metadata, "event_id") || item.resource_id;
  return {
    workItemId: item.id,
    source: "server",
    eventId,
    action: readWorkItemMetadataString(metadata, "audit_action"),
    resourceType: readWorkItemMetadataString(metadata, "audit_resource_type"),
    resourceId: readWorkItemMetadataString(metadata, "audit_resource_id"),
    caseId: item.case_id ?? readWorkItemMetadataString(metadata, "case_id"),
    requestId: readWorkItemMetadataString(metadata, "request_id"),
    reportId: readWorkItemMetadataString(metadata, "report_id"),
    fileHash: readWorkItemMetadataString(metadata, "file_hash_sha256"),
    owner: resolveWorkItemOwnerDisplay(metadata, item.owner_user_id),
    priority: item.priority,
    localDeadline: toDateTimeLocalValue(item.due_at),
    workspaceStatus: normalizeWorkspaceStatus(resolveWorkItemWorkspaceStatus(metadata, "evidence_event")) ?? mapQueueStatusToWorkspaceStatus(item.queue_status),
    note: item.note ?? readWorkItemMetadataString(metadata, "note"),
    lastActionAt: item.last_activity_at || item.updated_at
  };
}

function getWorkspaceUrgency(record: EvidenceWorkspaceRecord) {
  if (!record.localDeadline) {
    return "no_deadline";
  }
  if (record.workspaceStatus === "sealed") {
    return "on_track";
  }
  const deadline = new Date(record.localDeadline).getTime();
  if (Number.isNaN(deadline)) {
    return "no_deadline";
  }
  const delta = deadline - Date.now();
  if (delta < 0) {
    return "overdue";
  }
  if (delta < 24 * 60 * 60 * 1000) {
    return "due_soon";
  }
  return "on_track";
}

function toneForWorkspaceSource(source: WorkspaceSource): "success" | "warning" {
  return source === "server" ? "success" : "warning";
}

function resolveDownloadFilename(contentDisposition: string | null, fallbackName: string) {
  if (!contentDisposition) {
    return fallbackName;
  }
  const match = /filename="([^"]+)"/i.exec(contentDisposition);
  return match?.[1] ?? fallbackName;
}

function summarizeDossierHash(hash: string | null) {
  const normalized = hash?.trim() ?? "";
  if (!normalized) {
    return "n/a";
  }
  return normalized.length > 16 ? `${normalized.slice(0, 16)}...` : normalized;
}

function resolveManualWorkspaceRecord(
  workspace: EvidenceWorkspaceRecord[],
  selectedLog: AuditLogEntry | null,
  selectedContext: ReturnType<typeof inferLogOperationalContext> | null
) {
  if (!selectedLog || !selectedContext || !resolveManualReviewBaseAction(selectedLog)) {
    return null;
  }
  return (
    workspace.find((entry: EvidenceWorkspaceRecord) => {
      if (selectedContext.requestId && entry.requestId === selectedContext.requestId) {
        return true;
      }
      if (selectedContext.reportId && entry.reportId === selectedContext.reportId) {
        return true;
      }
      return false;
    }) ??
    null
  );
}

function buildManualPackageAuditPresetHref(requestId: string, reportId: string | null | undefined) {
  const normalizedRequestId = requestId.trim();
  if (!normalizedRequestId) {
    return null;
  }

  const query = new URLSearchParams({
    action: "evidence_manual_review_package_exported",
    resource_type: "audit_log",
    request_id: normalizedRequestId
  });
  const normalizedReportId = reportId?.trim() ?? "";
  if (normalizedReportId) {
    query.set("report_id", normalizedReportId);
  }
  return `/audit?${query.toString()}`;
}

function buildManualPackageGovernanceAuditHref(sealId: string, reportId: string | null | undefined) {
  const normalizedSealId = sealId.trim();
  if (!normalizedSealId) {
    return null;
  }

  const query = new URLSearchParams({
    preset: "governanca",
    seal_id: normalizedSealId
  });
  const normalizedReportId = reportId?.trim() ?? "";
  if (normalizedReportId) {
    query.set("report_id", normalizedReportId);
  }
  return `/audit?${query.toString()}`;
}

function isAuditManualReturnOrigin(value: string | null) {
  return value === "manual_package";
}

function resolveSelectedWorkspaceRecord(
  workspace: EvidenceWorkspaceRecord[],
  selectedLog: AuditLogEntry | null,
  selectedContext: ReturnType<typeof inferLogOperationalContext> | null
) {
  if (!selectedLog) {
    return null;
  }
  return (
    workspace.find((entry: EvidenceWorkspaceRecord) => entry.eventId === selectedLog.id) ??
    resolveManualWorkspaceRecord(workspace, selectedLog, selectedContext)
  );
}

function logMatchesSelectedContext(
  entry: AuditLogEntry,
  selectedContext: ReturnType<typeof inferLogOperationalContext> | null
) {
  if (!selectedContext) {
    return false;
  }

  const entryContext = inferLogOperationalContext(entry);
  if (selectedContext.reportId && entryContext.reportId === selectedContext.reportId) {
    return true;
  }
  if (selectedContext.requestId && entryContext.requestId === selectedContext.requestId) {
    return true;
  }
  if (selectedContext.caseId && entryContext.caseId === selectedContext.caseId) {
    return true;
  }
  return false;
}

function buildWorkspaceSummary(record: EvidenceWorkspaceRecord) {
  return {
    work_item_id: record.workItemId ?? null,
    event_id: record.eventId,
    action: record.action || null,
    resource_type: record.resourceType || null,
    resource_id: record.resourceId || null,
    case_id: record.caseId || null,
    request_id: record.requestId || null,
    report_id: record.reportId || null,
    file_hash_sha256: record.fileHash || null,
    owner: record.owner || null,
    priority: record.priority,
    deadline: record.localDeadline || null,
    status: record.workspaceStatus,
    source: record.source,
    note: record.note || null,
    last_action_at: record.lastActionAt
  };
}

function resolveLogForWorkspaceRecord(logs: AuditLogEntry[], record: EvidenceWorkspaceRecord) {
  return (
    logs.find((entry: AuditLogEntry) => entry.id === record.eventId) ??
    logs.find((entry: AuditLogEntry) => {
      if (record.requestId && entry.request_id === record.requestId) {
        return true;
      }
      if (record.reportId && entry.report_id === record.reportId) {
        return true;
      }
      if (record.resourceType && entry.resource_type !== record.resourceType) {
        return false;
      }
      if (record.resourceId && entry.resource_id !== record.resourceId) {
        return false;
      }
      return Boolean(record.resourceType || record.resourceId);
    }) ??
    null
  );
}

export default function EvidenceTrailPage() {
  const { locale, t } = useI18n();
  const searchParams = useSearchParams();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);
  const formatTranslatedCodeValue = (value: string | null | undefined, labelKeys: Record<string, MessageKey>) => {
    const normalized = value?.trim() ?? "";
    if (!normalized) {
      return tr("evidenceTrail.notAvailable" as MessageKey);
    }
    const labelKey = labelKeys[normalized];
    if (!labelKey) {
      return normalized;
    }
    const translated = tr(labelKey);
    return translated === normalized ? normalized : `${translated} (${normalized})`;
  };
  const formatTranslatedCodeList = (values: string[], labelKeys: Record<string, MessageKey>, separator: string) => {
    if (!values.length) {
      return tr("evidenceTrail.notAvailable" as MessageKey);
    }
    return values.map((value) => formatTranslatedCodeValue(value, labelKeys)).join(separator);
  };
  const formatDateValue = (value: string | null | undefined) => {
    const normalized = value?.trim() ?? "";
    return normalized ? formatDate(normalized, locale) ?? normalized : tr("evidenceTrail.notAvailable" as MessageKey);
  };
  const formatOptionalDateValue = (value: string | null | undefined) => {
    const normalized = value?.trim() ?? "";
    return normalized ? formatDateValue(normalized) : tr("evidenceTrail.notAvailable" as MessageKey);
  };
  const formatEvidenceActionValue = (value: string | null | undefined) => {
    const normalized = value?.trim() ?? "";
    if (!normalized) {
      return tr("evidenceTrail.notAvailable" as MessageKey);
    }
    if (!isEvidenceActionValue(normalized)) {
      return normalized;
    }
    return formatTranslatedCodeValue(normalized, EVIDENCE_ACTION_LABEL_KEYS);
  };
  const formatEvidenceResourceTypeValue = (value: string | null | undefined) => {
    const normalized = value?.trim() ?? "";
    if (!normalized) {
      return tr("evidenceTrail.notAvailable" as MessageKey);
    }
    if (!isEvidenceResourceTypeValue(normalized)) {
      return normalized;
    }
    return formatTranslatedCodeValue(normalized, EVIDENCE_RESOURCE_TYPE_LABEL_KEYS);
  };
  const formatManualPackageSealStatusValue = (value: string | null | undefined) =>
    formatTranslatedCodeValue(value, MANUAL_PACKAGE_SEAL_STATUS_LABEL_KEYS);
  const formatManualPackageSealRoleValue = (value: string | null | undefined) =>
    formatTranslatedCodeValue(value, MANUAL_PACKAGE_SEAL_SIGNER_LABEL_KEYS);
  const formatManualPackageSealDecisionValue = (value: string | null | undefined) =>
    formatTranslatedCodeValue(value, MANUAL_PACKAGE_SEAL_DECISION_LABEL_KEYS);
  const formatManualPackageSealMethodValue = (value: string | null | undefined) =>
    formatTranslatedCodeValue(value, MANUAL_PACKAGE_SEAL_METHOD_LABEL_KEYS);
  const toneForManualPackageSealStatus = (value: string | null | undefined): "success" | "warning" | "danger" => {
    if (value === "sealed") {
      return "success";
    }
    if (value === "failed" || value === "revoked" || value === "superseded") {
      return "danger";
    }
    return "warning";
  };

  function renderDossierContext(
    context: EvidenceDossierContext,
    testIds: { container: string; openReport: string; openRosCoaf: string }
  ) {
    return (
      <div className="otc-stack otc-controls--spaced" data-testid={testIds.container}>
        <strong>{tr("evidenceTrail.details.dossierContextTitle" as MessageKey)}</strong>
        <div className="otc-kv">
          <div className="otc-kv__row">
            <span className="otc-kv__key">{tr("evidenceTrail.details.dossierFilename" as MessageKey)}</span>
            <span className="otc-kv__value otc-mono">{context.filename || tr("evidenceTrail.notAvailable" as MessageKey)}</span>
          </div>
          <div className="otc-kv__row">
            <span className="otc-kv__key">{tr("evidenceTrail.details.dossierHash" as MessageKey)}</span>
            <span className="otc-kv__value otc-mono">{context.dossierSha256 || tr("evidenceTrail.notAvailable" as MessageKey)}</span>
          </div>
        </div>
        <div className="otc-controls">
          {context.reportId ? (
            <a
              className="otc-button otc-button--ghost"
              href={`/reports?history_report_id=${encodeURIComponent(context.reportId)}`}
              data-testid={testIds.openReport}
            >
              {tr("evidenceTrail.details.openDossierReport" as MessageKey)}
            </a>
          ) : null}
          <a
            className="otc-button otc-button--ghost"
            href={`/ros-coaf?ros_id=${encodeURIComponent(context.rosId)}${
              context.reportId ? `&report_id=${encodeURIComponent(context.reportId)}` : ""
            }`}
            data-testid={testIds.openRosCoaf}
          >
            {tr("evidenceTrail.details.openDossierRosCoaf" as MessageKey)}
          </a>
        </div>
      </div>
    );
  }

  function renderHashContextDetail(context: EvidenceHashContext) {
    return (
      <div className="otc-kv" data-testid="evidence-hash-context">
        <div className="otc-kv__row">
          <span className="otc-kv__key">{tr("evidenceTrail.details.activeHash" as MessageKey)}</span>
          <span className="otc-kv__value otc-mono">{context.primaryHash}</span>
        </div>
        <div className="otc-kv__row">
          <span className="otc-kv__key">{tr("evidenceTrail.details.hashSource" as MessageKey)}</span>
          <span className="otc-kv__value">{context.sourceLabel}</span>
        </div>
        <div className="otc-kv__row">
          <span className="otc-kv__key">{tr("evidenceTrail.details.artifactType" as MessageKey)}</span>
          <span className="otc-kv__value">{context.artifactTypeLabel}</span>
        </div>
      </div>
    );
  }

  function renderHashContextChainRows(context: EvidenceHashContext) {
    return (
      <>
        <div className="otc-kv__row" data-testid="evidence-chain-hash-source">
          <span className="otc-kv__key">{tr("evidenceTrail.details.hashSource" as MessageKey)}</span>
          <span className="otc-kv__value">{context.sourceLabel}</span>
        </div>
        <div className="otc-kv__row" data-testid="evidence-chain-artifact-type">
          <span className="otc-kv__key">{tr("evidenceTrail.details.artifactType" as MessageKey)}</span>
          <span className="otc-kv__value">{context.artifactTypeLabel}</span>
        </div>
      </>
    );
  }
  const [filters, setFilters] = useState<EvidenceFilters>(DEFAULT_FILTERS);
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [count, setCount] = useState(0);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportingSelectedChain, setExportingSelectedChain] = useState(false);
  const [exportingManualPackage, setExportingManualPackage] = useState(false);
  const [exportingRosCoafDossier, setExportingRosCoafDossier] = useState(false);
  const [lastRosDossierExport, setLastRosDossierExport] = useState<{ rosId: string; sha256: string; filename: string } | null>(null);
  const [syncingWorkspace, setSyncingWorkspace] = useState(false);
  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [manualPackageSeal, setManualPackageSeal] = useState<ManualPackageSeal | null>(null);
  const [manualPackageSealLoading, setManualPackageSealLoading] = useState(false);
  const [manualPackageSealError, setManualPackageSealError] = useState<string | null>(null);
  const [initializingManualPackageSignoff, setInitializingManualPackageSignoff] = useState(false);
  const [recordingManualPackageSignoff, setRecordingManualPackageSignoff] = useState(false);
  const [finalizingManualPackageSeal, setFinalizingManualPackageSeal] = useState(false);
  const [revokingManualPackageSeal, setRevokingManualPackageSeal] = useState(false);
  const [supersedingManualPackageSeal, setSupersedingManualPackageSeal] = useState(false);
  const [manualPackageRevokeTicketRef, setManualPackageRevokeTicketRef] = useState("");
  const [manualPackageRevokeReason, setManualPackageRevokeReason] = useState("");
  const [manualPackageSupersedeSealId, setManualPackageSupersedeSealId] = useState("");
  const [manualPackageSupersedeTicketRef, setManualPackageSupersedeTicketRef] = useState("");
  const [manualPackageSupersedeReason, setManualPackageSupersedeReason] = useState("");
  const [manualPackageSignoffRole, setManualPackageSignoffRole] = useState("compliance_owner");
  const [manualPackageSignoffDecision, setManualPackageSignoffDecision] = useState("approved");
  const [manualPackageSignoffMethod, setManualPackageSignoffMethod] = useState("platform_authenticated_2fa");
  const [manualPackageSignoffTicketRef, setManualPackageSignoffTicketRef] = useState("");
  const [manualPackageSignoffNotes, setManualPackageSignoffNotes] = useState("");
  const [manualPackageSignoffDisplayName, setManualPackageSignoffDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);
  const [linkedRosIdFromReport, setLinkedRosIdFromReport] = useState<string | null>(null);
  const [linkedRosLoading, setLinkedRosLoading] = useState(false);
  const [workspace, setWorkspace] = useState<EvidenceWorkspaceRecord[]>([]);
  const [owner, setOwner] = useState("");
  const [priority, setPriority] = useState<WorkspacePriority>("normal");
  const [localDeadline, setLocalDeadline] = useState("");
  const [workspaceStatus, setWorkspaceStatus] = useState<WorkspaceStatus>("queued");
  const [workspaceNote, setWorkspaceNote] = useState("");
  const [timelineEventId, setTimelineEventId] = useState("");
  const {
    timelineLoading,
    timelineError,
    timelineData,
    commentType,
    commentBody,
    commentSubmitting,
    setCommentType,
    setCommentBody,
    resetTimeline,
    loadTimeline,
    submitTimelineComment
  } = useWorkItemTimeline<WorkItemResponse>({
    resolveErrorMessage: (apiError, fallback) => resolveApiErrorMessage(t, apiError, fallback),
    loadErrorMessage: tr("evidenceTrail.workspace.timeline.errorLoad" as MessageKey),
    commentErrorMessage: tr("evidenceTrail.workspace.timeline.errorComment" as MessageKey),
    emptySelectionErrorMessage: tr("evidenceTrail.workspace.timeline.emptyLocal" as MessageKey),
    emptyCommentErrorMessage: tr("evidenceTrail.workspace.timeline.commentEmpty" as MessageKey),
    onCommentSaved: () => {
      setNotice(tr("evidenceTrail.workspace.timeline.commentSaved" as MessageKey));
    }
  });
  const latestRequestRef = useRef(0);

  const selectedDomain = useMemo(
    () => DOMAIN_PRESETS.find((preset) => preset.id === filters.domain) ?? DOMAIN_PRESETS[0],
    [filters.domain]
  );
  const activeFilterCount = useMemo(
    () => [filters.requestId, filters.action, filters.resourceType, filters.reportId, filters.resourceId].filter((value) => value.trim()).length,
    [filters]
  );
  const selectedContext = useMemo(() => (selectedLog ? inferLogOperationalContext(selectedLog) : null), [selectedLog]);
  useEffect(() => {
    const reportId = selectedContext?.reportId?.trim() ?? "";
    if (!reportId || Boolean(selectedContext?.rosId)) {
      setLinkedRosIdFromReport(null);
      setLinkedRosLoading(false);
      return;
    }

    setLinkedRosLoading(true);
    fetch(`/api/app/reports/${encodeURIComponent(reportId)}/ros-coaf-ref`, { cache: "no-store" })
      .then(async (res) => {
        const data = (await res.json().catch(() => null)) as { ros_id?: string | null } | null;
        if (!res.ok) {
          setLinkedRosIdFromReport(null);
          setLinkedRosLoading(false);
          return;
        }
        const rosIdValue = typeof data?.ros_id === "string" ? data.ros_id.trim() : "";
        setLinkedRosIdFromReport(rosIdValue ? rosIdValue : null);
        setLinkedRosLoading(false);
      })
      .catch(() => {
        setLinkedRosIdFromReport(null);
        setLinkedRosLoading(false);
      });
  }, [selectedContext?.reportId, selectedContext?.rosId]);
  const selectedContextForLinks = useMemo(() => {
    if (!selectedContext) {
      return null;
    }
    if (selectedContext.rosId) {
      return selectedContext;
    }
    if (linkedRosIdFromReport) {
      return { ...selectedContext, rosId: linkedRosIdFromReport };
    }
    return selectedContext;
  }, [linkedRosIdFromReport, selectedContext]);
  const resolvedRosIdForDossier = selectedContextForLinks?.rosId?.trim() ?? "";
  const selectedDossierContext = useMemo(() => {
    if (!resolvedRosIdForDossier) {
      return null;
    }
    if (!lastRosDossierExport || lastRosDossierExport.rosId !== resolvedRosIdForDossier) {
      return null;
    }

    const reportId = selectedLog?.report_id?.trim() ?? "";
    const filename = lastRosDossierExport.filename.trim();
    const dossierSha256 = lastRosDossierExport.sha256.trim();
    if (!filename && !dossierSha256) {
      return null;
    }

    return {
      reportId,
      rosId: resolvedRosIdForDossier,
      filename,
      dossierSha256
    };
  }, [lastRosDossierExport, resolvedRosIdForDossier, selectedLog?.report_id]);
  const selectedManualReviewAction = useMemo(() => resolveManualReviewBaseAction(selectedLog), [selectedLog]);
  const selectedManualReview = useMemo(() => {
    if (!selectedLog || !selectedManualReviewAction) {
      return null;
    }
    const metadata = selectedLog.metadata ?? {};
    return {
      provider: readWorkItemMetadataString(metadata, "provider") || "manual_review",
      providerStatus: readWorkItemMetadataString(metadata, "provider_status") || "degraded",
      degradedReason: readWorkItemMetadataString(metadata, "degraded_reason") || "manual_review_required",
      capabilityStatus: readWorkItemMetadataString(metadata, "capability_status") || "degraded",
      deliveryMode:
        readWorkItemMetadataString(metadata, "delivery_mode") ||
        readWorkItemMetadataString(metadata, "origin_analysis_status") ||
        "manual_review_pending",
      requiresHumanReview:
        readWorkItemMetadataBoolean(metadata, "requires_human_review") ??
        readWorkItemMetadataBoolean(metadata, "counterparty_context_present") ??
        true,
      counterpartyContext: readWorkItemMetadataString(metadata, "counterparty_context"),
      purpose: readWorkItemMetadataString(metadata, "purpose"),
      amount: readWorkItemMetadataNumber(metadata, "amount")
    };
  }, [selectedLog, selectedManualReviewAction]);
  const selectedManualPackageSummary = useMemo(() => {
    if (!selectedManualReview || !selectedLog || !selectedContext || !selectedManualReviewAction) {
      return null;
    }
    return deriveEvidenceManualPackageSummary({
      action: selectedManualReviewAction,
      review: selectedManualReview,
      scopeId: selectedContext.requestId || selectedContext.address || selectedLog.id,
      hasRequestId: Boolean(selectedContext.requestId),
      hasReportId: Boolean(selectedContext.reportId),
      hasFileHash: Boolean(selectedContext.fileHash || selectedLog.file_hash_sha256)
    });
  }, [selectedContext, selectedLog, selectedManualReview, selectedManualReviewAction]);
  const selectedManualWorkspaceRecord = useMemo(() => {
    if (!selectedLog || !selectedManualReviewAction) {
      return null;
    }
    return resolveSelectedWorkspaceRecord(workspace, selectedLog, selectedContext);
  }, [selectedContext, selectedLog, selectedManualReviewAction, workspace]);
  const selectedManualAuditPresetHref = useMemo(() => {
    if (!selectedManualPackageSummary) {
      return null;
    }

    const requestId = selectedContext?.requestId?.trim() || readWorkItemMetadataString(selectedLog?.metadata ?? {}, "request_id");
    const reportId = selectedContext?.reportId?.trim() || readWorkItemMetadataString(selectedLog?.metadata ?? {}, "report_id");
    return buildManualPackageAuditPresetHref(requestId, reportId);
  }, [selectedContext?.reportId, selectedContext?.requestId, selectedLog?.metadata, selectedManualPackageSummary]);
  const selectedManualGovernanceAuditHref = useMemo(() => {
    const sealId = manualPackageSeal?.seal_id?.trim() ?? "";
    if (!sealId) {
      return null;
    }

    const reportId =
      manualPackageSeal?.report_id?.trim() ||
      selectedContext?.reportId?.trim() ||
      readWorkItemMetadataString(selectedLog?.metadata ?? {}, "report_id");
    return buildManualPackageGovernanceAuditHref(sealId, reportId);
  }, [manualPackageSeal?.report_id, manualPackageSeal?.seal_id, selectedContext?.reportId, selectedLog?.metadata]);
  const selectedWorkspaceRecord = useMemo(
    () => resolveSelectedWorkspaceRecord(workspace, selectedLog, selectedContext),
    [selectedContext, selectedLog, workspace]
  );
  const selectedChainLogs = useMemo(() => {
    if (!selectedContext) {
      return [] as AuditLogEntry[];
    }
    return logs.filter((entry: AuditLogEntry) => logMatchesSelectedContext(entry, selectedContext));
  }, [logs, selectedContext]);
  const selectedManualPackageExportContext = useMemo<EvidenceManualPackageExportContext | null>(() => {
    if (!selectedManualPackageSummary || !selectedContext) {
      return null;
    }

    const exportEntry = selectedChainLogs
      .filter((entry: AuditLogEntry) => entry.action === "evidence_manual_review_package_exported")
      .slice()
      .sort((a: AuditLogEntry, b: AuditLogEntry) => String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")))
      .find((entry: AuditLogEntry) => {
        const manualReviewAction = readWorkItemMetadataString(entry.metadata ?? {}, "manual_review_action");
        return !manualReviewAction || manualReviewAction === selectedManualReviewAction;
      });

    if (!exportEntry) {
      return null;
    }

    const packageSha256 = readWorkItemMetadataString(exportEntry.metadata ?? {}, "package_sha256");
    const filename = readWorkItemMetadataString(exportEntry.metadata ?? {}, "filename");
    if (!packageSha256 && !filename) {
      return null;
    }

    return {
      packageSha256,
      filename,
      createdAt: exportEntry.created_at
    };
  }, [selectedChainLogs, selectedContext, selectedManualPackageSummary, selectedManualReviewAction]);
  const canManageManualPackageSealState = useMemo(
    () => canManageManualPackageSeal(authContext?.role),
    [authContext?.role]
  );
  const pendingManualPackageSignerRoles = useMemo(
    () => getPendingRequiredManualPackageSignerRoles(manualPackageSeal),
    [manualPackageSeal]
  );
  const availableManualPackageSignerRoles = useMemo(
    () => pendingManualPackageSignerRoles.filter((role) => canRecordManualPackageSignoff(authContext?.role, role)),
    [authContext?.role, pendingManualPackageSignerRoles]
  );
  const selectedHashContext = useMemo(() => {
    const dossierSha256 =
      lastRosDossierExport && lastRosDossierExport.rosId === resolvedRosIdForDossier
        ? lastRosDossierExport.sha256.trim()
        : "";

    const resolved = resolveHashContext({
      packageSha256: selectedManualPackageExportContext?.packageSha256,
      dossierSha256,
      fileSha256: selectedLog?.file_hash_sha256
    });
    if (!resolved) {
      return null;
    }

    const isManualPackage = resolved.source === "package";
    const isDossier = resolved.source === "dossier";
    return {
      primaryHash: resolved.primaryHash,
      sourceLabel: tr(
        isManualPackage
          ? ("evidenceTrail.details.hashSourceManualPackage" as MessageKey)
          : isDossier
            ? ("evidenceTrail.details.hashSourceDossier" as MessageKey)
            : ("evidenceTrail.details.hashSourceFile" as MessageKey)
      ),
      artifactTypeLabel: tr(
        isManualPackage
          ? ("evidenceTrail.details.artifactTypeManualPackage" as MessageKey)
          : isDossier
            ? ("evidenceTrail.details.artifactTypeDossier" as MessageKey)
            : ("evidenceTrail.details.artifactTypeFile" as MessageKey)
      )
    };
  }, [lastRosDossierExport, resolvedRosIdForDossier, selectedLog?.file_hash_sha256, selectedManualPackageExportContext?.packageSha256, tr]);
  const selectedChainSummary = useMemo(() => {
    if (!selectedChainLogs.length) {
      return null;
    }
    const sorted = selectedChainLogs
      .slice()
      .sort((a: AuditLogEntry, b: AuditLogEntry) => String(a.created_at ?? "").localeCompare(String(b.created_at ?? "")));
    return {
      total: selectedChainLogs.length,
      uniqueActions: new Set(selectedChainLogs.map((entry: AuditLogEntry) => entry.action).filter(Boolean)).size,
      firstAt: sorted[0]?.created_at ?? null,
      lastAt: sorted[sorted.length - 1]?.created_at ?? null,
      withHash: selectedChainLogs.filter((entry: AuditLogEntry) => entry.file_hash_sha256).length,
      withReportId: selectedChainLogs.filter((entry: AuditLogEntry) => entry.report_id).length,
      withRequestId: selectedChainLogs.filter((entry: AuditLogEntry) => entry.request_id).length
    };
  }, [selectedChainLogs]);
  const selectedContextLinks = useMemo(() => {
    if (!selectedContextForLinks) {
      return [] as Array<OperationalContextLink & { labelKey: MessageKey }>;
    }
    const labelKeyByKind: Record<OperationalContextLink["kind"], MessageKey> = {
      case: "evidenceTrail.details.openCase",
      audit: "evidenceTrail.details.openAudit",
      evidence: "evidenceTrail.details.openAudit",
      reports: "evidenceTrail.details.openReports",
      investigate: "evidenceTrail.details.openInvestigate",
      sanctions: "evidenceTrail.details.openSanctions",
      blocks: "evidenceTrail.details.openBlocks",
      counterparty: "evidenceTrail.details.openCounterparty",
      ros: "evidenceTrail.details.openRos"
    };

    return buildOperationalContextLinks(selectedContextForLinks, {
      auditFallbackResourceType: "audit_log"
    })
      .filter((link: OperationalContextLink) => link.kind !== "evidence")
      .map((link: OperationalContextLink) => ({
        ...link,
        labelKey: labelKeyByKind[link.kind]
      }));
  }, [selectedContextForLinks]);
  const auditManualReturnContext = useMemo(() => {
    if (!isAuditManualReturnOrigin(searchParams.get("audit_origin"))) {
      return null;
    }

    const requestId = searchParams.get("request_id")?.trim() ?? "";
    if (!requestId) {
      return null;
    }

    const action = searchParams.get("action")?.trim() ?? "";
    const reportId = searchParams.get("report_id")?.trim() ?? "";
    const domain = searchParams.get("domain")?.trim() ?? "";
    const actionLabel = action ? formatEvidenceActionValue(action) : tr("evidenceTrail.notAvailable" as MessageKey);
    const domainLabel = domain ? tr(`evidenceTrail.domain.${domain === "due_diligence" ? "dueDiligence" : domain === "source_of_funds" ? "sourceOfFunds" : "all"}` as MessageKey) : tr("evidenceTrail.notAvailable" as MessageKey);

    return {
      requestId,
      actionLabel,
      domainLabel,
      auditHref: buildManualPackageAuditPresetHref(requestId, reportId)
    };
  }, [searchParams, tr]);
  const workspaceByEventId = useMemo(
    () => new Map(workspace.map((record: EvidenceWorkspaceRecord) => [record.eventId, record])),
    [workspace]
  );
  const selectedTimelineRecord = timelineEventId ? workspaceByEventId.get(timelineEventId) ?? null : null;
  const serverWorkspaceCount = useMemo(
    () => workspace.filter((record: EvidenceWorkspaceRecord) => record.source === "server").length,
    [workspace]
  );
  const localWorkspaceCount = useMemo(
    () => workspace.filter((record: EvidenceWorkspaceRecord) => record.source === "local").length,
    [workspace]
  );
  const hasMixedWorkspaceSources = serverWorkspaceCount > 0 && localWorkspaceCount > 0;
  const timelineContextBadges = selectedTimelineRecord
    ? [
        {
          label: tr(`evidenceTrail.workspace.source.${selectedTimelineRecord.source}` as MessageKey),
          tone: toneForWorkspaceSource(selectedTimelineRecord.source) as "success" | "warning"
        },
        {
          label: tr(`evidenceTrail.workspace.status.${selectedTimelineRecord.workspaceStatus}` as MessageKey),
          tone: (
            selectedTimelineRecord.workspaceStatus === "sealed"
              ? "success"
              : selectedTimelineRecord.workspaceStatus === "reviewing"
                ? "warning"
                : "danger"
          ) as "success" | "warning" | "danger"
        }
      ]
    : [];

  function filtersFromSearchParams(): EvidenceFilters {
    return {
      domain: searchParams.get("domain") ?? DEFAULT_FILTERS.domain,
      requestId: searchParams.get("request_id") ?? "",
      action: searchParams.get("action") ?? "",
      resourceType: searchParams.get("resource_type") ?? "",
      reportId: searchParams.get("report_id") ?? "",
      resourceId: searchParams.get("resource_id") ?? "",
      limit: searchParams.get("limit") ?? DEFAULT_FILTERS.limit
    };
  }

  async function fetchLogs(nextFilters: EvidenceFilters, page = 1) {
    const requestNumber = latestRequestRef.current + 1;
    latestRequestRef.current = requestNumber;
    setLoading(true);
    setError(null);
    setNotice(null);
    const res = await fetch(`/api/app/audit/logs?${buildAuditLogQuery(nextFilters, page)}`, { cache: "no-store" });
    const data = (await res.json().catch(() => null)) as AuditLogsResponse | { error?: string } | null;
    if (requestNumber !== latestRequestRef.current) {
      return;
    }
    if (!res.ok) {
      const apiError = extractAuditApiError(data);
      setLogs([]);
      setCount(0);
      setTotal(0);
      setCurrentPage(1);
      setHasMore(false);
      setSelectedLog(null);
      setError(apiError ? resolveApiErrorMessage(t, apiError, tr("evidenceTrail.errorLoad" as MessageKey)) : tr("evidenceTrail.errorLoad" as MessageKey));
      setLoading(false);
      return;
    }

    const payload = data && "data" in data ? data : null;
    const rows = payload?.data ?? [];
    setLogs(rows);
    setCount(Number(payload?.count ?? rows.length));
    setTotal(Number(payload?.total ?? rows.length));
    setCurrentPage(Number(payload?.page ?? page));
    setHasMore(Boolean(payload?.has_more));
    setSelectedLog((current: AuditLogEntry | null) => rows.find((entry: AuditLogEntry) => entry.id === current?.id) ?? rows[0] ?? null);
    setLoading(false);
  }

  async function loadOperationalWorkspace(localRecords: EvidenceWorkspaceRecord[]) {
    const res = await fetch(
      `/api/app/operations/work-items?module=evidence&resource_type=evidence_event&limit=${WORKSPACE_PAGE_LIMIT}`,
      { cache: "no-store" }
    );
    const data = (await res.json().catch(() => null)) as EvidenceWorkItemListResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setWorkspace(localRecords);
      setNotice(tr("evidenceTrail.workspace.noticeLoadedLocal" as MessageKey));
      return;
    }

    const items = data && "data" in data && Array.isArray(data.data) ? data.data : [];
    const serverRecords = items.map((item) => mapWorkItemToWorkspaceRecord(item));
    setWorkspace(mergeWorkspaceRecords(serverRecords, localRecords));
  }

  useEffect(() => {
    const nextFilters = filtersFromSearchParams();
    setFilters(nextFilters);
    const localRecords = loadWorkspace();
    setWorkspace(localRecords);
    loadOperationalWorkspace(localRecords).catch(() => {
      setWorkspace(localRecords);
      setNotice(tr("evidenceTrail.workspace.noticeLoadedLocal" as MessageKey));
    });
    fetchLogs(nextFilters).catch(() => {
      setError(tr("evidenceTrail.errorLoad" as MessageKey));
      setLoading(false);
    });

    fetchAuthContext()
      .then((data) => {
        if (data) {
          setAuthContext(data);
        }
      })
      .catch(() => {
        // Keep owner_user_id optional when auth context is unavailable.
      });
  }, [searchParams]);

  useEffect(() => {
    const packageSha256 = selectedManualPackageExportContext?.packageSha256?.trim() ?? "";
    if (!packageSha256) {
      setManualPackageSeal(null);
      setManualPackageSealError(null);
      setManualPackageSealLoading(false);
      return;
    }

    if (!canReadManualPackageSeal(authContext?.role)) {
      setManualPackageSeal(null);
      setManualPackageSealError(null);
      setManualPackageSealLoading(false);
      return;
    }

    let active = true;
    setManualPackageSealLoading(true);
    setManualPackageSealError(null);
    fetch(`/api/app/evidence/manual-package/seal?package_sha256=${encodeURIComponent(packageSha256)}`, { cache: "no-store" })
      .then(async (res) => {
        const data = (await res.json().catch(() => null)) as ManualPackageSeal | { error?: string } | null;
        if (!active) {
          return;
        }
        if (!res.ok) {
          setManualPackageSeal(null);
          setManualPackageSealError(res.status === 404 ? null : tr("evidenceTrail.manualPackage.seal.errorLoad" as MessageKey));
          setManualPackageSealLoading(false);
          return;
        }

        setManualPackageSeal(data && "seal_id" in data ? data : null);
        setManualPackageSealError(null);
        setManualPackageSealLoading(false);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setManualPackageSeal(null);
        setManualPackageSealError(tr("evidenceTrail.manualPackage.seal.errorLoad" as MessageKey));
        setManualPackageSealLoading(false);
      });

    return () => {
      active = false;
    };
  }, [authContext?.role, locale, selectedManualPackageExportContext?.packageSha256]);

  useEffect(() => {
    if (!pendingManualPackageSignerRoles.length) {
      return;
    }
    if (!availableManualPackageSignerRoles.includes(manualPackageSignoffRole)) {
      setManualPackageSignoffRole(availableManualPackageSignerRoles[0] ?? "");
    }
  }, [availableManualPackageSignerRoles, manualPackageSignoffRole]);

  useEffect(() => {
    saveWorkspace(workspace);
  }, [workspace]);

  useEffect(() => {
    if (!workspace.length) {
      setTimelineEventId("");
      resetTimeline();
      return;
    }
    if (!timelineEventId || !workspace.some((entry: EvidenceWorkspaceRecord) => entry.eventId === timelineEventId)) {
      const firstServerRecord = workspace.find((entry: EvidenceWorkspaceRecord) => Boolean(entry.workItemId)) ?? workspace[0];
      setTimelineEventId(firstServerRecord.eventId);
    }
  }, [timelineEventId, workspace]);

  useEffect(() => {
    if (!selectedLog) {
      return;
    }
    const currentRecord = selectedWorkspaceRecord;
    if (!currentRecord) {
      return;
    }
    setOwner(currentRecord.owner);
    setPriority(currentRecord.priority);
    setLocalDeadline(currentRecord.localDeadline);
    setWorkspaceStatus(currentRecord.workspaceStatus);
    setWorkspaceNote(currentRecord.note);
  }, [selectedLog, selectedWorkspaceRecord]);

  useEffect(() => {
    if (!selectedTimelineRecord?.workItemId) {
      resetTimeline();
      return;
    }
    void loadTimeline(selectedTimelineRecord.workItemId);
  }, [loadTimeline, resetTimeline, selectedTimelineRecord?.workItemId]);

  function updateFilter<K extends keyof EvidenceFilters>(key: K, value: EvidenceFilters[K]) {
    setFilters((current: EvidenceFilters) => ({ ...current, [key]: value }));
  }

  function applyDomainPreset(domainId: string) {
    const preset = DOMAIN_PRESETS.find((entry) => entry.id === domainId) ?? DOMAIN_PRESETS[0];
    const nextFilters = {
      ...filters,
      domain: preset.id,
      action: preset.action,
      resourceType: preset.resourceType
    };
    setFilters(nextFilters);
    void fetchLogs(nextFilters, 1);
  }

  async function onReset() {
    setFilters(DEFAULT_FILTERS);
    await fetchLogs(DEFAULT_FILTERS, 1);
  }

  async function onExportEvidence() {
    setExporting(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch("/api/app/audit/evidence-export", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          format: "json",
          request_id: filters.requestId.trim() || null,
          action: filters.action.trim() || null,
          resource_type: filters.resourceType.trim() || null,
          report_id: filters.reportId.trim() || null,
          resource_id: filters.resourceId.trim() || null,
          limit: Number(filters.limit),
          include_audit_logs: true,
          include_credit_ledger: true,
          include_reports: true
        })
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as { error?: string } | null;
        throw new Error(data?.error ? resolveApiErrorMessage(t, data.error, tr("evidenceTrail.errorExport" as MessageKey)) : tr("evidenceTrail.errorExport" as MessageKey));
      }

      const blob = await res.blob();
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = href;
      link.download = resolveDownloadFilename(res.headers.get("content-disposition"), "ontrackchain-evidence-bundle.json");
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(href);
      setNotice(tr("evidenceTrail.exportSuccess" as MessageKey));
    } catch (exportError) {
      setError(exportError instanceof Error ? exportError.message : tr("evidenceTrail.errorExport" as MessageKey));
    } finally {
      setExporting(false);
    }
  }

  function focusSelectedChain() {
    if (!selectedContext) {
      return;
    }
    const nextFilters: EvidenceFilters = {
      ...filters,
      domain: selectedContext.reportId ? "reports" : filters.domain,
      requestId: selectedContext.requestId || "",
      action: "",
      resourceType: "",
      reportId: selectedContext.reportId || "",
      resourceId: ""
    };
    setFilters(nextFilters);
    void fetchLogs(nextFilters, 1);
  }

  async function fetchSelectedChainBundle() {
    const res = await fetch("/api/app/audit/evidence-export", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        format: "json",
        request_id: selectedContext?.requestId || null,
        action: null,
        resource_type: selectedContext?.caseId ? "case" : selectedLog?.resource_type || null,
        report_id: selectedContext?.reportId || null,
        resource_id: selectedContext?.caseId || selectedLog?.resource_id || null,
        limit: Number(filters.limit),
        include_audit_logs: true,
        include_credit_ledger: true,
        include_reports: true
      })
    });
    if (!res.ok) {
      const data = (await res.json().catch(() => null)) as { error?: string } | null;
      throw new Error(data?.error ? resolveApiErrorMessage(t, data.error, tr("evidenceTrail.errorExport" as MessageKey)) : tr("evidenceTrail.errorExport" as MessageKey));
    }
    return res;
  }

  async function onExportSelectedChain() {
    if (!selectedContext) {
      return;
    }

    setExportingSelectedChain(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetchSelectedChainBundle();
      const blob = await res.blob();
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = href;
      link.download = resolveDownloadFilename(
        res.headers.get("content-disposition"),
        `ontrackchain-evidence-chain-${selectedContext.reportId || selectedContext.requestId || selectedLog?.id || "selection"}.json`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(href);
      setNotice(
        tr("evidenceTrail.chain.exportSuccess" as MessageKey, {
          scopeId: selectedContext.reportId || selectedContext.requestId || selectedLog?.id || "selection"
        })
      );
    } catch (exportError) {
      setError(exportError instanceof Error ? exportError.message : tr("evidenceTrail.errorExport" as MessageKey));
    } finally {
      setExportingSelectedChain(false);
    }
  }

  async function onExportManualReviewPackage() {
    if (!selectedManualReview || !selectedManualPackageSummary || !selectedLog || !selectedContext || !selectedManualReviewAction) {
      return;
    }

    setExportingManualPackage(true);
    setError(null);
    setNotice(null);
    try {
      const workspaceRecord = selectedManualWorkspaceRecord;
      const manualReviewAction = selectedManualReviewAction;
      const payload = buildEvidenceManualPackagePayload({
        action: manualReviewAction,
        summary: selectedManualPackageSummary,
        evidenceRequest: {
          request_id: selectedContext.requestId || null,
          report_id: selectedContext.reportId || null,
          resource_type: selectedContext.caseId ? "case" : selectedLog.resource_type || null,
          resource_id: selectedContext.caseId || selectedLog.resource_id || null,
          limit: Number(filters.limit),
          include_audit_logs: true,
          include_credit_ledger: true,
          include_reports: true
        },
        scope: {
          request_id: selectedContext.requestId || null,
          report_id: selectedContext.reportId || null,
          address: selectedContext.address || null,
          chain: selectedContext.chain || null,
          resource_id: selectedLog.resource_id || null
        },
        manualReview: selectedManualReview,
        workspaceSummary: workspaceRecord ? buildWorkspaceSummary(workspaceRecord) : null
      });
      const res = await fetch("/api/app/evidence/manual-package", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as { error?: string } | null;
        throw new Error(data?.error ? resolveApiErrorMessage(t, data.error, tr("evidenceTrail.errorExport" as MessageKey)) : tr("evidenceTrail.errorExport" as MessageKey));
      }

      const blob = await res.blob();
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = href;
      link.download = resolveDownloadFilename(
        res.headers.get("content-disposition"),
        buildManualReviewPackageFilename(manualReviewAction, selectedManualPackageSummary.scopeId)
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(href);
      setNotice(tr("evidenceTrail.manualPackage.exportSuccess" as MessageKey, { scopeId: selectedManualPackageSummary.scopeId }));
    } catch (exportError) {
      setError(exportError instanceof Error ? exportError.message : tr("evidenceTrail.errorExport" as MessageKey));
    } finally {
      setExportingManualPackage(false);
    }
  }

  async function onCreateManualPackageSignoffRequest() {
    const packageSha256 = selectedManualPackageExportContext?.packageSha256?.trim() ?? "";
    if (!selectedManualPackageSummary || !selectedManualReviewAction || !packageSha256) {
      return;
    }

    setInitializingManualPackageSignoff(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch("/api/app/evidence/manual-package/signoff-requests", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          request_id: selectedContext?.requestId?.trim() || selectedManualPackageSummary.scopeId,
          report_id: selectedContext?.reportId?.trim() || null,
          scope_id: selectedManualPackageSummary.scopeId,
          manual_review_action: selectedManualReviewAction,
          package_sha256: packageSha256,
          manifest_schema_version: "manual_review_package/v2",
          classification: "restricted_regulatory",
          signoff_mode: MANUAL_PACKAGE_CANONICAL_SIGNOFF_MODE,
          package_kind: "manual_review_package",
          policy_version: "manual_package_sealing/v1"
        })
      });
      const data = (await res.json().catch(() => null)) as ManualPackageSeal | { error?: string; detail?: unknown } | null;
      if (!res.ok) {
        throw new Error(resolveApiErrorMessage(t, data, tr("evidenceTrail.manualPackage.seal.errorCreateRequest" as MessageKey)));
      }
      if (!data || !("seal_id" in data)) {
        throw new Error(tr("evidenceTrail.manualPackage.seal.errorCreateRequest" as MessageKey));
      }

      setManualPackageSeal(data);
      setManualPackageSealError(null);
      setNotice(tr("evidenceTrail.manualPackage.seal.requestCreated" as MessageKey, { sealId: data.seal_id }));
    } catch (signoffError) {
      setError(
        signoffError instanceof Error ? signoffError.message : tr("evidenceTrail.manualPackage.seal.errorCreateRequest" as MessageKey)
      );
    } finally {
      setInitializingManualPackageSignoff(false);
    }
  }

  async function onRecordManualPackageSignoff() {
    if (!manualPackageSeal?.seal_id) {
      return;
    }
    if (!manualPackageSignoffRole.trim()) {
      setError(tr("evidenceTrail.manualPackage.seal.roleRequired" as MessageKey));
      return;
    }

    setRecordingManualPackageSignoff(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch(`/api/app/evidence/manual-package/seals/${encodeURIComponent(manualPackageSeal.seal_id)}/signoffs`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          decision: manualPackageSignoffDecision,
          signer_role: manualPackageSignoffRole,
          signoff_method: manualPackageSignoffMethod,
          ticket_ref: manualPackageSignoffTicketRef.trim() || null,
          notes: manualPackageSignoffNotes.trim() || null,
          signer_display_name: manualPackageSignoffDisplayName.trim() || null,
          metadata: {
            source: "evidence_manual_package_ui"
          }
        })
      });
      const data = (await res.json().catch(() => null)) as ManualPackageSeal | { error?: string; detail?: unknown } | null;
      if (!res.ok) {
        throw new Error(resolveApiErrorMessage(t, data, tr("evidenceTrail.manualPackage.seal.errorRecordSignoff" as MessageKey)));
      }
      if (!data || !("seal_id" in data)) {
        throw new Error(tr("evidenceTrail.manualPackage.seal.errorRecordSignoff" as MessageKey));
      }

      setManualPackageSeal(data);
      setManualPackageSealError(null);
      setManualPackageSignoffTicketRef("");
      setManualPackageSignoffNotes("");
      setNotice(
        tr("evidenceTrail.manualPackage.seal.signoffRecorded" as MessageKey, {
          role: formatManualPackageSealRoleValue(manualPackageSignoffRole),
          decision: formatManualPackageSealDecisionValue(manualPackageSignoffDecision)
        })
      );
    } catch (signoffError) {
      setError(
        signoffError instanceof Error ? signoffError.message : tr("evidenceTrail.manualPackage.seal.errorRecordSignoff" as MessageKey)
      );
    } finally {
      setRecordingManualPackageSignoff(false);
    }
  }

  async function onFinalizeManualPackageSeal() {
    if (!manualPackageSeal?.seal_id) {
      return;
    }

    setFinalizingManualPackageSeal(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch(`/api/app/evidence/manual-package/seals/${encodeURIComponent(manualPackageSeal.seal_id)}/finalize`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          metadata: {
            source: "evidence_manual_package_ui",
            request_id: selectedContext?.requestId?.trim() || manualPackageSeal.request_id,
            report_id: selectedContext?.reportId?.trim() || manualPackageSeal.report_id || null,
            package_sha256: manualPackageSeal.package_sha256,
            manual_review_action: manualPackageSeal.manual_review_action
          }
        })
      });
      const data = (await res.json().catch(() => null)) as ManualPackageSeal | { error?: string; detail?: unknown } | null;
      if (!res.ok) {
        throw new Error(resolveApiErrorMessage(t, data, tr("evidenceTrail.manualPackage.seal.errorFinalize" as MessageKey)));
      }
      if (!data || !("seal_id" in data)) {
        throw new Error(tr("evidenceTrail.manualPackage.seal.errorFinalize" as MessageKey));
      }

      setManualPackageSeal(data);
      setManualPackageSealError(null);
      setNotice(
        tr("evidenceTrail.manualPackage.seal.finalized" as MessageKey, {
          sealId: data.seal_id
        })
      );
    } catch (finalizeError) {
      setError(finalizeError instanceof Error ? finalizeError.message : tr("evidenceTrail.manualPackage.seal.errorFinalize" as MessageKey));
    } finally {
      setFinalizingManualPackageSeal(false);
    }
  }

  async function onRevokeManualPackageSeal() {
    if (!manualPackageSeal?.seal_id) {
      return;
    }
    if (!manualPackageRevokeTicketRef.trim() || !manualPackageRevokeReason.trim()) {
      setError(tr("evidenceTrail.manualPackage.seal.revokeFieldsRequired" as MessageKey));
      return;
    }

    setRevokingManualPackageSeal(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch(`/api/app/evidence/manual-package/seals/${encodeURIComponent(manualPackageSeal.seal_id)}/revoke`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          ticket_ref: manualPackageRevokeTicketRef.trim(),
          reason: manualPackageRevokeReason.trim(),
          metadata: {
            source: "evidence_manual_package_ui"
          }
        })
      });
      const data = (await res.json().catch(() => null)) as ManualPackageSeal | { error?: string; detail?: unknown } | null;
      if (!res.ok) {
        throw new Error(resolveApiErrorMessage(t, data, tr("evidenceTrail.manualPackage.seal.errorRevoke" as MessageKey)));
      }
      if (!data || !("seal_id" in data)) {
        throw new Error(tr("evidenceTrail.manualPackage.seal.errorRevoke" as MessageKey));
      }

      setManualPackageSeal(data);
      setManualPackageSealError(null);
      setManualPackageRevokeTicketRef("");
      setManualPackageRevokeReason("");
      setNotice(tr("evidenceTrail.manualPackage.seal.revoked" as MessageKey, { sealId: data.seal_id }));
    } catch (revokeError) {
      setError(revokeError instanceof Error ? revokeError.message : tr("evidenceTrail.manualPackage.seal.errorRevoke" as MessageKey));
    } finally {
      setRevokingManualPackageSeal(false);
    }
  }

  async function onSupersedeManualPackageSeal() {
    if (!manualPackageSeal?.seal_id) {
      return;
    }
    if (!manualPackageSupersedeSealId.trim() || !manualPackageSupersedeTicketRef.trim() || !manualPackageSupersedeReason.trim()) {
      setError(tr("evidenceTrail.manualPackage.seal.supersedeFieldsRequired" as MessageKey));
      return;
    }

    setSupersedingManualPackageSeal(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch(
        `/api/app/evidence/manual-package/seals/${encodeURIComponent(manualPackageSeal.seal_id)}/supersede`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            superseded_by_seal_id: manualPackageSupersedeSealId.trim(),
            ticket_ref: manualPackageSupersedeTicketRef.trim(),
            reason: manualPackageSupersedeReason.trim(),
            metadata: {
              source: "evidence_manual_package_ui"
            }
          })
        }
      );
      const data = (await res.json().catch(() => null)) as ManualPackageSeal | { error?: string; detail?: unknown } | null;
      if (!res.ok) {
        throw new Error(resolveApiErrorMessage(t, data, tr("evidenceTrail.manualPackage.seal.errorSupersede" as MessageKey)));
      }
      if (!data || !("seal_id" in data)) {
        throw new Error(tr("evidenceTrail.manualPackage.seal.errorSupersede" as MessageKey));
      }

      setManualPackageSeal(data);
      setManualPackageSealError(null);
      setManualPackageSupersedeSealId("");
      setManualPackageSupersedeTicketRef("");
      setManualPackageSupersedeReason("");
      setNotice(
        tr("evidenceTrail.manualPackage.seal.superseded" as MessageKey, {
          sealId: data.seal_id,
          replacementSealId: String(data.superseded_by_seal_id ?? "")
        })
      );
    } catch (supersedeError) {
      setError(
        supersedeError instanceof Error
          ? supersedeError.message
          : tr("evidenceTrail.manualPackage.seal.errorSupersede" as MessageKey)
      );
    } finally {
      setSupersedingManualPackageSeal(false);
    }
  }

  async function onExportRosCoafRegulatoryDossier(rosId: string) {
    const normalizedRosId = rosId.trim();
    if (!normalizedRosId) {
      return;
    }

    setExportingRosCoafDossier(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch(`/api/app/reports/ros-coaf/${encodeURIComponent(normalizedRosId)}/regulatory-dossier`, { cache: "no-store" });
      const data = (await res.json().catch(() => null)) as { error?: string; detail?: unknown } | null;
      if (!res.ok) {
        setError(resolveApiErrorMessage(t, data, tr("evidenceTrail.details.exportRosDossierError" as MessageKey)));
        setExportingRosCoafDossier(false);
        return;
      }

      const dossierSha256 = res.headers.get("x-ontrack-dossier-sha256");
      const normalizedDossierSha256 = dossierSha256?.trim() ?? "";
      const resolvedFilename = resolveDownloadFilename(
        res.headers.get("content-disposition"),
        `ontrackchain-ros-coaf-regulatory-dossier-${normalizedRosId}.json`
      );
      setLastRosDossierExport(
        { rosId: normalizedRosId, sha256: normalizedDossierSha256, filename: resolvedFilename }
      );
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = href;
      link.download = resolveDownloadFilename(
        res.headers.get("content-disposition"),
        `ontrackchain-ros-coaf-regulatory-dossier-${normalizedRosId}.json`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(href);
      setNotice(
        tr("evidenceTrail.details.exportRosDossierSuccess" as MessageKey, {
          hash: summarizeDossierHash(res.headers.get("x-ontrack-dossier-sha256"))
        })
      );
    } catch {
      setError(tr("evidenceTrail.details.exportRosDossierError" as MessageKey));
    } finally {
      setExportingRosCoafDossier(false);
    }
  }

  function trackSelectedEvent() {
    if (!selectedLog || !selectedContext) {
      return;
    }
    void (async () => {
      const draftRecord: EvidenceWorkspaceRecord = {
        workItemId: selectedWorkspaceRecord?.workItemId,
        source: "local",
        eventId: selectedLog.id,
        action: selectedLog.action,
        resourceType: selectedLog.resource_type,
        resourceId: selectedLog.resource_id ?? "",
        caseId: selectedContext.caseId,
        requestId: selectedContext.requestId,
        reportId: selectedContext.reportId,
        fileHash: selectedContext.fileHash,
        owner,
        priority,
        localDeadline,
        workspaceStatus,
        note: workspaceNote,
        lastActionAt: new Date().toISOString()
      };
      setWorkspace((current: EvidenceWorkspaceRecord[]) => upsertWorkspaceRecord(current, draftRecord));
      setTimelineEventId(draftRecord.eventId);
      try {
        await syncWorkspaceRecord(draftRecord);
        setNotice(tr("evidenceTrail.workspace.noticeTrackedSynced" as MessageKey, { eventId: selectedLog.id }));
      } catch (syncError) {
        setNotice(tr("evidenceTrail.workspace.noticeTrackedLocalOnly" as MessageKey, { eventId: selectedLog.id }));
        setError(syncError instanceof Error ? syncError.message : tr("evidenceTrail.workspace.errorSync" as MessageKey));
      }
    })();
  }

  function hydrateWorkspaceRecord(record: EvidenceWorkspaceRecord) {
    const matchingLog = resolveLogForWorkspaceRecord(logs, record);
    if (matchingLog) {
      setSelectedLog(matchingLog);
    }
    setTimelineEventId(record.eventId);
    setOwner(record.owner);
    setPriority(record.priority);
    setLocalDeadline(record.localDeadline);
    setWorkspaceStatus(record.workspaceStatus);
    setWorkspaceNote(record.note);
    setNotice(tr("evidenceTrail.workspace.noticeLoaded" as MessageKey, { eventId: record.eventId }));
  }

  function openWorkspaceTimeline(record: EvidenceWorkspaceRecord) {
    hydrateWorkspaceRecord(record);
    setTimelineEventId(record.eventId);
  }

  async function syncWorkspaceRecord(record: EvidenceWorkspaceRecord, nextStatus?: WorkspaceStatus) {
    if (!record.eventId.trim()) {
      throw new Error(tr("evidenceTrail.workspace.errorSyncMissingEventId" as MessageKey));
    }

    const ownerUserId = resolveOwnerUserId({
      ownerLabel: record.owner,
      linkedUserId: authContext?.linked_user_id,
      isUuidLike
    });

    const localStatus = nextStatus ?? record.workspaceStatus;
    const queueStatus: WorkItemQueueStatus = localStatus === "sealed" ? "CLOSED" : "UNDER_REVIEW";
    const resourceId = resolveWorkItemResourceId(
      "evidence_event",
      record.eventId,
      record.caseId,
      record.requestId,
      record.reportId
    );
    const metadata: EvidenceWorkItemMetadata = withCanonicalWorkItemMetadata(
      {
        event_id: record.eventId,
        audit_action: record.action,
        audit_resource_type: record.resourceType,
        audit_resource_id: record.resourceId,
        ...(record.requestId ? { request_id: record.requestId } : {}),
        ...(record.reportId ? { report_id: record.reportId } : {}),
        ...(record.fileHash ? { file_hash_sha256: record.fileHash } : {})
      },
      {
        resourceType: "evidence_event",
        caseId: record.caseId,
        ownerLabel: record.owner,
        ownerUserId,
        workspaceStatus: localStatus,
        note: record.note
      }
    );
    const requestBody: CreateWorkItemRequest<EvidenceWorkItemMetadata> | PatchWorkItemRequest<EvidenceWorkItemMetadata> = record.workItemId
      ? {
          ...(ownerUserId ? { owner_user_id: ownerUserId } : {}),
          priority: record.priority,
          queue_status: queueStatus,
          due_at: toApiDueAt(record.localDeadline),
          title: `Evidence event • ${record.action || record.eventId}`,
          note: record.note || null,
          metadata
        }
      : {
          module: "evidence",
          resource_type: "evidence_event",
          resource_id: resourceId,
          ...(isWorkItemUuidLike(record.caseId) ? { case_id: record.caseId.trim() } : {}),
          ...(ownerUserId ? { owner_user_id: ownerUserId } : {}),
          priority: record.priority,
          queue_status: queueStatus,
          due_at: toApiDueAt(record.localDeadline),
          title: `Evidence event • ${record.action || record.eventId}`,
          note: record.note || null,
          metadata
        };

    setSyncingWorkspace(true);
    const res = await fetch(
      record.workItemId ? `/api/app/operations/work-items/${encodeURIComponent(record.workItemId)}` : "/api/app/operations/work-items",
      {
        method: record.workItemId ? "PATCH" : "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(requestBody),
        cache: "no-store"
      }
    );
    const data = (await res.json().catch(() => null)) as EvidenceWorkItemResponse | { error?: string; detail?: unknown } | null;
    setSyncingWorkspace(false);
    if (!res.ok) {
      throw new Error(resolveApiErrorMessage(t, data, tr("evidenceTrail.workspace.errorSync" as MessageKey)));
    }

    const nextRecord = mapWorkItemToWorkspaceRecord(data as EvidenceWorkItemResponse);
    setWorkspace((current: EvidenceWorkspaceRecord[]) => upsertWorkspaceRecord(current, nextRecord));
    if (timelineEventId === nextRecord.eventId && nextRecord.workItemId) {
      await loadTimeline(nextRecord.workItemId);
    }
    return nextRecord;
  }

  function updateWorkspaceStatus(eventId: string, nextStatus: WorkspaceStatus) {
    void (async () => {
      const currentRecord = workspace.find((entry: EvidenceWorkspaceRecord) => entry.eventId === eventId);
      if (!currentRecord) {
        return;
      }

      const draftRecord = { ...currentRecord, workspaceStatus: nextStatus, lastActionAt: new Date().toISOString() };
      setWorkspace((current: EvidenceWorkspaceRecord[]) =>
        upsertWorkspaceRecord(current, {
          eventId,
          workspaceStatus: nextStatus,
          lastActionAt: draftRecord.lastActionAt
        })
      );
      try {
        await syncWorkspaceRecord(draftRecord, nextStatus);
      } catch (syncError) {
        setError(syncError instanceof Error ? syncError.message : tr("evidenceTrail.workspace.errorSync" as MessageKey));
        setNotice(tr("evidenceTrail.workspace.noticeTrackedLocalOnly" as MessageKey, { eventId }));
      }
    })();
  }

  function removeWorkspaceRecord(eventId: string) {
    setWorkspace((current: EvidenceWorkspaceRecord[]) =>
      current.filter((entry: EvidenceWorkspaceRecord) => entry.eventId !== eventId)
    );
  }

  return (
    <AppShell
      title={tr("evidenceTrail.title" as MessageKey)}
      subtitle={tr("evidenceTrail.subtitle" as MessageKey)}
      activePath="/evidence"
      actions={<Pill>{tr("evidenceTrail.active" as MessageKey)}</Pill>}
    >
      <MetricGrid>
        <MetricCard label={tr("evidenceTrail.stats.loaded" as MessageKey)} value={loading ? "..." : count} meta={tr("evidenceTrail.stats.loadedMeta" as MessageKey)} />
        <MetricCard label={tr("evidenceTrail.stats.total" as MessageKey)} value={loading ? "..." : total} meta={tr("evidenceTrail.stats.totalMeta" as MessageKey)} />
        <MetricCard label={tr("evidenceTrail.stats.filters" as MessageKey)} value={activeFilterCount} meta={tr("evidenceTrail.stats.filtersMeta" as MessageKey)} accent />
        <MetricCard label={tr("evidenceTrail.stats.domain" as MessageKey)} value={tr(selectedDomain.label)} meta={tr("evidenceTrail.stats.domainMeta" as MessageKey)} />
      </MetricGrid>

      <Panel title={tr("evidenceTrail.presets.title" as MessageKey)} description={tr("evidenceTrail.presets.description" as MessageKey)}>
        <div className="otc-grid otc-grid--counterparty-form">
          {DOMAIN_PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              className="otc-button otc-button--ghost otc-button--stack-start otc-evidence-preset"
              onClick={() => applyDomainPreset(preset.id)}
            >
              <span>
                <strong>{tr(preset.label)}</strong>
                <span className="otc-muted otc-evidence-preset__description">{tr(preset.description)}</span>
              </span>
            </button>
          ))}
        </div>
      </Panel>

      <Panel title={tr("evidenceTrail.filters.title" as MessageKey)} description={tr("evidenceTrail.filters.description" as MessageKey)}>
        <div className="otc-grid otc-grid--counterparty-form">
          <label className="otc-field">
            {tr("evidenceTrail.filters.action" as MessageKey)}
            <select
              className="otc-select"
              data-testid="evidence-filter-action"
              value={filters.action}
              onChange={(event) => updateFilter("action", event.target.value)}
            >
              <option value="">{tr("evidenceTrail.filters.all" as MessageKey)}</option>
              {EVIDENCE_ACTION_VALUES.filter((value) => value !== "evidence_bundle_exported").map((value) => (
                <option key={value} value={value}>
                  {formatEvidenceActionValue(value)}
                </option>
              ))}
            </select>
          </label>
          <label className="otc-field">
            {tr("evidenceTrail.filters.resourceType" as MessageKey)}
            <select
              className="otc-select"
              data-testid="evidence-filter-resource-type"
              value={filters.resourceType}
              onChange={(event) => updateFilter("resourceType", event.target.value)}
            >
              <option value="">{tr("evidenceTrail.filters.all" as MessageKey)}</option>
              {EVIDENCE_RESOURCE_TYPE_VALUES.map((value) => (
                <option key={value} value={value}>
                  {formatEvidenceResourceTypeValue(value)}
                </option>
              ))}
            </select>
          </label>
          <label className="otc-field">
            {tr("evidenceTrail.filters.requestId" as MessageKey)}
            <input className="otc-input" value={filters.requestId} onChange={(event) => updateFilter("requestId", event.target.value)} />
          </label>
          <label className="otc-field">
            {tr("evidenceTrail.filters.reportId" as MessageKey)}
            <input className="otc-input" value={filters.reportId} onChange={(event) => updateFilter("reportId", event.target.value)} />
          </label>
          <label className="otc-field">
            {tr("evidenceTrail.filters.resourceId" as MessageKey)}
            <input className="otc-input" value={filters.resourceId} onChange={(event) => updateFilter("resourceId", event.target.value)} />
          </label>
          <label className="otc-field">
            {tr("evidenceTrail.filters.limit" as MessageKey)}
            <select className="otc-select" value={filters.limit} onChange={(event) => updateFilter("limit", event.target.value)}>
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="200">200</option>
            </select>
          </label>
        </div>
        <div className="otc-controls otc-controls--spaced">
          <button type="button" className="otc-button otc-button--accent" onClick={() => void fetchLogs(filters, 1)}>
            {tr("evidenceTrail.actions.search" as MessageKey)}
          </button>
          <button type="button" className="otc-button otc-button--ghost" onClick={() => void onReset()}>
            {tr("evidenceTrail.actions.reset" as MessageKey)}
          </button>
          <button type="button" className="otc-button otc-button--ghost" onClick={() => void onExportEvidence()} disabled={exporting}>
            {exporting ? tr("evidenceTrail.actions.exportLoading" as MessageKey) : tr("evidenceTrail.actions.export" as MessageKey)}
          </button>
          <span className="otc-muted">
            {tr("evidenceTrail.summary" as MessageKey, { total })}
          </span>
        </div>
      </Panel>

      {error ? <Message tone="error">{error}</Message> : null}
      {notice ? <Message tone="success">{notice}</Message> : null}
      {auditManualReturnContext ? (
        <Message>
          <div className="otc-stack otc-controls--spaced" data-testid="evidence-audit-return-banner">
            <strong>{tr("evidenceTrail.auditReturn.title" as MessageKey)}</strong>
            <span>
              {tr("evidenceTrail.auditReturn.description" as MessageKey, {
                requestId: auditManualReturnContext.requestId,
                action: auditManualReturnContext.actionLabel,
                domain: auditManualReturnContext.domainLabel
              })}
            </span>
            {auditManualReturnContext.auditHref ? (
              <div className="otc-controls">
                <a
                  className="otc-button otc-button--ghost"
                  href={auditManualReturnContext.auditHref}
                  data-testid="evidence-audit-return-open-audit"
                >
                  {tr("evidenceTrail.auditReturn.openAudit" as MessageKey)}
                </a>
              </div>
            ) : null}
          </div>
        </Message>
      ) : null}

      <Panel title={tr("evidenceTrail.workspace.title" as MessageKey)} description={tr("evidenceTrail.workspace.description" as MessageKey)}>
        {localWorkspaceCount > 0 && serverWorkspaceCount === 0 ? (
          <Message>{tr("evidenceTrail.workspace.mode.localOnly" as MessageKey, { count: localWorkspaceCount })}</Message>
        ) : null}
        {hasMixedWorkspaceSources ? (
          <Message>
            {tr("evidenceTrail.workspace.mode.mixed" as MessageKey, {
              server: serverWorkspaceCount,
              local: localWorkspaceCount
            })}
          </Message>
        ) : null}
        <div className="otc-grid otc-grid--counterparty-form">
          <label className="otc-field">
            {tr("evidenceTrail.workspace.filters.owner" as MessageKey)}
            <input className="otc-input" value={owner} onChange={(event) => setOwner(event.target.value)} />
          </label>
          <label className="otc-field">
            {tr("evidenceTrail.workspace.filters.priority" as MessageKey)}
            <select className="otc-select" value={priority} onChange={(event) => setPriority(event.target.value as WorkspacePriority)}>
              <option value="critical">{t("common.priority.critical")}</option>
              <option value="high">{t("common.priority.high")}</option>
              <option value="normal">{t("common.priority.normal")}</option>
            </select>
          </label>
          <label className="otc-field">
            {tr("evidenceTrail.workspace.filters.deadline" as MessageKey)}
            <input className="otc-input" type="datetime-local" value={localDeadline} onChange={(event) => setLocalDeadline(event.target.value)} />
          </label>
          <label className="otc-field">
            {tr("evidenceTrail.workspace.filters.status" as MessageKey)}
            <select className="otc-select" value={workspaceStatus} onChange={(event) => setWorkspaceStatus(event.target.value as WorkspaceStatus)}>
              <option value="queued">{tr("evidenceTrail.workspace.status.queued" as MessageKey)}</option>
              <option value="reviewing">{tr("evidenceTrail.workspace.status.reviewing" as MessageKey)}</option>
              <option value="sealed">{tr("evidenceTrail.workspace.status.sealed" as MessageKey)}</option>
            </select>
          </label>
          <label className="otc-field">
            {tr("evidenceTrail.workspace.filters.note" as MessageKey)}
            <input className="otc-input" value={workspaceNote} onChange={(event) => setWorkspaceNote(event.target.value)} />
          </label>
          <div className="otc-controls otc-controls--spaced">
            <button type="button" className="otc-button" onClick={trackSelectedEvent} disabled={!selectedLog || syncingWorkspace}>
              {tr("evidenceTrail.workspace.actions.trackSelected" as MessageKey)}
            </button>
          </div>
        </div>
        {workspace.length ? (
          <table className="otc-table otc-table--spaced">
            <thead>
              <tr>
                <th>{tr("evidenceTrail.workspace.table.eventId" as MessageKey)}</th>
                <th>{tr("evidenceTrail.workspace.table.resource" as MessageKey)}</th>
                <th>{tr("evidenceTrail.workspace.table.owner" as MessageKey)}</th>
                <th>{tr("evidenceTrail.workspace.table.priority" as MessageKey)}</th>
                <th>{tr("evidenceTrail.workspace.table.deadline" as MessageKey)}</th>
                <th>{tr("evidenceTrail.workspace.table.status" as MessageKey)}</th>
                <th>{tr("evidenceTrail.workspace.sourceLabel" as MessageKey)}</th>
                <th>{tr("evidenceTrail.workspace.table.actions" as MessageKey)}</th>
              </tr>
            </thead>
            <tbody>
              {workspace.map((record) => (
                <tr key={record.eventId}>
                  <td>
                    <strong>{record.eventId}</strong>
                    <div className="otc-muted">{formatEvidenceActionValue(record.action)}</div>
                    {record.note ? <div className="otc-muted">{record.note}</div> : null}
                  </td>
                  <td>{formatEvidenceResourceTypeValue(record.resourceType)}{record.resourceId ? ` • ${record.resourceId}` : ""}</td>
                  <td>{record.owner || tr("evidenceTrail.notAvailable" as MessageKey)}</td>
                  <td>{t(`common.priority.${record.priority}` as MessageKey)}</td>
                  <td>
                    {formatOptionalDateValue(record.localDeadline)}
                    <div className="otc-muted">{tr(`evidenceTrail.workspace.urgency.${getWorkspaceUrgency(record)}` as MessageKey)}</div>
                  </td>
                  <td>{tr(`evidenceTrail.workspace.status.${record.workspaceStatus}` as MessageKey)}</td>
                  <td>
                    <Pill tone={toneForWorkspaceSource(record.source)}>{tr(`evidenceTrail.workspace.source.${record.source}` as MessageKey)}</Pill>
                  </td>
                  <td>
                    <div className="otc-controls">
                      <button type="button" className="otc-button otc-button--ghost" onClick={() => hydrateWorkspaceRecord(record)}>
                        {tr("evidenceTrail.workspace.table.load" as MessageKey)}
                      </button>
                      <button type="button" className="otc-button otc-button--ghost" onClick={() => openWorkspaceTimeline(record)}>
                        {tr("evidenceTrail.workspace.timeline.open" as MessageKey)}
                      </button>
                      <button type="button" className="otc-button otc-button--ghost" onClick={() => updateWorkspaceStatus(record.eventId, "queued")}>
                        {tr("evidenceTrail.workspace.table.markQueued" as MessageKey)}
                      </button>
                      <button type="button" className="otc-button otc-button--ghost" onClick={() => updateWorkspaceStatus(record.eventId, "reviewing")}>
                        {tr("evidenceTrail.workspace.table.markReviewing" as MessageKey)}
                      </button>
                      <button type="button" className="otc-button otc-button--ghost" onClick={() => updateWorkspaceStatus(record.eventId, "sealed")}>
                        {tr("evidenceTrail.workspace.table.markSealed" as MessageKey)}
                      </button>
                      {record.source === "local" ? (
                        <button type="button" className="otc-button otc-button--ghost" onClick={() => removeWorkspaceRecord(record.eventId)}>
                          {tr("evidenceTrail.workspace.table.remove" as MessageKey)}
                        </button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <Message>{tr("evidenceTrail.workspace.empty" as MessageKey)}</Message>
        )}
      </Panel>

      <WorkItemTimelinePanel
        state={!selectedTimelineRecord ? "empty_selection" : !selectedTimelineRecord.workItemId ? "local_only" : "ready"}
        summary={selectedTimelineRecord ? tr("evidenceTrail.workspace.timeline.summary" as MessageKey, { eventId: selectedTimelineRecord.eventId }) : null}
        contextBadges={timelineContextBadges}
        localOnlyHint={selectedTimelineRecord ? tr("evidenceTrail.workspace.timeline.localHint" as MessageKey) : null}
        labels={buildWorkItemTimelineLabels(tr, "evidenceTrail.workspace.timeline")}
        timelineError={timelineError}
        timelineData={timelineData}
        timelineLoading={timelineLoading}
        commentType={commentType}
        commentBody={commentBody}
        commentSubmitting={commentSubmitting}
        onCommentTypeChange={setCommentType}
        onCommentBodyChange={setCommentBody}
        onCommentSubmit={() => {
          void submitTimelineComment(selectedTimelineRecord?.workItemId);
        }}
        onRefresh={
          selectedTimelineRecord?.workItemId
            ? () => {
                void loadTimeline(selectedTimelineRecord.workItemId!);
              }
            : undefined
        }
        formatDate={formatDateValue}
        formatEventLabel={formatTimelineEvent}
      />

      <section className="otc-grid otc-evidence-layout">
        <Panel title={tr("evidenceTrail.events.title" as MessageKey)} description={tr("evidenceTrail.events.description" as MessageKey)}>
          <div className="otc-controls">
            <button type="button" className="otc-button otc-button--ghost" onClick={() => void fetchLogs(filters, Math.max(1, currentPage - 1))} disabled={loading || currentPage <= 1}>
              {tr("evidenceTrail.pagination.previous" as MessageKey)}
            </button>
            <button type="button" className="otc-button otc-button--ghost" onClick={() => void fetchLogs(filters, currentPage + 1)} disabled={loading || !hasMore}>
              {tr("evidenceTrail.pagination.next" as MessageKey)}
            </button>
            <span className="otc-muted">{tr("evidenceTrail.pagination.summary" as MessageKey, { page: currentPage, total })}</span>
          </div>
          {logs.length ? (
            <div className="otc-stack otc-controls--spaced">
              {logs.map((entry) => {
                const isSelected = entry.id === selectedLog?.id;
                return (
                  <button
                    key={entry.id}
                    type="button"
                    className={`otc-button otc-button--ghost otc-button--stack-start otc-evidence-log${isSelected ? " otc-evidence-log--selected" : ""}`}
                    onClick={() => setSelectedLog(entry)}
                  >
                    <span>
                      <strong>{formatEvidenceActionValue(entry.action)}</strong>
                      <span className="otc-muted otc-evidence-log__meta">
                        {formatEvidenceResourceTypeValue(entry.resource_type)}{entry.resource_id ? ` • ${entry.resource_id}` : ""}
                      </span>
                      <span className="otc-muted otc-evidence-log__meta otc-evidence-log__meta--tight">
                        request_id: {entry.request_id ?? tr("evidenceTrail.notAvailable" as MessageKey)}
                      </span>
                      <span
                        className="otc-muted otc-evidence-log__meta otc-evidence-log__meta--tight"
                        data-testid={`evidence-log-timestamp-${entry.id}`}
                      >
                        {formatDateValue(entry.created_at)}
                      </span>
                    </span>
                    <span className="otc-controls" data-testid="evidence-log-row">
                      <span className="otc-link-button">{tr("evidenceTrail.events.select" as MessageKey)}</span>
                    </span>
                  </button>
                );
              })}
            </div>
          ) : (
            <Message>{tr("evidenceTrail.events.empty" as MessageKey)}</Message>
          )}
        </Panel>

        <Panel title={tr("evidenceTrail.details.title" as MessageKey)} description={tr("evidenceTrail.details.description" as MessageKey)}>
          {selectedLog ? (
            <div className="otc-stack" data-testid="evidence-details-panel">
              <div className="otc-kv">
                <div className="otc-kv__row">
                  <span className="otc-kv__key">{tr("evidenceTrail.details.action" as MessageKey)}</span>
                  <span className="otc-kv__value">{formatEvidenceActionValue(selectedLog.action)}</span>
                </div>
                <div className="otc-kv__row">
                  <span className="otc-kv__key">{tr("evidenceTrail.details.resource" as MessageKey)}</span>
                  <span className="otc-kv__value">
                    {formatEvidenceResourceTypeValue(selectedLog.resource_type)}
                    {selectedLog.resource_id ? ` • ${selectedLog.resource_id}` : ""}
                  </span>
                </div>
                <div className="otc-kv__row">
                  <span className="otc-kv__key">{tr("evidenceTrail.details.requestId" as MessageKey)}</span>
                  <span className="otc-kv__value">{selectedLog.request_id ?? tr("evidenceTrail.notAvailable" as MessageKey)}</span>
                </div>
                <div className="otc-kv__row">
                  <span className="otc-kv__key">{tr("evidenceTrail.details.reportId" as MessageKey)}</span>
                  <span className="otc-kv__value">{selectedLog.report_id ?? tr("evidenceTrail.notAvailable" as MessageKey)}</span>
                </div>
                <div className="otc-kv__row">
                  <span className="otc-kv__key">{tr("evidenceTrail.details.fileHash" as MessageKey)}</span>
                  <span className="otc-kv__value">{selectedLog.file_hash_sha256 ?? tr("evidenceTrail.notAvailable" as MessageKey)}</span>
                </div>
                <div className="otc-kv__row">
                  <span className="otc-kv__key">{tr("evidenceTrail.details.caseId" as MessageKey)}</span>
                  <span className="otc-kv__value">{selectedContext?.caseId || tr("evidenceTrail.notAvailable" as MessageKey)}</span>
                </div>
                <div className="otc-kv__row">
                  <span className="otc-kv__key">{tr("evidenceTrail.details.addressChain" as MessageKey)}</span>
                  <span className="otc-kv__value">
                    {selectedContext?.address ? `${selectedContext.address} • ${selectedContext.chain}` : tr("evidenceTrail.notAvailable" as MessageKey)}
                  </span>
                </div>
                <div className="otc-kv__row">
                  <span className="otc-kv__key">{tr("evidenceTrail.details.counterpartyId" as MessageKey)}</span>
                  <span className="otc-kv__value">{selectedContext?.counterpartyId || tr("evidenceTrail.notAvailable" as MessageKey)}</span>
                </div>
                <div className="otc-kv__row">
                  <span className="otc-kv__key">{tr("evidenceTrail.details.rosId" as MessageKey)}</span>
                  <span className="otc-kv__value">{selectedContext?.rosId || tr("evidenceTrail.notAvailable" as MessageKey)}</span>
                </div>
              </div>
              {selectedHashContext ? renderHashContextDetail(selectedHashContext) : null}
              {selectedDossierContext
                ? renderDossierContext(selectedDossierContext, {
                    container: "evidence-dossier-detail-context",
                    openReport: "evidence-dossier-detail-open-report",
                    openRosCoaf: "evidence-dossier-detail-open-roscoaf"
                  })
                : null}
              {selectedManualReview ? (
                <div className="otc-kv" data-testid="evidence-manual-review-panel">
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualReview.title" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      <Pill>{formatTranslatedCodeValue(selectedManualReview.deliveryMode, MANUAL_REVIEW_VALUE_LABEL_KEYS)}</Pill>
                    </span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualReview.provider" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      {formatTranslatedCodeValue(selectedManualReview.provider, MANUAL_REVIEW_VALUE_LABEL_KEYS)} •{" "}
                      {formatTranslatedCodeValue(selectedManualReview.providerStatus, MANUAL_REVIEW_VALUE_LABEL_KEYS)}
                    </span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualReview.capability" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      {formatTranslatedCodeValue(selectedManualReview.capabilityStatus, MANUAL_REVIEW_VALUE_LABEL_KEYS)} •{" "}
                      {formatTranslatedCodeValue(selectedManualReview.degradedReason, MANUAL_REVIEW_VALUE_LABEL_KEYS)}
                    </span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualReview.humanReview" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      {selectedManualReview.requiresHumanReview ? tr("common.yes" as MessageKey) : tr("common.no" as MessageKey)}
                    </span>
                  </div>
                  {selectedManualReview.counterpartyContext ? (
                    <div className="otc-kv__row">
                      <span className="otc-kv__key">{tr("evidenceTrail.manualReview.counterpartyContext" as MessageKey)}</span>
                      <span className="otc-kv__value">{selectedManualReview.counterpartyContext}</span>
                    </div>
                  ) : null}
                  {selectedManualReview.purpose ? (
                    <div className="otc-kv__row">
                      <span className="otc-kv__key">{tr("evidenceTrail.manualReview.purpose" as MessageKey)}</span>
                      <span className="otc-kv__value">{selectedManualReview.purpose}</span>
                    </div>
                  ) : null}
                  {selectedManualReview.amount !== null ? (
                    <div className="otc-kv__row">
                      <span className="otc-kv__key">{tr("evidenceTrail.manualReview.amount" as MessageKey)}</span>
                      <span className="otc-kv__value">{selectedManualReview.amount}</span>
                    </div>
                  ) : null}
                </div>
              ) : null}
              {selectedManualPackageSummary ? (
                <div className="otc-kv" data-testid="evidence-manual-package-panel">
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.title" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      <Pill tone="warning">
                        {formatTranslatedCodeValue(selectedManualPackageSummary.packageType, MANUAL_PACKAGE_VALUE_LABEL_KEYS)}
                      </Pill>
                    </span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.sensitivity" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      {formatTranslatedCodeValue(selectedManualPackageSummary.sensitivity, MANUAL_PACKAGE_VALUE_LABEL_KEYS)}
                    </span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.workflow" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      {formatTranslatedCodeValue(selectedManualPackageSummary.workflow, MANUAL_PACKAGE_VALUE_LABEL_KEYS)}
                    </span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.accessPolicy" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      {formatTranslatedCodeValue(selectedManualPackageSummary.accessPolicy, MANUAL_PACKAGE_VALUE_LABEL_KEYS)}
                    </span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.signoff" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      {formatTranslatedCodeValue(selectedManualPackageSummary.signoffMode, MANUAL_PACKAGE_VALUE_LABEL_KEYS)}
                    </span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.reviewMode" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      {formatTranslatedCodeValue(selectedManualPackageSummary.reviewMode, MANUAL_PACKAGE_VALUE_LABEL_KEYS)}
                    </span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.custody" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      {formatTranslatedCodeValue(selectedManualPackageSummary.custodyState, MANUAL_PACKAGE_VALUE_LABEL_KEYS)}
                    </span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.anchor" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      {formatTranslatedCodeValue(selectedManualPackageSummary.anchoringStatus, MANUAL_PACKAGE_VALUE_LABEL_KEYS)}
                    </span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.scope" as MessageKey)}</span>
                    <span className="otc-kv__value">{selectedManualPackageSummary.scopeId}</span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.dossierFields" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      {formatTranslatedCodeList(selectedManualPackageSummary.dossierFields, MANUAL_PACKAGE_FIELD_LABEL_KEYS, ", ")}
                    </span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.checklist" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      {formatTranslatedCodeList(selectedManualPackageSummary.checklist, MANUAL_PACKAGE_CHECKLIST_LABEL_KEYS, " • ")}
                    </span>
                  </div>
                  <div className="otc-kv__row" data-testid="evidence-manual-package-export-hash">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.seal.lookupHash" as MessageKey)}</span>
                    <span className="otc-kv__value otc-mono">
                      {selectedManualPackageExportContext?.packageSha256 || tr("evidenceTrail.manualPackage.seal.statusNotMaterialized" as MessageKey)}
                    </span>
                  </div>
                  <div className="otc-kv__row" data-testid="evidence-manual-package-export-filename">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.seal.lastExportFilename" as MessageKey)}</span>
                    <span className="otc-kv__value otc-mono">
                      {selectedManualPackageExportContext?.filename || tr("evidenceTrail.notAvailable" as MessageKey)}
                    </span>
                  </div>
                  <div className="otc-kv__row" data-testid="evidence-manual-package-export-created-at">
                    <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.seal.lastExportAt" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      {formatOptionalDateValue(selectedManualPackageExportContext?.createdAt)}
                    </span>
                  </div>
                  <div className="otc-kv" data-testid="evidence-manual-package-seal-panel">
                    <div className="otc-kv__row">
                      <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.seal.title" as MessageKey)}</span>
                      <span className="otc-kv__value">
                        {manualPackageSeal ? (
                          <Pill tone={toneForManualPackageSealStatus(manualPackageSeal.seal_status)}>
                            {formatManualPackageSealStatusValue(manualPackageSeal.seal_status)}
                          </Pill>
                        ) : manualPackageSealLoading ? (
                          tr("evidenceTrail.manualPackage.seal.statusLoading" as MessageKey)
                        ) : !selectedManualPackageExportContext?.packageSha256 ? (
                          tr("evidenceTrail.manualPackage.seal.statusNotMaterialized" as MessageKey)
                        ) : !canReadManualPackageSeal(authContext?.role) ? (
                          tr("evidenceTrail.manualPackage.seal.accessRestricted" as MessageKey)
                        ) : manualPackageSealError ? (
                          manualPackageSealError
                        ) : (
                          tr("evidenceTrail.manualPackage.seal.statusUnavailable" as MessageKey)
                        )}
                      </span>
                    </div>
                    <div className="otc-kv__row">
                      <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.seal.signoffProgress" as MessageKey)}</span>
                      <span className="otc-kv__value">
                        {manualPackageSeal
                          ? `${manualPackageSeal.approved_required_signoffs}/${manualPackageSeal.required_signoffs}`
                          : tr("evidenceTrail.notAvailable" as MessageKey)}
                      </span>
                    </div>
                    <div className="otc-kv__row">
                      <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.seal.signers" as MessageKey)}</span>
                      <span className="otc-kv__value">
                        {manualPackageSeal?.signoffs.length
                          ? manualPackageSeal.signoffs
                              .map((signoff) =>
                                [
                                  signoff.signer_display_name,
                                  formatManualPackageSealRoleValue(signoff.signer_role),
                                  formatManualPackageSealDecisionValue(signoff.decision)
                                ].join(" • ")
                              )
                              .join(" | ")
                          : tr("evidenceTrail.notAvailable" as MessageKey)}
                      </span>
                    </div>
                    <div className="otc-kv__row">
                      <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.seal.sealId" as MessageKey)}</span>
                      <span className="otc-kv__value otc-mono">
                        {manualPackageSeal?.seal_id || tr("evidenceTrail.notAvailable" as MessageKey)}
                      </span>
                    </div>
                    <div className="otc-kv__row">
                      <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.seal.signatureAlgorithm" as MessageKey)}</span>
                      <span className="otc-kv__value">
                        {manualPackageSeal?.signature_algorithm || tr("evidenceTrail.notAvailable" as MessageKey)}
                      </span>
                    </div>
                    <div className="otc-kv__row">
                      <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.seal.trustBundle" as MessageKey)}</span>
                      <span className="otc-kv__value otc-mono">
                        {manualPackageSeal?.certificate_bundle_ref || tr("evidenceTrail.notAvailable" as MessageKey)}
                      </span>
                    </div>
                    <div className="otc-kv__row">
                      <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.seal.sealedAt" as MessageKey)}</span>
                      <span className="otc-kv__value">{formatOptionalDateValue(manualPackageSeal?.sealed_at)}</span>
                    </div>
                    <div className="otc-kv__row">
                      <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.seal.verification" as MessageKey)}</span>
                      <span className="otc-kv__value">
                        {typeof manualPackageSeal?.verification_summary?.verified === "boolean"
                          ? manualPackageSeal.verification_summary.verified
                            ? tr("common.yes" as MessageKey)
                            : tr("common.no" as MessageKey)
                          : tr("evidenceTrail.notAvailable" as MessageKey)}
                      </span>
                    </div>
                    <div className="otc-kv__row">
                      <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.seal.verificationMethod" as MessageKey)}</span>
                      <span className="otc-kv__value">
                        {readWorkItemMetadataString(manualPackageSeal?.verification_summary ?? {}, "verification_method") ||
                          tr("evidenceTrail.notAvailable" as MessageKey)}
                      </span>
                    </div>
                    <div className="otc-kv__row">
                      <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.seal.issuer" as MessageKey)}</span>
                      <span className="otc-kv__value">
                        {readWorkItemMetadataString(manualPackageSeal?.verification_summary ?? {}, "issuer") ||
                          tr("evidenceTrail.notAvailable" as MessageKey)}
                      </span>
                    </div>
                    <div className="otc-kv__row">
                      <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.seal.keyId" as MessageKey)}</span>
                      <span className="otc-kv__value otc-mono">
                        {readWorkItemMetadataString(manualPackageSeal?.verification_summary ?? {}, "key_id") ||
                          tr("evidenceTrail.notAvailable" as MessageKey)}
                      </span>
                    </div>
                    <div className="otc-kv__row">
                      <span className="otc-kv__key">{tr("evidenceTrail.manualPackage.seal.pendingRoles" as MessageKey)}</span>
                      <span className="otc-kv__value">
                        {pendingManualPackageSignerRoles.length
                          ? pendingManualPackageSignerRoles.map((role) => formatManualPackageSealRoleValue(role)).join(" • ")
                          : tr("evidenceTrail.manualPackage.seal.noPendingRequiredRoles" as MessageKey)}
                      </span>
                    </div>
                    {canManageManualPackageSealState && selectedManualPackageExportContext?.packageSha256 && !manualPackageSeal ? (
                      <div className="otc-stack otc-controls--spaced" data-testid="evidence-manual-package-signoff-init-panel">
                        <div className="otc-muted">{tr("evidenceTrail.manualPackage.seal.writeHint" as MessageKey)}</div>
                        <div className="otc-controls">
                          <button
                            type="button"
                            className="otc-button"
                            onClick={() => void onCreateManualPackageSignoffRequest()}
                            disabled={initializingManualPackageSignoff || manualPackageSealLoading}
                            data-testid="evidence-manual-package-init-signoff-request"
                          >
                            {initializingManualPackageSignoff
                              ? tr("evidenceTrail.manualPackage.seal.actions.initRequestLoading" as MessageKey)
                              : tr("evidenceTrail.manualPackage.seal.actions.initRequest" as MessageKey)}
                          </button>
                        </div>
                      </div>
                    ) : null}
                    {availableManualPackageSignerRoles.length > 0 &&
                    manualPackageSeal &&
                    !["sealed", "revoked", "superseded"].includes(manualPackageSeal.seal_status) &&
                    pendingManualPackageSignerRoles.length ? (
                      <div className="otc-stack otc-controls--spaced" data-testid="evidence-manual-package-signoff-form">
                        <strong>{tr("evidenceTrail.manualPackage.seal.formTitle" as MessageKey)}</strong>
                        <div className="otc-grid otc-grid--counterparty-form">
                          <label className="otc-field">
                            {tr("evidenceTrail.manualPackage.seal.role" as MessageKey)}
                            <select
                              className="otc-select"
                              value={manualPackageSignoffRole}
                              onChange={(event) => setManualPackageSignoffRole(event.target.value)}
                              data-testid="evidence-manual-package-signoff-role"
                            >
                              {availableManualPackageSignerRoles.map((role) => (
                                <option key={role} value={role}>
                                  {formatManualPackageSealRoleValue(role)}
                                </option>
                              ))}
                            </select>
                          </label>
                          <label className="otc-field">
                            {tr("evidenceTrail.manualPackage.seal.decision" as MessageKey)}
                            <select
                              className="otc-select"
                              value={manualPackageSignoffDecision}
                              onChange={(event) => setManualPackageSignoffDecision(event.target.value)}
                              data-testid="evidence-manual-package-signoff-decision"
                            >
                              <option value="approved">{formatManualPackageSealDecisionValue("approved")}</option>
                              <option value="rejected">{formatManualPackageSealDecisionValue("rejected")}</option>
                            </select>
                          </label>
                          <label className="otc-field">
                            {tr("evidenceTrail.manualPackage.seal.method" as MessageKey)}
                            <select
                              className="otc-select"
                              value={manualPackageSignoffMethod}
                              onChange={(event) => setManualPackageSignoffMethod(event.target.value)}
                              data-testid="evidence-manual-package-signoff-method"
                            >
                              <option value="platform_authenticated_2fa">
                                {formatManualPackageSealMethodValue("platform_authenticated_2fa")}
                              </option>
                              <option value="governance_ticket">{formatManualPackageSealMethodValue("governance_ticket")}</option>
                            </select>
                          </label>
                          <label className="otc-field">
                            {tr("evidenceTrail.manualPackage.seal.displayName" as MessageKey)}
                            <input
                              className="otc-input"
                              value={manualPackageSignoffDisplayName}
                              onChange={(event) => setManualPackageSignoffDisplayName(event.target.value)}
                              data-testid="evidence-manual-package-signoff-display-name"
                            />
                          </label>
                          <label className="otc-field">
                            {tr("evidenceTrail.manualPackage.seal.ticketRef" as MessageKey)}
                            <input
                              className="otc-input"
                              value={manualPackageSignoffTicketRef}
                              onChange={(event) => setManualPackageSignoffTicketRef(event.target.value)}
                              data-testid="evidence-manual-package-signoff-ticket-ref"
                            />
                          </label>
                          <label className="otc-field">
                            {tr("evidenceTrail.manualPackage.seal.notes" as MessageKey)}
                            <input
                              className="otc-input"
                              value={manualPackageSignoffNotes}
                              onChange={(event) => setManualPackageSignoffNotes(event.target.value)}
                              data-testid="evidence-manual-package-signoff-notes"
                            />
                          </label>
                        </div>
                        <div className="otc-controls">
                          <button
                            type="button"
                            className="otc-button"
                            onClick={() => void onRecordManualPackageSignoff()}
                            disabled={recordingManualPackageSignoff}
                            data-testid="evidence-manual-package-record-signoff"
                          >
                            {recordingManualPackageSignoff
                              ? tr("evidenceTrail.manualPackage.seal.actions.recordSignoffLoading" as MessageKey)
                              : tr("evidenceTrail.manualPackage.seal.actions.recordSignoff" as MessageKey)}
                          </button>
                        </div>
                      </div>
                    ) : null}
                    {canManageManualPackageSealState &&
                    manualPackageSeal &&
                    manualPackageSeal.seal_status === "ready_to_seal" &&
                    !pendingManualPackageSignerRoles.length ? (
                      <div className="otc-stack otc-controls--spaced" data-testid="evidence-manual-package-ready-to-seal">
                        <div className="otc-muted">{tr("evidenceTrail.manualPackage.seal.readyToSealNotice" as MessageKey)}</div>
                        <div className="otc-controls">
                          <button
                            type="button"
                            className="otc-button"
                            onClick={() => void onFinalizeManualPackageSeal()}
                            disabled={finalizingManualPackageSeal}
                            data-testid="evidence-manual-package-finalize"
                          >
                            {finalizingManualPackageSeal
                              ? tr("evidenceTrail.manualPackage.seal.actions.finalizeLoading" as MessageKey)
                              : tr("evidenceTrail.manualPackage.seal.actions.finalize" as MessageKey)}
                          </button>
                        </div>
                      </div>
                    ) : null}
                    {manualPackageSeal?.seal_status === "sealed" ? (
                      <div className="otc-muted" data-testid="evidence-manual-package-sealed-notice">
                        {tr("evidenceTrail.manualPackage.seal.sealedNotice" as MessageKey)}
                      </div>
                    ) : null}
                    {manualPackageSeal?.seal_status === "revoked" ? (
                      <div className="otc-muted" data-testid="evidence-manual-package-revoked-notice">
                        {tr("evidenceTrail.manualPackage.seal.revokedNotice" as MessageKey)}
                      </div>
                    ) : null}
                    {manualPackageSeal?.seal_status === "superseded" ? (
                      <div className="otc-muted" data-testid="evidence-manual-package-superseded-notice">
                        {tr("evidenceTrail.manualPackage.seal.supersededNotice" as MessageKey, {
                          replacementSealId: String(manualPackageSeal.superseded_by_seal_id ?? "")
                        })}
                      </div>
                    ) : null}
                    {canManageManualPackageSealState && manualPackageSeal && manualPackageSeal.seal_status !== "revoked" ? (
                      <div className="otc-stack otc-controls--spaced" data-testid="evidence-manual-package-revoke-panel">
                        <strong>{tr("evidenceTrail.manualPackage.seal.revokeTitle" as MessageKey)}</strong>
                        <div className="otc-grid otc-grid--counterparty-form">
                          <label className="otc-field">
                            {tr("evidenceTrail.manualPackage.seal.ticketRef" as MessageKey)}
                            <input
                              className="otc-input"
                              value={manualPackageRevokeTicketRef}
                              onChange={(event) => setManualPackageRevokeTicketRef(event.target.value)}
                              data-testid="evidence-manual-package-revoke-ticket-ref"
                            />
                          </label>
                          <label className="otc-field">
                            {tr("evidenceTrail.manualPackage.seal.reason" as MessageKey)}
                            <input
                              className="otc-input"
                              value={manualPackageRevokeReason}
                              onChange={(event) => setManualPackageRevokeReason(event.target.value)}
                              data-testid="evidence-manual-package-revoke-reason"
                            />
                          </label>
                        </div>
                        <div className="otc-controls">
                          <button
                            type="button"
                            className="otc-button otc-button--danger"
                            onClick={() => void onRevokeManualPackageSeal()}
                            disabled={revokingManualPackageSeal}
                            data-testid="evidence-manual-package-revoke"
                          >
                            {revokingManualPackageSeal
                              ? tr("evidenceTrail.manualPackage.seal.actions.revokeLoading" as MessageKey)
                              : tr("evidenceTrail.manualPackage.seal.actions.revoke" as MessageKey)}
                          </button>
                        </div>
                      </div>
                    ) : null}
                    {canManageManualPackageSealState &&
                    manualPackageSeal &&
                    !["revoked", "superseded"].includes(manualPackageSeal.seal_status) ? (
                      <div className="otc-stack otc-controls--spaced" data-testid="evidence-manual-package-supersede-panel">
                        <strong>{tr("evidenceTrail.manualPackage.seal.supersedeTitle" as MessageKey)}</strong>
                        <div className="otc-grid otc-grid--counterparty-form">
                          <label className="otc-field">
                            {tr("evidenceTrail.manualPackage.seal.supersedeSealId" as MessageKey)}
                            <input
                              className="otc-input"
                              value={manualPackageSupersedeSealId}
                              onChange={(event) => setManualPackageSupersedeSealId(event.target.value)}
                              data-testid="evidence-manual-package-supersede-seal-id"
                            />
                          </label>
                          <label className="otc-field">
                            {tr("evidenceTrail.manualPackage.seal.ticketRef" as MessageKey)}
                            <input
                              className="otc-input"
                              value={manualPackageSupersedeTicketRef}
                              onChange={(event) => setManualPackageSupersedeTicketRef(event.target.value)}
                              data-testid="evidence-manual-package-supersede-ticket-ref"
                            />
                          </label>
                          <label className="otc-field">
                            {tr("evidenceTrail.manualPackage.seal.reason" as MessageKey)}
                            <input
                              className="otc-input"
                              value={manualPackageSupersedeReason}
                              onChange={(event) => setManualPackageSupersedeReason(event.target.value)}
                              data-testid="evidence-manual-package-supersede-reason"
                            />
                          </label>
                        </div>
                        <div className="otc-controls">
                          <button
                            type="button"
                            className="otc-button otc-button--danger"
                            onClick={() => void onSupersedeManualPackageSeal()}
                            disabled={supersedingManualPackageSeal}
                            data-testid="evidence-manual-package-supersede"
                          >
                            {supersedingManualPackageSeal
                              ? tr("evidenceTrail.manualPackage.seal.actions.supersedeLoading" as MessageKey)
                              : tr("evidenceTrail.manualPackage.seal.actions.supersede" as MessageKey)}
                          </button>
                        </div>
                      </div>
                    ) : null}
                  </div>
                  {selectedContext ? (
                    <div className="otc-controls otc-controls--spaced">
                      <button
                        type="button"
                        className="otc-button otc-button--ghost"
                        onClick={focusSelectedChain}
                        data-testid="evidence-manual-package-focus-chain"
                      >
                        {tr("evidenceTrail.chain.focus" as MessageKey)}
                      </button>
                      <button
                        type="button"
                        className="otc-button otc-button--ghost"
                        onClick={() => void onExportSelectedChain()}
                        disabled={exportingSelectedChain}
                        data-testid="evidence-manual-package-export-chain"
                      >
                        {exportingSelectedChain
                          ? tr("evidenceTrail.chain.exportLoading" as MessageKey)
                          : tr("evidenceTrail.chain.export" as MessageKey)}
                      </button>
                      <button
                        type="button"
                        className="otc-button otc-button--ghost"
                        onClick={() => void onExportManualReviewPackage()}
                        disabled={exportingManualPackage}
                        data-testid="evidence-manual-package-export-package"
                      >
                        {exportingManualPackage
                          ? tr("evidenceTrail.manualPackage.exportLoading" as MessageKey)
                          : tr("evidenceTrail.manualPackage.export" as MessageKey)}
                      </button>
                      {selectedManualAuditPresetHref ? (
                        <a
                          className="otc-button otc-button--ghost"
                          href={selectedManualAuditPresetHref}
                          data-testid="evidence-manual-package-open-audit-preset"
                        >
                          {tr("evidenceTrail.manualPackage.openAuditPreset" as MessageKey)}
                        </a>
                      ) : null}
                      {selectedManualGovernanceAuditHref ? (
                        <a
                          className="otc-button otc-button--ghost"
                          href={selectedManualGovernanceAuditHref}
                          data-testid="evidence-manual-package-open-audit-governance"
                        >
                          {tr("evidenceTrail.manualPackage.openAuditGovernance" as MessageKey)}
                        </a>
                      ) : null}
                      {selectedContextLinks.map((link: OperationalContextLink & { labelKey: MessageKey }) => (
                        <a
                          key={`manual-package-${link.testIdSuffix}`}
                          className="otc-button otc-button--ghost"
                          href={link.href}
                          data-testid={`evidence-manual-package-${link.testIdSuffix}`}
                        >
                          {tr(link.labelKey as MessageKey)}
                        </a>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : null}
              {selectedManualWorkspaceRecord ? (
                <div className="otc-kv" data-testid="evidence-manual-workspace-panel">
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.workspace.table.eventId" as MessageKey)}</span>
                    <span className="otc-kv__value">{selectedManualWorkspaceRecord.eventId}</span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.details.resource" as MessageKey)}</span>
                    <span className="otc-kv__value">
                      {formatEvidenceResourceTypeValue(selectedManualWorkspaceRecord.resourceType)}
                      {selectedManualWorkspaceRecord.resourceId ? ` • ${selectedManualWorkspaceRecord.resourceId}` : ""}
                    </span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.details.caseId" as MessageKey)}</span>
                    <span className="otc-kv__value">{selectedManualWorkspaceRecord.caseId || tr("evidenceTrail.notAvailable" as MessageKey)}</span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.details.requestId" as MessageKey)}</span>
                    <span className="otc-kv__value">{selectedManualWorkspaceRecord.requestId || tr("evidenceTrail.notAvailable" as MessageKey)}</span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.details.reportId" as MessageKey)}</span>
                    <span className="otc-kv__value">{selectedManualWorkspaceRecord.reportId || tr("evidenceTrail.notAvailable" as MessageKey)}</span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.details.fileHash" as MessageKey)}</span>
                    <span className="otc-kv__value">{selectedManualWorkspaceRecord.fileHash || tr("evidenceTrail.notAvailable" as MessageKey)}</span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.workspace.table.owner" as MessageKey)}</span>
                    <span className="otc-kv__value">{selectedManualWorkspaceRecord.owner || tr("evidenceTrail.notAvailable" as MessageKey)}</span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.workspace.table.priority" as MessageKey)}</span>
                    <span className="otc-kv__value">{t(`common.priority.${selectedManualWorkspaceRecord.priority}` as MessageKey)}</span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.workspace.table.deadline" as MessageKey)}</span>
                    <span className="otc-kv__value">{formatOptionalDateValue(selectedManualWorkspaceRecord.localDeadline)}</span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.workspace.table.status" as MessageKey)}</span>
                    <span className="otc-kv__value">{tr(`evidenceTrail.workspace.status.${selectedManualWorkspaceRecord.workspaceStatus}` as MessageKey)}</span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.workspace.sourceLabel" as MessageKey)}</span>
                    <span className="otc-kv__value">{tr(`evidenceTrail.workspace.source.${selectedManualWorkspaceRecord.source}` as MessageKey)}</span>
                  </div>
                  <div className="otc-kv__row">
                    <span className="otc-kv__key">{tr("evidenceTrail.workspace.filters.note" as MessageKey)}</span>
                    <span className="otc-kv__value">{selectedManualWorkspaceRecord.note || tr("evidenceTrail.notAvailable" as MessageKey)}</span>
                  </div>
                  <div className="otc-controls otc-controls--spaced">
                    <button
                      type="button"
                      className="otc-button otc-button--ghost"
                      onClick={() => hydrateWorkspaceRecord(selectedManualWorkspaceRecord)}
                      data-testid="evidence-manual-workspace-load"
                    >
                      {tr("evidenceTrail.workspace.table.load" as MessageKey)}
                    </button>
                    <button
                      type="button"
                      className="otc-button otc-button--ghost"
                      onClick={() => openWorkspaceTimeline(selectedManualWorkspaceRecord)}
                      data-testid="evidence-manual-workspace-open-timeline"
                    >
                      {tr("evidenceTrail.workspace.timeline.open" as MessageKey)}
                    </button>
                    <button
                      type="button"
                      className="otc-button otc-button--ghost"
                      onClick={() => updateWorkspaceStatus(selectedManualWorkspaceRecord.eventId, "queued")}
                      data-testid="evidence-manual-workspace-mark-queued"
                    >
                      {tr("evidenceTrail.workspace.table.markQueued" as MessageKey)}
                    </button>
                    <button
                      type="button"
                      className="otc-button otc-button--ghost"
                      onClick={() => updateWorkspaceStatus(selectedManualWorkspaceRecord.eventId, "reviewing")}
                      data-testid="evidence-manual-workspace-mark-reviewing"
                    >
                      {tr("evidenceTrail.workspace.table.markReviewing" as MessageKey)}
                    </button>
                    <button
                      type="button"
                      className="otc-button otc-button--ghost"
                      onClick={() => updateWorkspaceStatus(selectedManualWorkspaceRecord.eventId, "sealed")}
                      data-testid="evidence-manual-workspace-mark-sealed"
                    >
                      {tr("evidenceTrail.workspace.table.markSealed" as MessageKey)}
                    </button>
                    {selectedManualWorkspaceRecord.source === "local" ? (
                      <button
                        type="button"
                        className="otc-button otc-button--ghost"
                        onClick={() => removeWorkspaceRecord(selectedManualWorkspaceRecord.eventId)}
                        data-testid="evidence-manual-workspace-remove"
                      >
                        {tr("evidenceTrail.workspace.table.remove" as MessageKey)}
                      </button>
                    ) : null}
                  </div>
                </div>
              ) : null}
              {selectedContext ? (
                <div className="otc-controls otc-controls--spaced">
                  <button type="button" className="otc-button" onClick={focusSelectedChain} data-testid="evidence-focus-chain">
                    {tr("evidenceTrail.chain.focus" as MessageKey)}
                  </button>
                  <button
                    type="button"
                    className="otc-button otc-button--ghost"
                    onClick={() => void onExportSelectedChain()}
                    disabled={exportingSelectedChain}
                    data-testid="evidence-export-selected-chain"
                  >
                    {exportingSelectedChain ? tr("evidenceTrail.chain.exportLoading" as MessageKey) : tr("evidenceTrail.chain.export" as MessageKey)}
                  </button>
                  {selectedManualPackageSummary ? (
                    <button
                      type="button"
                      className="otc-button otc-button--ghost"
                      onClick={() => void onExportManualReviewPackage()}
                      disabled={exportingManualPackage}
                      data-testid="evidence-export-manual-package"
                    >
                      {exportingManualPackage
                        ? tr("evidenceTrail.manualPackage.exportLoading" as MessageKey)
                        : tr("evidenceTrail.manualPackage.export" as MessageKey)}
                    </button>
                  ) : null}
                  {linkedRosLoading ? (
                    <button type="button" className="otc-button otc-button--ghost" disabled>
                      {tr("evidenceTrail.details.loadingRosCoaf" as MessageKey)}
                    </button>
                  ) : null}
                  {!linkedRosLoading && resolvedRosIdForDossier ? (
                    <button
                      type="button"
                      className="otc-button otc-button--ghost"
                      onClick={() => void onExportRosCoafRegulatoryDossier(resolvedRosIdForDossier)}
                      disabled={exportingRosCoafDossier}
                      data-testid="evidence-export-ros-dossier"
                    >
                      {exportingRosCoafDossier
                        ? tr("evidenceTrail.details.exportRosDossierLoading" as MessageKey)
                        : tr("evidenceTrail.details.exportRosDossier" as MessageKey)}
                    </button>
                  ) : null}
                  {selectedContextLinks.map((link: OperationalContextLink & { labelKey: MessageKey }) => (
                    <a key={`global-${link.testIdSuffix}`} className="otc-button otc-button--ghost" href={link.href}>
                      {tr(link.labelKey as MessageKey)}
                    </a>
                  ))}
                </div>
              ) : null}
              <CodeBlock>{JSON.stringify(selectedLog.metadata, null, 2)}</CodeBlock>
            </div>
          ) : (
            <Message>{tr("evidenceTrail.details.empty" as MessageKey)}</Message>
          )}
        </Panel>
      </section>

      <Panel
        title={tr("evidenceTrail.chain.title" as MessageKey)}
        description={tr("evidenceTrail.chain.description" as MessageKey)}
      >
        {!selectedContext || !selectedChainSummary ? (
          <div data-testid="evidence-chain-empty">
            <Message>{tr("evidenceTrail.chain.empty" as MessageKey)}</Message>
          </div>
        ) : (
          <div className="otc-stack" data-testid="evidence-chain-panel">
            <MetricGrid>
              <MetricCard
                label={tr("evidenceTrail.chain.metrics.total" as MessageKey)}
                value={selectedChainSummary.total}
                meta={tr("evidenceTrail.chain.metrics.totalMeta" as MessageKey)}
              />
              <MetricCard
                label={tr("evidenceTrail.chain.metrics.uniqueActions" as MessageKey)}
                value={selectedChainSummary.uniqueActions}
                meta={tr("evidenceTrail.chain.metrics.uniqueActionsMeta" as MessageKey)}
              />
              <MetricCard
                label={tr("evidenceTrail.chain.metrics.withHash" as MessageKey)}
                value={selectedChainSummary.withHash}
                meta={tr("evidenceTrail.chain.metrics.withHashMeta" as MessageKey)}
              />
              <MetricCard
                label={tr("evidenceTrail.chain.metrics.withTrace" as MessageKey)}
                value={`${selectedChainSummary.withRequestId}/${selectedChainSummary.withReportId}`}
                meta={tr("evidenceTrail.chain.metrics.withTraceMeta" as MessageKey)}
              />
            </MetricGrid>
            <div className="otc-kv" data-testid="evidence-chain-summary">
              <div className="otc-kv__row">
                <span className="otc-kv__key">{tr("evidenceTrail.chain.scope" as MessageKey)}</span>
                <span className="otc-kv__value">
                  {selectedContext.reportId || selectedContext.requestId || selectedContext.caseId || tr("evidenceTrail.notAvailable" as MessageKey)}
                </span>
              </div>
              <div className="otc-kv__row">
                <span className="otc-kv__key">{tr("evidenceTrail.chain.firstEvent" as MessageKey)}</span>
                <span className="otc-kv__value" data-testid="evidence-chain-first-event">
                  {formatOptionalDateValue(selectedChainSummary.firstAt)}
                </span>
              </div>
              <div className="otc-kv__row">
                <span className="otc-kv__key">{tr("evidenceTrail.chain.lastEvent" as MessageKey)}</span>
                <span className="otc-kv__value" data-testid="evidence-chain-last-event">
                  {formatOptionalDateValue(selectedChainSummary.lastAt)}
                </span>
              </div>
              <div className="otc-kv__row">
                <span className="otc-kv__key">{tr("evidenceTrail.chain.materialHash" as MessageKey)}</span>
                <span className="otc-kv__value otc-mono">{selectedHashContext?.primaryHash || selectedContext.fileHash || selectedLog?.file_hash_sha256 || tr("evidenceTrail.notAvailable" as MessageKey)}</span>
              </div>
              {selectedHashContext ? renderHashContextChainRows(selectedHashContext) : null}
            </div>
            {selectedDossierContext
              ? renderDossierContext(selectedDossierContext, {
                  container: "evidence-chain-dossier-context",
                  openReport: "evidence-chain-open-report",
                  openRosCoaf: "evidence-chain-open-roscoaf"
                })
              : null}
          </div>
        )}
      </Panel>

      <Panel title={tr("evidenceTrail.matrix.title" as MessageKey)} description={tr("evidenceTrail.matrix.description" as MessageKey)}>
        <table className="otc-table otc-table--spaced">
          <thead>
            <tr>
              <th>{tr("evidenceTrail.matrix.domain" as MessageKey)}</th>
              <th>{tr("evidenceTrail.matrix.auditAction" as MessageKey)}</th>
              <th>{tr("evidenceTrail.matrix.evidenceTypes" as MessageKey)}</th>
              <th>{tr("evidenceTrail.matrix.keys" as MessageKey)}</th>
            </tr>
          </thead>
          <tbody>
            {DOMAIN_PRESETS.filter((preset) => preset.id !== "all").map((preset) => (
              <tr key={preset.id}>
                <td><strong>{tr(preset.label)}</strong></td>
                <td>{preset.action || tr("evidenceTrail.notAvailable" as MessageKey)}</td>
                <td>{preset.evidenceTypes.join(", ")}</td>
                <td>{tr(`evidenceTrail.keys.${preset.id}` as MessageKey)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>

      <Panel title={tr("evidenceTrail.workspaceHistory.title" as MessageKey)} description={tr("evidenceTrail.workspaceHistory.description" as MessageKey)}>
        {workspace.length ? (
          <table className="otc-table otc-table--spaced">
            <thead>
              <tr>
                <th>{tr("evidenceTrail.workspaceHistory.eventId" as MessageKey)}</th>
                <th>{tr("evidenceTrail.workspaceHistory.action" as MessageKey)}</th>
                <th>{tr("evidenceTrail.workspaceHistory.resourceType" as MessageKey)}</th>
                <th>{tr("evidenceTrail.workspaceHistory.status" as MessageKey)}</th>
                <th>{tr("evidenceTrail.workspaceHistory.owner" as MessageKey)}</th>
                <th>{tr("evidenceTrail.workspaceHistory.lastAction" as MessageKey)}</th>
              </tr>
            </thead>
            <tbody>
              {workspace
                .slice()
                .sort((a, b) => b.lastActionAt.localeCompare(a.lastActionAt))
                .slice(0, 100)
                .map((record) => (
                  <tr
                    key={record.eventId}
                    className={timelineEventId === record.eventId ? "otc-row-selected otc-row-clickable" : "otc-row-clickable"}
                    onClick={() => setTimelineEventId(record.eventId)}
                  >
                    <td><span className="otc-mono">{record.eventId}</span></td>
                    <td>{record.action || tr("evidenceTrail.notAvailable" as MessageKey)}</td>
                    <td>{record.resourceType || tr("evidenceTrail.notAvailable" as MessageKey)}</td>
                    <td>
                      <Pill tone={record.workspaceStatus === "sealed" ? "success" : record.workspaceStatus === "reviewing" ? "warning" : undefined}>
                        {record.workspaceStatus}
                      </Pill>
                    </td>
                    <td>{record.owner || tr("evidenceTrail.notAvailable" as MessageKey)}</td>
                    <td>{formatDateValue(record.lastActionAt)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        ) : (
          <Message>{tr("evidenceTrail.workspaceHistory.empty" as MessageKey)}</Message>
        )}
      </Panel>
    </AppShell>
  );
}

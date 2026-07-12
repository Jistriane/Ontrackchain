"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import { formatDateTime as formatDate } from "../lib/date-format";
import { useI18n } from "../../components/i18n-provider";
import { WorkItemTimelinePanel } from "../../components/work-item-timeline-panel";
import type { MessageKey } from "../lib/i18n";
import { fetchAuthContext, resolveOwnerUserId, type AuthContext } from "../lib/ownership";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { buildWorkItemTimelineLabels } from "../lib/work-item-timeline-labels";
import { useWorkItemTimeline } from "../lib/use-work-item-timeline";
import { formatTimelineEvent } from "../lib/work-item-timeline";
import {
  loadWorkspaceRecords,
  saveWorkspaceRecords,
  sortByLastActionAtDesc,
  toApiDueAt,
  toDateTimeLocalValue
} from "../lib/workspace-storage";
import {
  buildOperationalContextLinks,
  type OperationalContext,
  type OperationalContextLink
} from "../lib/operational-context";
import {
  isWorkItemUuidLike as isUuidLike,
  readWorkItemMetadataString,
  resolveWorkItemOwnerDisplay,
  resolveWorkItemWorkspaceStatus,
  type CreateWorkItemRequest,
  type PatchWorkItemRequest,
  type RosCoafWorkItemMetadata,
  type WorkItemListResponse,
  type WorkItemPriority,
  type WorkItemQueueStatus,
  type WorkItemResponse,
  withCanonicalWorkItemMetadata
} from "../lib/work-items";

type GenerateRosCoafResponse = {
  ros_id: string;
  report_id: string;
  report_type: string;
  status: string;
  created_at: string;
  file_hash_sha256: string;
  content_type: string;
};

type ApproveRosCoafResponse = {
  ros_id: string;
  status: string;
  approved_at: string;
  approval_2fa_verified: boolean;
};

type SubmitRosCoafResponse = {
  ros_id: string;
  status: string;
  submitted_at: string;
  coaf_protocol_number: string;
  coaf_receipt_hash: string;
};

type RosCoafListItem = {
  ros_id: string;
  case_id: string | null;
  status: string;
  report_id: string;
  created_at: string;
  approved_at: string | null;
  submitted_at: string | null;
  coaf_protocol_number: string;
  coaf_receipt_hash: string;
  rejection_reason: string;
  approval_2fa_verified: boolean;
  submission_deadline: string | null;
  deadline_breached: boolean;
  last_activity_at: string;
};

type RosCoafListResponse = {
  data: RosCoafListItem[];
  page: number;
  limit: number;
  total: number;
  has_more: boolean;
};

type RosCoafAuditEntry = {
  id: string;
  action: string;
  user_id: string | null;
  created_at: string;
  metadata: Record<string, unknown>;
};

type RosCoafDetailResponse = {
  ros_id: string;
  case_id: string | null;
  report_id: string;
  status: string;
  tipologia_code: string;
  tipologia_description: string;
  trigger_reason: string;
  suspected_amount_brl: number | null;
  suspected_address: string;
  suspected_chain: string;
  pdf_hash: string;
  pdf_path: string;
  generated_at: string | null;
  approved_at: string | null;
  submitted_at: string | null;
  approval_2fa_verified: boolean;
  rejection_reason: string;
  submission_deadline: string | null;
  deadline_breached: boolean;
  coaf_protocol_number: string;
  coaf_receipt_hash: string;
  evidence_hash: string;
  evidence_trail_ref: string;
  created_at: string;
  updated_at: string;
  retain_until: string;
  audit: RosCoafAuditEntry[];
};

type RegulatoryTimelineEntry = {
  id: string;
  source: "domain_audit" | "work_event" | "work_comment";
  label: string;
  detail: string | null;
  actor: string | null;
  createdAt: string;
};

type RosCoafDossierHistoryEntry = {
  id: string;
  filename: string;
  dossierSha256: string;
  actor: string | null;
  createdAt: string;
};

type RosCoafDossierHistorySummary = {
  totalDownloads: number;
  latestFilename: string;
  latestHash: string;
  latestCreatedAt: string;
};

type WorkspacePriority = WorkItemPriority;
type WorkspaceSource = "server" | "local";
type RosCoafWorkItemResponse = WorkItemResponse<RosCoafWorkItemMetadata>;
type RosCoafWorkItemListResponse = WorkItemListResponse<RosCoafWorkItemMetadata>;

type RosWorkspaceRecord = {
  workItemId?: string;
  source: WorkspaceSource;
  rosId: string;
  caseId: string;
  owner: string;
  priority: WorkspacePriority;
  localDeadline: string;
  status: string;
  reportId: string;
  createdAt: string;
  approvedAt: string;
  submittedAt: string;
  coafProtocolNumber: string;
  coafReceiptHash: string;
  submissionDeadline: string;
  deadlineBreached: boolean;
  rejectionReason: string;
  approval2faVerified: boolean;
  lastActionAt: string;
};

const STORAGE_KEY = "otc-ros-coaf-workspace";
const WORKSPACE_PAGE_LIMIT = 100;
const ROS_COAF_APPROVE_ALLOWED_ROLES = new Set([
  "ADMIN",
  "COMPLIANCE_OFFICER",
  "OTK_COMPLIANCE_OFFICER",
  "LEGAL_REVIEWER",
  "OTK_LEGAL_REVIEWER",
  "REVIEWER",
  "OTK_REVIEWER"
]);
const ROS_COAF_SUBMITTED_ALLOWED_ROLES = new Set(["ADMIN", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"]);

function normalizeAuthRole(role: string | null | undefined) {
  return String(role ?? "").trim().toUpperCase();
}

function loadWorkspace(): RosWorkspaceRecord[] {
  return loadWorkspaceRecords<RosWorkspaceRecord>(STORAGE_KEY, (record) => {
    const source: WorkspaceSource = record.source === "server" ? "server" : "local";
    return {
      workItemId: typeof record.workItemId === "string" ? record.workItemId : undefined,
      source,
      rosId: typeof record.rosId === "string" ? record.rosId : "",
      caseId: typeof record.caseId === "string" ? record.caseId : "",
      owner: typeof record.owner === "string" ? record.owner : "",
      priority: record.priority === "critical" || record.priority === "high" || record.priority === "normal" ? record.priority : "normal",
      localDeadline: typeof record.localDeadline === "string" ? record.localDeadline : "",
      status: typeof record.status === "string" ? record.status : "PENDING_GENERATION",
      reportId: typeof record.reportId === "string" ? record.reportId : "",
      createdAt: typeof record.createdAt === "string" ? record.createdAt : "",
      approvedAt: typeof record.approvedAt === "string" ? record.approvedAt : "",
      submittedAt: typeof record.submittedAt === "string" ? record.submittedAt : "",
      coafProtocolNumber: typeof record.coafProtocolNumber === "string" ? record.coafProtocolNumber : "",
      coafReceiptHash: typeof record.coafReceiptHash === "string" ? record.coafReceiptHash : "",
      submissionDeadline: typeof record.submissionDeadline === "string" ? record.submissionDeadline : "",
      deadlineBreached: record.deadlineBreached === true,
      rejectionReason: typeof record.rejectionReason === "string" ? record.rejectionReason : "",
      approval2faVerified: record.approval2faVerified === true,
      lastActionAt: typeof record.lastActionAt === "string" ? record.lastActionAt : ""
    };
  });
}

function saveWorkspace(records: RosWorkspaceRecord[]) {
  saveWorkspaceRecords(STORAGE_KEY, records);
}

function upsertWorkspaceRecord(
  current: RosWorkspaceRecord[],
  next: Partial<RosWorkspaceRecord> & { rosId: string }
): RosWorkspaceRecord[] {
  const existing = current.find((item) => item.rosId === next.rosId);
  const base: RosWorkspaceRecord =
    existing ?? {
      workItemId: next.workItemId,
      source: next.source ?? "local",
      rosId: next.rosId,
      caseId: "",
      owner: "",
      priority: "normal",
      localDeadline: "",
      status: "PENDING_GENERATION",
      reportId: "",
      createdAt: "",
      approvedAt: "",
      submittedAt: "",
      coafProtocolNumber: "",
      coafReceiptHash: "",
      submissionDeadline: "",
      deadlineBreached: false,
      rejectionReason: "",
      approval2faVerified: false,
      lastActionAt: ""
    };

  const merged: RosWorkspaceRecord = {
    ...base,
    ...next,
    lastActionAt: next.lastActionAt ?? new Date().toISOString()
  };

  const withoutCurrent = current.filter((item) => item.rosId !== next.rosId);
  return sortByLastActionAtDesc([merged, ...withoutCurrent]);
}

function mergeWorkspaceRecords(serverRecords: RosWorkspaceRecord[], localRecords: RosWorkspaceRecord[]) {
  const merged = [...serverRecords];
  const seenRosIds = new Set(serverRecords.map((record) => record.rosId));
  const seenWorkItemIds = new Set(serverRecords.map((record) => record.workItemId).filter(Boolean));

  for (const record of localRecords) {
    if (seenRosIds.has(record.rosId)) {
      continue;
    }
    if (record.workItemId && seenWorkItemIds.has(record.workItemId)) {
      continue;
    }
    merged.push(record);
  }

  return sortByLastActionAtDesc(merged);
}

function mapQueueStatusToRosStatus(status: WorkItemQueueStatus) {
  switch (status) {
    case "APPROVED":
      return "APPROVED";
    case "REJECTED":
      return "REJECTED";
    case "SUBMITTED":
    case "CLOSED":
      return "SUBMITTED_MANUAL";
    default:
      return "PENDING_APPROVAL";
  }
}

function mapRosStatusToQueueStatus(status: string): WorkItemQueueStatus {
  switch (status) {
    case "APPROVED":
      return "APPROVED";
    case "REJECTED":
      return "REJECTED";
    case "SUBMITTED_MANUAL":
      return "SUBMITTED";
    default:
      return "UNDER_REVIEW";
  }
}

function mapRosStatusToPhase(status: string) {
  switch (status) {
    case "APPROVED":
      return "approved";
    case "REJECTED":
      return "rejected";
    case "SUBMITTED_MANUAL":
      return "submitted";
    default:
      return "generated";
  }
}

function mapWorkItemToWorkspaceRecord(item: RosCoafWorkItemResponse): RosWorkspaceRecord {
  const metadata = item.metadata ?? {};
  const status = resolveWorkItemWorkspaceStatus(metadata, "ros_record", mapQueueStatusToRosStatus(item.queue_status));
  return {
    workItemId: item.id,
    source: "server",
    rosId: readWorkItemMetadataString(metadata, "ros_id") || item.resource_id,
    caseId: item.case_id ?? readWorkItemMetadataString(metadata, "case_id"),
    owner: resolveWorkItemOwnerDisplay(metadata, item.owner_user_id),
    priority: item.priority,
    localDeadline: toDateTimeLocalValue(item.due_at),
    status,
    reportId: item.report_external_id ?? readWorkItemMetadataString(metadata, "report_id"),
    createdAt: readWorkItemMetadataString(metadata, "created_at"),
    approvedAt: readWorkItemMetadataString(metadata, "approved_at"),
    submittedAt: readWorkItemMetadataString(metadata, "submitted_at"),
    coafProtocolNumber: readWorkItemMetadataString(metadata, "coaf_protocol_number"),
    coafReceiptHash: readWorkItemMetadataString(metadata, "coaf_receipt_hash") || (status === "SUBMITTED_MANUAL" ? item.note ?? "" : ""),
    submissionDeadline: "",
    deadlineBreached: false,
    rejectionReason: readWorkItemMetadataString(metadata, "rejection_reason") || (status === "REJECTED" ? item.note ?? "" : ""),
    approval2faVerified: metadata.approval_2fa_verified === true,
    lastActionAt: item.last_activity_at || item.updated_at
  };
}

function mapOfficialRosRecordToWorkspaceRecord(item: RosCoafListItem): RosWorkspaceRecord {
  return {
    source: "server",
    rosId: item.ros_id,
    caseId: item.case_id ?? "",
    owner: "",
    priority: "normal",
    localDeadline: "",
    status: item.status,
    reportId: item.report_id,
    createdAt: item.created_at,
    approvedAt: item.approved_at ?? "",
    submittedAt: item.submitted_at ?? "",
    coafProtocolNumber: item.coaf_protocol_number,
    coafReceiptHash: item.coaf_receipt_hash,
    submissionDeadline: item.submission_deadline ?? "",
    deadlineBreached: item.deadline_breached === true,
    rejectionReason: item.rejection_reason,
    approval2faVerified: item.approval_2fa_verified === true,
    lastActionAt: item.last_activity_at
  };
}

function mergeOfficialWorkspaceRecords(current: RosWorkspaceRecord[], officialRecords: RosWorkspaceRecord[]) {
  if (!officialRecords.length) {
    return current;
  }

  const byRosId = new Map(current.map((record) => [record.rosId, record]));
  for (const officialRecord of officialRecords) {
    const existing = byRosId.get(officialRecord.rosId);
    if (!existing) {
      byRosId.set(officialRecord.rosId, officialRecord);
      continue;
    }

    byRosId.set(officialRecord.rosId, {
      ...existing,
      source: "server",
      caseId: officialRecord.caseId || existing.caseId,
      status: officialRecord.status || existing.status,
      reportId: officialRecord.reportId || existing.reportId,
      createdAt: officialRecord.createdAt || existing.createdAt,
      approvedAt: officialRecord.approvedAt || existing.approvedAt,
      submittedAt: officialRecord.submittedAt || existing.submittedAt,
      coafProtocolNumber: officialRecord.coafProtocolNumber || existing.coafProtocolNumber,
      coafReceiptHash: officialRecord.coafReceiptHash || existing.coafReceiptHash,
      submissionDeadline: officialRecord.submissionDeadline || existing.submissionDeadline,
      deadlineBreached: officialRecord.deadlineBreached,
      rejectionReason: officialRecord.rejectionReason || existing.rejectionReason,
      approval2faVerified: officialRecord.approval2faVerified || existing.approval2faVerified,
      lastActionAt:
        (officialRecord.lastActionAt || "").localeCompare(existing.lastActionAt || "") > 0
          ? officialRecord.lastActionAt
          : existing.lastActionAt
    });
  }

  return [...byRosId.values()].sort((a, b) => (b.lastActionAt || "").localeCompare(a.lastActionAt || ""));
}

function getUrgency(record: RosWorkspaceRecord): "overdue" | "due_soon" | "on_track" | "no_deadline" {
  if (!record.localDeadline) {
    return "no_deadline";
  }

  if (record.status === "SUBMITTED_MANUAL" || record.status === "REJECTED") {
    return "on_track";
  }

  const now = Date.now();
  const deadline = new Date(record.localDeadline).getTime();
  if (Number.isNaN(deadline)) {
    return "no_deadline";
  }
  if (deadline < now) {
    return "overdue";
  }
  if (deadline - now < 24 * 60 * 60 * 1000) {
    return "due_soon";
  }
  return "on_track";
}

function getRegulatorySlaState(record: RosWorkspaceRecord): "breached" | "onTrack" | "notAvailable" {
  if (!record.submissionDeadline) {
    return "notAvailable";
  }
  return record.deadlineBreached ? "breached" : "onTrack";
}

function buildReportDownloadUrl(reportId: string, createdAt: string, caseId: string) {
  if (!reportId.trim() || !createdAt.trim()) {
    return null;
  }
  const query = new URLSearchParams({
    report_id: reportId,
    report_type: "coaf_ready_report",
    created_at: createdAt
  });
  if (caseId.trim()) {
    query.set("case_id", caseId.trim());
  }
  return `/api/app/reports/download?${query.toString()}`;
}

function buildRosRegulatoryDossierFilename(rosId: string) {
  return `ontrackchain-ros-coaf-regulatory-dossier-${rosId.trim() || "selection"}.json`;
}

function resolveDownloadFilename(contentDisposition: string | null, fallbackName: string) {
  if (!contentDisposition) {
    return fallbackName;
  }

  const match = contentDisposition.match(/filename\*?=(?:UTF-8''|")?([^\";]+)"?/i);
  if (!match) {
    return fallbackName;
  }

  try {
    return decodeURIComponent(match[1]);
  } catch {
    return match[1];
  }
}

function summarizeDossierHash(hash: string | null) {
  const normalized = hash?.trim() ?? "";
  if (!normalized) {
    return "n/a";
  }
  return normalized.length > 16 ? `${normalized.slice(0, 16)}...` : normalized;
}

function buildRosOperationalContext(input: {
  caseId?: string | null;
  reportId?: string | null;
  rosId?: string | null;
}): OperationalContext {
  const caseId = input.caseId?.trim() ?? "";
  const reportId = input.reportId?.trim() ?? "";
  const rosId = input.rosId?.trim() ?? "";
  return {
    caseId,
    requestId: caseId,
    reportId,
    fileHash: "",
    resourceType: "case",
    resourceId: caseId || rosId || reportId,
    address: "",
    chain: "ethereum",
    counterpartyId: "",
    legalName: "",
    documentNumber: "",
    rosId,
    reportType: "coaf_ready_report",
    blockId: ""
  };
}

function buildRosContextLinks(
  context: OperationalContext,
  labelKeyByKind: Partial<Record<OperationalContextLink["kind"], MessageKey>>
) {
  return buildOperationalContextLinks(context, {
    includeEvidence: true,
    evidenceDomain: "reports",
    auditFallbackResourceType: "case",
    auditResourceIdOverride: context.caseId || context.rosId || context.reportId,
    evidenceResourceIdOverride: context.caseId || context.rosId || context.reportId
  })
    .filter((link: OperationalContextLink) => link.kind === "case" || link.kind === "audit" || link.kind === "evidence")
    .map((link: OperationalContextLink) => ({
      ...link,
      labelKey: labelKeyByKind[link.kind] ?? "rosCoaf.workspace.openAudit"
    }));
}

function summarizeMetadataFields(
  record: Record<string, unknown> | null | undefined,
  preferredKeys: string[]
) {
  if (!record) {
    return null;
  }

  const parts: string[] = [];
  for (const key of preferredKeys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) {
      parts.push(`${key}: ${value.trim()}`);
      continue;
    }
    if (typeof value === "number" || typeof value === "boolean") {
      parts.push(`${key}: ${String(value)}`);
    }
    if (parts.length >= 3) {
      break;
    }
  }

  return parts.length ? parts.join(" | ") : null;
}

function readAuditMetadataString(record: Record<string, unknown> | null | undefined, key: string) {
  const value = record?.[key];
  return typeof value === "string" && value.trim() ? value.trim() : "";
}

function summarizeShortHash(value: string) {
  const normalized = value.trim();
  if (!normalized) {
    return "";
  }
  return normalized.length > 16 ? `${normalized.slice(0, 16)}...` : normalized;
}

export default function RosCoafPage() {
  const { locale, t } = useI18n();
  const searchParams = useSearchParams();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);

  function formatTimelineSourceTone(source: RegulatoryTimelineEntry["source"]) {
    return source === "domain_audit" ? "success" : source === "work_event" ? "warning" : "danger";
  }

  function formatActorValue(actor: string | null) {
    return actor || tr("rosCoaf.history.notAvailable" as MessageKey);
  }

  function formatDateValue(value: string) {
    return formatDate(value, locale) ?? value;
  }

  function formatOptionalDateValue(value: string | null | undefined, fallback: string) {
    const normalized = value?.trim() ?? "";
    return normalized ? formatDateValue(normalized) : fallback;
  }

  function formatSourceTone(source: WorkspaceSource) {
    return source === "server" ? "success" : "warning";
  }

  function formatSourceLabel(source: WorkspaceSource) {
    return tr(`rosCoaf.workspace.source.${source}` as MessageKey);
  }

  function renderSourcePill(source: WorkspaceSource) {
    return <Pill tone={formatSourceTone(source)}>{formatSourceLabel(source)}</Pill>;
  }

  function formatPriorityTone(priority: RosWorkspaceRecord["priority"]) {
    return priority === "critical" ? "danger" : priority === "high" ? "warning" : undefined;
  }

  function renderPriorityPill(priority: RosWorkspaceRecord["priority"]) {
    return <Pill tone={formatPriorityTone(priority)}>{tr(`rosCoaf.priority.${priority}` as MessageKey)}</Pill>;
  }

  function formatUrgencyTone(urgency: ReturnType<typeof getUrgency>) {
    return urgency === "overdue" ? "danger" : urgency === "due_soon" ? "warning" : undefined;
  }

  function formatPhaseTone(status: string) {
    return status === "SUBMITTED_MANUAL" ? "success" : status === "REJECTED" ? "danger" : "warning";
  }

  function formatPhaseLabel(status: string) {
    return tr(`rosCoaf.workspace.phase.${mapRosStatusToPhase(status)}` as MessageKey);
  }

  function renderPhasePill(status: string) {
    return <Pill tone={formatPhaseTone(status)}>{formatPhaseLabel(status)}</Pill>;
  }

  function resolveSlaState(input: {
    submissionDeadline: string | null;
    deadlineBreached: boolean;
  }): "breached" | "onTrack" | "notAvailable" {
    if (!input.submissionDeadline) {
      return "notAvailable";
    }
    return input.deadlineBreached ? "breached" : "onTrack";
  }

  function formatSlaTone(state: "breached" | "onTrack" | "notAvailable") {
    return state === "breached" ? "danger" : state === "onTrack" ? "success" : "warning";
  }

  function renderSlaPill(state: "breached" | "onTrack" | "notAvailable") {
    return (
      <Pill tone={formatSlaTone(state)}>{tr(`rosCoaf.workspace.sla.${state}` as MessageKey)}</Pill>
    );
  }

  function renderOfficialDetailTable(detail: RosCoafDetailResponse) {
    return (
      <table className="otc-table otc-table--spaced" data-testid="roscoaf-detail-table">
        <tbody>
          <tr>
            <th>{tr("rosCoaf.detail.rosId" as MessageKey)}</th>
            <td className="otc-mono">{detail.ros_id}</td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.caseId" as MessageKey)}</th>
            <td className="otc-mono">{detail.case_id || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.reportId" as MessageKey)}</th>
            <td className="otc-mono">{detail.report_id || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.status" as MessageKey)}</th>
            <td className="otc-mono">{detail.status}</td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.tipologia" as MessageKey)}</th>
            <td>
              <strong>{detail.tipologia_code}</strong>
              <div className="otc-muted">{detail.tipologia_description}</div>
            </td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.triggerReason" as MessageKey)}</th>
            <td>{detail.trigger_reason}</td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.suspectedAddress" as MessageKey)}</th>
            <td className="otc-mono">{detail.suspected_address || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.suspectedChain" as MessageKey)}</th>
            <td className="otc-mono">{detail.suspected_chain || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.suspectedAmount" as MessageKey)}</th>
            <td>{detail.suspected_amount_brl ?? tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.pdfHash" as MessageKey)}</th>
            <td className="otc-mono">{detail.pdf_hash || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.submissionDeadline" as MessageKey)}</th>
            <td>
              {detail.submission_deadline
                ? formatDateValue(detail.submission_deadline)
                : tr("rosCoaf.history.notAvailable" as MessageKey)}
            </td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.slaLabel" as MessageKey)}</th>
            <td>
              {renderSlaPill(
                resolveSlaState({
                  submissionDeadline: detail.submission_deadline,
                  deadlineBreached: detail.deadline_breached
                })
              )}
            </td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.coafProtocol" as MessageKey)}</th>
            <td className="otc-mono">{detail.coaf_protocol_number || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.receiptHash" as MessageKey)}</th>
            <td className="otc-mono">{detail.coaf_receipt_hash || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.evidenceHash" as MessageKey)}</th>
            <td className="otc-mono">{detail.evidence_hash || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.evidenceTrailRef" as MessageKey)}</th>
            <td className="otc-mono">{detail.evidence_trail_ref || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
          </tr>
          <tr>
            <th>{tr("rosCoaf.detail.retainUntil" as MessageKey)}</th>
            <td>{formatDateValue(detail.retain_until)}</td>
          </tr>
        </tbody>
      </table>
    );
  }

  function renderRegulatoryTimelinePanel(entries: RegulatoryTimelineEntry[]) {
    return (
      <Panel title={tr("rosCoaf.timeline.title" as MessageKey)} description={tr("rosCoaf.timeline.description" as MessageKey)}>
        <table className="otc-table otc-table--spaced" data-testid="roscoaf-regulatory-timeline-table">
          <thead>
            <tr>
              <th>{tr("rosCoaf.timeline.source" as MessageKey)}</th>
              <th>{tr("rosCoaf.timeline.entry" as MessageKey)}</th>
              <th>{tr("rosCoaf.timeline.actor" as MessageKey)}</th>
              <th>{tr("rosCoaf.timeline.at" as MessageKey)}</th>
            </tr>
          </thead>
          <tbody>
            {entries.slice(0, 30).map((entry) => (
              <tr key={entry.id}>
                <td>
                  <Pill tone={formatTimelineSourceTone(entry.source)}>
                    {tr(`rosCoaf.timeline.sources.${entry.source}` as MessageKey)}
                  </Pill>
                </td>
                <td>
                  <strong>{entry.label}</strong>
                  {entry.detail ? <div className="otc-muted">{entry.detail}</div> : null}
                </td>
                <td className="otc-mono">{formatActorValue(entry.actor)}</td>
                <td>{formatDateValue(entry.createdAt)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    );
  }

  function renderDossierHistoryMetrics(summary: RosCoafDossierHistorySummary) {
    return (
      <MetricGrid>
        <MetricCard
          label={tr("rosCoaf.dossierHistory.metrics.total" as MessageKey)}
          value={summary.totalDownloads}
          meta={tr("rosCoaf.dossierHistory.metrics.totalMeta" as MessageKey)}
        />
        <MetricCard
          label={tr("rosCoaf.dossierHistory.metrics.latestAt" as MessageKey)}
        value={formatOptionalDateValue(summary.latestCreatedAt, tr("rosCoaf.history.notAvailable" as MessageKey))}
          meta={tr("rosCoaf.dossierHistory.metrics.latestAtMeta" as MessageKey)}
        />
        <MetricCard
          label={tr("rosCoaf.dossierHistory.metrics.latestHash" as MessageKey)}
          value={summarizeShortHash(summary.latestHash) || tr("rosCoaf.history.notAvailable" as MessageKey)}
          meta={tr("rosCoaf.dossierHistory.metrics.latestHashMeta" as MessageKey)}
        />
      </MetricGrid>
    );
  }

  function renderDossierHistoryPanel(entries: RosCoafDossierHistoryEntry[], officialRosId: string, officialReportId: string) {
    return (
      <Panel
        title={tr("rosCoaf.dossierHistory.title" as MessageKey)}
        description={tr("rosCoaf.dossierHistory.description" as MessageKey, { count: entries.length })}
        actions={
          <a
            className="otc-link-button"
            href={`/audit?action=${encodeURIComponent("coaf_regulatory_dossier_downloaded")}&resource_type=${encodeURIComponent("ros_record")}&resource_id=${encodeURIComponent(
              officialRosId
            )}&report_id=${encodeURIComponent(officialReportId)}`}
            data-testid="roscoaf-dossier-history-open-audit"
          >
            {tr("rosCoaf.dossierHistory.openAudit" as MessageKey)}
          </a>
        }
      >
        <table className="otc-table otc-table--spaced" data-testid="roscoaf-dossier-history-table">
          <thead>
            <tr>
              <th>{tr("rosCoaf.dossierHistory.filename" as MessageKey)}</th>
              <th>{tr("rosCoaf.dossierHistory.hash" as MessageKey)}</th>
              <th>{tr("rosCoaf.dossierHistory.actor" as MessageKey)}</th>
              <th>{tr("rosCoaf.dossierHistory.at" as MessageKey)}</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr key={entry.id}>
                <td className="otc-mono">{entry.filename || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
                <td className="otc-mono">{entry.dossierSha256 || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
                <td className="otc-mono">{formatActorValue(entry.actor)}</td>
                <td>{formatDateValue(entry.createdAt)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    );
  }

  function renderOfficialAuditTable(entries: RosCoafAuditEntry[]) {
    return (
      <Panel title={tr("rosCoaf.audit.title" as MessageKey)} description={tr("rosCoaf.audit.description" as MessageKey)}>
        <table className="otc-table otc-table--spaced" data-testid="roscoaf-audit-table">
          <thead>
            <tr>
              <th>{tr("rosCoaf.audit.action" as MessageKey)}</th>
              <th>{tr("rosCoaf.audit.at" as MessageKey)}</th>
            </tr>
          </thead>
          <tbody>
            {entries.slice(0, 20).map((entry) => (
              <tr key={entry.id}>
                <td className="otc-mono">{entry.action}</td>
                <td>{formatDateValue(entry.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    );
  }

  const [rosId, setRosId] = useState("");
  const [caseId, setCaseId] = useState("");
  const [owner, setOwner] = useState("");
  const [priority, setPriority] = useState<WorkspacePriority>("normal");
  const [localDeadline, setLocalDeadline] = useState("");

  const [approveRosId, setApproveRosId] = useState("");
  const [approved, setApproved] = useState(true);
  const [rejectionReason, setRejectionReason] = useState("");

  const [submitRosId, setSubmitRosId] = useState("");
  const [coafProtocolNumber, setCoafProtocolNumber] = useState("");
  const [coafReceiptHash, setCoafReceiptHash] = useState("");

  const [generating, setGenerating] = useState(false);
  const [approving, setApproving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [syncingWorkspace, setSyncingWorkspace] = useState(false);
  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [draft, setDraft] = useState<GenerateRosCoafResponse | null>(null);
  const [approval, setApproval] = useState<ApproveRosCoafResponse | null>(null);
  const [submission, setSubmission] = useState<SubmitRosCoafResponse | null>(null);
  const [workspaceRecords, setWorkspaceRecords] = useState<RosWorkspaceRecord[]>([]);
  const [workspaceFilter, setWorkspaceFilter] = useState("all");
  const [workspaceSearch, setWorkspaceSearch] = useState("");
  const [timelineRosId, setTimelineRosId] = useState("");
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
  } = useWorkItemTimeline<RosCoafWorkItemResponse>({
    resolveErrorMessage: (apiError, fallback) => resolveApiErrorMessage(t, apiError, fallback),
    loadErrorMessage: tr("rosCoaf.workspace.timeline.errorLoad" as MessageKey),
    commentErrorMessage: tr("rosCoaf.workspace.timeline.errorComment" as MessageKey),
    emptySelectionErrorMessage: tr("rosCoaf.workspace.timeline.emptyLocal" as MessageKey),
    emptyCommentErrorMessage: tr("rosCoaf.workspace.timeline.commentEmpty" as MessageKey),
    onCommentSaved: () => {
      setNotice(tr("rosCoaf.workspace.timeline.commentSaved" as MessageKey));
    }
  });
  const [exportingRegulatoryDossier, setExportingRegulatoryDossier] = useState(false);
  const [officialDetailLoading, setOfficialDetailLoading] = useState(false);
  const [officialDetailError, setOfficialDetailError] = useState<string | null>(null);
  const [officialDetail, setOfficialDetail] = useState<RosCoafDetailResponse | null>(null);

  const canApproveDecision = approved || rejectionReason.trim().length > 0;
  const canApproveRole = ROS_COAF_APPROVE_ALLOWED_ROLES.has(normalizeAuthRole(authContext?.role));
  const canSubmitRole = ROS_COAF_SUBMITTED_ALLOWED_ROLES.has(normalizeAuthRole(authContext?.role));
  const draftDownloadUrl = useMemo(() => {
    if (!draft?.report_id || !draft?.created_at) return null;
    return buildReportDownloadUrl(draft.report_id, draft.created_at, caseId);
  }, [draft, caseId]);
  const filteredWorkspaceRecords = useMemo(() => {
    return workspaceRecords.filter((record: RosWorkspaceRecord) => {
      const matchesStatus = workspaceFilter === "all" ? true : record.status === workspaceFilter;
      const search = workspaceSearch.trim().toLowerCase();
      const matchesSearch =
        !search ||
        record.rosId.toLowerCase().includes(search) ||
        record.caseId.toLowerCase().includes(search) ||
        record.owner.toLowerCase().includes(search) ||
        record.reportId.toLowerCase().includes(search) ||
        record.coafProtocolNumber.toLowerCase().includes(search);
      return matchesStatus && matchesSearch;
    });
  }, [workspaceFilter, workspaceRecords, workspaceSearch]);
  const pendingApprovalCount = useMemo(
    () => workspaceRecords.filter((record: RosWorkspaceRecord) => record.status === "PENDING_APPROVAL").length,
    [workspaceRecords]
  );
  const overdueCount = useMemo(
    () => workspaceRecords.filter((record: RosWorkspaceRecord) => getUrgency(record) === "overdue").length,
    [workspaceRecords]
  );
  const submittedCount = useMemo(
    () => workspaceRecords.filter((record: RosWorkspaceRecord) => record.status === "SUBMITTED_MANUAL").length,
    [workspaceRecords]
  );
  const workspaceById = useMemo(
    () => new Map(workspaceRecords.map((record: RosWorkspaceRecord) => [record.rosId, record])),
    [workspaceRecords]
  );
  const selectedTimelineRecord = timelineRosId ? workspaceById.get(timelineRosId) ?? null : null;
  const workItemTimelineLabels = useMemo(() => buildWorkItemTimelineLabels(tr, "rosCoaf.workspace.timeline"), [tr]);
  const serverWorkspaceCount = useMemo(
    () => workspaceRecords.filter((record: RosWorkspaceRecord) => record.source === "server").length,
    [workspaceRecords]
  );
  const localWorkspaceCount = useMemo(
    () => workspaceRecords.filter((record: RosWorkspaceRecord) => record.source === "local").length,
    [workspaceRecords]
  );
  const hasMixedWorkspaceSources = serverWorkspaceCount > 0 && localWorkspaceCount > 0;
  const timelineContextBadges = selectedTimelineRecord
    ? [
        {
          label: formatSourceLabel(selectedTimelineRecord.source),
          tone: formatSourceTone(selectedTimelineRecord.source) as "success" | "warning"
        },
        {
          label: formatPhaseLabel(selectedTimelineRecord.status),
          tone: formatPhaseTone(selectedTimelineRecord.status) as "success" | "warning" | "danger"
        },
        {
          label: tr(`rosCoaf.workspace.sla.${getRegulatorySlaState(selectedTimelineRecord)}` as MessageKey),
          tone: formatSlaTone(getRegulatorySlaState(selectedTimelineRecord)) as "success" | "warning" | "danger"
        }
      ]
    : [];
  const unifiedRegulatoryTimeline = useMemo(() => {
    const entries: RegulatoryTimelineEntry[] = [];

    for (const auditEntry of officialDetail?.audit ?? []) {
      entries.push({
        id: `audit-${auditEntry.id}`,
        source: "domain_audit",
        label: auditEntry.action,
        detail: summarizeMetadataFields(auditEntry.metadata, [
          "request_id",
          "report_id",
          "filename",
          "dossier_sha256",
          "external_user_id",
          "file_hash_sha256"
        ]),
        actor: auditEntry.user_id,
        createdAt: auditEntry.created_at
      });
    }

    for (const event of timelineData?.events ?? []) {
      entries.push({
        id: `event-${event.id}`,
        source: "work_event",
        label: formatTimelineEvent(event),
        detail: summarizeMetadataFields(event.payload, [
          "ros_id",
          "report_id",
          "request_id",
          "coaf_protocol_number",
          "coaf_receipt_hash"
        ]),
        actor: event.actor_user_id,
        createdAt: event.created_at
      });
    }

    for (const comment of timelineData?.comments ?? []) {
      entries.push({
        id: `comment-${comment.id}`,
        source: "work_comment",
        label: workItemTimelineLabels.commentTypes[comment.comment_type],
        detail: comment.body.trim() || null,
        actor: comment.actor_user_id,
        createdAt: comment.created_at
      });
    }

    return entries.sort((left, right) => (right.createdAt || "").localeCompare(left.createdAt || ""));
  }, [officialDetail?.audit, timelineData?.comments, timelineData?.events, workItemTimelineLabels.commentTypes]);
  const dossierDownloadHistory: RosCoafDossierHistoryEntry[] = useMemo(
    () =>
      (officialDetail?.audit ?? [])
        .filter((entry) => entry.action === "coaf_regulatory_dossier_downloaded")
        .map((entry) => ({
          id: entry.id,
          filename: readAuditMetadataString(entry.metadata, "filename"),
          dossierSha256: readAuditMetadataString(entry.metadata, "dossier_sha256"),
          actor: entry.user_id,
          createdAt: entry.created_at
        })),
    [officialDetail?.audit]
  );
  const dossierHistorySummary: RosCoafDossierHistorySummary = useMemo(() => {
    const latestEntry = dossierDownloadHistory[0] ?? null;
    return {
      totalDownloads: dossierDownloadHistory.length,
      latestFilename: latestEntry?.filename ?? "",
      latestHash: latestEntry?.dossierSha256 ?? "",
      latestCreatedAt: latestEntry?.createdAt ?? ""
    };
  }, [dossierDownloadHistory]);

  async function loadOfficialWorkspace() {
    const res = await fetch(`/api/app/reports/ros-coaf?limit=${WORKSPACE_PAGE_LIMIT}`, { cache: "no-store" });
    const data = (await res.json().catch(() => null)) as RosCoafListResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      throw new Error(resolveApiErrorMessage(t, data, tr("rosCoaf.workspace.errorLoadOfficial" as MessageKey)));
    }

    const items = data && "data" in data && Array.isArray(data.data) ? data.data : [];
    return items.map((item) => mapOfficialRosRecordToWorkspaceRecord(item));
  }

  async function loadOperationalWorkspace() {
    const res = await fetch(
      `/api/app/operations/work-items?module=ros_coaf&resource_type=ros_record&limit=${WORKSPACE_PAGE_LIMIT}`,
      { cache: "no-store" }
    );
    const data = (await res.json().catch(() => null)) as RosCoafWorkItemListResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      throw new Error(resolveApiErrorMessage(t, data, tr("rosCoaf.workspace.errorSync" as MessageKey)));
    }

    const items = data && "data" in data && Array.isArray(data.data) ? data.data : [];
    return items.map((item) => mapWorkItemToWorkspaceRecord(item));
  }

  async function hydrateWorkspace(localRecords: RosWorkspaceRecord[]) {
    let mergedRecords = [...localRecords];
    let officialLoaded = false;
    let operationalLoaded = false;

    try {
      const officialRecords = await loadOfficialWorkspace();
      mergedRecords = mergeOfficialWorkspaceRecords(mergedRecords, officialRecords);
      officialLoaded = true;
    } catch {
      // Keep local/work-item fallback when the official ROS/COAF list is unavailable.
    }

    try {
      const operationalRecords = await loadOperationalWorkspace();
      mergedRecords = mergeWorkspaceRecords(operationalRecords, mergedRecords);
      operationalLoaded = true;
    } catch {
      // Keep local/domain records when the shared queue is unavailable.
    }

    setWorkspaceRecords(mergedRecords);
    if (!officialLoaded && !operationalLoaded) {
      setNotice(tr("rosCoaf.workspace.noticeLoadedLocal" as MessageKey));
    }
  }

  useEffect(() => {
    const localRecords = loadWorkspace();
    setWorkspaceRecords(localRecords);
    hydrateWorkspace(localRecords).catch(() => {
      setWorkspaceRecords(localRecords);
      setNotice(tr("rosCoaf.workspace.noticeLoadedLocal" as MessageKey));
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
  }, []);

  useEffect(() => {
    saveWorkspace(workspaceRecords);
  }, [workspaceRecords]);

  useEffect(() => {
    const nextRosId = searchParams.get("ros_id");
    const nextCaseId = searchParams.get("case_id");
    const nextOwner = searchParams.get("owner");
    const nextPriority = searchParams.get("priority") as WorkspacePriority | null;
    const nextDeadline = searchParams.get("deadline");

    if (nextRosId) {
      setRosId(nextRosId);
      setApproveRosId(nextRosId);
      setSubmitRosId(nextRosId);
      setTimelineRosId(nextRosId);
    }
    if (nextCaseId) {
      setCaseId(nextCaseId);
    }
    if (nextOwner) {
      setOwner(nextOwner);
    }
    if (nextPriority === "critical" || nextPriority === "high" || nextPriority === "normal") {
      setPriority(nextPriority);
    }
    if (nextDeadline) {
      setLocalDeadline(nextDeadline);
    }
  }, [searchParams]);

  useEffect(() => {
    if (!workspaceRecords.length) {
      setTimelineRosId("");
      resetTimeline();
      return;
    }
    if (!timelineRosId || !workspaceRecords.some((record: RosWorkspaceRecord) => record.rosId === timelineRosId)) {
      const firstServerRecord = workspaceRecords.find((record: RosWorkspaceRecord) => Boolean(record.workItemId)) ?? workspaceRecords[0];
      setTimelineRosId(firstServerRecord.rosId);
    }
  }, [timelineRosId, workspaceRecords]);

  useEffect(() => {
    if (!selectedTimelineRecord?.workItemId) {
      resetTimeline();
      return;
    }
    void loadTimeline(selectedTimelineRecord.workItemId);
  }, [loadTimeline, resetTimeline, selectedTimelineRecord?.workItemId]);

  useEffect(() => {
    const selectedRosId = timelineRosId.trim();
    if (!selectedRosId) {
      setOfficialDetail(null);
      setOfficialDetailError(null);
      return;
    }

    setOfficialDetailLoading(true);
    setOfficialDetailError(null);
    fetch(`/api/app/reports/ros-coaf/${encodeURIComponent(selectedRosId)}`, { cache: "no-store" })
      .then(async (res) => {
        const data = (await res.json().catch(() => null)) as RosCoafDetailResponse | { error?: string; detail?: unknown } | null;
        if (!res.ok) {
          throw new Error(resolveApiErrorMessage(t, data, tr("rosCoaf.detail.errorLoad" as MessageKey)));
        }
        setOfficialDetail(data as RosCoafDetailResponse);
        setOfficialDetailLoading(false);
      })
      .catch((err) => {
        setOfficialDetail(null);
        setOfficialDetailError(err instanceof Error ? err.message : tr("rosCoaf.detail.errorLoad" as MessageKey));
        setOfficialDetailLoading(false);
      });
  }, [timelineRosId, t]);

  function hydrateWorkspaceRecord(record: RosWorkspaceRecord) {
    setRosId(record.rosId);
    setCaseId(record.caseId);
    setOwner(record.owner);
    setPriority(record.priority);
    setLocalDeadline(record.localDeadline);
    setApproveRosId(record.rosId);
    setSubmitRosId(record.rosId);
    setTimelineRosId(record.rosId);
    setCoafProtocolNumber(record.coafProtocolNumber);
    setCoafReceiptHash(record.coafReceiptHash);
    setRejectionReason(record.rejectionReason);
  }

  function removeWorkspaceRecord(rosIdToRemove: string) {
    setWorkspaceRecords((current: RosWorkspaceRecord[]) =>
      current.filter((record: RosWorkspaceRecord) => record.rosId !== rosIdToRemove)
    );
  }

  async function syncWorkspaceRecord(record: RosWorkspaceRecord) {
    if (!isUuidLike(record.rosId)) {
      throw new Error(tr("rosCoaf.workspace.errorSyncMissingRosId" as MessageKey));
    }

    const ownerUserId = resolveOwnerUserId({
      ownerLabel: record.owner,
      linkedUserId: authContext?.linked_user_id,
      isUuidLike
    });

    const metadata: RosCoafWorkItemMetadata = withCanonicalWorkItemMetadata(
      {
        ros_id: record.rosId,
        report_id: record.reportId,
        created_at: record.createdAt,
        approved_at: record.approvedAt,
        approval_2fa_verified: record.approval2faVerified,
        submitted_at: record.submittedAt,
        coaf_protocol_number: record.coafProtocolNumber,
        coaf_receipt_hash: record.coafReceiptHash,
        rejection_reason: record.rejectionReason,
        ros_phase: mapRosStatusToPhase(record.status)
      },
      {
        resourceType: "ros_record",
        caseId: record.caseId,
        ownerLabel: record.owner,
        ownerUserId,
        workspaceStatus: record.status
      }
    );
    const note =
      record.status === "REJECTED"
        ? record.rejectionReason || null
        : record.status === "SUBMITTED_MANUAL"
          ? record.coafReceiptHash || null
          : null;
    const requestBody: CreateWorkItemRequest<RosCoafWorkItemMetadata> | PatchWorkItemRequest<RosCoafWorkItemMetadata> = record.workItemId
      ? {
          ...(record.reportId ? { report_external_id: record.reportId } : {}),
          ...(ownerUserId ? { owner_user_id: ownerUserId } : {}),
          priority: record.priority,
          queue_status: mapRosStatusToQueueStatus(record.status),
          due_at: toApiDueAt(record.localDeadline),
          title: `ROS/COAF • ${record.rosId}`,
          note,
          metadata
        }
      : {
          module: "ros_coaf",
          resource_type: "ros_record",
          resource_id: record.rosId,
          ...(isUuidLike(record.caseId) ? { case_id: record.caseId.trim() } : {}),
          ...(record.reportId ? { report_external_id: record.reportId } : {}),
          ...(ownerUserId ? { owner_user_id: ownerUserId } : {}),
          priority: record.priority,
          queue_status: mapRosStatusToQueueStatus(record.status),
          due_at: toApiDueAt(record.localDeadline),
          title: `ROS/COAF • ${record.rosId}`,
          note,
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
    const data = (await res.json().catch(() => null)) as RosCoafWorkItemResponse | { error?: string; detail?: unknown } | null;
    setSyncingWorkspace(false);
    if (!res.ok) {
      throw new Error(resolveApiErrorMessage(t, data, tr("rosCoaf.workspace.errorSync" as MessageKey)));
    }

    const nextRecord = mapWorkItemToWorkspaceRecord(data as RosCoafWorkItemResponse);
    setWorkspaceRecords((current: RosWorkspaceRecord[]) => upsertWorkspaceRecord(current, nextRecord));
    if (timelineRosId === nextRecord.rosId && nextRecord.workItemId) {
      await loadTimeline(nextRecord.workItemId);
    }
    return nextRecord;
  }

  async function downloadRegulatoryDossier() {
    if (!officialDetail) {
      return;
    }

    setExportingRegulatoryDossier(true);
    setError(null);

    try {
      const res = await fetch(
        `/api/app/reports/ros-coaf/${encodeURIComponent(officialDetail.ros_id)}/regulatory-dossier`,
        { cache: "no-store" }
      );
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as { error?: string; detail?: unknown } | null;
        setError(resolveApiErrorMessage(t, data, tr("rosCoaf.detail.exportDossierError" as MessageKey)));
        setExportingRegulatoryDossier(false);
        return;
      }

      const blob = await res.blob();
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = href;
      link.download = resolveDownloadFilename(res.headers.get("content-disposition"), buildRosRegulatoryDossierFilename(officialDetail.ros_id));
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(href);
      setNotice(
        tr("rosCoaf.detail.exportDossierSuccess" as MessageKey, {
          hash: summarizeDossierHash(res.headers.get("x-ontrack-dossier-sha256"))
        })
      );
    } catch {
      setError(tr("rosCoaf.detail.exportDossierError" as MessageKey));
    } finally {
      setExportingRegulatoryDossier(false);
    }
  }

  async function onGenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setGenerating(true);
    setDraft(null);
    setApproval(null);
    setSubmission(null);

    const payload = { ros_id: rosId.trim() };
    const res = await fetch("/api/app/reports/ros-coaf", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = (await res.json().catch(() => null)) as GenerateRosCoafResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setError(resolveApiErrorMessage(t, data, tr("rosCoaf.errorGenerate" as MessageKey)));
      setGenerating(false);
      return;
    }

    setDraft(data as GenerateRosCoafResponse);
    setApproveRosId((data as GenerateRosCoafResponse).ros_id);
    setSubmitRosId((data as GenerateRosCoafResponse).ros_id);
    const draftRecord: RosWorkspaceRecord = {
      workItemId: workspaceById.get((data as GenerateRosCoafResponse).ros_id)?.workItemId,
      source: "local",
      rosId: (data as GenerateRosCoafResponse).ros_id,
      caseId: caseId.trim(),
      owner: owner.trim(),
      priority,
      localDeadline,
      status: (data as GenerateRosCoafResponse).status,
      reportId: (data as GenerateRosCoafResponse).report_id,
      createdAt: (data as GenerateRosCoafResponse).created_at,
      approvedAt: "",
      submittedAt: "",
      coafProtocolNumber: "",
      coafReceiptHash: "",
      submissionDeadline: workspaceById.get((data as GenerateRosCoafResponse).ros_id)?.submissionDeadline ?? "",
      deadlineBreached: workspaceById.get((data as GenerateRosCoafResponse).ros_id)?.deadlineBreached ?? false,
      rejectionReason: "",
      approval2faVerified: false,
      lastActionAt: (data as GenerateRosCoafResponse).created_at
    };
    setWorkspaceRecords((current: RosWorkspaceRecord[]) => upsertWorkspaceRecord(current, draftRecord));
    try {
      await syncWorkspaceRecord(draftRecord);
      setNotice(tr("rosCoaf.workspace.noticeGeneratedSynced" as MessageKey));
    } catch (syncError) {
      setNotice(tr("rosCoaf.workspace.noticeGeneratedLocalOnly" as MessageKey));
      setError(syncError instanceof Error ? syncError.message : tr("rosCoaf.workspace.errorSync" as MessageKey));
    }
    setGenerating(false);
  }

  async function onApprove(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setApproving(true);
    setApproval(null);

    const payload = {
      approved,
      ...(approved ? {} : { rejection_reason: rejectionReason.trim() })
    };

    const res = await fetch(`/api/app/reports/ros-coaf/${encodeURIComponent(approveRosId.trim())}/approve`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = (await res.json().catch(() => null)) as ApproveRosCoafResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setError(resolveApiErrorMessage(t, data, tr("rosCoaf.errorApprove" as MessageKey)));
      setApproving(false);
      return;
    }

    setApproval(data as ApproveRosCoafResponse);
    const currentRecord = workspaceById.get(approveRosId.trim());
    const draftRecord: RosWorkspaceRecord = {
      workItemId: currentRecord?.workItemId,
      source: currentRecord?.source ?? "local",
      rosId: approveRosId.trim(),
      caseId: currentRecord?.caseId ?? caseId.trim(),
      owner: currentRecord?.owner ?? owner.trim(),
      priority: currentRecord?.priority ?? priority,
      localDeadline: currentRecord?.localDeadline ?? localDeadline,
      status: (data as ApproveRosCoafResponse).status,
      reportId: currentRecord?.reportId ?? draft?.report_id ?? "",
      createdAt: currentRecord?.createdAt ?? draft?.created_at ?? "",
      approvedAt: (data as ApproveRosCoafResponse).approved_at,
      submittedAt: currentRecord?.submittedAt ?? "",
      coafProtocolNumber: currentRecord?.coafProtocolNumber ?? "",
      coafReceiptHash: currentRecord?.coafReceiptHash ?? "",
      submissionDeadline: currentRecord?.submissionDeadline ?? "",
      deadlineBreached: currentRecord?.deadlineBreached ?? false,
      rejectionReason: approved ? "" : rejectionReason.trim(),
      approval2faVerified: (data as ApproveRosCoafResponse).approval_2fa_verified,
      lastActionAt: (data as ApproveRosCoafResponse).approved_at
    };
    setWorkspaceRecords((current: RosWorkspaceRecord[]) => upsertWorkspaceRecord(current, draftRecord));
    try {
      await syncWorkspaceRecord(draftRecord);
      setNotice(tr("rosCoaf.workspace.noticeApprovedSynced" as MessageKey));
    } catch (syncError) {
      setNotice(tr("rosCoaf.workspace.noticeApprovedLocalOnly" as MessageKey));
      setError(syncError instanceof Error ? syncError.message : tr("rosCoaf.workspace.errorSync" as MessageKey));
    }
    setApproving(false);
  }

  async function onSubmitted(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setSubmitting(true);
    setSubmission(null);

    const payload = {
      coaf_protocol_number: coafProtocolNumber.trim(),
      coaf_receipt_hash: coafReceiptHash.trim() || null
    };

    const res = await fetch(`/api/app/reports/ros-coaf/${encodeURIComponent(submitRosId.trim())}/submitted`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = (await res.json().catch(() => null)) as SubmitRosCoafResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setError(resolveApiErrorMessage(t, data, tr("rosCoaf.errorSubmitted" as MessageKey)));
      setSubmitting(false);
      return;
    }

    setSubmission(data as SubmitRosCoafResponse);
    const currentRecord = workspaceById.get(submitRosId.trim());
    const draftRecord: RosWorkspaceRecord = {
      workItemId: currentRecord?.workItemId,
      source: currentRecord?.source ?? "local",
      rosId: submitRosId.trim(),
      caseId: currentRecord?.caseId ?? caseId.trim(),
      owner: currentRecord?.owner ?? owner.trim(),
      priority: currentRecord?.priority ?? priority,
      localDeadline: currentRecord?.localDeadline ?? localDeadline,
      status: (data as SubmitRosCoafResponse).status,
      reportId: currentRecord?.reportId ?? draft?.report_id ?? "",
      createdAt: currentRecord?.createdAt ?? draft?.created_at ?? "",
      approvedAt: currentRecord?.approvedAt ?? approval?.approved_at ?? "",
      submittedAt: (data as SubmitRosCoafResponse).submitted_at,
      coafProtocolNumber: (data as SubmitRosCoafResponse).coaf_protocol_number,
      coafReceiptHash: (data as SubmitRosCoafResponse).coaf_receipt_hash,
      submissionDeadline: currentRecord?.submissionDeadline ?? "",
      deadlineBreached: currentRecord?.deadlineBreached ?? false,
      rejectionReason: currentRecord?.rejectionReason ?? "",
      approval2faVerified: currentRecord?.approval2faVerified ?? Boolean(approval?.approval_2fa_verified),
      lastActionAt: (data as SubmitRosCoafResponse).submitted_at
    };
    setWorkspaceRecords((current: RosWorkspaceRecord[]) => upsertWorkspaceRecord(current, draftRecord));
    try {
      await syncWorkspaceRecord(draftRecord);
      setNotice(tr("rosCoaf.workspace.noticeSubmittedSynced" as MessageKey));
    } catch (syncError) {
      setNotice(tr("rosCoaf.workspace.noticeSubmittedLocalOnly" as MessageKey));
      setError(syncError instanceof Error ? syncError.message : tr("rosCoaf.workspace.errorSync" as MessageKey));
    }
    setSubmitting(false);
  }

  return (
    <AppShell
      title={tr("rosCoaf.title" as MessageKey)}
      subtitle={tr("rosCoaf.subtitle" as MessageKey)}
      activePath="/ros-coaf"
      actions={<Pill>{tr("rosCoaf.active" as MessageKey)}</Pill>}
    >
      <MetricGrid>
        <MetricCard label={tr("rosCoaf.stats.rosId" as MessageKey)} value={draft?.ros_id ?? "--"} meta={tr("rosCoaf.stats.rosIdMeta" as MessageKey)} />
        <MetricCard label={tr("rosCoaf.stats.pendingApproval" as MessageKey)} value={pendingApprovalCount} meta={tr("rosCoaf.stats.pendingApprovalMeta" as MessageKey)} />
        <MetricCard label={tr("rosCoaf.stats.overdue" as MessageKey)} value={overdueCount} meta={tr("rosCoaf.stats.overdueMeta" as MessageKey)} accent />
        <MetricCard label={tr("rosCoaf.stats.submitted" as MessageKey)} value={submittedCount} meta={tr("rosCoaf.stats.submittedMeta" as MessageKey)} />
      </MetricGrid>

      <Panel title={tr("rosCoaf.auth.title" as MessageKey)} description={tr("rosCoaf.auth.description" as MessageKey)}>
        <Message>{tr("rosCoaf.auth.notice" as MessageKey)}</Message>
      </Panel>

      <Panel title={tr("rosCoaf.generate.title" as MessageKey)} description={tr("rosCoaf.generate.description" as MessageKey)}>
        <form className="otc-stack" onSubmit={onGenerate}>
          <div className="otc-grid otc-grid--counterparty-form">
            <label className="otc-field">
              {tr("rosCoaf.generate.rosId" as MessageKey)}
              <input className="otc-input" data-testid="roscoaf-ros-id" value={rosId} onChange={(event) => setRosId(event.target.value)} required />
            </label>
            <label className="otc-field">
              {tr("rosCoaf.generate.caseId" as MessageKey)}
              <input className="otc-input" value={caseId} onChange={(event) => setCaseId(event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("rosCoaf.generate.owner" as MessageKey)}
              <input className="otc-input" value={owner} onChange={(event) => setOwner(event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("rosCoaf.generate.priority" as MessageKey)}
              <select className="otc-select" value={priority} onChange={(event) => setPriority(event.target.value as WorkspacePriority)}>
                <option value="critical">{tr("rosCoaf.priority.critical" as MessageKey)}</option>
                <option value="high">{tr("rosCoaf.priority.high" as MessageKey)}</option>
                <option value="normal">{tr("rosCoaf.priority.normal" as MessageKey)}</option>
              </select>
            </label>
            <label className="otc-field">
              {tr("rosCoaf.generate.localDeadline" as MessageKey)}
              <input className="otc-input" type="datetime-local" value={localDeadline} onChange={(event) => setLocalDeadline(event.target.value)} />
            </label>
          </div>
          <div className="otc-controls">
            <button className="otc-button otc-button--accent" type="submit" data-testid="roscoaf-generate-btn" disabled={generating || syncingWorkspace}>
              {generating ? tr("rosCoaf.generate.submitting" as MessageKey) : tr("rosCoaf.generate.submit" as MessageKey)}
            </button>
            {draftDownloadUrl ? (
              <a className="otc-link-button" href={draftDownloadUrl}>
                {tr("rosCoaf.generate.downloadDraft" as MessageKey)}
              </a>
            ) : null}
            {draft
              ? buildRosContextLinks(
                  buildRosOperationalContext({
                    caseId,
                    reportId: draft.report_id,
                    rosId: draft.ros_id
                  }),
                  {
                    case: "rosCoaf.generate.openCase",
                    audit: "rosCoaf.generate.openAudit",
                    evidence: "rosCoaf.generate.openEvidence"
                  }
                ).map((link: OperationalContextLink & { labelKey: MessageKey }) => (
                  <a key={`generate-${link.testIdSuffix}`} className="otc-link-button" href={link.href}>
                    {tr(link.labelKey)}
                  </a>
                ))
              : null}
          </div>
        </form>
      </Panel>

      <Panel title={tr("rosCoaf.workspace.title" as MessageKey)} description={tr("rosCoaf.workspace.description" as MessageKey)}>
        {localWorkspaceCount > 0 && serverWorkspaceCount === 0 ? (
          <Message>{tr("rosCoaf.workspace.mode.localOnly" as MessageKey, { count: localWorkspaceCount })}</Message>
        ) : null}
        {hasMixedWorkspaceSources ? (
          <Message>
            {tr("rosCoaf.workspace.mode.mixed" as MessageKey, {
              server: serverWorkspaceCount,
              local: localWorkspaceCount
            })}
          </Message>
        ) : null}
        <div className="otc-grid otc-grid--counterparty-form">
          <label className="otc-field">
            {tr("rosCoaf.workspace.filterStatus" as MessageKey)}
            <select className="otc-select" value={workspaceFilter} onChange={(event) => setWorkspaceFilter(event.target.value)}>
              <option value="all">{tr("rosCoaf.workspace.all" as MessageKey)}</option>
              <option value="PENDING_APPROVAL">PENDING_APPROVAL</option>
              <option value="APPROVED">APPROVED</option>
              <option value="REJECTED">REJECTED</option>
              <option value="SUBMITTED_MANUAL">SUBMITTED_MANUAL</option>
            </select>
          </label>
          <label className="otc-field">
            {tr("rosCoaf.workspace.search" as MessageKey)}
            <input className="otc-input" value={workspaceSearch} onChange={(event) => setWorkspaceSearch(event.target.value)} />
          </label>
        </div>
        <table className="otc-table otc-table--spaced">
          <thead>
            <tr>
              <th>{tr("rosCoaf.workspace.rosId" as MessageKey)}</th>
              <th>{tr("rosCoaf.workspace.owner" as MessageKey)}</th>
              <th>{tr("rosCoaf.workspace.priority" as MessageKey)}</th>
              <th>{tr("rosCoaf.workspace.deadline" as MessageKey)}</th>
              <th>{tr("rosCoaf.workspace.urgency" as MessageKey)}</th>
              <th>{tr("rosCoaf.workspace.regulatoryDeadline" as MessageKey)}</th>
              <th>{tr("rosCoaf.workspace.slaLabel" as MessageKey)}</th>
              <th>{tr("rosCoaf.workspace.status" as MessageKey)}</th>
              <th>{tr("rosCoaf.workspace.sourceLabel" as MessageKey)}</th>
              <th>{tr("rosCoaf.workspace.actions" as MessageKey)}</th>
            </tr>
          </thead>
          <tbody>
            {filteredWorkspaceRecords.length ? (
              filteredWorkspaceRecords.map((record) => {
                const urgency = getUrgency(record);
                return (
                  <tr key={record.rosId} data-testid={`roscoaf-workspace-row-${record.rosId}`}>
                    <td>
                      <strong>{record.rosId}</strong>
                      {record.caseId ? <div className="otc-muted">{record.caseId}</div> : null}
                    </td>
                    <td>{record.owner || tr("rosCoaf.workspace.unassigned" as MessageKey)}</td>
                    <td data-testid={`roscoaf-workspace-priority-${record.rosId}`}>{renderPriorityPill(record.priority)}</td>
                    <td data-testid={`roscoaf-workspace-local-deadline-${record.rosId}`}>
                      {formatOptionalDateValue(record.localDeadline, tr("rosCoaf.workspace.noDeadline" as MessageKey))}
                    </td>
                    <td>
                      <Pill tone={formatUrgencyTone(urgency)}>{tr(`rosCoaf.urgency.${urgency}` as MessageKey)}</Pill>
                    </td>
                    <td data-testid={`roscoaf-workspace-submission-deadline-${record.rosId}`}>
                      {formatOptionalDateValue(record.submissionDeadline, tr("rosCoaf.history.notAvailable" as MessageKey))}
                    </td>
                    <td data-testid={`roscoaf-workspace-sla-${record.rosId}`}>
                      {renderSlaPill(getRegulatorySlaState(record))}
                    </td>
                    <td data-testid={`roscoaf-workspace-phase-${record.rosId}`}>
                      <div className="otc-stack">
                        {renderPhasePill(record.status)}
                        <div className="otc-muted">{record.status}</div>
                      </div>
                    </td>
                    <td data-testid={`roscoaf-workspace-source-${record.rosId}`}>{renderSourcePill(record.source)}</td>
                    <td>
                      <div className="otc-controls">
                        <button className="otc-button" type="button" onClick={() => hydrateWorkspaceRecord(record)}>
                          {tr("rosCoaf.workspace.load" as MessageKey)}
                        </button>
                        <button className="otc-button otc-button--ghost" type="button" onClick={() => setTimelineRosId(record.rosId)}>
                          {tr("rosCoaf.workspace.timeline.open" as MessageKey)}
                        </button>
                        {buildRosContextLinks(
                          buildRosOperationalContext({
                            caseId: record.caseId,
                            reportId: record.reportId,
                            rosId: record.rosId
                          }),
                          {
                            case: "rosCoaf.workspace.openCase",
                            audit: "rosCoaf.workspace.openAudit",
                            evidence: "rosCoaf.workspace.openEvidence"
                          }
                        ).map((link: OperationalContextLink & { labelKey: MessageKey }) => (
                          <a key={`workspace-${record.rosId}-${link.testIdSuffix}`} className="otc-button otc-button--ghost" href={link.href}>
                            {tr(link.labelKey)}
                          </a>
                        ))}
                        {buildReportDownloadUrl(record.reportId, record.createdAt, record.caseId) ? (
                          <a className="otc-button otc-button--ghost" href={buildReportDownloadUrl(record.reportId, record.createdAt, record.caseId) ?? undefined}>
                            {tr("rosCoaf.workspace.downloadDraft" as MessageKey)}
                          </a>
                        ) : null}
                        {record.source === "local" ? (
                          <button className="otc-button otc-button--ghost" type="button" onClick={() => removeWorkspaceRecord(record.rosId)}>
                            {tr("rosCoaf.workspace.remove" as MessageKey)}
                          </button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={10} className="otc-muted">
                  {tr("rosCoaf.workspace.empty" as MessageKey)}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Panel>

      <Panel title={tr("rosCoaf.detail.title" as MessageKey)} description={tr("rosCoaf.detail.description" as MessageKey)}>
        {!timelineRosId.trim() ? (
          <Message>{tr("rosCoaf.detail.empty" as MessageKey)}</Message>
        ) : officialDetailLoading ? (
          <Message>{tr("rosCoaf.detail.loading" as MessageKey)}</Message>
        ) : officialDetailError ? (
          <Message>{officialDetailError}</Message>
        ) : officialDetail ? (
          <div className="otc-stack">
            <div className="otc-controls">
              <a
                className="otc-button"
                href={`/evidence?domain=ros&resource_type=ros_record&resource_id=${encodeURIComponent(
                  officialDetail.ros_id
                )}${officialDetail.report_id ? `&report_id=${encodeURIComponent(officialDetail.report_id)}` : ""}`}
              >
                {tr("rosCoaf.workspace.openEvidence" as MessageKey)}
              </a>
              {officialDetail.report_id ? (
                <a
                  className="otc-button otc-button--ghost"
                  href={`/reports?history_report_id=${encodeURIComponent(officialDetail.report_id)}`}
                >
                  {tr("rosCoaf.detail.openReport" as MessageKey)}
                </a>
              ) : null}
              <button
                type="button"
                className="otc-button otc-button--ghost"
                onClick={() => {
                  void downloadRegulatoryDossier();
                }}
                disabled={exportingRegulatoryDossier}
                data-testid="roscoaf-detail-export-dossier"
              >
                {exportingRegulatoryDossier
                  ? tr("rosCoaf.detail.exportingDossier" as MessageKey)
                  : tr("rosCoaf.detail.exportDossier" as MessageKey)}
              </button>
              {buildRosContextLinks(
                buildRosOperationalContext({
                  caseId: officialDetail.case_id ?? "",
                  reportId: officialDetail.report_id,
                  rosId: officialDetail.ros_id
                }),
                {
                  case: "rosCoaf.workspace.openCase",
                  audit: "rosCoaf.workspace.openAudit",
                  evidence: "rosCoaf.workspace.openEvidence"
                }
              ).map((link: OperationalContextLink & { labelKey: MessageKey }) => (
                link.kind === "evidence" ? null :
                <a key={`detail-${link.testIdSuffix}`} className="otc-button otc-button--ghost" href={link.href}>
                  {tr(link.labelKey)}
                </a>
              ))}
            </div>
            {renderOfficialDetailTable(officialDetail)}
            {unifiedRegulatoryTimeline.length ? (
              renderRegulatoryTimelinePanel(unifiedRegulatoryTimeline)
            ) : null}
            {dossierDownloadHistory.length ? (
              renderDossierHistoryMetrics(dossierHistorySummary)
            ) : null}
            {dossierDownloadHistory.length ? (
              renderDossierHistoryPanel(dossierDownloadHistory, officialDetail.ros_id, officialDetail.report_id)
            ) : null}
            {officialDetail.audit?.length ? renderOfficialAuditTable(officialDetail.audit) : null}
          </div>
        ) : (
          <Message>{tr("rosCoaf.detail.empty" as MessageKey)}</Message>
        )}
      </Panel>

      <WorkItemTimelinePanel
        state={!selectedTimelineRecord ? "empty_selection" : !selectedTimelineRecord.workItemId ? "local_only" : "ready"}
        summary={
          selectedTimelineRecord
            ? tr("rosCoaf.workspace.timeline.summary" as MessageKey, {
                rosId: selectedTimelineRecord.rosId,
                phase: tr(`rosCoaf.workspace.phase.${mapRosStatusToPhase(selectedTimelineRecord.status)}` as MessageKey)
              })
            : null
        }
        contextBadges={timelineContextBadges}
        localOnlyHint={selectedTimelineRecord ? tr("rosCoaf.workspace.timeline.localHint" as MessageKey) : null}
        labels={workItemTimelineLabels}
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
          formatDate={(value) => formatDate(value, locale)}
        formatEventLabel={formatTimelineEvent}
      />

      <Panel title={tr("rosCoaf.approve.title" as MessageKey)} description={tr("rosCoaf.approve.description" as MessageKey)}>
        <form className="otc-stack" onSubmit={onApprove}>
          <div className="otc-grid otc-grid--counterparty-form">
            <label className="otc-field">
              {tr("rosCoaf.approve.rosId" as MessageKey)}
              <input className="otc-input" data-testid="roscoaf-approve-ros-id" value={approveRosId} onChange={(event) => setApproveRosId(event.target.value)} required />
            </label>
            <label className="otc-field">
              {tr("rosCoaf.approve.decision" as MessageKey)}
              <select className="otc-select" value={approved ? "approve" : "reject"} onChange={(event) => setApproved(event.target.value === "approve")}>
                <option value="approve">{tr("rosCoaf.approve.approve" as MessageKey)}</option>
                <option value="reject">{tr("rosCoaf.approve.reject" as MessageKey)}</option>
              </select>
            </label>
            {!approved ? (
              <label className="otc-field">
                {tr("rosCoaf.approve.rejectionReason" as MessageKey)}
                <input className="otc-input" value={rejectionReason} onChange={(event) => setRejectionReason(event.target.value)} />
              </label>
            ) : null}
          </div>
          <div className="otc-controls">
            <button
              className="otc-button otc-button--accent"
              type="submit"
              data-testid="roscoaf-approve-btn"
              disabled={approving || syncingWorkspace || !canApproveDecision || !canApproveRole}
            >
              {approving ? tr("rosCoaf.approve.submitting" as MessageKey) : tr("rosCoaf.approve.submit" as MessageKey)}
            </button>
            {buildRosContextLinks(
              buildRosOperationalContext({
                caseId,
                reportId: draft?.report_id ?? "",
                rosId: approveRosId
              }),
              {
                case: "rosCoaf.approve.openCase",
                audit: "rosCoaf.approve.openAudit",
                evidence: "rosCoaf.approve.openEvidence"
              }
            ).map((link: OperationalContextLink & { labelKey: MessageKey }) => (
              <a key={`approve-${link.testIdSuffix}`} className="otc-link-button" href={link.href}>
                {tr(link.labelKey)}
              </a>
            ))}
          </div>
        </form>
      </Panel>

      <Panel title={tr("rosCoaf.submitted.title" as MessageKey)} description={tr("rosCoaf.submitted.description" as MessageKey)}>
        <form className="otc-stack" onSubmit={onSubmitted}>
          <div className="otc-grid otc-grid--counterparty-form">
            <label className="otc-field">
              {tr("rosCoaf.submitted.rosId" as MessageKey)}
              <input className="otc-input" data-testid="roscoaf-submitted-ros-id" value={submitRosId} onChange={(event) => setSubmitRosId(event.target.value)} required />
            </label>
            <label className="otc-field">
              {tr("rosCoaf.submitted.protocol" as MessageKey)}
              <input className="otc-input" data-testid="roscoaf-protocol" value={coafProtocolNumber} onChange={(event) => setCoafProtocolNumber(event.target.value)} required />
            </label>
            <label className="otc-field">
              {tr("rosCoaf.submitted.receiptHash" as MessageKey)}
              <input className="otc-input" value={coafReceiptHash} onChange={(event) => setCoafReceiptHash(event.target.value)} />
            </label>
          </div>
          <div className="otc-controls">
            <button
              className="otc-button otc-button--accent"
              type="submit"
              data-testid="roscoaf-submitted-btn"
              disabled={submitting || syncingWorkspace || !canSubmitRole}
            >
              {submitting ? tr("rosCoaf.submitted.submitting" as MessageKey) : tr("rosCoaf.submitted.submit" as MessageKey)}
            </button>
            {buildRosContextLinks(
              buildRosOperationalContext({
                caseId,
                reportId: draft?.report_id ?? "",
                rosId: submitRosId
              }),
              {
                case: "rosCoaf.submitted.openCase",
                audit: "rosCoaf.submitted.openAudit",
                evidence: "rosCoaf.submitted.openEvidence"
              }
            ).map((link: OperationalContextLink & { labelKey: MessageKey }) => (
              <a key={`submitted-${link.testIdSuffix}`} className="otc-link-button" href={link.href}>
                {tr(link.labelKey)}
              </a>
            ))}
          </div>
        </form>
      </Panel>

      <Panel title={tr("rosCoaf.debug.title" as MessageKey)} description={tr("rosCoaf.debug.description" as MessageKey)}>
        {draft || approval || submission ? (
          <CodeBlock>{JSON.stringify({ draft, approval, submission }, null, 2)}</CodeBlock>
        ) : (
          <Message>{tr("rosCoaf.debug.empty" as MessageKey)}</Message>
        )}
      </Panel>

      {error ? <Message tone="error">{error}</Message> : null}
      {notice ? <Message tone="success">{notice}</Message> : null}

      <Panel title={tr("rosCoaf.history.title" as MessageKey)} description={tr("rosCoaf.history.description" as MessageKey)}>
        {workspaceRecords.length ? (
          <table className="otc-table otc-table--spaced">
            <thead>
              <tr>
                <th>{tr("rosCoaf.history.rosId" as MessageKey)}</th>
                <th>{tr("rosCoaf.history.caseId" as MessageKey)}</th>
                <th>{tr("rosCoaf.history.status" as MessageKey)}</th>
                <th>{tr("rosCoaf.history.phase" as MessageKey)}</th>
                <th>{tr("rosCoaf.history.source" as MessageKey)}</th>
                <th>{tr("rosCoaf.history.coafProtocol" as MessageKey)}</th>
                <th>{tr("rosCoaf.history.receiptHash" as MessageKey)}</th>
                <th>{tr("rosCoaf.history.regulatoryDeadline" as MessageKey)}</th>
                <th>{tr("rosCoaf.history.sla" as MessageKey)}</th>
                <th>{tr("rosCoaf.history.lastAction" as MessageKey)}</th>
              </tr>
            </thead>
            <tbody>
              {workspaceRecords
                .slice()
                .sort((a, b) => b.lastActionAt.localeCompare(a.lastActionAt))
                .slice(0, 100)
                .map((record) => (
                  <tr
                    key={record.rosId}
                    data-testid={`roscoaf-history-row-${record.rosId}`}
                    className={timelineRosId === record.rosId ? "otc-row-selected otc-row-clickable" : "otc-row-clickable"}
                    onClick={() => setTimelineRosId(record.rosId)}
                  >
                    <td><span className="otc-mono">{record.rosId}</span></td>
                    <td>{record.caseId || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
                    <td>
                      <Pill tone={formatPhaseTone(record.status)}>{record.status}</Pill>
                    </td>
                    <td data-testid={`roscoaf-history-phase-${record.rosId}`}>
                      {renderPhasePill(record.status)}
                    </td>
                    <td data-testid={`roscoaf-history-source-${record.rosId}`}>
                      {renderSourcePill(record.source)}
                    </td>
                    <td>{record.coafProtocolNumber || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
                    <td>{record.coafReceiptHash || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
                    <td data-testid={`roscoaf-history-submission-deadline-${record.rosId}`}>
                      {formatOptionalDateValue(record.submissionDeadline, tr("rosCoaf.history.notAvailable" as MessageKey))}
                    </td>
                    <td data-testid={`roscoaf-history-sla-${record.rosId}`}>
                      {renderSlaPill(getRegulatorySlaState(record))}
                    </td>
                    <td data-testid={`roscoaf-history-last-action-${record.rosId}`}>{formatDateValue(record.lastActionAt)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        ) : (
          <Message>{tr("rosCoaf.history.empty" as MessageKey)}</Message>
        )}
      </Panel>
    </AppShell>
  );
}

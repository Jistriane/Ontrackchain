"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

import { useI18n } from "../../components/i18n-provider";
import { WorkItemTimelinePanel } from "../../components/work-item-timeline-panel";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { buildWorkItemTimelineLabels } from "../lib/work-item-timeline-labels";
import { createWorkItemComment, fetchWorkItemTimeline } from "../lib/work-item-timeline-client";
import { fetchAuthContext, resolveOwnerUserId, type AuthContext } from "../lib/ownership";
import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import type { MessageKey } from "../lib/i18n";
import { formatTimelineEvent, type WorkCommentResponse, type WorkItemTimelineResponse } from "../lib/work-item-timeline";
import {
  buildAuditLogQuery,
  extractAuditApiError,
  type AuditLogEntry,
  type AuditLogQueryFilters,
  type AuditLogsResponse
} from "../lib/audit-log";
import {
  buildAuditHref,
  buildBlocksHref,
  buildCaseHref,
  buildCounterpartyHref,
  buildInvestigateHref,
  buildReportsHref,
  buildRosHref,
  buildSanctionsHref,
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

type WorkspacePriority = "critical" | "high" | "normal";
type WorkspaceStatus = "queued" | "reviewing" | "sealed";
type WorkspaceSource = "server" | "local";
type WorkItemQueueStatus = "UNDER_REVIEW" | "ESCALATED" | "READY" | "APPROVED" | "SUBMITTED" | "CLOSED" | "REJECTED";

type WorkItemResponse = {
  id: string;
  resource_id: string;
  owner_user_id?: string | null;
  queue_status: WorkItemQueueStatus;
  priority: WorkspacePriority;
  due_at: string | null;
  note: string | null;
  metadata: Record<string, unknown>;
  last_activity_at: string;
  updated_at: string;
};

type WorkItemListResponse = {
  data: WorkItemResponse[];
};

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

const STORAGE_KEY = "otc-evidence-workspace";
const WORKSPACE_PAGE_LIMIT = 100;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

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
  }
];

function formatDate(value: string | null | undefined) {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(parsed);
}

function isUuidLike(value: string | null | undefined) {
  return Boolean(value && UUID_PATTERN.test(value.trim()));
}

function toDateTimeLocalValue(value: string | null | undefined) {
  if (!value) {
    return "";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }

  const year = parsed.getFullYear();
  const month = `${parsed.getMonth() + 1}`.padStart(2, "0");
  const day = `${parsed.getDate()}`.padStart(2, "0");
  const hours = `${parsed.getHours()}`.padStart(2, "0");
  const minutes = `${parsed.getMinutes()}`.padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function toApiDueAt(value: string) {
  const normalized = value.trim();
  if (!normalized) {
    return null;
  }

  const parsed = new Date(normalized);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return parsed.toISOString();
}

function readMetadataString(metadata: Record<string, unknown>, key: string) {
  const value = metadata[key];
  return typeof value === "string" ? value : "";
}

function normalizeLegacyStatus(value: unknown): WorkspaceStatus {
  if (value === "queued" || value === "reviewing" || value === "sealed") {
    return value;
  }
  return "queued";
}

function loadWorkspace() {
  if (typeof window === "undefined") {
    return [] as EvidenceWorkspaceRecord[];
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed)
      ? parsed.map((entry) => {
          const record = (entry ?? {}) as Partial<EvidenceWorkspaceRecord>;
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
            workspaceStatus: normalizeLegacyStatus(record.workspaceStatus),
            note: typeof record.note === "string" ? record.note : "",
            lastActionAt: typeof record.lastActionAt === "string" ? record.lastActionAt : ""
          };
        })
      : [];
  } catch {
    return [];
  }
}

function saveWorkspace(records: EvidenceWorkspaceRecord[]) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
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

  return [merged, ...current.filter((entry) => entry.eventId !== next.eventId)].sort((left, right) =>
    (right.lastActionAt || "").localeCompare(left.lastActionAt || "")
  );
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

  return merged.sort((left, right) => (right.lastActionAt || "").localeCompare(left.lastActionAt || ""));
}

function mapQueueStatusToWorkspaceStatus(status: WorkItemQueueStatus): WorkspaceStatus {
  if (status === "READY" || status === "APPROVED" || status === "SUBMITTED" || status === "CLOSED") {
    return "sealed";
  }
  return "reviewing";
}

function mapWorkItemToWorkspaceRecord(item: WorkItemResponse): EvidenceWorkspaceRecord {
  const metadata = item.metadata ?? {};
  const eventId = readMetadataString(metadata, "event_id") || item.resource_id;
  return {
    workItemId: item.id,
    source: "server",
    eventId,
    action: readMetadataString(metadata, "audit_action"),
    resourceType: readMetadataString(metadata, "audit_resource_type"),
    resourceId: readMetadataString(metadata, "audit_resource_id"),
    caseId: readMetadataString(metadata, "case_id"),
    requestId: readMetadataString(metadata, "request_id"),
    reportId: readMetadataString(metadata, "report_id"),
    fileHash: readMetadataString(metadata, "file_hash_sha256"),
    owner: readMetadataString(metadata, "owner_label") || item.owner_user_id || "",
    priority: item.priority,
    localDeadline: toDateTimeLocalValue(item.due_at),
    workspaceStatus: normalizeLegacyStatus(metadata["local_workspace_status"]) || mapQueueStatusToWorkspaceStatus(item.queue_status),
    note: item.note ?? readMetadataString(metadata, "note"),
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

export default function EvidenceTrailPage() {
  const { t } = useI18n();
  const searchParams = useSearchParams();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);
  const [filters, setFilters] = useState<EvidenceFilters>(DEFAULT_FILTERS);
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [count, setCount] = useState(0);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [syncingWorkspace, setSyncingWorkspace] = useState(false);
  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);
  const [workspace, setWorkspace] = useState<EvidenceWorkspaceRecord[]>([]);
  const [owner, setOwner] = useState("");
  const [priority, setPriority] = useState<WorkspacePriority>("normal");
  const [localDeadline, setLocalDeadline] = useState("");
  const [workspaceStatus, setWorkspaceStatus] = useState<WorkspaceStatus>("queued");
  const [workspaceNote, setWorkspaceNote] = useState("");
  const [timelineEventId, setTimelineEventId] = useState("");
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineError, setTimelineError] = useState<string | null>(null);
  const [timelineData, setTimelineData] = useState<WorkItemTimelineResponse<WorkItemResponse> | null>(null);
  const [commentType, setCommentType] = useState<WorkCommentResponse["comment_type"]>("note");
  const [commentBody, setCommentBody] = useState("");
  const [commentSubmitting, setCommentSubmitting] = useState(false);
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
  const workspaceByEventId = useMemo(() => new Map(workspace.map((record) => [record.eventId, record])), [workspace]);
  const selectedTimelineRecord = timelineEventId ? workspaceByEventId.get(timelineEventId) ?? null : null;

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
    setSelectedLog((current) => rows.find((entry) => entry.id === current?.id) ?? rows[0] ?? null);
    setLoading(false);
  }

  async function loadTimeline(workItemId: string) {
    setTimelineLoading(true);
    setTimelineError(null);
    const result = await fetchWorkItemTimeline<WorkItemResponse>(workItemId);
    if (!result.ok) {
      setTimelineData(null);
      setTimelineError(resolveApiErrorMessage(t, result.error, tr("evidenceTrail.workspace.timeline.errorLoad" as MessageKey)));
      setTimelineLoading(false);
      return;
    }

    setTimelineData(result.data);
    setTimelineLoading(false);
  }

  async function loadOperationalWorkspace(localRecords: EvidenceWorkspaceRecord[]) {
    const res = await fetch(
      `/api/app/operations/work-items?module=evidence&resource_type=evidence_event&limit=${WORKSPACE_PAGE_LIMIT}`,
      { cache: "no-store" }
    );
    const data = (await res.json().catch(() => null)) as WorkItemListResponse | { error?: string; detail?: unknown } | null;
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
    saveWorkspace(workspace);
  }, [workspace]);

  useEffect(() => {
    if (!workspace.length) {
      setTimelineEventId("");
      setTimelineData(null);
      setTimelineError(null);
      return;
    }
    if (!timelineEventId || !workspace.some((entry) => entry.eventId === timelineEventId)) {
      const firstServerRecord = workspace.find((entry) => Boolean(entry.workItemId)) ?? workspace[0];
      setTimelineEventId(firstServerRecord.eventId);
    }
  }, [timelineEventId, workspace]);

  useEffect(() => {
    if (!selectedLog) {
      return;
    }
    const currentRecord = workspace.find((entry) => entry.eventId === selectedLog.id);
    if (!currentRecord) {
      return;
    }
    setOwner(currentRecord.owner);
    setPriority(currentRecord.priority);
    setLocalDeadline(currentRecord.localDeadline);
    setWorkspaceStatus(currentRecord.workspaceStatus);
    setWorkspaceNote(currentRecord.note);
  }, [selectedLog, workspace]);

  useEffect(() => {
    if (!selectedTimelineRecord?.workItemId) {
      setTimelineData(null);
      setTimelineError(null);
      return;
    }
    loadTimeline(selectedTimelineRecord.workItemId).catch(() => {
      setTimelineData(null);
      setTimelineError(tr("evidenceTrail.workspace.timeline.errorLoad" as MessageKey));
      setTimelineLoading(false);
    });
  }, [selectedTimelineRecord?.workItemId, t]);

  function updateFilter<K extends keyof EvidenceFilters>(key: K, value: EvidenceFilters[K]) {
    setFilters((current) => ({ ...current, [key]: value }));
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
      const disposition = res.headers.get("content-disposition");
      const filenameMatch = disposition?.match(/filename="([^"]+)"/);
      link.href = href;
      link.download = filenameMatch?.[1] ?? "ontrackchain-evidence-bundle.json";
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

  function trackSelectedEvent() {
    if (!selectedLog || !selectedContext) {
      return;
    }
    void (async () => {
      const draftRecord: EvidenceWorkspaceRecord = {
        workItemId: workspace.find((entry) => entry.eventId === selectedLog.id)?.workItemId,
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
      setWorkspace((current) => upsertWorkspaceRecord(current, draftRecord));
      setTimelineEventId(draftRecord.eventId);
      if (!isUuidLike(selectedLog.id)) {
        setNotice(tr("evidenceTrail.workspace.noticeTrackedLocalOnly" as MessageKey, { eventId: selectedLog.id }));
        return;
      }

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
    const matchingLog = logs.find((entry) => entry.id === record.eventId);
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

  async function syncWorkspaceRecord(record: EvidenceWorkspaceRecord, nextStatus?: WorkspaceStatus) {
    if (!isUuidLike(record.eventId)) {
      throw new Error(tr("evidenceTrail.workspace.errorSyncMissingEventId" as MessageKey));
    }

    const ownerUserId = resolveOwnerUserId({
      ownerLabel: record.owner,
      linkedUserId: authContext?.linked_user_id,
      isUuidLike
    });

    const localStatus = nextStatus ?? record.workspaceStatus;
    const queueStatus: WorkItemQueueStatus = localStatus === "sealed" ? "CLOSED" : "UNDER_REVIEW";
    const metadata = {
      event_id: record.eventId,
      audit_action: record.action,
      audit_resource_type: record.resourceType,
      audit_resource_id: record.resourceId,
      case_id: record.caseId,
      request_id: record.requestId,
      report_id: record.reportId,
      file_hash_sha256: record.fileHash,
      owner_user_id: ownerUserId,
      owner_label: record.owner,
      local_workspace_status: localStatus,
      note: record.note
    };
    const requestBody = record.workItemId
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
          resource_id: record.eventId,
          ...(isUuidLike(record.caseId) ? { case_id: record.caseId.trim() } : {}),
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
    const data = (await res.json().catch(() => null)) as WorkItemResponse | { error?: string; detail?: unknown } | null;
    setSyncingWorkspace(false);
    if (!res.ok) {
      throw new Error(resolveApiErrorMessage(t, data, tr("evidenceTrail.workspace.errorSync" as MessageKey)));
    }

    const nextRecord = mapWorkItemToWorkspaceRecord(data as WorkItemResponse);
    setWorkspace((current) => upsertWorkspaceRecord(current, nextRecord));
    if (timelineEventId === nextRecord.eventId && nextRecord.workItemId) {
      await loadTimeline(nextRecord.workItemId);
    }
    return nextRecord;
  }

  async function submitTimelineComment() {
    if (!selectedTimelineRecord?.workItemId) {
      setTimelineError(tr("evidenceTrail.workspace.timeline.emptyLocal" as MessageKey));
      return;
    }
    if (!commentBody.trim()) {
      setTimelineError(tr("evidenceTrail.workspace.timeline.commentEmpty" as MessageKey));
      return;
    }

    setCommentSubmitting(true);
    setTimelineError(null);
    const result = await createWorkItemComment(selectedTimelineRecord.workItemId, {
      comment_type: commentType,
      body: commentBody.trim()
    });
    if (!result.ok) {
      setTimelineError(resolveApiErrorMessage(t, result.error, tr("evidenceTrail.workspace.timeline.errorComment" as MessageKey)));
      setCommentSubmitting(false);
      return;
    }

    setCommentBody("");
    setCommentType("note");
    await loadTimeline(selectedTimelineRecord.workItemId);
    setNotice(tr("evidenceTrail.workspace.timeline.commentSaved" as MessageKey));
    setCommentSubmitting(false);
  }

  function updateWorkspaceStatus(eventId: string, nextStatus: WorkspaceStatus) {
    void (async () => {
      const currentRecord = workspace.find((entry) => entry.eventId === eventId);
      if (!currentRecord) {
        return;
      }

      const draftRecord = { ...currentRecord, workspaceStatus: nextStatus, lastActionAt: new Date().toISOString() };
      setWorkspace((current) =>
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
    setWorkspace((current) => current.filter((entry) => entry.eventId !== eventId));
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
            <select className="otc-select" value={filters.action} onChange={(event) => updateFilter("action", event.target.value)}>
              <option value="">{tr("evidenceTrail.filters.all" as MessageKey)}</option>
              <option value="compliance_sanctions_checked">compliance_sanctions_checked</option>
              <option value="preventive_block_lifted">preventive_block_lifted</option>
              <option value="counterparty_created">counterparty_created</option>
              <option value="coaf_report_generated">coaf_report_generated</option>
              <option value="coaf_report_approved">coaf_report_approved</option>
              <option value="coaf_report_rejected">coaf_report_rejected</option>
              <option value="coaf_report_submitted_manual">coaf_report_submitted_manual</option>
              <option value="report_generated">report_generated</option>
              <option value="report_downloaded">report_downloaded</option>
            </select>
          </label>
          <label className="otc-field">
            {tr("evidenceTrail.filters.resourceType" as MessageKey)}
            <select className="otc-select" value={filters.resourceType} onChange={(event) => updateFilter("resourceType", event.target.value)}>
              <option value="">{tr("evidenceTrail.filters.all" as MessageKey)}</option>
              <option value="report">report</option>
              <option value="ros_record">ros_record</option>
              <option value="preventive_block">preventive_block</option>
              <option value="counterparty">counterparty</option>
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

      <Panel title={tr("evidenceTrail.workspace.title" as MessageKey)} description={tr("evidenceTrail.workspace.description" as MessageKey)}>
        <div className="otc-grid otc-grid--counterparty-form">
          <label className="otc-field">
            {tr("evidenceTrail.workspace.filters.owner" as MessageKey)}
            <input className="otc-input" value={owner} onChange={(event) => setOwner(event.target.value)} />
          </label>
          <label className="otc-field">
            {tr("evidenceTrail.workspace.filters.priority" as MessageKey)}
            <select className="otc-select" value={priority} onChange={(event) => setPriority(event.target.value as WorkspacePriority)}>
              <option value="critical">{tr("common.priority.critical" as MessageKey)}</option>
              <option value="high">{tr("common.priority.high" as MessageKey)}</option>
              <option value="normal">{tr("common.priority.normal" as MessageKey)}</option>
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
                <th>{tr("evidenceTrail.workspace.table.actions" as MessageKey)}</th>
              </tr>
            </thead>
            <tbody>
              {workspace.map((record) => (
                <tr key={record.eventId}>
                  <td>
                    <strong>{record.eventId}</strong>
                    <div className="otc-muted">{record.action}</div>
                    <div className="otc-muted">
                      <Pill tone={record.source === "server" ? "success" : "warning"}>
                        {tr(`evidenceTrail.workspace.source.${record.source}` as MessageKey)}
                      </Pill>
                    </div>
                    {record.note ? <div className="otc-muted">{record.note}</div> : null}
                  </td>
                  <td>{record.resourceType}{record.resourceId ? ` • ${record.resourceId}` : ""}</td>
                  <td>{record.owner || tr("evidenceTrail.notAvailable" as MessageKey)}</td>
                  <td>{tr(`common.priority.${record.priority}` as MessageKey)}</td>
                  <td>
                    {record.localDeadline ? formatDate(record.localDeadline) ?? record.localDeadline : tr("evidenceTrail.notAvailable" as MessageKey)}
                    <div className="otc-muted">{tr(`evidenceTrail.workspace.urgency.${getWorkspaceUrgency(record)}` as MessageKey)}</div>
                  </td>
                  <td>{tr(`evidenceTrail.workspace.status.${record.workspaceStatus}` as MessageKey)}</td>
                  <td>
                    <div className="otc-controls">
                      <button type="button" className="otc-button otc-button--ghost" onClick={() => hydrateWorkspaceRecord(record)}>
                        {tr("evidenceTrail.workspace.table.load" as MessageKey)}
                      </button>
                      <button type="button" className="otc-button otc-button--ghost" onClick={() => setTimelineEventId(record.eventId)}>
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
          void submitTimelineComment();
        }}
        onRefresh={
          selectedTimelineRecord?.workItemId
            ? () => {
                void loadTimeline(selectedTimelineRecord.workItemId!);
              }
            : undefined
        }
        formatDate={formatDate}
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
                      <strong>{entry.action}</strong>
                      <span className="otc-muted otc-evidence-log__meta">
                        {entry.resource_type}{entry.resource_id ? ` • ${entry.resource_id}` : ""}
                      </span>
                      <span className="otc-muted otc-evidence-log__meta otc-evidence-log__meta--tight">
                        request_id: {entry.request_id ?? tr("evidenceTrail.notAvailable" as MessageKey)}
                      </span>
                      <span className="otc-muted otc-evidence-log__meta otc-evidence-log__meta--tight">
                        {formatDate(entry.created_at) ?? tr("evidenceTrail.notAvailable" as MessageKey)}
                      </span>
                    </span>
                    <span className="otc-controls">
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
            <div className="otc-stack">
              <div className="otc-kv">
                <div className="otc-kv__row">
                  <span className="otc-kv__key">{tr("evidenceTrail.details.action" as MessageKey)}</span>
                  <span className="otc-kv__value">{selectedLog.action}</span>
                </div>
                <div className="otc-kv__row">
                  <span className="otc-kv__key">{tr("evidenceTrail.details.resource" as MessageKey)}</span>
                  <span className="otc-kv__value">{selectedLog.resource_type}{selectedLog.resource_id ? ` • ${selectedLog.resource_id}` : ""}</span>
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
              {selectedContext ? (
                <div className="otc-controls otc-controls--spaced">
                  {buildCaseHref(selectedContext.caseId) ? (
                    <a className="otc-button otc-button--ghost" href={buildCaseHref(selectedContext.caseId) ?? undefined}>
                      {tr("evidenceTrail.details.openCase" as MessageKey)}
                    </a>
                  ) : null}
                  <a className="otc-button otc-button--ghost" href={buildAuditHref(selectedContext, { fallbackResourceType: "audit_log" })}>
                    {tr("evidenceTrail.details.openAudit" as MessageKey)}
                  </a>
                  <a className="otc-button otc-button--ghost" href={buildReportsHref(selectedContext)}>
                    {tr("evidenceTrail.details.openReports" as MessageKey)}
                  </a>
                  {buildInvestigateHref(selectedContext) ? (
                    <a className="otc-button otc-button--ghost" href={buildInvestigateHref(selectedContext) ?? undefined}>
                      {tr("evidenceTrail.details.openInvestigate" as MessageKey)}
                    </a>
                  ) : null}
                  {buildSanctionsHref(selectedContext) ? (
                    <a className="otc-button otc-button--ghost" href={buildSanctionsHref(selectedContext) ?? undefined}>
                      {tr("evidenceTrail.details.openSanctions" as MessageKey)}
                    </a>
                  ) : null}
                  {buildBlocksHref(selectedContext) ? (
                    <a className="otc-button otc-button--ghost" href={buildBlocksHref(selectedContext) ?? undefined}>
                      {tr("evidenceTrail.details.openBlocks" as MessageKey)}
                    </a>
                  ) : null}
                  {buildCounterpartyHref(selectedContext) ? (
                    <a className="otc-button otc-button--ghost" href={buildCounterpartyHref(selectedContext) ?? undefined}>
                      {tr("evidenceTrail.details.openCounterparty" as MessageKey)}
                    </a>
                  ) : null}
                  {buildRosHref(selectedContext) ? (
                    <a className="otc-button otc-button--ghost" href={buildRosHref(selectedContext) ?? undefined}>
                      {tr("evidenceTrail.details.openRos" as MessageKey)}
                    </a>
                  ) : null}
                </div>
              ) : null}
              <CodeBlock>{JSON.stringify(selectedLog.metadata, null, 2)}</CodeBlock>
            </div>
          ) : (
            <Message>{tr("evidenceTrail.details.empty" as MessageKey)}</Message>
          )}
        </Panel>
      </section>

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
                    <td>{formatDate(record.lastActionAt) ?? record.lastActionAt}</td>
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

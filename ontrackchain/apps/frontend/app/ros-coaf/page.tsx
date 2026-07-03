"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import { useI18n } from "../../components/i18n-provider";
import { WorkItemTimelinePanel } from "../../components/work-item-timeline-panel";
import type { MessageKey } from "../lib/i18n";
import { fetchAuthContext, resolveOwnerUserId, type AuthContext } from "../lib/ownership";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { buildWorkItemTimelineLabels } from "../lib/work-item-timeline-labels";
import { createWorkItemComment, fetchWorkItemTimeline } from "../lib/work-item-timeline-client";
import { formatTimelineEvent, type WorkCommentResponse, type WorkItemTimelineResponse } from "../lib/work-item-timeline";

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

type WorkspacePriority = "critical" | "high" | "normal";
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
  lastActionAt: string;
};

const STORAGE_KEY = "otc-ros-coaf-workspace";
const WORKSPACE_PAGE_LIMIT = 100;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

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

function loadWorkspace(): RosWorkspaceRecord[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed)
      ? parsed.map((entry) => {
          const record = (entry ?? {}) as Partial<RosWorkspaceRecord>;
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
            lastActionAt: typeof record.lastActionAt === "string" ? record.lastActionAt : ""
          };
        })
      : [];
  } catch {
    return [];
  }
}

function saveWorkspace(records: RosWorkspaceRecord[]) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
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
      lastActionAt: ""
    };

  const merged: RosWorkspaceRecord = {
    ...base,
    ...next,
    lastActionAt: next.lastActionAt ?? new Date().toISOString()
  };

  const withoutCurrent = current.filter((item) => item.rosId !== next.rosId);
  return [merged, ...withoutCurrent].sort((a, b) => (b.lastActionAt || "").localeCompare(a.lastActionAt || ""));
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

  return merged.sort((a, b) => (b.lastActionAt || "").localeCompare(a.lastActionAt || ""));
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

function mapWorkItemToWorkspaceRecord(item: WorkItemResponse): RosWorkspaceRecord {
  const metadata = item.metadata ?? {};
  return {
    workItemId: item.id,
    source: "server",
    rosId: readMetadataString(metadata, "ros_id") || item.resource_id,
    caseId: readMetadataString(metadata, "case_id"),
    owner: readMetadataString(metadata, "owner_label") || item.owner_user_id || "",
    priority: item.priority,
    localDeadline: toDateTimeLocalValue(item.due_at),
    status: readMetadataString(metadata, "ros_status") || mapQueueStatusToRosStatus(item.queue_status),
    reportId: readMetadataString(metadata, "report_id"),
    createdAt: readMetadataString(metadata, "created_at"),
    approvedAt: readMetadataString(metadata, "approved_at"),
    submittedAt: readMetadataString(metadata, "submitted_at"),
    coafProtocolNumber: readMetadataString(metadata, "coaf_protocol_number"),
    coafReceiptHash: item.note ?? readMetadataString(metadata, "coaf_receipt_hash"),
    lastActionAt: item.last_activity_at || item.updated_at
  };
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

function buildAuditHref(caseId: string, reportId: string, rosId: string) {
  const params = new URLSearchParams({
    resource_type: "case",
    resource_id: caseId.trim() || rosId.trim() || reportId.trim()
  });
  if (caseId.trim()) {
    params.set("request_id", caseId.trim());
  }
  if (reportId.trim()) {
    params.set("report_id", reportId.trim());
  }
  return `/audit?${params.toString()}`;
}

function buildEvidenceHref(caseId: string, reportId: string, rosId: string) {
  const params = new URLSearchParams({
    domain: "reports",
    resource_type: "case",
    resource_id: caseId.trim() || rosId.trim() || reportId.trim()
  });
  if (caseId.trim()) {
    params.set("request_id", caseId.trim());
  }
  if (reportId.trim()) {
    params.set("report_id", reportId.trim());
  }
  return `/evidence?${params.toString()}`;
}

export default function RosCoafPage() {
  const { t } = useI18n();
  const searchParams = useSearchParams();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);

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
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineError, setTimelineError] = useState<string | null>(null);
  const [timelineData, setTimelineData] = useState<WorkItemTimelineResponse<WorkItemResponse> | null>(null);
  const [commentType, setCommentType] = useState<WorkCommentResponse["comment_type"]>("note");
  const [commentBody, setCommentBody] = useState("");
  const [commentSubmitting, setCommentSubmitting] = useState(false);

  const canApprove = approved || rejectionReason.trim().length > 0;
  const draftDownloadUrl = useMemo(() => {
    if (!draft?.report_id || !draft?.created_at) return null;
    return buildReportDownloadUrl(draft.report_id, draft.created_at, caseId);
  }, [draft, caseId]);
  const filteredWorkspaceRecords = useMemo(() => {
    return workspaceRecords.filter((record) => {
      const matchesStatus = workspaceFilter === "all" ? true : record.status === workspaceFilter;
      const search = workspaceSearch.trim().toLowerCase();
      const matchesSearch =
        !search ||
        record.rosId.toLowerCase().includes(search) ||
        record.caseId.toLowerCase().includes(search) ||
        record.owner.toLowerCase().includes(search) ||
        record.reportId.toLowerCase().includes(search);
      return matchesStatus && matchesSearch;
    });
  }, [workspaceFilter, workspaceRecords, workspaceSearch]);
  const pendingApprovalCount = useMemo(
    () => workspaceRecords.filter((record) => record.status === "PENDING_APPROVAL").length,
    [workspaceRecords]
  );
  const overdueCount = useMemo(
    () => workspaceRecords.filter((record) => getUrgency(record) === "overdue").length,
    [workspaceRecords]
  );
  const submittedCount = useMemo(
    () => workspaceRecords.filter((record) => record.status === "SUBMITTED_MANUAL").length,
    [workspaceRecords]
  );
  const workspaceById = useMemo(() => new Map(workspaceRecords.map((record) => [record.rosId, record])), [workspaceRecords]);
  const selectedTimelineRecord = timelineRosId ? workspaceById.get(timelineRosId) ?? null : null;

  async function loadTimeline(workItemId: string) {
    setTimelineLoading(true);
    setTimelineError(null);
    const result = await fetchWorkItemTimeline<WorkItemResponse>(workItemId);
    if (!result.ok) {
      setTimelineData(null);
      setTimelineError(resolveApiErrorMessage(t, result.error, tr("rosCoaf.workspace.timeline.errorLoad" as MessageKey)));
      setTimelineLoading(false);
      return;
    }

    setTimelineData(result.data);
    setTimelineLoading(false);
  }

  async function loadOperationalWorkspace(localRecords: RosWorkspaceRecord[]) {
    const res = await fetch(
      `/api/app/operations/work-items?module=ros_coaf&resource_type=ros_record&limit=${WORKSPACE_PAGE_LIMIT}`,
      { cache: "no-store" }
    );
    const data = (await res.json().catch(() => null)) as WorkItemListResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setWorkspaceRecords(localRecords);
      setNotice(tr("rosCoaf.workspace.noticeLoadedLocal" as MessageKey));
      return;
    }

    const items = data && "data" in data && Array.isArray(data.data) ? data.data : [];
    const serverRecords = items.map((item) => mapWorkItemToWorkspaceRecord(item));
    setWorkspaceRecords(mergeWorkspaceRecords(serverRecords, localRecords));
  }

  useEffect(() => {
    const localRecords = loadWorkspace();
    setWorkspaceRecords(localRecords);
    loadOperationalWorkspace(localRecords).catch(() => {
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
      setTimelineData(null);
      setTimelineError(null);
      return;
    }
    if (!timelineRosId || !workspaceRecords.some((record) => record.rosId === timelineRosId)) {
      const firstServerRecord = workspaceRecords.find((record) => Boolean(record.workItemId)) ?? workspaceRecords[0];
      setTimelineRosId(firstServerRecord.rosId);
    }
  }, [timelineRosId, workspaceRecords]);

  useEffect(() => {
    if (!selectedTimelineRecord?.workItemId) {
      setTimelineData(null);
      setTimelineError(null);
      return;
    }
    loadTimeline(selectedTimelineRecord.workItemId).catch(() => {
      setTimelineData(null);
      setTimelineError(tr("rosCoaf.workspace.timeline.errorLoad" as MessageKey));
      setTimelineLoading(false);
    });
  }, [selectedTimelineRecord?.workItemId, t]);

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
  }

  function removeWorkspaceRecord(rosIdToRemove: string) {
    setWorkspaceRecords((current) => current.filter((record) => record.rosId !== rosIdToRemove));
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

    const metadata = {
      ros_id: record.rosId,
      case_id: record.caseId,
      owner_user_id: ownerUserId,
      owner_label: record.owner,
      ros_status: record.status,
      report_id: record.reportId,
      created_at: record.createdAt,
      approved_at: record.approvedAt,
      submitted_at: record.submittedAt,
      coaf_protocol_number: record.coafProtocolNumber,
      coaf_receipt_hash: record.coafReceiptHash
    };
    const requestBody = record.workItemId
      ? {
          ...(ownerUserId ? { owner_user_id: ownerUserId } : {}),
          priority: record.priority,
          queue_status: mapRosStatusToQueueStatus(record.status),
          due_at: toApiDueAt(record.localDeadline),
          title: `ROS/COAF • ${record.rosId}`,
          note: record.coafReceiptHash || null,
          metadata
        }
      : {
          module: "ros_coaf",
          resource_type: "ros_record",
          resource_id: record.rosId,
          ...(isUuidLike(record.caseId) ? { case_id: record.caseId.trim() } : {}),
          ...(ownerUserId ? { owner_user_id: ownerUserId } : {}),
          priority: record.priority,
          queue_status: mapRosStatusToQueueStatus(record.status),
          due_at: toApiDueAt(record.localDeadline),
          title: `ROS/COAF • ${record.rosId}`,
          note: record.coafReceiptHash || null,
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
      throw new Error(resolveApiErrorMessage(t, data, tr("rosCoaf.workspace.errorSync" as MessageKey)));
    }

    const nextRecord = mapWorkItemToWorkspaceRecord(data as WorkItemResponse);
    setWorkspaceRecords((current) => upsertWorkspaceRecord(current, nextRecord));
    if (timelineRosId === nextRecord.rosId && nextRecord.workItemId) {
      await loadTimeline(nextRecord.workItemId);
    }
    return nextRecord;
  }

  async function submitTimelineComment() {
    if (!selectedTimelineRecord?.workItemId) {
      setTimelineError(tr("rosCoaf.workspace.timeline.emptyLocal" as MessageKey));
      return;
    }
    if (!commentBody.trim()) {
      setTimelineError(tr("rosCoaf.workspace.timeline.commentEmpty" as MessageKey));
      return;
    }

    setCommentSubmitting(true);
    setTimelineError(null);
    const result = await createWorkItemComment(selectedTimelineRecord.workItemId, {
      comment_type: commentType,
      body: commentBody.trim()
    });
    if (!result.ok) {
      setTimelineError(resolveApiErrorMessage(t, result.error, tr("rosCoaf.workspace.timeline.errorComment" as MessageKey)));
      setCommentSubmitting(false);
      return;
    }

    setCommentBody("");
    setCommentType("note");
    await loadTimeline(selectedTimelineRecord.workItemId);
    setNotice(tr("rosCoaf.workspace.timeline.commentSaved" as MessageKey));
    setCommentSubmitting(false);
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
      lastActionAt: (data as GenerateRosCoafResponse).created_at
    };
    setWorkspaceRecords((current) => upsertWorkspaceRecord(current, draftRecord));
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
      lastActionAt: (data as ApproveRosCoafResponse).approved_at
    };
    setWorkspaceRecords((current) => upsertWorkspaceRecord(current, draftRecord));
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
      lastActionAt: (data as SubmitRosCoafResponse).submitted_at
    };
    setWorkspaceRecords((current) => upsertWorkspaceRecord(current, draftRecord));
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
            {caseId.trim() ? (
              <a className="otc-link-button" href={`/cases/${caseId.trim()}`}>
                {tr("rosCoaf.generate.openCase" as MessageKey)}
              </a>
            ) : null}
            {draft ? (
              <>
                <a className="otc-link-button" href={buildAuditHref(caseId, draft.report_id, draft.ros_id)}>
                  {tr("rosCoaf.generate.openAudit" as MessageKey)}
                </a>
                <a className="otc-link-button" href={buildEvidenceHref(caseId, draft.report_id, draft.ros_id)}>
                  {tr("rosCoaf.generate.openEvidence" as MessageKey)}
                </a>
              </>
            ) : null}
          </div>
        </form>
      </Panel>

      <Panel title={tr("rosCoaf.workspace.title" as MessageKey)} description={tr("rosCoaf.workspace.description" as MessageKey)}>
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
              <th>{tr("rosCoaf.workspace.status" as MessageKey)}</th>
              <th>{tr("rosCoaf.workspace.actions" as MessageKey)}</th>
            </tr>
          </thead>
          <tbody>
            {filteredWorkspaceRecords.length ? (
              filteredWorkspaceRecords.map((record) => {
                const urgency = getUrgency(record);
                const urgencyTone = urgency === "overdue" ? "danger" : urgency === "due_soon" ? "warning" : undefined;
                return (
                  <tr key={record.rosId}>
                    <td>
                      <strong>{record.rosId}</strong>
                      {record.caseId ? <div className="otc-muted">{record.caseId}</div> : null}
                      <div className="otc-muted">
                        <Pill tone={record.source === "server" ? "success" : "warning"}>
                          {tr(`rosCoaf.workspace.source.${record.source}` as MessageKey)}
                        </Pill>
                      </div>
                    </td>
                    <td>{record.owner || tr("rosCoaf.workspace.unassigned" as MessageKey)}</td>
                    <td>
                      <Pill tone={record.priority === "critical" ? "danger" : record.priority === "high" ? "warning" : undefined}>
                        {tr(`rosCoaf.priority.${record.priority}` as MessageKey)}
                      </Pill>
                    </td>
                    <td>{formatDate(record.localDeadline) ?? tr("rosCoaf.workspace.noDeadline" as MessageKey)}</td>
                    <td>
                      <Pill tone={urgencyTone}>{tr(`rosCoaf.urgency.${urgency}` as MessageKey)}</Pill>
                    </td>
                    <td>{record.status}</td>
                    <td>
                      <div className="otc-controls">
                        <button className="otc-button" type="button" onClick={() => hydrateWorkspaceRecord(record)}>
                          {tr("rosCoaf.workspace.load" as MessageKey)}
                        </button>
                        <button className="otc-button otc-button--ghost" type="button" onClick={() => setTimelineRosId(record.rosId)}>
                          {tr("rosCoaf.workspace.timeline.open" as MessageKey)}
                        </button>
                        {record.caseId ? (
                          <a className="otc-button otc-button--ghost" href={`/cases/${record.caseId}`}>
                            {tr("rosCoaf.workspace.openCase" as MessageKey)}
                          </a>
                        ) : null}
                        <a className="otc-button otc-button--ghost" href={buildAuditHref(record.caseId, record.reportId, record.rosId)}>
                          {tr("rosCoaf.workspace.openAudit" as MessageKey)}
                        </a>
                        <a className="otc-button otc-button--ghost" href={buildEvidenceHref(record.caseId, record.reportId, record.rosId)}>
                          {tr("rosCoaf.workspace.openEvidence" as MessageKey)}
                        </a>
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
                <td colSpan={7} className="otc-muted">
                  {tr("rosCoaf.workspace.empty" as MessageKey)}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Panel>

      <WorkItemTimelinePanel
        state={!selectedTimelineRecord ? "empty_selection" : !selectedTimelineRecord.workItemId ? "local_only" : "ready"}
        summary={selectedTimelineRecord ? tr("rosCoaf.workspace.timeline.summary" as MessageKey, { rosId: selectedTimelineRecord.rosId }) : null}
        labels={buildWorkItemTimelineLabels(tr, "rosCoaf.workspace.timeline")}
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
            <button className="otc-button otc-button--accent" type="submit" data-testid="roscoaf-approve-btn" disabled={approving || syncingWorkspace || !canApprove}>
              {approving ? tr("rosCoaf.approve.submitting" as MessageKey) : tr("rosCoaf.approve.submit" as MessageKey)}
            </button>
            {caseId.trim() ? (
              <a className="otc-link-button" href={`/cases/${caseId.trim()}`}>
                {tr("rosCoaf.approve.openCase" as MessageKey)}
              </a>
            ) : null}
            <a className="otc-link-button" href={buildAuditHref(caseId, draft?.report_id ?? "", approveRosId)}>
              {tr("rosCoaf.approve.openAudit" as MessageKey)}
            </a>
            <a className="otc-link-button" href={buildEvidenceHref(caseId, draft?.report_id ?? "", approveRosId)}>
              {tr("rosCoaf.approve.openEvidence" as MessageKey)}
            </a>
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
            <button className="otc-button otc-button--accent" type="submit" data-testid="roscoaf-submitted-btn" disabled={submitting || syncingWorkspace}>
              {submitting ? tr("rosCoaf.submitted.submitting" as MessageKey) : tr("rosCoaf.submitted.submit" as MessageKey)}
            </button>
            {caseId.trim() ? (
              <a className="otc-link-button" href={`/cases/${caseId.trim()}`}>
                {tr("rosCoaf.submitted.openCase" as MessageKey)}
              </a>
            ) : null}
            <a className="otc-link-button" href={buildAuditHref(caseId, draft?.report_id ?? "", submitRosId)}>
              {tr("rosCoaf.submitted.openAudit" as MessageKey)}
            </a>
            <a className="otc-link-button" href={buildEvidenceHref(caseId, draft?.report_id ?? "", submitRosId)}>
              {tr("rosCoaf.submitted.openEvidence" as MessageKey)}
            </a>
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
                <th>{tr("rosCoaf.history.coafProtocol" as MessageKey)}</th>
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
                    className={timelineRosId === record.rosId ? "otc-row-selected otc-row-clickable" : "otc-row-clickable"}
                    onClick={() => setTimelineRosId(record.rosId)}
                  >
                    <td><span className="otc-mono">{record.rosId}</span></td>
                    <td>{record.caseId || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
                    <td>
                      <Pill tone={record.status === "SUBMITTED_MANUAL" ? "success" : record.status === "REJECTED" ? "danger" : "warning"}>
                        {record.status}
                      </Pill>
                    </td>
                    <td>{record.coafProtocolNumber || tr("rosCoaf.history.notAvailable" as MessageKey)}</td>
                    <td>{formatDate(record.lastActionAt) ?? record.lastActionAt}</td>
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

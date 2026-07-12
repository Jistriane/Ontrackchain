"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useI18n } from "../../components/i18n-provider";
import { WorkItemTimelinePanel } from "../../components/work-item-timeline-panel";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { formatDateTime as formatDate } from "../lib/date-format";
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
  buildReportFormalDossierFilename,
  deriveReportFormalDossierSummary,
  isReportFormalDossierValue,
  REPORT_FORMAL_DOSSIER_SUMMARY_FIELDS,
  type ReportFormalDossierSummaryField
} from "../lib/report-formal-dossier";
import {
  isWorkItemUuidLike as isUuidLike,
  readWorkItemMetadataString,
  resolveWorkItemOwnerDisplay,
  resolveWorkItemWorkspaceStatus,
  type CreateWorkItemRequest,
  type PatchWorkItemRequest,
  type ReportWorkItemMetadata,
  type WorkItemListResponse,
  type WorkItemPriority,
  type WorkItemQueueStatus,
  type WorkItemResponse,
  withCanonicalWorkItemMetadata
} from "../lib/work-items";
import { buildWorkItemTimelineLabels } from "../lib/work-item-timeline-labels";
import { useWorkItemTimeline } from "../lib/use-work-item-timeline";
import { fetchAuthContext, resolveOwnerUserId, type AuthContext } from "../lib/ownership";
import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import type { MessageKey } from "../lib/i18n";
import { formatTimelineEvent } from "../lib/work-item-timeline";

type ReportTypeItem = {
  canonical: string;
  label: string;
  available: boolean;
  cost_credits: number;
  min_plan?: string | null;
  format?: string | null;
  deprecated?: boolean;
};

type ReportTypesResponse = {
  generated_at?: string;
  types: ReportTypeItem[];
};

type CaseRow = {
  id: string;
  status: string;
  target_address: string;
  target_chain: string;
  created_at: string | null;
  completed_at: string | null;
};

type CasesResponse = {
  page: number;
  limit: number;
  data: CaseRow[];
};

type ReportHistoryRow = {
  report_id: string;
  case_id: string | null;
  report_type_requested: string;
  report_type: string;
  content_type: string;
  file_hash_sha256: string | null;
  onchain_hash: string | null;
  created_at: string;
  has_download_audit: boolean;
};

type ReportHistoryResponse = {
  data: ReportHistoryRow[];
  page: number;
  limit: number;
  total: number;
  has_more: boolean;
};

type ReportDetailResponse = {
  report_id: string;
  case_id: string;
  report_type_requested: string;
  report_type: string;
  created_at: string;
  file_hash_sha256: string;
  onchain_hash: string | null;
  content_type: string;
};

type ReportRosCoafRefResponse = {
  report_id: string;
  ros_id: string | null;
};

type WorkspacePriority = WorkItemPriority;
type WorkspaceStatus = "draft" | "in_review" | "ready";
type WorkspaceSource = "server" | "local";
type ReportWorkItemResponse = WorkItemResponse<ReportWorkItemMetadata>;
type ReportWorkItemListResponse = WorkItemListResponse<ReportWorkItemMetadata>;

type ReportWorkspaceRecord = {
  workItemId?: string;
  resourceId: string;
  source: WorkspaceSource;
  caseId: string;
  reportExternalId: string;
  targetAddress: string;
  targetChain: string;
  reportType: string;
  owner: string;
  priority: WorkspacePriority;
  localDeadline: string;
  slaBreached: boolean;
  workspaceStatus: WorkspaceStatus;
  note: string;
  lastActionAt: string;
};

const REPORT_DOSSIER_FIELD_LABEL_KEYS: Record<ReportFormalDossierSummaryField, MessageKey> = {
  packageType: "reports.dossier.packageType",
  classification: "reports.dossier.classification",
  accessPolicy: "reports.dossier.accessPolicy",
  signoffMode: "reports.dossier.signoff",
  anchoringStatus: "reports.dossier.anchor",
  downloadState: "reports.dossier.downloadState",
  custodyState: "reports.dossier.custodyState",
  distributionScope: "reports.dossier.distributionScope",
  retentionClass: "reports.dossier.retentionClass"
};

const STORAGE_KEY = "otc-reports-workspace";
const WORKSPACE_PAGE_LIMIT = 100;

function normalizeWorkspaceStatus(value: unknown): WorkspaceStatus | null {
  if (value === "draft" || value === "in_review" || value === "ready") {
    return value;
  }
  return null;
}

function toPlanRank(plan: string) {
  const normalized = plan.toLowerCase();
  if (normalized === "free") return 0;
  if (normalized === "starter") return 1;
  if (normalized === "professional") return 2;
  if (normalized === "enterprise") return 3;
  return 99;
}

function buildReportOperationalContext(input: {
  caseId: string;
  reportId?: string | null;
  reportType?: string | null;
  address?: string | null;
  chain?: string | null;
}): OperationalContext {
  const caseId = input.caseId.trim();
  return {
    caseId,
    requestId: caseId,
    reportId: input.reportId?.trim() ?? "",
    fileHash: "",
    resourceType: "case",
    resourceId: caseId,
    address: input.address?.trim() ?? "",
    chain: input.chain?.trim() || "ethereum",
    counterpartyId: "",
    legalName: "",
    documentNumber: "",
    rosId: "",
    reportType: input.reportType?.trim() ?? "",
    blockId: ""
  };
}

function buildReportContextLinks(context: OperationalContext) {
  const labelKeyByKind: Partial<Record<OperationalContextLink["kind"], MessageKey>> = {
    case: "reports.cases.table.openCase",
    audit: "reports.cases.table.openAudit",
    evidence: "reports.cases.table.openEvidence",
    investigate: "reports.cases.table.openInvestigate"
  };

  return buildOperationalContextLinks(context, {
    includeEvidence: true,
    evidenceDomain: "reports",
    investigateReportType: context.reportType || undefined
  })
    .filter(
      (link: OperationalContextLink) =>
        link.kind === "case" || link.kind === "audit" || link.kind === "evidence" || link.kind === "investigate"
    )
    .map((link: OperationalContextLink) => ({
      ...link,
      labelKey: labelKeyByKind[link.kind] ?? "reports.cases.table.openCase"
    }));
}

function loadWorkspace() {
  return loadWorkspaceRecords<ReportWorkspaceRecord>(STORAGE_KEY, (record) => {
    const caseId = typeof record.caseId === "string" ? record.caseId : "";
    const source: WorkspaceSource = record.source === "server" ? "server" : "local";
    return {
      workItemId: typeof record.workItemId === "string" ? record.workItemId : undefined,
      resourceId: typeof record.resourceId === "string" ? record.resourceId : caseId,
      source,
      caseId,
      targetAddress: typeof record.targetAddress === "string" ? record.targetAddress : "",
      targetChain: typeof record.targetChain === "string" ? record.targetChain : "",
      reportType: typeof record.reportType === "string" ? record.reportType : "",
      reportExternalId: typeof record.reportExternalId === "string" ? record.reportExternalId : "",
      owner: typeof record.owner === "string" ? record.owner : "",
      priority: record.priority === "critical" || record.priority === "high" || record.priority === "normal" ? record.priority : "normal",
      localDeadline: typeof record.localDeadline === "string" ? record.localDeadline : "",
      slaBreached: record.slaBreached === true,
      workspaceStatus: normalizeWorkspaceStatus(record.workspaceStatus) ?? "draft",
      note: typeof record.note === "string" ? record.note : "",
      lastActionAt: typeof record.lastActionAt === "string" ? record.lastActionAt : ""
    };
  });
}

function buildReportWorkspaceIdentity(input: {
  caseId?: string | null;
  reportExternalId?: string | null;
  workItemId?: string | null;
}) {
  return input.reportExternalId?.trim() || input.caseId?.trim() || input.workItemId?.trim() || "";
}

function isSameReportWorkspaceRecord(
  left: Pick<ReportWorkspaceRecord, "caseId" | "reportExternalId" | "workItemId">,
  right: Pick<ReportWorkspaceRecord, "caseId" | "reportExternalId" | "workItemId">
) {
  const leftReportId = left.reportExternalId.trim();
  const rightReportId = right.reportExternalId.trim();
  if (leftReportId && rightReportId) {
    return leftReportId === rightReportId;
  }
  if (left.caseId.trim() && right.caseId.trim()) {
    return left.caseId.trim() === right.caseId.trim();
  }
  return Boolean(left.workItemId && right.workItemId && left.workItemId === right.workItemId);
}

function findReportWorkspaceRecord(
  records: ReportWorkspaceRecord[],
  input: { caseId?: string | null; reportExternalId?: string | null; workItemId?: string | null }
) {
  const reportExternalId = input.reportExternalId?.trim() ?? "";
  if (reportExternalId) {
    const byReportId = records.find((entry) => entry.reportExternalId.trim() === reportExternalId);
    if (byReportId) {
      return byReportId;
    }
  }

  const workItemId = input.workItemId?.trim() ?? "";
  if (workItemId) {
    const byWorkItemId = records.find((entry) => entry.workItemId === workItemId);
    if (byWorkItemId) {
      return byWorkItemId;
    }
  }

  const caseId = input.caseId?.trim() ?? "";
  if (caseId) {
    return records.find((entry) => entry.caseId === caseId) ?? null;
  }
  return null;
}

function saveWorkspace(records: ReportWorkspaceRecord[]) {
  saveWorkspaceRecords(STORAGE_KEY, records);
}

function upsertWorkspaceRecord(
  current: ReportWorkspaceRecord[],
  next: Partial<ReportWorkspaceRecord> & { caseId: string }
) {
  const nextIdentity = buildReportWorkspaceIdentity(next);
  const existing =
    findReportWorkspaceRecord(current, {
      caseId: next.caseId,
      reportExternalId: next.reportExternalId,
      workItemId: next.workItemId
    }) ?? null;
  const base: ReportWorkspaceRecord =
    existing ?? {
      workItemId: next.workItemId,
      resourceId: next.resourceId ?? next.caseId,
      source: next.source ?? "local",
      caseId: next.caseId,
      targetAddress: "",
      targetChain: "",
      reportType: "",
      reportExternalId: "",
      owner: "",
      priority: "normal",
      localDeadline: "",
      slaBreached: false,
      workspaceStatus: "draft",
      note: "",
      lastActionAt: ""
    };

  const merged: ReportWorkspaceRecord = {
    ...base,
    ...next,
    lastActionAt: next.lastActionAt ?? new Date().toISOString()
  };

  return sortByLastActionAtDesc(
    [merged, ...current.filter((entry) => buildReportWorkspaceIdentity(entry) !== nextIdentity && !isSameReportWorkspaceRecord(entry, merged))]
  );
}

function mergeWorkspaceRecords(serverRecords: ReportWorkspaceRecord[], localRecords: ReportWorkspaceRecord[]) {
  const merged = [...serverRecords];
  const seenWorkspaceIdentities = new Set(serverRecords.map((record) => buildReportWorkspaceIdentity(record)).filter(Boolean));
  const seenWorkItemIds = new Set(serverRecords.map((record) => record.workItemId).filter(Boolean));

  for (const record of localRecords) {
    const workspaceIdentity = buildReportWorkspaceIdentity(record);
    if (workspaceIdentity && seenWorkspaceIdentities.has(workspaceIdentity)) {
      continue;
    }
    if (record.workItemId && seenWorkItemIds.has(record.workItemId)) {
      continue;
    }
    if (merged.some((serverRecord) => isSameReportWorkspaceRecord(serverRecord, record))) {
      continue;
    }
    merged.push(record);
  }

  return sortByLastActionAtDesc(merged);
}

function mapQueueStatusToWorkspaceStatus(status: WorkItemQueueStatus): WorkspaceStatus {
  if (status === "READY" || status === "APPROVED" || status === "SUBMITTED" || status === "CLOSED") {
    return "ready";
  }
  return "in_review";
}

function mapWorkItemToWorkspaceRecord(item: ReportWorkItemResponse): ReportWorkspaceRecord {
  const metadata = item.metadata ?? {};
  const caseId = item.case_id ?? (readWorkItemMetadataString(metadata, "case_id") || item.resource_id);
  return {
    workItemId: item.id,
    resourceId: item.resource_id,
    source: "server",
    caseId,
    targetAddress: readWorkItemMetadataString(metadata, "target_address"),
    targetChain: readWorkItemMetadataString(metadata, "target_chain"),
    reportType: readWorkItemMetadataString(metadata, "report_type"),
    reportExternalId: item.report_external_id ?? readWorkItemMetadataString(metadata, "report_id"),
    owner: resolveWorkItemOwnerDisplay(metadata, item.owner_user_id),
    priority: item.priority,
    localDeadline: toDateTimeLocalValue(item.due_at),
    slaBreached: item.sla_breached === true,
    workspaceStatus: normalizeWorkspaceStatus(resolveWorkItemWorkspaceStatus(metadata, "formal_report_case")) ?? mapQueueStatusToWorkspaceStatus(item.queue_status),
    note: item.note ?? readWorkItemMetadataString(metadata, "note"),
    lastActionAt: item.last_activity_at || item.updated_at
  };
}

function getWorkspaceUrgency(record: ReportWorkspaceRecord) {
  if (!record.localDeadline) {
    return "no_deadline";
  }
  if (record.workspaceStatus === "ready") {
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

function toHistoryDateTimeInputValue(value: string | null) {
  if (!value) {
    return "";
  }
  return toDateTimeLocalValue(value) ?? "";
}

function toHistoryDateTimeQueryValue(value: string) {
  const trimmed = value.trim();
  if (!trimmed) {
    return "";
  }
  const parsed = new Date(trimmed);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }
  return parsed.toISOString();
}

function resolveDownloadFilename(contentDisposition: string | null, fallbackName: string) {
  if (!contentDisposition) {
    return fallbackName;
  }
  const match = /filename="([^"]+)"/i.exec(contentDisposition);
  return match?.[1] ?? fallbackName;
}

function buildReportWorkspaceSummary(record: ReportWorkspaceRecord) {
  return {
    work_item_id: record.workItemId ?? null,
    case_id: record.caseId,
    report_type: record.reportType || null,
    owner: record.owner || null,
    priority: record.priority,
    deadline: record.localDeadline || null,
    report_external_id: record.reportExternalId || null,
    sla_breached: record.slaBreached,
    status: record.workspaceStatus,
    source: record.source,
    note: record.note || null,
    last_action_at: record.lastActionAt
  };
}

function getWorkspaceStatusLabelKey(status: WorkspaceStatus): MessageKey {
  if (status === "in_review") {
    return "reports.workspace.status.inReview";
  }
  if (status === "ready") {
    return "reports.workspace.status.ready";
  }
  return "reports.workspace.status.draft";
}

function toneForWorkspaceSource(source: WorkspaceSource): "success" | "warning" {
  return source === "server" ? "success" : "warning";
}

function toneForSla(record: ReportWorkspaceRecord): "success" | "danger" {
  return record.slaBreached ? "danger" : "success";
}

const REPORT_PLAN_OPTIONS = ["free", "starter", "professional", "enterprise"] as const;
const REPORT_CASE_CHAIN_OPTIONS = ["ethereum", "bitcoin", "arbitrum", "base"] as const;
const REPORT_CASE_STATUS_OPTIONS = ["QUEUED", "PROCESSING", "COMPLETED", "FAILED"] as const;
const REQUESTED_REPORT_TYPE_ALIAS_TO_CANONICAL: Record<string, string> = {
  technical: "technical_basic",
  tech: "technical_basic",
  basic: "technical_basic",
  technical_full: "technical_full",
  deep_technical: "technical_full",
  coaf: "coaf_ready_report",
  coaf_report: "coaf_ready_report",
  ros: "coaf_ready_report",
  compliance: "compliance_aml",
  aml: "compliance_aml",
  kyt: "compliance_aml",
  aml_kyt: "compliance_aml",
  legal: "legal_report",
  juridico: "legal_report",
  parecer: "legal_report",
  full: "full_investigation",
  investigation: "full_investigation"
};

function getReportPlanLabelKey(plan: string | null | undefined): MessageKey | null {
  const normalized = plan?.toLowerCase();
  if (!normalized) {
    return null;
  }
  if (REPORT_PLAN_OPTIONS.includes(normalized as (typeof REPORT_PLAN_OPTIONS)[number])) {
    return `reports.catalog.filters.plan.${normalized}` as MessageKey;
  }
  return null;
}

function getReportCaseChainLabelKey(chain: string | null | undefined): MessageKey | null {
  const normalized = chain?.toLowerCase();
  if (!normalized) {
    return null;
  }
  if (REPORT_CASE_CHAIN_OPTIONS.includes(normalized as (typeof REPORT_CASE_CHAIN_OPTIONS)[number])) {
    return `reports.cases.filters.chain.${normalized}` as MessageKey;
  }
  return null;
}

function getReportCaseStatusLabelKey(status: string | null | undefined): MessageKey | null {
  if (!status) {
    return null;
  }
  if (REPORT_CASE_STATUS_OPTIONS.includes(status as (typeof REPORT_CASE_STATUS_OPTIONS)[number])) {
    return `reports.cases.filters.status.${status}` as MessageKey;
  }
  return null;
}

export default function ReportsPage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { locale, t } = useI18n();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);

  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [loadingCases, setLoadingCases] = useState(false);
  const [syncingWorkspace, setSyncingWorkspace] = useState(false);
  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [catalog, setCatalog] = useState<ReportTypeItem[]>([]);
  const [catalogFilterAvailability, setCatalogFilterAvailability] = useState("available");
  const [catalogFilterPlan, setCatalogFilterPlan] = useState("all");
  const [catalogSearch, setCatalogSearch] = useState("");
  const [selectedReportType, setSelectedReportType] = useState("");

  const [cases, setCases] = useState<CaseRow[]>([]);
  const [casesPage, setCasesPage] = useState(1);
  const [casesLimit, setCasesLimit] = useState(20);
  const [casesChainFilter, setCasesChainFilter] = useState("all");
  const [casesStatusFilter, setCasesStatusFilter] = useState("all");
  const [casesSearch, setCasesSearch] = useState("");
  const [openCaseId, setOpenCaseId] = useState("");
  const [workspace, setWorkspace] = useState<ReportWorkspaceRecord[]>([]);
  const [historySearch, setHistorySearch] = useState("");
  const [historyReportIdFilter, setHistoryReportIdFilter] = useState("");
  const [historyTypeFilter, setHistoryTypeFilter] = useState("all");
  const [historyCaseFilter, setHistoryCaseFilter] = useState("");
  const [historyCreatedFromFilter, setHistoryCreatedFromFilter] = useState("");
  const [historyCreatedToFilter, setHistoryCreatedToFilter] = useState("");
  const [historyRows, setHistoryRows] = useState<ReportHistoryRow[]>([]);
  const [selectedReportDetail, setSelectedReportDetail] = useState<ReportDetailResponse | null>(null);
  const [loadingReportDetail, setLoadingReportDetail] = useState(false);
  const [linkedRosId, setLinkedRosId] = useState<string | null>(null);
  const [linkedRosLoading, setLinkedRosLoading] = useState(false);
  const [exportingEvidenceBundle, setExportingEvidenceBundle] = useState(false);
  const [exportingFormalDossier, setExportingFormalDossier] = useState(false);
  const [historyPage, setHistoryPage] = useState(1);
  const [historyLimit, setHistoryLimit] = useState(20);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyHasMore, setHistoryHasMore] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [owner, setOwner] = useState("");
  const [priority, setPriority] = useState<WorkspacePriority>("normal");
  const [localDeadline, setLocalDeadline] = useState("");
  const [workspaceStatus, setWorkspaceStatus] = useState<WorkspaceStatus>("draft");
  const [workspaceNote, setWorkspaceNote] = useState("");
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
    loadErrorMessage: tr("reports.workspace.timeline.errorLoad" as MessageKey),
    commentErrorMessage: tr("reports.workspace.timeline.errorComment" as MessageKey),
    emptySelectionErrorMessage: tr("reports.workspace.timeline.emptyLocal" as MessageKey),
    emptyCommentErrorMessage: tr("reports.workspace.timeline.commentEmpty" as MessageKey),
    onCommentSaved: () => {
      setNotice(tr("reports.workspace.timeline.commentSaved" as MessageKey));
    }
  });

  const availableReportCount = useMemo(() => catalog.filter((entry: ReportTypeItem) => entry.available).length, [catalog]);
  const deprecatedReportCount = useMemo(() => catalog.filter((entry: ReportTypeItem) => Boolean(entry.deprecated)).length, [catalog]);
  const reportTypeLabelByCanonical = useMemo(() => {
    return catalog.reduce<Record<string, string>>((acc: Record<string, string>, entry: ReportTypeItem) => {
      if (entry.canonical.trim() && entry.label.trim()) {
        acc[entry.canonical] = entry.label;
      }
      return acc;
    }, {});
  }, [catalog]);
  const minimumPlanReports = useMemo(() => {
    return catalog.reduce<Record<string, number>>((acc: Record<string, number>, entry: ReportTypeItem) => {
      const plan = entry.min_plan ?? "unknown";
      acc[plan] = (acc[plan] ?? 0) + 1;
      return acc;
    }, {});
  }, [catalog]);
  const selectedReportHistoryEntry = useMemo(
    () => historyRows.find((entry: ReportHistoryRow) => entry.report_id === selectedReportDetail?.report_id) ?? null,
    [historyRows, selectedReportDetail?.report_id]
  );
  const selectedReportFormalDossier = useMemo(() => {
    if (!selectedReportDetail) {
      return null;
    }
    return deriveReportFormalDossierSummary(selectedReportDetail, Boolean(selectedReportHistoryEntry?.has_download_audit));
  }, [selectedReportDetail, selectedReportHistoryEntry?.has_download_audit]);
  const selectedReportWorkspaceRecord = useMemo(() => {
    if (!selectedReportDetail) {
      return null;
    }
    return findReportWorkspaceRecord(workspace, {
      caseId: selectedReportDetail.case_id,
      reportExternalId: selectedReportDetail.report_id
    });
  }, [selectedReportDetail, workspace]);
  const serverWorkspaceCount = useMemo(
    () => workspace.filter((entry: ReportWorkspaceRecord) => entry.source === "server").length,
    [workspace]
  );
  const localWorkspaceCount = useMemo(
    () => workspace.filter((entry: ReportWorkspaceRecord) => entry.source === "local").length,
    [workspace]
  );
  const hasMixedWorkspaceSources = serverWorkspaceCount > 0 && localWorkspaceCount > 0;

  const filteredCatalog = useMemo<ReportTypeItem[]>(() => {
    const query = catalogSearch.trim().toLowerCase();
    return catalog
      .filter((entry: ReportTypeItem) => {
        if (catalogFilterAvailability === "available") return entry.available;
        if (catalogFilterAvailability === "unavailable") return !entry.available;
        return true;
      })
      .filter((entry: ReportTypeItem) => {
        if (catalogFilterPlan === "all") return true;
        const minPlan = (entry.min_plan ?? "").toLowerCase();
        return minPlan === catalogFilterPlan;
      })
      .filter((entry: ReportTypeItem) => {
        if (!query) return true;
        return entry.canonical.toLowerCase().includes(query) || entry.label.toLowerCase().includes(query);
      })
      .sort((a: ReportTypeItem, b: ReportTypeItem) => {
        const rankDiff = toPlanRank(String(a.min_plan ?? "unknown")) - toPlanRank(String(b.min_plan ?? "unknown"));
        if (rankDiff !== 0) return rankDiff;
        return a.canonical.localeCompare(b.canonical);
      });
  }, [catalog, catalogFilterAvailability, catalogFilterPlan, catalogSearch]);

  const filteredCases = useMemo<CaseRow[]>(() => {
    const query = casesSearch.trim().toLowerCase();
    return cases.filter((entry: CaseRow) => {
      if (!query) return true;
      return (
        entry.id.toLowerCase().includes(query) ||
        entry.target_address.toLowerCase().includes(query) ||
        entry.target_chain.toLowerCase().includes(query) ||
        entry.status.toLowerCase().includes(query)
      );
    });
  }, [cases, casesSearch]);
  const filteredHistoryRows = useMemo<ReportHistoryRow[]>(() => {
    const query = historySearch.trim().toLowerCase();
    return historyRows
      .filter((record: ReportHistoryRow) =>
        !query ||
        (record.case_id ?? "").toLowerCase().includes(query) ||
        (reportTypeLabelByCanonical[record.report_type] ?? "").toLowerCase().includes(query) ||
        (reportTypeLabelByCanonical[REQUESTED_REPORT_TYPE_ALIAS_TO_CANONICAL[record.report_type_requested] ?? ""] ?? "")
          .toLowerCase()
          .includes(query) ||
        record.report_type.toLowerCase().includes(query) ||
        record.report_type_requested.toLowerCase().includes(query) ||
        record.report_id.toLowerCase().includes(query)
      )
      .sort((a: ReportHistoryRow, b: ReportHistoryRow) => b.created_at.localeCompare(a.created_at))
      .slice(0, 100);
  }, [historyRows, historySearch, reportTypeLabelByCanonical]);

  const quickContextLinks = openCaseId.trim()
    ? buildReportContextLinks(
        buildReportOperationalContext({
          caseId: openCaseId,
          reportId:
            selectedReportWorkspaceRecord?.reportExternalId ||
            (selectedReportDetail?.case_id === openCaseId.trim() ? selectedReportDetail.report_id : ""),
          reportType: selectedReportType,
          address: cases.find((entry: CaseRow) => entry.id === openCaseId)?.target_address ?? "",
          chain: cases.find((entry: CaseRow) => entry.id === openCaseId)?.target_chain ?? ""
        })
      )
    : [];
  const selectedTimelineRecord =
    selectedReportWorkspaceRecord ??
    findReportWorkspaceRecord(workspace, {
      caseId: openCaseId.trim(),
      reportExternalId: historyReportIdFilter.trim()
    });
  const selectedReportLastHandoff = useMemo(() => {
    if (!selectedReportWorkspaceRecord?.workItemId) {
      return null;
    }
    const handoffComments = timelineData?.comments.filter((comment) => comment.comment_type === "handoff") ?? [];
    if (!handoffComments.length) {
      return null;
    }
    return [...handoffComments].sort((left, right) => right.created_at.localeCompare(left.created_at))[0] ?? null;
  }, [selectedReportWorkspaceRecord?.workItemId, timelineData?.comments]);
  const timelineContextBadges = selectedTimelineRecord
    ? [
        {
          label: tr(`reports.workspace.source.${selectedTimelineRecord.source}` as MessageKey),
          tone: toneForWorkspaceSource(selectedTimelineRecord.source) as "success" | "warning"
        },
        {
          label: tr(getWorkspaceStatusLabelKey(selectedTimelineRecord.workspaceStatus)),
          tone: (
            selectedTimelineRecord.workspaceStatus === "ready"
              ? "success"
              : selectedTimelineRecord.workspaceStatus === "in_review"
                ? "warning"
                : "danger"
          ) as "success" | "warning" | "danger"
        },
        {
          label: tr(
            selectedTimelineRecord.slaBreached ? ("reports.workspace.sla.breached" as MessageKey) : ("reports.workspace.sla.onTrack" as MessageKey)
          ),
          tone: toneForSla(selectedTimelineRecord) as "success" | "danger"
        }
      ]
    : [];

  function renderReportTypeValue(value: string | null | undefined) {
    const normalized = value?.trim() ?? "";
    if (!normalized) {
      return t("common.notAvailable");
    }
    const label = reportTypeLabelByCanonical[normalized];
    if (!label || label === normalized) {
      return normalized;
    }
    return (
      <>
        <strong>{label}</strong>
        <div className="otc-muted otc-mono">{normalized}</div>
      </>
    );
  }

  function renderRequestedReportTypeValue(value: string | null | undefined) {
    const normalized = value?.trim() ?? "";
    if (!normalized) {
      return t("common.notAvailable");
    }
    const canonical = REQUESTED_REPORT_TYPE_ALIAS_TO_CANONICAL[normalized] ?? normalized;
    const label = reportTypeLabelByCanonical[canonical];
    if (!label) {
      return normalized;
    }
    if (canonical === normalized) {
      return renderReportTypeValue(normalized);
    }
    return (
      <>
        <strong>{label}</strong>
        <div className="otc-muted otc-mono">{normalized}</div>
      </>
    );
  }

  function formatReportTypeOptionLabel(entry: ReportTypeItem) {
    const label = entry.label.trim();
    const canonical = entry.canonical.trim();
    if (!label) {
      return canonical;
    }
    if (!canonical || label === canonical) {
      return label;
    }
    return `${label} (${canonical})`;
  }

  function renderDossierSummaryValue(value: string | null | undefined) {
    const normalized = value?.trim() ?? "";
    if (!normalized) {
      return t("common.notAvailable");
    }
    if (!isReportFormalDossierValue(normalized)) {
      return normalized;
    }
    return (
      <>
        <strong>{tr(`reports.dossier.values.${normalized}` as MessageKey)}</strong>
        <div className="otc-muted otc-mono">{normalized}</div>
      </>
    );
  }

  function syncHistoryLocation(next: {
    reportId?: string;
    reportType?: string;
    caseId?: string;
    createdFrom?: string;
    createdTo?: string;
  }) {
    const params = new URLSearchParams(searchParams.toString());
    const mappings = [
      ["history_report_id", next.reportId?.trim() ?? ""],
      ["history_report_type", next.reportType && next.reportType !== "all" ? next.reportType : ""],
      ["history_case_id", next.caseId?.trim() ?? ""],
      ["history_created_from", next.createdFrom ?? ""],
      ["history_created_to", next.createdTo ?? ""]
    ] as const;

    for (const [key, value] of mappings) {
      if (value) {
        params.set(key, value);
      } else {
        params.delete(key);
      }
    }

    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }

  function openReportFromHistory(reportId: string) {
    const normalizedReportId = reportId.trim();
    if (!normalizedReportId) {
      return;
    }

    setHistoryReportIdFilter(normalizedReportId);
    syncHistoryLocation({
      reportId: normalizedReportId,
      reportType: historyTypeFilter,
      caseId: historyCaseFilter,
      createdFrom: toHistoryDateTimeQueryValue(historyCreatedFromFilter),
      createdTo: toHistoryDateTimeQueryValue(historyCreatedToFilter)
    });
    void loadReportDetail(normalizedReportId);
  }

  function applyHistoryFilters() {
    const nextReportId = historyReportIdFilter.trim();
    const nextType = historyTypeFilter;
    const nextCaseId = historyCaseFilter.trim();
    const nextCreatedFrom = toHistoryDateTimeQueryValue(historyCreatedFromFilter);
    const nextCreatedTo = toHistoryDateTimeQueryValue(historyCreatedToFilter);

    syncHistoryLocation({
      reportId: nextReportId,
      reportType: nextType,
      caseId: nextCaseId,
      createdFrom: nextCreatedFrom,
      createdTo: nextCreatedTo
    });

    setHistoryPage(1);
    void loadReportDetail(nextReportId);
    void loadReportHistory(1, {
      reportId: nextReportId,
      reportType: nextType,
      caseId: nextCaseId,
      createdFrom: historyCreatedFromFilter,
      createdTo: historyCreatedToFilter
    });
  }

  function clearHistoryFilters() {
    setHistoryReportIdFilter("");
    setHistoryTypeFilter("all");
    setHistoryCaseFilter("");
    setHistoryCreatedFromFilter("");
    setHistoryCreatedToFilter("");
    setSelectedReportDetail(null);
    syncHistoryLocation({});
    setHistoryPage(1);
    void loadReportHistory(1, {
      reportId: "",
      reportType: "all",
      caseId: "",
      createdFrom: "",
      createdTo: ""
    });
  }

  async function loadOperationalWorkspace(localRecords: ReportWorkspaceRecord[], reportExternalId?: string) {
    const query = new URLSearchParams({
      module: "reports",
      resource_type: "formal_report_case",
      limit: String(WORKSPACE_PAGE_LIMIT)
    });
    if (reportExternalId?.trim()) {
      query.set("report_external_id", reportExternalId.trim());
    }
    const res = await fetch(
      `/api/app/operations/work-items?${query.toString()}`,
      { cache: "no-store" }
    );
    const data = (await res.json().catch(() => null)) as ReportWorkItemListResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setWorkspace(localRecords);
      setError(resolveApiErrorMessage(t, data, tr("reports.workspace.errorSync" as MessageKey)));
      return;
    }

    const items = data && "data" in data && Array.isArray(data.data) ? data.data : [];
    const serverRecords = items.map((item) => mapWorkItemToWorkspaceRecord(item));
    setWorkspace(mergeWorkspaceRecords(serverRecords, localRecords));
  }

  async function hydrateWorkspaceByReportExternalId(reportExternalId: string) {
    const normalizedReportId = reportExternalId.trim();
    if (!normalizedReportId) {
      return;
    }

    const currentLocalRecords = loadWorkspace();
    await loadOperationalWorkspace(currentLocalRecords, normalizedReportId);
  }

  async function loadCatalog() {
    setLoadingCatalog(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch("/api/app/report-types?include_unavailable=true&include_deprecated=true", { cache: "no-store" });
      const data = (await res.json().catch(() => null)) as ReportTypesResponse | { error?: string; detail?: unknown } | null;
      if (!res.ok) {
        setError(resolveApiErrorMessage(t, data, tr("reports.errorLoadCatalog" as MessageKey)));
        setCatalog([]);
        setLoadingCatalog(false);
        return;
      }
      const items = Array.isArray((data as ReportTypesResponse).types) ? (data as ReportTypesResponse).types : [];
      setCatalog(
        items.map((item) => ({
          canonical: item.canonical,
          label: item.label,
          available: Boolean(item.available),
          cost_credits: Number(item.cost_credits),
          min_plan: item.min_plan ?? null,
          format: item.format ?? null,
          deprecated: Boolean(item.deprecated)
        }))
      );
      setLoadingCatalog(false);
    } catch (err) {
      setCatalog([]);
      setError(err instanceof Error ? err.message : tr("reports.errorLoadCatalog" as MessageKey));
      setLoadingCatalog(false);
    }
  }

  async function loadCases(
    page = casesPage,
    overrides?: {
      chainFilter?: string;
      statusFilter?: string;
      limit?: number;
    }
  ) {
    setLoadingCases(true);
    setError(null);
    setNotice(null);
    const effectiveLimit = overrides?.limit ?? casesLimit;
    const effectiveChainFilter = overrides?.chainFilter ?? casesChainFilter;
    const effectiveStatusFilter = overrides?.statusFilter ?? casesStatusFilter;
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("limit", String(effectiveLimit));
    if (effectiveChainFilter !== "all") params.set("chain", effectiveChainFilter);
    if (effectiveStatusFilter !== "all") params.set("status", effectiveStatusFilter);
    try {
      const res = await fetch(`/api/app/investigation/cases?${params.toString()}`, { cache: "no-store" });
      const data = (await res.json().catch(() => null)) as CasesResponse | { error?: string; detail?: unknown } | null;
      if (!res.ok) {
        setError(resolveApiErrorMessage(t, data, tr("reports.errorLoadCases" as MessageKey)));
        setCases([]);
        setLoadingCases(false);
        return;
      }
      const rows = Array.isArray((data as CasesResponse).data) ? (data as CasesResponse).data : [];
      setCases(rows);
      setCasesPage(Number((data as CasesResponse).page ?? page));
      setCasesLimit(Number((data as CasesResponse).limit ?? effectiveLimit));
      setLoadingCases(false);
    } catch (err) {
      setCases([]);
      setError(err instanceof Error ? err.message : tr("reports.errorLoadCases" as MessageKey));
      setLoadingCases(false);
    }
  }

  async function loadReportHistory(
    page = historyPage,
    overrides?: {
      reportId?: string;
      reportType?: string;
      caseId?: string;
      createdFrom?: string;
      createdTo?: string;
      limit?: number;
    }
  ) {
    setLoadingHistory(true);
    setError(null);
    const effectiveLimit = overrides?.limit ?? historyLimit;
    const effectiveReportId = (overrides?.reportId ?? historyReportIdFilter).trim();
    const effectiveReportType = overrides?.reportType ?? historyTypeFilter;
    const effectiveCaseId = (overrides?.caseId ?? historyCaseFilter).trim();
    const effectiveCreatedFrom = toHistoryDateTimeQueryValue(overrides?.createdFrom ?? historyCreatedFromFilter);
    const effectiveCreatedTo = toHistoryDateTimeQueryValue(overrides?.createdTo ?? historyCreatedToFilter);

    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("limit", String(effectiveLimit));
    if (effectiveReportId) {
      params.set("report_id", effectiveReportId);
    }
    if (effectiveReportType !== "all") {
      params.set("report_type", effectiveReportType);
    }
    if (effectiveCaseId) {
      params.set("case_id", effectiveCaseId);
    }
    if (effectiveCreatedFrom) {
      params.set("created_from", effectiveCreatedFrom);
    }
    if (effectiveCreatedTo) {
      params.set("created_to", effectiveCreatedTo);
    }

    try {
      const res = await fetch(`/api/app/reports/list?${params.toString()}`, { cache: "no-store" });
      const data = (await res.json().catch(() => null)) as ReportHistoryResponse | { error?: string; detail?: unknown } | null;
      if (!res.ok) {
        setError(resolveApiErrorMessage(t, data, tr("reports.history.empty" as MessageKey)));
        setHistoryRows([]);
        setLoadingHistory(false);
        return;
      }

      const rows = Array.isArray((data as ReportHistoryResponse).data) ? (data as ReportHistoryResponse).data : [];
      setHistoryRows(rows);
      setHistoryPage(Number((data as ReportHistoryResponse).page ?? page));
      setHistoryLimit(Number((data as ReportHistoryResponse).limit ?? effectiveLimit));
      setHistoryTotal(Number((data as ReportHistoryResponse).total ?? 0));
      setHistoryHasMore(Boolean((data as ReportHistoryResponse).has_more));
      setLoadingHistory(false);
    } catch (err) {
      setHistoryRows([]);
      setError(err instanceof Error ? err.message : tr("reports.history.empty" as MessageKey));
      setLoadingHistory(false);
    }
  }

  async function loadReportDetail(reportId: string) {
    const normalizedReportId = reportId.trim();
    if (!normalizedReportId) {
      setSelectedReportDetail(null);
      return;
    }

    setLoadingReportDetail(true);
    setError(null);
    try {
      const res = await fetch(`/api/app/reports/${encodeURIComponent(normalizedReportId)}`, { cache: "no-store" });
      const data = (await res.json().catch(() => null)) as ReportDetailResponse | { error?: string; detail?: unknown } | null;
      if (!res.ok) {
        setSelectedReportDetail(null);
        setError(resolveApiErrorMessage(t, data, tr("reports.history.empty" as MessageKey)));
        setLoadingReportDetail(false);
        return;
      }

      setSelectedReportDetail(data as ReportDetailResponse);
      setOpenCaseId((data as ReportDetailResponse).case_id);
      setLoadingReportDetail(false);
    } catch (err) {
      setSelectedReportDetail(null);
      setError(err instanceof Error ? err.message : tr("reports.history.empty" as MessageKey));
      setLoadingReportDetail(false);
    }
  }

  async function requestEvidenceBundleForReport(report: ReportDetailResponse) {
    const res = await fetch("/api/app/audit/evidence-export", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        format: "json",
        request_id: report.case_id.trim() || null,
        action: null,
        resource_type: "case",
        report_id: report.report_id.trim() || null,
        resource_id: report.case_id.trim() || null,
        limit: 200,
        include_audit_logs: true,
        include_credit_ledger: true,
        include_reports: true
      })
    });

    if (!res.ok) {
      const data = (await res.json().catch(() => null)) as { error?: string; detail?: unknown } | null;
      throw new Error(resolveApiErrorMessage(t, data, tr("reports.history.empty" as MessageKey)));
    }

    return res;
  }

  async function exportEvidenceBundleForReport(report: ReportDetailResponse) {
    setExportingEvidenceBundle(true);
    setError(null);
    setNotice(null);
    try {
      const res = await requestEvidenceBundleForReport(report);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = resolveDownloadFilename(
        res.headers.get("content-disposition"),
        `ontrackchain-evidence-bundle-${report.report_id}.json`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setNotice(tr("reports.detail.noticeEvidenceExported" as MessageKey, { reportId: report.report_id }));
    } catch (err) {
      setError(err instanceof Error ? err.message : tr("reports.detail.errorExportEvidence" as MessageKey));
    } finally {
      setExportingEvidenceBundle(false);
    }
  }

  async function exportFormalDossierForReport(report: ReportDetailResponse) {
    setExportingFormalDossier(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch("/api/app/reports/formal-dossier", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          report: {
            report_id: report.report_id,
            case_id: report.case_id,
            report_type_requested: report.report_type_requested,
            report_type: report.report_type,
            created_at: report.created_at,
            content_type: report.content_type,
            file_hash_sha256: report.file_hash_sha256,
            onchain_hash: report.onchain_hash
          },
          has_download_audit: Boolean(selectedReportHistoryEntry?.has_download_audit),
          workspace_summary: selectedReportWorkspaceRecord ? buildReportWorkspaceSummary(selectedReportWorkspaceRecord) : null
        })
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as { error?: string; detail?: unknown } | null;
        throw new Error(resolveApiErrorMessage(t, data, tr("reports.history.empty" as MessageKey)));
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = resolveDownloadFilename(res.headers.get("content-disposition"), buildReportFormalDossierFilename(report.report_id));
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setNotice(tr("reports.detail.noticeDossierExported" as MessageKey, { reportId: report.report_id }));
    } catch (err) {
      setError(err instanceof Error ? err.message : tr("reports.detail.errorExportDossier" as MessageKey));
    } finally {
      setExportingFormalDossier(false);
    }
  }

  useEffect(() => {
    void loadCatalog();
    void loadCases(1);
    void loadReportHistory(1);
    const localRecords: ReportWorkspaceRecord[] = [];
    setWorkspace(localRecords);
    loadOperationalWorkspace(localRecords).catch(() => {
      setWorkspace(localRecords);
      setError(tr("reports.workspace.errorSync" as MessageKey));
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
    saveWorkspace(workspace);
  }, [workspace]);

  useEffect(() => {
    if (selectedReportType || !catalog.length) {
      return;
    }
    const nextReportType = catalog.find((entry: ReportTypeItem) => entry.available && !entry.deprecated)?.canonical ?? catalog[0]?.canonical ?? "";
    if (nextReportType) {
      setSelectedReportType(nextReportType);
    }
  }, [catalog, selectedReportType]);

  useEffect(() => {
    const nextAvailability = searchParams.get("catalog_availability");
    const nextPlan = searchParams.get("catalog_plan");
    const nextCatalogSearch = searchParams.get("catalog_q");
    const nextReportType = searchParams.get("report_type");
    const nextChain = searchParams.get("chain");
    const nextStatus = searchParams.get("status");
    const nextCaseId = searchParams.get("case_id");
    const nextCasesSearch = searchParams.get("cases_q");
    const nextOwner = searchParams.get("owner");
    const nextPriority = searchParams.get("priority") as WorkspacePriority | null;
    const nextDeadline = searchParams.get("deadline");
    const nextWorkspaceStatus = searchParams.get("workspace_status") as WorkspaceStatus | null;
    const nextWorkspaceNote = searchParams.get("workspace_note");
    const nextHistoryReportId = searchParams.get("history_report_id");
    const nextHistoryType = searchParams.get("history_report_type");
    const nextHistoryCaseId = searchParams.get("history_case_id");
    const nextHistoryCreatedFrom = searchParams.get("history_created_from");
    const nextHistoryCreatedTo = searchParams.get("history_created_to");

    if (nextAvailability === "available" || nextAvailability === "unavailable" || nextAvailability === "all") {
      setCatalogFilterAvailability(nextAvailability);
    }
    if (nextPlan) {
      setCatalogFilterPlan(nextPlan);
    }
    if (nextCatalogSearch !== null) {
      setCatalogSearch(nextCatalogSearch);
    }
    if (nextReportType) {
      setSelectedReportType(nextReportType);
    }
    if (nextChain) {
      setCasesChainFilter(nextChain);
    }
    if (nextStatus) {
      setCasesStatusFilter(nextStatus);
    }
    if (nextCaseId) {
      setOpenCaseId(nextCaseId);
    }
    if (nextCasesSearch !== null) {
      setCasesSearch(nextCasesSearch);
    }
    if (nextOwner !== null) {
      setOwner(nextOwner);
    }
    if (nextPriority === "critical" || nextPriority === "high" || nextPriority === "normal") {
      setPriority(nextPriority);
    }
    if (nextDeadline !== null) {
      setLocalDeadline(nextDeadline);
    }
    if (nextWorkspaceStatus === "draft" || nextWorkspaceStatus === "in_review" || nextWorkspaceStatus === "ready") {
      setWorkspaceStatus(nextWorkspaceStatus);
    }
    if (nextWorkspaceNote !== null) {
      setWorkspaceNote(nextWorkspaceNote);
    }
    if (nextHistoryReportId !== null) {
      setHistoryReportIdFilter(nextHistoryReportId);
    }
    if (nextHistoryType !== null) {
      setHistoryTypeFilter(nextHistoryType || "all");
    }
    if (nextHistoryCaseId !== null) {
      setHistoryCaseFilter(nextHistoryCaseId);
    }
    if (nextHistoryCreatedFrom !== null) {
      setHistoryCreatedFromFilter(toHistoryDateTimeInputValue(nextHistoryCreatedFrom));
    }
    if (nextHistoryCreatedTo !== null) {
      setHistoryCreatedToFilter(toHistoryDateTimeInputValue(nextHistoryCreatedTo));
    }
    if (nextChain || nextStatus) {
      void loadCases(1, {
        chainFilter: nextChain ?? casesChainFilter,
        statusFilter: nextStatus ?? casesStatusFilter
      });
    }
    if (
      nextHistoryReportId !== null ||
      nextHistoryType !== null ||
      nextHistoryCaseId !== null ||
      nextHistoryCreatedFrom !== null ||
      nextHistoryCreatedTo !== null
    ) {
      void loadReportHistory(1, {
        reportId: nextHistoryReportId ?? "",
        reportType: nextHistoryType ?? "all",
        caseId: nextHistoryCaseId ?? "",
        createdFrom: toHistoryDateTimeInputValue(nextHistoryCreatedFrom),
        createdTo: toHistoryDateTimeInputValue(nextHistoryCreatedTo)
      });
    }
    if (nextHistoryReportId !== null) {
      void loadReportDetail(nextHistoryReportId);
    }
  }, [searchParams]);

  useEffect(() => {
    const currentRecord =
      selectedReportWorkspaceRecord ??
      findReportWorkspaceRecord(workspace, {
        caseId: openCaseId.trim(),
        reportExternalId: historyReportIdFilter.trim()
      });
    if (!currentRecord) {
      return;
    }
    setOwner(currentRecord.owner);
    setPriority(currentRecord.priority);
    setLocalDeadline(currentRecord.localDeadline);
    setWorkspaceStatus(currentRecord.workspaceStatus);
    setWorkspaceNote(currentRecord.note);
    if (currentRecord.reportType) {
      setSelectedReportType(currentRecord.reportType);
    }
  }, [historyReportIdFilter, openCaseId, selectedReportWorkspaceRecord, workspace]);

  useEffect(() => {
    const reportExternalId = selectedReportDetail?.report_id?.trim() || historyReportIdFilter.trim();
    if (!reportExternalId) {
      return;
    }

    hydrateWorkspaceByReportExternalId(reportExternalId).catch(() => {
      // Mantem o workspace atual quando a hidratação seletiva falha.
    });
  }, [historyReportIdFilter, selectedReportDetail?.report_id]);

  useEffect(() => {
    const reportId = selectedReportDetail?.report_id?.trim() ?? "";
    const reportType = selectedReportDetail?.report_type?.trim() ?? "";
    if (!reportId || reportType !== "coaf_ready_report") {
      setLinkedRosId(null);
      setLinkedRosLoading(false);
      return;
    }

    setLinkedRosLoading(true);
    fetch(`/api/app/reports/${encodeURIComponent(reportId)}/ros-coaf-ref`, { cache: "no-store" })
      .then(async (res) => {
        const data = (await res.json().catch(() => null)) as ReportRosCoafRefResponse | { error?: string; detail?: unknown } | null;
        if (!res.ok) {
          setLinkedRosId(null);
          setLinkedRosLoading(false);
          return;
        }
        setLinkedRosId(data && "ros_id" in data && typeof data.ros_id === "string" && data.ros_id.trim() ? data.ros_id.trim() : null);
        setLinkedRosLoading(false);
      })
      .catch(() => {
        setLinkedRosId(null);
        setLinkedRosLoading(false);
      });
  }, [selectedReportDetail?.report_id, selectedReportDetail?.report_type]);

  useEffect(() => {
    if (!selectedTimelineRecord?.workItemId) {
      resetTimeline();
      return;
    }
    void loadTimeline(selectedTimelineRecord.workItemId);
  }, [loadTimeline, resetTimeline, selectedTimelineRecord?.workItemId]);

  function trackCase(entry: CaseRow) {
    void (async () => {
      const nextReportType = selectedReportType.trim();
      const draftRecord: ReportWorkspaceRecord = {
        workItemId:
          findReportWorkspaceRecord(workspace, {
            caseId: entry.id,
            reportExternalId: selectedReportDetail?.case_id === entry.id ? selectedReportDetail.report_id : ""
          })?.workItemId,
        resourceId: entry.id,
        source: "local",
        caseId: entry.id,
        targetAddress: entry.target_address,
        targetChain: entry.target_chain,
        reportType: nextReportType,
        reportExternalId: selectedReportDetail?.case_id === entry.id ? selectedReportDetail.report_id : "",
        owner,
        priority,
        localDeadline,
        slaBreached: false,
        workspaceStatus,
        note: workspaceNote,
        lastActionAt: new Date().toISOString()
      };
      setWorkspace((current: ReportWorkspaceRecord[]) => upsertWorkspaceRecord(current, draftRecord));
      setOpenCaseId(entry.id);
      if (!isUuidLike(entry.id)) {
        setNotice(tr("reports.workspace.noticeTrackedLocalOnly" as MessageKey, { caseId: entry.id }));
        return;
      }

      try {
        await syncWorkspaceRecord(draftRecord);
        setNotice(tr("reports.workspace.noticeTrackedSynced" as MessageKey, { caseId: entry.id }));
      } catch (syncError) {
        setNotice(tr("reports.workspace.noticeTrackedLocalOnly" as MessageKey, { caseId: entry.id }));
        setError(syncError instanceof Error ? syncError.message : tr("reports.workspace.errorSync" as MessageKey));
      }
    })();
  }

  function hydrateWorkspaceRecord(record: ReportWorkspaceRecord) {
    setOpenCaseId(record.caseId);
    if (record.reportExternalId) {
      setHistoryReportIdFilter(record.reportExternalId);
      syncHistoryLocation({
        reportId: record.reportExternalId,
        reportType: historyTypeFilter,
        caseId: historyCaseFilter,
        createdFrom: toHistoryDateTimeQueryValue(historyCreatedFromFilter),
        createdTo: toHistoryDateTimeQueryValue(historyCreatedToFilter)
      });
      void loadReportDetail(record.reportExternalId);
    }
    setSelectedReportType(record.reportType);
    setOwner(record.owner);
    setPriority(record.priority);
    setLocalDeadline(record.localDeadline);
    setWorkspaceStatus(record.workspaceStatus);
    setWorkspaceNote(record.note);
    setNotice(tr("reports.workspace.noticeLoaded" as MessageKey, { caseId: record.caseId }));
  }

  async function syncWorkspaceRecord(record: ReportWorkspaceRecord, nextStatus?: WorkspaceStatus) {
    if (!isUuidLike(record.caseId)) {
      throw new Error(tr("reports.workspace.errorSyncMissingCaseId" as MessageKey));
    }

    const ownerUserId = resolveOwnerUserId({
      ownerLabel: record.owner,
      linkedUserId: authContext?.linked_user_id,
      isUuidLike
    });

    const localStatus = nextStatus ?? record.workspaceStatus;
    const queueStatus: WorkItemQueueStatus = localStatus === "ready" ? "READY" : "UNDER_REVIEW";
    const metadata: ReportWorkItemMetadata = withCanonicalWorkItemMetadata(
      {
        target_address: record.targetAddress,
        target_chain: record.targetChain,
        report_type: record.reportType,
        ...(record.reportExternalId ? { report_id: record.reportExternalId } : {})
      },
      {
        resourceType: "formal_report_case",
        caseId: record.caseId,
        ownerLabel: record.owner,
        ownerUserId,
        workspaceStatus: localStatus,
        note: record.note
      }
    );
    const requestBody: CreateWorkItemRequest<ReportWorkItemMetadata> | PatchWorkItemRequest<ReportWorkItemMetadata> = record.workItemId
      ? {
          ...(record.reportExternalId ? { report_external_id: record.reportExternalId } : {}),
          ...(ownerUserId ? { owner_user_id: ownerUserId } : {}),
          priority: record.priority,
          queue_status: queueStatus,
          due_at: toApiDueAt(record.localDeadline),
          title: `Formal report case • ${record.caseId}`,
          note: record.note || null,
          metadata
        }
      : {
          module: "reports",
          resource_type: "formal_report_case",
          resource_id: record.caseId,
          case_id: record.caseId,
          ...(record.reportExternalId ? { report_external_id: record.reportExternalId } : {}),
          ...(ownerUserId ? { owner_user_id: ownerUserId } : {}),
          priority: record.priority,
          queue_status: queueStatus,
          due_at: toApiDueAt(record.localDeadline),
          title: `Formal report case • ${record.caseId}`,
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
    const data = (await res.json().catch(() => null)) as ReportWorkItemResponse | { error?: string; detail?: unknown } | null;
    setSyncingWorkspace(false);
    if (!res.ok) {
      throw new Error(resolveApiErrorMessage(t, data, tr("reports.workspace.errorSync" as MessageKey)));
    }

    const nextRecord = mapWorkItemToWorkspaceRecord(data as ReportWorkItemResponse);
    setWorkspace((current: ReportWorkspaceRecord[]) => upsertWorkspaceRecord(current, nextRecord));
    const currentSelectionMatchesNextRecord = Boolean(
      nextRecord.workItemId &&
        selectedTimelineRecord &&
        isSameReportWorkspaceRecord(selectedTimelineRecord, nextRecord)
    );
    if (currentSelectionMatchesNextRecord && nextRecord.workItemId) {
      await loadTimeline(nextRecord.workItemId);
    }
    return nextRecord;
  }

  function updateWorkspaceStatus(recordToUpdate: ReportWorkspaceRecord, nextStatus: WorkspaceStatus) {
    void (async () => {
      const currentRecord =
        findReportWorkspaceRecord(workspace, {
          caseId: recordToUpdate.caseId,
          reportExternalId: recordToUpdate.reportExternalId,
          workItemId: recordToUpdate.workItemId
        }) ?? null;
      if (!currentRecord) {
        return;
      }

      const draftRecord = { ...currentRecord, workspaceStatus: nextStatus, lastActionAt: new Date().toISOString() };
      setWorkspace((current: ReportWorkspaceRecord[]) =>
        upsertWorkspaceRecord(current, {
          caseId: currentRecord.caseId,
          reportExternalId: currentRecord.reportExternalId,
          workspaceStatus: nextStatus,
          lastActionAt: draftRecord.lastActionAt
        })
      );
      try {
        await syncWorkspaceRecord(draftRecord, nextStatus);
      } catch (syncError) {
        setError(syncError instanceof Error ? syncError.message : tr("reports.workspace.errorSync" as MessageKey));
        setNotice(tr("reports.workspace.noticeTrackedLocalOnly" as MessageKey, { caseId: currentRecord.caseId }));
      }
    })();
  }

  function removeWorkspaceRecord(recordToRemove: ReportWorkspaceRecord) {
    const identityToRemove = buildReportWorkspaceIdentity(recordToRemove);
    setWorkspace((current: ReportWorkspaceRecord[]) =>
      current.filter(
        (entry: ReportWorkspaceRecord) =>
          buildReportWorkspaceIdentity(entry) !== identityToRemove && !isSameReportWorkspaceRecord(entry, recordToRemove)
      )
    );
  }

  return (
    <AppShell
      title={tr("reports.title" as MessageKey)}
      subtitle={tr("reports.subtitle" as MessageKey)}
      activePath="/reports"
      actions={<Pill>{tr("reports.active" as MessageKey)}</Pill>}
    >
      <MetricGrid>
        <MetricCard label={tr("reports.stats.totalTypes" as MessageKey)} value={loadingCatalog ? t("common.loading") : catalog.length} meta={tr("reports.stats.totalTypesMeta" as MessageKey)} />
        <MetricCard label={tr("reports.stats.availableTypes" as MessageKey)} value={loadingCatalog ? t("common.loading") : availableReportCount} meta={tr("reports.stats.availableTypesMeta" as MessageKey)} accent />
        <MetricCard label={tr("reports.stats.deprecatedTypes" as MessageKey)} value={loadingCatalog ? t("common.loading") : deprecatedReportCount} meta={tr("reports.stats.deprecatedTypesMeta" as MessageKey)} />
        <MetricCard
          label={tr("reports.stats.plans" as MessageKey)}
          value={loadingCatalog ? t("common.loading") : Object.keys(minimumPlanReports).length}
          meta={tr("reports.stats.plansMeta" as MessageKey)}
        />
      </MetricGrid>

      {error ? <Message tone="error">{error}</Message> : null}
      {notice ? <Message tone="success">{notice}</Message> : null}

      <Panel
        title={tr("reports.catalog.title" as MessageKey)}
        description={tr("reports.catalog.description" as MessageKey)}
        actions={
          <div className="otc-controls">
            <button className="otc-button otc-button--ghost" type="button" onClick={() => loadCatalog()} disabled={loadingCatalog}>
              {loadingCatalog ? tr("reports.catalog.refreshLoading" as MessageKey) : tr("reports.catalog.refresh" as MessageKey)}
            </button>
          </div>
        }
      >
        <div className="otc-controls">
          <label className="otc-field">
            {tr("reports.catalog.filters.availability" as MessageKey)}
            <select className="otc-select" value={catalogFilterAvailability} onChange={(event) => setCatalogFilterAvailability(event.target.value)}>
              <option value="available">{tr("reports.catalog.filters.available" as MessageKey)}</option>
              <option value="unavailable">{tr("reports.catalog.filters.unavailable" as MessageKey)}</option>
              <option value="all">{tr("reports.catalog.filters.all" as MessageKey)}</option>
            </select>
          </label>
          <label className="otc-field">
            {tr("reports.catalog.filters.minPlan" as MessageKey)}
            <select className="otc-select" value={catalogFilterPlan} onChange={(event) => setCatalogFilterPlan(event.target.value)}>
              <option value="all">{tr("reports.catalog.filters.all" as MessageKey)}</option>
              {REPORT_PLAN_OPTIONS.map((plan) => (
                <option key={plan} value={plan}>
                  {tr(getReportPlanLabelKey(plan) ?? "reports.catalog.filters.all")}
                </option>
              ))}
            </select>
          </label>
          <label className="otc-field">
            {tr("reports.catalog.filters.search" as MessageKey)}
            <input className="otc-input" value={catalogSearch} onChange={(event) => setCatalogSearch(event.target.value)} />
          </label>
        </div>

        {filteredCatalog.length ? (
          <table className="otc-table otc-table--spaced">
            <thead>
              <tr>
                <th>{tr("reports.catalog.table.type" as MessageKey)}</th>
                <th>{tr("reports.catalog.table.plan" as MessageKey)}</th>
                <th>{tr("reports.catalog.table.cost" as MessageKey)}</th>
                <th>{tr("reports.catalog.table.status" as MessageKey)}</th>
                <th>{tr("reports.catalog.table.actions" as MessageKey)}</th>
              </tr>
            </thead>
            <tbody>
              {filteredCatalog.map((entry) => (
                <tr key={entry.canonical}>
                  <td>
                    <strong>{entry.label}</strong>
                    <div className="otc-muted">{entry.canonical}</div>
                  </td>
                  <td>
                    {(() => {
                      const labelKey = getReportPlanLabelKey(entry.min_plan);
                      if (labelKey) {
                        return tr(labelKey);
                      }
                      return entry.min_plan ?? t("common.notAvailable");
                    })()}
                  </td>
                  <td>{Number.isFinite(entry.cost_credits) ? entry.cost_credits : t("common.notAvailable")}</td>
                  <td>
                    <div className="otc-controls">
                      <Pill tone={entry.available ? "success" : "warning"}>{entry.available ? tr("reports.catalog.table.available" as MessageKey) : tr("reports.catalog.table.unavailable" as MessageKey)}</Pill>
                      {entry.deprecated ? <Pill tone="danger">{tr("reports.catalog.table.deprecated" as MessageKey)}</Pill> : null}
                    </div>
                  </td>
                  <td>
                    <div className="otc-controls">
                      <button className="otc-button otc-button--ghost" type="button" onClick={() => setSelectedReportType(entry.canonical)}>
                        {tr("reports.catalog.table.useInCases" as MessageKey)}
                      </button>
                      <a className="otc-button otc-button--ghost" href={`/investigate?report_type=${encodeURIComponent(entry.canonical)}`}>
                        {tr("reports.catalog.table.openInvestigate" as MessageKey)}
                      </a>
                      <a className="otc-button otc-button--ghost" href="/ros-coaf">
                        {tr("reports.catalog.table.openRos" as MessageKey)}
                      </a>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <Message>{loadingCatalog ? tr("reports.catalog.loading" as MessageKey) : tr("reports.catalog.empty" as MessageKey)}</Message>
        )}

        <details className="otc-panel otc-controls--spaced">
          <summary>{tr("reports.catalog.notesTitle" as MessageKey)}</summary>
          <CodeBlock>{JSON.stringify({ legal_report: "strong_auth_required", full_investigation: "enterprise_only" }, null, 2)}</CodeBlock>
        </details>
      </Panel>

      <Panel
        title={tr("reports.cases.title" as MessageKey)}
        description={tr("reports.cases.description" as MessageKey)}
        actions={
          <div className="otc-controls">
            <button className="otc-button otc-button--ghost" type="button" onClick={() => loadCases(1)} disabled={loadingCases}>
              {loadingCases ? tr("reports.cases.refreshLoading" as MessageKey) : tr("reports.cases.refresh" as MessageKey)}
            </button>
          </div>
        }
      >
        <div className="otc-controls">
          <label className="otc-field">
            {tr("reports.cases.filters.chain" as MessageKey)}
            <select className="otc-select" value={casesChainFilter} onChange={(event) => setCasesChainFilter(event.target.value)}>
              <option value="all">{tr("reports.cases.filters.all" as MessageKey)}</option>
              {REPORT_CASE_CHAIN_OPTIONS.map((chain) => (
                <option key={chain} value={chain}>
                  {tr(getReportCaseChainLabelKey(chain) ?? "reports.cases.filters.all")}
                </option>
              ))}
            </select>
          </label>
          <label className="otc-field">
            {tr("reports.cases.filters.status" as MessageKey)}
            <select className="otc-select" value={casesStatusFilter} onChange={(event) => setCasesStatusFilter(event.target.value)}>
              <option value="all">{tr("reports.cases.filters.all" as MessageKey)}</option>
              {REPORT_CASE_STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>
                  {tr(getReportCaseStatusLabelKey(status) ?? "reports.cases.filters.all")}
                </option>
              ))}
            </select>
          </label>
          <label className="otc-field">
            {tr("reports.cases.filters.caseId" as MessageKey)}
            <input className="otc-input" value={openCaseId} onChange={(event) => setOpenCaseId(event.target.value)} />
          </label>
          <label className="otc-field">
            {tr("reports.cases.filters.reportType" as MessageKey)}
            <select
              className="otc-select"
              value={selectedReportType}
              onChange={(event) => setSelectedReportType(event.target.value)}
              data-testid="reports-cases-report-type"
            >
              <option value="">{tr("reports.cases.filters.none" as MessageKey)}</option>
              {catalog.map((entry) => (
                <option key={entry.canonical} value={entry.canonical}>
                  {formatReportTypeOptionLabel(entry)}
                </option>
              ))}
            </select>
          </label>
          <label className="otc-field">
            {tr("reports.cases.filters.search" as MessageKey)}
            <input className="otc-input" value={casesSearch} onChange={(event) => setCasesSearch(event.target.value)} />
          </label>
          <label className="otc-field">
            {tr("reports.workspace.filters.owner" as MessageKey)}
            <input className="otc-input" value={owner} onChange={(event) => setOwner(event.target.value)} />
          </label>
          <label className="otc-field">
            {tr("reports.workspace.filters.priority" as MessageKey)}
            <select className="otc-select" value={priority} onChange={(event) => setPriority(event.target.value as WorkspacePriority)}>
              <option value="critical">{t("common.priority.critical")}</option>
              <option value="high">{t("common.priority.high")}</option>
              <option value="normal">{t("common.priority.normal")}</option>
            </select>
          </label>
          <label className="otc-field">
            {tr("reports.workspace.filters.deadline" as MessageKey)}
            <input className="otc-input" type="datetime-local" value={localDeadline} onChange={(event) => setLocalDeadline(event.target.value)} />
          </label>
          <label className="otc-field">
            {tr("reports.workspace.filters.status" as MessageKey)}
            <select className="otc-select" value={workspaceStatus} onChange={(event) => setWorkspaceStatus(event.target.value as WorkspaceStatus)}>
              <option value="draft">{tr("reports.workspace.status.draft" as MessageKey)}</option>
              <option value="in_review">{tr("reports.workspace.status.inReview" as MessageKey)}</option>
              <option value="ready">{tr("reports.workspace.status.ready" as MessageKey)}</option>
            </select>
          </label>
          <label className="otc-field">
            {tr("reports.workspace.filters.note" as MessageKey)}
            <input className="otc-input" value={workspaceNote} onChange={(event) => setWorkspaceNote(event.target.value)} />
          </label>
          {quickContextLinks.map((link: OperationalContextLink & { labelKey: MessageKey }) => (
            <a
              key={`quick-${link.testIdSuffix}`}
              className={link.kind === "case" ? "otc-button" : "otc-button otc-button--ghost"}
              href={link.href}
            >
              {tr(
                (link.kind === "case"
                  ? "reports.cases.openCase"
                  : link.kind === "audit"
                    ? "reports.cases.openAudit"
                    : link.kind === "evidence"
                      ? "reports.cases.openEvidence"
                      : "reports.cases.table.openInvestigate") as MessageKey
              )}
            </a>
          ))}
          <button
            type="button"
            className="otc-button"
            onClick={() => {
              setCasesPage(1);
              void loadCases(1);
            }}
          >
            {tr("reports.cases.apply" as MessageKey)}
          </button>
        </div>

        <Panel title={tr("reports.workspace.title" as MessageKey)} description={tr("reports.workspace.description" as MessageKey)}>
          {localWorkspaceCount > 0 && serverWorkspaceCount === 0 ? (
            <Message>{tr("reports.workspace.mode.localOnly" as MessageKey, { count: localWorkspaceCount })}</Message>
          ) : null}
          {hasMixedWorkspaceSources ? (
            <Message>
              {tr("reports.workspace.mode.mixed" as MessageKey, {
                server: serverWorkspaceCount,
                local: localWorkspaceCount
              })}
            </Message>
          ) : null}
          {workspace.length ? (
            <table className="otc-table otc-table--spaced">
              <thead>
                <tr>
                  <th>{tr("reports.workspace.table.caseId" as MessageKey)}</th>
                  <th>{tr("reports.history.reportId" as MessageKey)}</th>
                  <th>{tr("reports.workspace.table.reportType" as MessageKey)}</th>
                  <th>{tr("reports.workspace.table.owner" as MessageKey)}</th>
                  <th>{tr("reports.workspace.table.priority" as MessageKey)}</th>
                  <th>{tr("reports.workspace.table.deadline" as MessageKey)}</th>
                  <th>{tr("reports.workspace.table.sla" as MessageKey)}</th>
                  <th>{tr("reports.workspace.table.status" as MessageKey)}</th>
                  <th>{tr("reports.workspace.table.source" as MessageKey)}</th>
                  <th>{tr("reports.workspace.table.actions" as MessageKey)}</th>
                </tr>
              </thead>
              <tbody>
              {workspace.map((record: ReportWorkspaceRecord) => (
                  <tr
                    key={buildReportWorkspaceIdentity(record)}
                    data-testid={`reports-workspace-row-${record.caseId}`}
                    className={
                      selectedReportWorkspaceRecord && isSameReportWorkspaceRecord(selectedReportWorkspaceRecord, record)
                        ? "otc-row-selected"
                        : undefined
                    }
                  >
                    <td>
                      <strong>{record.caseId}</strong>
                      {record.note ? <div className="otc-muted">{record.note}</div> : null}
                    </td>
                    <td className="otc-mono">{record.reportExternalId || t("common.notAvailable")}</td>
                    <td>{renderReportTypeValue(record.reportType)}</td>
                    <td>{record.owner || t("common.notAvailable")}</td>
                    <td data-testid={`reports-workspace-priority-${record.caseId}`}>{t(`common.priority.${record.priority}` as MessageKey)}</td>
                    <td data-testid={`reports-workspace-deadline-${record.caseId}`}>
                      {record.localDeadline ? formatDate(record.localDeadline, locale) ?? record.localDeadline : t("common.notAvailable")}
                      <div className="otc-muted">{tr(`reports.workspace.urgency.${getWorkspaceUrgency(record)}` as MessageKey)}</div>
                    </td>
                    <td data-testid={`reports-workspace-sla-${record.caseId}`}>
                      <Pill tone={toneForSla(record)}>
                        {tr(record.slaBreached ? ("reports.workspace.sla.breached" as MessageKey) : ("reports.workspace.sla.onTrack" as MessageKey))}
                      </Pill>
                    </td>
                    <td>{tr(`reports.workspace.status.${record.workspaceStatus === "in_review" ? "inReview" : record.workspaceStatus}` as MessageKey)}</td>
                    <td data-testid={`reports-workspace-source-${record.caseId}`}>
                      <Pill tone={toneForWorkspaceSource(record.source)}>{tr(`reports.workspace.source.${record.source}` as MessageKey)}</Pill>
                    </td>
                    <td>
                      <div className="otc-controls">
                        <button type="button" className="otc-button otc-button--ghost" onClick={() => hydrateWorkspaceRecord(record)}>
                          {tr("reports.workspace.table.load" as MessageKey)}
                        </button>
                        <button type="button" className="otc-button otc-button--ghost" onClick={() => setOpenCaseId(record.caseId)}>
                          {tr("reports.workspace.timeline.open" as MessageKey)}
                        </button>
                        {buildReportContextLinks(
                          buildReportOperationalContext({
                            caseId: record.caseId,
                            reportType: record.reportType,
                            address: record.targetAddress,
                            chain: record.targetChain
                          })
                        ).map((link: OperationalContextLink & { labelKey: MessageKey }) => (
                          <a key={`workspace-${record.caseId}-${link.testIdSuffix}`} className="otc-button otc-button--ghost" href={link.href}>
                            {tr(link.labelKey)}
                          </a>
                        ))}
                        <button type="button" className="otc-button otc-button--ghost" onClick={() => updateWorkspaceStatus(record, "draft")}>
                          {tr("reports.workspace.table.markDraft" as MessageKey)}
                        </button>
                        <button type="button" className="otc-button otc-button--ghost" onClick={() => updateWorkspaceStatus(record, "in_review")}>
                          {tr("reports.workspace.table.markInReview" as MessageKey)}
                        </button>
                        <button type="button" className="otc-button otc-button--ghost" onClick={() => updateWorkspaceStatus(record, "ready")}>
                          {tr("reports.workspace.table.markReady" as MessageKey)}
                        </button>
                        {record.source === "local" ? (
                          <button type="button" className="otc-button otc-button--ghost" onClick={() => removeWorkspaceRecord(record)}>
                            {tr("reports.workspace.table.remove" as MessageKey)}
                          </button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <Message>{tr("reports.workspace.empty" as MessageKey)}</Message>
          )}
        </Panel>

        <WorkItemTimelinePanel
          state={!selectedTimelineRecord ? "empty_selection" : !selectedTimelineRecord.workItemId ? "local_only" : "ready"}
          summary={
            selectedTimelineRecord
              ? tr("reports.workspace.timeline.summary" as MessageKey, {
                  caseId: selectedTimelineRecord.caseId
                })
              : null
          }
          contextBadges={timelineContextBadges}
          localOnlyHint={selectedTimelineRecord ? tr("reports.workspace.timeline.localHint" as MessageKey) : null}
          labels={buildWorkItemTimelineLabels(tr, "reports.workspace.timeline")}
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

        {filteredCases.length ? (
          <table className="otc-table otc-table--spaced">
            <thead>
              <tr>
                <th>{tr("reports.cases.table.caseId" as MessageKey)}</th>
                <th>{tr("reports.cases.table.status" as MessageKey)}</th>
                <th>{tr("reports.cases.table.address" as MessageKey)}</th>
                <th>{tr("reports.cases.table.chain" as MessageKey)}</th>
                <th>{tr("reports.cases.table.createdAt" as MessageKey)}</th>
                <th>{tr("reports.cases.table.completedAt" as MessageKey)}</th>
                <th>{tr("reports.cases.table.actions" as MessageKey)}</th>
              </tr>
            </thead>
            <tbody>
              {filteredCases.map((entry: CaseRow) => (
                <tr key={entry.id}>
                  <td><strong>{entry.id}</strong></td>
                  <td>
                    {(() => {
                      const labelKey = getReportCaseStatusLabelKey(entry.status);
                      return labelKey ? tr(labelKey) : entry.status;
                    })()}
                  </td>
                  <td>{entry.target_address}</td>
                  <td>
                    {(() => {
                      const labelKey = getReportCaseChainLabelKey(entry.target_chain);
                      return labelKey ? tr(labelKey) : entry.target_chain;
                    })()}
                  </td>
                  <td>{formatDate(entry.created_at, locale) ?? t("common.notAvailable")}</td>
                  <td>{formatDate(entry.completed_at, locale) ?? t("common.notAvailable")}</td>
                  <td>
                    <div className="otc-controls">
                      {buildReportContextLinks(
                        buildReportOperationalContext({
                          caseId: entry.id,
                          reportType: selectedReportType,
                          address: entry.target_address,
                          chain: entry.target_chain
                        })
                      ).map((link: OperationalContextLink & { labelKey: MessageKey }) => (
                        <a key={`case-${entry.id}-${link.testIdSuffix}`} className="otc-link-button" href={link.href}>
                          {tr(link.labelKey)}
                        </a>
                      ))}
                      <button type="button" className="otc-link-button" onClick={() => trackCase(entry)} disabled={syncingWorkspace}>
                        {tr("reports.cases.table.track" as MessageKey)}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <Message>{loadingCases ? tr("reports.cases.loading" as MessageKey) : tr("reports.cases.empty" as MessageKey)}</Message>
        )}

        <div className="otc-controls otc-controls--spaced">
          <button type="button" className="otc-button otc-button--ghost" onClick={() => loadCases(Math.max(1, casesPage - 1))} disabled={loadingCases || casesPage <= 1}>
            {tr("reports.cases.previous" as MessageKey)}
          </button>
          <span className="otc-muted">{tr("reports.cases.page" as MessageKey, { page: casesPage })}</span>
          <button type="button" className="otc-button otc-button--ghost" onClick={() => loadCases(casesPage + 1)} disabled={loadingCases || cases.length < casesLimit}>
            {tr("reports.cases.next" as MessageKey)}
          </button>
        </div>
      </Panel>

      <Panel title={tr("reports.history.title" as MessageKey)} description={tr("reports.history.description" as MessageKey)}>
        <div className="otc-controls">
          <label className="otc-field">
            {tr("reports.history.reportId" as MessageKey)}
            <input
              className="otc-input"
              value={historyReportIdFilter}
              onChange={(event) => setHistoryReportIdFilter(event.target.value)}
              data-testid="reports-history-report-id"
            />
          </label>
          <label className="otc-field">
            {tr("reports.history.search" as MessageKey)}
            <input
              className="otc-input"
              value={historySearch}
              placeholder={tr("reports.history.searchPlaceholder" as MessageKey)}
              onChange={(event) => setHistorySearch(event.target.value)}
            />
          </label>
          <label className="otc-field">
            {tr("reports.history.reportType" as MessageKey)}
            <select
              className="otc-select"
              value={historyTypeFilter}
              onChange={(event) => setHistoryTypeFilter(event.target.value)}
              data-testid="reports-history-report-type"
            >
              <option value="all">{tr("reports.cases.filters.all" as MessageKey)}</option>
              {catalog.map((entry) => (
                <option key={entry.canonical} value={entry.canonical}>
                  {formatReportTypeOptionLabel(entry)}
                </option>
              ))}
            </select>
          </label>
          <label className="otc-field">
            {tr("reports.history.caseId" as MessageKey)}
            <input
              className="otc-input"
              value={historyCaseFilter}
              onChange={(event) => setHistoryCaseFilter(event.target.value)}
              data-testid="reports-history-case-id"
            />
          </label>
          <label className="otc-field">
            {tr("reports.history.createdFrom" as MessageKey)}
            <input
              type="datetime-local"
              className="otc-input"
              value={historyCreatedFromFilter}
              onChange={(event) => setHistoryCreatedFromFilter(event.target.value)}
              data-testid="reports-history-created-from"
            />
          </label>
          <label className="otc-field">
            {tr("reports.history.createdTo" as MessageKey)}
            <input
              type="datetime-local"
              className="otc-input"
              value={historyCreatedToFilter}
              onChange={(event) => setHistoryCreatedToFilter(event.target.value)}
              data-testid="reports-history-created-to"
            />
          </label>
          <button
            type="button"
            className="otc-button otc-button--ghost"
            onClick={applyHistoryFilters}
            data-testid="reports-history-apply"
          >
            {tr("reports.history.apply" as MessageKey)}
          </button>
          <button type="button" className="otc-button otc-button--ghost" onClick={clearHistoryFilters} data-testid="reports-history-clear">
            {tr("reports.history.clear" as MessageKey)}
          </button>
          <button type="button" className="otc-button otc-button--ghost" onClick={() => void loadReportHistory(historyPage)} data-testid="reports-history-refresh">
            {tr("reports.history.refresh" as MessageKey)}
          </button>
          <button
            type="button"
            className="otc-button otc-button--ghost"
            onClick={() => openReportFromHistory(historyReportIdFilter)}
            disabled={!historyReportIdFilter.trim() || loadingReportDetail}
            data-testid="reports-history-load-detail"
          >
            {loadingReportDetail ? tr("reports.history.loadDetailLoading" as MessageKey) : tr("reports.history.loadDetail" as MessageKey)}
          </button>
        </div>
        {(() => {
          if (!filteredHistoryRows.length) {
            return <Message>{loadingHistory ? t("common.loading") : tr("reports.history.empty" as MessageKey)}</Message>;
          }
          return (
            <table className="otc-table otc-table--spaced" data-testid="reports-history-table">
              <thead>
                <tr>
                  <th>{tr("reports.history.reportId" as MessageKey)}</th>
                  <th>{tr("reports.history.caseId" as MessageKey)}</th>
                  <th>{tr("reports.history.reportType" as MessageKey)}</th>
                  <th>{tr("reports.history.downloaded" as MessageKey)}</th>
                  <th>{tr("reports.history.lastAction" as MessageKey)}</th>
                </tr>
              </thead>
              <tbody>
                {filteredHistoryRows.map((record: ReportHistoryRow) => (
                  <tr
                    key={record.report_id}
                    className={selectedReportDetail?.report_id === record.report_id ? "otc-row-selected otc-row-clickable" : "otc-row-clickable"}
                    onClick={() => {
                      setOpenCaseId(record.case_id ?? "");
                      openReportFromHistory(record.report_id);
                    }}
                    data-testid="reports-history-row"
                  >
                    <td>
                      <strong className="otc-mono">{record.report_id}</strong>
                    </td>
                    <td><strong>{record.case_id || tr("reports.history.notAvailable" as MessageKey)}</strong></td>
                    <td>
                      <Pill>{renderReportTypeValue(record.report_type)}</Pill>
                    </td>
                    <td>
                      <Pill tone={record.has_download_audit ? "success" : "warning"}>
                        {record.has_download_audit
                          ? tr("reports.history.downloadedYes" as MessageKey)
                          : tr("reports.history.downloadedNo" as MessageKey)}
                      </Pill>
                    </td>
                    <td>{formatDate(record.created_at, locale) ?? record.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          );
        })()}

        <div className="otc-controls otc-controls--spaced">
          <button
            type="button"
            className="otc-button otc-button--ghost"
            onClick={() => void loadReportHistory(Math.max(1, historyPage - 1))}
            disabled={loadingHistory || historyPage <= 1}
            data-testid="reports-history-prev"
          >
            {tr("reports.history.previous" as MessageKey)}
          </button>
          <span className="otc-muted" data-testid="reports-history-page">
            {tr("reports.history.pagination" as MessageKey, { page: historyPage, total: historyTotal })}
          </span>
          <button
            type="button"
            className="otc-button otc-button--ghost"
            onClick={() => void loadReportHistory(historyPage + 1)}
            disabled={loadingHistory || !historyHasMore}
            data-testid="reports-history-next"
          >
            {tr("reports.history.next" as MessageKey)}
          </button>
        </div>
      </Panel>

      <Panel
        title={tr("reports.detail.title" as MessageKey)}
        description={tr("reports.detail.description" as MessageKey)}
        actions={
          <div className="otc-controls">
            <button
              type="button"
              className="otc-button otc-button--ghost"
              onClick={() => openReportFromHistory(historyReportIdFilter)}
              disabled={!historyReportIdFilter.trim() || loadingReportDetail}
              data-testid="reports-detail-refresh"
            >
              {loadingReportDetail ? tr("reports.detail.refreshing" as MessageKey) : tr("reports.detail.refresh" as MessageKey)}
            </button>
            {linkedRosLoading ? (
              <button type="button" className="otc-button otc-button--ghost" disabled>
                {tr("reports.detail.loadingRosCoaf" as MessageKey)}
              </button>
            ) : linkedRosId ? (
              <a className="otc-button" href={`/ros-coaf?ros_id=${encodeURIComponent(linkedRosId)}`}>
                {tr("reports.detail.openRosCoaf" as MessageKey)}
              </a>
            ) : null}
            <button
              type="button"
              className="otc-button otc-button--ghost"
              onClick={() => setSelectedReportDetail(null)}
              disabled={!selectedReportDetail}
              data-testid="reports-detail-clear"
            >
              {tr("reports.detail.clear" as MessageKey)}
            </button>
          </div>
        }
      >
        {!selectedReportDetail ? (
          <div data-testid="reports-detail-empty">
            <Message>{tr("reports.detail.empty" as MessageKey)}</Message>
          </div>
        ) : (
          <>
            <div className="otc-controls" data-testid="reports-detail-actions">
              {buildReportContextLinks(
                buildReportOperationalContext({
                  caseId: selectedReportDetail.case_id,
                  reportId: selectedReportDetail.report_id
                })
              ).map((link: OperationalContextLink & { labelKey: MessageKey }) => (
                <a
                  key={`detail-${selectedReportDetail.report_id}-${link.testIdSuffix}`}
                  className={link.kind === "case" ? "otc-button" : "otc-button otc-button--ghost"}
                  href={link.href}
                >
                  {tr(link.labelKey)}
                </a>
              ))}
              <button
                type="button"
                className="otc-button otc-button--ghost"
                onClick={() => {
                  void exportEvidenceBundleForReport(selectedReportDetail);
                }}
                disabled={exportingEvidenceBundle}
                data-testid="reports-detail-export-evidence"
              >
                {exportingEvidenceBundle
                  ? tr("reports.detail.exportEvidenceLoading" as MessageKey)
                  : tr("reports.detail.exportEvidence" as MessageKey)}
              </button>
              <button
                type="button"
                className="otc-button otc-button--ghost"
                onClick={() => {
                  void exportFormalDossierForReport(selectedReportDetail);
                }}
                disabled={exportingFormalDossier}
                data-testid="reports-detail-export-dossier"
              >
                {exportingFormalDossier ? tr("reports.dossier.exportLoading" as MessageKey) : tr("reports.dossier.export" as MessageKey)}
              </button>
              <a
                className="otc-button otc-button--ghost"
                href={`/api/app/reports/download?report_id=${encodeURIComponent(selectedReportDetail.report_id)}&case_id=${encodeURIComponent(
                  selectedReportDetail.case_id
                )}&report_type=${encodeURIComponent(selectedReportDetail.report_type)}&created_at=${encodeURIComponent(selectedReportDetail.created_at)}`}
              >
                {tr("reports.detail.download" as MessageKey)}
              </a>
            </div>

            <table className="otc-table otc-table--spaced" data-testid="reports-detail-table">
              <tbody>
                <tr>
                  <th>{tr("reports.detail.reportId" as MessageKey)}</th>
                  <td className="otc-mono">{selectedReportDetail.report_id}</td>
                </tr>
                <tr>
                  <th>{tr("reports.detail.caseId" as MessageKey)}</th>
                  <td className="otc-mono">{selectedReportDetail.case_id}</td>
                </tr>
                <tr>
                  <th>{tr("reports.detail.canonicalType" as MessageKey)}</th>
                  <td>{renderReportTypeValue(selectedReportDetail.report_type)}</td>
                </tr>
                <tr>
                  <th>{tr("reports.detail.requestedType" as MessageKey)}</th>
                  <td>{renderRequestedReportTypeValue(selectedReportDetail.report_type_requested)}</td>
                </tr>
                <tr>
                  <th>{tr("reports.detail.createdAt" as MessageKey)}</th>
                  <td>{formatDate(selectedReportDetail.created_at, locale) ?? selectedReportDetail.created_at}</td>
                </tr>
                <tr>
                  <th>{tr("reports.detail.contentType" as MessageKey)}</th>
                  <td>{selectedReportDetail.content_type}</td>
                </tr>
                <tr>
                  <th>{tr("reports.detail.fileHash" as MessageKey)}</th>
                  <td className="otc-mono">{selectedReportDetail.file_hash_sha256}</td>
                </tr>
                <tr>
                  <th>{tr("reports.detail.onchainHash" as MessageKey)}</th>
                  <td className="otc-mono">{selectedReportDetail.onchain_hash || t("common.notAvailable")}</td>
                </tr>
              </tbody>
            </table>
            {selectedReportFormalDossier ? (
              <Panel title={tr("reports.dossier.title" as MessageKey)} description={tr("reports.dossier.description" as MessageKey)}>
                <table className="otc-table otc-table--spaced" data-testid="reports-dossier-table">
                  <tbody>
                    {REPORT_FORMAL_DOSSIER_SUMMARY_FIELDS.map((field) => (
                      <tr key={field}>
                        <th>{tr(REPORT_DOSSIER_FIELD_LABEL_KEYS[field])}</th>
                        <td>{renderDossierSummaryValue(selectedReportFormalDossier[field])}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Panel>
            ) : null}
            {selectedReportWorkspaceRecord ? (
              <Panel title={tr("reports.workspace.title" as MessageKey)} description={tr("reports.workspace.description" as MessageKey)}>
                <table className="otc-table otc-table--spaced" data-testid="reports-detail-workspace-table">
                  <tbody>
                    <tr>
                      <th>{tr("reports.workspace.table.caseId" as MessageKey)}</th>
                      <td>{selectedReportWorkspaceRecord.caseId}</td>
                    </tr>
                    <tr>
                      <th>{tr("reports.workspace.table.reportType" as MessageKey)}</th>
                      <td>{renderReportTypeValue(selectedReportWorkspaceRecord.reportType)}</td>
                    </tr>
                    <tr>
                      <th>{tr("reports.workspace.table.owner" as MessageKey)}</th>
                      <td>{selectedReportWorkspaceRecord.owner || t("common.notAvailable")}</td>
                    </tr>
                    <tr>
                      <th>{tr("reports.workspace.table.priority" as MessageKey)}</th>
                      <td>{t(`common.priority.${selectedReportWorkspaceRecord.priority}` as MessageKey)}</td>
                    </tr>
                    <tr>
                      <th>{tr("reports.workspace.table.deadline" as MessageKey)}</th>
                      <td>
                        {(formatDate(selectedReportWorkspaceRecord.localDeadline, locale) ?? selectedReportWorkspaceRecord.localDeadline) ||
                          t("common.notAvailable")}
                      </td>
                    </tr>
                    <tr>
                      <th>{tr("reports.workspace.table.sla" as MessageKey)}</th>
                      <td>
                        <Pill tone={toneForSla(selectedReportWorkspaceRecord)}>
                          {tr(
                            selectedReportWorkspaceRecord.slaBreached
                              ? ("reports.workspace.sla.breached" as MessageKey)
                              : ("reports.workspace.sla.onTrack" as MessageKey)
                          )}
                        </Pill>
                      </td>
                    </tr>
                    <tr>
                      <th>{tr("reports.workspace.table.status" as MessageKey)}</th>
                      <td>{tr(getWorkspaceStatusLabelKey(selectedReportWorkspaceRecord.workspaceStatus) as MessageKey)}</td>
                    </tr>
                    <tr>
                      <th>{tr("reports.workspace.table.source" as MessageKey)}</th>
                      <td>{tr(`reports.workspace.source.${selectedReportWorkspaceRecord.source}` as MessageKey)}</td>
                    </tr>
                    <tr>
                      <th>{tr("reports.detail.reportExternalId" as MessageKey)}</th>
                      <td>{selectedReportWorkspaceRecord.reportExternalId || t("common.notAvailable")}</td>
                    </tr>
                    <tr>
                      <th>{tr("reports.detail.lastHandoff" as MessageKey)}</th>
                      <td>
                        {selectedReportLastHandoff ? (
                          <div className="otc-stack">
                            <span>{selectedReportLastHandoff.body}</span>
                            <span className="otc-muted">
                              {formatDate(selectedReportLastHandoff.created_at, locale) ?? selectedReportLastHandoff.created_at}
                            </span>
                          </div>
                        ) : (
                          t("common.notAvailable")
                        )}
                      </td>
                    </tr>
                    <tr>
                      <th>{tr("reports.workspace.filters.note" as MessageKey)}</th>
                      <td>{selectedReportWorkspaceRecord.note || t("common.notAvailable")}</td>
                    </tr>
                  </tbody>
                </table>
              </Panel>
            ) : null}
          </>
        )}
      </Panel>
    </AppShell>
  );
}

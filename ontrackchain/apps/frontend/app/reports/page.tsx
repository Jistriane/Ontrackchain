"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useI18n } from "../../components/i18n-provider";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import type { MessageKey } from "../lib/i18n";

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

type WorkspacePriority = "critical" | "high" | "normal";
type WorkspaceStatus = "draft" | "in_review" | "ready";
type WorkspaceSource = "server" | "local";
type WorkItemQueueStatus = "UNDER_REVIEW" | "ESCALATED" | "READY" | "APPROVED" | "SUBMITTED" | "CLOSED" | "REJECTED";

type WorkItemResponse = {
  id: string;
  resource_id: string;
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

type ReportWorkspaceRecord = {
  workItemId?: string;
  resourceId: string;
  source: WorkspaceSource;
  caseId: string;
  targetAddress: string;
  targetChain: string;
  reportType: string;
  owner: string;
  priority: WorkspacePriority;
  localDeadline: string;
  workspaceStatus: WorkspaceStatus;
  note: string;
  lastActionAt: string;
};

const STORAGE_KEY = "otc-reports-workspace";
const WORKSPACE_PAGE_LIMIT = 100;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function formatDate(value: string | null | undefined) {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(parsed);
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
  if (value === "draft" || value === "in_review" || value === "ready") {
    return value;
  }
  return "draft";
}

function toPlanRank(plan: string) {
  const normalized = plan.toLowerCase();
  if (normalized === "free") return 0;
  if (normalized === "starter") return 1;
  if (normalized === "professional") return 2;
  if (normalized === "enterprise") return 3;
  return 99;
}

function buildCaseHref(caseId: string) {
  const normalizedCaseId = caseId.trim();
  return normalizedCaseId ? `/cases/${encodeURIComponent(normalizedCaseId)}` : null;
}

function buildAuditHref(caseId: string) {
  const normalizedCaseId = caseId.trim();
  const params = new URLSearchParams({
    request_id: normalizedCaseId,
    resource_type: "case",
    resource_id: normalizedCaseId
  });
  return `/audit?${params.toString()}`;
}

function buildEvidenceHref(caseId: string) {
  const normalizedCaseId = caseId.trim();
  const params = new URLSearchParams({
    domain: "reports",
    request_id: normalizedCaseId,
    resource_type: "case",
    resource_id: normalizedCaseId
  });
  return `/evidence?${params.toString()}`;
}

function buildInvestigateHref(reportType: string, address: string, chain: string) {
  const params = new URLSearchParams();
  if (reportType.trim()) {
    params.set("report_type", reportType.trim());
  }
  if (address.trim()) {
    params.set("address", address.trim());
  }
  if (chain.trim()) {
    params.set("chain", chain.trim());
  }
  return `/investigate?${params.toString()}`;
}

function loadWorkspace() {
  if (typeof window === "undefined") {
    return [] as ReportWorkspaceRecord[];
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed)
      ? parsed.map((entry) => {
          const record = (entry ?? {}) as Partial<ReportWorkspaceRecord>;
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

function saveWorkspace(records: ReportWorkspaceRecord[]) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
}

function upsertWorkspaceRecord(
  current: ReportWorkspaceRecord[],
  next: Partial<ReportWorkspaceRecord> & { caseId: string }
) {
  const existing = current.find((entry) => entry.caseId === next.caseId);
  const base: ReportWorkspaceRecord =
    existing ?? {
      workItemId: next.workItemId,
      resourceId: next.resourceId ?? next.caseId,
      source: next.source ?? "local",
      caseId: next.caseId,
      targetAddress: "",
      targetChain: "",
      reportType: "",
      owner: "",
      priority: "normal",
      localDeadline: "",
      workspaceStatus: "draft",
      note: "",
      lastActionAt: ""
    };

  const merged: ReportWorkspaceRecord = {
    ...base,
    ...next,
    lastActionAt: next.lastActionAt ?? new Date().toISOString()
  };

  return [merged, ...current.filter((entry) => entry.caseId !== next.caseId)].sort((left, right) =>
    (right.lastActionAt || "").localeCompare(left.lastActionAt || "")
  );
}

function mergeWorkspaceRecords(serverRecords: ReportWorkspaceRecord[], localRecords: ReportWorkspaceRecord[]) {
  const merged = [...serverRecords];
  const seenCaseIds = new Set(serverRecords.map((record) => record.caseId));
  const seenWorkItemIds = new Set(serverRecords.map((record) => record.workItemId).filter(Boolean));

  for (const record of localRecords) {
    if (seenCaseIds.has(record.caseId)) {
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
    return "ready";
  }
  return "in_review";
}

function mapWorkItemToWorkspaceRecord(item: WorkItemResponse): ReportWorkspaceRecord {
  const metadata = item.metadata ?? {};
  const caseId = readMetadataString(metadata, "case_id") || item.resource_id;
  return {
    workItemId: item.id,
    resourceId: item.resource_id,
    source: "server",
    caseId,
    targetAddress: readMetadataString(metadata, "target_address"),
    targetChain: readMetadataString(metadata, "target_chain"),
    reportType: readMetadataString(metadata, "report_type"),
    owner: readMetadataString(metadata, "owner_label"),
    priority: item.priority,
    localDeadline: toDateTimeLocalValue(item.due_at),
    workspaceStatus: normalizeLegacyStatus(metadata["local_workspace_status"]) || mapQueueStatusToWorkspaceStatus(item.queue_status),
    note: item.note ?? readMetadataString(metadata, "note"),
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

export default function ReportsPage() {
  const searchParams = useSearchParams();
  const { t } = useI18n();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);

  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [loadingCases, setLoadingCases] = useState(false);
  const [syncingWorkspace, setSyncingWorkspace] = useState(false);
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
  const [owner, setOwner] = useState("");
  const [priority, setPriority] = useState<WorkspacePriority>("normal");
  const [localDeadline, setLocalDeadline] = useState("");
  const [workspaceStatus, setWorkspaceStatus] = useState<WorkspaceStatus>("draft");
  const [workspaceNote, setWorkspaceNote] = useState("");

  const availableReportCount = useMemo(() => catalog.filter((entry) => entry.available).length, [catalog]);
  const deprecatedReportCount = useMemo(() => catalog.filter((entry) => Boolean(entry.deprecated)).length, [catalog]);
  const minimumPlanReports = useMemo(() => {
    return catalog.reduce<Record<string, number>>((acc, entry) => {
      const plan = entry.min_plan ?? "unknown";
      acc[plan] = (acc[plan] ?? 0) + 1;
      return acc;
    }, {});
  }, [catalog]);

  const filteredCatalog = useMemo(() => {
    const query = catalogSearch.trim().toLowerCase();
    return catalog
      .filter((entry) => {
        if (catalogFilterAvailability === "available") return entry.available;
        if (catalogFilterAvailability === "unavailable") return !entry.available;
        return true;
      })
      .filter((entry) => {
        if (catalogFilterPlan === "all") return true;
        const minPlan = (entry.min_plan ?? "").toLowerCase();
        return minPlan === catalogFilterPlan;
      })
      .filter((entry) => {
        if (!query) return true;
        return entry.canonical.toLowerCase().includes(query) || entry.label.toLowerCase().includes(query);
      })
      .sort((a, b) => {
        const rankDiff = toPlanRank(String(a.min_plan ?? "unknown")) - toPlanRank(String(b.min_plan ?? "unknown"));
        if (rankDiff !== 0) return rankDiff;
        return a.canonical.localeCompare(b.canonical);
      });
  }, [catalog, catalogFilterAvailability, catalogFilterPlan, catalogSearch]);

  const filteredCases = useMemo(() => {
    const query = casesSearch.trim().toLowerCase();
    return cases.filter((entry) => {
      if (!query) return true;
      return (
        entry.id.toLowerCase().includes(query) ||
        entry.target_address.toLowerCase().includes(query) ||
        entry.target_chain.toLowerCase().includes(query) ||
        entry.status.toLowerCase().includes(query)
      );
    });
  }, [cases, casesSearch]);

  const quickCaseHref = buildCaseHref(openCaseId);
  const quickAuditHref = openCaseId.trim() ? buildAuditHref(openCaseId) : null;
  const quickEvidenceHref = openCaseId.trim() ? buildEvidenceHref(openCaseId) : null;
  const quickInvestigateHref = openCaseId.trim()
    ? buildInvestigateHref(
        selectedReportType,
        cases.find((entry) => entry.id === openCaseId)?.target_address ?? "",
        cases.find((entry) => entry.id === openCaseId)?.target_chain ?? ""
      )
    : null;

  async function loadOperationalWorkspace(localRecords: ReportWorkspaceRecord[]) {
    const res = await fetch(
      `/api/app/operations/work-items?module=reports&resource_type=formal_report_case&limit=${WORKSPACE_PAGE_LIMIT}`,
      { cache: "no-store" }
    );
    const data = (await res.json().catch(() => null)) as WorkItemListResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setWorkspace(localRecords);
      setNotice(tr("reports.workspace.noticeLoadedLocal" as MessageKey));
      return;
    }

    const items = data && "data" in data && Array.isArray(data.data) ? data.data : [];
    const serverRecords = items.map((item) => mapWorkItemToWorkspaceRecord(item));
    setWorkspace(mergeWorkspaceRecords(serverRecords, localRecords));
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

  useEffect(() => {
    void loadCatalog();
    void loadCases(1);
    const localRecords = loadWorkspace();
    setWorkspace(localRecords);
    loadOperationalWorkspace(localRecords).catch(() => {
      setWorkspace(localRecords);
      setNotice(tr("reports.workspace.noticeLoadedLocal" as MessageKey));
    });
  }, []);

  useEffect(() => {
    saveWorkspace(workspace);
  }, [workspace]);

  useEffect(() => {
    if (selectedReportType || !catalog.length) {
      return;
    }
    const nextReportType = catalog.find((entry) => entry.available && !entry.deprecated)?.canonical ?? catalog[0]?.canonical ?? "";
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
    if (nextChain || nextStatus) {
      void loadCases(1, {
        chainFilter: nextChain ?? casesChainFilter,
        statusFilter: nextStatus ?? casesStatusFilter
      });
    }
  }, [searchParams]);

  useEffect(() => {
    const currentRecord = workspace.find((entry) => entry.caseId === openCaseId.trim());
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
  }, [openCaseId, workspace]);

  function trackCase(entry: CaseRow) {
    void (async () => {
      const nextReportType = selectedReportType.trim();
      const draftRecord: ReportWorkspaceRecord = {
        workItemId: workspace.find((current) => current.caseId === entry.id)?.workItemId,
        resourceId: entry.id,
        source: "local",
        caseId: entry.id,
        targetAddress: entry.target_address,
        targetChain: entry.target_chain,
        reportType: nextReportType,
        owner,
        priority,
        localDeadline,
        workspaceStatus,
        note: workspaceNote,
        lastActionAt: new Date().toISOString()
      };
      setWorkspace((current) => upsertWorkspaceRecord(current, draftRecord));
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

    const localStatus = nextStatus ?? record.workspaceStatus;
    const queueStatus: WorkItemQueueStatus = localStatus === "ready" ? "READY" : "UNDER_REVIEW";
    const metadata = {
      case_id: record.caseId,
      target_address: record.targetAddress,
      target_chain: record.targetChain,
      report_type: record.reportType,
      owner_label: record.owner,
      local_workspace_status: localStatus,
      note: record.note
    };
    const requestBody = record.workItemId
      ? {
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
    const data = (await res.json().catch(() => null)) as WorkItemResponse | { error?: string; detail?: unknown } | null;
    setSyncingWorkspace(false);
    if (!res.ok) {
      throw new Error(resolveApiErrorMessage(t, data, tr("reports.workspace.errorSync" as MessageKey)));
    }

    const nextRecord = mapWorkItemToWorkspaceRecord(data as WorkItemResponse);
    setWorkspace((current) => upsertWorkspaceRecord(current, nextRecord));
    return nextRecord;
  }

  function updateWorkspaceStatus(caseId: string, nextStatus: WorkspaceStatus) {
    void (async () => {
      const currentRecord = workspace.find((entry) => entry.caseId === caseId);
      if (!currentRecord) {
        return;
      }

      const draftRecord = { ...currentRecord, workspaceStatus: nextStatus, lastActionAt: new Date().toISOString() };
      setWorkspace((current) =>
        upsertWorkspaceRecord(current, {
          caseId,
          workspaceStatus: nextStatus,
          lastActionAt: draftRecord.lastActionAt
        })
      );
      try {
        await syncWorkspaceRecord(draftRecord, nextStatus);
      } catch (syncError) {
        setError(syncError instanceof Error ? syncError.message : tr("reports.workspace.errorSync" as MessageKey));
        setNotice(tr("reports.workspace.noticeTrackedLocalOnly" as MessageKey, { caseId }));
      }
    })();
  }

  function removeWorkspaceRecord(caseId: string) {
    setWorkspace((current) => current.filter((entry) => entry.caseId !== caseId));
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
              <option value="free">free</option>
              <option value="starter">starter</option>
              <option value="professional">professional</option>
              <option value="enterprise">enterprise</option>
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
                  <td>{entry.min_plan ?? t("common.notAvailable")}</td>
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
              <option value="ethereum">ethereum</option>
              <option value="bitcoin">bitcoin</option>
              <option value="arbitrum">arbitrum</option>
              <option value="base">base</option>
            </select>
          </label>
          <label className="otc-field">
            {tr("reports.cases.filters.status" as MessageKey)}
            <select className="otc-select" value={casesStatusFilter} onChange={(event) => setCasesStatusFilter(event.target.value)}>
              <option value="all">{tr("reports.cases.filters.all" as MessageKey)}</option>
              <option value="QUEUED">QUEUED</option>
              <option value="PROCESSING">PROCESSING</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="FAILED">FAILED</option>
            </select>
          </label>
          <label className="otc-field">
            {tr("reports.cases.filters.caseId" as MessageKey)}
            <input className="otc-input" value={openCaseId} onChange={(event) => setOpenCaseId(event.target.value)} />
          </label>
          <label className="otc-field">
            {tr("reports.cases.filters.reportType" as MessageKey)}
            <select className="otc-select" value={selectedReportType} onChange={(event) => setSelectedReportType(event.target.value)}>
              <option value="">{tr("reports.cases.filters.none" as MessageKey)}</option>
              {catalog.map((entry) => (
                <option key={entry.canonical} value={entry.canonical}>
                  {entry.label}
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
              <option value="critical">{tr("common.priority.critical" as MessageKey)}</option>
              <option value="high">{tr("common.priority.high" as MessageKey)}</option>
              <option value="normal">{tr("common.priority.normal" as MessageKey)}</option>
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
          {quickCaseHref ? (
            <a className="otc-button" href={quickCaseHref}>
              {tr("reports.cases.openCase" as MessageKey)}
            </a>
          ) : null}
          {quickAuditHref ? (
            <a className="otc-button otc-button--ghost" href={quickAuditHref}>
              {tr("reports.cases.openAudit" as MessageKey)}
            </a>
          ) : null}
          {quickEvidenceHref ? (
            <a className="otc-button otc-button--ghost" href={quickEvidenceHref}>
              {tr("reports.cases.openEvidence" as MessageKey)}
            </a>
          ) : null}
          {quickInvestigateHref ? (
            <a className="otc-button otc-button--ghost" href={quickInvestigateHref}>
              {tr("reports.cases.table.openInvestigate" as MessageKey)}
            </a>
          ) : null}
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
          {workspace.length ? (
            <table className="otc-table otc-table--spaced">
              <thead>
                <tr>
                  <th>{tr("reports.workspace.table.caseId" as MessageKey)}</th>
                  <th>{tr("reports.workspace.table.reportType" as MessageKey)}</th>
                  <th>{tr("reports.workspace.table.owner" as MessageKey)}</th>
                  <th>{tr("reports.workspace.table.priority" as MessageKey)}</th>
                  <th>{tr("reports.workspace.table.deadline" as MessageKey)}</th>
                  <th>{tr("reports.workspace.table.status" as MessageKey)}</th>
                  <th>{tr("reports.workspace.table.actions" as MessageKey)}</th>
                </tr>
              </thead>
              <tbody>
                {workspace.map((record) => (
                  <tr key={record.caseId}>
                    <td>
                      <strong>{record.caseId}</strong>
                      {record.note ? <div className="otc-muted">{record.note}</div> : null}
                    </td>
                    <td>{record.reportType || t("common.notAvailable")}</td>
                    <td>{record.owner || t("common.notAvailable")}</td>
                    <td>{tr(`common.priority.${record.priority}` as MessageKey)}</td>
                    <td>
                      {record.localDeadline ? formatDate(record.localDeadline) ?? record.localDeadline : t("common.notAvailable")}
                      <div className="otc-muted">{tr(`reports.workspace.urgency.${getWorkspaceUrgency(record)}` as MessageKey)}</div>
                    </td>
                    <td>{tr(`reports.workspace.status.${record.workspaceStatus === "in_review" ? "inReview" : record.workspaceStatus}` as MessageKey)}</td>
                    <td>
                      <div className="otc-controls">
                        <Pill tone={record.source === "server" ? "success" : "warning"}>{tr(`reports.workspace.source.${record.source}` as MessageKey)}</Pill>
                        <button type="button" className="otc-button otc-button--ghost" onClick={() => hydrateWorkspaceRecord(record)}>
                          {tr("reports.workspace.table.load" as MessageKey)}
                        </button>
                        <a className="otc-button otc-button--ghost" href={`/cases/${record.caseId}`}>
                          {tr("reports.cases.table.openCase" as MessageKey)}
                        </a>
                        <a className="otc-button otc-button--ghost" href={buildAuditHref(record.caseId)}>
                          {tr("reports.cases.table.openAudit" as MessageKey)}
                        </a>
                        <a className="otc-button otc-button--ghost" href={buildEvidenceHref(record.caseId)}>
                          {tr("reports.cases.table.openEvidence" as MessageKey)}
                        </a>
                        {record.targetAddress ? (
                          <a className="otc-button otc-button--ghost" href={buildInvestigateHref(record.reportType, record.targetAddress, record.targetChain)}>
                            {tr("reports.cases.table.openInvestigate" as MessageKey)}
                          </a>
                        ) : null}
                        <button type="button" className="otc-button otc-button--ghost" onClick={() => updateWorkspaceStatus(record.caseId, "draft")}>
                          {tr("reports.workspace.table.markDraft" as MessageKey)}
                        </button>
                        <button type="button" className="otc-button otc-button--ghost" onClick={() => updateWorkspaceStatus(record.caseId, "in_review")}>
                          {tr("reports.workspace.table.markInReview" as MessageKey)}
                        </button>
                        <button type="button" className="otc-button otc-button--ghost" onClick={() => updateWorkspaceStatus(record.caseId, "ready")}>
                          {tr("reports.workspace.table.markReady" as MessageKey)}
                        </button>
                        {record.source === "local" ? (
                          <button type="button" className="otc-button otc-button--ghost" onClick={() => removeWorkspaceRecord(record.caseId)}>
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
              {filteredCases.map((entry) => (
                <tr key={entry.id}>
                  <td><strong>{entry.id}</strong></td>
                  <td>{entry.status}</td>
                  <td>{entry.target_address}</td>
                  <td>{entry.target_chain}</td>
                  <td>{formatDate(entry.created_at) ?? t("common.notAvailable")}</td>
                  <td>{formatDate(entry.completed_at) ?? t("common.notAvailable")}</td>
                  <td>
                    <div className="otc-controls">
                      <a className="otc-link-button" href={`/cases/${entry.id}`}>
                        {tr("reports.cases.table.openCase" as MessageKey)}
                      </a>
                      <a className="otc-link-button" href={buildAuditHref(entry.id)}>
                        {tr("reports.cases.table.openAudit" as MessageKey)}
                      </a>
                      <a className="otc-link-button" href={buildEvidenceHref(entry.id)}>
                        {tr("reports.cases.table.openEvidence" as MessageKey)}
                      </a>
                      <a className="otc-link-button" href={buildInvestigateHref(selectedReportType, entry.target_address, entry.target_chain)}>
                        {tr("reports.cases.table.openInvestigate" as MessageKey)}
                      </a>
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
    </AppShell>
  );
}

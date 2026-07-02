"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import { useI18n } from "../../components/i18n-provider";
import type { MessageKey } from "../lib/i18n";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";

type SanctionsCheckResponse = {
  address: string;
  chain: string;
  provider: string;
  provider_status: "live" | "degraded";
  degraded_reason?: string | null;
  capability_status: "live" | "degraded";
  lists: string[];
  hit?: boolean | null;
  matched_lists: string[];
  entity_name?: string | null;
  designation_date?: string | null;
  checked_at: string;
};

type WorkspacePriority = "critical" | "high" | "normal";
type WorkspaceStatus = "UNDER_REVIEW" | "ESCALATED" | "READY" | "APPROVED" | "SUBMITTED" | "CLOSED" | "REJECTED";
type WorkspaceSource = "server" | "local";

type WorkItemResponse = {
  id: string;
  module: "sanctions";
  resource_type: "sanctions_screening";
  resource_id: string;
  case_id: string | null;
  owner_user_id: string | null;
  queue_status: WorkspaceStatus;
  priority: WorkspacePriority;
  due_at: string | null;
  title: string | null;
  note: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  last_activity_at: string;
};

type WorkItemListResponse = {
  data: WorkItemResponse[];
};

type SanctionsFormState = {
  address: string;
  chain: string;
  lists: string;
  caseId: string;
  owner: string;
  priority: WorkspacePriority;
  localDeadline: string;
};

type SanctionsWorkspaceRecord = {
  workspaceId: string;
  resourceId: string;
  workItemId?: string;
  source: WorkspaceSource;
  address: string;
  chain: string;
  lists: string[];
  caseId: string;
  owner: string;
  priority: WorkspacePriority;
  localDeadline: string;
  status: WorkspaceStatus;
  provider: string;
  providerStatus: string;
  capabilityStatus: string;
  degradedReason: string;
  matchedLists: string[];
  hit: boolean;
  entityName: string;
  designationDate: string;
  checkedAt: string;
  triageNote: string;
  lastActionAt: string;
};

const DEFAULT_LISTS = "OFAC,UN,EU,COAF";
const STORAGE_KEY = "otc-sanctions-workspace";
const WORKSPACE_PAGE_LIMIT = 100;
const ACTIVE_WORKSPACE_STATUSES = new Set<WorkspaceStatus>(["UNDER_REVIEW", "ESCALATED", "READY", "APPROVED", "SUBMITTED"]);
const TERMINAL_WORKSPACE_STATUSES = new Set<WorkspaceStatus>(["CLOSED", "REJECTED"]);
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const DEFAULT_FORM: SanctionsFormState = {
  address: "",
  chain: "ethereum",
  lists: DEFAULT_LISTS,
  caseId: "",
  owner: "",
  priority: "normal",
  localDeadline: ""
};

function normalizeLegacyStatus(value: unknown): WorkspaceStatus {
  if (value === "UNDER_REVIEW" || value === "ESCALATED" || value === "READY" || value === "APPROVED" || value === "SUBMITTED" || value === "CLOSED" || value === "REJECTED") {
    return value;
  }
  if (value === "HIT") {
    return "UNDER_REVIEW";
  }
  return "CLOSED";
}

function normalizeWorkspaceRecord(record: Partial<SanctionsWorkspaceRecord>): SanctionsWorkspaceRecord {
  const resourceId = typeof record.resourceId === "string" && isUuidLike(record.resourceId) ? record.resourceId : crypto.randomUUID();
  const checkedAt = typeof record.checkedAt === "string" ? record.checkedAt : "";
  const address = typeof record.address === "string" ? record.address : "";
  const chain = typeof record.chain === "string" && record.chain ? record.chain : "ethereum";

  return {
    workspaceId:
      typeof record.workspaceId === "string" && record.workspaceId
        ? record.workspaceId
        : buildWorkspaceIdFromFields(address, chain, checkedAt, resourceId),
    resourceId,
    workItemId: typeof record.workItemId === "string" ? record.workItemId : undefined,
    source: record.source === "server" ? "server" : "local",
    address,
    chain,
    lists: Array.isArray(record.lists) ? record.lists.filter((entry): entry is string => typeof entry === "string") : [],
    caseId: typeof record.caseId === "string" ? record.caseId : "",
    owner: typeof record.owner === "string" ? record.owner : "",
    priority: record.priority === "critical" || record.priority === "high" || record.priority === "normal" ? record.priority : "normal",
    localDeadline: typeof record.localDeadline === "string" ? record.localDeadline : "",
    status: normalizeLegacyStatus(record.status),
    provider: typeof record.provider === "string" ? record.provider : "",
    providerStatus: typeof record.providerStatus === "string" ? record.providerStatus : "",
    capabilityStatus: typeof record.capabilityStatus === "string" ? record.capabilityStatus : "",
    degradedReason: typeof record.degradedReason === "string" ? record.degradedReason : "",
    matchedLists: Array.isArray(record.matchedLists) ? record.matchedLists.filter((entry): entry is string => typeof entry === "string") : [],
    hit: record.hit === true,
    entityName: typeof record.entityName === "string" ? record.entityName : "",
    designationDate: typeof record.designationDate === "string" ? record.designationDate : "",
    checkedAt,
    triageNote: typeof record.triageNote === "string" ? record.triageNote : "",
    lastActionAt: typeof record.lastActionAt === "string" ? record.lastActionAt : checkedAt
  };
}

function loadWorkspace(): SanctionsWorkspaceRecord[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.map((entry) => normalizeWorkspaceRecord((entry ?? {}) as Partial<SanctionsWorkspaceRecord>)) : [];
  } catch {
    return [];
  }
}

function saveWorkspace(records: SanctionsWorkspaceRecord[]) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
}

function buildWorkspaceId(result: SanctionsCheckResponse) {
  return `${result.address}:${result.chain}:${result.checked_at}`;
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

function readMetadataStringArray(metadata: Record<string, unknown>, key: string) {
  const value = metadata[key];
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((entry): entry is string => typeof entry === "string");
}

function readMetadataBoolean(metadata: Record<string, unknown>, key: string) {
  return metadata[key] === true;
}

function buildWorkspaceIdFromFields(address: string, chain: string, checkedAt: string, resourceId: string) {
  if (address && chain && checkedAt) {
    return `${address}:${chain}:${checkedAt}`;
  }
  return resourceId;
}

function upsertWorkspaceRecord(
  current: SanctionsWorkspaceRecord[],
  next: Partial<SanctionsWorkspaceRecord> & { workspaceId: string }
): SanctionsWorkspaceRecord[] {
  const existing = current.find((record) => record.workspaceId === next.workspaceId);
  const base: SanctionsWorkspaceRecord =
    existing ?? {
      workspaceId: next.workspaceId,
      resourceId: next.resourceId ?? crypto.randomUUID(),
      source: next.source ?? "local",
      address: "",
      chain: "ethereum",
      lists: [],
      caseId: "",
      owner: "",
      priority: "normal",
      localDeadline: "",
      status: "UNDER_REVIEW",
      provider: "",
      providerStatus: "",
      capabilityStatus: "",
      degradedReason: "",
      matchedLists: [],
      hit: false,
      entityName: "",
      designationDate: "",
      checkedAt: "",
      triageNote: "",
      lastActionAt: ""
    };

  const merged: SanctionsWorkspaceRecord = {
    ...base,
    ...next,
    lastActionAt: next.lastActionAt ?? new Date().toISOString()
  };

  return [merged, ...current.filter((record) => record.workspaceId !== next.workspaceId)].sort((a, b) =>
    (b.lastActionAt || "").localeCompare(a.lastActionAt || "")
  );
}

function mergeWorkspaceRecords(serverRecords: SanctionsWorkspaceRecord[], localRecords: SanctionsWorkspaceRecord[]) {
  const merged = [...serverRecords];
  const seenWorkspaceIds = new Set(serverRecords.map((record) => record.workspaceId));
  const seenWorkItemIds = new Set(serverRecords.map((record) => record.workItemId).filter(Boolean));
  const seenResourceIds = new Set(serverRecords.map((record) => record.resourceId));

  for (const record of localRecords) {
    if (seenWorkspaceIds.has(record.workspaceId)) {
      continue;
    }
    if (record.workItemId && seenWorkItemIds.has(record.workItemId)) {
      continue;
    }
    if (record.resourceId && seenResourceIds.has(record.resourceId)) {
      continue;
    }
    merged.push(record);
  }

  return merged.sort((a, b) => (b.lastActionAt || "").localeCompare(a.lastActionAt || ""));
}

function deriveStatus(result: SanctionsCheckResponse): WorkspaceStatus {
  return result.hit ? "UNDER_REVIEW" : "CLOSED";
}

function toSanctionsResponse(record: SanctionsWorkspaceRecord): SanctionsCheckResponse {
  return {
    address: record.address,
    chain: record.chain,
    provider: record.provider,
    provider_status: (record.providerStatus || "live") as "live" | "degraded",
    degraded_reason: record.degradedReason || null,
    capability_status: (record.capabilityStatus || "live") as "live" | "degraded",
    lists: record.lists,
    hit: record.hit,
    matched_lists: record.matchedLists,
    entity_name: record.entityName || null,
    designation_date: record.designationDate || null,
    checked_at: record.checkedAt
  };
}

function getUrgency(record: SanctionsWorkspaceRecord): "overdue" | "due_soon" | "on_track" | "no_deadline" {
  if (!record.localDeadline) {
    return "no_deadline";
  }

  if (TERMINAL_WORKSPACE_STATUSES.has(record.status)) {
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

function toneForStatus(status: WorkspaceStatus): "success" | "warning" | "danger" {
  if (status === "ESCALATED" || status === "REJECTED") return "danger";
  if (status === "UNDER_REVIEW") return "warning";
  return "success";
}

function toneForUrgency(urgency: ReturnType<typeof getUrgency>): "warning" | "danger" | undefined {
  if (urgency === "overdue") return "danger";
  if (urgency === "due_soon") return "warning";
  return undefined;
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

function buildAuditHref(caseId: string, resourceId: string, reportId = "") {
  const params = new URLSearchParams({
    resource_type: "case",
    resource_id: resourceId
  });
  if (caseId.trim()) {
    params.set("request_id", caseId.trim());
  }
  if (reportId.trim()) {
    params.set("report_id", reportId.trim());
  }
  return `/audit?${params.toString()}`;
}

function buildEvidenceHref(resourceId: string, caseId: string) {
  const params = new URLSearchParams({
    domain: "sanctions",
    resource_id: resourceId,
    resource_type: "case"
  });
  if (caseId.trim()) {
    params.set("request_id", caseId.trim());
  }
  return `/evidence?${params.toString()}`;
}

function buildBlocksHref(record: { address: string; chain: string; caseId: string; owner: string; priority: WorkspacePriority; localDeadline: string }) {
  const params = new URLSearchParams({
    address: record.address,
    chain: record.chain,
    case_id: record.caseId,
    owner: record.owner,
    priority: record.priority,
    deadline: record.localDeadline,
    autostart: "1"
  });
  return `/blocks?${params.toString()}`;
}

function mapWorkItemToWorkspaceRecord(item: WorkItemResponse): SanctionsWorkspaceRecord {
  const metadata = item.metadata ?? {};
  const checkedAt = readMetadataString(metadata, "checked_at") || item.updated_at;
  const address = readMetadataString(metadata, "address");
  const chain = readMetadataString(metadata, "chain") || "ethereum";
  const workspaceId =
    readMetadataString(metadata, "workspace_id") || buildWorkspaceIdFromFields(address, chain, checkedAt, item.resource_id);

  return {
    workspaceId,
    resourceId: item.resource_id,
    workItemId: item.id,
    source: "server",
    address,
    chain,
    lists: readMetadataStringArray(metadata, "lists"),
    caseId: item.case_id ?? readMetadataString(metadata, "local_case_id"),
    owner: readMetadataString(metadata, "owner_label"),
    priority: item.priority,
    localDeadline: toDateTimeLocalValue(item.due_at),
    status: item.queue_status,
    provider: readMetadataString(metadata, "provider"),
    providerStatus: readMetadataString(metadata, "provider_status"),
    capabilityStatus: readMetadataString(metadata, "capability_status"),
    degradedReason: readMetadataString(metadata, "degraded_reason"),
    matchedLists: readMetadataStringArray(metadata, "matched_lists"),
    hit: readMetadataBoolean(metadata, "hit"),
    entityName: readMetadataString(metadata, "entity_name"),
    designationDate: readMetadataString(metadata, "designation_date"),
    checkedAt,
    triageNote: item.note ?? readMetadataString(metadata, "triage_note"),
    lastActionAt: item.last_activity_at || item.updated_at
  };
}

export default function SanctionsPage() {
  const { t } = useI18n();
  const searchParams = useSearchParams();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);
  const hydratedPrefillKeyRef = useRef<string | null>(null);

  const [form, setForm] = useState<SanctionsFormState>(DEFAULT_FORM);
  const [triageNote, setTriageNote] = useState("");

  const [loading, setLoading] = useState(false);
  const [syncingWorkspace, setSyncingWorkspace] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [result, setResult] = useState<SanctionsCheckResponse | null>(null);

  const [workspaceRecords, setWorkspaceRecords] = useState<SanctionsWorkspaceRecord[]>([]);
  const [workspaceFilter, setWorkspaceFilter] = useState("all");
  const [workspaceSearch, setWorkspaceSearch] = useState("");

  const isHit = Boolean(result?.hit);
  const matchedCount = result?.matched_lists?.length ?? 0;
  const currentWorkspaceId = result ? buildWorkspaceId(result) : null;
  const filteredWorkspaceRecords = useMemo(() => {
    return workspaceRecords.filter((record) => {
      const matchesStatus = workspaceFilter === "all" ? true : record.status === workspaceFilter;
      const search = workspaceSearch.trim().toLowerCase();
      const matchesSearch =
        !search ||
        record.address.toLowerCase().includes(search) ||
        record.caseId.toLowerCase().includes(search) ||
        record.owner.toLowerCase().includes(search) ||
        record.provider.toLowerCase().includes(search);
      return matchesStatus && matchesSearch;
    });
  }, [workspaceFilter, workspaceRecords, workspaceSearch]);
  const hitCount = useMemo(() => workspaceRecords.filter((record) => record.hit).length, [workspaceRecords]);
  const pendingReviewCount = useMemo(
    () => workspaceRecords.filter((record) => record.hit && ACTIVE_WORKSPACE_STATUSES.has(record.status)).length,
    [workspaceRecords]
  );
  const escalatedCount = useMemo(
    () => workspaceRecords.filter((record) => record.status === "ESCALATED").length,
    [workspaceRecords]
  );
  const overdueCount = useMemo(
    () => workspaceRecords.filter((record) => getUrgency(record) === "overdue").length,
    [workspaceRecords]
  );

  async function loadOperationalWorkspace(localRecords: SanctionsWorkspaceRecord[]) {
    const res = await fetch(
      `/api/app/operations/work-items?module=sanctions&resource_type=sanctions_screening&limit=${WORKSPACE_PAGE_LIMIT}`,
      { cache: "no-store" }
    );
    const data = (await res.json().catch(() => null)) as WorkItemListResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setWorkspaceRecords(localRecords);
      setNotice(tr("sanctions.noticeWorkspaceLoadedLocal" as MessageKey));
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
      setNotice(tr("sanctions.noticeWorkspaceLoadedLocal" as MessageKey));
    });
  }, []);

  useEffect(() => {
    saveWorkspace(workspaceRecords);
  }, [workspaceRecords]);

  function updateForm<K extends keyof SanctionsFormState>(key: K, value: SanctionsFormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function hydrateWorkspaceRecord(record: SanctionsWorkspaceRecord) {
    setForm({
      address: record.address,
      chain: record.chain,
      lists: record.lists.join(",") || DEFAULT_LISTS,
      caseId: record.caseId,
      owner: record.owner,
      priority: record.priority,
      localDeadline: record.localDeadline
    });
    setTriageNote(record.triageNote);
    setResult(toSanctionsResponse(record));
  }

  function removeWorkspaceRecord(workspaceId: string) {
    setWorkspaceRecords((current) => current.filter((record) => record.workspaceId !== workspaceId));
  }

  function buildWorkspaceRecordFromCurrentState(
    checked: SanctionsCheckResponse,
    nextForm: SanctionsFormState,
    note: string,
    base?: Partial<SanctionsWorkspaceRecord>
  ): SanctionsWorkspaceRecord {
    const resourceId = base?.resourceId ?? crypto.randomUUID();
    const workspaceId = base?.workspaceId ?? buildWorkspaceIdFromFields(checked.address, checked.chain, checked.checked_at, resourceId);

    return {
      workspaceId,
      resourceId,
      workItemId: base?.workItemId,
      source: base?.source ?? "local",
      address: checked.address,
      chain: checked.chain,
      lists: checked.lists,
      caseId: nextForm.caseId.trim(),
      owner: nextForm.owner.trim(),
      priority: nextForm.priority,
      localDeadline: nextForm.localDeadline,
      status: (base?.status as WorkspaceStatus | undefined) ?? deriveStatus(checked),
      provider: checked.provider,
      providerStatus: checked.provider_status,
      capabilityStatus: checked.capability_status,
      degradedReason: checked.degraded_reason ?? "",
      matchedLists: checked.matched_lists,
      hit: Boolean(checked.hit),
      entityName: checked.entity_name ?? "",
      designationDate: checked.designation_date ?? "",
      checkedAt: checked.checked_at,
      triageNote: note.trim(),
      lastActionAt: checked.checked_at
    };
  }

  async function syncWorkspaceRecord(record: SanctionsWorkspaceRecord, nextStatus?: WorkspaceStatus) {
    const metadata = {
      workspace_id: record.workspaceId,
      address: record.address,
      chain: record.chain,
      lists: record.lists,
      owner_label: record.owner,
      local_case_id: record.caseId,
      provider: record.provider,
      provider_status: record.providerStatus,
      capability_status: record.capabilityStatus,
      degraded_reason: record.degradedReason,
      matched_lists: record.matchedLists,
      hit: record.hit,
      entity_name: record.entityName,
      designation_date: record.designationDate,
      checked_at: record.checkedAt,
      triage_note: record.triageNote
    };
    const requestBody = {
      module: "sanctions",
      resource_type: "sanctions_screening",
      resource_id: record.resourceId,
      ...(isUuidLike(record.caseId) ? { case_id: record.caseId.trim() } : {}),
      priority: record.priority,
      queue_status: nextStatus ?? record.status,
      due_at: toApiDueAt(record.localDeadline),
      title: `${record.hit ? "Sanctions HIT" : "Sanctions clear"} • ${record.address}`,
      note: record.triageNote || null,
      metadata
    };
    const endpoint = record.workItemId ? `/api/app/operations/work-items/${encodeURIComponent(record.workItemId)}` : "/api/app/operations/work-items";
    const method = record.workItemId ? "PATCH" : "POST";
    const body =
      method === "PATCH"
        ? JSON.stringify({
            priority: requestBody.priority,
            queue_status: requestBody.queue_status,
            due_at: requestBody.due_at,
            title: requestBody.title,
            note: requestBody.note,
            metadata: requestBody.metadata
          })
        : JSON.stringify(requestBody);

    setSyncingWorkspace(true);
    const res = await fetch(endpoint, {
      method,
      headers: { "content-type": "application/json" },
      body,
      cache: "no-store"
    });
    const data = (await res.json().catch(() => null)) as WorkItemResponse | { error?: string; detail?: unknown } | null;
    setSyncingWorkspace(false);
    if (!res.ok) {
      throw new Error(resolveApiErrorMessage(t, data, tr("sanctions.errorWorkspaceSync" as MessageKey)));
    }

    const nextRecord = mapWorkItemToWorkspaceRecord(data as WorkItemResponse);
    setWorkspaceRecords((current) => upsertWorkspaceRecord(current, nextRecord));
    return nextRecord;
  }

  async function updateWorkspaceStatus(status: WorkspaceStatus) {
    if (!result) {
      return;
    }

    setError(null);
    setNotice(null);
    const baseRecord = workspaceRecords.find((record) => record.workspaceId === currentWorkspaceId) ?? undefined;
    const draftRecord = buildWorkspaceRecordFromCurrentState(result, form, triageNote, baseRecord);
    draftRecord.status = status;
    draftRecord.lastActionAt = new Date().toISOString();

    setWorkspaceRecords((current) => upsertWorkspaceRecord(current, draftRecord));

    try {
      await syncWorkspaceRecord(draftRecord, status);
      setNotice(tr("sanctions.noticeWorkspaceUpdated" as MessageKey));
    } catch (syncError) {
      setNotice(tr("sanctions.noticeCheckedLocalOnly" as MessageKey));
      setError(syncError instanceof Error ? syncError.message : tr("sanctions.errorWorkspaceSync" as MessageKey));
    }
  }

  async function runSanctionsCheck(nextForm: SanctionsFormState) {
    setError(null);
    setNotice(null);
    setLoading(true);
    setResult(null);

    const query = new URLSearchParams({
      address: nextForm.address.trim(),
      chain: nextForm.chain,
      lists: nextForm.lists.trim() || DEFAULT_LISTS
    });

    const res = await fetch(`/api/app/compliance/sanctions-check?${query.toString()}`, { cache: "no-store" });
    const data = (await res.json().catch(() => null)) as SanctionsCheckResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setError(resolveApiErrorMessage(t, data, tr("sanctions.errorCheck" as MessageKey)));
      setLoading(false);
      return;
    }

    const checked = data as SanctionsCheckResponse;
    setResult(checked);
    const draftRecord = buildWorkspaceRecordFromCurrentState(checked, nextForm, triageNote);
    setWorkspaceRecords((current) => upsertWorkspaceRecord(current, draftRecord));
    try {
      await syncWorkspaceRecord(draftRecord);
      setNotice(tr("sanctions.noticeCheckedSynced" as MessageKey));
    } catch (syncError) {
      setNotice(tr("sanctions.noticeCheckedLocalOnly" as MessageKey));
      setError(syncError instanceof Error ? syncError.message : tr("sanctions.errorWorkspaceSync" as MessageKey));
    }
    setLoading(false);
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runSanctionsCheck(form);
  }

  useEffect(() => {
    const nextForm: SanctionsFormState = {
      address: searchParams.get("address") ?? DEFAULT_FORM.address,
      chain: searchParams.get("chain") ?? DEFAULT_FORM.chain,
      lists: searchParams.get("lists") ?? DEFAULT_FORM.lists,
      caseId: searchParams.get("case_id") ?? DEFAULT_FORM.caseId,
      owner: searchParams.get("owner") ?? DEFAULT_FORM.owner,
      priority: ((searchParams.get("priority") as WorkspacePriority | null) ?? DEFAULT_FORM.priority),
      localDeadline: searchParams.get("deadline") ?? DEFAULT_FORM.localDeadline
    };
    const triage = searchParams.get("triage_note") ?? "";
    const shouldAutostart = searchParams.get("autostart") === "1";
    const prefillKey = JSON.stringify({ ...nextForm, triage, shouldAutostart });

    setForm(nextForm);
    setTriageNote(triage);

    if (shouldAutostart && nextForm.address.trim() && hydratedPrefillKeyRef.current !== prefillKey) {
      hydratedPrefillKeyRef.current = prefillKey;
      void runSanctionsCheck(nextForm);
    }
  }, [searchParams]);

  return (
    <AppShell
      title={tr("sanctions.title" as MessageKey)}
      subtitle={tr("sanctions.subtitle" as MessageKey)}
      activePath="/sanctions"
      actions={<Pill>{tr("sanctions.active" as MessageKey)}</Pill>}
    >
      <MetricGrid>
        <MetricCard label={tr("sanctions.stats.hitQueue" as MessageKey)} value={hitCount} meta={tr("sanctions.stats.hitQueueMeta" as MessageKey)} accent />
        <MetricCard label={tr("sanctions.stats.pendingReview" as MessageKey)} value={pendingReviewCount} meta={tr("sanctions.stats.pendingReviewMeta" as MessageKey)} />
        <MetricCard label={tr("sanctions.stats.escalated" as MessageKey)} value={escalatedCount} meta={tr("sanctions.stats.escalatedMeta" as MessageKey)} />
        <MetricCard label={tr("sanctions.stats.overdue" as MessageKey)} value={overdueCount} meta={tr("sanctions.stats.overdueMeta" as MessageKey)} />
      </MetricGrid>

      <Panel title={tr("sanctions.form.title" as MessageKey)} description={tr("sanctions.form.description" as MessageKey)}>
        <form className="otc-stack" onSubmit={onSubmit}>
          <div className="otc-grid otc-grid--counterparty-form">
            <label className="otc-field">
              {tr("sanctions.form.address" as MessageKey)}
              <input className="otc-input" data-testid="sanctions-address" value={form.address} onChange={(event) => updateForm("address", event.target.value)} required />
            </label>
            <label className="otc-field">
              {tr("sanctions.form.chain" as MessageKey)}
              <select className="otc-select" data-testid="sanctions-chain" value={form.chain} onChange={(event) => updateForm("chain", event.target.value)}>
                <option value="ethereum">Ethereum</option>
                <option value="polygon">Polygon</option>
                <option value="bsc">BSC</option>
                <option value="arbitrum">Arbitrum</option>
                <option value="base">Base</option>
                <option value="bitcoin">Bitcoin</option>
              </select>
            </label>
            <label className="otc-field">
              {tr("sanctions.form.lists" as MessageKey)}
              <input className="otc-input" value={form.lists} onChange={(event) => updateForm("lists", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("sanctions.form.caseId" as MessageKey)}
              <input className="otc-input" value={form.caseId} onChange={(event) => updateForm("caseId", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("sanctions.form.owner" as MessageKey)}
              <input className="otc-input" value={form.owner} onChange={(event) => updateForm("owner", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("sanctions.form.priority" as MessageKey)}
              <select className="otc-select" value={form.priority} onChange={(event) => updateForm("priority", event.target.value as WorkspacePriority)}>
                <option value="critical">{tr("sanctions.priority.critical" as MessageKey)}</option>
                <option value="high">{tr("sanctions.priority.high" as MessageKey)}</option>
                <option value="normal">{tr("sanctions.priority.normal" as MessageKey)}</option>
              </select>
            </label>
            <label className="otc-field">
              {tr("sanctions.form.localDeadline" as MessageKey)}
              <input className="otc-input" type="datetime-local" value={form.localDeadline} onChange={(event) => updateForm("localDeadline", event.target.value)} />
            </label>
          </div>

          <div className="otc-controls">
            <button className="otc-button otc-button--accent" type="submit" data-testid="sanctions-check-btn" disabled={loading}>
              {loading ? tr("sanctions.form.submitting" as MessageKey) : tr("sanctions.form.submit" as MessageKey)}
            </button>
            <button
              className="otc-button"
              type="button"
              onClick={() => {
                setForm(DEFAULT_FORM);
                setTriageNote("");
              }}
              disabled={loading}
            >
              {tr("sanctions.form.reset" as MessageKey)}
            </button>
          </div>
          {error ? <Message tone="error">{error}</Message> : null}
          {notice ? <Message tone="success">{notice}</Message> : null}
        </form>
      </Panel>

      <Panel title={tr("sanctions.workspace.title" as MessageKey)} description={tr("sanctions.workspace.description" as MessageKey)}>
        <div className="otc-controls">
          <label className="otc-field">
            {tr("sanctions.workspace.filterStatus" as MessageKey)}
            <select className="otc-select" value={workspaceFilter} onChange={(event) => setWorkspaceFilter(event.target.value)}>
              <option value="all">{tr("sanctions.workspace.all" as MessageKey)}</option>
                <option value="UNDER_REVIEW">{tr("sanctions.workspace.status.under_review" as MessageKey)}</option>
                <option value="ESCALATED">{tr("sanctions.workspace.status.escalated" as MessageKey)}</option>
                <option value="READY">{tr("sanctions.workspace.status.ready" as MessageKey)}</option>
                <option value="APPROVED">{tr("sanctions.workspace.status.approved" as MessageKey)}</option>
                <option value="SUBMITTED">{tr("sanctions.workspace.status.submitted" as MessageKey)}</option>
                <option value="CLOSED">{tr("sanctions.workspace.status.closed" as MessageKey)}</option>
                <option value="REJECTED">{tr("sanctions.workspace.status.rejected" as MessageKey)}</option>
            </select>
          </label>
          <label className="otc-field">
            {tr("sanctions.workspace.search" as MessageKey)}
            <input className="otc-input" value={workspaceSearch} onChange={(event) => setWorkspaceSearch(event.target.value)} />
          </label>
        </div>

        {filteredWorkspaceRecords.length ? (
          <table className="otc-table otc-table--spaced">
            <thead>
              <tr>
                <th>{tr("sanctions.workspace.address" as MessageKey)}</th>
                <th>{tr("sanctions.workspace.caseId" as MessageKey)}</th>
                <th>{tr("sanctions.workspace.owner" as MessageKey)}</th>
                <th>{tr("sanctions.workspace.priority" as MessageKey)}</th>
                <th>{tr("sanctions.workspace.deadline" as MessageKey)}</th>
                <th>{tr("sanctions.workspace.urgency" as MessageKey)}</th>
                <th>{tr("sanctions.workspace.status" as MessageKey)}</th>
                <th>{tr("sanctions.workspace.actions" as MessageKey)}</th>
              </tr>
            </thead>
            <tbody>
              {filteredWorkspaceRecords.map((record) => {
                const urgency = getUrgency(record);
                return (
                  <tr key={record.workspaceId}>
                    <td>
                      <strong>{record.address}</strong>
                      <div className="otc-muted">{record.provider}</div>
                    </td>
                    <td>{record.caseId || tr("sanctions.workspace.noCaseId" as MessageKey)}</td>
                    <td>{record.owner || tr("sanctions.workspace.unassigned" as MessageKey)}</td>
                    <td>
                      <Pill tone={record.priority === "critical" ? "danger" : record.priority === "high" ? "warning" : undefined}>
                        {tr(`sanctions.priority.${record.priority}` as MessageKey)}
                      </Pill>
                    </td>
                    <td>{formatDate(record.localDeadline) ?? tr("sanctions.workspace.noDeadline" as MessageKey)}</td>
                    <td>
                      <Pill tone={toneForUrgency(urgency)}>{tr(`sanctions.urgency.${urgency}` as MessageKey)}</Pill>
                    </td>
                    <td>
                      <Pill tone={toneForStatus(record.status)}>{tr(`sanctions.workspace.status.${record.status.toLowerCase()}` as MessageKey)}</Pill>
                    </td>
                    <td>
                      <div className="otc-controls">
                        <Pill tone={record.source === "server" ? "success" : "warning"}>
                          {tr(`sanctions.workspace.source.${record.source}` as MessageKey)}
                        </Pill>
                        <button type="button" className="otc-button otc-button--ghost" onClick={() => hydrateWorkspaceRecord(record)}>
                          {tr("sanctions.workspace.load" as MessageKey)}
                        </button>
                        {record.caseId ? (
                          <a className="otc-button otc-button--ghost" href={`/cases/${record.caseId}`}>
                            {tr("sanctions.workspace.openCase" as MessageKey)}
                          </a>
                        ) : null}
                        <a className="otc-button otc-button--ghost" href={buildAuditHref(record.caseId, record.caseId || record.address)}>
                          {tr("sanctions.workspace.openAudit" as MessageKey)}
                        </a>
                        <a className="otc-button otc-button--ghost" href={buildEvidenceHref(record.caseId || record.address, record.caseId)}>
                          {tr("sanctions.workspace.openEvidence" as MessageKey)}
                        </a>
                        {record.hit ? (
                          <a className="otc-button otc-button--ghost" href={buildBlocksHref(record)}>
                            {tr("sanctions.workspace.openBlocks" as MessageKey)}
                          </a>
                        ) : null}
                        {record.source === "local" ? (
                          <button type="button" className="otc-button otc-button--ghost" onClick={() => removeWorkspaceRecord(record.workspaceId)}>
                            {tr("sanctions.workspace.remove" as MessageKey)}
                          </button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <Message>{tr("sanctions.workspace.empty" as MessageKey)}</Message>
        )}
      </Panel>

      <Panel title={tr("sanctions.result.title" as MessageKey)} description={tr("sanctions.result.description" as MessageKey)}>
        {result ? (
          <div className="otc-stack">
            <Message tone={isHit ? "error" : "success"}>
              {isHit ? tr("sanctions.result.hit" as MessageKey) : tr("sanctions.result.clear" as MessageKey)}
            </Message>

            <div className="otc-grid otc-grid--counterparty-form">
              <div className="otc-panel">
                <div className="otc-muted">{tr("sanctions.result.checkedAt" as MessageKey)}</div>
                <strong>{formatDate(result.checked_at) ?? result.checked_at}</strong>
              </div>
              <div className="otc-panel">
                <div className="otc-muted">{tr("sanctions.result.provider" as MessageKey)}</div>
                <strong>{result.provider}</strong>
              </div>
              <div className="otc-panel">
                <div className="otc-muted">{tr("sanctions.result.providerStatus" as MessageKey)}</div>
                <strong>{result.provider_status}</strong>
                {result.degraded_reason ? <div className="otc-muted">{result.degraded_reason}</div> : null}
              </div>
              <div className="otc-panel">
                <div className="otc-muted">{tr("sanctions.result.capability" as MessageKey)}</div>
                <strong>{result.capability_status}</strong>
              </div>
            </div>

            <div className="otc-grid otc-grid--counterparty-form">
              <div className="otc-panel">
                <div className="otc-muted">{tr("sanctions.result.address" as MessageKey)}</div>
                <strong>{result.address}</strong>
                <div className="otc-muted">{tr("sanctions.result.chain" as MessageKey)} {result.chain}</div>
              </div>
              <div className="otc-panel">
                <div className="otc-muted">{tr("sanctions.result.entityName" as MessageKey)}</div>
                <strong>{result.entity_name ?? tr("sanctions.result.notAvailable" as MessageKey)}</strong>
                <div className="otc-muted">{tr("sanctions.result.designationDate" as MessageKey)} {formatDate(result.designation_date) ?? tr("sanctions.result.notAvailable" as MessageKey)}</div>
              </div>
              <div className="otc-panel">
                <div className="otc-muted">{tr("sanctions.result.matchedLists" as MessageKey)}</div>
                <strong>{matchedCount}</strong>
                <div className="otc-controls otc-controls--spaced">
                  {(result.matched_lists || []).length ? (
                    result.matched_lists.map((listName) => (
                      <Pill key={listName} tone={isHit ? "danger" : "success"}>
                        {listName}
                      </Pill>
                    ))
                  ) : (
                    <span className="otc-muted">{tr("sanctions.result.none" as MessageKey)}</span>
                  )}
                </div>
              </div>
            </div>

            <label className="otc-field">
              {tr("sanctions.triage.note" as MessageKey)}
              <textarea className="otc-textarea" rows={3} value={triageNote} onChange={(event) => setTriageNote(event.target.value)} />
            </label>
            <div className="otc-controls">
              {form.caseId.trim() ? (
                <a className="otc-button otc-button--ghost" href={`/cases/${form.caseId.trim()}`}>
                  {tr("sanctions.result.openCase" as MessageKey)}
                </a>
              ) : null}
              <a className="otc-button otc-button--ghost" href={buildAuditHref(form.caseId, form.caseId.trim() || result.address)}>
                {tr("sanctions.result.openAudit" as MessageKey)}
              </a>
              <a className="otc-button otc-button--ghost" href={buildEvidenceHref(form.caseId.trim() || result.address, form.caseId)}>
                {tr("sanctions.result.openEvidence" as MessageKey)}
              </a>
              <a className="otc-button otc-button--ghost" href={`/investigate?address=${encodeURIComponent(result.address)}&chain=${encodeURIComponent(result.chain)}&report_type=technical_basic`}>
                {tr("sanctions.result.openInvestigate" as MessageKey)}
              </a>
              {isHit ? (
                <a className="otc-button otc-button--ghost" href={buildBlocksHref({ address: result.address, chain: result.chain, caseId: form.caseId, owner: form.owner, priority: form.priority, localDeadline: form.localDeadline })}>
                  {tr("sanctions.result.openBlocks" as MessageKey)}
                </a>
              ) : null}
            </div>
            <div className="otc-controls">
              <button type="button" className="otc-button otc-button--ghost" onClick={() => updateWorkspaceStatus("UNDER_REVIEW")}>
                {tr("sanctions.triage.review" as MessageKey)}
              </button>
              <button type="button" className="otc-button otc-button--ghost" onClick={() => updateWorkspaceStatus("ESCALATED")} disabled={syncingWorkspace}>
                {tr("sanctions.triage.escalate" as MessageKey)}
              </button>
              <button type="button" className="otc-button otc-button--ghost" onClick={() => updateWorkspaceStatus("CLOSED")} disabled={syncingWorkspace}>
                {tr("sanctions.triage.clear" as MessageKey)}
              </button>
            </div>

            <details className="otc-panel">
              <summary>{tr("sanctions.result.raw" as MessageKey)}</summary>
              <div className="otc-controls otc-controls--spaced">
                <CodeBlock>{JSON.stringify(result, null, 2)}</CodeBlock>
              </div>
            </details>
          </div>
        ) : (
          <Message>{tr("sanctions.result.empty" as MessageKey)}</Message>
        )}
      </Panel>
    </AppShell>
  );
}

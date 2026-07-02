"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import { useI18n } from "../../components/i18n-provider";
import type { MessageKey } from "../lib/i18n";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";

type BlockEvaluateResponse = {
  address: string;
  chain: string;
  action: string;
  requires_coaf_report: boolean;
  decision_confidence: number;
  regulatory_basis: string[];
  matched_lists: string[];
  evidence_hash?: string | null;
  block_id?: string | null;
  screened_at: string;
};

type BlockLiftResponse = {
  block_id: string;
  status: string;
  review_status: string;
  lifted_at: string;
};

type BlockWorkspacePriority = "critical" | "high" | "normal";
type BlockWorkspaceStatus = "BLOCKED" | "REVIEW" | "CLEARED" | "LIFTED";
type BlockWorkspaceSource = "server" | "local";
type WorkItemQueueStatus = "UNDER_REVIEW" | "ESCALATED" | "READY" | "APPROVED" | "SUBMITTED" | "CLOSED" | "REJECTED";

type WorkItemResponse = {
  id: string;
  resource_id: string;
  queue_status: WorkItemQueueStatus;
  priority: BlockWorkspacePriority;
  due_at: string | null;
  note: string | null;
  metadata: Record<string, unknown>;
  last_activity_at: string;
  updated_at: string;
};

type WorkItemListResponse = {
  data: WorkItemResponse[];
};

type EvaluateFormState = {
  address: string;
  chain: string;
  entityName: string;
  entityDocument: string;
  caseId: string;
  owner: string;
  priority: BlockWorkspacePriority;
  localDeadline: string;
};

type BlockWorkspaceRecord = {
  workspaceId: string;
  resourceId: string;
  workItemId?: string;
  source: BlockWorkspaceSource;
  address: string;
  chain: string;
  entityName: string;
  entityDocument: string;
  caseId: string;
  owner: string;
  priority: BlockWorkspacePriority;
  localDeadline: string;
  action: string;
  status: BlockWorkspaceStatus;
  requiresCoafReport: boolean;
  decisionConfidence: number;
  regulatoryBasis: string[];
  matchedLists: string[];
  evidenceHash: string;
  blockId: string;
  screenedAt: string;
  liftedAt: string;
  liftReason: string;
  lastActionAt: string;
};

const STORAGE_KEY = "otc-blocks-workspace";
const WORKSPACE_PAGE_LIMIT = 100;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const DEFAULT_FORM: EvaluateFormState = {
  address: "",
  chain: "ethereum",
  entityName: "",
  entityDocument: "",
  caseId: "",
  owner: "",
  priority: "normal",
  localDeadline: ""
};

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

function normalizeLegacyStatus(value: unknown): BlockWorkspaceStatus {
  if (value === "BLOCKED" || value === "REVIEW" || value === "CLEARED" || value === "LIFTED") {
    return value;
  }
  return "REVIEW";
}

function normalizeWorkspaceRecord(record: Partial<BlockWorkspaceRecord>): BlockWorkspaceRecord {
  const resourceId = typeof record.resourceId === "string" && isUuidLike(record.resourceId) ? record.resourceId : "";
  const blockId = typeof record.blockId === "string" ? record.blockId : "";
  return {
    workspaceId: typeof record.workspaceId === "string" && record.workspaceId ? record.workspaceId : blockId || crypto.randomUUID(),
    resourceId,
    workItemId: typeof record.workItemId === "string" ? record.workItemId : undefined,
    source: record.source === "server" ? "server" : "local",
    address: typeof record.address === "string" ? record.address : "",
    chain: typeof record.chain === "string" && record.chain ? record.chain : "ethereum",
    entityName: typeof record.entityName === "string" ? record.entityName : "",
    entityDocument: typeof record.entityDocument === "string" ? record.entityDocument : "",
    caseId: typeof record.caseId === "string" ? record.caseId : "",
    owner: typeof record.owner === "string" ? record.owner : "",
    priority: record.priority === "critical" || record.priority === "high" || record.priority === "normal" ? record.priority : "normal",
    localDeadline: typeof record.localDeadline === "string" ? record.localDeadline : "",
    action: typeof record.action === "string" ? record.action : "",
    status: normalizeLegacyStatus(record.status),
    requiresCoafReport: record.requiresCoafReport === true,
    decisionConfidence: typeof record.decisionConfidence === "number" ? record.decisionConfidence : 0,
    regulatoryBasis: Array.isArray(record.regulatoryBasis) ? record.regulatoryBasis.filter((entry): entry is string => typeof entry === "string") : [],
    matchedLists: Array.isArray(record.matchedLists) ? record.matchedLists.filter((entry): entry is string => typeof entry === "string") : [],
    evidenceHash: typeof record.evidenceHash === "string" ? record.evidenceHash : "",
    blockId,
    screenedAt: typeof record.screenedAt === "string" ? record.screenedAt : "",
    liftedAt: typeof record.liftedAt === "string" ? record.liftedAt : "",
    liftReason: typeof record.liftReason === "string" ? record.liftReason : "",
    lastActionAt: typeof record.lastActionAt === "string" ? record.lastActionAt : ""
  };
}

function loadWorkspace(): BlockWorkspaceRecord[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.map((entry) => normalizeWorkspaceRecord((entry ?? {}) as Partial<BlockWorkspaceRecord>)) : [];
  } catch {
    return [];
  }
}

function saveWorkspace(records: BlockWorkspaceRecord[]) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
}

function buildWorkspaceId(result: BlockEvaluateResponse) {
  return result.block_id?.trim() || `${result.address}:${result.chain}:${result.screened_at}`;
}

function mergeWorkspaceRecords(serverRecords: BlockWorkspaceRecord[], localRecords: BlockWorkspaceRecord[]) {
  const merged = [...serverRecords];
  const seenWorkspaceIds = new Set(serverRecords.map((record) => record.workspaceId));
  const seenWorkItemIds = new Set(serverRecords.map((record) => record.workItemId).filter(Boolean));
  const seenResourceIds = new Set(serverRecords.map((record) => record.resourceId).filter(Boolean));

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

function toneForAction(action: string): "success" | "default" | "error" {
  const normalized = action.toLowerCase();
  if (normalized.includes("block") || normalized.includes("deny") || normalized.includes("reject")) return "error";
  if (normalized.includes("review") || normalized.includes("manual") || normalized.includes("inspect")) return "default";
  return "success";
}

function deriveWorkspaceStatus(result: BlockEvaluateResponse): BlockWorkspaceStatus {
  const normalized = result.action.toLowerCase();
  if (result.block_id || normalized.includes("block") || normalized.includes("deny") || normalized.includes("reject")) {
    return "BLOCKED";
  }
  if (normalized.includes("review") || normalized.includes("manual") || normalized.includes("inspect")) {
    return "REVIEW";
  }
  return "CLEARED";
}

function upsertWorkspaceRecord(
  current: BlockWorkspaceRecord[],
  next: Partial<BlockWorkspaceRecord> & { workspaceId: string }
): BlockWorkspaceRecord[] {
  const existing = current.find((record) => record.workspaceId === next.workspaceId);
  const base: BlockWorkspaceRecord =
    existing ?? {
      workspaceId: next.workspaceId,
      resourceId: next.resourceId ?? "",
      source: next.source ?? "local",
      address: "",
      chain: "ethereum",
      entityName: "",
      entityDocument: "",
      caseId: "",
      owner: "",
      priority: "normal",
      localDeadline: "",
      action: "",
      status: "REVIEW",
      requiresCoafReport: false,
      decisionConfidence: 0,
      regulatoryBasis: [],
      matchedLists: [],
      evidenceHash: "",
      blockId: "",
      screenedAt: "",
      liftedAt: "",
      liftReason: "",
      lastActionAt: ""
    };

  const merged: BlockWorkspaceRecord = {
    ...base,
    ...next,
    lastActionAt: next.lastActionAt ?? new Date().toISOString()
  };

  return [merged, ...current.filter((record) => record.workspaceId !== next.workspaceId)].sort((a, b) =>
    (b.lastActionAt || "").localeCompare(a.lastActionAt || "")
  );
}

function getUrgency(record: BlockWorkspaceRecord): "overdue" | "due_soon" | "on_track" | "no_deadline" {
  if (!record.localDeadline) {
    return "no_deadline";
  }

  if (record.status === "LIFTED" || record.status === "CLEARED") {
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

function toEvaluateResponse(record: BlockWorkspaceRecord): BlockEvaluateResponse {
  return {
    address: record.address,
    chain: record.chain,
    action: record.action,
    requires_coaf_report: record.requiresCoafReport,
    decision_confidence: record.decisionConfidence,
    regulatory_basis: record.regulatoryBasis,
    matched_lists: record.matchedLists,
    evidence_hash: record.evidenceHash || null,
    block_id: record.blockId || null,
    screened_at: record.screenedAt
  };
}

function toneForUrgency(urgency: ReturnType<typeof getUrgency>): "warning" | "danger" | undefined {
  if (urgency === "overdue") return "danger";
  if (urgency === "due_soon") return "warning";
  return undefined;
}

function toneForWorkspaceStatus(status: BlockWorkspaceStatus): "warning" | "danger" | undefined {
  if (status === "BLOCKED") return "danger";
  if (status === "REVIEW") return "warning";
  return undefined;
}

function mapWorkItemToWorkspaceRecord(item: WorkItemResponse): BlockWorkspaceRecord {
  const metadata = item.metadata ?? {};
  const localStatus = normalizeLegacyStatus(metadata["local_block_status"]);
  const blockId = readMetadataString(metadata, "block_id") || item.resource_id;
  return {
    workspaceId: readMetadataString(metadata, "workspace_id") || blockId,
    resourceId: item.resource_id,
    workItemId: item.id,
    source: "server",
    address: readMetadataString(metadata, "address"),
    chain: readMetadataString(metadata, "chain") || "ethereum",
    entityName: readMetadataString(metadata, "entity_name"),
    entityDocument: readMetadataString(metadata, "entity_document"),
    caseId: readMetadataString(metadata, "local_case_id"),
    owner: readMetadataString(metadata, "owner_label"),
    priority: item.priority,
    localDeadline: toDateTimeLocalValue(item.due_at),
    action: readMetadataString(metadata, "action"),
    status: localStatus,
    requiresCoafReport: readMetadataBoolean(metadata, "requires_coaf_report"),
    decisionConfidence: typeof metadata["decision_confidence"] === "number" ? metadata["decision_confidence"] : 0,
    regulatoryBasis: readMetadataStringArray(metadata, "regulatory_basis"),
    matchedLists: readMetadataStringArray(metadata, "matched_lists"),
    evidenceHash: readMetadataString(metadata, "evidence_hash"),
    blockId,
    screenedAt: readMetadataString(metadata, "screened_at"),
    liftedAt: readMetadataString(metadata, "lifted_at"),
    liftReason: item.note ?? readMetadataString(metadata, "lift_reason"),
    lastActionAt: item.last_activity_at || item.updated_at
  };
}

function buildAuditHref(caseId: string, resourceId: string, blockId = "") {
  const params = new URLSearchParams({
    resource_type: "case",
    resource_id: resourceId
  });
  if (caseId.trim()) {
    params.set("request_id", caseId.trim());
  }
  if (blockId.trim()) {
    params.set("report_id", blockId.trim());
  }
  return `/audit?${params.toString()}`;
}

function buildEvidenceHref(resourceId: string, caseId: string, blockId = "") {
  const params = new URLSearchParams({
    domain: "all",
    resource_type: "case",
    resource_id: resourceId
  });
  if (caseId.trim()) {
    params.set("request_id", caseId.trim());
  }
  if (blockId.trim()) {
    params.set("report_id", blockId.trim());
  }
  return `/evidence?${params.toString()}`;
}

function buildRosCoafHref(record: {
  caseId: string;
  owner: string;
  priority: BlockWorkspacePriority;
  localDeadline: string;
}) {
  const params = new URLSearchParams({
    case_id: record.caseId,
    owner: record.owner,
    priority: record.priority,
    deadline: record.localDeadline
  });
  return `/ros-coaf?${params.toString()}`;
}

export default function BlocksPage() {
  const { t } = useI18n();
  const searchParams = useSearchParams();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);
  const hydratedPrefillKeyRef = useRef<string | null>(null);

  const [form, setForm] = useState<EvaluateFormState>(DEFAULT_FORM);
  const [result, setResult] = useState<BlockEvaluateResponse | null>(null);
  const [liftResult, setLiftResult] = useState<BlockLiftResponse | null>(null);
  const [liftReason, setLiftReason] = useState("");

  const [evaluating, setEvaluating] = useState(false);
  const [lifting, setLifting] = useState(false);
  const [syncingWorkspace, setSyncingWorkspace] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [workspaceRecords, setWorkspaceRecords] = useState<BlockWorkspaceRecord[]>([]);
  const [workspaceFilter, setWorkspaceFilter] = useState("all");
  const [workspaceSearch, setWorkspaceSearch] = useState("");

  const matchedLists = useMemo(() => result?.matched_lists ?? [], [result]);
  const regulatoryBasis = useMemo(() => result?.regulatory_basis ?? [], [result]);
  const actionTone = result?.action ? toneForAction(result.action) : "default";
  const currentWorkspaceId = result ? buildWorkspaceId(result) : null;
  const filteredWorkspaceRecords = useMemo(() => {
    return workspaceRecords.filter((record) => {
      const matchesStatus = workspaceFilter === "all" ? true : record.status === workspaceFilter;
      const search = workspaceSearch.trim().toLowerCase();
      const matchesSearch =
        !search ||
        record.address.toLowerCase().includes(search) ||
        record.blockId.toLowerCase().includes(search) ||
        record.caseId.toLowerCase().includes(search) ||
        record.owner.toLowerCase().includes(search);
      return matchesStatus && matchesSearch;
    });
  }, [workspaceFilter, workspaceRecords, workspaceSearch]);
  const pendingQueueCount = useMemo(
    () => workspaceRecords.filter((record) => record.status === "BLOCKED" || record.status === "REVIEW").length,
    [workspaceRecords]
  );
  const overdueCount = useMemo(
    () => workspaceRecords.filter((record) => getUrgency(record) === "overdue").length,
    [workspaceRecords]
  );
  const liftedCount = useMemo(
    () => workspaceRecords.filter((record) => record.status === "LIFTED").length,
    [workspaceRecords]
  );

  async function loadOperationalWorkspace(localRecords: BlockWorkspaceRecord[]) {
    const res = await fetch(
      `/api/app/operations/work-items?module=blocks&resource_type=preventive_block&limit=${WORKSPACE_PAGE_LIMIT}`,
      { cache: "no-store" }
    );
    const data = (await res.json().catch(() => null)) as WorkItemListResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setWorkspaceRecords(localRecords);
      setNotice(tr("blocks.noticeWorkspaceLoadedLocal" as MessageKey));
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
      setNotice(tr("blocks.noticeWorkspaceLoadedLocal" as MessageKey));
    });
  }, []);

  useEffect(() => {
    saveWorkspace(workspaceRecords);
  }, [workspaceRecords]);

  function updateForm<K extends keyof EvaluateFormState>(key: K, value: EvaluateFormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function hydrateWorkspaceRecord(record: BlockWorkspaceRecord) {
    setForm({
      address: record.address,
      chain: record.chain,
      entityName: record.entityName,
      entityDocument: record.entityDocument,
      caseId: record.caseId,
      owner: record.owner,
      priority: record.priority,
      localDeadline: record.localDeadline
    });
    setLiftReason(record.liftReason);
    setResult(toEvaluateResponse(record));
    setLiftResult(
      record.liftedAt
        ? {
            block_id: record.blockId,
            status: "LIFTED",
            review_status: "COMPLETED",
            lifted_at: record.liftedAt
          }
        : null
    );
  }

  function removeWorkspaceRecord(workspaceId: string) {
    setWorkspaceRecords((current) => current.filter((record) => record.workspaceId !== workspaceId));
  }

  function buildWorkspaceRecordFromEvaluation(
    evaluation: BlockEvaluateResponse,
    nextForm: EvaluateFormState,
    base?: Partial<BlockWorkspaceRecord>
  ): BlockWorkspaceRecord {
    const workspaceId = base?.workspaceId ?? buildWorkspaceId(evaluation);
    const resourceId = evaluation.block_id && isUuidLike(evaluation.block_id) ? evaluation.block_id.trim() : base?.resourceId ?? "";
    return {
      workspaceId,
      resourceId,
      workItemId: base?.workItemId,
      source: base?.source ?? "local",
      address: evaluation.address,
      chain: evaluation.chain,
      entityName: nextForm.entityName.trim(),
      entityDocument: nextForm.entityDocument.trim(),
      caseId: nextForm.caseId.trim(),
      owner: nextForm.owner.trim(),
      priority: nextForm.priority,
      localDeadline: nextForm.localDeadline,
      action: evaluation.action,
      status: base?.status ?? deriveWorkspaceStatus(evaluation),
      requiresCoafReport: evaluation.requires_coaf_report,
      decisionConfidence: evaluation.decision_confidence,
      regulatoryBasis: evaluation.regulatory_basis,
      matchedLists: evaluation.matched_lists,
      evidenceHash: evaluation.evidence_hash ?? "",
      blockId: evaluation.block_id ?? "",
      screenedAt: evaluation.screened_at,
      liftedAt: base?.liftedAt ?? "",
      liftReason: base?.liftReason ?? liftReason.trim(),
      lastActionAt: evaluation.screened_at
    };
  }

  async function syncWorkspaceRecord(record: BlockWorkspaceRecord, nextStatus?: BlockWorkspaceStatus) {
    const resourceId = record.resourceId || (record.blockId && isUuidLike(record.blockId) ? record.blockId.trim() : "");
    if (!resourceId) {
      throw new Error(tr("blocks.errorWorkspaceSyncMissingBlockId" as MessageKey));
    }

    const localStatus = nextStatus ?? record.status;
    const queueStatus: WorkItemQueueStatus =
      localStatus === "CLEARED" || localStatus === "LIFTED" ? "CLOSED" : "UNDER_REVIEW";
    const metadata = {
      workspace_id: record.workspaceId,
      local_block_status: localStatus,
      address: record.address,
      chain: record.chain,
      entity_name: record.entityName,
      entity_document: record.entityDocument,
      local_case_id: record.caseId,
      owner_label: record.owner,
      action: record.action,
      requires_coaf_report: record.requiresCoafReport,
      decision_confidence: record.decisionConfidence,
      regulatory_basis: record.regulatoryBasis,
      matched_lists: record.matchedLists,
      evidence_hash: record.evidenceHash,
      block_id: record.blockId,
      screened_at: record.screenedAt,
      lifted_at: record.liftedAt,
      lift_reason: record.liftReason
    };
    const requestBody = record.workItemId
      ? {
          priority: record.priority,
          queue_status: queueStatus,
          due_at: toApiDueAt(record.localDeadline),
          title: `Preventive block • ${record.address}`,
          note: record.liftReason || null,
          metadata
        }
      : {
          module: "blocks",
          resource_type: "preventive_block",
          resource_id: resourceId,
          ...(isUuidLike(record.caseId) ? { case_id: record.caseId.trim() } : {}),
          priority: record.priority,
          queue_status: queueStatus,
          due_at: toApiDueAt(record.localDeadline),
          title: `Preventive block • ${record.address}`,
          note: record.liftReason || null,
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
      throw new Error(resolveApiErrorMessage(t, data, tr("blocks.errorWorkspaceSync" as MessageKey)));
    }

    const nextRecord = mapWorkItemToWorkspaceRecord(data as WorkItemResponse);
    setWorkspaceRecords((current) => upsertWorkspaceRecord(current, nextRecord));
    return nextRecord;
  }

  async function runEvaluate(nextForm: EvaluateFormState) {
    setError(null);
    setNotice(null);
    setLiftResult(null);
    setResult(null);
    setEvaluating(true);

    const payload = {
      address: nextForm.address.trim(),
      chain: nextForm.chain,
      entity_name: nextForm.entityName.trim() || null,
      entity_document: nextForm.entityDocument.trim() || null
    };

    const res = await fetch("/api/app/compliance/blocks/evaluate", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = (await res.json().catch(() => null)) as BlockEvaluateResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setError(resolveApiErrorMessage(t, data, tr("blocks.errorEvaluate" as MessageKey)));
      setEvaluating(false);
      return;
    }

    const evaluation = data as BlockEvaluateResponse;
    setResult(evaluation);
    const draftRecord = buildWorkspaceRecordFromEvaluation(evaluation, nextForm);
    setWorkspaceRecords((current) => upsertWorkspaceRecord(current, draftRecord));
    if (draftRecord.resourceId) {
      try {
        await syncWorkspaceRecord(draftRecord);
        setNotice(tr("blocks.noticeEvaluatedSynced" as MessageKey));
      } catch (syncError) {
        setNotice(tr("blocks.noticeEvaluatedLocalOnly" as MessageKey));
        setError(syncError instanceof Error ? syncError.message : tr("blocks.errorWorkspaceSync" as MessageKey));
      }
    } else {
      setNotice(tr("blocks.noticeEvaluatedLocalOnly" as MessageKey));
    }
    setEvaluating(false);
  }

  async function onEvaluate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runEvaluate(form);
  }

  useEffect(() => {
    const nextForm: EvaluateFormState = {
      address: searchParams.get("address") ?? DEFAULT_FORM.address,
      chain: searchParams.get("chain") ?? DEFAULT_FORM.chain,
      entityName: searchParams.get("entity_name") ?? DEFAULT_FORM.entityName,
      entityDocument: searchParams.get("entity_document") ?? DEFAULT_FORM.entityDocument,
      caseId: searchParams.get("case_id") ?? DEFAULT_FORM.caseId,
      owner: searchParams.get("owner") ?? DEFAULT_FORM.owner,
      priority: ((searchParams.get("priority") as BlockWorkspacePriority | null) ?? DEFAULT_FORM.priority),
      localDeadline: searchParams.get("deadline") ?? DEFAULT_FORM.localDeadline
    };
    const shouldAutostart = searchParams.get("autostart") === "1";
    const prefillKey = JSON.stringify({ ...nextForm, shouldAutostart });
    setForm(nextForm);
    if (shouldAutostart && nextForm.address.trim() && hydratedPrefillKeyRef.current !== prefillKey) {
      hydratedPrefillKeyRef.current = prefillKey;
      void runEvaluate(nextForm);
    }
  }, [searchParams]);

  async function onLift() {
    if (!result?.block_id) {
      setError(tr("blocks.errorMissingBlockId" as MessageKey));
      return;
    }

    setError(null);
    setNotice(null);
    setLifting(true);
    const res = await fetch(`/api/app/compliance/blocks/${result.block_id}/lift`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ reason: liftReason.trim() })
    });
    const data = (await res.json().catch(() => null)) as BlockLiftResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setError(resolveApiErrorMessage(t, data, tr("blocks.errorLift" as MessageKey)));
      setLifting(false);
      return;
    }

    const lifted = data as BlockLiftResponse;
    setLiftResult(lifted);
    if (currentWorkspaceId) {
      const baseRecord = workspaceRecords.find((record) => record.workspaceId === currentWorkspaceId);
      const nextRecord = upsertWorkspaceRecord(workspaceRecords, {
        workspaceId: currentWorkspaceId,
        resourceId: lifted.block_id,
        status: "LIFTED",
        liftedAt: lifted.lifted_at,
        liftReason: liftReason.trim(),
        blockId: lifted.block_id,
        lastActionAt: lifted.lifted_at
      })[0];
      setWorkspaceRecords((current) =>
        upsertWorkspaceRecord(current, {
          workspaceId: currentWorkspaceId,
          resourceId: lifted.block_id,
          status: "LIFTED",
          liftedAt: lifted.lifted_at,
          liftReason: liftReason.trim(),
          blockId: lifted.block_id,
          lastActionAt: lifted.lifted_at
        })
      );
      if (baseRecord || nextRecord) {
        try {
          await syncWorkspaceRecord({ ...(baseRecord ?? nextRecord), ...nextRecord, resourceId: lifted.block_id, blockId: lifted.block_id, status: "LIFTED", liftedAt: lifted.lifted_at, liftReason: liftReason.trim() }, "LIFTED");
          setNotice(tr("blocks.noticeLiftedSynced" as MessageKey));
          setLifting(false);
          return;
        } catch (syncError) {
          setNotice(tr("blocks.noticeLiftedLocalOnly" as MessageKey));
          setError(syncError instanceof Error ? syncError.message : tr("blocks.errorWorkspaceSync" as MessageKey));
        }
      }
    }
    setNotice(tr("blocks.noticeLifted" as MessageKey));
    setLifting(false);
  }

  return (
    <AppShell
      title={tr("blocks.title" as MessageKey)}
      subtitle={tr("blocks.subtitle" as MessageKey)}
      activePath="/blocks"
      actions={<Pill>{tr("blocks.active" as MessageKey)}</Pill>}
    >
      <MetricGrid>
        <MetricCard label={tr("blocks.stats.action" as MessageKey)} value={result?.action ?? "--"} meta={tr("blocks.stats.actionMeta" as MessageKey)} accent />
        <MetricCard label={tr("blocks.stats.pendingQueue" as MessageKey)} value={pendingQueueCount} meta={tr("blocks.stats.pendingQueueMeta" as MessageKey)} />
        <MetricCard label={tr("blocks.stats.overdue" as MessageKey)} value={overdueCount} meta={tr("blocks.stats.overdueMeta" as MessageKey)} />
        <MetricCard label={tr("blocks.stats.lifted" as MessageKey)} value={liftedCount} meta={tr("blocks.stats.liftedMeta" as MessageKey)} />
      </MetricGrid>

      <Panel title={tr("blocks.form.title" as MessageKey)} description={tr("blocks.form.description" as MessageKey)}>
        <form className="otc-stack" onSubmit={onEvaluate}>
          <div className="otc-grid otc-grid--counterparty-form">
            <label className="otc-field">
              {tr("blocks.form.address" as MessageKey)}
              <input className="otc-input" data-testid="blocks-address" value={form.address} onChange={(event) => updateForm("address", event.target.value)} required />
            </label>
            <label className="otc-field">
              {tr("blocks.form.chain" as MessageKey)}
              <select className="otc-select" data-testid="blocks-chain" value={form.chain} onChange={(event) => updateForm("chain", event.target.value)}>
                <option value="ethereum">Ethereum</option>
                <option value="polygon">Polygon</option>
                <option value="bsc">BSC</option>
                <option value="arbitrum">Arbitrum</option>
                <option value="base">Base</option>
                <option value="bitcoin">Bitcoin</option>
              </select>
            </label>
            <label className="otc-field">
              {tr("blocks.form.caseId" as MessageKey)}
              <input className="otc-input" value={form.caseId} onChange={(event) => updateForm("caseId", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("blocks.form.owner" as MessageKey)}
              <input className="otc-input" value={form.owner} onChange={(event) => updateForm("owner", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("blocks.form.priority" as MessageKey)}
              <select className="otc-select" value={form.priority} onChange={(event) => updateForm("priority", event.target.value as BlockWorkspacePriority)}>
                <option value="critical">{tr("blocks.priority.critical" as MessageKey)}</option>
                <option value="high">{tr("blocks.priority.high" as MessageKey)}</option>
                <option value="normal">{tr("blocks.priority.normal" as MessageKey)}</option>
              </select>
            </label>
            <label className="otc-field">
              {tr("blocks.form.localDeadline" as MessageKey)}
              <input className="otc-input" type="datetime-local" value={form.localDeadline} onChange={(event) => updateForm("localDeadline", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("blocks.form.entityName" as MessageKey)}
              <input className="otc-input" value={form.entityName} onChange={(event) => updateForm("entityName", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("blocks.form.entityDocument" as MessageKey)}
              <input className="otc-input" value={form.entityDocument} onChange={(event) => updateForm("entityDocument", event.target.value)} />
            </label>
          </div>

          <div className="otc-controls">
            <button className="otc-button otc-button--accent" type="submit" data-testid="blocks-evaluate-btn" disabled={evaluating}>
              {evaluating ? tr("blocks.form.submitting" as MessageKey) : tr("blocks.form.submit" as MessageKey)}
            </button>
            <button
              className="otc-button"
              type="button"
              onClick={() => {
                setForm(DEFAULT_FORM);
                setLiftReason("");
              }}
              disabled={evaluating}
            >
              {tr("blocks.form.reset" as MessageKey)}
            </button>
          </div>

          <Message>{tr("blocks.mfaNotice" as MessageKey)}</Message>
          {error ? <Message tone="error">{error}</Message> : null}
          {notice ? <Message tone="success">{notice}</Message> : null}
        </form>
      </Panel>

      <Panel title={tr("blocks.workspace.title" as MessageKey)} description={tr("blocks.workspace.description" as MessageKey)}>
        <div className="otc-controls">
          <label className="otc-field">
            {tr("blocks.workspace.filterStatus" as MessageKey)}
            <select className="otc-select" value={workspaceFilter} onChange={(event) => setWorkspaceFilter(event.target.value)}>
              <option value="all">{tr("blocks.workspace.all" as MessageKey)}</option>
              <option value="BLOCKED">{tr("blocks.workspace.status.blocked" as MessageKey)}</option>
              <option value="REVIEW">{tr("blocks.workspace.status.review" as MessageKey)}</option>
              <option value="CLEARED">{tr("blocks.workspace.status.cleared" as MessageKey)}</option>
              <option value="LIFTED">{tr("blocks.workspace.status.lifted" as MessageKey)}</option>
            </select>
          </label>
          <label className="otc-field">
            {tr("blocks.workspace.search" as MessageKey)}
            <input className="otc-input" value={workspaceSearch} onChange={(event) => setWorkspaceSearch(event.target.value)} />
          </label>
        </div>

        {filteredWorkspaceRecords.length ? (
          <table className="otc-table otc-table--spaced">
            <thead>
              <tr>
                <th>{tr("blocks.workspace.address" as MessageKey)}</th>
                <th>{tr("blocks.workspace.caseId" as MessageKey)}</th>
                <th>{tr("blocks.workspace.owner" as MessageKey)}</th>
                <th>{tr("blocks.workspace.priority" as MessageKey)}</th>
                <th>{tr("blocks.workspace.deadline" as MessageKey)}</th>
                <th>{tr("blocks.workspace.urgency" as MessageKey)}</th>
                <th>{tr("blocks.workspace.status" as MessageKey)}</th>
                <th>{tr("blocks.workspace.actions" as MessageKey)}</th>
              </tr>
            </thead>
            <tbody>
              {filteredWorkspaceRecords.map((record) => {
                const urgency = getUrgency(record);
                return (
                  <tr key={record.workspaceId}>
                    <td>
                      <strong>{record.address}</strong>
                      <div className="otc-muted">{record.blockId || tr("blocks.notAvailable" as MessageKey)}</div>
                    </td>
                    <td>{record.caseId || tr("blocks.workspace.noCaseId" as MessageKey)}</td>
                    <td>{record.owner || tr("blocks.workspace.unassigned" as MessageKey)}</td>
                    <td>
                      <Pill tone={record.priority === "critical" ? "danger" : record.priority === "high" ? "warning" : undefined}>
                        {tr(`blocks.priority.${record.priority}` as MessageKey)}
                      </Pill>
                    </td>
                    <td>{formatDate(record.localDeadline) ?? tr("blocks.workspace.noDeadline" as MessageKey)}</td>
                    <td>
                      <Pill tone={toneForUrgency(urgency)}>{tr(`blocks.urgency.${urgency}` as MessageKey)}</Pill>
                    </td>
                    <td>
                      <Pill tone={toneForWorkspaceStatus(record.status)}>{tr(`blocks.workspace.status.${record.status.toLowerCase()}` as MessageKey)}</Pill>
                    </td>
                    <td>
                      <div className="otc-controls">
                        <Pill tone={record.source === "server" ? "success" : "warning"}>{tr(`blocks.workspace.source.${record.source}` as MessageKey)}</Pill>
                        <button type="button" className="otc-button otc-button--ghost" onClick={() => hydrateWorkspaceRecord(record)}>
                          {tr("blocks.workspace.load" as MessageKey)}
                        </button>
                        {record.caseId ? (
                          <a className="otc-button otc-button--ghost" href={`/cases/${record.caseId}`}>
                            {tr("blocks.workspace.openCase" as MessageKey)}
                          </a>
                        ) : null}
                        <a className="otc-button otc-button--ghost" href={buildAuditHref(record.caseId, record.caseId || record.address, record.blockId)}>
                          {tr("blocks.workspace.openAudit" as MessageKey)}
                        </a>
                        <a className="otc-button otc-button--ghost" href={buildEvidenceHref(record.caseId || record.address, record.caseId, record.blockId)}>
                          {tr("blocks.workspace.openEvidence" as MessageKey)}
                        </a>
                        {record.requiresCoafReport ? (
                          <a className="otc-button otc-button--ghost" href={buildRosCoafHref(record)}>
                            {tr("blocks.workspace.openRos" as MessageKey)}
                          </a>
                        ) : null}
                        {record.source === "local" ? (
                          <button type="button" className="otc-button otc-button--ghost" onClick={() => removeWorkspaceRecord(record.workspaceId)}>
                            {tr("blocks.workspace.remove" as MessageKey)}
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
          <Message>{tr("blocks.workspace.empty" as MessageKey)}</Message>
        )}
      </Panel>

      <Panel title={tr("blocks.result.title" as MessageKey)} description={tr("blocks.result.description" as MessageKey)}>
        {result ? (
          <div className="otc-stack">
            <Message tone={actionTone}>{tr("blocks.result.actionLine" as MessageKey, { action: result.action })}</Message>
            <div className="otc-grid otc-grid--counterparty-form">
              <div className="otc-panel">
                <div className="otc-muted">{tr("blocks.result.screenedAt" as MessageKey)}</div>
                <strong>{formatDate(result.screened_at) ?? result.screened_at}</strong>
              </div>
              <div className="otc-panel">
                <div className="otc-muted">{tr("blocks.result.blockId" as MessageKey)}</div>
                <strong>{result.block_id ?? tr("blocks.notAvailable" as MessageKey)}</strong>
              </div>
              <div className="otc-panel">
                <div className="otc-muted">{tr("blocks.result.evidenceHash" as MessageKey)}</div>
                <strong>{result.evidence_hash ?? tr("blocks.notAvailable" as MessageKey)}</strong>
              </div>
              <div className="otc-panel">
                <div className="otc-muted">{tr("blocks.result.matchedLists" as MessageKey)}</div>
                <strong>{matchedLists.length}</strong>
                <div className="otc-controls otc-controls--spaced">
                  {matchedLists.length ? matchedLists.map((entry) => <Pill key={entry} tone="warning">{entry}</Pill>) : <span className="otc-muted">{tr("blocks.none" as MessageKey)}</span>}
                </div>
              </div>
            </div>

            <div className="otc-grid otc-grid--counterparty-form">
              <div className="otc-panel">
                <div className="otc-muted">{tr("blocks.result.regulatoryBasis" as MessageKey)}</div>
                {regulatoryBasis.length ? (
                  <ul className="otc-list">
                    {regulatoryBasis.map((entry) => (
                      <li key={entry}>{entry}</li>
                    ))}
                  </ul>
                ) : (
                  <div className="otc-muted">{tr("blocks.none" as MessageKey)}</div>
                )}
              </div>
              <div className="otc-panel">
                <div className="otc-muted">{tr("blocks.result.address" as MessageKey)}</div>
                <strong>{result.address}</strong>
                <div className="otc-muted">{tr("blocks.result.chain" as MessageKey)} {result.chain}</div>
                <div className="otc-muted">
                  {tr("blocks.stats.requiresCoaf" as MessageKey)} {result.requires_coaf_report ? tr("blocks.yes" as MessageKey) : tr("blocks.no" as MessageKey)}
                </div>
                <div className="otc-muted">
                  {tr("blocks.stats.confidence" as MessageKey)} {Math.round((result.decision_confidence ?? 0) * 100)}%
                </div>
              </div>
            </div>

            <div className="otc-controls">
              {form.caseId.trim() ? (
                <a className="otc-button otc-button--ghost" href={`/cases/${form.caseId.trim()}`}>
                  {tr("blocks.result.openCase" as MessageKey)}
                </a>
              ) : null}
              <a className="otc-button otc-button--ghost" href={buildAuditHref(form.caseId, form.caseId.trim() || result.address, result.block_id ?? "")}>
                {tr("blocks.result.openAudit" as MessageKey)}
              </a>
              <a className="otc-button otc-button--ghost" href={buildEvidenceHref(form.caseId.trim() || result.address, form.caseId, result.block_id ?? "")}>
                {tr("blocks.result.openEvidence" as MessageKey)}
              </a>
              <a
                className="otc-button otc-button--ghost"
                href={`/investigate?address=${encodeURIComponent(result.address)}&chain=${encodeURIComponent(result.chain)}&report_type=technical_basic`}
              >
                {tr("blocks.result.openInvestigate" as MessageKey)}
              </a>
              {result.requires_coaf_report ? (
                <a className="otc-button otc-button--ghost" href={buildRosCoafHref({ caseId: form.caseId, owner: form.owner, priority: form.priority, localDeadline: form.localDeadline })}>
                  {tr("blocks.result.openRos" as MessageKey)}
                </a>
              ) : null}
            </div>

            {result.block_id ? (
              <Panel title={tr("blocks.lift.title" as MessageKey)} description={tr("blocks.lift.description" as MessageKey)}>
                <div className="otc-stack">
                  <label className="otc-field">
                    {tr("blocks.lift.reason" as MessageKey)}
                    <textarea className="otc-textarea" rows={3} value={liftReason} onChange={(event) => setLiftReason(event.target.value)} />
                  </label>
                  <div className="otc-controls">
                    <button className="otc-button otc-button--danger" type="button" data-testid="blocks-lift-btn" onClick={onLift} disabled={lifting || syncingWorkspace || !liftReason.trim()}>
                      {lifting ? tr("blocks.lift.submitting" as MessageKey) : tr("blocks.lift.submit" as MessageKey)}
                    </button>
                    <a className="otc-button otc-button--ghost" href={buildAuditHref(form.caseId, form.caseId.trim() || result.address, result.block_id ?? "")}>
                      {tr("blocks.lift.openAudit" as MessageKey)}
                    </a>
                    <a className="otc-button otc-button--ghost" href={buildEvidenceHref(form.caseId.trim() || result.address, form.caseId, result.block_id ?? "")}>
                      {tr("blocks.lift.openEvidence" as MessageKey)}
                    </a>
                  </div>
                  {liftResult ? (
                    <Message tone="success">
                      {tr("blocks.lift.success" as MessageKey, { status: liftResult.status })}
                    </Message>
                  ) : null}
                </div>
              </Panel>
            ) : null}

            <details className="otc-panel">
              <summary>{tr("blocks.result.raw" as MessageKey)}</summary>
              <div className="otc-controls otc-controls--spaced">
                <CodeBlock>{JSON.stringify(result, null, 2)}</CodeBlock>
              </div>
            </details>
          </div>
        ) : (
          <Message>{tr("blocks.result.empty" as MessageKey)}</Message>
        )}
      </Panel>
    </AppShell>
  );
}

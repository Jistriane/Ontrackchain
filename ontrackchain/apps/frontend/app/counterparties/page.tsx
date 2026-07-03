"use client";

import { useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { AppShell, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import { useI18n } from "../../components/i18n-provider";
import { WorkItemTimelinePanel } from "../../components/work-item-timeline-panel";
import { fetchAuthContext, resolveOwnerUserId, type AuthContext } from "../lib/ownership";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { buildWorkItemTimelineLabels } from "../lib/work-item-timeline-labels";
import { createWorkItemComment, fetchWorkItemTimeline } from "../lib/work-item-timeline-client";
import type { MessageKey } from "../lib/i18n";
import { formatTimelineEvent, type WorkCommentResponse, type WorkItemTimelineResponse } from "../lib/work-item-timeline";

type WorkspacePriority = "critical" | "high" | "normal";
type WorkspaceStatus = "UNDER_REVIEW" | "ESCALATED" | "CLOSED";
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

type CounterpartyListItem = {
  id: string;
  legal_name: string;
  counterparty_type: string;
  document_type: string;
  document_number: string;
  risk_level: number;
  kyc_status: string;
  sanctions_cleared: boolean;
  is_pep: boolean;
  enhanced_dd_required: boolean;
  next_review_date: string | null;
  status: string;
  created_at: string;
};

type CounterpartyListResponse = {
  items: CounterpartyListItem[];
  total: number;
};

type CounterpartyCreateResponse = {
  counterparty_id: string;
  legal_name: string;
  risk_level: number;
  kyc_status: string;
  sanctions_cleared: boolean;
  is_pep: boolean;
  enhanced_dd_required: boolean;
  next_review_date: string;
  status: string;
};

type CounterpartyFormState = {
  counterpartyType: string;
  legalName: string;
  tradingName: string;
  documentType: string;
  documentNumber: string;
  documentCountry: string;
  email: string;
  phone: string;
  businessActivity: string;
  incorporationDate: string;
  nationality: string;
  declaredRiskContext: string;
  onchainRiskScore: string;
  walletChain: string;
  walletAddress: string;
  walletLabel: string;
  beneficialOwnerName: string;
  beneficialOwnerDocument: string;
  beneficialOwnerOwnershipPct: string;
};

type DdReviewStatus = "pending" | "in_progress" | "completed" | "escalated";

type CounterpartyWorkspaceRecord = {
  workItemId?: string;
  source: WorkspaceSource;
  counterpartyId: string;
  legalName: string;
  counterpartyType: string;
  documentType: string;
  documentNumber: string;
  walletChain: string;
  walletAddress: string;
  walletLabel: string;
  riskLevel: number;
  kycStatus: string;
  sanctionsCleared: boolean;
  isPep: boolean;
  enhancedDdRequired: boolean;
  nextReviewDate: string;
  status: string;
  createdAt: string;
  caseId: string;
  owner: string;
  priority: WorkspacePriority;
  localDeadline: string;
  workspaceStatus: WorkspaceStatus;
  note: string;
  // DD/SoF manual review fields
  ddReviewStatus: DdReviewStatus;
  ddReviewNote: string;
  sofDescription: string;
  sofDocumentRef: string;
  lastActionAt: string;
};

const DEFAULT_LIMIT = 20;
const STORAGE_KEY = "otc-counterparties-workspace";
const WORKSPACE_PAGE_LIMIT = 100;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const DEFAULT_FORM: CounterpartyFormState = {
  counterpartyType: "CLIENTE_PJ",
  legalName: "",
  tradingName: "",
  documentType: "CNPJ",
  documentNumber: "",
  documentCountry: "BRA",
  email: "",
  phone: "",
  businessActivity: "",
  incorporationDate: "",
  nationality: "",
  declaredRiskContext: "",
  onchainRiskScore: "",
  walletChain: "ethereum",
  walletAddress: "",
  walletLabel: "",
  beneficialOwnerName: "",
  beneficialOwnerDocument: "",
  beneficialOwnerOwnershipPct: ""
};

const COUNTERPARTY_TYPES = [
  "CLIENTE_PF",
  "CLIENTE_PJ",
  "PARCEIRO_COMERCIAL",
  "PRESTADOR_SERVICO",
  "CONTRAPARTE_DEFI",
  "EXCHANGE_CEX",
  "PROVEDOR_LIQUIDEZ"
] as const;

const DOCUMENT_TYPES = ["CPF", "CNPJ", "PASSPORT", "FOREIGN_ID"] as const;

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

function readMetadataBoolean(metadata: Record<string, unknown>, key: string) {
  return metadata[key] === true;
}

function readMetadataNumber(metadata: Record<string, unknown>, key: string) {
  const value = metadata[key];
  return typeof value === "number" ? value : 0;
}

function normalizeWorkspaceStatus(value: unknown): WorkspaceStatus {
  if (value === "UNDER_REVIEW" || value === "ESCALATED" || value === "CLOSED") {
    return value;
  }
  return "UNDER_REVIEW";
}

function buildRegistrationData(form: CounterpartyFormState) {
  const registrationData: Record<string, string> = {};

  if (form.email.trim()) registrationData.email = form.email.trim();
  if (form.phone.trim()) registrationData.phone = form.phone.trim();
  if (form.businessActivity.trim()) registrationData.business_activity = form.businessActivity.trim();
  if (form.incorporationDate.trim()) registrationData.incorporation_date = form.incorporationDate.trim();
  if (form.nationality.trim()) registrationData.nationality = form.nationality.trim();

  return registrationData;
}

function buildBeneficialOwners(form: CounterpartyFormState) {
  if (!form.beneficialOwnerName.trim() && !form.beneficialOwnerDocument.trim()) {
    return [];
  }

  return [
    {
      name: form.beneficialOwnerName.trim(),
      document: form.beneficialOwnerDocument.trim(),
      ownership_pct: form.beneficialOwnerOwnershipPct.trim() ? Number(form.beneficialOwnerOwnershipPct) : null
    }
  ];
}

function buildWalletAddresses(form: CounterpartyFormState) {
  if (!form.walletAddress.trim()) {
    return [];
  }

  return [
    {
      chain: form.walletChain,
      address: form.walletAddress.trim(),
      label: form.walletLabel.trim() || "primary"
    }
  ];
}

function buildCaseHref(caseId: string) {
  const normalizedCaseId = caseId.trim();
  return normalizedCaseId ? `/cases/${encodeURIComponent(normalizedCaseId)}` : null;
}

function buildAuditHref(caseId: string, resourceId: string, counterpartyId = "") {
  const params = new URLSearchParams({
    resource_type: "case",
    resource_id: resourceId.trim() || counterpartyId.trim()
  });
  if (caseId.trim()) {
    params.set("request_id", caseId.trim());
  }
  if (counterpartyId.trim()) {
    params.set("report_id", counterpartyId.trim());
  }
  return `/audit?${params.toString()}`;
}

function buildEvidenceHref(resourceId: string, caseId: string, counterpartyId = "") {
  const params = new URLSearchParams({
    domain: "compliance",
    resource_type: "case",
    resource_id: resourceId.trim() || counterpartyId.trim()
  });
  if (caseId.trim()) {
    params.set("request_id", caseId.trim());
  }
  if (counterpartyId.trim()) {
    params.set("report_id", counterpartyId.trim());
  }
  return `/evidence?${params.toString()}`;
}

function buildSanctionsHref(record: {
  walletAddress: string;
  walletChain: string;
  caseId: string;
  owner: string;
  priority: WorkspacePriority;
  localDeadline: string;
  legalName: string;
  documentNumber: string;
}) {
  const params = new URLSearchParams({
    case_id: record.caseId.trim(),
    owner: record.owner.trim(),
    priority: record.priority,
    deadline: record.localDeadline.trim(),
    triage_note: `${record.legalName.trim()} ${record.documentNumber.trim()}`.trim()
  });
  if (record.walletAddress.trim()) {
    params.set("address", record.walletAddress.trim());
    params.set("chain", record.walletChain.trim() || "ethereum");
    params.set("autostart", "1");
  }
  return `/sanctions?${params.toString()}`;
}

function riskTone(level: number): "success" | "warning" | "danger" {
  if (level >= 4) return "danger";
  if (level >= 3) return "warning";
  return "success";
}

function loadWorkspace(): CounterpartyWorkspaceRecord[] {
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
          const record = (entry ?? {}) as Partial<CounterpartyWorkspaceRecord>;
          const counterpartyId = typeof record.counterpartyId === "string" ? record.counterpartyId : "";
          const source: WorkspaceSource = record.source === "server" ? "server" : "local";
          return {
            workItemId: typeof record.workItemId === "string" ? record.workItemId : undefined,
            source,
            counterpartyId,
            legalName: typeof record.legalName === "string" ? record.legalName : "",
            counterpartyType: typeof record.counterpartyType === "string" ? record.counterpartyType : "",
            documentType: typeof record.documentType === "string" ? record.documentType : "",
            documentNumber: typeof record.documentNumber === "string" ? record.documentNumber : "",
            walletChain: typeof record.walletChain === "string" ? record.walletChain : "",
            walletAddress: typeof record.walletAddress === "string" ? record.walletAddress : "",
            walletLabel: typeof record.walletLabel === "string" ? record.walletLabel : "",
            riskLevel: typeof record.riskLevel === "number" ? record.riskLevel : 0,
            kycStatus: typeof record.kycStatus === "string" ? record.kycStatus : "",
            sanctionsCleared: record.sanctionsCleared === true,
            isPep: record.isPep === true,
            enhancedDdRequired: record.enhancedDdRequired === true,
            nextReviewDate: typeof record.nextReviewDate === "string" ? record.nextReviewDate : "",
            status: typeof record.status === "string" ? record.status : "",
            createdAt: typeof record.createdAt === "string" ? record.createdAt : "",
            caseId: typeof record.caseId === "string" ? record.caseId : "",
            owner: typeof record.owner === "string" ? record.owner : "",
            priority: record.priority === "critical" || record.priority === "high" || record.priority === "normal" ? record.priority : "normal",
            localDeadline: typeof record.localDeadline === "string" ? record.localDeadline : "",
            workspaceStatus: normalizeWorkspaceStatus(record.workspaceStatus),
            note: typeof record.note === "string" ? record.note : "",
            ddReviewStatus:
              record.ddReviewStatus === "in_progress" || record.ddReviewStatus === "completed" || record.ddReviewStatus === "escalated"
                ? record.ddReviewStatus
                : "pending",
            ddReviewNote: typeof record.ddReviewNote === "string" ? record.ddReviewNote : "",
            sofDescription: typeof record.sofDescription === "string" ? record.sofDescription : "",
            sofDocumentRef: typeof record.sofDocumentRef === "string" ? record.sofDocumentRef : "",
            lastActionAt: typeof record.lastActionAt === "string" ? record.lastActionAt : ""
          };
        })
      : [];
  } catch {
    return [];
  }
}

function saveWorkspace(records: CounterpartyWorkspaceRecord[]) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
}

function upsertWorkspaceRecord(
  current: CounterpartyWorkspaceRecord[],
  next: Partial<CounterpartyWorkspaceRecord> & { counterpartyId: string }
): CounterpartyWorkspaceRecord[] {
  const existing = current.find((record) => record.counterpartyId === next.counterpartyId);
  const base: CounterpartyWorkspaceRecord =
    existing ?? {
      workItemId: next.workItemId,
      source: next.source ?? "local",
      counterpartyId: next.counterpartyId,
      legalName: "",
      counterpartyType: "",
      documentType: "",
      documentNumber: "",
      walletChain: "",
      walletAddress: "",
      walletLabel: "",
      riskLevel: 0,
      kycStatus: "",
      sanctionsCleared: false,
      isPep: false,
      enhancedDdRequired: false,
      nextReviewDate: "",
      status: "",
      createdAt: "",
      caseId: "",
      owner: "",
      priority: "normal",
      localDeadline: "",
      workspaceStatus: "UNDER_REVIEW",
      note: "",
      ddReviewStatus: "pending",
      ddReviewNote: "",
      sofDescription: "",
      sofDocumentRef: "",
      lastActionAt: ""
    };

  const merged: CounterpartyWorkspaceRecord = {
    ...base,
    ...next,
    lastActionAt: next.lastActionAt ?? new Date().toISOString()
  };

  return [merged, ...current.filter((record) => record.counterpartyId !== next.counterpartyId)].sort((a, b) =>
    (b.lastActionAt || "").localeCompare(a.lastActionAt || "")
  );
}

function mergeWorkspaceRecords(serverRecords: CounterpartyWorkspaceRecord[], localRecords: CounterpartyWorkspaceRecord[]) {
  const merged = [...serverRecords];
  const seenCounterpartyIds = new Set(serverRecords.map((record) => record.counterpartyId));
  const seenWorkItemIds = new Set(serverRecords.map((record) => record.workItemId).filter(Boolean));

  for (const record of localRecords) {
    if (seenCounterpartyIds.has(record.counterpartyId)) {
      continue;
    }
    if (record.workItemId && seenWorkItemIds.has(record.workItemId)) {
      continue;
    }
    merged.push(record);
  }

  return merged.sort((a, b) => (b.lastActionAt || "").localeCompare(a.lastActionAt || ""));
}

function mapQueueStatusToWorkspaceStatus(status: WorkItemQueueStatus): WorkspaceStatus {
  if (status === "CLOSED" || status === "APPROVED" || status === "SUBMITTED") {
    return "CLOSED";
  }
  if (status === "ESCALATED" || status === "REJECTED") {
    return "ESCALATED";
  }
  return "UNDER_REVIEW";
}

function mapWorkItemToWorkspaceRecord(item: WorkItemResponse): CounterpartyWorkspaceRecord {
  const metadata = item.metadata ?? {};
  const counterpartyId = readMetadataString(metadata, "counterparty_id") || item.resource_id;
  return {
    workItemId: item.id,
    source: "server",
    counterpartyId,
    legalName: readMetadataString(metadata, "legal_name"),
    counterpartyType: readMetadataString(metadata, "counterparty_type"),
    documentType: readMetadataString(metadata, "document_type"),
    documentNumber: readMetadataString(metadata, "document_number"),
    walletChain: readMetadataString(metadata, "wallet_chain"),
    walletAddress: readMetadataString(metadata, "wallet_address"),
    walletLabel: readMetadataString(metadata, "wallet_label"),
    riskLevel: readMetadataNumber(metadata, "risk_level"),
    kycStatus: readMetadataString(metadata, "kyc_status"),
    sanctionsCleared: readMetadataBoolean(metadata, "sanctions_cleared"),
    isPep: readMetadataBoolean(metadata, "is_pep"),
    enhancedDdRequired: readMetadataBoolean(metadata, "enhanced_dd_required"),
    nextReviewDate: readMetadataString(metadata, "next_review_date"),
    status: readMetadataString(metadata, "status"),
    createdAt: readMetadataString(metadata, "created_at"),
    caseId: readMetadataString(metadata, "case_id"),
    owner: readMetadataString(metadata, "owner_label") || item.owner_user_id || "",
    priority: item.priority,
    localDeadline: toDateTimeLocalValue(item.due_at),
    workspaceStatus: normalizeWorkspaceStatus(metadata["local_workspace_status"]) || mapQueueStatusToWorkspaceStatus(item.queue_status),
    note: item.note ?? readMetadataString(metadata, "note"),
    ddReviewStatus: (readMetadataString(metadata, "dd_review_status") || "pending") as DdReviewStatus,
    ddReviewNote: readMetadataString(metadata, "dd_review_note"),
    sofDescription: readMetadataString(metadata, "sof_description"),
    sofDocumentRef: readMetadataString(metadata, "sof_document_ref"),
    lastActionAt: item.last_activity_at || item.updated_at
  };
}

function getUrgency(record: CounterpartyWorkspaceRecord): "overdue" | "due_soon" | "on_track" | "no_deadline" {
  if (!record.localDeadline) {
    return "no_deadline";
  }
  if (record.workspaceStatus === "CLOSED") {
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

function toneForUrgency(urgency: ReturnType<typeof getUrgency>): "warning" | "danger" | undefined {
  if (urgency === "overdue") return "danger";
  if (urgency === "due_soon") return "warning";
  return undefined;
}

function toneForWorkspaceStatus(status: WorkspaceStatus): "warning" | "danger" | undefined {
  if (status === "ESCALATED") return "danger";
  if (status === "UNDER_REVIEW") return "warning";
  return undefined;
}

export default function CounterpartiesPage() {
  const searchParams = useSearchParams();
  const { t } = useI18n();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);
  const [items, setItems] = useState<CounterpartyListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [syncingWorkspace, setSyncingWorkspace] = useState(false);
  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [form, setForm] = useState<CounterpartyFormState>(DEFAULT_FORM);
  const [workspaceRecords, setWorkspaceRecords] = useState<CounterpartyWorkspaceRecord[]>([]);
  const [ddReviewCounterpartyId, setDdReviewCounterpartyId] = useState<string>("");
  const [workspaceFilter, setWorkspaceFilter] = useState("all");
  const [workspaceSearch, setWorkspaceSearch] = useState("");
  const [workspaceNoteId, setWorkspaceNoteId] = useState<string>("");
  const [timelineCounterpartyId, setTimelineCounterpartyId] = useState<string>("");
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineError, setTimelineError] = useState<string | null>(null);
  const [timelineData, setTimelineData] = useState<WorkItemTimelineResponse<WorkItemResponse> | null>(null);
  const [commentType, setCommentType] = useState<WorkCommentResponse["comment_type"]>("note");
  const [commentBody, setCommentBody] = useState("");
  const [commentSubmitting, setCommentSubmitting] = useState(false);

  const highRiskCount = useMemo(() => items.filter((item) => item.risk_level >= 3).length, [items]);
  const pendingKycCount = useMemo(() => items.filter((item) => item.kyc_status !== "APPROVED").length, [items]);
  const totalPages = Math.max(1, Math.ceil(total / DEFAULT_LIMIT));
  const currentPage = Math.floor(offset / DEFAULT_LIMIT) + 1;
  const trackedCount = useMemo(() => workspaceRecords.length, [workspaceRecords]);
  const pendingReviewCount = useMemo(
    () => workspaceRecords.filter((record) => record.workspaceStatus === "UNDER_REVIEW" || record.workspaceStatus === "ESCALATED").length,
    [workspaceRecords]
  );
  const overdueCount = useMemo(() => workspaceRecords.filter((record) => getUrgency(record) === "overdue").length, [workspaceRecords]);
  const workspaceById = useMemo(
    () => new Map(workspaceRecords.map((record) => [record.counterpartyId, record])),
    [workspaceRecords]
  );
  const selectedTimelineRecord = timelineCounterpartyId ? workspaceById.get(timelineCounterpartyId) ?? null : null;

  async function loadTimeline(workItemId: string) {
    setTimelineLoading(true);
    setTimelineError(null);
    const result = await fetchWorkItemTimeline<WorkItemResponse>(workItemId);
    if (!result.ok) {
      setTimelineData(null);
      setTimelineError(resolveApiErrorMessage(t, result.error, tr("counterparties.workspace.timeline.errorLoad" as MessageKey)));
      setTimelineLoading(false);
      return;
    }

    setTimelineData(result.data);
    setTimelineLoading(false);
  }

  async function loadOperationalWorkspace(localRecords: CounterpartyWorkspaceRecord[]) {
    const res = await fetch(
      `/api/app/operations/work-items?module=counterparties&resource_type=counterparty&limit=${WORKSPACE_PAGE_LIMIT}`,
      { cache: "no-store" }
    );
    const data = (await res.json().catch(() => null)) as WorkItemListResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setWorkspaceRecords(localRecords);
      setNotice(tr("counterparties.workspace.noticeLoadedLocal" as MessageKey));
      return;
    }

    const items = data && "data" in data && Array.isArray(data.data) ? data.data : [];
    const serverRecords = items.map((item) => mapWorkItemToWorkspaceRecord(item));
    setWorkspaceRecords(mergeWorkspaceRecords(serverRecords, localRecords));
  }

  async function loadCounterparties(nextOffset = offset) {
    setLoading(true);
    setError(null);
    const res = await fetch(`/api/app/compliance/counterparties?limit=${DEFAULT_LIMIT}&offset=${nextOffset}`, { cache: "no-store" });
    const data = (await res.json().catch(() => null)) as CounterpartyListResponse | { error?: string; detail?: string } | null;
    if (!res.ok) {
      setItems([]);
      setTotal(0);
      setError(
        resolveApiErrorMessage(t, data, tr("counterparties.errorLoad" as MessageKey))
      );
      setLoading(false);
      return;
    }

    setItems(data && "items" in data ? data.items : []);
    setTotal(data && "total" in data ? data.total : 0);
    setOffset(nextOffset);
    setLoading(false);
  }

  useEffect(() => {
    loadCounterparties(0).catch(() => {
      setError(tr("counterparties.errorLoad" as MessageKey));
      setLoading(false);
    });
  }, [t]);

  useEffect(() => {
    const localRecords = loadWorkspace();
    setWorkspaceRecords(localRecords);
    loadOperationalWorkspace(localRecords).catch(() => {
      setWorkspaceRecords(localRecords);
      setNotice(tr("counterparties.workspace.noticeLoadedLocal" as MessageKey));
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
    const counterpartyId = searchParams.get("counterparty_id");
    const legalName = searchParams.get("legal_name");
    const counterpartyType = searchParams.get("counterparty_type");
    const documentType = searchParams.get("document_type");
    const documentNumber = searchParams.get("document_number");
    const documentCountry = searchParams.get("document_country");
    const email = searchParams.get("email");
    const phone = searchParams.get("phone");
    const businessActivity = searchParams.get("business_activity");
    const incorporationDate = searchParams.get("incorporation_date");
    const nationality = searchParams.get("nationality");
    const declaredRiskContext = searchParams.get("declared_risk_context");
    const onchainRiskScore = searchParams.get("onchain_risk_score");
    const walletChain = searchParams.get("wallet_chain");
    const walletAddress = searchParams.get("wallet_address");
    const walletLabel = searchParams.get("wallet_label");
    const beneficialOwnerName = searchParams.get("beneficial_owner_name");
    const beneficialOwnerDocument = searchParams.get("beneficial_owner_document");
    const beneficialOwnerOwnershipPct = searchParams.get("beneficial_owner_ownership_pct");
    const caseId = searchParams.get("case_id");
    const owner = searchParams.get("owner");
    const priority = searchParams.get("priority") as WorkspacePriority | null;
    const deadline = searchParams.get("deadline");
    const note = searchParams.get("note");

    if (
      !counterpartyId &&
      !legalName &&
      !documentNumber &&
      !walletAddress &&
      !caseId &&
      !owner &&
      !deadline
    ) {
      return;
    }

    setForm((current) => ({
      ...current,
      counterpartyType: counterpartyType ?? current.counterpartyType,
      legalName: legalName ?? current.legalName,
      documentType: documentType ?? current.documentType,
      documentNumber: documentNumber ?? current.documentNumber,
      documentCountry: documentCountry ?? current.documentCountry,
      email: email ?? current.email,
      phone: phone ?? current.phone,
      businessActivity: businessActivity ?? current.businessActivity,
      incorporationDate: incorporationDate ?? current.incorporationDate,
      nationality: nationality ?? current.nationality,
      declaredRiskContext: declaredRiskContext ?? current.declaredRiskContext,
      onchainRiskScore: onchainRiskScore ?? current.onchainRiskScore,
      walletChain: walletChain ?? current.walletChain,
      walletAddress: walletAddress ?? current.walletAddress,
      walletLabel: walletLabel ?? current.walletLabel,
      beneficialOwnerName: beneficialOwnerName ?? current.beneficialOwnerName,
      beneficialOwnerDocument: beneficialOwnerDocument ?? current.beneficialOwnerDocument,
      beneficialOwnerOwnershipPct: beneficialOwnerOwnershipPct ?? current.beneficialOwnerOwnershipPct
    }));

    if (counterpartyId) {
      setWorkspaceRecords((current) =>
        upsertWorkspaceRecord(current, {
          workItemId: current.find((record) => record.counterpartyId === counterpartyId)?.workItemId,
          source: "local",
          counterpartyId,
          legalName: legalName ?? "",
          counterpartyType: counterpartyType ?? "",
          documentType: documentType ?? "",
          documentNumber: documentNumber ?? "",
          walletChain: walletChain ?? "",
          walletAddress: walletAddress ?? "",
          walletLabel: walletLabel ?? "",
          caseId: caseId ?? "",
          owner: owner ?? "",
          priority: priority === "critical" || priority === "high" || priority === "normal" ? priority : "normal",
          localDeadline: deadline ?? "",
          note: note ?? ""
        })
      );
    }
  }, [searchParams]);

  useEffect(() => {
    saveWorkspace(workspaceRecords);
  }, [workspaceRecords]);

  useEffect(() => {
    if (!workspaceRecords.length) {
      setWorkspaceNoteId("");
      setTimelineCounterpartyId("");
      setTimelineData(null);
      setTimelineError(null);
      return;
    }
    if (!workspaceNoteId || !workspaceRecords.some((record) => record.counterpartyId === workspaceNoteId)) {
      setWorkspaceNoteId(workspaceRecords[0].counterpartyId);
    }
    if (!timelineCounterpartyId || !workspaceRecords.some((record) => record.counterpartyId === timelineCounterpartyId)) {
      const firstServerRecord = workspaceRecords.find((record) => Boolean(record.workItemId)) ?? workspaceRecords[0];
      setTimelineCounterpartyId(firstServerRecord.counterpartyId);
    }
  }, [timelineCounterpartyId, workspaceNoteId, workspaceRecords]);

  useEffect(() => {
    const currentRecord = timelineCounterpartyId ? workspaceById.get(timelineCounterpartyId) : null;
    if (!currentRecord?.workItemId) {
      setTimelineData(null);
      setTimelineError(null);
      return;
    }
    loadTimeline(currentRecord.workItemId).catch(() => {
      setTimelineData(null);
      setTimelineError(tr("counterparties.workspace.timeline.errorLoad" as MessageKey));
      setTimelineLoading(false);
    });
  }, [timelineCounterpartyId, workspaceById, t]);

  function updateForm<K extends keyof CounterpartyFormState>(key: K, value: CounterpartyFormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function syncWorkspaceRecord(record: CounterpartyWorkspaceRecord, nextStatus?: WorkspaceStatus) {
    if (!isUuidLike(record.counterpartyId)) {
      throw new Error(tr("counterparties.workspace.errorSyncMissingCounterpartyId" as MessageKey));
    }

    const ownerUserId = resolveOwnerUserId({
      ownerLabel: record.owner,
      linkedUserId: authContext?.linked_user_id,
      isUuidLike
    });

    const localStatus = nextStatus ?? record.workspaceStatus;
    const queueStatus: WorkItemQueueStatus = localStatus;
    const metadata = {
      counterparty_id: record.counterpartyId,
      legal_name: record.legalName,
      counterparty_type: record.counterpartyType,
      document_type: record.documentType,
      document_number: record.documentNumber,
      wallet_chain: record.walletChain,
      wallet_address: record.walletAddress,
      wallet_label: record.walletLabel,
      risk_level: record.riskLevel,
      kyc_status: record.kycStatus,
      sanctions_cleared: record.sanctionsCleared,
      is_pep: record.isPep,
      enhanced_dd_required: record.enhancedDdRequired,
      next_review_date: record.nextReviewDate,
      status: record.status,
      created_at: record.createdAt,
      case_id: record.caseId,
      owner_user_id: ownerUserId,
      owner_label: record.owner,
      local_workspace_status: localStatus,
      note: record.note,
      dd_review_status: record.ddReviewStatus,
      dd_review_note: record.ddReviewNote,
      sof_description: record.sofDescription,
      sof_document_ref: record.sofDocumentRef
    };
    const requestBody = record.workItemId
      ? {
          ...(ownerUserId ? { owner_user_id: ownerUserId } : {}),
          priority: record.priority,
          queue_status: queueStatus,
          due_at: toApiDueAt(record.localDeadline),
          title: `Counterparty review • ${record.legalName || record.counterpartyId}`,
          note: record.note || null,
          metadata
        }
      : {
          module: "counterparties",
          resource_type: "counterparty",
          resource_id: record.counterpartyId,
          ...(isUuidLike(record.caseId) ? { case_id: record.caseId.trim() } : {}),
          ...(ownerUserId ? { owner_user_id: ownerUserId } : {}),
          priority: record.priority,
          queue_status: queueStatus,
          due_at: toApiDueAt(record.localDeadline),
          title: `Counterparty review • ${record.legalName || record.counterpartyId}`,
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
      throw new Error(resolveApiErrorMessage(t, data, tr("counterparties.workspace.errorSync" as MessageKey)));
    }

    const nextRecord = mapWorkItemToWorkspaceRecord(data as WorkItemResponse);
    setWorkspaceRecords((current) => upsertWorkspaceRecord(current, nextRecord));
    if (timelineCounterpartyId === nextRecord.counterpartyId && nextRecord.workItemId) {
      await loadTimeline(nextRecord.workItemId);
    }
    return nextRecord;
  }

  async function syncRecordById(counterpartyId: string) {
    const currentRecord = workspaceById.get(counterpartyId);
    if (!currentRecord) {
      return null;
    }
    return syncWorkspaceRecord(currentRecord);
  }

  function trackFromList(item: CounterpartyListItem) {
    void (async () => {
      const draftRecord: CounterpartyWorkspaceRecord = {
        workItemId: workspaceById.get(item.id)?.workItemId,
        source: "local",
        counterpartyId: item.id,
        legalName: item.legal_name,
        counterpartyType: item.counterparty_type,
        documentType: item.document_type,
        documentNumber: item.document_number,
        riskLevel: item.risk_level,
        kycStatus: item.kyc_status,
        sanctionsCleared: item.sanctions_cleared,
        isPep: item.is_pep,
        enhancedDdRequired: item.enhanced_dd_required,
        nextReviewDate: item.next_review_date ?? "",
        status: item.status,
        createdAt: item.created_at,
        walletChain: "",
        walletAddress: "",
        walletLabel: "",
        caseId: workspaceById.get(item.id)?.caseId ?? "",
        owner: workspaceById.get(item.id)?.owner ?? "",
        priority: workspaceById.get(item.id)?.priority ?? "normal",
        localDeadline: workspaceById.get(item.id)?.localDeadline ?? "",
        workspaceStatus: item.kyc_status === "APPROVED" && item.sanctions_cleared ? "CLOSED" : "UNDER_REVIEW",
        note: workspaceById.get(item.id)?.note ?? "",
        ddReviewStatus: workspaceById.get(item.id)?.ddReviewStatus ?? "pending",
        ddReviewNote: workspaceById.get(item.id)?.ddReviewNote ?? "",
        sofDescription: workspaceById.get(item.id)?.sofDescription ?? "",
        sofDocumentRef: workspaceById.get(item.id)?.sofDocumentRef ?? "",
        lastActionAt: new Date().toISOString()
      };
      setWorkspaceRecords((current) => upsertWorkspaceRecord(current, draftRecord));
      if (!isUuidLike(item.id)) {
        setNotice(tr("counterparties.workspace.noticeTrackedLocalOnly" as MessageKey, { name: item.legal_name }));
        return;
      }

      try {
        await syncWorkspaceRecord(draftRecord);
        setNotice(tr("counterparties.workspace.noticeTrackedSynced" as MessageKey, { name: item.legal_name }));
      } catch (syncError) {
        setNotice(tr("counterparties.workspace.noticeTrackedLocalOnly" as MessageKey, { name: item.legal_name }));
        setError(syncError instanceof Error ? syncError.message : tr("counterparties.workspace.errorSync" as MessageKey));
      }
    })();
  }

  function hydrateWorkspaceRecord(record: CounterpartyWorkspaceRecord) {
    setTimelineCounterpartyId(record.counterpartyId);
    setForm((current) => ({
      ...current,
      counterpartyType: record.counterpartyType || current.counterpartyType,
      legalName: record.legalName || current.legalName,
      documentType: record.documentType || current.documentType,
      documentNumber: record.documentNumber || current.documentNumber,
      documentCountry: current.documentCountry,
      walletChain: record.walletChain || current.walletChain,
      walletAddress: record.walletAddress || current.walletAddress,
      walletLabel: record.walletLabel || current.walletLabel
    }));
  }

  function updateWorkspaceStatus(counterpartyId: string, status: WorkspaceStatus) {
    void (async () => {
      const currentRecord = workspaceById.get(counterpartyId);
      if (!currentRecord) {
        return;
      }

      const draftRecord = { ...currentRecord, workspaceStatus: status, lastActionAt: new Date().toISOString() };
      setWorkspaceRecords((current) =>
        upsertWorkspaceRecord(current, {
          counterpartyId,
          workspaceStatus: status,
          lastActionAt: draftRecord.lastActionAt
        })
      );
      try {
        await syncWorkspaceRecord(draftRecord, status);
        setNotice(tr("counterparties.workspace.noticeUpdatedSynced" as MessageKey));
      } catch (syncError) {
        setError(syncError instanceof Error ? syncError.message : tr("counterparties.workspace.errorSync" as MessageKey));
        setNotice(tr("counterparties.workspace.noticeUpdatedLocalOnly" as MessageKey));
      }
    })();
  }

  function removeWorkspaceRecord(counterpartyId: string) {
    setWorkspaceRecords((current) => current.filter((record) => record.counterpartyId !== counterpartyId));
  }

  function updateWorkspaceField<K extends keyof CounterpartyWorkspaceRecord>(counterpartyId: string, key: K, value: CounterpartyWorkspaceRecord[K]) {
    setWorkspaceRecords((current) =>
      upsertWorkspaceRecord(current, {
        counterpartyId,
        [key]: value,
        lastActionAt: new Date().toISOString()
      })
    );
  }

  async function submitTimelineComment() {
    if (!selectedTimelineRecord?.workItemId) {
      setTimelineError(tr("counterparties.workspace.timeline.emptyLocal" as MessageKey));
      return;
    }
    if (!commentBody.trim()) {
      setTimelineError(tr("counterparties.workspace.timeline.commentEmpty" as MessageKey));
      return;
    }

    setCommentSubmitting(true);
    setTimelineError(null);
    const result = await createWorkItemComment(selectedTimelineRecord.workItemId, {
      comment_type: commentType,
      body: commentBody.trim()
    });
    if (!result.ok) {
      setTimelineError(resolveApiErrorMessage(t, result.error, tr("counterparties.workspace.timeline.errorComment" as MessageKey)));
      setCommentSubmitting(false);
      return;
    }

    setCommentBody("");
    setCommentType("note");
    await loadTimeline(selectedTimelineRecord.workItemId);
    setNotice(tr("counterparties.workspace.timeline.commentSaved" as MessageKey));
    setCommentSubmitting(false);
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setNotice(null);

    const payload = {
      counterparty_type: form.counterpartyType,
      legal_name: form.legalName.trim(),
      trading_name: form.tradingName.trim() || null,
      document_type: form.documentType,
      document_number: form.documentNumber.trim(),
      document_country: form.documentCountry.trim() || "BRA",
      registration_data: buildRegistrationData(form),
      beneficial_owners: buildBeneficialOwners(form),
      wallet_addresses: buildWalletAddresses(form),
      declared_risk_context: form.declaredRiskContext.trim() || null,
      onchain_risk_score: form.onchainRiskScore.trim() ? Number(form.onchainRiskScore) : null
    };

    try {
      const res = await fetch("/api/app/compliance/counterparties", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = (await res.json().catch(() => null)) as CounterpartyCreateResponse | { error?: string; detail?: string } | null;
      if (!res.ok) {
        throw new Error(resolveApiErrorMessage(t, data, t("counterparties.errorCreate")));
      }

      setNotice(
        tr("counterparties.successCreated" as MessageKey, {
          name: data && "legal_name" in data ? data.legal_name : payload.legal_name
        })
      );
      if (data && "counterparty_id" in data) {
        const draftRecord: CounterpartyWorkspaceRecord = {
          workItemId: workspaceById.get(data.counterparty_id)?.workItemId,
          source: "local",
          counterpartyId: data.counterparty_id,
          legalName: data.legal_name,
          counterpartyType: form.counterpartyType,
          documentType: form.documentType,
          documentNumber: form.documentNumber.trim(),
          walletChain: form.walletChain,
          walletAddress: form.walletAddress.trim(),
          walletLabel: form.walletLabel.trim(),
          riskLevel: data.risk_level,
          kycStatus: data.kyc_status,
          sanctionsCleared: data.sanctions_cleared,
          isPep: data.is_pep,
          enhancedDdRequired: data.enhanced_dd_required,
          nextReviewDate: data.next_review_date,
          status: data.status,
          createdAt: new Date().toISOString(),
          caseId: "",
          owner: "",
          priority: "normal",
          localDeadline: "",
          workspaceStatus: data.kyc_status === "APPROVED" && data.sanctions_cleared ? "CLOSED" : "UNDER_REVIEW",
          note: "",
          ddReviewStatus: "pending",
          ddReviewNote: "",
          sofDescription: "",
          sofDocumentRef: "",
          lastActionAt: new Date().toISOString()
        };
        setWorkspaceRecords((current) => upsertWorkspaceRecord(current, draftRecord));
        try {
          await syncWorkspaceRecord(draftRecord);
          setNotice(tr("counterparties.workspace.noticeTrackedSynced" as MessageKey, { name: data.legal_name }));
        } catch (syncError) {
          setNotice(tr("counterparties.workspace.noticeTrackedLocalOnly" as MessageKey, { name: data.legal_name }));
          setError(syncError instanceof Error ? syncError.message : tr("counterparties.workspace.errorSync" as MessageKey));
        }
      }
      setForm(DEFAULT_FORM);
      await loadCounterparties(0);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : tr("counterparties.errorCreate" as MessageKey));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppShell
      title={tr("counterparties.title" as MessageKey)}
      subtitle={tr("counterparties.subtitle" as MessageKey)}
      activePath="/counterparties"
      actions={<Pill>{tr("counterparties.active" as MessageKey)}</Pill>}
    >
      <MetricGrid>
        <MetricCard label={tr("counterparties.stats.total" as MessageKey)} value={loading ? "..." : total} meta={tr("counterparties.stats.totalMeta" as MessageKey)} />
        <MetricCard label={tr("counterparties.stats.currentSlice" as MessageKey)} value={loading ? "..." : items.length} meta={tr("counterparties.stats.currentSliceMeta" as MessageKey)} />
        <MetricCard label={tr("counterparties.stats.highRisk" as MessageKey)} value={loading ? "..." : highRiskCount} meta={tr("counterparties.stats.highRiskMeta" as MessageKey)} accent />
        <MetricCard label={tr("counterparties.stats.pendingKyc" as MessageKey)} value={loading ? "..." : pendingKycCount} meta={tr("counterparties.stats.pendingKycMeta" as MessageKey)} />
      </MetricGrid>

      <MetricGrid>
        <MetricCard label={tr("counterparties.workspace.stats.tracked" as MessageKey)} value={trackedCount} meta={tr("counterparties.workspace.stats.trackedMeta" as MessageKey)} />
        <MetricCard label={tr("counterparties.workspace.stats.pendingReview" as MessageKey)} value={pendingReviewCount} meta={tr("counterparties.workspace.stats.pendingReviewMeta" as MessageKey)} accent />
        <MetricCard label={tr("counterparties.workspace.stats.overdue" as MessageKey)} value={overdueCount} meta={tr("counterparties.workspace.stats.overdueMeta" as MessageKey)} />
        <MetricCard label={tr("counterparties.workspace.stats.highRiskTracked" as MessageKey)} value={workspaceRecords.filter((record) => record.riskLevel >= 3).length} meta={tr("counterparties.workspace.stats.highRiskTrackedMeta" as MessageKey)} />
      </MetricGrid>

      <Panel title={tr("counterparties.form.title" as MessageKey)} description={tr("counterparties.form.description" as MessageKey)}>
        <form className="otc-stack" onSubmit={onSubmit}>
          <div className="otc-grid otc-grid--counterparty-form">
            <label className="otc-field">
              {tr("counterparties.form.counterpartyType" as MessageKey)}
              <select className="otc-select" value={form.counterpartyType} onChange={(event) => updateForm("counterpartyType", event.target.value)}>
                {COUNTERPARTY_TYPES.map((item) => (
                  <option key={item} value={item}>
                    {tr(`counterparties.types.${item}` as MessageKey)}
                  </option>
                ))}
              </select>
            </label>
            <label className="otc-field">
              {tr("counterparties.form.legalName" as MessageKey)}
              <input className="otc-input" data-testid="counterparty-legal-name" value={form.legalName} onChange={(event) => updateForm("legalName", event.target.value)} required />
            </label>
            <label className="otc-field">
              {tr("counterparties.form.tradingName" as MessageKey)}
              <input className="otc-input" value={form.tradingName} onChange={(event) => updateForm("tradingName", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("counterparties.form.documentType" as MessageKey)}
              <select className="otc-select" value={form.documentType} onChange={(event) => updateForm("documentType", event.target.value)}>
                {DOCUMENT_TYPES.map((item) => (
                  <option key={item} value={item}>
                    {tr(`counterparties.document.${item}` as MessageKey)}
                  </option>
                ))}
              </select>
            </label>
            <label className="otc-field">
              {tr("counterparties.form.documentNumber" as MessageKey)}
              <input className="otc-input" data-testid="counterparty-document-number" value={form.documentNumber} onChange={(event) => updateForm("documentNumber", event.target.value)} required />
            </label>
            <label className="otc-field">
              {tr("counterparties.form.documentCountry" as MessageKey)}
              <input className="otc-input" value={form.documentCountry} maxLength={3} onChange={(event) => updateForm("documentCountry", event.target.value.toUpperCase())} />
            </label>
            <label className="otc-field">
              {tr("counterparties.form.email" as MessageKey)}
              <input className="otc-input" type="email" value={form.email} onChange={(event) => updateForm("email", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("counterparties.form.phone" as MessageKey)}
              <input className="otc-input" value={form.phone} onChange={(event) => updateForm("phone", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("counterparties.form.businessActivity" as MessageKey)}
              <input className="otc-input" value={form.businessActivity} onChange={(event) => updateForm("businessActivity", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("counterparties.form.incorporationDate" as MessageKey)}
              <input className="otc-input" type="date" value={form.incorporationDate} onChange={(event) => updateForm("incorporationDate", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("counterparties.form.nationality" as MessageKey)}
              <input className="otc-input" value={form.nationality} onChange={(event) => updateForm("nationality", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("counterparties.form.onchainRiskScore" as MessageKey)}
              <input className="otc-input" type="number" min="0" max="100" value={form.onchainRiskScore} onChange={(event) => updateForm("onchainRiskScore", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("counterparties.form.walletChain" as MessageKey)}
              <input className="otc-input" value={form.walletChain} onChange={(event) => updateForm("walletChain", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("counterparties.form.walletAddress" as MessageKey)}
              <input className="otc-input" value={form.walletAddress} onChange={(event) => updateForm("walletAddress", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("counterparties.form.walletLabel" as MessageKey)}
              <input className="otc-input" value={form.walletLabel} onChange={(event) => updateForm("walletLabel", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("counterparties.form.beneficialOwnerName" as MessageKey)}
              <input className="otc-input" value={form.beneficialOwnerName} onChange={(event) => updateForm("beneficialOwnerName", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("counterparties.form.beneficialOwnerDocument" as MessageKey)}
              <input className="otc-input" value={form.beneficialOwnerDocument} onChange={(event) => updateForm("beneficialOwnerDocument", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("counterparties.form.beneficialOwnerOwnership" as MessageKey)}
              <input className="otc-input" type="number" min="0" max="100" step="0.01" value={form.beneficialOwnerOwnershipPct} onChange={(event) => updateForm("beneficialOwnerOwnershipPct", event.target.value)} />
            </label>
          </div>

          <label className="otc-field">
            {tr("counterparties.form.declaredRiskContext" as MessageKey)}
            <textarea className="otc-textarea" rows={4} value={form.declaredRiskContext} onChange={(event) => updateForm("declaredRiskContext", event.target.value)} />
          </label>

          <div className="otc-controls">
            <button className="otc-button otc-button--accent" type="submit" data-testid="create-counterparty-btn" disabled={submitting}>
              {submitting ? tr("counterparties.form.submitting" as MessageKey) : tr("counterparties.form.submit" as MessageKey)}
            </button>
          </div>

          {error ? <Message tone="error">{error}</Message> : null}
          {notice ? <Message tone="success">{notice}</Message> : null}
        </form>
      </Panel>

      <Panel title={tr("counterparties.workspace.title" as MessageKey)} description={tr("counterparties.workspace.description" as MessageKey)}>
        <div className="otc-controls">
          <label className="otc-field">
            {tr("counterparties.workspace.filterStatus" as MessageKey)}
            <select className="otc-select" value={workspaceFilter} onChange={(event) => setWorkspaceFilter(event.target.value)}>
              <option value="all">{tr("counterparties.workspace.all" as MessageKey)}</option>
              <option value="UNDER_REVIEW">{tr("counterparties.workspace.status.under_review" as MessageKey)}</option>
              <option value="ESCALATED">{tr("counterparties.workspace.status.escalated" as MessageKey)}</option>
              <option value="CLOSED">{tr("counterparties.workspace.status.closed" as MessageKey)}</option>
            </select>
          </label>
          <label className="otc-field">
            {tr("counterparties.workspace.search" as MessageKey)}
            <input className="otc-input" value={workspaceSearch} onChange={(event) => setWorkspaceSearch(event.target.value)} />
          </label>
        </div>

        {workspaceRecords.filter((record) => {
          const matchesStatus = workspaceFilter === "all" ? true : record.workspaceStatus === workspaceFilter;
          const search = workspaceSearch.trim().toLowerCase();
          const matchesSearch =
            !search ||
            record.legalName.toLowerCase().includes(search) ||
            record.documentNumber.toLowerCase().includes(search) ||
            record.caseId.toLowerCase().includes(search) ||
            record.owner.toLowerCase().includes(search);
          return matchesStatus && matchesSearch;
        }).length ? (
          <table className="otc-table otc-table--spaced">
            <thead>
              <tr>
                <th>{tr("counterparties.workspace.legalName" as MessageKey)}</th>
                <th>{tr("counterparties.workspace.document" as MessageKey)}</th>
                <th>{tr("counterparties.workspace.owner" as MessageKey)}</th>
                <th>{tr("counterparties.workspace.priority" as MessageKey)}</th>
                <th>{tr("counterparties.workspace.deadline" as MessageKey)}</th>
                <th>{tr("counterparties.workspace.urgency" as MessageKey)}</th>
                <th>{tr("counterparties.workspace.status" as MessageKey)}</th>
                <th>{tr("counterparties.workspace.actions" as MessageKey)}</th>
              </tr>
            </thead>
            <tbody>
              {workspaceRecords
                .filter((record) => {
                  const matchesStatus = workspaceFilter === "all" ? true : record.workspaceStatus === workspaceFilter;
                  const search = workspaceSearch.trim().toLowerCase();
                  const matchesSearch =
                    !search ||
                    record.legalName.toLowerCase().includes(search) ||
                    record.documentNumber.toLowerCase().includes(search) ||
                    record.caseId.toLowerCase().includes(search) ||
                    record.owner.toLowerCase().includes(search);
                  return matchesStatus && matchesSearch;
                })
                .map((record) => {
                  const urgency = getUrgency(record);
                  const caseHref = buildCaseHref(record.caseId);
                  const auditHref = buildAuditHref(record.caseId, record.caseId || record.counterpartyId, record.counterpartyId);
                  const evidenceHref = buildEvidenceHref(record.caseId || record.counterpartyId, record.caseId, record.counterpartyId);
                  const sanctionsHref = buildSanctionsHref(record);
                  const isTimelineSelected = timelineCounterpartyId === record.counterpartyId;
                  return (
                    <tr key={record.counterpartyId} className={isTimelineSelected ? "otc-row-selected" : undefined}>
                      <td>
                        <strong>{record.legalName}</strong>
                        <div className="otc-muted">{tr(`counterparties.types.${record.counterpartyType}` as MessageKey)}</div>
                        <div className="otc-muted">
                          <Pill tone={record.source === "server" ? "success" : "warning"}>
                            {tr(`counterparties.workspace.source.${record.source}` as MessageKey)}
                          </Pill>
                        </div>
                      </td>
                      <td>{record.documentType} - {record.documentNumber}</td>
                      <td>
                        <input
                          className="otc-input"
                          value={record.owner}
                          onChange={(event) => updateWorkspaceField(record.counterpartyId, "owner", event.target.value)}
                          onBlur={() => {
                            void syncRecordById(record.counterpartyId).catch((syncError) => {
                              setError(syncError instanceof Error ? syncError.message : tr("counterparties.workspace.errorSync" as MessageKey));
                              setNotice(tr("counterparties.workspace.noticeUpdatedLocalOnly" as MessageKey));
                            });
                          }}
                          aria-label={tr("counterparties.workspace.owner" as MessageKey)}
                        />
                      </td>
                      <td>
                        <select
                          className="otc-select"
                          value={record.priority}
                          onChange={(event) => {
                            const nextPriority = event.target.value as WorkspacePriority;
                            updateWorkspaceField(record.counterpartyId, "priority", nextPriority);
                            const currentRecord = workspaceById.get(record.counterpartyId);
                            if (!currentRecord) {
                              return;
                            }
                            void syncWorkspaceRecord({ ...currentRecord, priority: nextPriority, lastActionAt: new Date().toISOString() }).catch((syncError) => {
                              setError(syncError instanceof Error ? syncError.message : tr("counterparties.workspace.errorSync" as MessageKey));
                              setNotice(tr("counterparties.workspace.noticeUpdatedLocalOnly" as MessageKey));
                            });
                          }}
                          aria-label={tr("counterparties.workspace.priority" as MessageKey)}
                        >
                          <option value="critical">{tr("counterparties.priority.critical" as MessageKey)}</option>
                          <option value="high">{tr("counterparties.priority.high" as MessageKey)}</option>
                          <option value="normal">{tr("counterparties.priority.normal" as MessageKey)}</option>
                        </select>
                      </td>
                      <td>
                        <input
                          className="otc-input"
                          type="datetime-local"
                          value={record.localDeadline}
                          onChange={(event) => {
                            const nextDeadline = event.target.value;
                            updateWorkspaceField(record.counterpartyId, "localDeadline", nextDeadline);
                            const currentRecord = workspaceById.get(record.counterpartyId);
                            if (!currentRecord) {
                              return;
                            }
                            void syncWorkspaceRecord({ ...currentRecord, localDeadline: nextDeadline, lastActionAt: new Date().toISOString() }).catch((syncError) => {
                              setError(syncError instanceof Error ? syncError.message : tr("counterparties.workspace.errorSync" as MessageKey));
                              setNotice(tr("counterparties.workspace.noticeUpdatedLocalOnly" as MessageKey));
                            });
                          }}
                          aria-label={tr("counterparties.workspace.deadline" as MessageKey)}
                        />
                      </td>
                      <td>
                        <Pill tone={toneForUrgency(urgency)}>{tr(`counterparties.urgency.${urgency}` as MessageKey)}</Pill>
                      </td>
                      <td>
                        <Pill tone={toneForWorkspaceStatus(record.workspaceStatus)}>{tr(`counterparties.workspace.status.${record.workspaceStatus.toLowerCase()}` as MessageKey)}</Pill>
                      </td>
                      <td>
                        <div className="otc-controls">
                          {caseHref ? (
                            <a className="otc-button otc-button--ghost" href={caseHref}>
                              {tr("counterparties.actions.openCase" as MessageKey)}
                            </a>
                          ) : null}
                          <a className="otc-button otc-button--ghost" href={auditHref}>
                            {tr("counterparties.actions.openAudit" as MessageKey)}
                          </a>
                          <a className="otc-button otc-button--ghost" href={evidenceHref}>
                            {tr("counterparties.actions.openEvidence" as MessageKey)}
                          </a>
                          <a className="otc-button otc-button--ghost" href={sanctionsHref}>
                            {tr("counterparties.actions.openSanctions" as MessageKey)}
                          </a>
                          <button type="button" className="otc-button otc-button--ghost" onClick={() => hydrateWorkspaceRecord(record)}>
                            {tr("counterparties.workspace.load" as MessageKey)}
                          </button>
                          <button type="button" className="otc-button otc-button--ghost" onClick={() => setTimelineCounterpartyId(record.counterpartyId)}>
                            {tr("counterparties.workspace.timeline.open" as MessageKey)}
                          </button>
                          <button type="button" className="otc-button otc-button--ghost" onClick={() => updateWorkspaceStatus(record.counterpartyId, "UNDER_REVIEW")}>
                            {tr("counterparties.workspace.markUnderReview" as MessageKey)}
                          </button>
                          <button type="button" className="otc-button otc-button--ghost" onClick={() => updateWorkspaceStatus(record.counterpartyId, "ESCALATED")}>
                            {tr("counterparties.workspace.markEscalated" as MessageKey)}
                          </button>
                          <button type="button" className="otc-button otc-button--ghost" onClick={() => updateWorkspaceStatus(record.counterpartyId, "CLOSED")}>
                            {tr("counterparties.workspace.markClosed" as MessageKey)}
                          </button>
                          {record.source === "local" ? (
                            <button type="button" className="otc-button otc-button--ghost" onClick={() => removeWorkspaceRecord(record.counterpartyId)}>
                              {tr("counterparties.workspace.remove" as MessageKey)}
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
          <Message>{tr("counterparties.workspace.empty" as MessageKey)}</Message>
        )}

        {workspaceRecords.length ? (
          <div className="otc-grid otc-grid--counterparty-form">
            <label className="otc-field">
              {tr("counterparties.workspace.noteFor" as MessageKey)}
              <select className="otc-select" value={workspaceNoteId} onChange={(event) => setWorkspaceNoteId(event.target.value)}>
                {workspaceRecords.map((record) => (
                  <option key={record.counterpartyId} value={record.counterpartyId}>
                    {record.legalName}
                  </option>
                ))}
              </select>
            </label>
            <label className="otc-field">
              {tr("counterparties.workspace.note" as MessageKey)}
              <textarea
                className="otc-textarea"
                rows={3}
                value={workspaceRecords.find((record) => record.counterpartyId === workspaceNoteId)?.note ?? ""}
                placeholder={tr("counterparties.workspace.notePlaceholder" as MessageKey)}
                onChange={(event) => updateWorkspaceField(workspaceNoteId, "note", event.target.value)}
                onBlur={() => {
                  void syncRecordById(workspaceNoteId).catch((syncError) => {
                    setError(syncError instanceof Error ? syncError.message : tr("counterparties.workspace.errorSync" as MessageKey));
                    setNotice(tr("counterparties.workspace.noticeUpdatedLocalOnly" as MessageKey));
                  });
                }}
              />
            </label>
          </div>
        ) : null}

        {workspaceRecords.length ? (
          <div className="otc-stack">
            <strong>{tr("counterparties.workspace.ddReview.title" as MessageKey)}</strong>
            <p className="otc-muted">{tr("counterparties.workspace.ddReview.description" as MessageKey)}</p>
            <label className="otc-field">
              {tr("counterparties.workspace.ddReview.selectCounterparty" as MessageKey)}
              <select className="otc-select" value={ddReviewCounterpartyId || workspaceRecords[0]?.counterpartyId} onChange={(event) => setDdReviewCounterpartyId(event.target.value)}>
                {workspaceRecords.map((record) => (
                  <option key={record.counterpartyId} value={record.counterpartyId}>
                    {record.legalName || record.counterpartyId}
                  </option>
                ))}
              </select>
            </label>
            {(() => {
              const ddId = ddReviewCounterpartyId || workspaceRecords[0]?.counterpartyId;
              const ddRecord = workspaceById.get(ddId);
              if (!ddRecord) return null;
              return (
                <div className="otc-grid otc-grid--counterparty-form">
                  <label className="otc-field">
                    {tr("counterparties.workspace.ddReview.status" as MessageKey)}
                    <select
                      className="otc-select"
                      value={ddRecord.ddReviewStatus}
                      onChange={(event) => {
                        const nextStatus = event.target.value as DdReviewStatus;
                        updateWorkspaceField(ddId, "ddReviewStatus", nextStatus);
                        void syncRecordById(ddId).catch((syncError) => {
                          setError(syncError instanceof Error ? syncError.message : tr("counterparties.workspace.errorSync" as MessageKey));
                        });
                      }}
                    >
                      <option value="pending">{tr("counterparties.workspace.ddReview.statusPending" as MessageKey)}</option>
                      <option value="in_progress">{tr("counterparties.workspace.ddReview.statusInProgress" as MessageKey)}</option>
                      <option value="completed">{tr("counterparties.workspace.ddReview.statusCompleted" as MessageKey)}</option>
                      <option value="escalated">{tr("counterparties.workspace.ddReview.statusEscalated" as MessageKey)}</option>
                    </select>
                  </label>
                  <label className="otc-field">
                    {tr("counterparties.workspace.ddReview.sofDocumentRef" as MessageKey)}
                    <input
                      className="otc-input"
                      value={ddRecord.sofDocumentRef}
                      placeholder={tr("counterparties.workspace.ddReview.sofDocumentRefPlaceholder" as MessageKey)}
                      onChange={(event) => updateWorkspaceField(ddId, "sofDocumentRef", event.target.value)}
                      onBlur={() => void syncRecordById(ddId).catch(() => undefined)}
                    />
                  </label>
                  <label className="otc-field otc-field--span2">
                    {tr("counterparties.workspace.ddReview.sofDescription" as MessageKey)}
                    <textarea
                      className="otc-textarea"
                      rows={3}
                      value={ddRecord.sofDescription}
                      placeholder={tr("counterparties.workspace.ddReview.sofDescriptionPlaceholder" as MessageKey)}
                      onChange={(event) => updateWorkspaceField(ddId, "sofDescription", event.target.value)}
                      onBlur={() => void syncRecordById(ddId).catch(() => undefined)}
                    />
                  </label>
                  <label className="otc-field otc-field--span2">
                    {tr("counterparties.workspace.ddReview.note" as MessageKey)}
                    <textarea
                      className="otc-textarea"
                      rows={3}
                      value={ddRecord.ddReviewNote}
                      placeholder={tr("counterparties.workspace.ddReview.notePlaceholder" as MessageKey)}
                      onChange={(event) => updateWorkspaceField(ddId, "ddReviewNote", event.target.value)}
                      onBlur={() => void syncRecordById(ddId).catch(() => undefined)}
                    />
                  </label>
                </div>
              );
            })()}
          </div>
        ) : null}

        <WorkItemTimelinePanel
          state={!selectedTimelineRecord ? "empty_selection" : !selectedTimelineRecord.workItemId ? "local_only" : "ready"}
          summary={
            selectedTimelineRecord
              ? tr("counterparties.workspace.timeline.summary" as MessageKey, {
                  name: selectedTimelineRecord.legalName || selectedTimelineRecord.counterpartyId
                })
              : null
          }
          labels={buildWorkItemTimelineLabels(tr, "counterparties.workspace.timeline")}
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
      </Panel>

      <Panel
        title={tr("counterparties.list.title" as MessageKey)}
        description={tr("counterparties.list.description" as MessageKey)}
        actions={
          <div className="otc-controls">
            <button className="otc-button" type="button" onClick={() => loadCounterparties(offset)} disabled={loading}>
              {t("monitoring.actions.refresh")}
            </button>
          </div>
        }
      >
        <div className="otc-message otc-panel-summary">
          {tr("counterparties.list.total" as MessageKey, { total, page: currentPage, pages: totalPages })}
        </div>
        <table className="otc-table otc-table--spaced">
          <thead>
            <tr>
              <th>{tr("counterparties.list.legalName" as MessageKey)}</th>
              <th>{tr("counterparties.list.type" as MessageKey)}</th>
              <th>{tr("counterparties.list.document" as MessageKey)}</th>
              <th>{tr("counterparties.list.risk" as MessageKey)}</th>
              <th>{tr("counterparties.list.kyc" as MessageKey)}</th>
              <th>{tr("counterparties.list.sanctions" as MessageKey)}</th>
              <th>{tr("counterparties.list.pep" as MessageKey)}</th>
              <th>{tr("counterparties.list.review" as MessageKey)}</th>
              <th>{tr("counterparties.list.status" as MessageKey)}</th>
              <th>{tr("counterparties.list.createdAt" as MessageKey)}</th>
              <th>{tr("counterparties.list.actions" as MessageKey)}</th>
            </tr>
          </thead>
          <tbody>
            {items.length ? (
              items.map((item) => {
                const trackedRecord = workspaceById.get(item.id);
                const caseHref = trackedRecord ? buildCaseHref(trackedRecord.caseId) : null;
                const auditHref = trackedRecord
                  ? buildAuditHref(trackedRecord.caseId, trackedRecord.caseId || trackedRecord.counterpartyId, trackedRecord.counterpartyId)
                  : null;
                const evidenceHref = trackedRecord
                  ? buildEvidenceHref(trackedRecord.caseId || trackedRecord.counterpartyId, trackedRecord.caseId, trackedRecord.counterpartyId)
                  : null;
                const sanctionsHref = trackedRecord ? buildSanctionsHref(trackedRecord) : null;

                return (
                  <tr key={item.id}>
                    <td>
                      <strong>{item.legal_name}</strong>
                    </td>
                    <td>{tr(`counterparties.types.${item.counterparty_type}` as MessageKey)}</td>
                    <td>{item.document_type} - {item.document_number}</td>
                    <td>
                      <Pill tone={riskTone(item.risk_level)}>{String(item.risk_level)}</Pill>
                    </td>
                    <td>{item.kyc_status}</td>
                    <td>{item.sanctions_cleared ? tr("counterparties.list.yes" as MessageKey) : tr("counterparties.list.no" as MessageKey)}</td>
                    <td>{item.is_pep ? tr("counterparties.list.yes" as MessageKey) : tr("counterparties.list.no" as MessageKey)}</td>
                    <td>{item.next_review_date ?? t("common.notAvailable")}</td>
                    <td>{item.status}</td>
                    <td>{formatDate(item.created_at) ?? t("common.notAvailable")}</td>
                    <td>
                      <div className="otc-controls">
                        <button type="button" className="otc-button otc-button--ghost" onClick={() => trackFromList(item)} disabled={syncingWorkspace}>
                          {tr("counterparties.list.track" as MessageKey)}
                        </button>
                        {caseHref ? (
                          <a className="otc-button otc-button--ghost" href={caseHref}>
                            {tr("counterparties.actions.openCase" as MessageKey)}
                          </a>
                        ) : null}
                        {auditHref ? (
                          <a className="otc-button otc-button--ghost" href={auditHref}>
                            {tr("counterparties.actions.openAudit" as MessageKey)}
                          </a>
                        ) : null}
                        {evidenceHref ? (
                          <a className="otc-button otc-button--ghost" href={evidenceHref}>
                            {tr("counterparties.actions.openEvidence" as MessageKey)}
                          </a>
                        ) : null}
                        {sanctionsHref ? (
                          <a className="otc-button otc-button--ghost" href={sanctionsHref}>
                            {tr("counterparties.actions.openSanctions" as MessageKey)}
                          </a>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={11} className="otc-muted">
                  {loading ? t("common.loading") : tr("counterparties.list.empty" as MessageKey)}
                </td>
              </tr>
            )}
          </tbody>
        </table>
        <div className="otc-controls otc-controls--spaced">
          <button className="otc-button" type="button" onClick={() => loadCounterparties(Math.max(0, offset - DEFAULT_LIMIT))} disabled={loading || offset === 0}>
            {tr("counterparties.list.previous" as MessageKey)}
          </button>
          <button className="otc-button" type="button" onClick={() => loadCounterparties(offset + DEFAULT_LIMIT)} disabled={loading || offset + DEFAULT_LIMIT >= total}>
            {tr("counterparties.list.next" as MessageKey)}
          </button>
        </div>
      </Panel>
    </AppShell>
  );
}

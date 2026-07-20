"use client";

import { useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { AppShell, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import { formatDateTime as formatDate } from "../lib/date-format";
import { useI18n } from "../../components/i18n-provider";
import { WorkItemTimelinePanel } from "../../components/work-item-timeline-panel";
import { canCreateCounterparty, canReadCounterparty, canReviewCounterparty } from "../lib/authz";
import { fetchAuthContext, resolveOwnerUserId, type AuthContext } from "../lib/ownership";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { buildWorkItemTimelineLabels } from "../lib/work-item-timeline-labels";
import { useWorkItemTimeline } from "../lib/use-work-item-timeline";
import {
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
  readWorkItemMetadataBoolean,
  readWorkItemMetadataNumber,
  readWorkItemMetadataString,
  resolveWorkItemOwnerDisplay,
  resolveWorkItemWorkspaceStatus,
  isWorkItemUuidLike as isUuidLike,
  type CounterpartyWorkItemMetadata,
  type CreateWorkItemRequest,
  type PatchWorkItemRequest,
  type WorkItemListResponse,
  type WorkItemPriority,
  type WorkItemQueueStatus,
  type WorkItemResponse,
  withCanonicalWorkItemMetadata
} from "../lib/work-items";
import type { MessageKey } from "../lib/i18n";
import { formatTimelineEvent } from "../lib/work-item-timeline";

type WorkspacePriority = WorkItemPriority;
type WorkspaceStatus = "UNDER_REVIEW" | "ESCALATED" | "CLOSED";
type WorkspaceSource = "server" | "local";
type CounterpartyWorkItemResponse = WorkItemResponse<CounterpartyWorkItemMetadata>;
type CounterpartyWorkItemListResponse = WorkItemListResponse<CounterpartyWorkItemMetadata>;

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
  dd_review_status?: string;
  dd_review_note?: string;
  sof_description?: string;
  sof_document_ref?: string;
  last_reviewed_at?: string | null;
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

type CounterpartyReviewResponse = {
  counterparty_id: string;
  dd_review_status: string;
  dd_review_note: string;
  sof_description: string;
  sof_document_ref: string;
  last_reviewed_at?: string | null;
};

type CounterpartyDetailResponse = {
  counterparty_id: string;
  legal_name: string;
  counterparty_type: string;
  document_type: string;
  document_number: string;
  document_country: string;
  registration_data: Record<string, string>;
  beneficial_owners: Array<{ name: string; document: string; ownership_pct: number | null }>;
  wallet_addresses: Array<{ chain: string; address: string; label: string }>;
  risk_level: number;
  risk_rationale: string;
  onchain_risk_score?: number | null;
  onchain_analysis: Record<string, unknown>;
  is_pep: boolean;
  pep_detail: Record<string, unknown>;
  sanctions_cleared: boolean;
  sanctions_hits: Array<Record<string, unknown>>;
  kyc_status: string;
  enhanced_dd_required: boolean;
  next_review_date?: string | null;
  status: string;
  created_at: string;
  review_snapshot: {
    dd_review_status: string;
    dd_review_note: string;
    sof_description: string;
    sof_document_ref: string;
    last_reviewed_at?: string | null;
  };
};

type CounterpartyHistoryItem = {
  id: string;
  counterparty_id: string;
  changed_by_user_id: string;
  change_type: string;
  field_changed?: string | null;
  old_value?: string | null;
  new_value?: string | null;
  change_reason?: string | null;
  changed_at: string;
  evidence_hash: string;
};

type CounterpartyHistoryResponse = {
  items: CounterpartyHistoryItem[];
  total: number;
  limit: number;
  offset: number;
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

function normalizeWorkspaceStatus(value: unknown): WorkspaceStatus {
  if (value === "UNDER_REVIEW" || value === "ESCALATED" || value === "CLOSED") {
    return value;
  }
  return "UNDER_REVIEW";
}

function normalizeDdReviewStatus(value: unknown): DdReviewStatus {
  return value === "in_progress" || value === "completed" || value === "escalated" ? value : "pending";
}

function getCounterpartyDomainReviewFields(item: Partial<CounterpartyListItem>) {
  return {
    ddReviewStatus: normalizeDdReviewStatus(item.dd_review_status),
    ddReviewNote: typeof item.dd_review_note === "string" ? item.dd_review_note : "",
    sofDescription: typeof item.sof_description === "string" ? item.sof_description : "",
    sofDocumentRef: typeof item.sof_document_ref === "string" ? item.sof_document_ref : ""
  };
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

function buildCounterpartyOperationalContext(record: {
  caseId?: string | null;
  counterpartyId: string;
  walletAddress?: string | null;
  walletChain?: string | null;
}): OperationalContext {
  const caseId = record.caseId?.trim() ?? "";
  const counterpartyId = record.counterpartyId.trim();
  return {
    caseId,
    requestId: caseId,
    reportId: counterpartyId,
    fileHash: "",
    resourceType: "case",
    resourceId: caseId || counterpartyId,
    address: record.walletAddress?.trim() ?? "",
    chain: record.walletChain?.trim() || "ethereum",
    counterpartyId,
    legalName: "",
    documentNumber: "",
    rosId: "",
    reportType: "",
    blockId: ""
  };
}

function buildCounterpartyContextLinks(
  context: OperationalContext,
  labelKeyByKind: Partial<Record<OperationalContextLink["kind"], MessageKey>>
) {
  return buildOperationalContextLinks(context, {
    includeEvidence: true,
    evidenceDomain: "compliance",
    auditFallbackResourceType: "case",
    auditResourceIdOverride: context.caseId || context.counterpartyId,
    evidenceResourceIdOverride: context.caseId || context.counterpartyId
  })
    .filter((link: OperationalContextLink) => link.kind === "case" || link.kind === "audit" || link.kind === "evidence")
    .map((link: OperationalContextLink) => ({
      ...link,
      labelKey: labelKeyByKind[link.kind] ?? "counterparties.actions.openAudit"
    }));
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

function saveWorkspace(records: CounterpartyWorkspaceRecord[]) {
  saveWorkspaceRecords(STORAGE_KEY, records);
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

  return sortByLastActionAtDesc([merged, ...current.filter((record) => record.counterpartyId !== next.counterpartyId)]);
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

  return sortByLastActionAtDesc(merged);
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

function mapWorkItemToWorkspaceRecord(item: CounterpartyWorkItemResponse): CounterpartyWorkspaceRecord {
  const metadata = item.metadata ?? {};
  const counterpartyId = readWorkItemMetadataString(metadata, "counterparty_id") || item.resource_id;
  return {
    workItemId: item.id,
    source: "server",
    counterpartyId,
    legalName: readWorkItemMetadataString(metadata, "legal_name"),
    counterpartyType: readWorkItemMetadataString(metadata, "counterparty_type"),
    documentType: readWorkItemMetadataString(metadata, "document_type"),
    documentNumber: readWorkItemMetadataString(metadata, "document_number"),
    walletChain: readWorkItemMetadataString(metadata, "wallet_chain"),
    walletAddress: readWorkItemMetadataString(metadata, "wallet_address"),
    walletLabel: readWorkItemMetadataString(metadata, "wallet_label"),
    riskLevel: readWorkItemMetadataNumber(metadata, "risk_level") ?? 0,
    kycStatus: readWorkItemMetadataString(metadata, "kyc_status"),
    sanctionsCleared: readWorkItemMetadataBoolean(metadata, "sanctions_cleared") === true,
    isPep: readWorkItemMetadataBoolean(metadata, "is_pep") === true,
    enhancedDdRequired: readWorkItemMetadataBoolean(metadata, "enhanced_dd_required") === true,
    nextReviewDate: readWorkItemMetadataString(metadata, "next_review_date"),
    status: readWorkItemMetadataString(metadata, "status"),
    createdAt: readWorkItemMetadataString(metadata, "created_at"),
    caseId: item.case_id ?? readWorkItemMetadataString(metadata, "case_id"),
    owner: resolveWorkItemOwnerDisplay(metadata, item.owner_user_id),
    priority: item.priority,
    localDeadline: toDateTimeLocalValue(item.due_at),
    workspaceStatus: normalizeWorkspaceStatus(resolveWorkItemWorkspaceStatus(metadata, "counterparty")) || mapQueueStatusToWorkspaceStatus(item.queue_status),
    note: item.note ?? readWorkItemMetadataString(metadata, "note"),
    ddReviewStatus: (readWorkItemMetadataString(metadata, "dd_review_status") || "pending") as DdReviewStatus,
    ddReviewNote: readWorkItemMetadataString(metadata, "dd_review_note"),
    sofDescription: readWorkItemMetadataString(metadata, "sof_description"),
    sofDocumentRef: readWorkItemMetadataString(metadata, "sof_document_ref"),
    lastActionAt: item.last_activity_at || item.updated_at
  };
}

function mergeDomainReviewIntoWorkspace(
  current: CounterpartyWorkspaceRecord[],
  items: CounterpartyListItem[]
): CounterpartyWorkspaceRecord[] {
  if (!items.length || !current.length) {
    return current;
  }

  const byId = new Map(items.map((item) => [item.id, item]));
  return current.map((record) => {
    const domainItem = byId.get(record.counterpartyId);
    if (!domainItem) {
      return record;
    }

    return {
      ...record,
      ...getCounterpartyDomainReviewFields(domainItem)
    };
  });
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

function toneForWorkspaceSource(source: WorkspaceSource): "success" | "warning" {
  return source === "server" ? "success" : "warning";
}

function getDdReviewStatusLabelKey(status: DdReviewStatus): MessageKey {
  switch (status) {
    case "in_progress":
      return "counterparties.workspace.ddReview.statusInProgress";
    case "completed":
      return "counterparties.workspace.ddReview.statusCompleted";
    case "escalated":
      return "counterparties.workspace.ddReview.statusEscalated";
    default:
      return "counterparties.workspace.ddReview.statusPending";
  }
}

export default function CounterpartiesPage() {
  const searchParams = useSearchParams();
  const { locale, t } = useI18n();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);
  const [items, setItems] = useState<CounterpartyListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [syncingWorkspace, setSyncingWorkspace] = useState(false);
  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [authResolved, setAuthResolved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [form, setForm] = useState<CounterpartyFormState>(DEFAULT_FORM);
  const [workspaceRecords, setWorkspaceRecords] = useState<CounterpartyWorkspaceRecord[]>([]);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [ddReviewCounterpartyId, setDdReviewCounterpartyId] = useState<string>("");
  const [workspaceFilter, setWorkspaceFilter] = useState("all");
  const [workspaceSearch, setWorkspaceSearch] = useState("");
  const [workspaceNoteId, setWorkspaceNoteId] = useState<string>("");
  const [timelineCounterpartyId, setTimelineCounterpartyId] = useState<string>("");
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [counterpartyDetail, setCounterpartyDetail] = useState<CounterpartyDetailResponse | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [counterpartyHistory, setCounterpartyHistory] = useState<CounterpartyHistoryItem[]>([]);
  const canReadCounterpartyData = authResolved ? canReadCounterparty(authContext?.role) : null;
  const canCreateCounterpartyRecord = canCreateCounterparty(authContext?.role);
  const canEditCounterpartyReview = canReviewCounterparty(authContext?.role);
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
  } = useWorkItemTimeline<CounterpartyWorkItemResponse>({
    resolveErrorMessage: (apiError, fallback) => resolveApiErrorMessage(t, apiError, fallback),
    loadErrorMessage: tr("counterparties.workspace.timeline.errorLoad" as MessageKey),
    commentErrorMessage: tr("counterparties.workspace.timeline.errorComment" as MessageKey),
    emptySelectionErrorMessage: tr("counterparties.workspace.timeline.emptyLocal" as MessageKey),
    emptyCommentErrorMessage: tr("counterparties.workspace.timeline.commentEmpty" as MessageKey),
    onCommentSaved: () => {
      setNotice(tr("counterparties.workspace.timeline.commentSaved" as MessageKey));
    }
  });

  const highRiskCount = useMemo(() => items.filter((item: CounterpartyListItem) => item.risk_level >= 3).length, [items]);
  const pendingKycCount = useMemo(() => items.filter((item: CounterpartyListItem) => item.kyc_status !== "APPROVED").length, [items]);
  const totalPages = Math.max(1, Math.ceil(total / DEFAULT_LIMIT));
  const currentPage = Math.floor(offset / DEFAULT_LIMIT) + 1;
  const trackedCount = useMemo(() => workspaceRecords.length, [workspaceRecords]);
  const pendingReviewCount = useMemo(
    () => workspaceRecords.filter((record: CounterpartyWorkspaceRecord) => record.workspaceStatus === "UNDER_REVIEW" || record.workspaceStatus === "ESCALATED").length,
    [workspaceRecords]
  );
  const overdueCount = useMemo(() => workspaceRecords.filter((record: CounterpartyWorkspaceRecord) => getUrgency(record) === "overdue").length, [workspaceRecords]);
  const workspaceById = useMemo(
    () => new Map(workspaceRecords.map((record: CounterpartyWorkspaceRecord) => [record.counterpartyId, record])),
    [workspaceRecords]
  );
  const selectedTimelineRecord = timelineCounterpartyId ? workspaceById.get(timelineCounterpartyId) ?? null : null;
  const selectedDetailRecord = useMemo(() => {
    if (timelineCounterpartyId) {
      return workspaceById.get(timelineCounterpartyId) ?? null;
    }
    if (workspaceRecords.length) {
      return workspaceRecords[0];
    }
    return items.length ? { counterpartyId: items[0].id } : null;
  }, [items, timelineCounterpartyId, workspaceById, workspaceRecords]);
  const serverWorkspaceCount = useMemo(
    () => workspaceRecords.filter((record: CounterpartyWorkspaceRecord) => record.source === "server").length,
    [workspaceRecords]
  );
  const localWorkspaceCount = useMemo(
    () => workspaceRecords.filter((record: CounterpartyWorkspaceRecord) => record.source === "local").length,
    [workspaceRecords]
  );
  const hasMixedWorkspaceSources = serverWorkspaceCount > 0 && localWorkspaceCount > 0;
  const timelineContextBadges = selectedTimelineRecord
    ? [
        {
          label: tr(`counterparties.workspace.source.${selectedTimelineRecord.source}` as MessageKey),
          tone: toneForWorkspaceSource(selectedTimelineRecord.source) as "success" | "warning"
        },
        {
          label: tr(`counterparties.workspace.status.${selectedTimelineRecord.workspaceStatus.toLowerCase()}` as MessageKey),
          tone: (toneForWorkspaceStatus(selectedTimelineRecord.workspaceStatus) ?? "success") as "success" | "warning" | "danger"
        },
        {
          label: tr(getDdReviewStatusLabelKey(selectedTimelineRecord.ddReviewStatus)),
          tone: (
            selectedTimelineRecord.ddReviewStatus === "completed"
              ? "success"
              : selectedTimelineRecord.ddReviewStatus === "escalated"
                ? "danger"
                : "warning"
          ) as "success" | "warning" | "danger"
        }
      ]
    : [];

  async function loadOperationalWorkspace(localRecords: CounterpartyWorkspaceRecord[]) {
    if (canReadCounterpartyData !== true) {
      setWorkspaceRecords(localRecords);
      setWorkspaceError(null);
      return;
    }
    const res = await fetch(
      `/api/app/operations/work-items?module=counterparties&resource_type=counterparty&limit=${WORKSPACE_PAGE_LIMIT}`,
      { cache: "no-store" }
    );
    const data = (await res.json().catch(() => null)) as CounterpartyWorkItemListResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setWorkspaceRecords(localRecords);
      setWorkspaceError(resolveApiErrorMessage(t, data, tr("counterparties.workspace.errorSync" as MessageKey)));
      return;
    }

    const items = data && "data" in data && Array.isArray(data.data) ? data.data : [];
    const serverRecords = items.map((item) => mapWorkItemToWorkspaceRecord(item));
    setWorkspaceRecords(mergeWorkspaceRecords(serverRecords, localRecords));
    setWorkspaceError(null);
  }

  async function loadCounterparties(nextOffset = offset) {
    if (canReadCounterpartyData !== true) {
      setItems([]);
      setTotal(0);
      return;
    }
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

    const nextItems = data && "items" in data ? data.items : [];
    setItems(nextItems);
    setTotal(data && "total" in data ? data.total : 0);
    setOffset(nextOffset);
    setWorkspaceRecords((current) => mergeDomainReviewIntoWorkspace(current, nextItems));
    setLoading(false);
  }

  useEffect(() => {
    fetchAuthContext()
      .then((data) => {
        setAuthContext(data ?? null);
      })
      .catch(() => {
        setAuthContext(null);
      })
      .finally(() => setAuthResolved(true));
  }, []);

  useEffect(() => {
    if (!authResolved) {
      return;
    }
    if (canReadCounterpartyData !== true) {
      setItems([]);
      setTotal(0);
      setWorkspaceRecords([]);
      setWorkspaceError(null);
      setLoading(false);
      return;
    }
    loadCounterparties(0).catch(() => {
      setError(tr("counterparties.errorLoad" as MessageKey));
      setLoading(false);
    });
  }, [authResolved, canReadCounterpartyData, t]);

  useEffect(() => {
    if (!authResolved) {
      return;
    }
    setWorkspaceRecords([]);
    setWorkspaceError(null);
    loadOperationalWorkspace([]).catch(() => {
      setWorkspaceRecords([]);
      setWorkspaceError(tr("counterparties.workspace.errorSync" as MessageKey));
    });
  }, [authResolved, canReadCounterpartyData, t]);

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

    setForm((current: CounterpartyFormState) => ({
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
      setWorkspaceRecords((current: CounterpartyWorkspaceRecord[]) =>
        upsertWorkspaceRecord(current, {
          workItemId: current.find((record: CounterpartyWorkspaceRecord) => record.counterpartyId === counterpartyId)?.workItemId,
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
      resetTimeline();
      return;
    }
    if (!workspaceNoteId || !workspaceRecords.some((record: CounterpartyWorkspaceRecord) => record.counterpartyId === workspaceNoteId)) {
      setWorkspaceNoteId(workspaceRecords[0].counterpartyId);
    }
    if (!timelineCounterpartyId || !workspaceRecords.some((record: CounterpartyWorkspaceRecord) => record.counterpartyId === timelineCounterpartyId)) {
      const firstServerRecord = workspaceRecords.find((record: CounterpartyWorkspaceRecord) => Boolean(record.workItemId)) ?? workspaceRecords[0];
      setTimelineCounterpartyId(firstServerRecord.counterpartyId);
    }
  }, [timelineCounterpartyId, workspaceNoteId, workspaceRecords]);

  useEffect(() => {
    const currentRecord = timelineCounterpartyId ? workspaceById.get(timelineCounterpartyId) : null;
    if (!currentRecord?.workItemId) {
      resetTimeline();
      return;
    }
    void loadTimeline(currentRecord.workItemId);
  }, [loadTimeline, resetTimeline, timelineCounterpartyId, workspaceById]);

  useEffect(() => {
    if (canReadCounterpartyData !== true || !selectedDetailRecord?.counterpartyId || !isUuidLike(selectedDetailRecord.counterpartyId)) {
      setCounterpartyDetail(null);
      setDetailError(null);
      setCounterpartyHistory([]);
      setHistoryError(null);
      return;
    }

    let active = true;
    setDetailLoading(true);
    setDetailError(null);
    void fetch(`/api/app/compliance/counterparties/${encodeURIComponent(selectedDetailRecord.counterpartyId)}`, {
      cache: "no-store"
    })
      .then(async (res) => {
        const data = (await res.json().catch(() => null)) as CounterpartyDetailResponse | { error?: string; detail?: unknown } | null;
        if (!active) {
          return;
        }
        if (!res.ok) {
          setCounterpartyDetail(null);
          setDetailError(resolveApiErrorMessage(t, data, tr("counterparties.detail.errorLoad" as MessageKey)));
          return;
        }
        setCounterpartyDetail(data as CounterpartyDetailResponse);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setCounterpartyDetail(null);
        setDetailError(tr("counterparties.detail.errorLoad" as MessageKey));
      })
      .finally(() => {
        if (active) {
          setDetailLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [canReadCounterpartyData, selectedDetailRecord?.counterpartyId, t]);

  useEffect(() => {
    if (canReadCounterpartyData !== true || !selectedDetailRecord?.counterpartyId || !isUuidLike(selectedDetailRecord.counterpartyId)) {
      setCounterpartyHistory([]);
      setHistoryError(null);
      return;
    }

    let active = true;
    setHistoryLoading(true);
    setHistoryError(null);
    void fetch(`/api/app/compliance/counterparties/${encodeURIComponent(selectedDetailRecord.counterpartyId)}/history?limit=20&offset=0`, {
      cache: "no-store"
    })
      .then(async (res) => {
        const data = (await res.json().catch(() => null)) as CounterpartyHistoryResponse | { error?: string; detail?: unknown } | null;
        if (!active) {
          return;
        }
        if (!res.ok) {
          setCounterpartyHistory([]);
          setHistoryError(resolveApiErrorMessage(t, data, tr("counterparties.detail.history.errorLoad" as MessageKey)));
          return;
        }
        setCounterpartyHistory(data && "items" in data && Array.isArray(data.items) ? data.items : []);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setCounterpartyHistory([]);
        setHistoryError(tr("counterparties.detail.history.errorLoad" as MessageKey));
      })
      .finally(() => {
        if (active) {
          setHistoryLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [canReadCounterpartyData, selectedDetailRecord?.counterpartyId, t]);

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
    const metadata: CounterpartyWorkItemMetadata = withCanonicalWorkItemMetadata(
      {
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
        dd_review_status: record.ddReviewStatus,
        dd_review_note: record.ddReviewNote,
        sof_description: record.sofDescription,
        sof_document_ref: record.sofDocumentRef
      },
      {
        resourceType: "counterparty",
        caseId: record.caseId,
        ownerLabel: record.owner,
        ownerUserId,
        workspaceStatus: localStatus,
        note: record.note
      }
    );
    const requestBody: CreateWorkItemRequest<CounterpartyWorkItemMetadata> | PatchWorkItemRequest<CounterpartyWorkItemMetadata> = record.workItemId
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
    const data = (await res.json().catch(() => null)) as CounterpartyWorkItemResponse | { error?: string; detail?: unknown } | null;
    setSyncingWorkspace(false);
    if (!res.ok) {
      throw new Error(resolveApiErrorMessage(t, data, tr("counterparties.workspace.errorSync" as MessageKey)));
    }

    const nextRecord = mapWorkItemToWorkspaceRecord(data as CounterpartyWorkItemResponse);
    setWorkspaceRecords((current: CounterpartyWorkspaceRecord[]) => upsertWorkspaceRecord(current, nextRecord));
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

  async function syncCounterpartyDomainReview(record: CounterpartyWorkspaceRecord) {
    if (!isUuidLike(record.counterpartyId)) {
      throw new Error(tr("counterparties.workspace.errorSyncMissingCounterpartyId" as MessageKey));
    }
    if (!canEditCounterpartyReview) {
      throw new Error(tr("apiErrors.counterpartyReviewRoleRequired" as MessageKey));
    }

    const res = await fetch(`/api/app/compliance/counterparties/${encodeURIComponent(record.counterpartyId)}/review`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        dd_review_status: record.ddReviewStatus,
        dd_review_note: record.ddReviewNote,
        sof_description: record.sofDescription,
        sof_document_ref: record.sofDocumentRef
      }),
      cache: "no-store"
    });
    const data = (await res.json().catch(() => null)) as CounterpartyReviewResponse | { error?: string; detail?: string } | null;
    if (!res.ok) {
      throw new Error(resolveApiErrorMessage(t, data, tr("counterparties.workspace.errorSync" as MessageKey)));
    }

    if (data && "counterparty_id" in data) {
      setItems((current) =>
        current.map((item) =>
          item.id === data.counterparty_id
            ? {
                ...item,
                dd_review_status: data.dd_review_status,
                dd_review_note: data.dd_review_note,
                sof_description: data.sof_description,
                sof_document_ref: data.sof_document_ref,
                last_reviewed_at: data.last_reviewed_at ?? null
              }
            : item
        )
      );
      setWorkspaceRecords((current) =>
        upsertWorkspaceRecord(current, {
          counterpartyId: data.counterparty_id,
          ddReviewStatus: normalizeDdReviewStatus(data.dd_review_status),
          ddReviewNote: data.dd_review_note,
          sofDescription: data.sof_description,
          sofDocumentRef: data.sof_document_ref
        })
      );
    }
  }

  async function syncCounterpartyReviewById(counterpartyId: string) {
    const currentRecord = workspaceById.get(counterpartyId);
    if (!currentRecord) {
      return null;
    }

    await syncCounterpartyDomainReview(currentRecord);
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
        ddReviewStatus: workspaceById.get(item.id)?.ddReviewStatus ?? getCounterpartyDomainReviewFields(item).ddReviewStatus,
        ddReviewNote: workspaceById.get(item.id)?.ddReviewNote ?? getCounterpartyDomainReviewFields(item).ddReviewNote,
        sofDescription: workspaceById.get(item.id)?.sofDescription ?? getCounterpartyDomainReviewFields(item).sofDescription,
        sofDocumentRef: workspaceById.get(item.id)?.sofDocumentRef ?? getCounterpartyDomainReviewFields(item).sofDocumentRef,
        lastActionAt: new Date().toISOString()
      };
      setWorkspaceRecords((current: CounterpartyWorkspaceRecord[]) => upsertWorkspaceRecord(current, draftRecord));
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
    setForm((current: CounterpartyFormState) => ({
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
      setWorkspaceRecords((current: CounterpartyWorkspaceRecord[]) =>
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
    setWorkspaceRecords((current: CounterpartyWorkspaceRecord[]) => current.filter((record: CounterpartyWorkspaceRecord) => record.counterpartyId !== counterpartyId));
  }

  function updateWorkspaceField<K extends keyof CounterpartyWorkspaceRecord>(counterpartyId: string, key: K, value: CounterpartyWorkspaceRecord[K]) {
    setWorkspaceRecords((current: CounterpartyWorkspaceRecord[]) =>
      upsertWorkspaceRecord(current, {
        counterpartyId,
        [key]: value,
        lastActionAt: new Date().toISOString()
      })
    );
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canCreateCounterpartyRecord) {
      setError(tr("apiErrors.counterpartyCreateRoleRequired" as MessageKey));
      return;
    }

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
        {canCreateCounterpartyRecord ? (
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
        ) : (
          <Message>{tr("counterparties.form.restricted" as MessageKey)}</Message>
        )}
      </Panel>

      <Panel title={tr("counterparties.workspace.title" as MessageKey)} description={tr("counterparties.workspace.description" as MessageKey)}>
        {canReadCounterpartyData === false ? (
          <Message data-testid="counterparties-workspace-read-restricted">
            {tr("counterparties.workspace.restricted" as MessageKey)}
          </Message>
        ) : workspaceError ? (
          <Message tone="error" data-testid="counterparties-workspace-message">
            {workspaceError}
          </Message>
        ) : localWorkspaceCount > 0 && serverWorkspaceCount === 0 ? (
          <Message>{tr("counterparties.workspace.mode.localOnly" as MessageKey, { count: localWorkspaceCount })}</Message>
        ) : null}
        {canReadCounterpartyData !== false && hasMixedWorkspaceSources ? (
          <Message>
            {tr("counterparties.workspace.mode.mixed" as MessageKey, {
              server: serverWorkspaceCount,
              local: localWorkspaceCount
            })}
          </Message>
        ) : null}
        {canReadCounterpartyData !== false ? (
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
        ) : null}

        {canReadCounterpartyData === false ? null : workspaceRecords.filter((record) => {
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
                <th>{tr("counterparties.workspace.review" as MessageKey)}</th>
                <th>{tr("counterparties.workspace.status" as MessageKey)}</th>
                <th>{tr("counterparties.workspace.sourceLabel" as MessageKey)}</th>
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
                  const contextLinks = buildCounterpartyContextLinks(
                    buildCounterpartyOperationalContext({
                      caseId: record.caseId,
                      counterpartyId: record.counterpartyId,
                      walletAddress: record.walletAddress,
                      walletChain: record.walletChain
                    }),
                    {
                      case: "counterparties.actions.openCase",
                      audit: "counterparties.actions.openAudit",
                      evidence: "counterparties.actions.openEvidence"
                    }
                  );
                  const sanctionsHref = buildSanctionsHref(record);
                  const isTimelineSelected = timelineCounterpartyId === record.counterpartyId;
                  return (
                    <tr
                      key={record.counterpartyId}
                      data-testid={`counterparties-workspace-row-${record.counterpartyId}`}
                      className={isTimelineSelected ? "otc-row-selected" : undefined}
                    >
                      <td>
                        <strong>{record.legalName}</strong>
                        <div className="otc-muted">{tr(`counterparties.types.${record.counterpartyType}` as MessageKey)}</div>
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
                      <td data-testid={`counterparties-workspace-deadline-${record.counterpartyId}`}>
                        <input
                          className="otc-input"
                          type="datetime-local"
                          data-testid={`counterparties-workspace-deadline-input-${record.counterpartyId}`}
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
                      <td data-testid={`counterparties-workspace-review-${record.counterpartyId}`}>
                        <Pill
                          tone={
                            record.ddReviewStatus === "completed"
                              ? "success"
                              : record.ddReviewStatus === "escalated"
                                ? "danger"
                                : "warning"
                          }
                        >
                          {tr(getDdReviewStatusLabelKey(record.ddReviewStatus))}
                        </Pill>
                      </td>
                      <td data-testid={`counterparties-workspace-status-${record.counterpartyId}`}>
                        <Pill tone={toneForWorkspaceStatus(record.workspaceStatus)}>{tr(`counterparties.workspace.status.${record.workspaceStatus.toLowerCase()}` as MessageKey)}</Pill>
                      </td>
                      <td data-testid={`counterparties-workspace-source-${record.counterpartyId}`}>
                        <Pill tone={toneForWorkspaceSource(record.source)}>
                          {tr(`counterparties.workspace.source.${record.source}` as MessageKey)}
                        </Pill>
                      </td>
                      <td>
                        <div className="otc-controls">
                          {contextLinks.map((link: OperationalContextLink & { labelKey: MessageKey }) => (
                            <a key={`workspace-${record.counterpartyId}-${link.testIdSuffix}`} className="otc-button otc-button--ghost" href={link.href}>
                              {tr(link.labelKey)}
                            </a>
                          ))}
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
        ) : workspaceError ? null : (
          <Message>{tr("counterparties.workspace.empty" as MessageKey)}</Message>
        )}

        {canReadCounterpartyData !== false && workspaceRecords.length ? (
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

        {canReadCounterpartyData !== false && workspaceRecords.length && canEditCounterpartyReview ? (
          <div className="otc-stack" data-testid="counterparty-dd-review-panel">
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
                        void syncCounterpartyReviewById(ddId).catch((syncError) => {
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
                      onBlur={() => void syncCounterpartyReviewById(ddId).catch(() => undefined)}
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
                      onBlur={() => void syncCounterpartyReviewById(ddId).catch(() => undefined)}
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
                      onBlur={() => void syncCounterpartyReviewById(ddId).catch(() => undefined)}
                    />
                  </label>
                </div>
              );
            })()}
          </div>
        ) : canReadCounterpartyData !== false && workspaceRecords.length ? (
          <Message>{tr("counterparties.workspace.ddReview.restricted" as MessageKey)}</Message>
        ) : null}

        {canReadCounterpartyData !== false && selectedDetailRecord ? (
          <div className="otc-stack" data-testid="counterparty-official-detail-panel">
            <strong>{tr("counterparties.detail.title" as MessageKey)}</strong>
            <p className="otc-muted">{tr("counterparties.detail.description" as MessageKey)}</p>
            {detailLoading ? (
              <Message>{tr("counterparties.detail.loading" as MessageKey)}</Message>
            ) : detailError ? (
              <Message tone="error">{detailError}</Message>
            ) : counterpartyDetail ? (
              <>
                <div className="otc-grid otc-grid--counterparty-form">
                  <div className="otc-field">
                    <strong>{tr("counterparties.list.legalName" as MessageKey)}</strong>
                    <div data-testid="counterparty-official-detail-legal-name">{counterpartyDetail.legal_name}</div>
                  </div>
                  <div className="otc-field">
                    <strong>{tr("counterparties.list.document" as MessageKey)}</strong>
                    <div>{counterpartyDetail.document_type} - {counterpartyDetail.document_number}</div>
                  </div>
                  <div className="otc-field">
                    <strong>{tr("counterparties.list.risk" as MessageKey)}</strong>
                    <div>{counterpartyDetail.risk_level}</div>
                  </div>
                  <div className="otc-field">
                    <strong>{tr("counterparties.list.kyc" as MessageKey)}</strong>
                    <div>{counterpartyDetail.kyc_status}</div>
                  </div>
                  <div className="otc-field">
                    <strong>{tr("counterparties.detail.riskRationale" as MessageKey)}</strong>
                    <div>{counterpartyDetail.risk_rationale || t("common.notAvailable")}</div>
                  </div>
                  <div className="otc-field">
                    <strong>{tr("counterparties.detail.wallets" as MessageKey)}</strong>
                    <div>
                      {counterpartyDetail.wallet_addresses.length
                        ? counterpartyDetail.wallet_addresses.map((wallet) => `${wallet.chain}:${wallet.address}`).join(" • ")
                        : t("common.notAvailable")}
                    </div>
                  </div>
                  <div className="otc-field">
                    <strong>{tr("counterparties.workspace.ddReview.status" as MessageKey)}</strong>
                    <div>{tr(getDdReviewStatusLabelKey(normalizeDdReviewStatus(counterpartyDetail.review_snapshot.dd_review_status)))}</div>
                  </div>
                  <div className="otc-field">
                    <strong>{tr("counterparties.detail.lastReviewedAt" as MessageKey)}</strong>
                    <div>{formatDate(counterpartyDetail.review_snapshot.last_reviewed_at ?? null, locale) ?? t("common.notAvailable")}</div>
                  </div>
                  <div className="otc-field">
                    <strong>{tr("counterparties.workspace.ddReview.sofDocumentRef" as MessageKey)}</strong>
                    <div>{counterpartyDetail.review_snapshot.sof_document_ref || t("common.notAvailable")}</div>
                  </div>
                </div>
                <label className="otc-field">
                  {tr("counterparties.workspace.ddReview.sofDescription" as MessageKey)}
                  <textarea className="otc-textarea" rows={3} value={counterpartyDetail.review_snapshot.sof_description || t("common.notAvailable")} readOnly />
                </label>
                <div className="otc-stack" data-testid="counterparty-official-history-panel">
                  <strong>{tr("counterparties.detail.history.title" as MessageKey)}</strong>
                  <p className="otc-muted">{tr("counterparties.detail.history.description" as MessageKey)}</p>
                  {historyLoading ? (
                    <Message>{tr("counterparties.detail.history.loading" as MessageKey)}</Message>
                  ) : historyError ? (
                    <Message data-testid="counterparty-official-history-message">{historyError}</Message>
                  ) : counterpartyHistory.length ? (
                    <ul className="otc-list">
                      {counterpartyHistory.map((item) => (
                        <li key={item.id} data-testid={`counterparty-official-history-item-${item.id}`}>
                          <strong>{item.change_type}</strong>
                          {" • "}
                          {formatDate(item.changed_at, locale) ?? item.changed_at}
                          {" • "}
                          {(item.field_changed || tr("counterparties.detail.history.fieldGeneric" as MessageKey))}
                          {" • "}
                          {(item.new_value || t("common.notAvailable"))}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <Message data-testid="counterparty-official-history-message">
                      {tr("counterparties.detail.history.empty" as MessageKey)}
                    </Message>
                  )}
                </div>
              </>
            ) : null}
          </div>
        ) : null}

        {canReadCounterpartyData === false ? null : <WorkItemTimelinePanel
          state={!selectedTimelineRecord ? "empty_selection" : !selectedTimelineRecord.workItemId ? "local_only" : "ready"}
          summary={
            selectedTimelineRecord
              ? tr("counterparties.workspace.timeline.summary" as MessageKey, {
                  name: selectedTimelineRecord.legalName || selectedTimelineRecord.counterpartyId
                })
              : null
          }
          contextBadges={timelineContextBadges}
          localOnlyHint={selectedTimelineRecord ? tr("counterparties.workspace.timeline.localHint" as MessageKey) : null}
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
        />}
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
        {canReadCounterpartyData === false ? (
          <Message data-testid="counterparties-list-read-restricted">
            {tr("counterparties.list.restricted" as MessageKey)}
          </Message>
        ) : <div className="otc-message otc-panel-summary">
          {tr("counterparties.list.total" as MessageKey, { total, page: currentPage, pages: totalPages })}
        </div>}
        {canReadCounterpartyData === false ? null : <table className="otc-table otc-table--spaced">
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
                const contextLinks = trackedRecord
                  ? buildCounterpartyContextLinks(
                      buildCounterpartyOperationalContext({
                        caseId: trackedRecord.caseId,
                        counterpartyId: trackedRecord.counterpartyId,
                        walletAddress: trackedRecord.walletAddress,
                        walletChain: trackedRecord.walletChain
                      }),
                      {
                        case: "counterparties.actions.openCase",
                        audit: "counterparties.actions.openAudit",
                        evidence: "counterparties.actions.openEvidence"
                      }
                    )
                  : [];
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
                    <td>{formatDate(item.created_at, locale) ?? t("common.notAvailable")}</td>
                    <td>
                      <div className="otc-controls">
                        <button type="button" className="otc-button otc-button--ghost" onClick={() => trackFromList(item)} disabled={syncingWorkspace}>
                          {tr("counterparties.list.track" as MessageKey)}
                        </button>
                        {contextLinks.map((link: OperationalContextLink & { labelKey: MessageKey }) => (
                          <a key={`list-${item.id}-${link.testIdSuffix}`} className="otc-button otc-button--ghost" href={link.href}>
                            {tr(link.labelKey)}
                          </a>
                        ))}
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
        </table>}
        {canReadCounterpartyData === false ? null : <div className="otc-controls otc-controls--spaced">
          <button className="otc-button" type="button" onClick={() => loadCounterparties(Math.max(0, offset - DEFAULT_LIMIT))} disabled={loading || offset === 0}>
            {tr("counterparties.list.previous" as MessageKey)}
          </button>
          <button className="otc-button" type="button" onClick={() => loadCounterparties(offset + DEFAULT_LIMIT)} disabled={loading || offset + DEFAULT_LIMIT >= total}>
            {tr("counterparties.list.next" as MessageKey)}
          </button>
        </div>}
      </Panel>
    </AppShell>
  );
}

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

import { AppShell, CodeBlock, ConfirmDialog, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import { useI18n } from "../../components/i18n-provider";
import { formatDateTime as formatDate } from "../lib/date-format";
import { buildAlertRcaSummary, normalizeAlertContainmentStatus, type AlertRcaContainmentStatus } from "../lib/alert-rca";
import type { MessageKey } from "../lib/i18n";
import { canManageMonitoringAdmin, canReadMonitoringAdmin } from "../lib/authz";
import { fetchAuthContext, resolveOwnerUserId, type AuthContext } from "../lib/ownership";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { WorkItemTimelinePanel } from "../../components/work-item-timeline-panel";
import { buildWorkItemTimelineLabels } from "../lib/work-item-timeline-labels";
import { formatTimelineEvent } from "../lib/work-item-timeline";
import { createWorkItemComment } from "../lib/work-item-timeline-client";
import {
  buildOperationalContextLinks,
  type OperationalContextLink,
  inferAlertOperationalContext
} from "../lib/operational-context";
import { useWorkItemTimeline } from "../lib/use-work-item-timeline";
import {
  buildPlatformAlertSelectionScope,
  clearPersistedPlatformAlertSelection,
  readPersistedPlatformAlertSelection,
  writePersistedPlatformAlertSelection,
  type PlatformAlertFilterState
} from "../lib/monitoring-platform-alerts";
import {
  type AlertsWorkItemMetadata,
  type CreateWorkItemRequest,
  type PatchWorkItemRequest,
  readWorkItemMetadataString,
  readWorkItemMetadataStringArray,
  resolveWorkItemOwnerDisplay,
  type WorkItemListResponse,
  type WorkItemPriority,
  type WorkItemQueueStatus,
  type WorkItemResponse,
  withCanonicalWorkItemMetadata
} from "../lib/work-items";

type PlatformOperationalAlertsSnapshot = {
  generated_at: string;
  receiver_filter: string | null;
  service_filter: string | null;
  severity_filter: string | null;
  status_filter: string | null;
  triage_status_filter: string | null;
  cursor: string | null;
  limit: number;
  count: number;
  total_count: number;
  has_more: boolean;
  next_cursor: string | null;
  data: Array<{
    id: string;
    receiver: string;
    status: string;
    triage_status: string;
    alertname: string;
    service: string | null;
    severity: string | null;
    fingerprint: string;
    labels: Record<string, unknown>;
    annotations: Record<string, unknown>;
    first_received_at: string;
    last_received_at: string;
    delivery_count: number;
    resolved_at: string | null;
    triaged_at: string | null;
    triaged_by: string | null;
    triage_note: string | null;
  }>;
};
type PlatformOperationalAlertEntry = PlatformOperationalAlertsSnapshot["data"][number];

type PlatformOperationalAlertFilterOptions = {
  services: string[];
  receivers: string[];
  generated_at: string;
};

type PlatformAlertExportFormat = "csv" | "json";
type AlertsWorkItemResponse = WorkItemResponse<AlertsWorkItemMetadata>;
type AlertsWorkItemListResponse = WorkItemListResponse<AlertsWorkItemMetadata>;
type PlatformAlertConfirmDialogState =
  | {
      kind: "filtered";
    }
  | {
      kind: "selected";
      selectedIds: string[];
    }
  | null;
type AlertRcaForm = {
  queueStatus: WorkItemQueueStatus;
  domain: string;
  affectedDomains: string;
  incidentCommander: string;
  containmentStatus: AlertRcaContainmentStatus;
  runbookRef: string;
  impactSummary: string;
  suspectedRootCause: string;
  confirmedRootCause: string;
  correctiveActions: string;
  evidenceRefs: string;
};
type AlertRcaSnapshot = {
  queueStatus: WorkItemQueueStatus;
  domain: string;
  affectedDomains: string[];
  incidentCommander: string;
  containmentStatus: AlertRcaContainmentStatus;
  runbookRef: string;
  impactSummary: string;
  suspectedRootCause: string;
  confirmedRootCause: string;
  correctiveActions: string[];
  evidenceRefs: string[];
};

const WORK_ITEMS_LIMIT = 100;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ALERT_RCA_CONTAINMENT_STATUSES: AlertRcaContainmentStatus[] = ["not_started", "in_progress", "contained", "validated"];
const DEFAULT_ALERT_RCA_FORM: AlertRcaForm = {
  queueStatus: "UNDER_REVIEW",
  domain: "monitoring",
  affectedDomains: "",
  incidentCommander: "",
  containmentStatus: "not_started",
  runbookRef: "",
  impactSummary: "",
  suspectedRootCause: "",
  confirmedRootCause: "",
  correctiveActions: "",
  evidenceRefs: ""
};

function buildDynamicFilterValues(currentValue: string, values: string[] | undefined) {
  const merged = new Set((values ?? []).filter((entry) => entry && entry !== "all"));
  if (currentValue !== "all") {
    merged.add(currentValue);
  }
  return Array.from(merged).sort((left, right) => left.localeCompare(right));
}

function isUuidLike(value: string | null | undefined) {
  return Boolean(value && UUID_PATTERN.test(value.trim()));
}

function priorityFromSeverity(severity: string | null): WorkItemPriority {
  if (severity === "critical") {
    return "critical";
  }
  if (severity === "warning") {
    return "high";
  }
  return "normal";
}

function toneForQueueStatus(status: WorkItemQueueStatus): "success" | "warning" | "danger" {
  if (status === "ESCALATED" || status === "REJECTED") {
    return "danger";
  }
  if (status === "UNDER_REVIEW") {
    return "warning";
  }
  return "success";
}

function parseCommaSeparatedList(value: string) {
  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function buildAlertRcaForm(item: AlertsWorkItemResponse | null): AlertRcaForm {
  if (!item) {
    return DEFAULT_ALERT_RCA_FORM;
  }

  const metadata = (item.metadata ?? {}) as Record<string, unknown>;
  return {
    queueStatus: item.queue_status,
    domain: readWorkItemMetadataString(metadata, "domain", "service") || "monitoring",
    affectedDomains: readWorkItemMetadataStringArray(metadata, "affected_domains").join(", "),
    incidentCommander: readWorkItemMetadataString(metadata, "incident_commander") || resolveWorkItemOwnerDisplay(metadata, item.owner_user_id),
    containmentStatus: normalizeAlertContainmentStatus(readWorkItemMetadataString(metadata, "containment_status")),
    runbookRef: readWorkItemMetadataString(metadata, "runbook_ref"),
    impactSummary: readWorkItemMetadataString(metadata, "impact_summary"),
    suspectedRootCause: readWorkItemMetadataString(metadata, "suspected_root_cause"),
    confirmedRootCause: readWorkItemMetadataString(metadata, "confirmed_root_cause"),
    correctiveActions: readWorkItemMetadataStringArray(metadata, "corrective_actions").join(", "),
    evidenceRefs: readWorkItemMetadataStringArray(metadata, "evidence_refs").join(", ")
  };
}

function buildAlertRcaSnapshotFromForm(form: AlertRcaForm): AlertRcaSnapshot {
  return {
    queueStatus: form.queueStatus,
    domain: form.domain.trim(),
    affectedDomains: parseCommaSeparatedList(form.affectedDomains),
    incidentCommander: form.incidentCommander.trim(),
    containmentStatus: form.containmentStatus,
    runbookRef: form.runbookRef.trim(),
    impactSummary: form.impactSummary.trim(),
    suspectedRootCause: form.suspectedRootCause.trim(),
    confirmedRootCause: form.confirmedRootCause.trim(),
    correctiveActions: parseCommaSeparatedList(form.correctiveActions),
    evidenceRefs: parseCommaSeparatedList(form.evidenceRefs)
  };
}

function buildAlertRcaSnapshotFromItem(item: AlertsWorkItemResponse | null): AlertRcaSnapshot {
  return buildAlertRcaSnapshotFromForm(buildAlertRcaForm(item));
}

function sameAlertRcaSnapshot(left: AlertRcaSnapshot, right: AlertRcaSnapshot) {
  return JSON.stringify(left) === JSON.stringify(right);
}

function buildFallbackPlatformAlertEntry(item: AlertsWorkItemResponse): PlatformOperationalAlertEntry {
  const metadata = (item.metadata ?? {}) as Record<string, unknown>;
  return {
    id: item.resource_id,
    receiver: readWorkItemMetadataString(metadata, "receiver") || "unknown",
    status: readWorkItemMetadataString(metadata, "status") || "firing",
    triage_status: readWorkItemMetadataString(metadata, "triage_status") || (item.queue_status === "CLOSED" ? "acknowledged" : "pending"),
    alertname: readWorkItemMetadataString(metadata, "alertname") || item.resource_id,
    service: readWorkItemMetadataString(metadata, "service") || null,
    severity: readWorkItemMetadataString(metadata, "severity") || null,
    fingerprint: readWorkItemMetadataString(metadata, "fingerprint") || item.id,
    labels: {},
    annotations: {},
    first_received_at: readWorkItemMetadataString(metadata, "first_received_at") || item.created_at || item.updated_at,
    last_received_at: readWorkItemMetadataString(metadata, "last_received_at") || item.last_activity_at || item.updated_at,
    delivery_count: typeof metadata["delivery_count"] === "number" ? metadata["delivery_count"] : 0,
    resolved_at: item.queue_status === "CLOSED" ? item.updated_at : null,
    triaged_at: readWorkItemMetadataString(metadata, "triaged_at") || null,
    triaged_by: readWorkItemMetadataString(metadata, "triaged_by") || null,
    triage_note: item.note ?? readWorkItemMetadataString(metadata, "triage_note")
  };
}

export default function AlertsPage() {
  const { locale, t } = useI18n();
  const searchParams = useSearchParams();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);

  const [platformOperationalAlerts, setPlatformOperationalAlerts] = useState<PlatformOperationalAlertsSnapshot | null>(null);
  const [platformAlertStatusFilter, setPlatformAlertStatusFilter] = useState("all");
  const [platformAlertTriageFilter, setPlatformAlertTriageFilter] = useState("all");
  const [platformAlertServiceFilter, setPlatformAlertServiceFilter] = useState("all");
  const [platformAlertReceiverFilter, setPlatformAlertReceiverFilter] = useState("all");
  const [platformAlertSeverityFilter, setPlatformAlertSeverityFilter] = useState("all");
  const [platformAlertCursor, setPlatformAlertCursor] = useState<string | null>(null);
  const [platformAlertCursorHistory, setPlatformAlertCursorHistory] = useState<Array<string | null>>([]);
  const [platformAlertMessage, setPlatformAlertMessage] = useState<string | null>(null);
  const [acknowledgingPlatformAlertId, setAcknowledgingPlatformAlertId] = useState<string | null>(null);
  const [acknowledgingPlatformAlertsBatch, setAcknowledgingPlatformAlertsBatch] = useState(false);
  const [exportingPlatformAlerts, setExportingPlatformAlerts] = useState<"filtered" | "selected" | null>(null);
  const [platformAlertExportFormat, setPlatformAlertExportFormat] = useState<PlatformAlertExportFormat>("csv");
  const [selectedPlatformAlertIds, setSelectedPlatformAlertIds] = useState<string[]>([]);
  const [platformAlertSelectionScope, setPlatformAlertSelectionScope] = useState<string | null>(null);
  const [platformAlertSelectionHydrated, setPlatformAlertSelectionHydrated] = useState(false);
  const [platformAlertFilterOptions, setPlatformAlertFilterOptions] = useState<PlatformOperationalAlertFilterOptions | null>(null);
  const [platformAlertConfirmDialogState, setPlatformAlertConfirmDialogState] = useState<PlatformAlertConfirmDialogState>(null);
  const [platformAlertWorkItems, setPlatformAlertWorkItems] = useState<Record<string, AlertsWorkItemResponse>>({});
  const [trackingPlatformAlertId, setTrackingPlatformAlertId] = useState<string | null>(null);
  const [rcaForm, setRcaForm] = useState<AlertRcaForm>(DEFAULT_ALERT_RCA_FORM);
  const [rcaSaving, setRcaSaving] = useState(false);
  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [authResolved, setAuthResolved] = useState(false);
  const [timelineAlertId, setTimelineAlertId] = useState<string | null>(null);
  const {
    timelineLoading,
    timelineError,
    timelineData,
    commentType,
    commentBody,
    commentSubmitting,
    setCommentType,
    setCommentBody,
    loadTimeline,
    submitTimelineComment
  } = useWorkItemTimeline<AlertsWorkItemResponse>({
    resolveErrorMessage: (apiError, fallback) => resolveApiErrorMessage(t, apiError, fallback),
    loadErrorMessage: tr("alerts.workspace.timeline.errorLoad" as MessageKey),
    commentErrorMessage: tr("alerts.workspace.timeline.errorComment" as MessageKey)
  });
  const [error, setError] = useState<string | null>(null);
  const platformAlertsRequestIdRef = useRef(0);
  const canReadPlatformAdmin = authResolved ? canReadMonitoringAdmin(authContext?.role) : null;
  const canManagePlatformAdmin = authResolved ? canManageMonitoringAdmin(authContext?.role) : null;

  const platformAlertPage = platformAlertCursorHistory.length + 1;
  const platformAlertTotalPages = platformOperationalAlerts
    ? Math.max(1, Math.ceil(platformOperationalAlerts.total_count / platformOperationalAlerts.limit))
    : 1;

  const selectablePlatformAlertIds =
    platformOperationalAlerts?.data
      .filter((entry) => entry.triage_status === "pending")
      .map((entry) => entry.id) ?? [];
  const allSelectablePlatformAlertsSelected =
    selectablePlatformAlertIds.length > 0 && selectablePlatformAlertIds.every((entryId) => selectedPlatformAlertIds.includes(entryId));

  const platformAlertServiceOptions = useMemo(() => {
    return buildDynamicFilterValues(platformAlertServiceFilter, platformAlertFilterOptions?.services);
  }, [platformAlertFilterOptions?.services, platformAlertServiceFilter]);

  const platformAlertReceiverOptions = useMemo(() => {
    return buildDynamicFilterValues(platformAlertReceiverFilter, platformAlertFilterOptions?.receivers);
  }, [platformAlertFilterOptions?.receivers, platformAlertReceiverFilter]);
  const trackedPlatformAlertCount = useMemo(() => Object.keys(platformAlertWorkItems).length, [platformAlertWorkItems]);
  const platformAlertConfirmDialog = platformAlertConfirmDialogState
    ? {
        title: tr("monitoring.platform.confirmTitle" as MessageKey),
        description:
          platformAlertConfirmDialogState.kind === "filtered"
            ? tr("monitoring.platform.confirmFiltered" as MessageKey)
            : tr("monitoring.platform.confirmSelected" as MessageKey, {
                count: platformAlertConfirmDialogState.selectedIds.length
              }),
        confirmLabel:
          platformAlertConfirmDialogState.kind === "filtered"
            ? tr("monitoring.platform.ackFiltered" as MessageKey)
            : tr("monitoring.platform.ackSelected" as MessageKey, {
                count: platformAlertConfirmDialogState.selectedIds.length
              }),
        cancelLabel: tr("common.cancel" as MessageKey),
        tone: "default" as const,
        testId:
          platformAlertConfirmDialogState.kind === "filtered"
            ? "platform-alert-confirm-dialog-filtered"
            : "platform-alert-confirm-dialog-selected"
      }
    : null;

  function filtersFromSearchParams() {
    return {
      status: searchParams.get("status") ?? "all",
      triageStatus: searchParams.get("triage_status") ?? "all",
      service: searchParams.get("service") ?? "all",
      receiver: searchParams.get("receiver") ?? "all",
      severity: searchParams.get("severity") ?? "all"
    };
  }

  function currentPlatformAlertFilters(): PlatformAlertFilterState {
    return {
      status: platformAlertStatusFilter,
      triageStatus: platformAlertTriageFilter,
      service: platformAlertServiceFilter,
      receiver: platformAlertReceiverFilter,
      severity: platformAlertSeverityFilter
    };
  }

  function clearPlatformAlertSelectionPersistence() {
    if (typeof window === "undefined") {
      return;
    }
    clearPersistedPlatformAlertSelection(window.sessionStorage);
  }

  function persistPlatformAlertSelection(scope: string | null, selectedIds: string[]) {
    if (typeof window === "undefined") {
      return;
    }
    writePersistedPlatformAlertSelection(window.sessionStorage, {
      ...currentPlatformAlertFilters(),
      cursor: platformAlertCursor,
      cursorHistory: platformAlertCursorHistory,
      selectedIds,
      selectionScope: scope
    });
  }

  function hydratePersistedPlatformAlertSelection(scope: string | null) {
    if (typeof window === "undefined") {
      return;
    }
    try {
      const parsed = readPersistedPlatformAlertSelection(window.sessionStorage);
      if (parsed?.selectionScope && parsed.selectionScope === scope) {
        setSelectedPlatformAlertIds(parsed.selectedIds);
      }
    } catch {
      return;
    }
  }

  function translatePlatformStatus(status: string) {
    if (status === "firing") {
      return t("monitoring.platform.status.firing");
    }
    if (status === "resolved") {
      return t("monitoring.platform.status.resolved");
    }
    return status;
  }

  function translatePlatformTriage(status: string) {
    if (status === "pending") {
      return t("monitoring.platform.triage.pending");
    }
    if (status === "acknowledged") {
      return t("monitoring.platform.triage.acknowledged");
    }
    return status;
  }

  function formatPlatformTimestamp(value: string | null | undefined) {
    const normalized = value?.trim() ?? "";
    if (!normalized) {
      return t("common.notAvailable");
    }
    return formatDate(normalized, locale) ?? normalized;
  }

  function translatePlatformSeverity(severity: string | null) {
    if (severity === "info") {
      return t("monitoring.platform.severity.info");
    }
    if (severity === "warning") {
      return t("monitoring.platform.severity.warning");
    }
    if (severity === "critical") {
      return t("monitoring.platform.severity.critical");
    }
    return severity ?? t("common.notAvailable");
  }

  async function loadPlatformOperationalAlertFilterOptions() {
    if (canReadPlatformAdmin !== true) {
      return;
    }
    const res = await fetch("/api/app/monitoring/operational-alert-filter-options", { cache: "no-store" });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      setError(t("monitoring.errors.loadPlatformFilterOptions"));
      return;
    }
    setPlatformAlertFilterOptions(data as PlatformOperationalAlertFilterOptions);
  }

  async function loadPlatformAlertWorkItems() {
    if (canReadPlatformAdmin !== true) {
      return;
    }
    const res = await fetch(
      `/api/app/operations/work-items?module=alerts&resource_type=operational_alert&limit=${WORK_ITEMS_LIMIT}`,
      { cache: "no-store" }
    );
    const data = (await res.json().catch(() => null)) as AlertsWorkItemListResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      return;
    }

    const items = data && "data" in data && Array.isArray(data.data) ? data.data : [];
    const nextMap = items.reduce<Record<string, AlertsWorkItemResponse>>((accumulator, item) => {
      accumulator[item.resource_id] = item;
      return accumulator;
    }, {});
    setPlatformAlertWorkItems(nextMap);
  }

  async function loadPlatformOperationalAlerts(
    status = platformAlertStatusFilter,
    triageStatus = platformAlertTriageFilter,
    service = platformAlertServiceFilter,
    receiver = platformAlertReceiverFilter,
    severity = platformAlertSeverityFilter,
    cursor = platformAlertCursor
  ) {
    if (canReadPlatformAdmin !== true) {
      return;
    }
    const params = new URLSearchParams();
    if (status !== "all") {
      params.set("status", status);
    }
    if (triageStatus !== "all") {
      params.set("triage_status", triageStatus);
    }
    if (service !== "all") {
      params.set("service", service);
    }
    if (receiver !== "all") {
      params.set("receiver", receiver);
    }
    if (severity !== "all") {
      params.set("severity", severity);
    }
    if (cursor) {
      params.set("cursor", cursor);
    }
    params.set("limit", "20");

    const requestId = platformAlertsRequestIdRef.current + 1;
    platformAlertsRequestIdRef.current = requestId;
    const res = await fetch(`/api/app/monitoring/operational-alerts?${params.toString()}`, { cache: "no-store" });
    const data = await res.json().catch(() => null);
    if (requestId !== platformAlertsRequestIdRef.current) {
      return;
    }
    if (!res.ok) {
      setError(t("monitoring.errors.loadPlatformAlerts"));
      return;
    }
    setPlatformOperationalAlerts(data as PlatformOperationalAlertsSnapshot);
    await loadPlatformAlertWorkItems();
    const nextScope = buildPlatformAlertSelectionScope({ status, triageStatus, service, receiver, severity });
    setPlatformAlertSelectionScope((currentScope) => {
      if (currentScope && currentScope !== nextScope) {
        setSelectedPlatformAlertIds([]);
      }
      return nextScope;
    });
  }

  async function refreshPlatformOperationalAlerts() {
    if (canReadPlatformAdmin !== true) {
      return;
    }
    setPlatformAlertMessage(null);
    setError(null);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    await loadPlatformOperationalAlerts(
      platformAlertStatusFilter,
      platformAlertTriageFilter,
      platformAlertServiceFilter,
      platformAlertReceiverFilter,
      platformAlertSeverityFilter,
      null
    );
  }

  async function handlePlatformAlertStatusFilterChange(value: string) {
    if (canReadPlatformAdmin !== true) {
      return;
    }
    setPlatformAlertStatusFilter(value);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    await loadPlatformOperationalAlerts(value, platformAlertTriageFilter, platformAlertServiceFilter, platformAlertReceiverFilter, platformAlertSeverityFilter, null);
  }

  async function handlePlatformAlertTriageFilterChange(value: string) {
    if (canReadPlatformAdmin !== true) {
      return;
    }
    setPlatformAlertTriageFilter(value);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    await loadPlatformOperationalAlerts(platformAlertStatusFilter, value, platformAlertServiceFilter, platformAlertReceiverFilter, platformAlertSeverityFilter, null);
  }

  async function handlePlatformAlertServiceFilterChange(value: string) {
    if (canReadPlatformAdmin !== true) {
      return;
    }
    setPlatformAlertServiceFilter(value);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    await loadPlatformOperationalAlerts(platformAlertStatusFilter, platformAlertTriageFilter, value, platformAlertReceiverFilter, platformAlertSeverityFilter, null);
  }

  async function handlePlatformAlertReceiverFilterChange(value: string) {
    if (canReadPlatformAdmin !== true) {
      return;
    }
    setPlatformAlertReceiverFilter(value);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    await loadPlatformOperationalAlerts(platformAlertStatusFilter, platformAlertTriageFilter, platformAlertServiceFilter, value, platformAlertSeverityFilter, null);
  }

  async function handlePlatformAlertSeverityFilterChange(value: string) {
    if (canReadPlatformAdmin !== true) {
      return;
    }
    setPlatformAlertSeverityFilter(value);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    await loadPlatformOperationalAlerts(platformAlertStatusFilter, platformAlertTriageFilter, platformAlertServiceFilter, platformAlertReceiverFilter, value, null);
  }

  function togglePlatformAlertSelection(alertId: string) {
    setSelectedPlatformAlertIds((current) => {
      const next = current.includes(alertId) ? current.filter((entry) => entry !== alertId) : [...current, alertId];
      persistPlatformAlertSelection(platformAlertSelectionScope, next);
      return next;
    });
  }

  function toggleAllSelectablePlatformAlerts() {
    setSelectedPlatformAlertIds((current) => {
      const next = allSelectablePlatformAlertsSelected
        ? current.filter((entryId) => !selectablePlatformAlertIds.includes(entryId))
        : Array.from(new Set([...current, ...selectablePlatformAlertIds]));
      persistPlatformAlertSelection(platformAlertSelectionScope, next);
      return next;
    });
  }

  async function acknowledgePlatformAlert(eventId: string) {
    if (!eventId || canManagePlatformAdmin !== true) {
      if (canManagePlatformAdmin === false) {
        setError(t("monitoring.platform.mutationRestricted" as MessageKey));
      }
      return;
    }
    const trackedWorkItem = platformAlertWorkItems[eventId];
    const currentEntry = platformOperationalAlerts?.data.find((entry) => entry.id === eventId) ?? null;
    setAcknowledgingPlatformAlertId(eventId);
    setError(null);
    setPlatformAlertMessage(null);
    const res = await fetch(`/api/app/monitoring/operational-alerts/${eventId}/acknowledge`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ note: "ack_from_alerts_ui", triaged_by: "admin_ui" }),
      cache: "no-store"
    });
    const body = await res.json().catch(() => null);
    if (!res.ok) {
      setError(resolveApiErrorMessage(t, body, t("monitoring.errors.ackPlatformAlert")));
      setAcknowledgingPlatformAlertId(null);
      return;
    }
    if (trackedWorkItem && currentEntry) {
      try {
        await syncPlatformAlertWorkItem(currentEntry, { nextStatus: "CLOSED" });
      } catch (syncError) {
        setError(syncError instanceof Error ? syncError.message : t("monitoring.errors.trackPlatformAlert" as MessageKey));
      }
    }
    setPlatformAlertMessage(t("monitoring.platform.messageAckSingle", { eventId, status: body?.triage_status ?? "acknowledged" }));
    setAcknowledgingPlatformAlertId(null);
    setSelectedPlatformAlertIds((current) => current.filter((entry) => entry !== eventId));
    await refreshPlatformOperationalAlerts();
  }

  async function performAcknowledgeFilteredPlatformAlerts() {
    if (canManagePlatformAdmin !== true) {
      if (canManagePlatformAdmin === false) {
        setError(t("monitoring.platform.mutationRestricted" as MessageKey));
      }
      return;
    }
    if (!platformOperationalAlerts?.total_count) {
      return;
    }

    setAcknowledgingPlatformAlertsBatch(true);
    setError(null);
    setPlatformAlertMessage(null);
    try {
      const res = await fetch("/api/app/monitoring/operational-alerts/acknowledge-batch", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          note: "ack_batch_from_alerts_ui",
          triaged_by: "admin_ui",
          status: platformAlertStatusFilter === "all" ? null : platformAlertStatusFilter,
          triage_status: platformAlertTriageFilter === "all" ? null : platformAlertTriageFilter,
          service: platformAlertServiceFilter === "all" ? null : platformAlertServiceFilter,
          receiver: platformAlertReceiverFilter === "all" ? null : platformAlertReceiverFilter,
          severity: platformAlertSeverityFilter === "all" ? null : platformAlertSeverityFilter
        }),
        cache: "no-store"
      });
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        setError(resolveApiErrorMessage(t, data, t("monitoring.errors.ackPlatformAlertsBatch")));
        return;
      }
      const data = await res.json().catch(() => null);
      const updatedCount = typeof data?.updated_count === "number" ? data.updated_count : 0;
      setPlatformAlertMessage(
        updatedCount ? t("monitoring.platform.messageAckBatchDone", { count: updatedCount }) : t("monitoring.platform.messageAckBatchEmpty")
      );
      clearPlatformAlertSelectionPersistence();
      setSelectedPlatformAlertIds([]);
      await refreshPlatformOperationalAlerts();
    } catch {
      setError(t("monitoring.errors.ackPlatformAlertsBatch"));
    } finally {
      setAcknowledgingPlatformAlertsBatch(false);
    }
  }

  async function performAcknowledgeSelectedPlatformAlerts(selectedIds: string[]) {
    if (canManagePlatformAdmin !== true) {
      if (canManagePlatformAdmin === false) {
        setError(t("monitoring.platform.mutationRestricted" as MessageKey));
      }
      return;
    }
    if (!selectedIds.length) {
      return;
    }

    setAcknowledgingPlatformAlertsBatch(true);
    setError(null);
    setPlatformAlertMessage(null);
    try {
      const res = await fetch("/api/app/monitoring/operational-alerts/acknowledge-batch", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          ids: selectedIds,
          note: "ack_selected_from_alerts_ui",
          triaged_by: "admin_ui",
          status: platformAlertStatusFilter === "all" ? null : platformAlertStatusFilter,
          triage_status: platformAlertTriageFilter === "all" ? null : platformAlertTriageFilter,
          service: platformAlertServiceFilter === "all" ? null : platformAlertServiceFilter,
          receiver: platformAlertReceiverFilter === "all" ? null : platformAlertReceiverFilter,
          severity: platformAlertSeverityFilter === "all" ? null : platformAlertSeverityFilter
        }),
        cache: "no-store"
      });
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        setError(resolveApiErrorMessage(t, data, t("monitoring.errors.ackPlatformAlertsSelected")));
        return;
      }
      const data = await res.json().catch(() => null);
      const updatedCount = typeof data?.updated_count === "number" ? data.updated_count : 0;
      setPlatformAlertMessage(
        updatedCount ? t("monitoring.platform.messageAckSelectedDone", { count: updatedCount }) : t("monitoring.platform.messageAckSelectedEmpty")
      );
      clearPlatformAlertSelectionPersistence();
      setSelectedPlatformAlertIds([]);
      await refreshPlatformOperationalAlerts();
    } catch {
      setError(t("monitoring.errors.ackPlatformAlertsSelected"));
    } finally {
      setAcknowledgingPlatformAlertsBatch(false);
    }
  }

  function acknowledgeFilteredPlatformAlerts() {
    if (!platformOperationalAlerts?.total_count) {
      return;
    }

    setPlatformAlertConfirmDialogState({ kind: "filtered" });
  }

  function acknowledgeSelectedPlatformAlerts() {
    if (!selectedPlatformAlertIds.length) {
      return;
    }

    setPlatformAlertConfirmDialogState({
      kind: "selected",
      selectedIds: [...selectedPlatformAlertIds]
    });
  }

  function cancelPlatformAlertConfirmation() {
    if (acknowledgingPlatformAlertsBatch) {
      return;
    }

    setPlatformAlertConfirmDialogState(null);
  }

  async function confirmPlatformAlertConfirmation() {
    if (!platformAlertConfirmDialogState) {
      return;
    }

    const pendingConfirmation = platformAlertConfirmDialogState;
    setPlatformAlertConfirmDialogState(null);

    if (pendingConfirmation.kind === "filtered") {
      await performAcknowledgeFilteredPlatformAlerts();
      return;
    }

    await performAcknowledgeSelectedPlatformAlerts(pendingConfirmation.selectedIds);
  }

  function resolveDownloadFilename(contentDisposition: string | null, fallbackName: string) {
    if (!contentDisposition) {
      return fallbackName;
    }
    const match = /filename="([^"]+)"/i.exec(contentDisposition);
    return match?.[1] ?? fallbackName;
  }

  async function exportPlatformAlerts(scope: "filtered" | "selected") {
    if (canManagePlatformAdmin !== true) {
      if (canManagePlatformAdmin === false) {
        setError(t("monitoring.platform.mutationRestricted" as MessageKey));
      }
      return;
    }
    if (scope === "selected" && !selectedPlatformAlertIds.length) {
      setError(t("monitoring.platform.selectAtLeastOne"));
      return;
    }
    setExportingPlatformAlerts(scope);
    setError(null);
    setPlatformAlertMessage(null);
    const res = await fetch("/api/app/monitoring/operational-alerts/export", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        format: platformAlertExportFormat,
        scope,
        ids: scope === "selected" ? selectedPlatformAlertIds : [],
        status: platformAlertStatusFilter === "all" ? null : platformAlertStatusFilter,
        triage_status: platformAlertTriageFilter === "all" ? null : platformAlertTriageFilter,
        service: platformAlertServiceFilter === "all" ? null : platformAlertServiceFilter,
        receiver: platformAlertReceiverFilter === "all" ? null : platformAlertReceiverFilter,
        severity: platformAlertSeverityFilter === "all" ? null : platformAlertSeverityFilter
      })
    });
    if (!res.ok) {
      setError(t("monitoring.errors.exportPlatformAlerts"));
      setExportingPlatformAlerts(null);
      return;
    }

    const filename = resolveDownloadFilename(res.headers.get("content-disposition"), `operational-alerts-${scope}.${platformAlertExportFormat}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    setPlatformAlertMessage(
      scope === "selected"
        ? t("monitoring.platform.messageExportSelected", { count: selectedPlatformAlertIds.length })
        : t("monitoring.platform.messageExportFiltered")
    );
    setExportingPlatformAlerts(null);
  }

  async function syncPlatformAlertWorkItem(
    entry: PlatformOperationalAlertEntry,
    options?: {
      nextStatus?: WorkItemQueueStatus;
      metadataOverrides?: Partial<AlertsWorkItemMetadata>;
    }
  ) {
    if (canManagePlatformAdmin !== true) {
      throw new Error(t("monitoring.platform.mutationRestricted" as MessageKey));
    }
    const existing = platformAlertWorkItems[entry.id];
    const context = inferAlertOperationalContext(entry);
    const ownerUserId = resolveOwnerUserId({
      existingOwnerUserId: existing?.owner_user_id,
      linkedUserId: authContext?.linked_user_id,
      isUuidLike
    });
    const queueStatus =
      options?.nextStatus ??
      existing?.queue_status ??
      (entry.triage_status === "acknowledged" || entry.status === "resolved" ? "CLOSED" : "UNDER_REVIEW");
    const buildMetadata = (): AlertsWorkItemMetadata =>
      withCanonicalWorkItemMetadata(
        {
          ...(existing?.metadata ?? {}),
          alertname: entry.alertname,
          receiver: entry.receiver,
          service: entry.service,
          severity: entry.severity,
          status: entry.status,
          fingerprint: entry.fingerprint,
          first_received_at: entry.first_received_at,
          last_received_at: entry.last_received_at,
          delivery_count: entry.delivery_count,
          triage_status: entry.triage_status,
          triaged_at: entry.triaged_at,
          triaged_by: entry.triaged_by,
          triage_note: entry.triage_note,
          ...(context.address ? { address: context.address } : {}),
          ...(context.reportId ? { report_id: context.reportId } : {}),
          ...(options?.metadataOverrides ?? {})
        },
        {
          resourceType: "operational_alert",
          caseId: context.caseId,
          ownerLabel: readWorkItemMetadataString(existing?.metadata ?? {}, "owner_label"),
          ownerUserId
        }
      );
    const requestBody: CreateWorkItemRequest<AlertsWorkItemMetadata> | PatchWorkItemRequest<AlertsWorkItemMetadata> = existing
      ? {
          ...(ownerUserId ? { owner_user_id: ownerUserId } : {}),
          priority: priorityFromSeverity(entry.severity),
          queue_status: queueStatus,
          due_at: existing.due_at ?? null,
          title: `Alert ${entry.alertname}`,
          note: entry.triage_note ?? existing.note,
          metadata: buildMetadata()
        }
      : {
          module: "alerts",
          resource_type: "operational_alert",
          resource_id: entry.id,
          ...(isUuidLike(context.caseId) ? { case_id: context.caseId?.trim() } : {}),
          ...(ownerUserId ? { owner_user_id: ownerUserId } : {}),
          priority: priorityFromSeverity(entry.severity),
          queue_status: queueStatus,
          due_at: null,
          title: `Alert ${entry.alertname}`,
          note: entry.triage_note,
          metadata: buildMetadata()
        };

    setTrackingPlatformAlertId(entry.id);
    const res = await fetch(
      existing ? `/api/app/operations/work-items/${encodeURIComponent(existing.id)}` : "/api/app/operations/work-items",
      {
        method: existing ? "PATCH" : "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(requestBody),
        cache: "no-store"
      }
    );
    const data = (await res.json().catch(() => null)) as AlertsWorkItemResponse | { error?: string; detail?: unknown } | null;
    setTrackingPlatformAlertId(null);
    if (!res.ok) {
      throw new Error(resolveApiErrorMessage(t, data, t("monitoring.errors.trackPlatformAlert" as MessageKey)));
    }

    const workItem = data as AlertsWorkItemResponse;
    setPlatformAlertWorkItems((current) => ({ ...current, [workItem.resource_id]: workItem }));
    return workItem;
  }

  async function trackPlatformAlert(entry: PlatformOperationalAlertsSnapshot["data"][number]) {
    setError(null);
    setPlatformAlertMessage(null);
    try {
      const workItem = await syncPlatformAlertWorkItem(entry);
      setPlatformAlertMessage(
        t("monitoring.platform.messageTrackSingle" as MessageKey, { eventId: entry.id, status: workItem.queue_status.toLowerCase() })
      );
    } catch (trackError) {
      setError(trackError instanceof Error ? trackError.message : t("monitoring.errors.trackPlatformAlert" as MessageKey));
    }
  }

  function goToPreviousPlatformAlertsPage() {
    if (!platformAlertCursorHistory.length) {
      return;
    }
    const history = [...platformAlertCursorHistory];
    const previousCursor = history.pop() ?? null;
    setPlatformAlertCursorHistory(history);
    setPlatformAlertCursor(previousCursor);
    setError(null);
    loadPlatformOperationalAlerts(
      platformAlertStatusFilter,
      platformAlertTriageFilter,
      platformAlertServiceFilter,
      platformAlertReceiverFilter,
      platformAlertSeverityFilter,
      previousCursor
    ).catch(() => undefined);
  }

  function goToNextPlatformAlertsPage() {
    const nextCursor = platformOperationalAlerts?.next_cursor;
    if (!nextCursor) {
      return;
    }
    setError(null);
    setPlatformAlertCursorHistory((current) => [...current, platformAlertCursor]);
    setPlatformAlertCursor(nextCursor);
    loadPlatformOperationalAlerts(
      platformAlertStatusFilter,
      platformAlertTriageFilter,
      platformAlertServiceFilter,
      platformAlertReceiverFilter,
      platformAlertSeverityFilter,
      nextCursor
    ).catch(() => undefined);
  }

  useEffect(() => {
    fetchAuthContext()
      .then((data) => {
        setAuthContext(data);
      })
      .catch(() => {
        // Keep owner_user_id optional when auth context is unavailable.
        setAuthContext(null);
      })
      .finally(() => setAuthResolved(true));
  }, []);

  useEffect(() => {
    if (!authResolved) {
      return;
    }
    if (canReadPlatformAdmin !== true) {
      setPlatformOperationalAlerts(null);
      setPlatformAlertFilterOptions(null);
      setPlatformAlertWorkItems({});
      setSelectedPlatformAlertIds([]);
      setPlatformAlertMessage(null);
      setTimelineAlertId(null);
      return;
    }
    loadPlatformOperationalAlertFilterOptions().catch(() => undefined);
  }, [authResolved, canReadPlatformAdmin]);

  useEffect(() => {
    if (!authResolved) {
      return;
    }
    if (canReadPlatformAdmin !== true) {
      return;
    }
    const next = filtersFromSearchParams();
    setPlatformAlertStatusFilter(next.status);
    setPlatformAlertTriageFilter(next.triageStatus);
    setPlatformAlertServiceFilter(next.service);
    setPlatformAlertReceiverFilter(next.receiver);
    setPlatformAlertSeverityFilter(next.severity);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    setError(null);
    setPlatformAlertMessage(null);
    loadPlatformOperationalAlerts(next.status, next.triageStatus, next.service, next.receiver, next.severity, null).catch(() => undefined);
  }, [authResolved, canReadPlatformAdmin, searchParams]);

  useEffect(() => {
    if (platformAlertSelectionHydrated) {
      return;
    }
    if (!platformAlertSelectionScope) {
      return;
    }
    hydratePersistedPlatformAlertSelection(platformAlertSelectionScope);
    setPlatformAlertSelectionHydrated(true);
  }, [platformAlertSelectionHydrated, platformAlertSelectionScope]);

  const firingCount = useMemo(() => platformOperationalAlerts?.data.filter((entry) => entry.status === "firing").length ?? 0, [platformOperationalAlerts]);
  const pendingTriageCount = useMemo(() => platformOperationalAlerts?.data.filter((entry) => entry.triage_status === "pending").length ?? 0, [platformOperationalAlerts]);
  const acknowledgedCount = useMemo(
    () => platformOperationalAlerts?.data.filter((entry) => entry.triage_status === "acknowledged").length ?? 0,
    [platformOperationalAlerts]
  );

  const selectedTimelineWorkItem = timelineAlertId ? platformAlertWorkItems[timelineAlertId] ?? null : null;
  const selectedTimelineEntry = timelineAlertId
    ? platformOperationalAlerts?.data.find((entry) => entry.id === timelineAlertId) ?? null
    : null;

  useEffect(() => {
    setRcaForm(buildAlertRcaForm(selectedTimelineWorkItem));
  }, [selectedTimelineWorkItem]);

  function updateRcaForm<Key extends keyof AlertRcaForm>(field: Key, value: AlertRcaForm[Key]) {
    setRcaForm((current) => ({ ...current, [field]: value }));
  }

  function translateContainmentStatus(status: AlertRcaContainmentStatus) {
    return tr(`alerts.workspace.rca.containment.${status}` as MessageKey);
  }

  function buildAlertRcaAutoCommentBody(snapshot: AlertRcaSnapshot) {
    const lines = [tr("alerts.workspace.rca.autoCommentTitle" as MessageKey)];
    lines.push(
      `${tr("alerts.workspace.rca.queueStatus" as MessageKey)}: ${tr(`monitoring.platform.queueStatus.${snapshot.queueStatus.toLowerCase()}` as MessageKey)}`
    );
    lines.push(`${tr("alerts.workspace.rca.domain" as MessageKey)}: ${snapshot.domain || tr("alerts.history.notAvailable" as MessageKey)}`);
    lines.push(
      `${tr("alerts.workspace.rca.containmentStatus" as MessageKey)}: ${translateContainmentStatus(snapshot.containmentStatus)}`
    );
    if (snapshot.incidentCommander) {
      lines.push(`${tr("alerts.workspace.rca.incidentCommander" as MessageKey)}: ${snapshot.incidentCommander}`);
    }
    if (snapshot.affectedDomains.length) {
      lines.push(`${tr("alerts.workspace.rca.affectedDomains" as MessageKey)}: ${snapshot.affectedDomains.join(", ")}`);
    }
    if (snapshot.runbookRef) {
      lines.push(`${tr("alerts.workspace.rca.runbookRef" as MessageKey)}: ${snapshot.runbookRef}`);
    }
    if (snapshot.impactSummary) {
      lines.push(`${tr("alerts.workspace.rca.impactSummary" as MessageKey)}: ${snapshot.impactSummary}`);
    }
    if (snapshot.suspectedRootCause) {
      lines.push(`${tr("alerts.workspace.rca.suspectedRootCause" as MessageKey)}: ${snapshot.suspectedRootCause}`);
    }
    if (snapshot.confirmedRootCause) {
      lines.push(`${tr("alerts.workspace.rca.confirmedRootCause" as MessageKey)}: ${snapshot.confirmedRootCause}`);
    }
    if (snapshot.correctiveActions.length) {
      lines.push(`${tr("alerts.workspace.rca.correctiveActions" as MessageKey)}: ${snapshot.correctiveActions.join(", ")}`);
    }
    if (snapshot.evidenceRefs.length) {
      lines.push(`${tr("alerts.workspace.rca.evidenceRefs" as MessageKey)}: ${snapshot.evidenceRefs.join(", ")}`);
    }
    return lines.join("\n");
  }

  async function saveAlertRca() {
    if (!selectedTimelineWorkItem) {
      setError(tr("alerts.workspace.rca.errorSave" as MessageKey));
      return;
    }

    setRcaSaving(true);
    setError(null);
    setPlatformAlertMessage(null);
    try {
      const previousSnapshot = buildAlertRcaSnapshotFromItem(selectedTimelineWorkItem);
      const nextSnapshot = buildAlertRcaSnapshotFromForm(rcaForm);
      const workItem = await syncPlatformAlertWorkItem(selectedTimelineEntry ?? buildFallbackPlatformAlertEntry(selectedTimelineWorkItem), {
        nextStatus: nextSnapshot.queueStatus,
        metadataOverrides: {
          domain: nextSnapshot.domain,
          affected_domains: nextSnapshot.affectedDomains,
          incident_commander: nextSnapshot.incidentCommander,
          containment_status: nextSnapshot.containmentStatus,
          runbook_ref: nextSnapshot.runbookRef,
          impact_summary: nextSnapshot.impactSummary,
          suspected_root_cause: nextSnapshot.suspectedRootCause,
          confirmed_root_cause: nextSnapshot.confirmedRootCause,
          corrective_actions: nextSnapshot.correctiveActions,
          evidence_refs: nextSnapshot.evidenceRefs
        }
      });
      const shouldPostAutoComment = !sameAlertRcaSnapshot(previousSnapshot, nextSnapshot);
      let autoCommentFailed = false;
      if (shouldPostAutoComment) {
        const commentResult = await createWorkItemComment(workItem.id, {
          comment_type: "decision",
          body: buildAlertRcaAutoCommentBody(nextSnapshot)
        });
        autoCommentFailed = !commentResult.ok;
      }
      setPlatformAlertMessage(
        tr(
          shouldPostAutoComment && !autoCommentFailed ? ("alerts.workspace.rca.savedWithComment" as MessageKey) : ("alerts.workspace.rca.saved" as MessageKey),
          {
            alertId: selectedTimelineEntry?.id ?? selectedTimelineWorkItem.resource_id
          }
        )
      );
      await loadTimeline(workItem.id);
      if (shouldPostAutoComment && autoCommentFailed) {
        setError(tr("alerts.workspace.rca.errorCommentAuto" as MessageKey));
      }
    } catch (rcaError) {
      setError(rcaError instanceof Error ? rcaError.message : tr("alerts.workspace.rca.errorSave" as MessageKey));
    } finally {
      setRcaSaving(false);
    }
  }

  if (!authResolved) {
    return (
      <AppShell
        title={tr("alerts.title" as MessageKey)}
        subtitle={tr("alerts.subtitle" as MessageKey)}
        activePath="/alerts"
        actions={<Pill>{tr("alerts.active" as MessageKey)}</Pill>}
      >
        <Message data-testid="alerts-auth-loading">{t("common.loading")}</Message>
      </AppShell>
    );
  }

  return (
    <AppShell title={tr("alerts.title" as MessageKey)} subtitle={tr("alerts.subtitle" as MessageKey)} activePath="/alerts" actions={<Pill>{tr("alerts.active" as MessageKey)}</Pill>}>
      <MetricGrid>
        <MetricCard label={tr("alerts.stats.total" as MessageKey)} value={platformOperationalAlerts?.total_count ?? 0} meta={tr("alerts.stats.totalMeta" as MessageKey)} />
        <MetricCard label={tr("alerts.stats.firing" as MessageKey)} value={firingCount} meta={tr("alerts.stats.firingMeta" as MessageKey)} accent />
        <MetricCard label={tr("alerts.stats.pending" as MessageKey)} value={pendingTriageCount} meta={tr("alerts.stats.pendingMeta" as MessageKey)} />
        <MetricCard label={tr("alerts.stats.ack" as MessageKey)} value={acknowledgedCount} meta={tr("alerts.stats.ackMeta" as MessageKey)} />
        <MetricCard label={tr("alerts.stats.tracked" as MessageKey)} value={trackedPlatformAlertCount} meta={tr("alerts.stats.trackedMeta" as MessageKey)} />
      </MetricGrid>

      <Panel title={t("monitoring.platform.title")}>
        {canReadPlatformAdmin === false ? (
          <Message data-testid="platform-alert-read-restricted">{t("monitoring.platform.readRestricted" as MessageKey)}</Message>
        ) : (
          <>
        <div className="otc-controls">
          <select
            aria-label={t("monitoring.platform.filters.statusAria")}
            data-testid="platform-alert-filter-status"
            value={platformAlertStatusFilter}
            onChange={(event) => handlePlatformAlertStatusFilterChange(event.target.value)}
            className="otc-select"
          >
            <option value="all">{t("monitoring.platform.statusAll")}</option>
            <option value="firing">{t("monitoring.platform.status.firing")}</option>
            <option value="resolved">{t("monitoring.platform.status.resolved")}</option>
          </select>
          <select
            aria-label={t("monitoring.platform.filters.triageAria")}
            data-testid="platform-alert-filter-triage"
            value={platformAlertTriageFilter}
            onChange={(event) => handlePlatformAlertTriageFilterChange(event.target.value)}
            className="otc-select"
          >
            <option value="all">{t("monitoring.platform.triageAll")}</option>
            <option value="pending">{t("monitoring.platform.triage.pending")}</option>
            <option value="acknowledged">{t("monitoring.platform.triage.acknowledged")}</option>
          </select>
          <select
            aria-label={t("monitoring.platform.filters.serviceAria")}
            data-testid="platform-alert-filter-service"
            value={platformAlertServiceFilter}
            onChange={(event) => handlePlatformAlertServiceFilterChange(event.target.value)}
            className="otc-select"
          >
            <option value="all">{t("monitoring.platform.serviceAll")}</option>
            {platformAlertServiceOptions.map((serviceOption) => (
              <option key={serviceOption} value={serviceOption}>
                {serviceOption}
              </option>
            ))}
          </select>
          <select
            aria-label={t("monitoring.platform.filters.receiverAria")}
            data-testid="platform-alert-filter-receiver"
            value={platformAlertReceiverFilter}
            onChange={(event) => handlePlatformAlertReceiverFilterChange(event.target.value)}
            className="otc-select"
          >
            <option value="all">{t("monitoring.platform.receiverAll")}</option>
            {platformAlertReceiverOptions.map((receiverOption) => (
              <option key={receiverOption} value={receiverOption}>
                {receiverOption}
              </option>
            ))}
          </select>
          <select
            aria-label={t("monitoring.platform.filters.severityAria")}
            data-testid="platform-alert-filter-severity"
            value={platformAlertSeverityFilter}
            onChange={(event) => handlePlatformAlertSeverityFilterChange(event.target.value)}
            className="otc-select"
          >
            <option value="all">{t("monitoring.platform.severityAll")}</option>
            <option value="info">{t("monitoring.platform.severity.info")}</option>
            <option value="warning">{t("monitoring.platform.severity.warning")}</option>
            <option value="critical">{t("monitoring.platform.severity.critical")}</option>
          </select>
          <button type="button" data-testid="platform-alerts-refresh-btn" onClick={refreshPlatformOperationalAlerts} className="otc-button otc-button--ghost">
            {t("monitoring.platform.refresh")}
          </button>
          {canManagePlatformAdmin ? (
            <>
              <button
                type="button"
                data-testid="platform-alerts-ack-batch-btn"
                onClick={acknowledgeFilteredPlatformAlerts}
                disabled={acknowledgingPlatformAlertsBatch || !platformOperationalAlerts?.total_count || platformAlertTriageFilter === "acknowledged"}
                className="otc-button"
              >
                {acknowledgingPlatformAlertsBatch ? t("monitoring.platform.ackFilteredLoading") : t("monitoring.platform.ackFiltered")}
              </button>
              <button
                type="button"
                data-testid="platform-alerts-ack-selected-btn"
                onClick={acknowledgeSelectedPlatformAlerts}
                disabled={acknowledgingPlatformAlertsBatch || !selectedPlatformAlertIds.length}
                className="otc-button"
              >
                {acknowledgingPlatformAlertsBatch ? t("monitoring.platform.ackSelectedLoading") : t("monitoring.platform.ackSelected", { count: selectedPlatformAlertIds.length })}
              </button>
              <select
                aria-label={t("monitoring.platform.filters.exportFormatAria")}
                data-testid="platform-alert-export-format"
                value={platformAlertExportFormat}
                onChange={(event) => setPlatformAlertExportFormat(event.target.value as PlatformAlertExportFormat)}
                className="otc-select"
              >
                <option value="csv">CSV</option>
                <option value="json">JSON</option>
              </select>
              <button
                type="button"
                data-testid="platform-alerts-export-filtered-btn"
                onClick={() => exportPlatformAlerts("filtered")}
                disabled={!!exportingPlatformAlerts || !platformOperationalAlerts?.total_count}
                className="otc-button otc-button--ghost"
              >
                {exportingPlatformAlerts === "filtered" ? t("monitoring.platform.exportFilteredLoading") : t("monitoring.platform.exportFiltered")}
              </button>
              <button
                type="button"
                data-testid="platform-alerts-export-selected-btn"
                onClick={() => exportPlatformAlerts("selected")}
                disabled={!!exportingPlatformAlerts || !selectedPlatformAlertIds.length}
                className="otc-button otc-button--ghost"
              >
                {exportingPlatformAlerts === "selected"
                  ? t("monitoring.platform.exportSelectedLoading")
                  : t("monitoring.platform.exportSelected", { count: selectedPlatformAlertIds.length })}
              </button>
            </>
          ) : canManagePlatformAdmin === false ? (
            <Message data-testid="platform-alert-mutation-restricted">{t("monitoring.platform.mutationRestricted" as MessageKey)}</Message>
          ) : null}
          <span data-testid="platform-alerts-summary" className="otc-monitoring-meta">
            {platformOperationalAlerts
              ? t("monitoring.platform.summary", {
                  count: platformOperationalAlerts.count,
                  total: platformOperationalAlerts.total_count,
                  selected: selectedPlatformAlertIds.length,
                  page: platformAlertPage,
                  pages: platformAlertTotalPages
                })
              : t("monitoring.platform.noSnapshot")}
          </span>
          <button
            type="button"
            data-testid="platform-alerts-prev-btn"
            onClick={goToPreviousPlatformAlertsPage}
            disabled={!platformAlertCursorHistory.length}
            className="otc-button otc-button--ghost"
          >
            {t("monitoring.platform.previous")}
          </button>
          <button
            type="button"
            data-testid="platform-alerts-next-btn"
            onClick={goToNextPlatformAlertsPage}
            disabled={!platformOperationalAlerts?.has_more}
            className="otc-button otc-button--ghost"
          >
            {t("monitoring.platform.next")}
          </button>
        </div>

        {platformAlertMessage ? (
          <div data-testid="platform-alert-message" className="otc-monitoring-banner">
            <Message tone="success">{platformAlertMessage}</Message>
          </div>
        ) : null}

        {error ? (
          <div className="otc-monitoring-banner">
            <Message tone="error">{error}</Message>
          </div>
        ) : null}

        {platformOperationalAlerts ? (
          platformOperationalAlerts.data.length ? (
            <div className="otc-monitoring-grid otc-monitoring-banner">
              {canManagePlatformAdmin ? (
              <label data-testid="platform-alert-select-all-label" className="otc-monitoring-checkbox-row">
                <input
                  type="checkbox"
                  data-testid="platform-alert-select-all"
                  aria-label={t("monitoring.platform.selectAllAria")}
                  checked={allSelectablePlatformAlertsSelected}
                  disabled={!selectablePlatformAlertIds.length || acknowledgingPlatformAlertsBatch}
                  onChange={toggleAllSelectablePlatformAlerts}
                />
                {t("monitoring.platform.selectAll")}
              </label>
              ) : null}
              {platformOperationalAlerts.data.map((entry) => (
                (() => {
                  const context = inferAlertOperationalContext(entry);
                  const trackedWorkItem = platformAlertWorkItems[entry.id];
                  const rcaSummary = buildAlertRcaSummary(trackedWorkItem ?? null);
                  const contextLinks = buildOperationalContextLinks(context, {
                    includeEvidence: true,
                    evidenceDomain: "all",
                    auditFallbackResourceType: "operational_alert",
                    auditPreferCaseResource: true,
                    evidencePreferCaseResource: true,
                    investigateIncludeCaseId: true
                  }).filter(
                    (link: OperationalContextLink) =>
                      link.kind === "case" ||
                      link.kind === "audit" ||
                      link.kind === "evidence" ||
                      link.kind === "investigate" ||
                      link.kind === "sanctions"
                  );

                  return (
                    <div
                      key={entry.id}
                      data-testid={`platform-alert-row-${entry.id}`}
                      className={`otc-monitoring-card ${entry.status === "firing" ? "otc-monitoring-card--warning" : "otc-monitoring-card--success"}`}
                    >
                      <div className="otc-monitoring-row">
                        <div className="otc-monitoring-inline">
                          {canManagePlatformAdmin ? (
                          <input
                            type="checkbox"
                            data-testid={`platform-alert-select-${entry.id}`}
                            aria-label={t("monitoring.platform.selectOneAria", { name: entry.alertname })}
                            checked={selectedPlatformAlertIds.includes(entry.id)}
                            disabled={entry.triage_status !== "pending" || acknowledgingPlatformAlertsBatch}
                            onChange={() => togglePlatformAlertSelection(entry.id)}
                          />
                          ) : null}
                          <strong>{entry.alertname}</strong>
                        </div>
                        <span data-testid={`platform-alert-state-${entry.id}`}>
                          {translatePlatformSeverity(entry.severity)} • {translatePlatformStatus(entry.status)} • {t("monitoring.platform.triageLabel")}={translatePlatformTriage(entry.triage_status)}
                        </span>
                      </div>
                      <div className="otc-monitoring-detail">
                        {t("monitoring.platform.service")}={entry.service ?? t("common.notAvailable")} • {t("monitoring.platform.receiver")}={entry.receiver} • {t("monitoring.platform.deliveries")}={entry.delivery_count}
                      </div>
                      <div className="otc-monitoring-detail--subtle" data-testid={`platform-alert-timestamps-${entry.id}`}>
                        {t("monitoring.platform.firstReceived")}={formatPlatformTimestamp(entry.first_received_at)} • {t("monitoring.platform.lastReceived")}={formatPlatformTimestamp(entry.last_received_at)}
                      </div>
                      {context.caseId || context.address || context.reportId ? (
                        <div className="otc-monitoring-detail--subtle">
                          case_id={context.caseId || t("common.notAvailable")} • address={context.address || t("common.notAvailable")} • report_id={context.reportId || t("common.notAvailable")}
                        </div>
                      ) : null}
                      {entry.resolved_at ? (
                        <div className="otc-monitoring-detail--subtle">{t("monitoring.platform.resolvedAt")}={entry.resolved_at}</div>
                      ) : null}
                      {entry.triaged_at ? (
                        <div className="otc-monitoring-detail--subtle" data-testid={`platform-alert-triaged-at-${entry.id}`}>
                          {t("monitoring.platform.triagedAt")}={formatPlatformTimestamp(entry.triaged_at)} {t("common.by")} {entry.triaged_by ?? t("monitoring.platform.adminFallback")}
                        </div>
                      ) : null}
                      {entry.triage_note ? (
                        <div className="otc-monitoring-detail--subtle">{t("monitoring.platform.note")}: {entry.triage_note}</div>
                      ) : null}
                      {trackedWorkItem ? (
                        <div className="otc-monitoring-detail--subtle" data-testid={`platform-alert-queue-${entry.id}`}>
                          {t("monitoring.platform.queueLabel" as MessageKey)}{" "}
                          <Pill tone={toneForQueueStatus(trackedWorkItem.queue_status)}>
                            {t(`monitoring.platform.queueStatus.${trackedWorkItem.queue_status.toLowerCase()}` as MessageKey)}
                          </Pill>
                        </div>
                      ) : null}
                      {rcaSummary ? (
                        <div className="otc-monitoring-detail--subtle" data-testid={`platform-alert-rca-summary-${entry.id}`}>
                          {tr("alerts.workspace.rca.inlineSummary" as MessageKey, {
                            domain: rcaSummary.domain || tr("alerts.history.notAvailable" as MessageKey),
                            containment: translateContainmentStatus(rcaSummary.containmentStatus),
                            commander: rcaSummary.incidentCommander || tr("alerts.history.notAvailable" as MessageKey)
                          })}
                          {rcaSummary.affectedDomains.length ? ` • ${tr("alerts.workspace.rca.inlineDomains" as MessageKey)}=${rcaSummary.affectedDomains.join(", ")}` : ""}
                          {rcaSummary.confirmedRootCause
                            ? ` • ${tr("alerts.workspace.rca.inlineConfirmed" as MessageKey)}=${rcaSummary.confirmedRootCause}`
                            : rcaSummary.suspectedRootCause
                              ? ` • ${tr("alerts.workspace.rca.inlineSuspected" as MessageKey)}=${rcaSummary.suspectedRootCause}`
                              : ""}
                        </div>
                      ) : null}
                      {entry.annotations?.summary ? (
                        <div className="otc-monitoring-detail">{String(entry.annotations.summary)}</div>
                      ) : null}
                      {entry.annotations?.description ? (
                        <div className="otc-monitoring-detail--subtle">{String(entry.annotations.description)}</div>
                      ) : null}
                      <details className="otc-monitoring-detail">
                        <summary>{t("monitoring.platform.labels")}</summary>
                        <div data-testid="platform-alert-labels">
                          <CodeBlock>{JSON.stringify(entry.labels, null, 2)}</CodeBlock>
                        </div>
                      </details>
                      <div className="otc-monitoring-actions">
                        {contextLinks.map((link: OperationalContextLink) => (
                          <a key={`${entry.id}-${link.testIdSuffix}`} className="otc-button otc-button--ghost" href={link.href}>
                            {tr(
                              (link.kind === "case"
                                ? "reports.cases.openCase"
                                : link.kind === "audit"
                                  ? "reports.cases.openAudit"
                                  : link.kind === "evidence"
                                    ? "monitoring.alerts.openEvidence"
                                    : link.kind === "investigate"
                                      ? "monitoring.alerts.openInvestigate"
                                      : "monitoring.alerts.openSanctions") as MessageKey
                            )}
                          </a>
                        ))}
                        {canManagePlatformAdmin ? (
                          <>
                            <button
                              type="button"
                              data-testid={`platform-alert-track-btn-${entry.id}`}
                              onClick={() => trackPlatformAlert(entry)}
                              disabled={trackingPlatformAlertId === entry.id}
                              className="otc-button otc-button--ghost"
                            >
                              {trackingPlatformAlertId === entry.id
                                ? t("monitoring.platform.trackWorkItemLoading" as MessageKey)
                                : trackedWorkItem
                                  ? t("monitoring.platform.syncWorkItem" as MessageKey)
                                  : t("monitoring.platform.trackWorkItem" as MessageKey)}
                            </button>
                            <button
                              type="button"
                              data-testid={`platform-alert-ack-btn-${entry.id}`}
                              onClick={() => acknowledgePlatformAlert(entry.id)}
                              disabled={entry.triage_status === "acknowledged" || acknowledgingPlatformAlertId === entry.id}
                              className="otc-button"
                            >
                              {acknowledgingPlatformAlertId === entry.id ? t("monitoring.platform.ackLoading") : t("monitoring.platform.ack")}
                            </button>
                          </>
                        ) : null}
                      </div>
                      {trackedWorkItem ? (
                        <button
                          type="button"
                          className={`otc-button otc-button--ghost${timelineAlertId === entry.id ? " otc-button--active" : ""}`}
                          onClick={() => {
                            setTimelineAlertId(entry.id);
                            void loadTimeline(trackedWorkItem.id);
                          }}
                        >
                          {tr("alerts.workspace.timeline.open" as MessageKey)}
                        </button>
                      ) : null}
                    </div>
                  );
                })()
              ))}
            </div>
          ) : (
            <div data-testid="platform-alert-empty" className="otc-monitoring-banner">
              <Message>{t("monitoring.platform.empty")}</Message>
            </div>
          )
        ) : (
          <div data-testid="platform-alert-loading" className="otc-monitoring-banner">
            <Message>{t("monitoring.platform.loading")}</Message>
          </div>
        )}
          </>
        )}
      </Panel>

      <Panel title={tr("alerts.workspace.rca.title" as MessageKey)} description={tr("alerts.workspace.rca.description" as MessageKey)}>
        {canReadPlatformAdmin === false ? (
          <div data-testid="platform-alert-rca-read-restricted">
            <Message>{t("monitoring.platform.readRestricted" as MessageKey)}</Message>
          </div>
        ) : !timelineAlertId ? (
          <div data-testid="platform-alert-rca-empty-selection">
            <Message>{tr("alerts.workspace.rca.emptySelection" as MessageKey)}</Message>
          </div>
        ) : !selectedTimelineWorkItem ? (
          <div data-testid="platform-alert-rca-local-only">
            <Message>{tr("alerts.workspace.rca.localOnly" as MessageKey)}</Message>
          </div>
        ) : (
          <div data-testid="platform-alert-rca-panel" className="otc-controls otc-controls--spaced">
            <div className="otc-monitoring-detail">
              {tr("alerts.workspace.rca.summary" as MessageKey, {
                alertId: selectedTimelineEntry?.id ?? selectedTimelineWorkItem.resource_id
              })}
            </div>
            <div className="otc-monitoring-detail--subtle" data-testid="platform-alert-rca-badges">
              <Pill tone={toneForQueueStatus(rcaForm.queueStatus)}>
                {tr(`monitoring.platform.queueStatus.${rcaForm.queueStatus.toLowerCase()}` as MessageKey)}
              </Pill>{" "}
              <Pill>{translateContainmentStatus(rcaForm.containmentStatus)}</Pill>
            </div>
            <label>
              {tr("alerts.workspace.rca.queueStatus" as MessageKey)}
              <select
                className="otc-select"
                data-testid="platform-alert-rca-queue-status"
                value={rcaForm.queueStatus}
                onChange={(event) => updateRcaForm("queueStatus", event.target.value as WorkItemQueueStatus)}
              >
                <option value="UNDER_REVIEW">{tr("monitoring.platform.queueStatus.under_review" as MessageKey)}</option>
                <option value="ESCALATED">{tr("monitoring.platform.queueStatus.escalated" as MessageKey)}</option>
                <option value="READY">{tr("monitoring.platform.queueStatus.ready" as MessageKey)}</option>
                <option value="APPROVED">{tr("monitoring.platform.queueStatus.approved" as MessageKey)}</option>
                <option value="SUBMITTED">{tr("monitoring.platform.queueStatus.submitted" as MessageKey)}</option>
                <option value="CLOSED">{tr("monitoring.platform.queueStatus.closed" as MessageKey)}</option>
                <option value="REJECTED">{tr("monitoring.platform.queueStatus.rejected" as MessageKey)}</option>
              </select>
            </label>
            <label>
              {tr("alerts.workspace.rca.domain" as MessageKey)}
              <input
                className="otc-input"
                data-testid="platform-alert-rca-domain"
                value={rcaForm.domain}
                onChange={(event) => updateRcaForm("domain", event.target.value)}
              />
            </label>
            <label>
              {tr("alerts.workspace.rca.affectedDomains" as MessageKey)}
              <input
                className="otc-input"
                data-testid="platform-alert-rca-affected-domains"
                value={rcaForm.affectedDomains}
                onChange={(event) => updateRcaForm("affectedDomains", event.target.value)}
              />
            </label>
            <label>
              {tr("alerts.workspace.rca.incidentCommander" as MessageKey)}
              <input
                className="otc-input"
                data-testid="platform-alert-rca-incident-commander"
                value={rcaForm.incidentCommander}
                onChange={(event) => updateRcaForm("incidentCommander", event.target.value)}
              />
            </label>
            <label>
              {tr("alerts.workspace.rca.containmentStatus" as MessageKey)}
              <select
                className="otc-select"
                data-testid="platform-alert-rca-containment-status"
                value={rcaForm.containmentStatus}
                onChange={(event) => updateRcaForm("containmentStatus", event.target.value as AlertRcaContainmentStatus)}
              >
                {ALERT_RCA_CONTAINMENT_STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {translateContainmentStatus(status)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              {tr("alerts.workspace.rca.runbookRef" as MessageKey)}
              <input
                className="otc-input"
                data-testid="platform-alert-rca-runbook-ref"
                value={rcaForm.runbookRef}
                onChange={(event) => updateRcaForm("runbookRef", event.target.value)}
              />
            </label>
            <label>
              {tr("alerts.workspace.rca.impactSummary" as MessageKey)}
              <textarea
                className="otc-textarea"
                rows={3}
                data-testid="platform-alert-rca-impact-summary"
                value={rcaForm.impactSummary}
                onChange={(event) => updateRcaForm("impactSummary", event.target.value)}
              />
            </label>
            <label>
              {tr("alerts.workspace.rca.suspectedRootCause" as MessageKey)}
              <textarea
                className="otc-textarea"
                rows={3}
                data-testid="platform-alert-rca-suspected-root-cause"
                value={rcaForm.suspectedRootCause}
                onChange={(event) => updateRcaForm("suspectedRootCause", event.target.value)}
              />
            </label>
            <label>
              {tr("alerts.workspace.rca.confirmedRootCause" as MessageKey)}
              <textarea
                className="otc-textarea"
                rows={3}
                data-testid="platform-alert-rca-confirmed-root-cause"
                value={rcaForm.confirmedRootCause}
                onChange={(event) => updateRcaForm("confirmedRootCause", event.target.value)}
              />
            </label>
            <label>
              {tr("alerts.workspace.rca.correctiveActions" as MessageKey)}
              <textarea
                className="otc-textarea"
                rows={2}
                data-testid="platform-alert-rca-corrective-actions"
                value={rcaForm.correctiveActions}
                onChange={(event) => updateRcaForm("correctiveActions", event.target.value)}
              />
            </label>
            <label>
              {tr("alerts.workspace.rca.evidenceRefs" as MessageKey)}
              <textarea
                className="otc-textarea"
                rows={2}
                data-testid="platform-alert-rca-evidence-refs"
                value={rcaForm.evidenceRefs}
                onChange={(event) => updateRcaForm("evidenceRefs", event.target.value)}
              />
            </label>
            {canManagePlatformAdmin ? (
              <div className="otc-controls">
                <button
                  type="button"
                  className="otc-button"
                  data-testid="platform-alert-rca-save"
                  onClick={() => {
                    void saveAlertRca();
                  }}
                  disabled={rcaSaving}
                >
                  {rcaSaving ? tr("alerts.workspace.rca.saving" as MessageKey) : tr("alerts.workspace.rca.save" as MessageKey)}
                </button>
              </div>
            ) : (
              <Message data-testid="platform-alert-rca-mutation-restricted">{t("monitoring.platform.mutationRestricted" as MessageKey)}</Message>
            )}
          </div>
        )}
      </Panel>

      <WorkItemTimelinePanel
        state={!timelineAlertId ? "empty_selection" : !selectedTimelineWorkItem ? "local_only" : "ready"}
        summary={timelineAlertId && selectedTimelineWorkItem ? tr("alerts.workspace.timeline.summary" as MessageKey, { alertId: timelineAlertId }) : null}
        labels={buildWorkItemTimelineLabels(tr, "alerts.workspace.timeline")}
        timelineError={timelineError}
        timelineData={timelineData}
        timelineLoading={timelineLoading}
        commentType={commentType}
        commentBody={commentBody}
        commentSubmitting={commentSubmitting}
        onCommentTypeChange={setCommentType}
        onCommentBodyChange={setCommentBody}
        onCommentSubmit={() => {
          void submitTimelineComment(selectedTimelineWorkItem?.id);
        }}
        onRefresh={
          selectedTimelineWorkItem
            ? () => { void loadTimeline(selectedTimelineWorkItem.id); }
            : undefined
        }
        formatDate={(value) => formatDate(value, locale)}
        formatEventLabel={formatTimelineEvent}
      />

      {Object.keys(platformAlertWorkItems).length ? (
        <Panel title={tr("alerts.history.title" as MessageKey)} description={tr("alerts.history.description" as MessageKey)}>
          <table className="otc-table otc-table--spaced">
            <thead>
              <tr>
                <th>{tr("alerts.history.alertname" as MessageKey)}</th>
                <th>{tr("alerts.history.service" as MessageKey)}</th>
                <th>{tr("alerts.history.severity" as MessageKey)}</th>
                <th>{tr("alerts.history.status" as MessageKey)}</th>
                <th>{tr("alerts.history.queueStatus" as MessageKey)}</th>
                <th>{tr("alerts.history.rca" as MessageKey)}</th>
              </tr>
            </thead>
            <tbody>
              {Object.values(platformAlertWorkItems)
                .sort((a, b) =>
                  (b.last_activity_at || b.updated_at || "").localeCompare(a.last_activity_at || a.updated_at || "")
                )
                .slice(0, 100)
                .map((item) => {
                  const meta = (item.metadata ?? {}) as Record<string, unknown>;
                  const rcaSummary = buildAlertRcaSummary(item);
                  const alertname = typeof meta["alertname"] === "string" ? meta["alertname"] : item.resource_id;
                  const service = typeof meta["service"] === "string" ? meta["service"] : null;
                  const severity = typeof meta["severity"] === "string" ? meta["severity"] : null;
                  return (
                    <tr key={String(item.id)} className="otc-row-clickable">
                      <td><strong>{alertname}</strong></td>
                      <td>{service ?? tr("alerts.history.notAvailable" as MessageKey)}</td>
                      <td>
                        {severity ? (
                          <Pill tone={severity === "critical" ? "danger" : severity === "warning" ? "warning" : undefined}>
                            {severity}
                          </Pill>
                        ) : (
                          tr("alerts.history.notAvailable" as MessageKey)
                        )}
                      </td>
                      <td>
                        <Pill tone={toneForQueueStatus(item.queue_status)}>
                          {item.queue_status}
                        </Pill>
                      </td>
                      <td data-testid={`platform-alert-history-rca-${item.resource_id}`}>
                        {rcaSummary ? (
                          <>
                            <div>
                              <strong>{rcaSummary.domain || tr("alerts.history.notAvailable" as MessageKey)}</strong> •{" "}
                              {translateContainmentStatus(rcaSummary.containmentStatus)}
                            </div>
                            <div className="otc-monitoring-detail--subtle">
                              {rcaSummary.confirmedRootCause ||
                                rcaSummary.suspectedRootCause ||
                                rcaSummary.impactSummary ||
                                rcaSummary.incidentCommander ||
                                tr("alerts.history.notAvailable" as MessageKey)}
                            </div>
                          </>
                        ) : (
                          tr("alerts.history.rcaEmpty" as MessageKey)
                        )}
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </Panel>
      ) : null}

      {platformAlertConfirmDialog ? (
        <ConfirmDialog
          open
          title={platformAlertConfirmDialog.title}
          description={platformAlertConfirmDialog.description}
          confirmLabel={platformAlertConfirmDialog.confirmLabel}
          cancelLabel={platformAlertConfirmDialog.cancelLabel}
          onCancel={cancelPlatformAlertConfirmation}
          onConfirm={() => {
            confirmPlatformAlertConfirmation().catch(() => undefined);
          }}
          tone={platformAlertConfirmDialog.tone}
          busy={acknowledgingPlatformAlertsBatch}
          testId={platformAlertConfirmDialog.testId}
        />
      ) : null}
    </AppShell>
  );
}

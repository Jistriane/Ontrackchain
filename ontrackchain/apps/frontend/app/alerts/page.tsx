"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import { useI18n } from "../../components/i18n-provider";
import type { MessageKey } from "../lib/i18n";
import { fetchAuthContext, resolveOwnerUserId, type AuthContext } from "../lib/ownership";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { WorkItemTimelinePanel } from "../../components/work-item-timeline-panel";
import { buildWorkItemTimelineLabels } from "../lib/work-item-timeline-labels";
import { createWorkItemComment, fetchWorkItemTimeline } from "../lib/work-item-timeline-client";
import { formatTimelineEvent, type WorkCommentResponse, type WorkItemTimelineResponse } from "../lib/work-item-timeline";
import {
  buildAuditHref,
  buildCaseHref,
  buildEvidenceHref,
  buildInvestigateHref,
  buildSanctionsHref,
  inferAlertOperationalContext
} from "../lib/operational-context";

const PLATFORM_ALERT_SELECTION_STORAGE_KEY = "monitoring-platform-alert-selection";

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

type PlatformOperationalAlertFilterOptions = {
  services: string[];
  receivers: string[];
  generated_at: string;
};

type PlatformAlertExportFormat = "csv" | "json";
type WorkItemPriority = "critical" | "high" | "normal";
type WorkItemQueueStatus = "UNDER_REVIEW" | "ESCALATED" | "READY" | "APPROVED" | "SUBMITTED" | "CLOSED" | "REJECTED";

type WorkItemResponse = {
  id: string;
  resource_id: string;
  owner_user_id?: string | null;
  queue_status: WorkItemQueueStatus;
  priority: WorkItemPriority;
  note: string | null;
  metadata: Record<string, unknown>;
};

type WorkItemListResponse = {
  data: WorkItemResponse[];
};

const WORK_ITEMS_LIMIT = 100;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

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

export default function AlertsPage() {
  const { t } = useI18n();
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
  const [platformAlertWorkItems, setPlatformAlertWorkItems] = useState<Record<string, WorkItemResponse>>({});
  const [trackingPlatformAlertId, setTrackingPlatformAlertId] = useState<string | null>(null);
  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [timelineAlertId, setTimelineAlertId] = useState<string | null>(null);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineError, setTimelineError] = useState<string | null>(null);
  const [timelineData, setTimelineData] = useState<WorkItemTimelineResponse<WorkItemResponse> | null>(null);
  const [commentType, setCommentType] = useState<WorkCommentResponse["comment_type"]>("note");
  const [commentBody, setCommentBody] = useState("");
  const [commentSubmitting, setCommentSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const platformAlertsRequestIdRef = useRef(0);

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

  function buildPlatformAlertSelectionScope(
    status = platformAlertStatusFilter,
    triageStatus = platformAlertTriageFilter,
    service = platformAlertServiceFilter,
    receiver = platformAlertReceiverFilter,
    severity = platformAlertSeverityFilter
  ) {
    return JSON.stringify({ status, triageStatus, service, receiver, severity });
  }

  function filtersFromSearchParams() {
    return {
      status: searchParams.get("status") ?? "all",
      triageStatus: searchParams.get("triage_status") ?? "all",
      service: searchParams.get("service") ?? "all",
      receiver: searchParams.get("receiver") ?? "all",
      severity: searchParams.get("severity") ?? "all"
    };
  }

  function clearPersistedPlatformAlertSelection() {
    if (typeof window === "undefined") {
      return;
    }
    window.sessionStorage.removeItem(PLATFORM_ALERT_SELECTION_STORAGE_KEY);
  }

  function persistPlatformAlertSelection(scope: string | null, selectedIds: string[]) {
    if (typeof window === "undefined") {
      return;
    }
    window.sessionStorage.setItem(
      PLATFORM_ALERT_SELECTION_STORAGE_KEY,
      JSON.stringify({
        saved_at: new Date().toISOString(),
        scope,
        selected_ids: selectedIds
      })
    );
  }

  function hydratePersistedPlatformAlertSelection(scope: string | null) {
    if (typeof window === "undefined") {
      return;
    }
    const raw = window.sessionStorage.getItem(PLATFORM_ALERT_SELECTION_STORAGE_KEY);
    if (!raw) {
      return;
    }
    try {
      const parsed = JSON.parse(raw) as { scope?: string; selected_ids?: unknown };
      if (parsed.scope && parsed.scope === scope && Array.isArray(parsed.selected_ids)) {
        setSelectedPlatformAlertIds(parsed.selected_ids.filter((entry) => typeof entry === "string") as string[]);
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
    const res = await fetch("/api/app/monitoring/operational-alert-filter-options", { cache: "no-store" });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      setError(t("monitoring.errors.loadPlatformFilterOptions"));
      return;
    }
    setPlatformAlertFilterOptions(data as PlatformOperationalAlertFilterOptions);
  }

  async function loadPlatformAlertWorkItems() {
    const res = await fetch(
      `/api/app/operations/work-items?module=alerts&resource_type=operational_alert&limit=${WORK_ITEMS_LIMIT}`,
      { cache: "no-store" }
    );
    const data = (await res.json().catch(() => null)) as WorkItemListResponse | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      return;
    }

    const items = data && "data" in data && Array.isArray(data.data) ? data.data : [];
    const nextMap = items.reduce<Record<string, WorkItemResponse>>((accumulator, item) => {
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
    const nextScope = buildPlatformAlertSelectionScope(status, triageStatus, service, receiver, severity);
    setPlatformAlertSelectionScope((currentScope) => {
      if (currentScope && currentScope !== nextScope) {
        setSelectedPlatformAlertIds([]);
      }
      return nextScope;
    });
  }

  async function refreshPlatformOperationalAlerts() {
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
    setPlatformAlertStatusFilter(value);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    await loadPlatformOperationalAlerts(value, platformAlertTriageFilter, platformAlertServiceFilter, platformAlertReceiverFilter, platformAlertSeverityFilter, null);
  }

  async function handlePlatformAlertTriageFilterChange(value: string) {
    setPlatformAlertTriageFilter(value);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    await loadPlatformOperationalAlerts(platformAlertStatusFilter, value, platformAlertServiceFilter, platformAlertReceiverFilter, platformAlertSeverityFilter, null);
  }

  async function handlePlatformAlertServiceFilterChange(value: string) {
    setPlatformAlertServiceFilter(value);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    await loadPlatformOperationalAlerts(platformAlertStatusFilter, platformAlertTriageFilter, value, platformAlertReceiverFilter, platformAlertSeverityFilter, null);
  }

  async function handlePlatformAlertReceiverFilterChange(value: string) {
    setPlatformAlertReceiverFilter(value);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    await loadPlatformOperationalAlerts(platformAlertStatusFilter, platformAlertTriageFilter, platformAlertServiceFilter, value, platformAlertSeverityFilter, null);
  }

  async function handlePlatformAlertSeverityFilterChange(value: string) {
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
    if (!eventId) {
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
        await syncPlatformAlertWorkItem(currentEntry, "CLOSED");
      } catch (syncError) {
        setError(syncError instanceof Error ? syncError.message : t("monitoring.errors.trackPlatformAlert" as MessageKey));
      }
    }
    setPlatformAlertMessage(t("monitoring.platform.messageAckSingle", { eventId, status: body?.triage_status ?? "acknowledged" }));
    setAcknowledgingPlatformAlertId(null);
    setSelectedPlatformAlertIds((current) => current.filter((entry) => entry !== eventId));
    await refreshPlatformOperationalAlerts();
  }

  async function acknowledgeFilteredPlatformAlerts() {
    if (!platformOperationalAlerts?.total_count) {
      return;
    }
    const confirmed = window.confirm(t("monitoring.platform.confirmFiltered"));
    if (!confirmed) {
      return;
    }
    setAcknowledgingPlatformAlertsBatch(true);
    setError(null);
    setPlatformAlertMessage(null);
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
      setAcknowledgingPlatformAlertsBatch(false);
      return;
    }
    const data = await res.json().catch(() => null);
    const updatedCount = typeof data?.updated_count === "number" ? data.updated_count : 0;
    setPlatformAlertMessage(
      updatedCount ? t("monitoring.platform.messageAckBatchDone", { count: updatedCount }) : t("monitoring.platform.messageAckBatchEmpty")
    );
    setAcknowledgingPlatformAlertsBatch(false);
    clearPersistedPlatformAlertSelection();
    setSelectedPlatformAlertIds([]);
    await refreshPlatformOperationalAlerts();
  }

  async function acknowledgeSelectedPlatformAlerts() {
    if (!selectedPlatformAlertIds.length) {
      return;
    }
    const confirmed = window.confirm(t("monitoring.platform.confirmSelected", { count: selectedPlatformAlertIds.length }));
    if (!confirmed) {
      return;
    }
    setAcknowledgingPlatformAlertsBatch(true);
    setError(null);
    setPlatformAlertMessage(null);
    const res = await fetch("/api/app/monitoring/operational-alerts/acknowledge-batch", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        ids: selectedPlatformAlertIds,
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
      setAcknowledgingPlatformAlertsBatch(false);
      return;
    }
    const data = await res.json().catch(() => null);
    const updatedCount = typeof data?.updated_count === "number" ? data.updated_count : 0;
    setPlatformAlertMessage(
      updatedCount ? t("monitoring.platform.messageAckSelectedDone", { count: updatedCount }) : t("monitoring.platform.messageAckSelectedEmpty")
    );
    setAcknowledgingPlatformAlertsBatch(false);
    clearPersistedPlatformAlertSelection();
    setSelectedPlatformAlertIds([]);
    await refreshPlatformOperationalAlerts();
  }

  function resolveDownloadFilename(contentDisposition: string | null, fallbackName: string) {
    if (!contentDisposition) {
      return fallbackName;
    }
    const match = /filename="([^"]+)"/i.exec(contentDisposition);
    return match?.[1] ?? fallbackName;
  }

  async function exportPlatformAlerts(scope: "filtered" | "selected") {
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
    entry: PlatformOperationalAlertsSnapshot["data"][number],
    nextStatus?: WorkItemQueueStatus
  ) {
    const existing = platformAlertWorkItems[entry.id];
    const context = inferAlertOperationalContext(entry);
    const ownerUserId = resolveOwnerUserId({
      existingOwnerUserId: existing?.owner_user_id,
      linkedUserId: authContext?.linked_user_id,
      isUuidLike
    });
    const queueStatus =
      nextStatus ??
      existing?.queue_status ??
      (entry.triage_status === "acknowledged" || entry.status === "resolved" ? "CLOSED" : "UNDER_REVIEW");
    const requestBody = existing
      ? {
          ...(ownerUserId ? { owner_user_id: ownerUserId } : {}),
          priority: priorityFromSeverity(entry.severity),
          queue_status: queueStatus,
          title: `Alert ${entry.alertname}`,
          note: entry.triage_note ?? existing.note,
          metadata: {
            ...(existing.metadata ?? {}),
            alertname: entry.alertname,
            receiver: entry.receiver,
            service: entry.service,
            severity: entry.severity,
            fingerprint: entry.fingerprint,
            first_received_at: entry.first_received_at,
            last_received_at: entry.last_received_at,
            delivery_count: entry.delivery_count,
            triage_status: entry.triage_status,
            triaged_at: entry.triaged_at,
            triaged_by: entry.triaged_by,
            triage_note: entry.triage_note,
            case_id: context.caseId,
            address: context.address,
            report_id: context.reportId
          }
        }
      : {
          module: "alerts",
          resource_type: "operational_alert",
          resource_id: entry.id,
          ...(isUuidLike(context.caseId) ? { case_id: context.caseId?.trim() } : {}),
          ...(ownerUserId ? { owner_user_id: ownerUserId } : {}),
          priority: priorityFromSeverity(entry.severity),
          queue_status: queueStatus,
          title: `Alert ${entry.alertname}`,
          note: entry.triage_note,
          metadata: {
            alertname: entry.alertname,
            receiver: entry.receiver,
            service: entry.service,
            severity: entry.severity,
            fingerprint: entry.fingerprint,
            first_received_at: entry.first_received_at,
            last_received_at: entry.last_received_at,
            delivery_count: entry.delivery_count,
            triage_status: entry.triage_status,
            triaged_at: entry.triaged_at,
            triaged_by: entry.triaged_by,
            triage_note: entry.triage_note,
            case_id: context.caseId,
            address: context.address,
            report_id: context.reportId
          }
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
    const data = (await res.json().catch(() => null)) as WorkItemResponse | { error?: string; detail?: unknown } | null;
    setTrackingPlatformAlertId(null);
    if (!res.ok) {
      throw new Error(resolveApiErrorMessage(t, data, t("monitoring.errors.trackPlatformAlert" as MessageKey)));
    }

    const workItem = data as WorkItemResponse;
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
    loadPlatformOperationalAlertFilterOptions().catch(() => undefined);

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
  }, [searchParams]);

  useEffect(() => {
    if (platformAlertSelectionHydrated) {
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

  async function loadTimeline(workItemId: string) {
    setTimelineLoading(true);
    setTimelineError(null);
    const result = await fetchWorkItemTimeline<WorkItemResponse>(workItemId);
    if (!result.ok) {
      setTimelineData(null);
      setTimelineError(resolveApiErrorMessage(t, result.error, tr("alerts.workspace.timeline.errorLoad" as MessageKey)));
      setTimelineLoading(false);
      return;
    }
    setTimelineData(result.data);
    setTimelineLoading(false);
  }

  async function submitTimelineComment() {
    if (!selectedTimelineWorkItem || !commentBody.trim()) return;
    setCommentSubmitting(true);
    const result = await createWorkItemComment(selectedTimelineWorkItem.id, {
      comment_type: commentType,
      body: commentBody.trim()
    });
    setCommentSubmitting(false);
    if (!result.ok) {
      setTimelineError(resolveApiErrorMessage(t, result.error, tr("alerts.workspace.timeline.errorComment" as MessageKey)));
      return;
    }
    setCommentBody("");
    await loadTimeline(selectedTimelineWorkItem.id);
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
              {platformOperationalAlerts.data.map((entry) => (
                (() => {
                  const context = inferAlertOperationalContext(entry);
                  const trackedWorkItem = platformAlertWorkItems[entry.id];
                  const caseHref = buildCaseHref(context.caseId);
                  const investigateHref = buildInvestigateHref(context, { includeCaseId: true });
                  const sanctionsHref = buildSanctionsHref(context);
                  const auditHref = buildAuditHref(context, { fallbackResourceType: "operational_alert", preferCaseResource: true });
                  const evidenceHref = buildEvidenceHref(context, { domain: "all", fallbackResourceType: "operational_alert", preferCaseResource: true });

                  return (
                    <div
                      key={entry.id}
                      data-testid="platform-alert-row"
                      className={`otc-monitoring-card ${entry.status === "firing" ? "otc-monitoring-card--warning" : "otc-monitoring-card--success"}`}
                    >
                      <div className="otc-monitoring-row">
                        <div className="otc-monitoring-inline">
                          <input
                            type="checkbox"
                            data-testid={`platform-alert-select-${entry.id}`}
                            aria-label={t("monitoring.platform.selectOneAria", { name: entry.alertname })}
                            checked={selectedPlatformAlertIds.includes(entry.id)}
                            disabled={entry.triage_status !== "pending" || acknowledgingPlatformAlertsBatch}
                            onChange={() => togglePlatformAlertSelection(entry.id)}
                          />
                          <strong>{entry.alertname}</strong>
                        </div>
                        <span>
                          {translatePlatformSeverity(entry.severity)} • {translatePlatformStatus(entry.status)} • {t("monitoring.platform.triageLabel")}={translatePlatformTriage(entry.triage_status)}
                        </span>
                      </div>
                      <div className="otc-monitoring-detail">
                        {t("monitoring.platform.service")}={entry.service ?? t("common.notAvailable")} • {t("monitoring.platform.receiver")}={entry.receiver} • {t("monitoring.platform.deliveries")}={entry.delivery_count}
                      </div>
                      <div className="otc-monitoring-detail--subtle">
                        {t("monitoring.platform.firstReceived")}={entry.first_received_at} • {t("monitoring.platform.lastReceived")}={entry.last_received_at}
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
                        <div className="otc-monitoring-detail--subtle">
                          {t("monitoring.platform.triagedAt")}={entry.triaged_at} {t("common.by")} {entry.triaged_by ?? t("monitoring.platform.adminFallback")}
                        </div>
                      ) : null}
                      {entry.triage_note ? (
                        <div className="otc-monitoring-detail--subtle">{t("monitoring.platform.note")}: {entry.triage_note}</div>
                      ) : null}
                      {trackedWorkItem ? (
                        <div className="otc-monitoring-detail--subtle">
                          {t("monitoring.platform.queueLabel" as MessageKey)}{" "}
                          <Pill tone={toneForQueueStatus(trackedWorkItem.queue_status)}>
                            {t(`monitoring.platform.queueStatus.${trackedWorkItem.queue_status.toLowerCase()}` as MessageKey)}
                          </Pill>
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
                        {caseHref ? (
                          <a className="otc-button otc-button--ghost" href={caseHref}>
                            {tr("reports.cases.openCase" as MessageKey)}
                          </a>
                        ) : null}
                        <a className="otc-button otc-button--ghost" href={auditHref}>
                          {tr("reports.cases.openAudit" as MessageKey)}
                        </a>
                        <a className="otc-button otc-button--ghost" href={evidenceHref}>
                          {tr("monitoring.alerts.openEvidence" as MessageKey)}
                        </a>
                        {investigateHref ? (
                          <a className="otc-button otc-button--ghost" href={investigateHref}>
                            {tr("monitoring.alerts.openInvestigate" as MessageKey)}
                          </a>
                        ) : null}
                        {sanctionsHref ? (
                          <a className="otc-button otc-button--ghost" href={sanctionsHref}>
                            {tr("monitoring.alerts.openSanctions" as MessageKey)}
                          </a>
                        ) : null}
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
        onCommentSubmit={() => { void submitTimelineComment(); }}
        onRefresh={
          selectedTimelineWorkItem
            ? () => { void loadTimeline(selectedTimelineWorkItem.id); }
            : undefined
        }
        formatDate={(value) => {
          if (!value) return null;
          const parsed = new Date(value);
          if (Number.isNaN(parsed.getTime())) return value;
          return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(parsed);
        }}
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
                      <td>{item.note ?? tr("alerts.history.notAvailable" as MessageKey)}</td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </Panel>
      ) : null}
    </AppShell>
  );
}

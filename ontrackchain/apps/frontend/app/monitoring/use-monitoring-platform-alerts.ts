"use client";

import { useEffect, useRef, useState } from "react";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import {
  fetchMonitoringMetricsPreview,
  fetchMonitoringPlatformAlertFilterOptions,
  fetchMonitoringPlatformOperationalAlerts
} from "../lib/monitoring-api";
import {
  buildPlatformAlertSelectionScope,
  clearPersistedPlatformAlertSelection,
  resolveInitialPlatformAlertSelectionState,
  shouldPersistPlatformAlertSelection,
  writePersistedPlatformAlertSelection,
  type PlatformAlertExportFormat,
  type PlatformAlertFilterState,
  type PlatformOperationalAlertFilterOptions,
  type PlatformOperationalAlertsSnapshot
} from "../lib/monitoring-platform-alerts";
import type { MessageKey } from "../lib/i18n";
import type { AlertsWorkItemMetadata, WorkItemListResponse, WorkItemResponse } from "../lib/work-items";

type Translator = (key: MessageKey, values?: Record<string, string | number>) => string;

type UseMonitoringPlatformAlertsArgs = {
  t: Translator;
  setError: (message: string | null) => void;
};

function buildDynamicFilterValues(currentValue: string, values: string[] | undefined) {
  const merged = new Set((values ?? []).filter((entry) => entry && entry !== "all"));
  if (currentValue !== "all") {
    merged.add(currentValue);
  }
  return Array.from(merged).sort((left, right) => left.localeCompare(right));
}

function resolveDownloadFilename(contentDisposition: string | null, fallbackName: string) {
  if (!contentDisposition) {
    return fallbackName;
  }
  const match = /filename="([^"]+)"/i.exec(contentDisposition);
  return match?.[1] ?? fallbackName;
}

export function useMonitoringPlatformAlerts({ t, setError }: UseMonitoringPlatformAlertsArgs) {
  const [platformOperationalAlerts, setPlatformOperationalAlerts] = useState<PlatformOperationalAlertsSnapshot | null>(null);
  const [platformAlertTrackedWorkItems, setPlatformAlertTrackedWorkItems] = useState<Record<string, WorkItemResponse<AlertsWorkItemMetadata>>>({});
  const [metricsText, setMetricsText] = useState("");
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
  const platformAlertsRequestIdRef = useRef(0);

  function currentPlatformAlertFilters(
    status = platformAlertStatusFilter,
    triageStatus = platformAlertTriageFilter,
    service = platformAlertServiceFilter,
    receiver = platformAlertReceiverFilter,
    severity = platformAlertSeverityFilter
  ): PlatformAlertFilterState {
    return { status, triageStatus, service, receiver, severity };
  }

  async function loadPlatformOperationalAlertFilterOptions() {
    try {
      const data = await fetchMonitoringPlatformAlertFilterOptions();
      setPlatformAlertFilterOptions(data);
    } catch {
      setError(t("monitoring.errors.loadPlatformFilterOptions"));
    }
  }

  async function loadPlatformOperationalAlerts(
    status = platformAlertStatusFilter,
    triageStatus = platformAlertTriageFilter,
    service = platformAlertServiceFilter,
    receiver = platformAlertReceiverFilter,
    severity = platformAlertSeverityFilter,
    cursor = platformAlertCursor
  ) {
    const requestId = platformAlertsRequestIdRef.current + 1;
    platformAlertsRequestIdRef.current = requestId;
    try {
      const data = await fetchMonitoringPlatformOperationalAlerts(
        currentPlatformAlertFilters(status, triageStatus, service, receiver, severity),
        cursor
      );
      if (requestId !== platformAlertsRequestIdRef.current) {
        return;
      }
      setPlatformOperationalAlerts(data);
      const workItemsResponse = await fetch("/api/app/operations/work-items?module=alerts&resource_type=operational_alert&limit=100", {
        cache: "no-store"
      });
      const workItemsData = (await workItemsResponse.json().catch(() => null)) as WorkItemListResponse<AlertsWorkItemMetadata> | null;
      if (!workItemsResponse.ok) {
        setError(t("monitoring.errors.loadPlatformTrackedAlerts" as MessageKey));
      } else {
        const nextTrackedItems = Object.fromEntries(
          (workItemsData?.data ?? []).map((item) => [item.resource_id, item] satisfies [string, WorkItemResponse<AlertsWorkItemMetadata>])
        );
        setPlatformAlertTrackedWorkItems(nextTrackedItems);
      }
    } catch {
      if (requestId !== platformAlertsRequestIdRef.current) {
        return;
      }
      setError(t("monitoring.errors.loadPlatformAlerts"));
      return;
    }
    const nextScope = buildPlatformAlertSelectionScope(
      currentPlatformAlertFilters(status, triageStatus, service, receiver, severity)
    );
    setPlatformAlertSelectionScope((currentScope) => {
      if (currentScope && currentScope !== nextScope) {
        setSelectedPlatformAlertIds([]);
      }
      return nextScope;
    });
  }

  async function refreshMetricsPreview() {
    setError(null);
    try {
      const text = await fetchMonitoringMetricsPreview();
      setMetricsText(text);
    } catch {
      setError(t("monitoring.errors.loadMetrics"));
    }
  }

  useEffect(() => {
    const initialSelection = resolveInitialPlatformAlertSelectionState(
      typeof window !== "undefined" ? window.sessionStorage : null
    );
    setPlatformAlertStatusFilter(initialSelection.status);
    setPlatformAlertTriageFilter(initialSelection.triageStatus);
    setPlatformAlertServiceFilter(initialSelection.service);
    setPlatformAlertReceiverFilter(initialSelection.receiver);
    setPlatformAlertSeverityFilter(initialSelection.severity);
    setPlatformAlertCursor(initialSelection.cursor);
    setPlatformAlertCursorHistory(initialSelection.cursorHistory);
    setSelectedPlatformAlertIds(initialSelection.selectedIds);
    setPlatformAlertSelectionScope(initialSelection.selectionScope);

    loadPlatformOperationalAlertFilterOptions().catch(() => setError(t("monitoring.errors.loadPlatformFilterOptions")));
    loadPlatformOperationalAlerts(
      initialSelection.status,
      initialSelection.triageStatus,
      initialSelection.service,
      initialSelection.receiver,
      initialSelection.severity,
      initialSelection.cursor
    )
      .catch(() => setError(t("monitoring.errors.loadPlatformAlerts")))
      .finally(() => setPlatformAlertSelectionHydrated(true));
    refreshMetricsPreview().catch(() => setError(t("monitoring.errors.loadMetrics")));
  }, [t]);

  useEffect(() => {
    if (!platformAlertSelectionHydrated || typeof window === "undefined") {
      return;
    }

    const persistedState = {
      ...currentPlatformAlertFilters(),
      cursor: platformAlertCursor,
      cursorHistory: platformAlertCursorHistory,
      selectedIds: selectedPlatformAlertIds,
      selectionScope: platformAlertSelectionScope
    };

    if (!shouldPersistPlatformAlertSelection(persistedState)) {
      clearPersistedPlatformAlertSelection(window.sessionStorage);
      return;
    }

    writePersistedPlatformAlertSelection(window.sessionStorage, persistedState);
  }, [
    platformAlertSelectionHydrated,
    platformAlertStatusFilter,
    platformAlertTriageFilter,
    platformAlertServiceFilter,
    platformAlertReceiverFilter,
    platformAlertSeverityFilter,
    platformAlertCursor,
    platformAlertCursorHistory,
    selectedPlatformAlertIds,
    platformAlertSelectionScope
  ]);

  const platformAlertServiceOptions = buildDynamicFilterValues(
    platformAlertServiceFilter,
    platformAlertFilterOptions?.services
  );
  const platformAlertReceiverOptions = buildDynamicFilterValues(
    platformAlertReceiverFilter,
    platformAlertFilterOptions?.receivers
  );
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

  async function refreshPlatformOperationalAlerts() {
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

  async function goToNextPlatformAlertsPage() {
    const nextCursor = platformOperationalAlerts?.next_cursor;
    if (!nextCursor) {
      return;
    }
    setError(null);
    setPlatformAlertCursorHistory((current) => [...current, platformAlertCursor]);
    setPlatformAlertCursor(nextCursor);
    await loadPlatformOperationalAlerts(
      platformAlertStatusFilter,
      platformAlertTriageFilter,
      platformAlertServiceFilter,
      platformAlertReceiverFilter,
      platformAlertSeverityFilter,
      nextCursor
    );
  }

  async function goToPreviousPlatformAlertsPage() {
    if (!platformAlertCursorHistory.length) {
      return;
    }
    setError(null);
    const previousCursor = platformAlertCursorHistory[platformAlertCursorHistory.length - 1] ?? null;
    setPlatformAlertCursorHistory((current) => current.slice(0, -1));
    setPlatformAlertCursor(previousCursor);
    await loadPlatformOperationalAlerts(
      platformAlertStatusFilter,
      platformAlertTriageFilter,
      platformAlertServiceFilter,
      platformAlertReceiverFilter,
      platformAlertSeverityFilter,
      previousCursor
    );
  }

  async function acknowledgePlatformAlert(eventId: string) {
    setError(null);
    setPlatformAlertMessage(null);
    setAcknowledgingPlatformAlertId(eventId);
    try {
      const res = await fetch(`/api/app/monitoring/operational-alerts/${eventId}/acknowledge`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ note: "ack_from_monitoring_ui", triaged_by: "admin_ui" }),
        cache: "no-store"
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        setError(resolveApiErrorMessage(t, data, t("monitoring.errors.ackPlatformAlert")));
        return;
      }
      setPlatformAlertMessage(t("monitoring.platform.messageAckSingle", { eventId, status: data?.triage_status ?? "acknowledged" }));
      setSelectedPlatformAlertIds((current) => current.filter((entryId) => entryId !== eventId));
      await Promise.all([refreshPlatformOperationalAlerts(), refreshMetricsPreview()]);
    } finally {
      setAcknowledgingPlatformAlertId(null);
    }
  }

  async function acknowledgeFilteredPlatformAlerts() {
    if (!platformOperationalAlerts?.total_count) {
      return;
    }
    const confirmed = window.confirm(t("monitoring.platform.confirmFiltered"));
    if (!confirmed) {
      return;
    }

    setError(null);
    setPlatformAlertMessage(null);
    setAcknowledgingPlatformAlertsBatch(true);
    try {
      const res = await fetch("/api/app/monitoring/operational-alerts/acknowledge-batch", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          note: "ack_batch_from_monitoring_ui",
          triaged_by: "admin_ui",
          status: platformAlertStatusFilter === "all" ? null : platformAlertStatusFilter,
          triage_status: platformAlertTriageFilter === "all" ? null : platformAlertTriageFilter,
          service: platformAlertServiceFilter === "all" ? null : platformAlertServiceFilter,
          receiver: platformAlertReceiverFilter === "all" ? null : platformAlertReceiverFilter,
          severity: platformAlertSeverityFilter === "all" ? null : platformAlertSeverityFilter
        }),
        cache: "no-store"
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        setError(resolveApiErrorMessage(t, data, t("monitoring.errors.ackPlatformAlertsBatch")));
        return;
      }
      const updatedCount = typeof data?.updated_count === "number" ? data.updated_count : 0;
      setPlatformAlertMessage(
        updatedCount
          ? t("monitoring.platform.messageAckBatchDone", { count: updatedCount })
          : t("monitoring.platform.messageAckBatchEmpty")
      );
      setSelectedPlatformAlertIds([]);
      await Promise.all([refreshPlatformOperationalAlerts(), refreshMetricsPreview()]);
    } finally {
      setAcknowledgingPlatformAlertsBatch(false);
    }
  }

  function togglePlatformAlertSelection(eventId: string) {
    setSelectedPlatformAlertIds((current) =>
      current.includes(eventId) ? current.filter((entryId) => entryId !== eventId) : [...current, eventId]
    );
  }

  function toggleAllSelectablePlatformAlerts() {
    setSelectedPlatformAlertIds((current) => {
      if (allSelectablePlatformAlertsSelected) {
        return current.filter((entryId) => !selectablePlatformAlertIds.includes(entryId));
      }
      return Array.from(new Set([...current, ...selectablePlatformAlertIds]));
    });
  }

  async function acknowledgeSelectedPlatformAlerts() {
    if (!selectedPlatformAlertIds.length) {
      return;
    }
    const confirmed = window.confirm(t("monitoring.platform.confirmSelected", { count: selectedPlatformAlertIds.length }));
    if (!confirmed) {
      return;
    }

    setError(null);
    setPlatformAlertMessage(null);
    setAcknowledgingPlatformAlertsBatch(true);
    try {
      const res = await fetch("/api/app/monitoring/operational-alerts/acknowledge-batch", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          ids: selectedPlatformAlertIds,
          note: "ack_selected_from_monitoring_ui",
          triaged_by: "admin_ui",
          status: platformAlertStatusFilter === "all" ? null : platformAlertStatusFilter,
          triage_status: platformAlertTriageFilter === "all" ? null : platformAlertTriageFilter,
          service: platformAlertServiceFilter === "all" ? null : platformAlertServiceFilter,
          receiver: platformAlertReceiverFilter === "all" ? null : platformAlertReceiverFilter,
          severity: platformAlertSeverityFilter === "all" ? null : platformAlertSeverityFilter
        }),
        cache: "no-store"
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        setError(resolveApiErrorMessage(t, data, t("monitoring.errors.ackPlatformAlertsSelected")));
        return;
      }
      const updatedCount = typeof data?.updated_count === "number" ? data.updated_count : 0;
      setPlatformAlertMessage(
        updatedCount
          ? t("monitoring.platform.messageAckSelectedDone", { count: updatedCount })
          : t("monitoring.platform.messageAckSelectedEmpty")
      );
      setSelectedPlatformAlertIds([]);
      await Promise.all([refreshPlatformOperationalAlerts(), refreshMetricsPreview()]);
    } finally {
      setAcknowledgingPlatformAlertsBatch(false);
    }
  }

  async function exportPlatformAlerts(scope: "filtered" | "selected") {
    if (scope === "selected" && !selectedPlatformAlertIds.length) {
      setError(t("monitoring.platform.selectAtLeastOne"));
      return;
    }

    setError(null);
    setPlatformAlertMessage(null);
    setExportingPlatformAlerts(scope);
    try {
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
        return;
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const filename = resolveDownloadFilename(
        res.headers.get("content-disposition"),
        `operational-alerts-${scope}.${platformAlertExportFormat}`
      );
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
      setPlatformAlertMessage(
        scope === "selected"
          ? t("monitoring.platform.messageExportSelected", { count: selectedPlatformAlertIds.length })
          : t("monitoring.platform.messageExportFiltered")
      );
    } catch {
      setError(t("monitoring.errors.exportPlatformAlerts"));
    } finally {
      setExportingPlatformAlerts(null);
    }
  }

  function resetPlatformAlertViewState() {
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    setSelectedPlatformAlertIds([]);
    setPlatformAlertSelectionScope(null);
  }

  function handlePlatformAlertStatusFilterChange(value: string) {
    setPlatformAlertStatusFilter(value);
    resetPlatformAlertViewState();
  }

  function handlePlatformAlertTriageFilterChange(value: string) {
    setPlatformAlertTriageFilter(value);
    resetPlatformAlertViewState();
  }

  function handlePlatformAlertServiceFilterChange(value: string) {
    setPlatformAlertServiceFilter(value);
    resetPlatformAlertViewState();
  }

  function handlePlatformAlertReceiverFilterChange(value: string) {
    setPlatformAlertReceiverFilter(value);
    resetPlatformAlertViewState();
  }

  function handlePlatformAlertSeverityFilterChange(value: string) {
    setPlatformAlertSeverityFilter(value);
    resetPlatformAlertViewState();
  }

  return {
    metricsText,
    refreshMetricsPreview,
    platformOperationalAlerts,
    platformAlertTrackedWorkItems,
    platformAlertStatusFilter,
    platformAlertTriageFilter,
    platformAlertServiceFilter,
    platformAlertReceiverFilter,
    platformAlertSeverityFilter,
    platformAlertCursorHistory,
    platformAlertMessage,
    acknowledgingPlatformAlertId,
    acknowledgingPlatformAlertsBatch,
    exportingPlatformAlerts,
    platformAlertExportFormat,
    setPlatformAlertExportFormat,
    selectedPlatformAlertIds,
    platformAlertServiceOptions,
    platformAlertReceiverOptions,
    platformAlertPage,
    platformAlertTotalPages,
    selectablePlatformAlertIds,
    allSelectablePlatformAlertsSelected,
    refreshPlatformOperationalAlerts,
    goToNextPlatformAlertsPage,
    goToPreviousPlatformAlertsPage,
    acknowledgePlatformAlert,
    acknowledgeFilteredPlatformAlerts,
    acknowledgeSelectedPlatformAlerts,
    togglePlatformAlertSelection,
    toggleAllSelectablePlatformAlerts,
    exportPlatformAlerts,
    handlePlatformAlertStatusFilterChange,
    handlePlatformAlertTriageFilterChange,
    handlePlatformAlertServiceFilterChange,
    handlePlatformAlertReceiverFilterChange,
    handlePlatformAlertSeverityFilterChange
  };
}

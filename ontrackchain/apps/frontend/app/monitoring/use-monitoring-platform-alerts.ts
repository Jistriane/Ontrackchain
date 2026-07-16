"use client";

import { useEffect, useRef, useState } from "react";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { isFrontendStandaloneShowcaseMode } from "../lib/auth-runtime";
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
  canReadPlatformAlerts: boolean | null;
  canManagePlatformAlerts: boolean | null;
};

type PlatformAlertConfirmDialogState =
  | {
      kind: "filtered";
    }
  | {
      kind: "selected";
      selectedIds: string[];
    }
  | null;

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

function matchesCurrentPlatformAlertFilters(
  entry: PlatformOperationalAlertsSnapshot["data"][number],
  filters: PlatformAlertFilterState
) {
  const statusMatches = filters.status === "all" || entry.status === filters.status;
  const triageMatches = filters.triageStatus === "all" || entry.triage_status === filters.triageStatus;
  const serviceMatches = filters.service === "all" || (entry.service ?? "") === filters.service;
  const receiverMatches = filters.receiver === "all" || entry.receiver === filters.receiver;
  const severityMatches = filters.severity === "all" || (entry.severity ?? "") === filters.severity;
  return statusMatches && triageMatches && serviceMatches && receiverMatches && severityMatches;
}

export function useMonitoringPlatformAlerts({
  t,
  setError,
  canReadPlatformAlerts,
  canManagePlatformAlerts
}: UseMonitoringPlatformAlertsArgs) {
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
  const [platformAlertConfirmDialogState, setPlatformAlertConfirmDialogState] = useState<PlatformAlertConfirmDialogState>(null);
  const platformAlertsRequestIdRef = useRef(0);
  const platformAlertSelectionScopeRef = useRef<string | null>(null);
  const platformAlertFiltersRef = useRef<PlatformAlertFilterState>({
    status: "all",
    triageStatus: "all",
    service: "all",
    receiver: "all",
    severity: "all"
  });
  const standaloneShowcaseMode = isFrontendStandaloneShowcaseMode();

  function currentPlatformAlertFilters(
    status = platformAlertFiltersRef.current.status,
    triageStatus = platformAlertFiltersRef.current.triageStatus,
    service = platformAlertFiltersRef.current.service,
    receiver = platformAlertFiltersRef.current.receiver,
    severity = platformAlertFiltersRef.current.severity
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
      const nextScope = buildPlatformAlertSelectionScope(
        currentPlatformAlertFilters(status, triageStatus, service, receiver, severity)
      );
      const currentScope = platformAlertSelectionScopeRef.current;
      if (currentScope && currentScope !== nextScope) {
        setSelectedPlatformAlertIds([]);
      }
      platformAlertSelectionScopeRef.current = nextScope;
      setPlatformAlertSelectionScope(nextScope);
      setPlatformOperationalAlerts(data);
      const workItemsResponse = await fetch("/api/app/operations/work-items?module=alerts&resource_type=operational_alert&limit=100", {
        cache: "no-store"
      });
      if (requestId !== platformAlertsRequestIdRef.current) {
        return;
      }
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
    if (canReadPlatformAlerts === null) {
      return;
    }
    if (!canReadPlatformAlerts) {
      setPlatformOperationalAlerts(null);
      setPlatformAlertTrackedWorkItems({});
      setMetricsText("");
      setPlatformAlertFilterOptions(null);
      setPlatformAlertMessage(null);
      setPlatformAlertConfirmDialogState(null);
      setSelectedPlatformAlertIds([]);
      setPlatformAlertSelectionHydrated(true);
      return;
    }

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
    platformAlertFiltersRef.current = currentPlatformAlertFilters(
      initialSelection.status,
      initialSelection.triageStatus,
      initialSelection.service,
      initialSelection.receiver,
      initialSelection.severity
    );
    platformAlertSelectionScopeRef.current = initialSelection.selectionScope;
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
  }, [canReadPlatformAlerts, t]);

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
    if (!canReadPlatformAlerts) {
      return;
    }
    setError(null);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    const filters = currentPlatformAlertFilters();
    await loadPlatformOperationalAlerts(
      filters.status,
      filters.triageStatus,
      filters.service,
      filters.receiver,
      filters.severity,
      null
    );
  }

  function applyLocalAcknowledgedPlatformAlerts(eventIds: string[], note: string, triagedBy: string) {
    if (!eventIds.length) {
      return;
    }
    const targetIds = new Set(eventIds);
    const filters = currentPlatformAlertFilters();
    const acknowledgedAt = new Date().toISOString();
    setPlatformOperationalAlerts((current) => {
      if (!current) {
        return current;
      }
      const updatedData = current.data.map((entry) =>
        targetIds.has(entry.id)
          ? {
              ...entry,
              triage_status: "acknowledged",
              triaged_at: entry.triaged_at ?? acknowledgedAt,
              triaged_by: triagedBy,
              triage_note: note
            }
          : entry
      );
      const visibleData = updatedData.filter((entry) => matchesCurrentPlatformAlertFilters(entry, filters));
      return {
        ...current,
        count: visibleData.length,
        total_count:
          filters.triageStatus === "pending"
            ? Math.max(0, current.total_count - eventIds.length)
            : filters.triageStatus === "acknowledged"
              ? current.total_count + eventIds.length
              : current.total_count,
        has_more: current.has_more && visibleData.length >= current.limit,
        data: visibleData
      };
    });
  }

  async function goToNextPlatformAlertsPage() {
    if (!canReadPlatformAlerts) {
      return;
    }
    const nextCursor = platformOperationalAlerts?.next_cursor;
    if (!nextCursor) {
      return;
    }
    setError(null);
    setPlatformAlertCursorHistory((current) => [...current, platformAlertCursor]);
    setPlatformAlertCursor(nextCursor);
    const filters = currentPlatformAlertFilters();
    await loadPlatformOperationalAlerts(
      filters.status,
      filters.triageStatus,
      filters.service,
      filters.receiver,
      filters.severity,
      nextCursor
    );
  }

  async function goToPreviousPlatformAlertsPage() {
    if (!canReadPlatformAlerts) {
      return;
    }
    if (!platformAlertCursorHistory.length) {
      return;
    }
    setError(null);
    const previousCursor = platformAlertCursorHistory[platformAlertCursorHistory.length - 1] ?? null;
    setPlatformAlertCursorHistory((current) => current.slice(0, -1));
    setPlatformAlertCursor(previousCursor);
    const filters = currentPlatformAlertFilters();
    await loadPlatformOperationalAlerts(
      filters.status,
      filters.triageStatus,
      filters.service,
      filters.receiver,
      filters.severity,
      previousCursor
    );
  }

  async function acknowledgePlatformAlert(eventId: string) {
    if (!canManagePlatformAlerts) {
      setError(t("apiErrors.privilegedWriteRoleRequired" as MessageKey));
      return;
    }
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
      if (standaloneShowcaseMode) {
        applyLocalAcknowledgedPlatformAlerts(
          [eventId],
          data?.triage_note ?? "ack_from_monitoring_ui",
          data?.triaged_by ?? "admin_ui"
        );
        await refreshMetricsPreview();
      } else {
        await Promise.all([refreshPlatformOperationalAlerts(), refreshMetricsPreview()]);
      }
    } finally {
      setAcknowledgingPlatformAlertId(null);
    }
  }

  async function performAcknowledgeFilteredPlatformAlerts() {
    if (!canManagePlatformAlerts) {
      setError(t("apiErrors.privilegedWriteRoleRequired" as MessageKey));
      return;
    }
    if (!platformOperationalAlerts?.total_count) {
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
          status: currentPlatformAlertFilters().status === "all" ? null : currentPlatformAlertFilters().status,
          triage_status: currentPlatformAlertFilters().triageStatus === "all" ? null : currentPlatformAlertFilters().triageStatus,
          service: currentPlatformAlertFilters().service === "all" ? null : currentPlatformAlertFilters().service,
          receiver: currentPlatformAlertFilters().receiver === "all" ? null : currentPlatformAlertFilters().receiver,
          severity: currentPlatformAlertFilters().severity === "all" ? null : currentPlatformAlertFilters().severity
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
      const acknowledgedIds = platformOperationalAlerts?.data
        .filter((entry) => entry.triage_status === "pending")
        .map((entry) => entry.id) ?? [];
      setSelectedPlatformAlertIds([]);
      if (standaloneShowcaseMode) {
        applyLocalAcknowledgedPlatformAlerts(acknowledgedIds, "ack_batch_from_monitoring_ui", "admin_ui");
        await refreshMetricsPreview();
      } else {
        await Promise.all([refreshPlatformOperationalAlerts(), refreshMetricsPreview()]);
      }
    } catch {
      setError(t("monitoring.errors.ackPlatformAlertsBatch"));
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

  async function performAcknowledgeSelectedPlatformAlerts(selectedIds: string[]) {
    if (!canManagePlatformAlerts) {
      setError(t("apiErrors.privilegedWriteRoleRequired" as MessageKey));
      return;
    }
    if (!selectedIds.length) {
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
          ids: selectedIds,
          note: "ack_selected_from_monitoring_ui",
          triaged_by: "admin_ui",
          status: currentPlatformAlertFilters().status === "all" ? null : currentPlatformAlertFilters().status,
          triage_status: currentPlatformAlertFilters().triageStatus === "all" ? null : currentPlatformAlertFilters().triageStatus,
          service: currentPlatformAlertFilters().service === "all" ? null : currentPlatformAlertFilters().service,
          receiver: currentPlatformAlertFilters().receiver === "all" ? null : currentPlatformAlertFilters().receiver,
          severity: currentPlatformAlertFilters().severity === "all" ? null : currentPlatformAlertFilters().severity
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
      if (standaloneShowcaseMode) {
        applyLocalAcknowledgedPlatformAlerts(selectedIds, "ack_selected_from_monitoring_ui", "admin_ui");
        await refreshMetricsPreview();
      } else {
        await Promise.all([refreshPlatformOperationalAlerts(), refreshMetricsPreview()]);
      }
    } catch {
      setError(t("monitoring.errors.ackPlatformAlertsSelected"));
    } finally {
      setAcknowledgingPlatformAlertsBatch(false);
    }
  }

  function acknowledgeFilteredPlatformAlerts() {
    if (!canManagePlatformAlerts) {
      setError(t("apiErrors.privilegedWriteRoleRequired" as MessageKey));
      return;
    }
    if (!platformOperationalAlerts?.total_count) {
      return;
    }

    setPlatformAlertConfirmDialogState({ kind: "filtered" });
  }

  function acknowledgeSelectedPlatformAlerts() {
    if (!canManagePlatformAlerts) {
      setError(t("apiErrors.privilegedWriteRoleRequired" as MessageKey));
      return;
    }
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

  const platformAlertConfirmDialog = platformAlertConfirmDialogState
    ? {
        title: t("monitoring.platform.confirmTitle"),
        description:
          platformAlertConfirmDialogState.kind === "filtered"
            ? t("monitoring.platform.confirmFiltered")
            : t("monitoring.platform.confirmSelected", { count: platformAlertConfirmDialogState.selectedIds.length }),
        confirmLabel:
          platformAlertConfirmDialogState.kind === "filtered"
            ? t("monitoring.platform.ackFiltered")
            : t("monitoring.platform.ackSelected", { count: platformAlertConfirmDialogState.selectedIds.length }),
        cancelLabel: t("common.cancel"),
        tone: "default" as const,
        testId:
          platformAlertConfirmDialogState.kind === "filtered"
            ? "platform-alert-confirm-dialog-filtered"
            : "platform-alert-confirm-dialog-selected"
      }
    : null;

  async function exportPlatformAlerts(scope: "filtered" | "selected") {
    if (!canManagePlatformAlerts) {
      setError(t("apiErrors.privilegedWriteRoleRequired" as MessageKey));
      return;
    }
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
          status: currentPlatformAlertFilters().status === "all" ? null : currentPlatformAlertFilters().status,
          triage_status: currentPlatformAlertFilters().triageStatus === "all" ? null : currentPlatformAlertFilters().triageStatus,
          service: currentPlatformAlertFilters().service === "all" ? null : currentPlatformAlertFilters().service,
          receiver: currentPlatformAlertFilters().receiver === "all" ? null : currentPlatformAlertFilters().receiver,
          severity: currentPlatformAlertFilters().severity === "all" ? null : currentPlatformAlertFilters().severity
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
    platformAlertSelectionScopeRef.current = null;
    setPlatformAlertSelectionScope(null);
  }

  function handlePlatformAlertStatusFilterChange(value: string) {
    platformAlertFiltersRef.current = currentPlatformAlertFilters(value);
    setPlatformAlertStatusFilter(value);
    resetPlatformAlertViewState();
  }

  function handlePlatformAlertTriageFilterChange(value: string) {
    platformAlertFiltersRef.current = currentPlatformAlertFilters(undefined, value);
    setPlatformAlertTriageFilter(value);
    resetPlatformAlertViewState();
  }

  function handlePlatformAlertServiceFilterChange(value: string) {
    platformAlertFiltersRef.current = currentPlatformAlertFilters(undefined, undefined, value);
    setPlatformAlertServiceFilter(value);
    resetPlatformAlertViewState();
  }

  function handlePlatformAlertReceiverFilterChange(value: string) {
    platformAlertFiltersRef.current = currentPlatformAlertFilters(undefined, undefined, undefined, value);
    setPlatformAlertReceiverFilter(value);
    resetPlatformAlertViewState();
  }

  function handlePlatformAlertSeverityFilterChange(value: string) {
    platformAlertFiltersRef.current = currentPlatformAlertFilters(undefined, undefined, undefined, undefined, value);
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
    platformAlertConfirmDialog,
    refreshPlatformOperationalAlerts,
    goToNextPlatformAlertsPage,
    goToPreviousPlatformAlertsPage,
    acknowledgePlatformAlert,
    acknowledgeFilteredPlatformAlerts,
    acknowledgeSelectedPlatformAlerts,
    cancelPlatformAlertConfirmation,
    confirmPlatformAlertConfirmation,
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

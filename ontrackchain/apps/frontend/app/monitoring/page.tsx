"use client";

import { useEffect, useRef, useState } from "react";
import { useI18n } from "../../components/i18n-provider";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { AppShell, CodeBlock, Message, Panel, Pill } from "../../components/ui";

type Watchlist = {
  id: string;
  name: string;
  priority: string;
};

const PLATFORM_ALERT_SELECTION_STORAGE_KEY = "monitoring-platform-alert-selection";

type Alert = {
  id: string;
  watchlist_id: string;
  address: string;
  chain: string;
  severity: string;
  title: string;
  details: any;
  created_at: string;
};

type OperationsSnapshot = {
  queue: {
    ready: number;
    waiting: number;
    retry_pending: number;
    retry_due: number;
    wake_signals: number;
  };
  concurrency: {
    org_active: number;
    org_limit: number;
    global_active: number;
    global_limit: number;
    plan: string;
  };
  throughput: {
    completed_last_hour: number;
    failed_last_hour: number;
    billing_recalc_last_hour: number;
    avg_duration_ms_last_20: number;
  };
  states: {
    queued: number;
    processing: number;
    dlq_failed: number;
    dlq_resolved: number;
  };
  recent_cases: Array<{
    case_id: string;
    status: string;
    target_address: string;
    target_chain: string;
    created_at: string | null;
    completed_at: string | null;
    queue_state: string | null;
    last_error: string | null;
    attempt_count: number;
    report_type_canonical: string | null;
    charged_cost: number | null;
    duration_ms: number | null;
  }>;
  generated_at: string;
};

type DlqSnapshot = {
  count: number;
  credits_available: number;
  filters: {
    state: string;
    target_chain: string | null;
    can_requeue: boolean | null;
    limit: number;
  };
  cases: Array<{
    case_id: string;
    status: string;
    target_address: string;
    target_chain: string;
    created_at: string | null;
    completed_at: string | null;
    report_type_canonical: string | null;
    failure_reason: string | null;
    dlq_state: string | null;
    dlq_failed_at: string | null;
    dlq_requeue_count: number;
    dlq_acknowledged_at: string | null;
    dlq_acknowledged_by: string | null;
    dlq_resolution_note: string | null;
    attempt_count: number;
    max_attempts: number;
    credits_estimated: number;
    credits_available: number;
    can_requeue: boolean;
  }>;
  generated_at: string;
};

type OperationalAlertsSnapshot = {
  generated_at: string;
  open_total: number;
  critical_open_total: number;
  alerts: Array<{
    code: string;
    severity: string;
    status: string;
    metric: string;
    value: number;
    threshold: number;
    title: string;
    message: string;
    recommended_action: string;
  }>;
};

type PlatformOperationalAlertsSnapshot = {
  status_filter: string | null;
  triage_status_filter: string | null;
  service_filter: string | null;
  receiver_filter: string | null;
  severity_filter: string | null;
  cursor: string | null;
  limit: number;
  total_count: number;
  count: number;
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

export default function MonitoringPage() {
  const { t } = useI18n();
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [operations, setOperations] = useState<OperationsSnapshot | null>(null);
  const [operationalAlerts, setOperationalAlerts] = useState<OperationalAlertsSnapshot | null>(null);
  const [platformOperationalAlerts, setPlatformOperationalAlerts] = useState<PlatformOperationalAlertsSnapshot | null>(null);
  const [metricsText, setMetricsText] = useState<string>("");
  const [dlq, setDlq] = useState<DlqSnapshot | null>(null);
  const [requeueingCaseId, setRequeueingCaseId] = useState<string | null>(null);
  const [resolvingCaseId, setResolvingCaseId] = useState<string | null>(null);
  const [dlqMessage, setDlqMessage] = useState<string | null>(null);
  const [dlqFilterState, setDlqFilterState] = useState("failed_permanent");
  const [dlqFilterChain, setDlqFilterChain] = useState("all");
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

  function buildPlatformAlertSelectionScope(
    status = platformAlertStatusFilter,
    triageStatus = platformAlertTriageFilter,
    service = platformAlertServiceFilter,
    receiver = platformAlertReceiverFilter,
    severity = platformAlertSeverityFilter
  ) {
    return JSON.stringify({ status, triageStatus, service, receiver, severity });
  }

  function caseAuditHref(caseId: string, reportId?: string | null) {
    const params = new URLSearchParams({
      resource_type: "case",
      resource_id: caseId
    });
    if (reportId) {
      params.set("report_id", reportId);
    }
    return `/audit?${params.toString()}`;
  }

  function caseEvidenceHref(caseId: string, reportId?: string | null) {
    const params = new URLSearchParams({
      domain: reportId ? "reports" : "all",
      resource_type: "case",
      resource_id: caseId
    });
    if (reportId) {
      params.set("report_id", reportId);
    }
    return `/evidence?${params.toString()}`;
  }

  function clearPersistedPlatformAlertSelection() {
    if (typeof window === "undefined") {
      return;
    }
    window.sessionStorage.removeItem(PLATFORM_ALERT_SELECTION_STORAGE_KEY);
  }

  function buildDynamicFilterValues(currentValue: string, values: string[] | undefined) {
    const merged = new Set((values ?? []).filter((entry) => entry && entry !== "all"));
    if (currentValue !== "all") {
      merged.add(currentValue);
    }
    return Array.from(merged).sort((left, right) => left.localeCompare(right));
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

  async function loadDlq(state = dlqFilterState, chain = dlqFilterChain) {
    const params = new URLSearchParams();
    params.set("state", state);
    if (chain !== "all") {
      params.set("target_chain", chain);
    }
    const res = await fetch(`/api/app/investigation/dlq?${params.toString()}`, { cache: "no-store" });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      setError(t("monitoring.errors.loadDlq"));
      return;
    }
    setDlq(data as DlqSnapshot);
  }

  async function loadOperationalAlerts() {
    const res = await fetch("/api/app/investigation/alerts", { cache: "no-store" });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      setError(t("monitoring.errors.loadOperationalAlerts"));
      return;
    }
    setOperationalAlerts(data as OperationalAlertsSnapshot);
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
    const nextScope = buildPlatformAlertSelectionScope(status, triageStatus, service, receiver, severity);
    setPlatformAlertSelectionScope((currentScope) => {
      if (currentScope && currentScope !== nextScope) {
        setSelectedPlatformAlertIds([]);
      }
      return nextScope;
    });
  }

  async function loadMetricsPreview() {
    const res = await fetch("/api/app/investigation/metrics", { cache: "no-store" });
    const text = await res.text();
    if (!res.ok) {
      setError(t("monitoring.errors.loadMetrics"));
      return;
    }
    setMetricsText(text);
  }

  useEffect(() => {
    let initialStatus = "all";
    let initialTriageStatus = "all";
    let initialService = "all";
    let initialReceiver = "all";
    let initialSeverity = "all";
    let initialCursor: string | null = null;
    let initialCursorHistory: Array<string | null> = [];
    let initialSelectedIds: string[] = [];
    let initialSelectionScope: string | null = null;

    if (typeof window !== "undefined") {
      try {
        const raw = window.sessionStorage.getItem(PLATFORM_ALERT_SELECTION_STORAGE_KEY);
        if (raw) {
          const parsed = JSON.parse(raw) as {
            status?: string;
            triageStatus?: string;
            service?: string;
            receiver?: string;
            severity?: string;
            cursor?: string | null;
            cursorHistory?: Array<string | null>;
            selectedIds?: string[];
            selectionScope?: string | null;
          };
          initialStatus = parsed.status ?? "all";
          initialTriageStatus = parsed.triageStatus ?? "all";
          initialService = parsed.service ?? "all";
          initialReceiver = parsed.receiver ?? "all";
          initialSeverity = parsed.severity ?? "all";
          initialCursor = typeof parsed.cursor === "string" ? parsed.cursor : null;
          initialCursorHistory = Array.isArray(parsed.cursorHistory)
            ? parsed.cursorHistory.filter((entry): entry is string | null => typeof entry === "string" || entry === null)
            : [];
          initialSelectedIds = Array.isArray(parsed.selectedIds) ? parsed.selectedIds.filter((entry) => typeof entry === "string") : [];
          initialSelectionScope = typeof parsed.selectionScope === "string" ? parsed.selectionScope : null;
          setPlatformAlertStatusFilter(initialStatus);
          setPlatformAlertTriageFilter(initialTriageStatus);
          setPlatformAlertServiceFilter(initialService);
          setPlatformAlertReceiverFilter(initialReceiver);
          setPlatformAlertSeverityFilter(initialSeverity);
          setPlatformAlertCursor(initialCursor);
          setPlatformAlertCursorHistory(initialCursorHistory);
          setSelectedPlatformAlertIds(initialSelectedIds);
          setPlatformAlertSelectionScope(initialSelectionScope);
        }
      } catch {
        clearPersistedPlatformAlertSelection();
      }
    }

    fetch("/api/app/monitoring/watchlists", { cache: "no-store" })
      .then(async (r) => {
        const data = await r.json().catch(() => null);
        if (!r.ok) {
          setError(t("monitoring.errors.loadWatchlists"));
          return;
        }
        setWatchlists((data?.data ?? []) as Watchlist[]);
      })
      .catch(() => setError(t("monitoring.errors.loadWatchlists")));

    fetch("/api/app/investigation/operations", { cache: "no-store" })
      .then(async (r) => {
        const data = await r.json().catch(() => null);
        if (!r.ok) {
          setError(t("monitoring.errors.loadWorkerOperations"));
          return;
        }
        setOperations(data as OperationsSnapshot);
      })
      .catch(() => setError(t("monitoring.errors.loadWorkerOperations")));

    loadPlatformOperationalAlertFilterOptions().catch(() =>
      setError(t("monitoring.errors.loadPlatformFilterOptions"))
    );

    loadOperationalAlerts().catch(() => setError(t("monitoring.errors.loadOperationalAlerts")));
    loadPlatformOperationalAlerts(initialStatus, initialTriageStatus, initialService, initialReceiver, initialSeverity, initialCursor)
      .catch(() => setError(t("monitoring.errors.loadPlatformAlerts")))
      .finally(() => setPlatformAlertSelectionHydrated(true));
    loadMetricsPreview().catch(() => setError(t("monitoring.errors.loadMetrics")));
    loadDlq().catch(() => setError(t("monitoring.errors.loadDlq")));
  }, [t]);

  useEffect(() => {
    if (!platformAlertSelectionHydrated || typeof window === "undefined") {
      return;
    }

    if (!selectedPlatformAlertIds.length && !platformAlertSelectionScope && !platformAlertCursor && !platformAlertCursorHistory.length) {
      clearPersistedPlatformAlertSelection();
      return;
    }

    window.sessionStorage.setItem(
      PLATFORM_ALERT_SELECTION_STORAGE_KEY,
      JSON.stringify({
        status: platformAlertStatusFilter,
        triageStatus: platformAlertTriageFilter,
        service: platformAlertServiceFilter,
        receiver: platformAlertReceiverFilter,
        severity: platformAlertSeverityFilter,
        cursor: platformAlertCursor,
        cursorHistory: platformAlertCursorHistory,
        selectedIds: selectedPlatformAlertIds,
        selectionScope: platformAlertSelectionScope
      })
    );
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

  async function refreshAlerts() {
    setError(null);
    const wl = watchlists[0];
    const query = wl ? `?watchlist_id=${encodeURIComponent(wl.id)}&limit=50` : "?limit=50";
    const res = await fetch(`/api/app/monitoring/alerts${query}`, { cache: "no-store" });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      setError(t("monitoring.errors.loadAlerts"));
      return;
    }
    setAlerts((data?.data ?? []) as Alert[]);
  }

  async function refreshOperations() {
    setError(null);
    const res = await fetch("/api/app/investigation/operations", { cache: "no-store" });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      setError(t("monitoring.errors.loadWorkerOperations"));
      return;
    }
    setOperations(data as OperationsSnapshot);
  }

  async function refreshOperationalAlerts() {
    setError(null);
    await loadOperationalAlerts();
  }

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

  function handlePlatformAlertStatusFilterChange(value: string) {
    setPlatformAlertStatusFilter(value);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    setSelectedPlatformAlertIds([]);
    setPlatformAlertSelectionScope(null);
  }

  function handlePlatformAlertTriageFilterChange(value: string) {
    setPlatformAlertTriageFilter(value);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    setSelectedPlatformAlertIds([]);
    setPlatformAlertSelectionScope(null);
  }

  function handlePlatformAlertServiceFilterChange(value: string) {
    setPlatformAlertServiceFilter(value);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    setSelectedPlatformAlertIds([]);
    setPlatformAlertSelectionScope(null);
  }

  function handlePlatformAlertReceiverFilterChange(value: string) {
    setPlatformAlertReceiverFilter(value);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    setSelectedPlatformAlertIds([]);
    setPlatformAlertSelectionScope(null);
  }

  function handlePlatformAlertSeverityFilterChange(value: string) {
    setPlatformAlertSeverityFilter(value);
    setPlatformAlertCursor(null);
    setPlatformAlertCursorHistory([]);
    setSelectedPlatformAlertIds([]);
    setPlatformAlertSelectionScope(null);
  }

  async function refreshMetricsPreview() {
    setError(null);
    await loadMetricsPreview();
  }

  async function refreshDlq() {
    setError(null);
    await loadDlq();
  }

  async function requeueDlqCase(caseId: string) {
    setError(null);
    setDlqMessage(null);
    setRequeueingCaseId(caseId);
    try {
      const res = await fetch(`/api/app/investigation/dlq/${caseId}/requeue`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ reason: "manual_requeue_from_monitoring_ui" }),
        cache: "no-store"
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        setError(resolveApiErrorMessage(t, data, t("monitoring.errors.requeueDlq")));
        return;
      }
      setDlqMessage(t("monitoring.dlq.messageRequeue", { caseId, status: data?.status ?? "queued" }));
      await Promise.all([refreshDlq(), refreshOperations(), refreshOperationalAlerts(), refreshMetricsPreview()]);
    } finally {
      setRequeueingCaseId(null);
    }
  }

  async function resolveDlqCase(caseId: string, action: "acknowledged" | "discarded") {
    setError(null);
    setDlqMessage(null);
    setResolvingCaseId(caseId);
    try {
      const res = await fetch(`/api/app/investigation/dlq/${caseId}/acknowledge`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          action,
          note: action === "acknowledged" ? "ack_from_monitoring_ui" : "discard_from_monitoring_ui"
        }),
        cache: "no-store"
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        setError(resolveApiErrorMessage(t, data, t("monitoring.errors.resolveDlq")));
        return;
      }
      setDlqMessage(t("monitoring.dlq.messageResolve", { caseId, status: data?.dlq_state ?? action }));
      await Promise.all([refreshDlq(), refreshOperations(), refreshOperationalAlerts(), refreshMetricsPreview()]);
    } finally {
      setResolvingCaseId(null);
    }
  }

  async function triggerAlert() {
    const wl = watchlists[0];
    if (!wl) {
      setError(t("monitoring.errors.noWatchlist"));
      return;
    }
    const res = await fetch("/api/app/monitoring/trigger-alert", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        watchlist_id: wl.id,
        address: "0x1111111111111111111111111111111111111111",
        chain: "ethereum",
        severity: "high",
        title: t("monitoring.testAlertTitle"),
        details: { source: "test" }
      })
    });
    if (!res.ok) {
      setError(t("monitoring.errors.triggerAlert"));
      return;
    }
    await refreshAlerts();
  }

  return (
    <AppShell
      title={t("monitoring.title")}
      subtitle={t("monitoring.subtitle")}
      activePath="/monitoring"
      actions={<Pill>{t("monitoring.active")}</Pill>}
    >
      {error ? <Message tone="error">{error}</Message> : null}

      <Panel title={t("monitoring.watchlists.title")}>
        {watchlists.length ? (
          <div data-testid="watchlist-item" className="otc-monitoring-card">
            {watchlists[0].name} ({watchlists[0].priority})
          </div>
        ) : (
          <Message>{t("monitoring.watchlists.empty")}</Message>
        )}
      </Panel>

      <Panel title={t("monitoring.alerts.title")}>
        <div className="otc-controls">
          <button type="button" onClick={refreshAlerts} className="otc-button otc-button--ghost">
            {t("monitoring.actions.refresh")}
          </button>
          <button type="button" data-testid="trigger-alert-btn" onClick={triggerAlert} className="otc-button otc-button--accent">
            {t("monitoring.actions.triggerAlert")}
          </button>
        </div>

        {alerts.length ? (
          <div className="otc-monitoring-banner">
            <button
              type="button"
              data-testid="alert-badge"
              onClick={() => setSelectedAlert(alerts[0])}
              className="otc-button otc-button--ghost"
            >
              {alerts[0].severity}: {alerts[0].title}
            </button>
          </div>
        ) : null}

        {selectedAlert ? (
          <div data-testid="alert-details-panel" className="otc-monitoring-banner">
            <div className="otc-monitoring-actions">
              <a
                className="otc-button otc-button--ghost"
                href={`/sanctions?address=${encodeURIComponent(selectedAlert.address)}&chain=${encodeURIComponent(selectedAlert.chain)}&autostart=1`}
              >
                {t("monitoring.alerts.openSanctions")}
              </a>
              <a
                className="otc-button otc-button--ghost"
                href={`/investigate?address=${encodeURIComponent(selectedAlert.address)}&chain=${encodeURIComponent(selectedAlert.chain)}&report_type=technical_basic`}
              >
                {t("monitoring.alerts.openInvestigate")}
              </a>
              <a
                className="otc-button otc-button--ghost"
                href={`/evidence?domain=sanctions&resource_id=${encodeURIComponent(selectedAlert.id)}`}
              >
                {t("monitoring.alerts.openEvidence")}
              </a>
            </div>
            <CodeBlock>
              {JSON.stringify(selectedAlert, null, 2)}
            </CodeBlock>
          </div>
        ) : null}
      </Panel>

      <Panel title={t("monitoring.worker.title")}>
        <div className="otc-controls">
          <button type="button" data-testid="worker-refresh-btn" onClick={refreshOperations} className="otc-button otc-button--ghost">
            {t("monitoring.worker.refresh")}
          </button>
          <span data-testid="worker-generated-at" className="otc-monitoring-meta">
            {operations ? t("monitoring.worker.snapshot", { value: operations.generated_at }) : t("monitoring.worker.noSnapshot")}
          </span>
        </div>

        {operations ? (
          <>
            <div className="otc-monitoring-grid otc-monitoring-grid--metrics otc-monitoring-banner">
              <div data-testid="worker-metric-ready" className="otc-monitoring-card">
                <strong>{t("monitoring.worker.metricReady")}</strong>
                <div>{operations.queue.ready}</div>
              </div>
              <div data-testid="worker-metric-waiting" className="otc-monitoring-card">
                <strong>{t("monitoring.worker.metricWaiting")}</strong>
                <div>{operations.queue.waiting}</div>
              </div>
              <div data-testid="worker-metric-retry" className="otc-monitoring-card">
                <strong>{t("monitoring.worker.metricRetry")}</strong>
                <div>{operations.queue.retry_pending}</div>
              </div>
              <div data-testid="worker-metric-concurrency" className="otc-monitoring-card">
                <strong>{t("monitoring.worker.metricConcurrency")}</strong>
                <div>
                  {t("monitoring.worker.org")} {operations.concurrency.org_active}/{operations.concurrency.org_limit}
                </div>
                <div>
                  {t("monitoring.worker.global")} {operations.concurrency.global_active}/{operations.concurrency.global_limit}
                </div>
              </div>
              <div data-testid="worker-metric-throughput" className="otc-monitoring-card">
                <strong>{t("monitoring.worker.metricThroughput")}</strong>
                <div>{t("monitoring.worker.metricCompleted")} {operations.throughput.completed_last_hour}</div>
                <div>{t("monitoring.worker.metricFailed")} {operations.throughput.failed_last_hour}</div>
              </div>
              <div data-testid="worker-metric-duration" className="otc-monitoring-card">
                <strong>{t("monitoring.worker.metricDuration")}</strong>
                <div>{Math.round(operations.throughput.avg_duration_ms_last_20)} ms</div>
              </div>
              <div data-testid="worker-metric-dlq" className="otc-monitoring-card">
                <strong>DLQ</strong>
                <div>{t("monitoring.worker.metricDlqOpen")} {operations.states.dlq_failed}</div>
                <div>{t("monitoring.worker.metricDlqResolved")} {operations.states.dlq_resolved}</div>
              </div>
            </div>

            <div className="otc-monitoring-spacer">
              <h3>{t("monitoring.worker.recent")}</h3>
              {operations.recent_cases.length ? (
                <div className="otc-monitoring-grid">
                  {operations.recent_cases.map((entry) => (
                    <div
                      key={entry.case_id}
                      data-testid="worker-case-row"
                      className="otc-monitoring-card"
                    >
                      <div className="otc-monitoring-row">
                        <strong>{entry.status}</strong>
                        <span className="otc-monitoring-meta">{entry.created_at ?? t("common.noCreatedAt")}</span>
                      </div>
                      <div className="otc-monitoring-detail">
                        {entry.case_id} • {entry.target_chain} • {entry.report_type_canonical ?? t("common.notAvailable")}
                      </div>
                      <div className="otc-monitoring-detail--subtle">
                        {t("monitoring.worker.queue")}={entry.queue_state ?? t("common.notAvailable")} • {t("monitoring.worker.attempts")}={entry.attempt_count} • {t("monitoring.worker.duration")}={entry.duration_ms ?? 0}ms
                      </div>
                      {entry.last_error ? <div className="otc-monitoring-detail--subtle">{t("monitoring.worker.errorPrefix")}: {entry.last_error}</div> : null}
                      <div className="otc-monitoring-actions">
                        <a className="otc-button otc-button--ghost" href={`/cases/${entry.case_id}`}>
                          {t("monitoring.worker.openCase")}
                        </a>
                        <a className="otc-button otc-button--ghost" href={caseAuditHref(entry.case_id, null)}>
                          {t("monitoring.worker.openAudit")}
                        </a>
                        <a className="otc-button otc-button--ghost" href={caseEvidenceHref(entry.case_id, null)}>
                          {t("monitoring.worker.openEvidence")}
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div data-testid="worker-case-empty">
                  <Message>{t("monitoring.worker.recentEmpty")}</Message>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="otc-monitoring-banner">
            <div data-testid="worker-loading">
              <Message>{t("monitoring.worker.loading")}</Message>
            </div>
          </div>
        )}
      </Panel>

      <Panel title={t("monitoring.worker.operationalAlerts.title")}>
        <div className="otc-controls">
          <button type="button" data-testid="worker-alerts-refresh-btn" onClick={refreshOperationalAlerts} className="otc-button otc-button--ghost">
            {t("monitoring.worker.refreshAlerts")}
          </button>
          <button type="button" data-testid="worker-metrics-refresh-btn" onClick={refreshMetricsPreview} className="otc-button otc-button--ghost">
            {t("monitoring.worker.refreshMetrics")}
          </button>
          {operationalAlerts ? (
            <span data-testid="worker-alerts-summary" className="otc-monitoring-meta">
              {t("monitoring.worker.summary", { open: operationalAlerts.open_total, critical: operationalAlerts.critical_open_total })}
            </span>
          ) : (
            <span data-testid="worker-alerts-summary" className="otc-monitoring-meta">
              {t("monitoring.worker.noSnapshot")}
            </span>
          )}
        </div>

        {operationalAlerts ? (
          operationalAlerts.alerts.filter((alert) => alert.status === "open").length ? (
            <div className="otc-monitoring-grid otc-monitoring-banner">
              {operationalAlerts.alerts
                .filter((alert) => alert.status === "open")
                .map((alert) => (
                  <div
                    key={alert.code}
                    data-testid="worker-operational-alert"
                    className={`otc-monitoring-card ${alert.severity === "critical" ? "otc-monitoring-card--danger" : "otc-monitoring-card--warning"}`}
                  >
                    <div className="otc-monitoring-row">
                      <strong>{alert.title}</strong>
                      <span>{alert.severity}</span>
                    </div>
                    <div className="otc-monitoring-detail">{alert.message}</div>
                    <div className="otc-monitoring-detail--subtle">
                      {alert.metric}: {alert.value} / {t("monitoring.worker.threshold")} {alert.threshold}
                    </div>
                    <div className="otc-monitoring-detail--subtle">{alert.recommended_action}</div>
                    <div className="otc-monitoring-actions">
                      <a className="otc-button otc-button--ghost" href={`/alerts?severity=${encodeURIComponent(alert.severity)}`}>
                        {t("monitoring.worker.openAlerts")}
                      </a>
                    </div>
                  </div>
                ))}
            </div>
          ) : (
            <div className="otc-monitoring-banner">
              <div data-testid="worker-operational-alert-empty">
                <Message>{t("monitoring.worker.openAlertEmpty")}</Message>
              </div>
            </div>
          )
        ) : (
          <div className="otc-monitoring-banner">
            <div data-testid="worker-operational-alert-loading">
              <Message>{t("monitoring.worker.openAlertLoading")}</Message>
            </div>
          </div>
        )}

        <div className="otc-monitoring-spacer">
          <h3>{t("monitoring.worker.metricsPreview")}</h3>
          {metricsText ? (
            <div data-testid="worker-metrics-preview">
              <CodeBlock>{metricsText}</CodeBlock>
            </div>
          ) : (
            <div className="otc-monitoring-banner">
              <div data-testid="worker-metrics-loading">
                <Message>{t("monitoring.worker.metricsLoading")}</Message>
              </div>
            </div>
          )}
        </div>
      </Panel>

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
          <button
            type="button"
            data-testid="platform-alerts-refresh-btn"
            onClick={refreshPlatformOperationalAlerts}
            className="otc-button otc-button--ghost"
          >
            {t("monitoring.platform.refresh")}
          </button>
          <button
            type="button"
            data-testid="platform-alerts-ack-batch-btn"
            onClick={acknowledgeFilteredPlatformAlerts}
            disabled={
              acknowledgingPlatformAlertsBatch ||
              !platformOperationalAlerts?.total_count ||
              platformAlertTriageFilter === "acknowledged"
            }
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
            {acknowledgingPlatformAlertsBatch
              ? t("monitoring.platform.ackSelectedLoading")
              : t("monitoring.platform.ackSelected", { count: selectedPlatformAlertIds.length })}
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
                </div>
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

      <Panel title={t("monitoring.dlq.title")}>
        <div className="otc-controls">
          <select
            aria-label={t("monitoring.dlq.filters.stateAria")}
            data-testid="dlq-filter-state"
            value={dlqFilterState}
            onChange={(event) => setDlqFilterState(event.target.value)}
            className="otc-select"
          >
            <option value="failed_permanent">{t("monitoring.dlq.state.open")}</option>
            <option value="resolved">{t("monitoring.dlq.state.resolved")}</option>
            <option value="acknowledged">{t("monitoring.dlq.state.archived")}</option>
            <option value="discarded">{t("monitoring.dlq.state.discarded")}</option>
            <option value="all">{t("monitoring.dlq.state.all")}</option>
          </select>
          <select
            aria-label={t("monitoring.dlq.filters.chainAria")}
            data-testid="dlq-filter-chain"
            value={dlqFilterChain}
            onChange={(event) => setDlqFilterChain(event.target.value)}
            className="otc-select"
          >
            <option value="all">{t("monitoring.dlq.chainAll")}</option>
            <option value="ethereum">Ethereum</option>
            <option value="bitcoin">Bitcoin</option>
            <option value="arbitrum">Arbitrum</option>
            <option value="base">Base</option>
          </select>
          <button type="button" data-testid="dlq-refresh-btn" onClick={refreshDlq} className="otc-button otc-button--ghost">
            {t("monitoring.dlq.refresh")}
          </button>
          <span data-testid="dlq-generated-at" className="otc-monitoring-meta">
            {dlq ? t("monitoring.dlq.snapshot", { value: dlq.generated_at }) : t("monitoring.platform.noSnapshot")}
          </span>
          {dlq ? (
            <span data-testid="dlq-credits-available" className="otc-monitoring-meta">
              {t("monitoring.dlq.creditsAvailable", { count: dlq.credits_available })}
            </span>
          ) : null}
        </div>

        {dlqMessage ? (
          <div data-testid="dlq-message" className="otc-monitoring-banner">
            <Message tone="success">{dlqMessage}</Message>
          </div>
        ) : null}

        {dlq ? (
          dlq.cases.length ? (
            <div className="otc-monitoring-grid otc-monitoring-banner">
              {dlq.cases.map((entry) => (
                <div
                  key={entry.case_id}
                  data-testid="dlq-case-row"
                  className="otc-monitoring-card otc-monitoring-card--warning"
                >
                  <div className="otc-monitoring-row">
                    <strong>{entry.case_id}</strong>
                    <span className="otc-monitoring-meta">{entry.dlq_failed_at ?? entry.completed_at ?? t("common.noTimestamp")}</span>
                  </div>
                  <div className="otc-monitoring-detail">
                    {entry.target_chain} • {entry.report_type_canonical ?? t("common.notAvailable")} • {t("monitoring.dlq.attempt")} {entry.attempt_count}/{entry.max_attempts}
                  </div>
                  <div className="otc-monitoring-detail--subtle">
                    {t("monitoring.dlq.cost")}={entry.credits_estimated} • {t("monitoring.dlq.requeues")}={entry.dlq_requeue_count} • {t("monitoring.dlq.stateLabel")}={entry.dlq_state ?? t("common.notAvailable")}
                  </div>
                  {entry.failure_reason ? <div className="otc-monitoring-detail--subtle">{t("monitoring.dlq.errorLabel")}: {entry.failure_reason}</div> : null}
                  {entry.dlq_acknowledged_at ? (
                    <div className="otc-monitoring-detail--subtle">
                      {t("monitoring.dlq.resolvedAt")} {entry.dlq_acknowledged_at} {t("common.by")} {entry.dlq_acknowledged_by ?? t("monitoring.platform.adminFallback")}
                    </div>
                  ) : null}
                  {entry.dlq_resolution_note ? (
                    <div className="otc-monitoring-detail--subtle">{t("monitoring.dlq.note")}: {entry.dlq_resolution_note}</div>
                  ) : null}
                  <div className="otc-monitoring-actions">
                    <a className="otc-button otc-button--ghost" href={`/cases/${entry.case_id}`}>
                      {t("monitoring.dlq.openCase")}
                    </a>
                    <a className="otc-button otc-button--ghost" href={caseAuditHref(entry.case_id, null)}>
                      {t("monitoring.dlq.openAudit")}
                    </a>
                    <a className="otc-button otc-button--ghost" href={caseEvidenceHref(entry.case_id, null)}>
                      {t("monitoring.dlq.openEvidence")}
                    </a>
                    <button
                      type="button"
                      data-testid={`dlq-requeue-btn-${entry.case_id}`}
                      onClick={() => requeueDlqCase(entry.case_id)}
                      disabled={entry.dlq_state !== "failed_permanent" || !entry.can_requeue || requeueingCaseId === entry.case_id}
                      className="otc-button"
                    >
                      {requeueingCaseId === entry.case_id ? t("monitoring.dlq.requeueLoading") : t("monitoring.dlq.requeue")}
                    </button>
                    <button
                      type="button"
                      data-testid={`dlq-ack-btn-${entry.case_id}`}
                      onClick={() => resolveDlqCase(entry.case_id, "acknowledged")}
                      disabled={entry.dlq_state !== "failed_permanent" || resolvingCaseId === entry.case_id}
                      className="otc-button otc-button--ghost"
                    >
                      {resolvingCaseId === entry.case_id ? t("monitoring.dlq.archiveLoading") : t("monitoring.dlq.archive")}
                    </button>
                    <button
                      type="button"
                      data-testid={`dlq-discard-btn-${entry.case_id}`}
                      onClick={() => resolveDlqCase(entry.case_id, "discarded")}
                      disabled={entry.dlq_state !== "failed_permanent" || resolvingCaseId === entry.case_id}
                      className="otc-button otc-button--ghost"
                    >
                      {resolvingCaseId === entry.case_id ? t("monitoring.dlq.discardLoading") : t("monitoring.dlq.discard")}
                    </button>
                  </div>
                  {!entry.can_requeue ? (
                    <div className="otc-monitoring-detail--subtle">{t("monitoring.dlq.insufficientCredits")}</div>
                  ) : null}
                </div>
              ))}
            </div>
          ) : (
            <div data-testid="dlq-empty" className="otc-monitoring-banner">
              <Message>{t("monitoring.dlq.empty")}</Message>
            </div>
          )
        ) : (
          <div data-testid="dlq-loading" className="otc-monitoring-banner">
            <Message>{t("monitoring.dlq.loading")}</Message>
          </div>
        )}
      </Panel>
    </AppShell>
  );
}

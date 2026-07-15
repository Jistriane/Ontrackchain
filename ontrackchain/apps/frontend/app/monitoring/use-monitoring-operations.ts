"use client";

import { useEffect, useState } from "react";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import {
  fetchMonitoringDlq,
  fetchMonitoringOperationalAlerts,
  fetchMonitoringOperations
} from "../lib/monitoring-api";
import type { DlqSnapshot } from "../lib/monitoring-dlq";
import type { MessageKey } from "../lib/i18n";
import {
  normalizeOperationsSnapshot,
  type OperationsSnapshot,
  type OperationalAlertsSnapshot
} from "../lib/monitoring-investigation-operations";

type Translator = (key: MessageKey, values?: Record<string, string | number>) => string;

type UseMonitoringOperationsArgs = {
  t: Translator;
  setError: (message: string | null) => void;
  refreshMetricsPreview: () => Promise<void>;
  canReadInvestigationAdmin: boolean | null;
  canManageInvestigationAdmin: boolean | null;
};

export function useMonitoringOperations({
  t,
  setError,
  refreshMetricsPreview,
  canReadInvestigationAdmin,
  canManageInvestigationAdmin
}: UseMonitoringOperationsArgs) {
  const [operations, setOperations] = useState<OperationsSnapshot | null>(null);
  const [operationalAlerts, setOperationalAlerts] = useState<OperationalAlertsSnapshot | null>(null);
  const [dlq, setDlq] = useState<DlqSnapshot | null>(null);
  const [requeueingCaseId, setRequeueingCaseId] = useState<string | null>(null);
  const [resolvingCaseId, setResolvingCaseId] = useState<string | null>(null);
  const [dlqMessage, setDlqMessage] = useState<string | null>(null);
  const [dlqFilterState, setDlqFilterState] = useState("failed_permanent");
  const [dlqFilterChain, setDlqFilterChain] = useState("all");

  async function loadOperations() {
    try {
      const data = await fetchMonitoringOperations();
      setOperations(normalizeOperationsSnapshot(data));
    } catch {
      setError(t("monitoring.errors.loadWorkerOperations"));
    }
  }

  async function loadOperationalAlerts() {
    try {
      const data = await fetchMonitoringOperationalAlerts();
      setOperationalAlerts(data);
    } catch {
      setError(t("monitoring.errors.loadOperationalAlerts"));
    }
  }

  async function loadDlq(state = dlqFilterState, chain = dlqFilterChain) {
    try {
      const data = await fetchMonitoringDlq(state, chain);
      setDlq(data);
    } catch {
      setError(t("monitoring.errors.loadDlq"));
    }
  }

  useEffect(() => {
    if (canReadInvestigationAdmin === null) {
      return;
    }
    if (!canReadInvestigationAdmin) {
      setOperations(null);
      setOperationalAlerts(null);
      setDlq(null);
      setDlqMessage(null);
      return;
    }

    loadOperations().catch(() => setError(t("monitoring.errors.loadWorkerOperations")));
    loadOperationalAlerts().catch(() => setError(t("monitoring.errors.loadOperationalAlerts")));
    loadDlq().catch(() => setError(t("monitoring.errors.loadDlq")));
  }, [canReadInvestigationAdmin, t]);

  async function refreshOperations() {
    if (!canReadInvestigationAdmin) {
      return;
    }
    setError(null);
    await loadOperations();
  }

  async function refreshOperationalAlerts() {
    if (!canReadInvestigationAdmin) {
      return;
    }
    setError(null);
    await loadOperationalAlerts();
  }

  async function refreshDlq() {
    if (!canReadInvestigationAdmin) {
      return;
    }
    setError(null);
    await loadDlq();
  }

  async function requeueDlqCase(caseId: string) {
    if (!canManageInvestigationAdmin) {
      setError(t("apiErrors.privilegedWriteRoleRequired" as MessageKey));
      return;
    }
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
    if (!canManageInvestigationAdmin) {
      setError(t("apiErrors.privilegedWriteRoleRequired" as MessageKey));
      return;
    }
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

  return {
    operations,
    operationalAlerts,
    dlq,
    requeueingCaseId,
    resolvingCaseId,
    dlqMessage,
    dlqFilterState,
    setDlqFilterState,
    dlqFilterChain,
    setDlqFilterChain,
    refreshOperations,
    refreshOperationalAlerts,
    refreshDlq,
    requeueDlqCase,
    resolveDlqCase
  };
}

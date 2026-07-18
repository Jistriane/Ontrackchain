"use client";

import { useEffect, useState } from "react";
import { useI18n } from "../../components/i18n-provider";
import { buildCaseAuditHref, buildCaseEvidenceHref } from "../lib/operational-context";
import {
  canManageInvestigationAdmin,
  canManageMonitoringAdmin,
  canReadInvestigationAdmin,
  canReadMonitoringCore,
  canReadMonitoringAdmin,
  canTriggerMonitoringTestAlert
} from "../lib/authz";
import { fetchAuthContext, type AuthContext } from "../lib/ownership";
import { AppShell, ConfirmDialog, Message, Pill } from "../../components/ui";
import type { MessageKey } from "../lib/i18n";
import { DlqRemediationPanel } from "./dlq-remediation-panel";
import { InvestigationOperationsPanel } from "./investigation-operations-panel";
import { PlatformAlertTriagePanel } from "./platform-alert-triage-panel";
import { useMonitoringOperations } from "./use-monitoring-operations";
import { useMonitoringPlatformAlerts } from "./use-monitoring-platform-alerts";
import { useMonitoringWatchlistAlerts } from "./use-monitoring-watchlist-alerts";
import { WatchlistAlertsPanel } from "./watchlist-alerts-panel";

export default function MonitoringPage() {
  const { t } = useI18n();
  const [error, setError] = useState<string | null>(null);
  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [authResolved, setAuthResolved] = useState(false);
  const canReadCoreMonitoringSurface = authResolved ? canReadMonitoringCore(authContext?.role) : null;
  const canTriggerTestAlert = authResolved ? canTriggerMonitoringTestAlert(authContext?.role) : false;
  const canReadPlatformAdmin = authResolved ? canReadMonitoringAdmin(authContext?.role) : null;
  const canManagePlatformAdmin = authResolved ? canManageMonitoringAdmin(authContext?.role) : null;
  const canReadInvestigationAdminSurface = authResolved ? canReadInvestigationAdmin(authContext?.role) : null;
  const canManageInvestigationAdminSurface = authResolved ? canManageInvestigationAdmin(authContext?.role) : null;
  const { watchlists, alerts, selectedAlert, setSelectedAlert, refreshAlerts, triggerAlert } =
    useMonitoringWatchlistAlerts({ t, setError, canReadMonitoringCore: canReadCoreMonitoringSurface, canTriggerTestAlert });
  const {
    metricsText,
    refreshMetricsPreview: refreshPlatformMetricsPreview,
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
  } = useMonitoringPlatformAlerts({ t, setError, canReadPlatformAlerts: canReadPlatformAdmin, canManagePlatformAlerts: canManagePlatformAdmin });
  const {
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
  } = useMonitoringOperations({
    t,
    setError,
    refreshMetricsPreview: refreshPlatformMetricsPreview,
    canReadInvestigationAdmin: canReadInvestigationAdminSurface,
    canManageInvestigationAdmin: canManageInvestigationAdminSurface
  });

  useEffect(() => {
    fetchAuthContext()
      .then((context) => setAuthContext(context))
      .catch(() => setAuthContext(null))
      .finally(() => setAuthResolved(true));
  }, []);

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

  function translatePlatformQueueStatus(status: string) {
    const normalized = status.toLowerCase();
    return t(`monitoring.platform.queueStatus.${normalized}` as MessageKey);
  }

  function translatePlatformContainmentStatus(status: string) {
    return t(`alerts.workspace.rca.containment.${status}` as MessageKey);
  }

  async function refreshMetricsPreview() {
    setError(null);
    await refreshPlatformMetricsPreview();
  }

  return (
    <AppShell
      title={t("monitoring.title")}
      subtitle={t("monitoring.subtitle")}
      activePath="/monitoring"
      actions={<Pill>{t("monitoring.active")}</Pill>}
    >
      {error ? <Message tone="error">{error}</Message> : null}

      <WatchlistAlertsPanel
        t={t}
        canReadMonitoringCore={canReadCoreMonitoringSurface}
        watchlists={watchlists}
        alerts={alerts}
        selectedAlert={selectedAlert}
        setSelectedAlert={setSelectedAlert}
        refreshAlerts={refreshAlerts}
        triggerAlert={triggerAlert}
        canTriggerTestAlert={canTriggerTestAlert}
      />

      <InvestigationOperationsPanel
        t={t}
        canReadInvestigationAdmin={canReadInvestigationAdminSurface}
        operations={operations}
        refreshOperations={refreshOperations}
        caseAuditHref={buildCaseAuditHref}
        caseEvidenceHref={buildCaseEvidenceHref}
        operationalAlerts={operationalAlerts}
        refreshOperationalAlerts={refreshOperationalAlerts}
        refreshMetricsPreview={refreshMetricsPreview}
        metricsText={metricsText}
      />

      {authResolved ? (
        <PlatformAlertTriagePanel
          t={t}
          canReadPlatformAdmin={canReadPlatformAdmin}
          canManagePlatformAdmin={canManagePlatformAdmin}
          platformAlertStatusFilter={platformAlertStatusFilter}
          platformAlertTriageFilter={platformAlertTriageFilter}
          platformAlertServiceFilter={platformAlertServiceFilter}
          platformAlertReceiverFilter={platformAlertReceiverFilter}
          platformAlertSeverityFilter={platformAlertSeverityFilter}
          platformAlertServiceOptions={platformAlertServiceOptions}
          platformAlertReceiverOptions={platformAlertReceiverOptions}
          refreshPlatformOperationalAlerts={refreshPlatformOperationalAlerts}
          acknowledgeFilteredPlatformAlerts={acknowledgeFilteredPlatformAlerts}
          acknowledgeSelectedPlatformAlerts={acknowledgeSelectedPlatformAlerts}
          platformOperationalAlerts={platformOperationalAlerts}
          platformAlertTrackedWorkItems={platformAlertTrackedWorkItems}
          acknowledgingPlatformAlertsBatch={acknowledgingPlatformAlertsBatch}
          selectedPlatformAlertIds={selectedPlatformAlertIds}
          platformAlertExportFormat={platformAlertExportFormat}
          exportingPlatformAlerts={exportingPlatformAlerts}
          setPlatformAlertExportFormat={setPlatformAlertExportFormat}
          exportPlatformAlerts={exportPlatformAlerts}
          platformAlertPage={platformAlertPage}
          platformAlertTotalPages={platformAlertTotalPages}
          goToPreviousPlatformAlertsPage={goToPreviousPlatformAlertsPage}
          goToNextPlatformAlertsPage={goToNextPlatformAlertsPage}
          platformAlertCursorHistoryLength={platformAlertCursorHistory.length}
          platformAlertMessage={platformAlertMessage}
          allSelectablePlatformAlertsSelected={allSelectablePlatformAlertsSelected}
          selectablePlatformAlertIds={selectablePlatformAlertIds}
          toggleAllSelectablePlatformAlerts={toggleAllSelectablePlatformAlerts}
          togglePlatformAlertSelection={togglePlatformAlertSelection}
          translatePlatformSeverity={translatePlatformSeverity}
          translatePlatformStatus={translatePlatformStatus}
          translatePlatformTriage={translatePlatformTriage}
          translatePlatformQueueStatus={translatePlatformQueueStatus}
          translatePlatformContainmentStatus={translatePlatformContainmentStatus}
          acknowledgingPlatformAlertId={acknowledgingPlatformAlertId}
          acknowledgePlatformAlert={acknowledgePlatformAlert}
          handlePlatformAlertStatusFilterChange={handlePlatformAlertStatusFilterChange}
          handlePlatformAlertTriageFilterChange={handlePlatformAlertTriageFilterChange}
          handlePlatformAlertServiceFilterChange={handlePlatformAlertServiceFilterChange}
          handlePlatformAlertReceiverFilterChange={handlePlatformAlertReceiverFilterChange}
          handlePlatformAlertSeverityFilterChange={handlePlatformAlertSeverityFilterChange}
        />
      ) : (
        <Message data-testid="platform-alert-auth-loading">{t("common.loading")}</Message>
      )}

      <DlqRemediationPanel
        t={t}
        canReadInvestigationAdmin={canReadInvestigationAdminSurface}
        canManageInvestigationAdmin={canManageInvestigationAdminSurface}
        dlqFilterState={dlqFilterState}
        setDlqFilterState={setDlqFilterState}
        dlqFilterChain={dlqFilterChain}
        setDlqFilterChain={setDlqFilterChain}
        refreshDlq={refreshDlq}
        dlq={dlq}
        dlqMessage={dlqMessage}
        caseAuditHref={buildCaseAuditHref}
        caseEvidenceHref={buildCaseEvidenceHref}
        requeueDlqCase={requeueDlqCase}
        resolveDlqCase={resolveDlqCase}
        requeueingCaseId={requeueingCaseId}
        resolvingCaseId={resolvingCaseId}
      />

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

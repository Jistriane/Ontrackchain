"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { AppShell, Message, Panel, Pill } from "../../components/ui";
import { useI18n } from "../../components/i18n-provider";
import { canManageInvestigationAdmin, canReadInvestigationAdmin } from "../lib/authz";
import type { MessageKey } from "../lib/i18n";
import { fetchMonitoringMetricsPreview } from "../lib/monitoring-api";
import { buildCaseAuditHref, buildCaseEvidenceHref } from "../lib/operational-context";
import { fetchAuthContext, type AuthContext } from "../lib/ownership";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { DlqRemediationPanel } from "../monitoring/dlq-remediation-panel";
import { InvestigationOperationsPanel } from "../monitoring/investigation-operations-panel";
import { useMonitoringOperations } from "../monitoring/use-monitoring-operations";

export default function IncidentResponsePage() {
  const { t } = useI18n();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [authResolved, setAuthResolved] = useState(false);
  const [metricsText, setMetricsText] = useState("");
  const handoffAlertId = searchParams.get("alertId")?.trim() || null;
  const handoffAlertName = searchParams.get("alertName")?.trim() || null;
  const handoffSeverity = searchParams.get("severity")?.trim().toLowerCase() || null;
  const alertsReturnHref =
    handoffAlertId || handoffAlertName || handoffSeverity
      ? `/alerts?alertId=${encodeURIComponent(handoffAlertId ?? "")}&alertName=${encodeURIComponent(handoffAlertName ?? "")}&severity=${encodeURIComponent(handoffSeverity ?? "all")}`
      : "/alerts";
  const canReadIncidentResponse = authResolved ? canReadInvestigationAdmin(authContext?.role) : null;
  const canManageIncidentResponse = authResolved ? canManageInvestigationAdmin(authContext?.role) : null;
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
    refreshMetricsPreview,
    canReadInvestigationAdmin: canReadIncidentResponse,
    canManageInvestigationAdmin: canManageIncidentResponse
  });

  useEffect(() => {
    fetchAuthContext()
      .then((context) => setAuthContext(context))
      .catch(() => setAuthContext(null))
      .finally(() => setAuthResolved(true));
  }, []);

  async function refreshMetricsPreview() {
    if (!canReadIncidentResponse) {
      setMetricsText("");
      return;
    }
    setError(null);
    try {
      const text = await fetchMonitoringMetricsPreview();
      setMetricsText(text);
    } catch (cause) {
      setMetricsText("");
      setError(resolveApiErrorMessage(t, cause, t("monitoring.errors.loadMetrics" as MessageKey)));
    }
  }

  return (
    <AppShell
      title={t("incidentResponse.title" as MessageKey)}
      subtitle={t("incidentResponse.subtitle" as MessageKey)}
      activePath="/incident-response"
      actions={<Pill>{t("incidentResponse.active" as MessageKey)}</Pill>}
    >
      {error ? <Message tone="error">{error}</Message> : null}

      <Panel
        title={t("incidentResponse.handoff.title" as MessageKey)}
        description={t("incidentResponse.handoff.description" as MessageKey)}
      >
        {handoffAlertId || handoffAlertName || handoffSeverity ? (
          <div className="otc-monitoring-banner" data-testid="incident-response-handoff-context">
            <Message>
              {t("incidentResponse.handoff.contextSummary" as MessageKey, {
                alertId: handoffAlertId || t("common.notAvailable"),
                alertName: handoffAlertName || t("common.notAvailable"),
                severity: handoffSeverity || t("common.notAvailable")
              })}
            </Message>
          </div>
        ) : null}
        <div className="otc-monitoring-actions">
          <a className="otc-button otc-button--ghost" href="/monitoring" data-testid="incident-response-open-monitoring">
            {t("incidentResponse.handoff.openMonitoring" as MessageKey)}
          </a>
          <a className="otc-button" href={alertsReturnHref} data-testid="incident-response-open-alerts">
            {t(
              (handoffAlertId || handoffAlertName || handoffSeverity
                ? "incidentResponse.handoff.returnOrigin"
                : "incidentResponse.handoff.openAlerts") as MessageKey
            )}
          </a>
        </div>
      </Panel>

      <InvestigationOperationsPanel
        t={t}
        canReadInvestigationAdmin={canReadIncidentResponse}
        operations={operations}
        refreshOperations={refreshOperations}
        caseAuditHref={buildCaseAuditHref}
        caseEvidenceHref={buildCaseEvidenceHref}
        operationalAlerts={operationalAlerts}
        refreshOperationalAlerts={refreshOperationalAlerts}
        refreshMetricsPreview={refreshMetricsPreview}
        metricsText={metricsText}
        handoffAlertId={handoffAlertId}
        handoffAlertName={handoffAlertName}
        handoffSeverity={handoffSeverity}
      />

      <DlqRemediationPanel
        t={t}
        canReadInvestigationAdmin={canReadIncidentResponse}
        canManageInvestigationAdmin={canManageIncidentResponse}
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
    </AppShell>
  );
}

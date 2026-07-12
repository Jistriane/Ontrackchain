import { CodeBlock, Message, Panel } from "../../components/ui";
import type { MessageKey } from "../lib/i18n";
import type { OperationsSnapshot, OperationalAlertsSnapshot } from "../lib/monitoring-investigation-operations";

type Translator = (key: MessageKey, values?: Record<string, string | number>) => string;

type InvestigationOperationsPanelProps = {
  t: Translator;
  operations: OperationsSnapshot | null;
  refreshOperations: () => void;
  caseAuditHref: (caseId: string, reportId?: string | null) => string;
  caseEvidenceHref: (caseId: string, reportId?: string | null) => string;
  operationalAlerts: OperationalAlertsSnapshot | null;
  refreshOperationalAlerts: () => void;
  refreshMetricsPreview: () => void;
  metricsText: string;
};

const manualPackageMfaAuditHref =
  "/audit?preset=manual-package-mfa&action=evidence_manual_review_package_mfa_violation&resource_type=evidence_package_seal";

function hasWorkerSnapshotGeneratedAt(value: string | null | undefined) {
  return typeof value === "string" && value.trim().length > 0 && value !== "1970-01-01T00:00:00.000Z";
}

export function InvestigationOperationsPanel({
  t,
  operations,
  refreshOperations,
  caseAuditHref,
  caseEvidenceHref,
  operationalAlerts,
  refreshOperationalAlerts,
  refreshMetricsPreview,
  metricsText
}: InvestigationOperationsPanelProps) {
  return (
    <>
      <Panel title={t("monitoring.worker.title")}>
        <div className="otc-controls">
          <button type="button" data-testid="worker-refresh-btn" onClick={refreshOperations} className="otc-button otc-button--ghost">
            {t("monitoring.worker.refresh")}
          </button>
          <span data-testid="worker-generated-at" className="otc-monitoring-meta">
            {operations && hasWorkerSnapshotGeneratedAt(operations.generated_at)
              ? t("monitoring.worker.snapshot", { value: operations.generated_at })
              : t("monitoring.worker.noSnapshot")}
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
              <div data-testid="worker-metric-manual-package-mfa" className="otc-monitoring-card">
                <strong>{t("monitoring.worker.metricManualPackageMfa" as MessageKey)}</strong>
                <div>{t("monitoring.worker.metricManualPackageMfaTotal" as MessageKey)} {operations.security.manual_package_mfa_violations_last_hour}</div>
                <div>{t("monitoring.worker.metricManualPackageMfa2fa" as MessageKey)} {operations.security.manual_package_mfa_2fa_required_last_hour}</div>
                <div>{t("monitoring.worker.metricManualPackageMfaProvider" as MessageKey)} {operations.security.manual_package_mfa_provider_not_homologated_last_hour}</div>
                <div className="otc-monitoring-actions">
                  <a className="otc-button otc-button--ghost" href={manualPackageMfaAuditHref}>
                    {t("monitoring.worker.openAudit")}
                  </a>
                </div>
              </div>
            </div>

            <div className="otc-monitoring-spacer">
              <h3>{t("monitoring.worker.recent")}</h3>
              {operations.recent_cases.length ? (
                <div className="otc-monitoring-grid">
                  {operations.recent_cases.map((entry) => (
                    <div key={entry.case_id} data-testid="worker-case-row" className="otc-monitoring-card">
                      <div className="otc-monitoring-row">
                        <strong>{entry.status}</strong>
                        <span className="otc-monitoring-meta">{entry.created_at ?? t("common.noCreatedAt")}</span>
                      </div>
                      <div className="otc-monitoring-detail">
                        {entry.case_id} • {entry.target_chain} • {entry.report_type_canonical ?? t("common.notAvailable")}
                      </div>
                      <div className="otc-monitoring-detail--subtle">
                        {t("monitoring.worker.queue")}={entry.queue_state ?? t("common.notAvailable")} • {t("monitoring.worker.attempts")}=
                        {entry.attempt_count} • {t("monitoring.worker.duration")}={entry.duration_ms ?? 0}ms
                      </div>
                      {entry.last_error ? (
                        <div className="otc-monitoring-detail--subtle">{t("monitoring.worker.errorPrefix")}: {entry.last_error}</div>
                      ) : null}
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
    </>
  );
}

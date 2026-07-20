import { CodeBlock, Message, Panel } from "../../components/ui";
import { buildAlertRcaSummary } from "../lib/alert-rca";
import type { MessageKey } from "../lib/i18n";
import type {
  PlatformAlertExportFormat,
  PlatformOperationalAlertsSnapshot
} from "../lib/monitoring-platform-alerts";
import type { AlertsWorkItemMetadata, WorkItemResponse } from "../lib/work-items";

type Translator = (key: MessageKey, values?: Record<string, string | number>) => string;

type PlatformAlertTriagePanelProps = {
  t: Translator;
  canReadPlatformAdmin: boolean | null;
  canManagePlatformAdmin: boolean | null;
  platformAlertStatusFilter: string;
  platformAlertTriageFilter: string;
  platformAlertServiceFilter: string;
  platformAlertReceiverFilter: string;
  platformAlertSeverityFilter: string;
  platformAlertServiceOptions: string[];
  platformAlertReceiverOptions: string[];
  refreshPlatformOperationalAlerts: () => void;
  acknowledgeFilteredPlatformAlerts: () => void;
  acknowledgeSelectedPlatformAlerts: () => void;
  platformOperationalAlerts: PlatformOperationalAlertsSnapshot | null;
  platformAlertTrackedWorkItems: Record<string, WorkItemResponse<AlertsWorkItemMetadata>>;
  acknowledgingPlatformAlertsBatch: boolean;
  selectedPlatformAlertIds: string[];
  platformAlertExportFormat: PlatformAlertExportFormat;
  exportingPlatformAlerts: "filtered" | "selected" | null;
  setPlatformAlertExportFormat: (value: PlatformAlertExportFormat) => void;
  exportPlatformAlerts: (scope: "filtered" | "selected") => void;
  platformAlertPage: number;
  platformAlertTotalPages: number;
  platformAlertLoadError: string | null;
  goToPreviousPlatformAlertsPage: () => void;
  goToNextPlatformAlertsPage: () => void;
  platformAlertCursorHistoryLength: number;
  platformAlertMessage: string | null;
  allSelectablePlatformAlertsSelected: boolean;
  selectablePlatformAlertIds: string[];
  toggleAllSelectablePlatformAlerts: () => void;
  togglePlatformAlertSelection: (eventId: string) => void;
  translatePlatformSeverity: (severity: string | null) => string;
  translatePlatformStatus: (status: string) => string;
  translatePlatformTriage: (status: string) => string;
  translatePlatformQueueStatus: (status: string) => string;
  translatePlatformContainmentStatus: (status: string) => string;
  acknowledgingPlatformAlertId: string | null;
  acknowledgePlatformAlert: (eventId: string) => void;
  handlePlatformAlertStatusFilterChange: (value: string) => void;
  handlePlatformAlertTriageFilterChange: (value: string) => void;
  handlePlatformAlertServiceFilterChange: (value: string) => void;
  handlePlatformAlertReceiverFilterChange: (value: string) => void;
  handlePlatformAlertSeverityFilterChange: (value: string) => void;
};

export function PlatformAlertTriagePanel({
  t,
  canReadPlatformAdmin,
  canManagePlatformAdmin,
  platformAlertStatusFilter,
  platformAlertTriageFilter,
  platformAlertServiceFilter,
  platformAlertReceiverFilter,
  platformAlertSeverityFilter,
  platformAlertServiceOptions,
  platformAlertReceiverOptions,
  refreshPlatformOperationalAlerts,
  acknowledgeFilteredPlatformAlerts,
  acknowledgeSelectedPlatformAlerts,
  platformOperationalAlerts,
  platformAlertTrackedWorkItems,
  acknowledgingPlatformAlertsBatch,
  selectedPlatformAlertIds,
  platformAlertExportFormat,
  exportingPlatformAlerts,
  setPlatformAlertExportFormat,
  exportPlatformAlerts,
  platformAlertPage,
  platformAlertTotalPages,
  platformAlertLoadError,
  goToPreviousPlatformAlertsPage,
  goToNextPlatformAlertsPage,
  platformAlertCursorHistoryLength,
  platformAlertMessage,
  allSelectablePlatformAlertsSelected,
  selectablePlatformAlertIds,
  toggleAllSelectablePlatformAlerts,
  togglePlatformAlertSelection,
  translatePlatformSeverity,
  translatePlatformStatus,
  translatePlatformTriage,
  translatePlatformQueueStatus,
  translatePlatformContainmentStatus,
  acknowledgingPlatformAlertId,
  acknowledgePlatformAlert,
  handlePlatformAlertStatusFilterChange,
  handlePlatformAlertTriageFilterChange,
  handlePlatformAlertServiceFilterChange,
  handlePlatformAlertReceiverFilterChange,
  handlePlatformAlertSeverityFilterChange
}: PlatformAlertTriagePanelProps) {
  const canSelectPlatformAlerts = canManagePlatformAdmin === true;

  return (
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
        <button
          type="button"
          data-testid="platform-alerts-refresh-btn"
          onClick={refreshPlatformOperationalAlerts}
          className="otc-button otc-button--ghost"
        >
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
          </>
        ) : canManagePlatformAdmin === false ? (
          <Message data-testid="platform-alert-mutation-restricted">
            {t("monitoring.platform.mutationRestricted" as MessageKey)}
          </Message>
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
          disabled={!platformAlertCursorHistoryLength}
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

      {platformAlertLoadError ? (
        <div data-testid="platform-alert-load-error" className="otc-monitoring-banner">
          <Message tone="error">{platformAlertLoadError}</Message>
        </div>
      ) : platformOperationalAlerts ? (
        platformOperationalAlerts.data.length ? (
          <div className="otc-monitoring-grid otc-monitoring-banner">
            {canSelectPlatformAlerts ? (
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
              <div
                key={entry.id}
                data-testid="platform-alert-row"
                className={`otc-monitoring-card ${entry.status === "firing" ? "otc-monitoring-card--warning" : "otc-monitoring-card--success"}`}
              >
                {(() => {
                  const trackedWorkItem = platformAlertTrackedWorkItems[entry.id] ?? null;
                  const rcaSummary = buildAlertRcaSummary(trackedWorkItem);
                  return (
                    <>
                <div className="otc-monitoring-row">
                  <div className="otc-monitoring-inline">
                    {canSelectPlatformAlerts ? (
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
                  <span>
                    {translatePlatformSeverity(entry.severity)} • {translatePlatformStatus(entry.status)} •{" "}
                    {t("monitoring.platform.triageLabel")}={translatePlatformTriage(entry.triage_status)}
                  </span>
                </div>
                <div className="otc-monitoring-detail">
                  {t("monitoring.platform.service")}={entry.service ?? t("common.notAvailable")} • {t("monitoring.platform.receiver")}=
                  {entry.receiver} • {t("monitoring.platform.deliveries")}={entry.delivery_count}
                </div>
                <div className="otc-monitoring-detail--subtle">
                  {t("monitoring.platform.firstReceived")}={entry.first_received_at} • {t("monitoring.platform.lastReceived")}=
                  {entry.last_received_at}
                </div>
                {entry.resolved_at ? (
                  <div className="otc-monitoring-detail--subtle">{t("monitoring.platform.resolvedAt")}={entry.resolved_at}</div>
                ) : null}
                {entry.triaged_at ? (
                  <div className="otc-monitoring-detail--subtle">
                    {t("monitoring.platform.triagedAt")}={entry.triaged_at} {t("common.by")}{" "}
                    {entry.triaged_by ?? t("monitoring.platform.adminFallback")}
                  </div>
                ) : null}
                {entry.triage_note ? (
                  <div className="otc-monitoring-detail--subtle">{t("monitoring.platform.note")}: {entry.triage_note}</div>
                ) : null}
                {trackedWorkItem ? (
                  <div className="otc-monitoring-detail--subtle" data-testid={`monitoring-platform-alert-rca-summary-${entry.id}`}>
                    {t("monitoring.platform.rcaSummary", {
                      queue: translatePlatformQueueStatus(trackedWorkItem.queue_status),
                      containment: rcaSummary
                        ? translatePlatformContainmentStatus(rcaSummary.containmentStatus)
                        : t("monitoring.platform.rcaPendingShort"),
                      domain: rcaSummary?.domain || t("common.notAvailable"),
                      commander: rcaSummary?.incidentCommander || t("common.notAvailable")
                    })}
                    {rcaSummary?.affectedDomains.length
                      ? ` • ${t("monitoring.platform.rcaDomains")}=${rcaSummary.affectedDomains.join(", ")}`
                      : ""}
                    {rcaSummary?.confirmedRootCause
                      ? ` • ${t("monitoring.platform.rcaConfirmed")}=${rcaSummary.confirmedRootCause}`
                      : rcaSummary?.suspectedRootCause
                        ? ` • ${t("monitoring.platform.rcaSuspected")}=${rcaSummary.suspectedRootCause}`
                        : ` • ${t("monitoring.platform.rcaPending")}`}
                  </div>
                ) : null}
                {entry.annotations?.summary ? <div className="otc-monitoring-detail">{String(entry.annotations.summary)}</div> : null}
                {entry.annotations?.description ? (
                  <div className="otc-monitoring-detail--subtle">{String(entry.annotations.description)}</div>
                ) : null}
                <details className="otc-monitoring-detail">
                  <summary>{t("monitoring.platform.labels")}</summary>
                  <div data-testid="platform-alert-labels">
                    <CodeBlock>{JSON.stringify(entry.labels, null, 2)}</CodeBlock>
                  </div>
                </details>
                {canSelectPlatformAlerts ? (
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
                ) : null}
                    </>
                  );
                })()}
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
        </>
      )}
    </Panel>
  );
}

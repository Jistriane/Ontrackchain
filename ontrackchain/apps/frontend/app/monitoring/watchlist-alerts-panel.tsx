import { CodeBlock, Message, Panel } from "../../components/ui";
import type { MessageKey } from "../lib/i18n";
import type { Alert, Watchlist } from "../lib/monitoring-api";

type Translator = (key: MessageKey, values?: Record<string, string | number>) => string;

type WatchlistAlertsPanelProps = {
  t: Translator;
  canReadMonitoringCore: boolean | null;
  watchlists: Watchlist[];
  watchlistLoadError: string | null;
  alerts: Alert[];
  selectedAlert: Alert | null;
  setSelectedAlert: (alert: Alert | null) => void;
  refreshAlerts: () => void;
  triggerAlert: () => void;
  canTriggerTestAlert: boolean;
};

export function WatchlistAlertsPanel({
  t,
  canReadMonitoringCore,
  watchlists,
  watchlistLoadError,
  alerts,
  selectedAlert,
  setSelectedAlert,
  refreshAlerts,
  triggerAlert,
  canTriggerTestAlert
}: WatchlistAlertsPanelProps) {
  return (
    <>
      <Panel title={t("monitoring.watchlists.title")}>
        {canReadMonitoringCore === false ? (
          <div data-testid="monitoring-core-read-restricted">
            <Message>{t("monitoring.watchlists.readRestricted" as MessageKey)}</Message>
          </div>
        ) : watchlistLoadError ? (
          <div data-testid="watchlist-load-error">
            <Message tone="error">{watchlistLoadError}</Message>
          </div>
        ) : watchlists.length ? (
          <div data-testid="watchlist-item" className="otc-monitoring-card">
            {watchlists[0].name} ({watchlists[0].priority})
          </div>
        ) : (
          <div data-testid="watchlist-empty">
            <Message>{t("monitoring.watchlists.empty")}</Message>
          </div>
        )}
      </Panel>

      <Panel title={t("monitoring.alerts.title")}>
        {canReadMonitoringCore === false ? (
          <div data-testid="monitoring-alerts-read-restricted">
            <Message>{t("monitoring.watchlists.readRestricted" as MessageKey)}</Message>
          </div>
        ) : (
          <>
        <div className="otc-controls">
          <button type="button" onClick={refreshAlerts} className="otc-button otc-button--ghost">
            {t("monitoring.actions.refresh")}
          </button>
          {canTriggerTestAlert ? (
            <button type="button" data-testid="trigger-alert-btn" onClick={triggerAlert} className="otc-button otc-button--accent">
              {t("monitoring.actions.triggerAlert")}
            </button>
          ) : null}
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
            <CodeBlock>{JSON.stringify(selectedAlert, null, 2)}</CodeBlock>
          </div>
        ) : null}
          </>
        )}
      </Panel>
    </>
  );
}

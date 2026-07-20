"use client";

import { useEffect, useState } from "react";
import { useI18n } from "../../components/i18n-provider";
import {
  canManageMonitoringAdmin,
  canReadMonitoringCore,
  canReadMonitoringAdmin,
  canTriggerMonitoringTestAlert
} from "../lib/authz";
import { fetchAuthContext, type AuthContext } from "../lib/ownership";
import { AppShell, Message, Panel, Pill } from "../../components/ui";
import type { MessageKey } from "../lib/i18n";
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
  const { watchlists, watchlistLoadError, alerts, selectedAlert, setSelectedAlert, refreshAlerts, triggerAlert } =
    useMonitoringWatchlistAlerts({ t, setError, canReadMonitoringCore: canReadCoreMonitoringSurface, canTriggerTestAlert });
  const {
    platformOperationalAlerts,
    platformAlertLoadError,
    platformAlertTrackedWorkItems,
    refreshPlatformOperationalAlerts,
    platformAlertMessage
  } = useMonitoringPlatformAlerts({ t, setError, canReadPlatformAlerts: canReadPlatformAdmin, canManagePlatformAlerts: canManagePlatformAdmin });

  useEffect(() => {
    fetchAuthContext()
      .then((context) => setAuthContext(context))
      .catch(() => setAuthContext(null))
      .finally(() => setAuthResolved(true));
  }, []);

  const pendingPlatformAlerts =
    platformOperationalAlerts?.data.filter((entry) => entry.triage_status === "pending").length ?? 0;
  const acknowledgedPlatformAlerts =
    platformOperationalAlerts?.data.filter((entry) => entry.triage_status === "acknowledged").length ?? 0;
  const trackedPlatformAlerts = Object.keys(platformAlertTrackedWorkItems).length;

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
        watchlistLoadError={watchlistLoadError}
        alerts={alerts}
        selectedAlert={selectedAlert}
        setSelectedAlert={setSelectedAlert}
        refreshAlerts={refreshAlerts}
        triggerAlert={triggerAlert}
        canTriggerTestAlert={canTriggerTestAlert}
      />

      <Panel
        title={t("monitoring.incidentResponse.title" as MessageKey)}
        description={t("monitoring.incidentResponse.description" as MessageKey)}
      >
        {canReadPlatformAdmin ? (
          <div className="otc-monitoring-actions" data-testid="monitoring-incident-response-actions">
            <a className="otc-button" href="/incident-response" data-testid="monitoring-open-incident-response">
              {t("monitoring.incidentResponse.openRoute" as MessageKey)}
            </a>
            <a className="otc-button otc-button--ghost" href="/alerts" data-testid="monitoring-open-alerts-from-incident-response">
              {t("monitoring.incidentResponse.openAlerts" as MessageKey)}
            </a>
          </div>
        ) : canReadPlatformAdmin === false ? (
          <Message data-testid="monitoring-incident-response-restricted">
            {t("monitoring.incidentResponse.restricted" as MessageKey)}
          </Message>
        ) : (
          <Message data-testid="monitoring-incident-response-loading">{t("common.loading")}</Message>
        )}
      </Panel>

      <Panel
        title={t("monitoring.globalAlerts.title" as MessageKey)}
        description={t("monitoring.globalAlerts.description" as MessageKey)}
      >
        {canReadPlatformAdmin === false ? (
          <Message data-testid="monitoring-global-alerts-restricted">
            {t("monitoring.platform.readRestricted" as MessageKey)}
          </Message>
        ) : !authResolved ? (
          <Message data-testid="monitoring-global-alerts-loading">{t("common.loading")}</Message>
        ) : (
          <>
            <div className="otc-monitoring-actions" data-testid="monitoring-global-alerts-actions">
              <a className="otc-button" href="/alerts" data-testid="monitoring-open-global-alerts">
                {t("monitoring.globalAlerts.openRoute" as MessageKey)}
              </a>
              <button
                type="button"
                data-testid="monitoring-global-alerts-refresh"
                onClick={() => {
                  void refreshPlatformOperationalAlerts();
                }}
                className="otc-button otc-button--ghost"
              >
                {t("monitoring.globalAlerts.refresh" as MessageKey)}
              </button>
            </div>

            {platformAlertMessage ? (
              <div data-testid="monitoring-global-alerts-message" className="otc-monitoring-banner">
                <Message tone="success">{platformAlertMessage}</Message>
              </div>
            ) : null}

            {platformAlertLoadError ? (
              <div data-testid="monitoring-global-alerts-load-error" className="otc-monitoring-banner">
                <Message tone="error">{platformAlertLoadError}</Message>
              </div>
            ) : platformOperationalAlerts ? (
              <div className="otc-metric-grid" data-testid="monitoring-global-alerts-summary">
                <div className="otc-metric-card">
                  <span className="otc-metric-card__label">{t("monitoring.globalAlerts.total" as MessageKey)}</span>
                  <strong data-testid="monitoring-global-alerts-total">{platformOperationalAlerts.total_count}</strong>
                </div>
                <div className="otc-metric-card">
                  <span className="otc-metric-card__label">{t("monitoring.globalAlerts.pending" as MessageKey)}</span>
                  <strong data-testid="monitoring-global-alerts-pending">{pendingPlatformAlerts}</strong>
                </div>
                <div className="otc-metric-card">
                  <span className="otc-metric-card__label">{t("monitoring.globalAlerts.acknowledged" as MessageKey)}</span>
                  <strong data-testid="monitoring-global-alerts-acknowledged">{acknowledgedPlatformAlerts}</strong>
                </div>
                <div className="otc-metric-card">
                  <span className="otc-metric-card__label">{t("monitoring.globalAlerts.tracked" as MessageKey)}</span>
                  <strong data-testid="monitoring-global-alerts-tracked">{trackedPlatformAlerts}</strong>
                </div>
              </div>
            ) : (
              <div data-testid="monitoring-global-alerts-empty" className="otc-monitoring-banner">
                <Message>{t("monitoring.platform.loading" as MessageKey)}</Message>
              </div>
            )}
          </>
        )}
      </Panel>
    </AppShell>
  );
}

import { useEffect, useState } from "react";
import type { MessageKey } from "../lib/i18n";
import {
  fetchMonitoringAlerts,
  fetchMonitoringWatchlistItems,
  fetchMonitoringWatchlists,
  type Alert,
  type Watchlist,
  type WatchlistItem
} from "../lib/monitoring-api";

type Translator = (key: MessageKey, values?: Record<string, string | number>) => string;

type UseMonitoringWatchlistAlertsArgs = {
  t: Translator;
  setError: (value: string | null) => void;
};

export function useMonitoringWatchlistAlerts({ t, setError }: UseMonitoringWatchlistAlertsArgs) {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [watchlistItems, setWatchlistItems] = useState<WatchlistItem[]>([]);

  useEffect(() => {
    fetchMonitoringWatchlists()
      .then((data) => setWatchlists(data))
      .catch(() => setError(t("monitoring.errors.loadWatchlists")));
  }, [setError, t]);

  useEffect(() => {
    const primaryWatchlistId = watchlists[0]?.id;
    if (!primaryWatchlistId) {
      setWatchlistItems([]);
      return;
    }

    fetchMonitoringWatchlistItems(primaryWatchlistId)
      .then((items) => setWatchlistItems(items))
      .catch(() => setError(t("monitoring.errors.loadWatchlists")));
  }, [setError, t, watchlists]);

  async function refreshAlerts() {
    setError(null);
    try {
      const data = await fetchMonitoringAlerts(watchlists[0]?.id);
      setAlerts(data);
    } catch {
      setError(t("monitoring.errors.loadAlerts"));
    }
  }

  async function triggerAlert() {
    const watchlist = watchlists[0];
    if (!watchlist) {
      setError(t("monitoring.errors.noWatchlist"));
      return;
    }
    const watchlistItem = watchlistItems[0];
    if (!watchlistItem) {
      setError(t("monitoring.errors.noWatchlistItems"));
      return;
    }

    const response = await fetch("/api/app/monitoring/trigger-alert", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        watchlist_id: watchlist.id,
        address: watchlistItem.address,
        chain: watchlistItem.chain,
        severity: "high",
        title: t("monitoring.testAlertTitle"),
        details: { source: "test", watchlist_item_id: watchlistItem.id }
      })
    });

    if (!response.ok) {
      setError(t("monitoring.errors.triggerAlert"));
      return;
    }

    await refreshAlerts();
  }

  return {
    watchlists,
    alerts,
    selectedAlert,
    setSelectedAlert,
    refreshAlerts,
    triggerAlert
  };
}

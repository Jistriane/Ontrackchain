import type { DlqSnapshot } from "./monitoring-dlq";
import type { OperationsSnapshot, OperationalAlertsSnapshot } from "./monitoring-investigation-operations";
import type {
  PlatformAlertFilterState,
  PlatformOperationalAlertFilterOptions,
  PlatformOperationalAlertsSnapshot
} from "./monitoring-platform-alerts";

export type Watchlist = {
  id: string;
  name: string;
  priority: string;
};

export type WatchlistItem = {
  id: string;
  watchlist_id: string;
  address: string;
  chain: string;
  created_at: string;
};

export type Alert = {
  id: string;
  watchlist_id: string;
  address: string;
  chain: string;
  severity: string;
  title: string;
  details: any;
  created_at: string;
};

async function parseJsonResponse(response: Response) {
  return response.json().catch(() => null);
}

function tryParseJsonText(text: string) {
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return null;
  }
}

function throwMonitoringPayload(data: unknown, fallbackCode: string): never {
  throw (data ?? { detail: fallbackCode });
}

export async function fetchMonitoringWatchlists() {
  const response = await fetch("/api/app/monitoring/watchlists", { cache: "no-store" });
  const data = await parseJsonResponse(response);
  if (!response.ok) {
    throwMonitoringPayload(data, "loadWatchlists");
  }
  return (data?.data ?? []) as Watchlist[];
}

export async function fetchMonitoringAlerts(watchlistId?: string | null) {
  const query = watchlistId?.trim() ? `?watchlist_id=${encodeURIComponent(watchlistId)}&limit=50` : "?limit=50";
  const response = await fetch(`/api/app/monitoring/alerts${query}`, { cache: "no-store" });
  const data = await parseJsonResponse(response);
  if (!response.ok) {
    throwMonitoringPayload(data, "loadAlerts");
  }
  return (data?.data ?? []) as Alert[];
}

export async function fetchMonitoringWatchlistItems(watchlistId: string, limit = 20) {
  const response = await fetch(
    `/api/app/monitoring/watchlists/${encodeURIComponent(watchlistId)}/items?limit=${encodeURIComponent(String(limit))}`,
    { cache: "no-store" }
  );
  const data = await parseJsonResponse(response);
  if (!response.ok) {
    throwMonitoringPayload(data, "loadWatchlistItems");
  }
  return (data?.data ?? []) as WatchlistItem[];
}

export async function fetchMonitoringOperations() {
  const response = await fetch("/api/app/investigation/operations", { cache: "no-store" });
  const data = await parseJsonResponse(response);
  if (!response.ok) {
    throwMonitoringPayload(data, "loadWorkerOperations");
  }
  return data as OperationsSnapshot;
}

export async function fetchMonitoringOperationalAlerts() {
  const response = await fetch("/api/app/investigation/alerts", { cache: "no-store" });
  const data = await parseJsonResponse(response);
  if (!response.ok) {
    throwMonitoringPayload(data, "loadOperationalAlerts");
  }
  return data as OperationalAlertsSnapshot;
}

export async function fetchMonitoringPlatformAlertFilterOptions() {
  const response = await fetch("/api/app/monitoring/operational-alert-filter-options", { cache: "no-store" });
  const data = await parseJsonResponse(response);
  if (!response.ok) {
    throwMonitoringPayload(data, "loadPlatformFilterOptions");
  }
  return data as PlatformOperationalAlertFilterOptions;
}

export async function fetchMonitoringPlatformOperationalAlerts(
  filters: PlatformAlertFilterState,
  cursor: string | null
) {
  const params = new URLSearchParams();
  if (filters.status !== "all") {
    params.set("status", filters.status);
  }
  if (filters.triageStatus !== "all") {
    params.set("triage_status", filters.triageStatus);
  }
  if (filters.service !== "all") {
    params.set("service", filters.service);
  }
  if (filters.receiver !== "all") {
    params.set("receiver", filters.receiver);
  }
  if (filters.severity !== "all") {
    params.set("severity", filters.severity);
  }
  if (cursor) {
    params.set("cursor", cursor);
  }
  params.set("limit", "20");

  const response = await fetch(`/api/app/monitoring/operational-alerts?${params.toString()}`, { cache: "no-store" });
  const data = await parseJsonResponse(response);
  if (!response.ok) {
    throwMonitoringPayload(data, "loadPlatformAlerts");
  }
  return data as PlatformOperationalAlertsSnapshot;
}

export async function fetchMonitoringMetricsPreview() {
  const response = await fetch("/api/app/investigation/metrics", { cache: "no-store" });
  const text = await response.text();
  if (!response.ok) {
    throwMonitoringPayload(tryParseJsonText(text), "loadMetrics");
  }
  return text;
}

export async function fetchMonitoringDlq(state: string, chain: string) {
  const params = new URLSearchParams();
  params.set("state", state);
  if (chain !== "all") {
    params.set("target_chain", chain);
  }

  const response = await fetch(`/api/app/investigation/dlq?${params.toString()}`, { cache: "no-store" });
  const data = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error("loadDlq");
  }
  return data as DlqSnapshot;
}

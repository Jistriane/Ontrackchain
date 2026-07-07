export const PLATFORM_ALERT_SELECTION_STORAGE_KEY = "monitoring-platform-alert-selection";

export type PlatformAlertFilterState = {
  status: string;
  triageStatus: string;
  service: string;
  receiver: string;
  severity: string;
};

export type PlatformOperationalAlertsSnapshot = {
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

export type PlatformOperationalAlertFilterOptions = {
  services: string[];
  receivers: string[];
  generated_at: string;
};

export type PlatformAlertExportFormat = "csv" | "json";

export type PersistedPlatformAlertSelectionState = PlatformAlertFilterState & {
  cursor: string | null;
  cursorHistory: Array<string | null>;
  selectedIds: string[];
  selectionScope: string | null;
};

export function defaultPlatformAlertSelectionState(): PersistedPlatformAlertSelectionState {
  return {
    status: "all",
    triageStatus: "all",
    service: "all",
    receiver: "all",
    severity: "all",
    cursor: null,
    cursorHistory: [],
    selectedIds: [],
    selectionScope: null
  };
}

export function buildPlatformAlertSelectionScope(filters: PlatformAlertFilterState) {
  return JSON.stringify(filters);
}

export function clearPersistedPlatformAlertSelection(storage: Storage) {
  storage.removeItem(PLATFORM_ALERT_SELECTION_STORAGE_KEY);
}

export function readPersistedPlatformAlertSelection(storage: Storage): PersistedPlatformAlertSelectionState | null {
  const raw = storage.getItem(PLATFORM_ALERT_SELECTION_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  const parsed = JSON.parse(raw) as Partial<PersistedPlatformAlertSelectionState>;
  return {
    status: parsed.status ?? "all",
    triageStatus: parsed.triageStatus ?? "all",
    service: parsed.service ?? "all",
    receiver: parsed.receiver ?? "all",
    severity: parsed.severity ?? "all",
    cursor: typeof parsed.cursor === "string" ? parsed.cursor : null,
    cursorHistory: Array.isArray(parsed.cursorHistory)
      ? parsed.cursorHistory.filter((entry): entry is string | null => typeof entry === "string" || entry === null)
      : [],
    selectedIds: Array.isArray(parsed.selectedIds) ? parsed.selectedIds.filter((entry): entry is string => typeof entry === "string") : [],
    selectionScope: typeof parsed.selectionScope === "string" ? parsed.selectionScope : null
  };
}

export function resolveInitialPlatformAlertSelectionState(storage?: Storage | null) {
  const defaults = defaultPlatformAlertSelectionState();
  if (!storage) {
    return defaults;
  }

  try {
    return readPersistedPlatformAlertSelection(storage) ?? defaults;
  } catch {
    clearPersistedPlatformAlertSelection(storage);
    return defaults;
  }
}

export function shouldPersistPlatformAlertSelection(state: PersistedPlatformAlertSelectionState) {
  return Boolean(
    state.selectedIds.length || state.selectionScope || state.cursor || state.cursorHistory.length
  );
}

export function writePersistedPlatformAlertSelection(storage: Storage, state: PersistedPlatformAlertSelectionState) {
  storage.setItem(PLATFORM_ALERT_SELECTION_STORAGE_KEY, JSON.stringify(state));
}

export function loadWorkspaceRecords<T>(
  storageKey: string,
  parseRecord: (record: Partial<T>) => T
): T[] {
  void storageKey;
  void parseRecord;
  return [];
}

export function saveWorkspaceRecords<T>(storageKey: string, records: T[]) {
  void storageKey;
  void records;
}

export function toDateTimeLocalValue(value: string | null | undefined) {
  if (!value) {
    return "";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }

  const year = parsed.getFullYear();
  const month = `${parsed.getMonth() + 1}`.padStart(2, "0");
  const day = `${parsed.getDate()}`.padStart(2, "0");
  const hours = `${parsed.getHours()}`.padStart(2, "0");
  const minutes = `${parsed.getMinutes()}`.padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export function toApiDueAt(value: string) {
  const normalized = value.trim();
  if (!normalized) {
    return null;
  }

  const parsed = new Date(normalized);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return parsed.toISOString();
}

export function sortByLastActionAtDesc<T extends { lastActionAt?: string | null }>(records: T[]): T[] {
  return [...records].sort((left, right) => (right.lastActionAt || "").localeCompare(left.lastActionAt || ""));
}

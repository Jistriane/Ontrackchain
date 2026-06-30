import { expect, type Page } from "@playwright/test";

export type AuditEntry = {
  action?: string;
  request_id?: string;
  user_id?: string | null;
  resource_type?: string | null;
  metadata?: Record<string, any>;
  [key: string]: any;
};

type AuditQuery = {
  limit?: number;
  action?: string;
  requestId?: string;
};

function buildAuditLogsUrl(query: AuditQuery = {}) {
  const params = new URLSearchParams();
  if (query.limit) params.set("limit", String(query.limit));
  if (query.action) params.set("action", query.action);
  if (query.requestId) params.set("request_id", query.requestId);
  const serialized = params.toString();
  return serialized ? `/api/app/audit/logs?${serialized}` : "/api/app/audit/logs";
}

export async function getAuditLogs(page: Page, query: AuditQuery = {}) {
  const res = await page.request.get(buildAuditLogsUrl(query));
  expect(res.status()).toBe(200);
  const body = (await res.json()) as { data?: AuditEntry[] };
  return body.data ?? [];
}

export function normalizeAuditEntries(entries: AuditEntry[]) {
  return entries.map((entry) => ({
    ...entry,
    request_id: entry.metadata?.request_id ?? entry.request_id
  }));
}

export function findAuditEntriesByRequestId(entries: AuditEntry[], requestId: string, action?: string) {
  return normalizeAuditEntries(entries).filter((entry) => {
    const matchesRequest = entry.request_id === requestId;
    const matchesAction = action ? entry.action === action : true;
    return matchesRequest && matchesAction;
  });
}

export async function getAuditEntriesByRequestId(page: Page, requestId: string, action: string, limit = 20) {
  return getAuditLogs(page, { requestId, action, limit });
}

export async function waitForAuditEntriesByRequestId(
  page: Page,
  requestId: string,
  action: string,
  timeout = 10_000
) {
  await expect.poll(async () => (await getAuditEntriesByRequestId(page, requestId, action)).length, { timeout }).toBeGreaterThan(0);
  return getAuditEntriesByRequestId(page, requestId, action);
}

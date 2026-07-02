export type AuditLogEntry = {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  request_id: string | null;
  report_id: string | null;
  file_hash_sha256: string | null;
  metadata: Record<string, unknown>;
  created_at: string | null;
};

export type AuditLogsResponse = {
  data: AuditLogEntry[];
  page: number;
  count: number;
  limit: number;
  total: number;
  total_pages: number;
  has_more: boolean;
  filters?: Record<string, string | null>;
};

export type AuditLogQueryFilters = {
  requestId: string;
  action: string;
  resourceType: string;
  reportId: string;
  resourceId: string;
  limit: string;
};

export function buildAuditLogQuery(filters: AuditLogQueryFilters, page: number) {
  const params = new URLSearchParams();
  if (filters.requestId.trim()) params.set("request_id", filters.requestId.trim());
  if (filters.action.trim()) params.set("action", filters.action.trim());
  if (filters.resourceType.trim()) params.set("resource_type", filters.resourceType.trim());
  if (filters.reportId.trim()) params.set("report_id", filters.reportId.trim());
  if (filters.resourceId.trim()) params.set("resource_id", filters.resourceId.trim());
  params.set("page", String(page));
  params.set("limit", filters.limit);
  return params.toString();
}

export function extractAuditApiError(payload: AuditLogsResponse | { error?: string } | null) {
  if (payload && "error" in payload && typeof payload.error === "string" && payload.error.trim()) {
    return payload.error;
  }

  return null;
}

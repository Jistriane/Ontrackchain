"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useI18n } from "../../components/i18n-provider";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";

type AuditLogEntry = {
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

type AuditResponse = {
  data: AuditLogEntry[];
  page: number;
  count: number;
  limit: number;
  total: number;
  total_pages: number;
  has_more: boolean;
  filters?: Record<string, string | null>;
};

type AuditFilters = {
  requestId: string;
  action: string;
  resourceType: string;
  reportId: string;
  resourceId: string;
  limit: string;
};

const DEFAULT_FILTERS: AuditFilters = {
  requestId: "",
  action: "",
  resourceType: "",
  reportId: "",
  resourceId: "",
  limit: "50"
};

function buildQuery(filters: AuditFilters, page: number) {
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

export default function AuditPage() {
  const { t } = useI18n();
  const [filters, setFilters] = useState<AuditFilters>(DEFAULT_FILTERS);
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [count, setCount] = useState(0);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);
  const latestRequestRef = useRef(0);

  async function fetchLogs(nextFilters: AuditFilters, page = 1) {
    const requestNumber = latestRequestRef.current + 1;
    latestRequestRef.current = requestNumber;
    setLoading(true);
    setError(null);
    setNotice(null);
    const query = buildQuery(nextFilters, page);
    const res = await fetch(`/api/app/audit/logs?${query}`, { cache: "no-store" });
    const data = (await res.json().catch(() => null)) as AuditResponse | { error?: string } | null;
    if (requestNumber !== latestRequestRef.current) {
      return;
    }
    if (!res.ok) {
      setLogs([]);
      setCount(0);
      setTotal(0);
      setCurrentPage(1);
      setTotalPages(1);
      setHasMore(false);
      setSelectedLog(null);
      setError(
        data && "error" in data && data.error
          ? t("audit.errorLoadWithMessage", { message: resolveApiErrorMessage(t, data.error, data.error) })
          : t("audit.errorLoad")
      );
      setLoading(false);
      return;
    }

    const payload = data && "data" in data ? data : null;
    const rows = payload?.data ?? [];
    setLogs(rows);
    setCount(Number(payload?.count ?? rows.length));
    setTotal(Number(payload?.total ?? rows.length));
    setCurrentPage(Number(payload?.page ?? page));
    setTotalPages(Math.max(1, Number(payload?.total_pages ?? 1)));
    setHasMore(Boolean(payload?.has_more));
    setSelectedLog((current) => rows.find((entry) => entry.id === current?.id) ?? rows[0] ?? null);
    setLoading(false);
  }

  useEffect(() => {
    fetchLogs(DEFAULT_FILTERS).catch(() => {
      if (latestRequestRef.current > 1) {
        return;
      }
      setError(t("audit.errorLoad"));
      setLoading(false);
    });
  }, [t]);

  const activeFilterCount = useMemo(() => {
    return [filters.requestId, filters.action, filters.resourceType, filters.reportId, filters.resourceId].filter((value) => value.trim()).length;
  }, [filters]);

  function updateFilter<K extends keyof AuditFilters>(key: K, value: AuditFilters[K]) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  async function onSearch() {
    await fetchLogs(filters, 1);
  }

  async function onReset() {
    setFilters(DEFAULT_FILTERS);
    await fetchLogs(DEFAULT_FILTERS, 1);
  }

  async function onPreviousPage() {
    if (currentPage <= 1 || loading) {
      return;
    }
    await fetchLogs(filters, currentPage - 1);
  }

  async function onNextPage() {
    if (!hasMore || loading) {
      return;
    }
    await fetchLogs(filters, currentPage + 1);
  }

  async function onExportEvidence() {
    setExporting(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch("/api/app/audit/evidence-export", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          format: "json",
          request_id: filters.requestId.trim() || null,
          action: filters.action.trim() || null,
          resource_type: filters.resourceType.trim() || null,
          report_id: filters.reportId.trim() || null,
          resource_id: filters.resourceId.trim() || null,
          limit: Number(filters.limit),
          include_audit_logs: true,
          include_credit_ledger: true,
          include_reports: true
        })
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as { error?: string } | null;
        throw new Error(
          data?.error ? resolveApiErrorMessage(t, data.error, data.error) : t("audit.errorExport")
        );
      }

      const blob = await res.blob();
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      const disposition = res.headers.get("content-disposition");
      const filenameMatch = disposition?.match(/filename="([^"]+)"/);
      link.href = href;
      link.download = filenameMatch?.[1] ?? "ontrackchain-evidence-bundle.json";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(href);
      setNotice(t("audit.export.success"));
    } catch (exportError) {
      setError(exportError instanceof Error ? exportError.message : t("audit.errorExport"));
    } finally {
      setExporting(false);
    }
  }

  return (
    <AppShell
      title={t("audit.title")}
      subtitle={t("audit.subtitle")}
      activePath="/audit"
      actions={<a href="/dashboard" className="otc-link-button">{t("audit.back")}</a>}
    >
      <MetricGrid>
        <MetricCard label={t("audit.stats.events")} value={loading ? "..." : count} meta={t("audit.stats.eventsMeta")} />
        <MetricCard label={t("audit.stats.total")} value={loading ? "..." : total} meta={t("audit.stats.totalMeta")} />
        <MetricCard label={t("audit.stats.filters")} value={activeFilterCount} meta={t("audit.stats.filtersMeta")} />
        <MetricCard label={t("audit.stats.selected")} value={selectedLog?.action ?? "--"} meta={t("audit.stats.selectedMeta")} />
        <MetricCard label={t("audit.stats.integrity")} value={selectedLog?.file_hash_sha256 ? "SHA-256" : t("audit.notAvailable")} meta={t("audit.stats.integrityMeta")} accent />
      </MetricGrid>

      <Panel title={t("audit.filters.title")} description={t("audit.filters.description")}>
        <div className="otc-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
          <label className="otc-field">
            {t("audit.filters.requestId")}
            <input className="otc-input" data-testid="audit-filter-request-id" value={filters.requestId} onChange={(e) => updateFilter("requestId", e.target.value)} />
          </label>
          <label className="otc-field">
            {t("audit.filters.action")}
            <select className="otc-select" data-testid="audit-filter-action" value={filters.action} onChange={(e) => updateFilter("action", e.target.value)}>
              <option value="">{t("audit.filters.all")}</option>
              <option value="case_started">case_started</option>
              <option value="case_completed">case_completed</option>
              <option value="case_failed">case_failed</option>
              <option value="report_generated">report_generated</option>
              <option value="report_downloaded">report_downloaded</option>
            </select>
          </label>
          <label className="otc-field">
            {t("audit.filters.resourceType")}
            <select className="otc-select" data-testid="audit-filter-resource-type" value={filters.resourceType} onChange={(e) => updateFilter("resourceType", e.target.value)}>
              <option value="">{t("audit.filters.allMasculine")}</option>
              <option value="case">case</option>
              <option value="report">report</option>
            </select>
          </label>
          <label className="otc-field">
            {t("audit.filters.reportId")}
            <input className="otc-input" data-testid="audit-filter-report-id" value={filters.reportId} onChange={(e) => updateFilter("reportId", e.target.value)} />
          </label>
          <label className="otc-field">
            {t("audit.filters.resourceId")}
            <input className="otc-input" data-testid="audit-filter-resource-id" value={filters.resourceId} onChange={(e) => updateFilter("resourceId", e.target.value)} />
          </label>
          <label className="otc-field">
            {t("audit.filters.limit")}
            <select className="otc-select" data-testid="audit-filter-limit" value={filters.limit} onChange={(e) => updateFilter("limit", e.target.value)}>
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="200">200</option>
            </select>
          </label>
        </div>
        <div className="otc-controls" style={{ marginTop: 16 }}>
          <button type="button" className="otc-button otc-button--accent" data-testid="audit-search-btn" onClick={() => void onSearch()}>
            {t("audit.actions.search")}
          </button>
          <button type="button" className="otc-button otc-button--ghost" data-testid="audit-reset-btn" onClick={() => void onReset()}>
            {t("audit.actions.reset")}
          </button>
          <button type="button" className="otc-button otc-button--ghost" data-testid="audit-export-btn" onClick={() => void onExportEvidence()} disabled={exporting}>
            {exporting ? t("audit.actions.exportLoading") : t("audit.actions.export")}
          </button>
          <span data-testid="audit-summary" className="otc-muted">
            {loading ? t("audit.summary.loading") : t("audit.summary.found", { count: total })}
            {activeFilterCount ? t("audit.summary.activeFilters", { count: activeFilterCount }) : ""}
          </span>
        </div>
      </Panel>

      {error ? <Message tone="error"><span data-testid="audit-error">{error}</span></Message> : null}
      {notice ? <Message tone="success"><span data-testid="audit-export-notice">{notice}</span></Message> : null}

      <section className="otc-grid" style={{ gridTemplateColumns: "minmax(0, 1.5fr) minmax(320px, 1fr)" }}>
        <Panel title={t("audit.events.title")} description={t("audit.events.description")}>
          <div className="otc-controls" style={{ marginBottom: 16 }}>
            <button
              type="button"
              className="otc-button otc-button--ghost"
              data-testid="audit-prev-page-btn"
              onClick={() => void onPreviousPage()}
              disabled={loading || currentPage <= 1}
            >
              {t("audit.pagination.previous")}
            </button>
            <button
              type="button"
              className="otc-button otc-button--ghost"
              data-testid="audit-next-page-btn"
              onClick={() => void onNextPage()}
              disabled={loading || !hasMore}
            >
              {t("audit.pagination.next")}
            </button>
            <span data-testid="audit-page-summary" className="otc-muted">
              {t("audit.pagination.summary", { page: currentPage, totalPages, total })}
            </span>
          </div>
          {logs.length ? (
            <div className="otc-stack">
              {logs.map((entry) => {
                const isSelected = entry.id === selectedLog?.id;
                return (
                  <button
                    key={entry.id}
                    type="button"
                    data-testid="audit-row"
                    onClick={() => setSelectedLog(entry)}
                    style={{ textAlign: "left", borderColor: isSelected ? "rgba(70, 220, 255, 0.55)" : undefined }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                      <strong>{entry.action}</strong>
                      <span className="otc-muted">{entry.created_at ?? t("audit.noTimestamp")}</span>
                    </div>
                    <div style={{ marginTop: 8 }}>{entry.resource_type}{entry.resource_id ? ` • ${entry.resource_id}` : ""}</div>
                    <div className="otc-muted" style={{ marginTop: 8 }}>request_id: {entry.request_id ?? t("audit.notAvailable")}</div>
                    <div className="otc-muted" style={{ marginTop: 4 }}>report_id: {entry.report_id ?? t("audit.notAvailable")}</div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div data-testid="audit-empty" className="otc-message">{t("audit.events.empty")}</div>
          )}
        </Panel>

        <Panel title={t("audit.details.title")} description={t("audit.details.description")}>
          {selectedLog ? (
            <div data-testid="audit-details-panel" className="otc-stack">
              <div><strong>{t("audit.details.action")}:</strong> {selectedLog.action}</div>
              <div><strong>{t("audit.details.resourceType")}:</strong> {selectedLog.resource_type}</div>
              <div><strong>{t("audit.details.resourceId")}:</strong> {selectedLog.resource_id ?? t("audit.notAvailable")}</div>
              <div><strong>{t("audit.details.requestId")}:</strong> {selectedLog.request_id ?? t("audit.notAvailable")}</div>
              <div><strong>{t("audit.details.reportId")}:</strong> {selectedLog.report_id ?? t("audit.notAvailable")}</div>
              <div><strong>{t("audit.details.sha")}:</strong> {selectedLog.file_hash_sha256 ?? t("audit.notAvailable")}</div>
              <div style={{ marginTop: 8 }}>
                <Pill>{selectedLog.resource_type}</Pill>
              </div>
              <CodeBlock>
                <span data-testid="audit-metadata">{JSON.stringify(selectedLog.metadata, null, 2)}</span>
              </CodeBlock>
            </div>
          ) : (
            <div className="otc-message">{t("audit.details.empty")}</div>
          )}
        </Panel>
      </section>
    </AppShell>
  );
}

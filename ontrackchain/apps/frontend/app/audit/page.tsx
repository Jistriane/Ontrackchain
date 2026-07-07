"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useI18n } from "../../components/i18n-provider";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import {
  AUDIT_ACTION_VALUES,
  AUDIT_RESOURCE_TYPE_VALUES,
  isAuditActionValue,
  isAuditResourceTypeValue
} from "../lib/audit-catalog";
import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import {
  buildAuditLogQuery,
  extractAuditApiError,
  type AuditLogEntry,
  type AuditLogQueryFilters,
  type AuditLogsResponse
} from "../lib/audit-log";
import {
  buildOperationalContextLinks,
  type OperationalContextLink,
  inferLogOperationalContext
} from "../lib/operational-context";
import type { MessageKey } from "../lib/i18n";
type AuditFilters = AuditLogQueryFilters;

const DEFAULT_FILTERS: AuditFilters = {
  requestId: "",
  action: "",
  resourceType: "",
  reportId: "",
  resourceId: "",
  limit: "50"
};

export default function AuditPage() {
  const { t } = useI18n();
  const searchParams = useSearchParams();
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

  function resolveAuditActionLabel(value: string) {
    if (!value.trim()) {
      return t("audit.notAvailable");
    }
    return isAuditActionValue(value) ? t(`audit.values.actions.${value}` as MessageKey) : value;
  }

  function resolveAuditResourceTypeLabel(value: string) {
    if (!value.trim()) {
      return t("audit.notAvailable");
    }
    return isAuditResourceTypeValue(value) ? t(`audit.values.resourceTypes.${value}` as MessageKey) : value;
  }

  function formatAuditValue(value: string, label: string) {
    if (!value.trim()) {
      return t("audit.notAvailable");
    }
    return label === value ? value : `${label} (${value})`;
  }

  function formatAuditActionValue(value: string) {
    return formatAuditValue(value, resolveAuditActionLabel(value));
  }

  function formatAuditResourceTypeValue(value: string) {
    return formatAuditValue(value, resolveAuditResourceTypeLabel(value));
  }

  function filtersFromSearchParams(): AuditFilters {
    return {
      requestId: searchParams.get("request_id") ?? "",
      action: searchParams.get("action") ?? "",
      resourceType: searchParams.get("resource_type") ?? "",
      reportId: searchParams.get("report_id") ?? "",
      resourceId: searchParams.get("resource_id") ?? "",
      limit: searchParams.get("limit") ?? DEFAULT_FILTERS.limit
    };
  }

  async function fetchLogs(nextFilters: AuditFilters, page = 1) {
    const requestNumber = latestRequestRef.current + 1;
    latestRequestRef.current = requestNumber;
    setLoading(true);
    setError(null);
    setNotice(null);
    const query = buildAuditLogQuery(nextFilters, page);
    const res = await fetch(`/api/app/audit/logs?${query}`, { cache: "no-store" });
    const data = (await res.json().catch(() => null)) as AuditLogsResponse | { error?: string } | null;
    if (requestNumber !== latestRequestRef.current) {
      return;
    }
    if (!res.ok) {
      const apiError = extractAuditApiError(data);
      setLogs([]);
      setCount(0);
      setTotal(0);
      setCurrentPage(1);
      setTotalPages(1);
      setHasMore(false);
      setSelectedLog(null);
      setError(
        apiError
          ? t("audit.errorLoadWithMessage", { message: resolveApiErrorMessage(t, apiError, apiError) })
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
    const nextFilters = filtersFromSearchParams();
    setFilters(nextFilters);
    fetchLogs(nextFilters).catch(() => {
      if (latestRequestRef.current > 1) {
        return;
      }
      setError(t("audit.errorLoad"));
      setLoading(false);
    });
  }, [searchParams, t]);

  const activeFilterCount = useMemo(() => {
    return [filters.requestId, filters.action, filters.resourceType, filters.reportId, filters.resourceId].filter((value) => value.trim()).length;
  }, [filters]);
  const selectedContext = useMemo(() => (selectedLog ? inferLogOperationalContext(selectedLog) : null), [selectedLog]);
  const selectedContextLinks = useMemo(() => {
    if (!selectedContext) {
      return [] as Array<OperationalContextLink & { label: string }>;
    }

    const labelByKind: Record<OperationalContextLink["kind"], string> = {
      case: t("audit.details.openCase"),
      audit: t("audit.details.openCase"),
      evidence: t("audit.details.openEvidence"),
      reports: t("audit.details.openReports"),
      investigate: t("audit.details.openInvestigate"),
      sanctions: t("audit.details.openSanctions"),
      blocks: t("audit.details.openBlocks"),
      counterparty: t("audit.details.openCounterparty"),
      ros: t("audit.details.openRos")
    };

    return buildOperationalContextLinks(selectedContext, {
      includeEvidence: true,
      evidenceDomain: "all",
      auditFallbackResourceType: "audit_log",
      investigateIncludeCaseId: true
    })
      .filter((link: OperationalContextLink) => link.kind !== "audit")
      .map((link: OperationalContextLink) => ({
        ...link,
        label: labelByKind[link.kind]
      }));
  }, [selectedContext, t]);

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
        <MetricCard label={t("audit.stats.selected")} value={selectedLog ? formatAuditActionValue(selectedLog.action) : "--"} meta={t("audit.stats.selectedMeta")} />
        <MetricCard label={t("audit.stats.integrity")} value={selectedLog?.file_hash_sha256 ? "SHA-256" : t("audit.notAvailable")} meta={t("audit.stats.integrityMeta")} accent />
      </MetricGrid>

      <Panel title={t("audit.filters.title")} description={t("audit.filters.description")}>
        <div className="otc-grid otc-grid--audit-filters">
          <label className="otc-field">
            {t("audit.filters.requestId")}
            <input className="otc-input" data-testid="audit-filter-request-id" value={filters.requestId} onChange={(e) => updateFilter("requestId", e.target.value)} />
          </label>
          <label className="otc-field">
            {t("audit.filters.action")}
            <select className="otc-select" data-testid="audit-filter-action" value={filters.action} onChange={(e) => updateFilter("action", e.target.value)}>
              <option value="">{t("audit.filters.all")}</option>
              {AUDIT_ACTION_VALUES.map((value) => (
                <option key={value} value={value}>
                  {formatAuditActionValue(value)}
                </option>
              ))}
            </select>
          </label>
          <label className="otc-field">
            {t("audit.filters.resourceType")}
            <select className="otc-select" data-testid="audit-filter-resource-type" value={filters.resourceType} onChange={(e) => updateFilter("resourceType", e.target.value)}>
              <option value="">{t("audit.filters.allMasculine")}</option>
              {AUDIT_RESOURCE_TYPE_VALUES.map((value) => (
                <option key={value} value={value}>
                  {formatAuditResourceTypeValue(value)}
                </option>
              ))}
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
        <div className="otc-controls otc-audit-summary">
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

      <section className="otc-grid otc-audit-layout">
        <Panel title={t("audit.events.title")} description={t("audit.events.description")}>
          <div className="otc-controls otc-audit-pagination">
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
                    className={`otc-button otc-button--ghost otc-button--stack-start otc-audit-row${isSelected ? " otc-audit-row--selected" : ""}`}
                  >
                    <div className="otc-audit-row__header">
                      <strong>{formatAuditActionValue(entry.action)}</strong>
                      <span className="otc-muted">{entry.created_at ?? t("audit.noTimestamp")}</span>
                    </div>
                    <div className="otc-audit-row__resource">{formatAuditResourceTypeValue(entry.resource_type)}{entry.resource_id ? ` • ${entry.resource_id}` : ""}</div>
                    <div className="otc-muted otc-audit-row__meta">request_id: {entry.request_id ?? t("audit.notAvailable")}</div>
                    <div className="otc-muted otc-audit-row__meta otc-audit-row__meta--tight">report_id: {entry.report_id ?? t("audit.notAvailable")}</div>
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
              <div><strong>{t("audit.details.action")}:</strong> {formatAuditActionValue(selectedLog.action)}</div>
              <div><strong>{t("audit.details.resourceType")}:</strong> {formatAuditResourceTypeValue(selectedLog.resource_type)}</div>
              <div><strong>{t("audit.details.resourceId")}:</strong> {selectedLog.resource_id ?? t("audit.notAvailable")}</div>
              <div><strong>{t("audit.details.requestId")}:</strong> {selectedLog.request_id ?? t("audit.notAvailable")}</div>
              <div><strong>{t("audit.details.reportId")}:</strong> {selectedLog.report_id ?? t("audit.notAvailable")}</div>
              <div><strong>{t("audit.details.sha")}:</strong> {selectedLog.file_hash_sha256 ?? t("audit.notAvailable")}</div>
              <div><strong>{t("audit.details.caseId")}:</strong> {selectedContext?.caseId || t("audit.notAvailable")}</div>
              <div>
                <strong>{t("audit.details.addressChain")}:</strong>{" "}
                {selectedContext?.address ? `${selectedContext.address} • ${selectedContext.chain}` : t("audit.notAvailable")}
              </div>
              <div><strong>{t("audit.details.counterpartyId")}:</strong> {selectedContext?.counterpartyId || t("audit.notAvailable")}</div>
              <div><strong>{t("audit.details.rosId")}:</strong> {selectedContext?.rosId || t("audit.notAvailable")}</div>
              <div className="otc-audit-pill">
                <Pill>{formatAuditResourceTypeValue(selectedLog.resource_type)}</Pill>
              </div>
              {selectedContext ? (
                <div className="otc-controls otc-controls--spaced">
                  {selectedContextLinks.map((link: OperationalContextLink & { label: string }) => (
                    <a key={`audit-${link.testIdSuffix}`} className="otc-button otc-button--ghost" href={link.href}>
                      {link.label}
                    </a>
                  ))}
                </div>
              ) : null}
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

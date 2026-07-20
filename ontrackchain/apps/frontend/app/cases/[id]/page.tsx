"use client";

import { useEffect, useMemo, useState } from "react";
import { useI18n } from "../../../components/i18n-provider";
import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../../components/ui";
import { resolveApiErrorMessage } from "../../lib/api-error-catalog";
import type { MessageKey } from "../../lib/i18n";
import {
  canDownloadLegalReport,
  canDownloadReportArtifact,
  canExportSensitiveEvidence,
  canWriteReport
} from "../../lib/authz";
import { fetchAuthContext, type AuthContext } from "../../lib/ownership";

type ReportState = {
  report_id: string;
  created_at: string;
  report_type: string;
  file_hash_sha256: string;
  content_type: string;
};

type ReportTypeItem = {
  canonical: string;
  label: string;
  available: boolean;
  cost_credits: number;
};

const FALLBACK_REPORT_TYPE_LABELS = {
  technical_basic: "Technical Basic"
} as const;

export default function CasePage({ params }: { params: { id: string } }) {
  const { t } = useI18n();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);
  const caseId = params.id;
  const [status, setStatus] = useState<string>("unknown");
  const [reportType, setReportType] = useState("technical_basic");
  const [reportTypes, setReportTypes] = useState<ReportTypeItem[]>([]);
  const [reportTypeCatalogError, setReportTypeCatalogError] = useState<string | null>(null);
  const [report, setReport] = useState<ReportState | null>(null);
  const [generating, setGenerating] = useState(false);
  const [exportingEvidence, setExportingEvidence] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [authResolved, setAuthResolved] = useState(false);

  function resolveReportTypeLabel(value: string) {
    const normalized = value.trim();
    if (!normalized) {
      return t("common.notAvailable");
    }
    const catalogEntry = reportTypes.find((entry) => entry.canonical === normalized);
    if (catalogEntry?.label.trim()) {
      return catalogEntry.label.trim();
    }
    return FALLBACK_REPORT_TYPE_LABELS[normalized as keyof typeof FALLBACK_REPORT_TYPE_LABELS] ?? normalized;
  }

  function formatReportTypeValue(value: string) {
    const normalized = value.trim();
    if (!normalized) {
      return t("common.notAvailable");
    }
    const label = resolveReportTypeLabel(normalized);
    return label === normalized ? normalized : `${label} (${normalized})`;
  }

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      const res = await fetch(`/api/app/investigation/status?case_id=${caseId}`, { cache: "no-store" });
      if (cancelled) return;
      if (res.ok) {
        const data = (await res.json()) as { status: string };
        setStatus(data.status);
      }
    }
    poll();
    const interval = setInterval(poll, 2000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [caseId]);

  useEffect(() => {
    fetch("/api/app/report-types?include_unavailable=true&include_deprecated=false", { cache: "no-store" })
      .then(async (r) => {
        const data = await r.json().catch(() => null);
        if (!r.ok) {
          throw data ?? { error: "report_catalog_unavailable" };
        }
        return data;
      })
      .then((data) => {
        const items = (data?.types ?? []) as any[];
        const normalized = items.map((item) => ({
          canonical: String(item.canonical),
          label: String(item.label),
          available: Boolean(item.available),
          cost_credits: Number(item.cost_credits)
        })) as ReportTypeItem[];
        setReportTypes(normalized);
        setReportTypeCatalogError(null);
        setReportType((current) =>
          normalized.length && !normalized.some((entry) => entry.canonical === current) ? normalized[0].canonical : current
        );
      })
      .catch((err) => {
        setReportTypes([]);
        setReportTypeCatalogError(resolveApiErrorMessage(t, err, t("investigate.errorLoadReportCatalog")));
      });
  }, [t]);

  const downloadUrl = useMemo(() => {
    if (!report) return null;
    const query = new URLSearchParams({
      report_id: report.report_id,
      case_id: caseId,
      report_type: report.report_type,
      created_at: report.created_at
    }).toString();
    return `/api/app/reports/download?${query}`;
  }, [caseId, report]);
  const canGenerateReport = authResolved ? canWriteReport(authContext?.role) : null;
  const canExportEvidenceBundle = authResolved ? canExportSensitiveEvidence(authContext?.role) : null;
  const generatedReportRequiresStrongAuth = report?.report_type === "legal_report";
  const canDownloadGeneratedReport =
    authResolved && report
      ? generatedReportRequiresStrongAuth
        ? canDownloadLegalReport({
            role: authContext?.role,
            authMethod: authContext?.auth_method,
            mfaMode: authContext?.mfa_mode,
            mfaProviderHomologated: authContext?.mfa_provider_homologated,
            twoFactor: authContext?.two_factor
          })
        : canDownloadReportArtifact(authContext?.role)
      : null;
  const generatedReportDownloadRestrictedMessage = generatedReportRequiresStrongAuth
    ? tr("reports.detail.legalDownloadRestricted" as MessageKey)
    : tr("cases.report.downloadRestricted" as MessageKey);

  useEffect(() => {
    fetchAuthContext()
      .then((data) => setAuthContext(data))
      .catch(() => setAuthContext(null))
      .finally(() => setAuthResolved(true));
  }, []);

  async function onGenerateReport() {
    if (canGenerateReport === false) {
      setError(tr("cases.report.generateRestricted" as MessageKey));
      setNotice(null);
      return;
    }
    setError(null);
    setNotice(null);
    setGenerating(true);
    const res = await fetch("/api/app/reports/generate", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ case_id: caseId, report_type: reportType, include_onchain_hash: false })
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      setError(resolveApiErrorMessage(t, data, t("cases.errorGenerate")));
      setGenerating(false);
      return;
    }
    setReport(data as ReportState);
    setNotice(tr("cases.report.generated" as MessageKey));
    setGenerating(false);
  }

  async function onExportEvidence() {
    if (canExportEvidenceBundle === false) {
      setError(tr("cases.ops.exportRestricted" as MessageKey));
      setNotice(null);
      return;
    }
    setExportingEvidence(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch("/api/app/audit/evidence-export", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          format: "json",
          request_id: null,
          action: null,
          resource_type: "case",
          report_id: report?.report_id ?? null,
          resource_id: caseId,
          limit: 100,
          include_audit_logs: true,
          include_credit_ledger: true,
          include_reports: true
        })
      });
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(resolveApiErrorMessage(t, data, tr("cases.errorExportEvidence" as MessageKey)));
      }

      const blob = await res.blob();
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      const disposition = res.headers.get("content-disposition");
      const filenameMatch = disposition?.match(/filename="([^"]+)"/);
      link.href = href;
      link.download = filenameMatch?.[1] ?? `case-${caseId}-evidence-bundle.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(href);
      setNotice(tr("cases.export.success" as MessageKey));
    } catch (exportError) {
      setError(exportError instanceof Error ? exportError.message : tr("cases.errorExportEvidence" as MessageKey));
    } finally {
      setExportingEvidence(false);
    }
  }

  return (
    <AppShell
      title={t("cases.title")}
      subtitle={t("cases.subtitle", { caseId })}
      activePath="/investigate"
      actions={<Pill>{status}</Pill>}
    >
      <MetricGrid>
        <MetricCard label={t("cases.stats.caseId")} value={caseId.slice(0, 10) + "..."} meta={t("cases.stats.caseIdMeta")} />
        <MetricCard label={t("cases.stats.status")} value={<span data-testid="case-status">{status}</span>} meta={t("cases.stats.statusMeta")} />
        <MetricCard label={t("cases.stats.reportType")} value={formatReportTypeValue(reportType)} meta={t("cases.stats.reportTypeMeta")} />
        <MetricCard label={t("cases.stats.hash")} value={report ? t("cases.hash.available") : "--"} meta={t("cases.stats.hashMeta")} accent />
      </MetricGrid>

      <Panel title={tr("cases.ops.title" as MessageKey)} description={tr("cases.ops.description" as MessageKey)}>
        <div className="otc-controls">
          <a className="otc-button otc-button--ghost" href={`/audit?resource_type=case&resource_id=${encodeURIComponent(caseId)}&report_id=${encodeURIComponent(report?.report_id ?? "")}`}>
            {tr("cases.ops.openAudit" as MessageKey)}
          </a>
          <a className="otc-button otc-button--ghost" href={`/evidence?domain=reports&resource_type=case&resource_id=${encodeURIComponent(caseId)}&report_id=${encodeURIComponent(report?.report_id ?? "")}`}>
            {tr("cases.ops.openEvidence" as MessageKey)}
          </a>
          {canExportEvidenceBundle ? (
            <button
              type="button"
              className="otc-button otc-button--ghost"
              data-testid="case-export-evidence-btn"
              onClick={onExportEvidence}
              disabled={exportingEvidence}
            >
              {exportingEvidence ? tr("cases.ops.exportingEvidence" as MessageKey) : tr("cases.ops.exportEvidence" as MessageKey)}
            </button>
          ) : canExportEvidenceBundle === false ? (
            <Message data-testid="case-export-evidence-restricted">{tr("cases.ops.exportRestricted" as MessageKey)}</Message>
          ) : null}
        </div>
        {notice ? <Message tone="success">{notice}</Message> : null}
        {error ? <Message tone="error">{error}</Message> : null}
      </Panel>

      <Panel title={t("cases.report.title")} description={t("cases.report.description")}>
        <div className="otc-grid otc-grid--case-report">
          <label className="otc-field">
            {t("cases.report.type")}
            <select className="otc-select" data-testid="case-report-type-select" value={reportType} onChange={(e) => setReportType(e.target.value)}>
              {reportTypes.length ? (
                reportTypes.map((entry) => (
                  <option key={entry.canonical} value={entry.canonical} disabled={!entry.available}>
                    {formatReportTypeValue(entry.canonical)} — {entry.cost_credits}
                  </option>
                ))
              ) : (
                <option value="technical_basic">{formatReportTypeValue("technical_basic")}</option>
              )}
            </select>
            {reportTypeCatalogError ? (
              <div style={{ marginTop: 8 }}>
                <Message tone="error">
                  <span data-testid="case-report-type-message">{reportTypeCatalogError}</span>
                </Message>
              </div>
            ) : null}
          </label>
          {canGenerateReport ? (
            <button
              type="button"
              className="otc-button otc-button--accent"
              data-testid="download-report-btn"
              onClick={onGenerateReport}
              disabled={generating}
            >
              {generating ? tr("cases.report.generating" as MessageKey) : t("cases.report.generate")}
            </button>
          ) : canGenerateReport === false ? (
            <Message data-testid="case-report-generate-restricted">{tr("cases.report.generateRestricted" as MessageKey)}</Message>
          ) : null}
        </div>

        {report ? (
          <div className="otc-stack otc-controls--spaced">
            <div data-testid="report-status">{t("cases.report.completed")}</div>
            <div data-testid="stored-report-hash">{report.file_hash_sha256}</div>
            {downloadUrl ? (
              <div className="otc-controls">
                {canDownloadGeneratedReport ? (
                  <a className="otc-link-button" data-testid="download-link" href={downloadUrl} download>
                    {t("cases.report.download")}
                  </a>
                ) : canDownloadGeneratedReport === false ? (
                  <Message data-testid="case-report-download-restricted">{generatedReportDownloadRestrictedMessage}</Message>
                ) : null}
                <a className="otc-link-button" href={`/reports?history_report_id=${encodeURIComponent(report.report_id)}`}>
                  {t("dashboard.cases.openReports")}
                </a>
                <a className="otc-link-button" href={`/audit?resource_type=report&report_id=${encodeURIComponent(report.report_id)}&resource_id=${encodeURIComponent(caseId)}`}>
                  {tr("cases.report.openAudit" as MessageKey)}
                </a>
                <a className="otc-link-button" href={`/evidence?domain=reports&report_id=${encodeURIComponent(report.report_id)}&resource_id=${encodeURIComponent(caseId)}`}>
                  {tr("cases.report.openEvidence" as MessageKey)}
                </a>
              </div>
            ) : null}
            <CodeBlock>{JSON.stringify(report, null, 2)}</CodeBlock>
          </div>
        ) : null}
      </Panel>
    </AppShell>
  );
}

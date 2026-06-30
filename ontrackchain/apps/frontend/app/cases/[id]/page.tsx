"use client";

import { useEffect, useMemo, useState } from "react";
import { useI18n } from "../../../components/i18n-provider";
import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel } from "../../../components/ui";

type ReportState = {
  report_id: string;
  created_at: string;
  report_type: string;
  file_hash_sha256: string;
  content_type: string;
};

export default function CasePage({ params }: { params: { id: string } }) {
  const { t } = useI18n();
  const caseId = params.id;
  const [status, setStatus] = useState<string>("unknown");
  const [reportType, setReportType] = useState("technical_basic");
  const [report, setReport] = useState<ReportState | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  async function onGenerateReport() {
    setError(null);
    const res = await fetch("/api/app/reports/generate", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ case_id: caseId, report_type: reportType, include_onchain_hash: false })
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      setError(t("cases.errorGenerate"));
      return;
    }
    setReport(data as ReportState);
  }

  return (
    <AppShell
      title={t("cases.title")}
      subtitle={t("cases.subtitle", { caseId })}
      activePath="/investigate"
    >
      <MetricGrid>
        <MetricCard label={t("cases.stats.caseId")} value={caseId.slice(0, 10) + "..."} meta={t("cases.stats.caseIdMeta")} />
        <MetricCard label={t("cases.stats.status")} value={<span data-testid="case-status">{status}</span>} meta={t("cases.stats.statusMeta")} />
        <MetricCard label={t("cases.stats.reportType")} value={reportType} meta={t("cases.stats.reportTypeMeta")} />
        <MetricCard label={t("cases.stats.hash")} value={report ? t("cases.hash.available") : "--"} meta={t("cases.stats.hashMeta")} accent />
      </MetricGrid>

      <Panel title={t("cases.report.title")} description={t("cases.report.description")}>
        <div className="otc-grid" style={{ maxWidth: 560 }}>
          <label className="otc-field">
            {t("cases.report.type")}
            <select className="otc-select" value={reportType} onChange={(e) => setReportType(e.target.value)}>
              <option value="technical_basic">technical_basic</option>
              <option value="technical_full">technical_full</option>
              <option value="compliance_aml">compliance_aml</option>
              <option value="legal_report">legal_report</option>
              <option value="coaf_ready_report">coaf_ready_report</option>
            </select>
          </label>
          <button type="button" className="otc-button otc-button--accent" data-testid="download-report-btn" onClick={onGenerateReport}>
            {t("cases.report.generate")}
          </button>
          {error ? <Message tone="error">{error}</Message> : null}
        </div>

        {report ? (
          <div className="otc-stack" style={{ marginTop: 16 }}>
            <div data-testid="report-status">{t("cases.report.completed")}</div>
            <div data-testid="stored-report-hash">{report.file_hash_sha256}</div>
            {downloadUrl ? (
              <a className="otc-link-button" data-testid="download-link" href={downloadUrl} download>
                {t("cases.report.download")}
              </a>
            ) : null}
            <CodeBlock>{JSON.stringify(report, null, 2)}</CodeBlock>
          </div>
        ) : null}
      </Panel>
    </AppShell>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useI18n } from "../../components/i18n-provider";
import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import { canOperateInvestigation } from "../lib/authz";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import type { MessageKey } from "../lib/i18n";

type ReportTypeItem = {
  canonical: string;
  label: string;
  available: boolean;
  cost_credits: number;
};

type AuthContext = {
  role: string | null;
};

export default function InvestigatePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { t } = useI18n();
  const [address, setAddress] = useState("");
  const [chain, setChain] = useState("ethereum");
  const [reportType, setReportType] = useState("technical_basic");
  const [catalog, setCatalog] = useState<ReportTypeItem[]>([]);
  const [quote, setQuote] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [authContext, setAuthContext] = useState<AuthContext | null | undefined>(undefined);

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
        const nextCatalog = items.map((item) => ({
          canonical: item.canonical,
          label: item.label,
          available: Boolean(item.available),
          cost_credits: Number(item.cost_credits)
        }));
        setCatalog(nextCatalog);
        setReportType((current) => (nextCatalog.some((item) => item.canonical === current) ? current : nextCatalog.find((item) => item.available)?.canonical ?? ""));
      })
      .catch((err) => {
        setCatalog([]);
        setReportType("");
        setError(resolveApiErrorMessage(t, err, t("investigate.errorLoadReportCatalog")));
      });
  }, [t]);

  useEffect(() => {
    fetch("/api/app/auth/context", { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("auth_context_unavailable");
        }
        return response.json();
      })
      .then((data) => {
        setAuthContext({
          role: typeof data?.role === "string" ? data.role : null
        });
      })
      .catch(() => {
        setAuthContext(null);
      });
  }, []);

  useEffect(() => {
    const nextReportType = searchParams.get("report_type");
    const nextChain = searchParams.get("chain");
    const nextAddress = searchParams.get("address");
    if (nextReportType) {
      setReportType(nextReportType);
    }
    if (nextChain) {
      setChain(nextChain);
    }
    if (nextAddress) {
      setAddress(nextAddress);
    }
    setQuote(null);
    setError(null);
  }, [searchParams]);

  async function onEstimate() {
    setError(null);
    if (!canOperateInvestigation(authContext?.role)) {
      setError(t("apiErrors.investigationOperationalRoleRequired" as MessageKey));
      return;
    }
    if (!catalog.length || !reportType.trim()) {
      setError(t("investigate.errorLoadReportCatalog"));
      return;
    }
    if (!address.trim()) {
      setError(t("investigate.errorAddressRequired" as MessageKey));
      return;
    }
    const res = await fetch("/api/app/investigation/estimate", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        address,
        chains: [chain],
        depth: 3,
        report_type: reportType,
        addons: []
      })
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      setError(resolveApiErrorMessage(t, data, t("investigate.errorEstimate")));
      return;
    }
    setQuote(data);
  }

  async function onStart() {
    setError(null);
    if (!canOperateInvestigation(authContext?.role)) {
      setError(t("apiErrors.investigationOperationalRoleRequired" as MessageKey));
      return;
    }
    if (!quote?.quote_id) {
      setError(t("investigate.errorQuoteMissing"));
      return;
    }
    const res = await fetch("/api/app/investigation/start", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ quote_id: quote.quote_id, confirmed: true })
    });
    const data = await res.json().catch(() => null);
    if (!res.ok && res.status !== 202) {
      setError(resolveApiErrorMessage(t, data, t("investigate.errorStart")));
      return;
    }
    if (data?.case_id) {
      router.push(`/cases/${data.case_id}`);
      return;
    }
    setError(t("investigate.errorCaseIdMissing"));
  }

  return (
    <AppShell
      title={t("investigate.title")}
      subtitle={t("investigate.subtitle")}
      activePath="/investigate"
      actions={<Pill>{t("investigate.active")}</Pill>}
    >
      <MetricGrid>
        <MetricCard
          label={t("investigate.stats.targetAddress")}
          value={address.trim() ? address.slice(0, 10) + "..." : t("common.notAvailable")}
          meta={t("investigate.stats.targetAddressMeta")}
        />
        <MetricCard label={t("investigate.stats.network")} value={chain.toUpperCase()} meta={t("investigate.stats.networkMeta")} />
        <MetricCard label={t("investigate.stats.reportType")} value={reportType} meta={t("investigate.stats.reportTypeMeta")} />
        <MetricCard label={t("investigate.stats.quote")} value={quote ? String(quote.total_credits) : "--"} meta={t("investigate.stats.quoteMeta")} accent />
      </MetricGrid>

      <Panel title={t("investigate.form.title")} description={t("investigate.form.description")}>
        <div className="otc-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))" }}>
          <label className="otc-field">
            {t("investigate.form.address")}
            <input
              className="otc-input"
              data-testid="wallet-address"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="0x..."
            />
          </label>
          <label className="otc-field">
            {t("investigate.form.chain")}
            <select className="otc-select" data-testid="chain-select" value={chain} onChange={(e) => setChain(e.target.value)}>
              <option value="ethereum">Ethereum</option>
              <option value="polygon">Polygon</option>
              <option value="bsc">BSC</option>
              <option value="arbitrum">Arbitrum</option>
              <option value="base">Base</option>
              <option value="bitcoin">Bitcoin</option>
            </select>
          </label>
          <label className="otc-field">
            {t("investigate.form.reportType")}
            <select className="otc-select" data-testid="report-type" value={reportType} onChange={(e) => setReportType(e.target.value)}>
              {catalog.length ? (
                catalog.map((item) => (
                  <option key={item.canonical} value={item.canonical} disabled={!item.available}>
                    {item.label} ({item.canonical}) — {item.cost_credits}
                  </option>
                ))
              ) : (
                <option value="">{t("common.notAvailable")}</option>
              )}
            </select>
          </label>
        </div>
        <div className="otc-controls" style={{ marginTop: 16 }}>
          {canOperateInvestigation(authContext?.role) ? (
            <button
              className="otc-button otc-button--accent"
              data-testid="start-investigation-btn"
              onClick={onEstimate}
              disabled={!catalog.length || !reportType.trim()}
            >
              {t("investigate.form.generateQuote")}
            </button>
          ) : (
            <Message data-testid="investigate-generate-quote-restricted">
              {t("investigate.form.roleRestricted" as MessageKey)}
            </Message>
          )}
        </div>
        {error ? (
          <div style={{ marginTop: 14 }}>
            <Message tone="error">
              <span data-testid="investigate-error-message">{error}</span>
            </Message>
          </div>
        ) : null}
      </Panel>

      {quote ? (
        <Panel className="quote-preview-panel" title={t("investigate.quote.title")} description={t("investigate.quote.description")}>
          <div className="otc-controls" style={{ justifyContent: "space-between" }}>
            <div>
              <p className="otc-stat__label">{t("investigate.quote.totalCredits")}</p>
              <div className="otc-stat__value otc-stat__value--accent" data-testid="quote-credits">
                {String(quote.total_credits)}
              </div>
            </div>
            {canOperateInvestigation(authContext?.role) ? (
              <button type="button" className="otc-button" data-testid="confirm-investigation-btn" onClick={onStart}>
                {t("investigate.quote.confirm")}
              </button>
            ) : (
              <Message data-testid="investigate-confirm-restricted">
                {t("investigate.quote.roleRestricted" as MessageKey)}
              </Message>
            )}
          </div>
          <div style={{ marginTop: 16 }}>
            <div data-testid="quote-preview">
              <CodeBlock>{JSON.stringify(quote, null, 2)}</CodeBlock>
            </div>
          </div>
        </Panel>
      ) : null}
    </AppShell>
  );
}

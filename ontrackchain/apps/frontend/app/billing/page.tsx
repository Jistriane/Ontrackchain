"use client";

import { useEffect, useState } from "react";
import { useI18n } from "../../components/i18n-provider";
import { AppShell, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";

type BillingBalanceResponse = {
  credits_available?: number | string;
  available_credits?: number | string;
};

export default function BillingPage() {
  const [balance, setBalance] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { t } = useI18n();

  useEffect(() => {
    fetch("/api/app/billing/balance", { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(t("billing.errorLoad"));
        }
        return response.json();
      })
      .then((data: BillingBalanceResponse) => {
        const nextBalance = Number(data.credits_available ?? data.available_credits);
        if (!Number.isFinite(nextBalance)) {
          throw new Error(t("billing.errorLoad"));
        }
        setBalance(nextBalance);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : t("billing.errorLoad"));
      });
  }, [t]);

  return (
    <AppShell title={t("billing.title")} subtitle={t("billing.subtitle")} activePath="/billing">
      <MetricGrid>
        <MetricCard
          label={t("billing.stats.availableCredit")}
          value={<span data-testid="credits-balance">{balance === null ? t("common.loading") : String(balance)}</span>}
          meta={t("billing.stats.availableCreditMeta")}
          accent
        />
        <MetricCard label={t("billing.stats.plan")} value="Professional" meta={t("billing.stats.planMeta")} />
        <MetricCard label={t("billing.stats.operationalLimit")} value="3 analistas" meta={t("billing.stats.operationalLimitMeta")} />
        <MetricCard label={t("billing.stats.cycle")} value="Mensal" meta={t("billing.stats.cycleMeta")} />
      </MetricGrid>

      <Panel title={t("billing.summary.title")} description={t("billing.summary.description")}>
        <div className="otc-kv">
          <div className="otc-kv__row">
            <span className="otc-kv__key">{t("billing.summary.reserved")}</span>
            <span className="otc-kv__value">12</span>
          </div>
          <div className="otc-kv__row">
            <span className="otc-kv__key">{t("billing.summary.available")}</span>
            <span className="otc-kv__value">{balance === null ? t("billing.loading") : balance}</span>
          </div>
          <div className="otc-kv__row">
            <span className="otc-kv__key">{t("billing.summary.policy")}</span>
            <span className="otc-kv__value">
              <Pill>{t("billing.summary.policyValue")}</Pill>
            </span>
          </div>
        </div>
        {error ? <div className="otc-message otc-message--error">{error}</div> : null}
      </Panel>
    </AppShell>
  );
}

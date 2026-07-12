"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useI18n } from "../../components/i18n-provider";
import { AppShell, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import { canReadBilling } from "../lib/authz";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { formatDateTime } from "../lib/date-format";
import type { MessageKey } from "../lib/i18n";

type BillingBalanceResponse = {
  credits_available: number;
  credits_reserved: number;
  credits_used_total: number;
};

type BillingActionTotal = {
  action: string;
  entry_count: number;
  amount_total: number;
};

type BillingLedgerEntry = {
  id: string;
  case_id: string | null;
  action: string;
  amount: number | null;
  balance_after: number | null;
  request_id: string | null;
  quote_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string | null;
};

type BillingReconciliationResponse = {
  generated_at: string;
  balance: BillingBalanceResponse;
  quotes: {
    investigation: { open_total: number; expired_total: number };
    compliance: { open_total: number; expired_total: number };
    monitoring: { open_total: number; expired_total: number };
    open_total: number;
    expired_total: number;
  };
  ledger: {
    total_entries: number;
    action_totals: BillingActionTotal[];
    recent: BillingLedgerEntry[];
  };
};

type AuthContext = {
  org_id: string | null;
  user_id: string | null;
  linked_user_id: string | null;
  role: string | null;
  plan: string | null;
  auth_method: string | null;
  mfa_mode: string | null;
  mfa_provider_homologated: string | null;
};

type OperationsSnapshot = {
  concurrency: {
    org_active: number;
    org_limit: number;
    global_active: number;
    global_limit: number;
    plan: string;
  };
  generated_at: string;
};

type TeamMemberRecord = {
  member_id: string;
  name: string;
  email: string;
  role: string;
  status: string;
  note: string;
  created_at: string;
  updated_at: string;
};

const TEAM_STORAGE_KEY = "otc-team-roster";

function buildTeamMemberHref(member: TeamMemberRecord) {
  const params = new URLSearchParams({
    member_id: member.member_id,
    email: member.email,
    name: member.name,
    role: member.role,
    status: member.status,
    note: member.note,
    search: member.email,
    filter_status: member.status
  });
  return `/team?${params.toString()}`;
}

function loadTeamRoster(): TeamMemberRecord[] {
  if (typeof window === "undefined") {
    return [];
  }
  try {
    const raw = window.localStorage.getItem(TEAM_STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as TeamMemberRecord[]) : [];
  } catch {
    return [];
  }
}

export default function BillingPage() {
  const searchParams = useSearchParams();
  const [balance, setBalance] = useState<BillingBalanceResponse | null>(null);
  const [reconciliation, setReconciliation] = useState<BillingReconciliationResponse | null>(null);
  const [authContext, setAuthContext] = useState<AuthContext | null | undefined>(undefined);
  const [operations, setOperations] = useState<OperationsSnapshot | null>(null);
  const [teamRoster, setTeamRoster] = useState<TeamMemberRecord[]>([]);
  const [teamFilterStatus, setTeamFilterStatus] = useState("all");
  const [teamSearch, setTeamSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { locale, t } = useI18n();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);

  function formatBillingMemberStatus(status: string) {
    return status === "active" || status === "invited" || status === "disabled"
      ? t(`team.roster.status.${status}` as MessageKey)
      : status;
  }

  function formatBillingMemberStatusTone(status: string) {
    return status === "disabled" ? "danger" : status === "invited" ? "warning" : undefined;
  }

  function formatBillingTimestamp(value: string) {
    const normalized = value.trim();
    if (!normalized) {
      return t("common.notAvailable");
    }
    return formatDateTime(normalized, locale) ?? normalized;
  }

  const filteredTeamRoster = useMemo(() => {
    const query = teamSearch.trim().toLowerCase();
    return teamRoster.filter((member) => {
      const matchesStatus = teamFilterStatus === "all" ? true : member.status === teamFilterStatus;
      const matchesSearch =
        !query ||
        member.name.toLowerCase().includes(query) ||
        member.email.toLowerCase().includes(query) ||
        member.role.toLowerCase().includes(query);
      return matchesStatus && matchesSearch;
    });
  }, [teamFilterStatus, teamRoster, teamSearch]);

  const activeTeamCount = useMemo(() => teamRoster.filter((member) => member.status === "active").length, [teamRoster]);
  const invitedTeamCount = useMemo(() => teamRoster.filter((member) => member.status === "invited").length, [teamRoster]);
  const disabledTeamCount = useMemo(() => teamRoster.filter((member) => member.status === "disabled").length, [teamRoster]);

  async function refresh() {
    setLoading(true);
    setError(null);

    const [billingRes, reconciliationRes, authRes, opsRes] = await Promise.all([
      fetch("/api/app/billing/balance", { cache: "no-store" }),
      fetch("/api/app/billing/reconciliation?limit=5", { cache: "no-store" }),
      fetch("/api/app/auth/context", { cache: "no-store" }),
      fetch("/api/app/investigation/operations", { cache: "no-store" })
    ]);
    let nextError: string | null = null;

    const billingData = (await billingRes.json().catch(() => null)) as BillingBalanceResponse | { error?: string; detail?: unknown } | null;
    if (billingRes.ok) {
      setBalance(billingData as BillingBalanceResponse);
    } else {
      setBalance(null);
      nextError = resolveApiErrorMessage(t, billingData, t("billing.errorLoad"));
    }

    const reconciliationData = (await reconciliationRes.json().catch(() => null)) as BillingReconciliationResponse | { error?: string; detail?: unknown } | null;
    if (reconciliationRes.ok) {
      setReconciliation(reconciliationData as BillingReconciliationResponse);
    } else {
      setReconciliation(null);
      if (!nextError) {
        nextError = resolveApiErrorMessage(t, reconciliationData, t("billing.errorLoad"));
      }
    }

    const authData = (await authRes.json().catch(() => null)) as AuthContext | { error?: string; detail?: unknown } | null;
    if (authRes.ok) {
      setAuthContext(authData as AuthContext);
    } else {
      setAuthContext(null);
    }

    const opsData = (await opsRes.json().catch(() => null)) as OperationsSnapshot | { error?: string; detail?: unknown } | null;
    if (opsRes.ok) {
      setOperations(opsData as OperationsSnapshot);
    } else {
      setOperations(null);
    }

    setError(nextError);
    setLoading(false);
  }

  useEffect(() => {
    refresh().catch(() => {
      setError(t("billing.errorLoad"));
      setLoading(false);
    });
  }, [t]);

  useEffect(() => {
    setTeamRoster(loadTeamRoster());
  }, []);

  useEffect(() => {
    const nextTeamStatus = searchParams.get("team_status");
    const nextTeamSearch = searchParams.get("team_q");
    if (nextTeamStatus === "all" || nextTeamStatus === "active" || nextTeamStatus === "invited" || nextTeamStatus === "disabled") {
      setTeamFilterStatus(nextTeamStatus);
    }
    if (nextTeamSearch !== null) {
      setTeamSearch(nextTeamSearch);
    }
  }, [searchParams]);

  const billingAccessResolved = authContext !== undefined;
  const canReadBillingSurface = authContext ? canReadBilling(authContext.role) : true;
  const shouldRenderBillingData = !billingAccessResolved || canReadBillingSurface;
  const deniedBillingMessage = billingAccessResolved && !canReadBillingSurface ? error ?? t("billing.errorLoad") : null;

  return (
    <AppShell
      title={t("billing.title")}
      subtitle={t("billing.subtitle")}
      activePath="/billing"
      actions={
        <div className="otc-controls">
          {shouldRenderBillingData ? (
            <button className="otc-button otc-button--ghost" type="button" onClick={() => refresh()} disabled={loading}>
              {loading ? t("billing.refreshLoading") : t("billing.refresh")}
            </button>
          ) : null}
          <a className="otc-button otc-button--ghost" href="/team">
            {t("billing.openTeam")}
          </a>
        </div>
      }
    >
      {shouldRenderBillingData ? (
        <>
      <MetricGrid>
        <MetricCard
          label={t("billing.stats.availableCredit")}
          value={<span data-testid="credits-balance">{balance === null ? t("common.loading") : String(balance.credits_available)}</span>}
          meta={t("billing.stats.availableCreditMeta")}
          accent
        />
        <MetricCard
          label={t("billing.stats.plan")}
          value={authContext?.plan ?? operations?.concurrency.plan ?? t("common.notAvailable")}
          meta={t("billing.stats.planMeta")}
        />
        <MetricCard
          label={t("billing.stats.operationalLimit")}
          value={operations ? `${operations.concurrency.org_active} / ${operations.concurrency.org_limit}` : t("common.notAvailable")}
          meta={t("billing.stats.operationalLimitMeta")}
        />
        <MetricCard label={t("billing.stats.cycle")} value={t("billing.stats.cycleValue")} meta={t("billing.stats.cycleMeta")} />
      </MetricGrid>

      <MetricGrid>
        <MetricCard label={tr("billing.teamStats.total" as MessageKey)} value={teamRoster.length} meta={tr("billing.teamStats.totalMeta" as MessageKey)} />
        <MetricCard label={tr("billing.teamStats.active" as MessageKey)} value={activeTeamCount} meta={tr("billing.teamStats.activeMeta" as MessageKey)} accent />
        <MetricCard label={tr("billing.teamStats.invited" as MessageKey)} value={invitedTeamCount} meta={tr("billing.teamStats.invitedMeta" as MessageKey)} />
        <MetricCard label={tr("billing.teamStats.disabled" as MessageKey)} value={disabledTeamCount} meta={tr("billing.teamStats.disabledMeta" as MessageKey)} />
      </MetricGrid>

      <Panel title={tr("billing.auth.title" as MessageKey)} description={tr("billing.auth.description" as MessageKey)}>
        <Message>{tr("billing.auth.notice" as MessageKey)}</Message>
      </Panel>

      <Panel title={t("billing.summary.title")} description={t("billing.summary.description")}>
        <div className="otc-kv">
          <div className="otc-kv__row">
            <span className="otc-kv__key">{t("billing.summary.reserved")}</span>
            <span className="otc-kv__value">{balance === null ? t("billing.loading") : balance.credits_reserved}</span>
          </div>
          <div className="otc-kv__row">
            <span className="otc-kv__key">{t("billing.summary.available")}</span>
            <span className="otc-kv__value">{balance === null ? t("billing.loading") : balance.credits_available}</span>
          </div>
          <div className="otc-kv__row">
            <span className="otc-kv__key">{t("billing.summary.usedTotal")}</span>
            <span className="otc-kv__value">{balance === null ? t("billing.loading") : balance.credits_used_total}</span>
          </div>
          <div className="otc-kv__row">
            <span className="otc-kv__key">{t("billing.summary.policy")}</span>
            <span className="otc-kv__value">
              <Pill>{t("billing.summary.policyValue")}</Pill>
            </span>
          </div>
          <div className="otc-kv__row">
            <span className="otc-kv__key">{t("billing.summary.role")}</span>
            <span className="otc-kv__value">{authContext?.role ?? t("common.notAvailable")}</span>
          </div>
          <div className="otc-kv__row">
            <span className="otc-kv__key">{t("billing.summary.mfa")}</span>
            <span className="otc-kv__value">{authContext?.mfa_mode ?? t("common.notAvailable")}</span>
          </div>
        </div>
        {error ? <Message tone="error">{error}</Message> : null}
      </Panel>

      <Panel title={tr("billing.reconciliation.title" as MessageKey)} description={tr("billing.reconciliation.description" as MessageKey)}>
        {reconciliation ? (
          <>
            <div className="otc-kv">
              <div className="otc-kv__row">
                <span className="otc-kv__key">{tr("billing.reconciliation.generatedAt" as MessageKey)}</span>
                <span className="otc-kv__value">{formatBillingTimestamp(reconciliation.generated_at)}</span>
              </div>
              <div className="otc-kv__row">
                <span className="otc-kv__key">{tr("billing.reconciliation.openQuotes" as MessageKey)}</span>
                <span className="otc-kv__value" data-testid="billing-reconciliation-open-total">{reconciliation.quotes.open_total}</span>
              </div>
              <div className="otc-kv__row">
                <span className="otc-kv__key">{tr("billing.reconciliation.expiredQuotes" as MessageKey)}</span>
                <span className="otc-kv__value">{reconciliation.quotes.expired_total}</span>
              </div>
              <div className="otc-kv__row">
                <span className="otc-kv__key">{tr("billing.reconciliation.ledgerEntries" as MessageKey)}</span>
                <span className="otc-kv__value">{reconciliation.ledger.total_entries}</span>
              </div>
            </div>

            <div className="otc-kv">
              <div className="otc-kv__row">
                <span className="otc-kv__key">{tr("billing.reconciliation.domain.investigation" as MessageKey)}</span>
                <span className="otc-kv__value">
                  {reconciliation.quotes.investigation.open_total} / {reconciliation.quotes.investigation.expired_total}
                </span>
              </div>
              <div className="otc-kv__row">
                <span className="otc-kv__key">{tr("billing.reconciliation.domain.compliance" as MessageKey)}</span>
                <span className="otc-kv__value">
                  {reconciliation.quotes.compliance.open_total} / {reconciliation.quotes.compliance.expired_total}
                </span>
              </div>
              <div className="otc-kv__row">
                <span className="otc-kv__key">{tr("billing.reconciliation.domain.monitoring" as MessageKey)}</span>
                <span className="otc-kv__value">
                  {reconciliation.quotes.monitoring.open_total} / {reconciliation.quotes.monitoring.expired_total}
                </span>
              </div>
            </div>

            <h3>{tr("billing.reconciliation.actionTotalsTitle" as MessageKey)}</h3>
            {reconciliation.ledger.action_totals.length ? (
              <table className="otc-table otc-table--spaced">
                <thead>
                  <tr>
                    <th>{tr("billing.reconciliation.table.action" as MessageKey)}</th>
                    <th>{tr("billing.reconciliation.table.entries" as MessageKey)}</th>
                    <th>{tr("billing.reconciliation.table.amountTotal" as MessageKey)}</th>
                  </tr>
                </thead>
                <tbody>
                  {reconciliation.ledger.action_totals.map((entry) => (
                    <tr key={entry.action} data-testid={`billing-ledger-action-${entry.action}`}>
                      <td>{entry.action}</td>
                      <td>{entry.entry_count}</td>
                      <td>{entry.amount_total}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <Message>{tr("billing.reconciliation.empty" as MessageKey)}</Message>
            )}

            <h3>{tr("billing.reconciliation.recentTitle" as MessageKey)}</h3>
            {reconciliation.ledger.recent.length ? (
              <table className="otc-table otc-table--spaced">
                <thead>
                  <tr>
                    <th>{tr("billing.reconciliation.table.action" as MessageKey)}</th>
                    <th>{tr("billing.reconciliation.recent.amount" as MessageKey)}</th>
                    <th>{tr("billing.reconciliation.recent.balanceAfter" as MessageKey)}</th>
                    <th>{tr("billing.reconciliation.recent.requestId" as MessageKey)}</th>
                    <th>{tr("billing.reconciliation.recent.createdAt" as MessageKey)}</th>
                  </tr>
                </thead>
                <tbody>
                  {reconciliation.ledger.recent.map((entry) => (
                    <tr key={entry.id} data-testid={`billing-ledger-row-${entry.id}`}>
                      <td>{entry.action}</td>
                      <td>{entry.amount ?? t("common.notAvailable")}</td>
                      <td>{entry.balance_after ?? t("common.notAvailable")}</td>
                      <td>{entry.request_id ?? t("common.notAvailable")}</td>
                      <td>{entry.created_at ? formatBillingTimestamp(entry.created_at) : t("common.notAvailable")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <Message>{tr("billing.reconciliation.empty" as MessageKey)}</Message>
            )}
          </>
        ) : (
          <Message>{loading ? t("common.loading") : tr("billing.reconciliation.empty" as MessageKey)}</Message>
        )}
      </Panel>

      <Panel title={tr("billing.quick.title" as MessageKey)} description={tr("billing.quick.description" as MessageKey)}>
        <div className="otc-controls otc-controls--spaced">
          <a className="otc-button otc-button--ghost" href="/reports">
            {tr("billing.quick.openReports" as MessageKey)}
          </a>
          <a className="otc-button otc-button--ghost" href="/monitoring">
            {tr("billing.quick.openMonitoring" as MessageKey)}
          </a>
          <a className="otc-button otc-button--ghost" href="/alerts?status=pending">
            {tr("billing.quick.openAlerts" as MessageKey)}
          </a>
          <a className="otc-button otc-button--ghost" href="/team?filter_status=invited">
            {tr("billing.quick.openInvitedTeam" as MessageKey)}
          </a>
        </div>
      </Panel>

      <Panel title={t("billing.users.title")} description={t("billing.users.description")}>
        <div className="otc-controls">
          <label className="otc-field">
            {tr("billing.users.filters.status" as MessageKey)}
            <select className="otc-select" value={teamFilterStatus} onChange={(event) => setTeamFilterStatus(event.target.value)}>
              <option value="all">{tr("billing.users.filters.all" as MessageKey)}</option>
              <option value="active">{t("team.roster.status.active")}</option>
              <option value="invited">{t("team.roster.status.invited")}</option>
              <option value="disabled">{t("team.roster.status.disabled")}</option>
            </select>
          </label>
          <label className="otc-field">
            {tr("billing.users.filters.search" as MessageKey)}
            <input className="otc-input" value={teamSearch} onChange={(event) => setTeamSearch(event.target.value)} />
          </label>
        </div>
        {filteredTeamRoster.length ? (
          <table className="otc-table otc-table--spaced">
            <thead>
              <tr>
                <th>{t("team.roster.table.name")}</th>
                <th>{t("team.roster.table.email")}</th>
                <th>{t("team.roster.table.role")}</th>
                <th>{t("team.roster.table.status")}</th>
                <th>{t("team.roster.table.updated")}</th>
                <th>{tr("billing.users.actions" as MessageKey)}</th>
              </tr>
            </thead>
            <tbody>
              {filteredTeamRoster.slice(0, 12).map((member) => (
                <tr key={member.member_id} data-testid={`billing-user-row-${member.member_id}`}>
                  <td><strong>{member.name || member.email}</strong></td>
                  <td>{member.email}</td>
                  <td>{member.role}</td>
                  <td data-testid={`billing-user-status-${member.member_id}`}>
                    <Pill tone={formatBillingMemberStatusTone(member.status)}>{formatBillingMemberStatus(member.status)}</Pill>
                  </td>
                  <td data-testid={`billing-user-updated-${member.member_id}`}>{formatBillingTimestamp(member.updated_at)}</td>
                  <td>
                    <div className="otc-controls">
                      <a className="otc-button otc-button--ghost" href={buildTeamMemberHref(member)}>
                        {tr("billing.users.openMember" as MessageKey)}
                      </a>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <Message>{t("billing.users.empty")}</Message>
        )}
        <div className="otc-controls otc-controls--spaced">
          <a className="otc-button otc-button--ghost" href="/team">
            {t("billing.users.manage")}
          </a>
        </div>
      </Panel>
        </>
      ) : (
        <Panel title={t("billing.summary.title")} description={t("billing.summary.description")}>
          <Message tone="error" data-testid="billing-access-denied">
            {deniedBillingMessage}
          </Message>
          <div className="otc-controls otc-controls--spaced">
            <a className="otc-button otc-button--ghost" href="/dashboard">
              {t("home.openDashboard")}
            </a>
            <a className="otc-button otc-button--ghost" href="/team">
              {t("billing.openTeam")}
            </a>
          </div>
        </Panel>
      )}
    </AppShell>
  );
}

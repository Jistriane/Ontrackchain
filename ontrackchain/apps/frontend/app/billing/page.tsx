"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useI18n } from "../../components/i18n-provider";
import { AppShell, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import type { MessageKey } from "../lib/i18n";

type BillingBalanceResponse = {
  credits_available: number;
  credits_reserved: number;
  credits_used_total: number;
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
  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [operations, setOperations] = useState<OperationsSnapshot | null>(null);
  const [teamRoster, setTeamRoster] = useState<TeamMemberRecord[]>([]);
  const [teamFilterStatus, setTeamFilterStatus] = useState("all");
  const [teamSearch, setTeamSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { t } = useI18n();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);

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

    const [billingRes, authRes, opsRes] = await Promise.all([
      fetch("/api/app/billing/balance", { cache: "no-store" }),
      fetch("/api/app/auth/context", { cache: "no-store" }),
      fetch("/api/app/investigation/operations", { cache: "no-store" })
    ]);

    const billingData = (await billingRes.json().catch(() => null)) as BillingBalanceResponse | { error?: string; detail?: unknown } | null;
    if (billingRes.ok) {
      setBalance(billingData as BillingBalanceResponse);
    } else {
      setBalance(null);
      setError(resolveApiErrorMessage(t, billingData, t("billing.errorLoad")));
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

  return (
    <AppShell
      title={t("billing.title")}
      subtitle={t("billing.subtitle")}
      activePath="/billing"
      actions={
        <div className="otc-controls">
          <button className="otc-button otc-button--ghost" type="button" onClick={() => refresh()} disabled={loading}>
            {loading ? t("billing.refreshLoading") : t("billing.refresh")}
          </button>
          <a className="otc-button otc-button--ghost" href="/team">
            {t("billing.openTeam")}
          </a>
        </div>
      }
    >
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
                <tr key={member.member_id}>
                  <td><strong>{member.name || member.email}</strong></td>
                  <td>{member.email}</td>
                  <td>{member.role}</td>
                  <td>{member.status}</td>
                  <td>{member.updated_at}</td>
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
    </AppShell>
  );
}

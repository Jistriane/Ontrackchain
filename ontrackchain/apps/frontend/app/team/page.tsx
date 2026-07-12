"use client";

import { useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import { useI18n } from "../../components/i18n-provider";
import { formatDateTime } from "../lib/date-format";
import type { MessageKey } from "../lib/i18n";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { TEAM_ROLE_VALUES, isTeamRoleValue } from "../lib/team-catalog";

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

type TeamRole = (typeof TEAM_ROLE_VALUES)[number];
type TeamMemberStatus = "active" | "invited" | "disabled";
type TeamMemberRecord = {
  member_id: string;
  name: string;
  email: string;
  role: TeamRole;
  status: TeamMemberStatus;
  note: string;
  created_at: string;
  updated_at: string;
  linked_identity_count?: number;
  last_identity_seen_at?: string | null;
};

type MemberFormState = {
  name: string;
  email: string;
  role: TeamRole;
  status: TeamMemberStatus;
  note: string;
};

const KEYCLOAK_URL_KEY = "otc-team-keycloak-url";

const DEFAULT_MEMBER_FORM: MemberFormState = {
  name: "",
  email: "",
  role: "ANALYST",
  status: "invited",
  note: ""
};

function parseTeamRole(value: string | null): TeamRole | null {
  return value && isTeamRoleValue(value) ? value : null;
}

function parseTeamStatus(value: string | null): TeamMemberStatus | null {
  if (value === "active" || value === "invited" || value === "disabled") {
    return value;
  }
  return null;
}

function buildBillingHref(record: TeamMemberRecord) {
  const params = new URLSearchParams({
    team_status: record.status,
    team_q: record.email
  });
  return `/billing?${params.toString()}`;
}

function loadKeycloakUrl() {
  if (typeof window === "undefined") {
    return "";
  }
  try {
    return window.localStorage.getItem(KEYCLOAK_URL_KEY) ?? "";
  } catch {
    return "";
  }
}

function saveKeycloakUrl(value: string) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(KEYCLOAK_URL_KEY, value);
}

function upsertMember(current: TeamMemberRecord[], record: TeamMemberRecord) {
  const next = [record, ...current.filter((entry) => entry.member_id !== record.member_id)];
  next.sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || ""));
  return next;
}

function replaceMemberById(current: TeamMemberRecord[], memberId: string, updater: (record: TeamMemberRecord) => TeamMemberRecord) {
  return current.map((entry) => (entry.member_id === memberId ? updater(entry) : entry));
}

function exportRosterJson(records: TeamMemberRecord[]) {
  const blob = new Blob([JSON.stringify({ exported_at: new Date().toISOString(), records }, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `ontrackchain-team-roster-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export default function TeamPage() {
  const searchParams = useSearchParams();
  const { locale, t } = useI18n();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);

  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const [keycloakUrl, setKeycloakUrl] = useState("");

  const [roster, setRoster] = useState<TeamMemberRecord[]>([]);
  const [rosterLoading, setRosterLoading] = useState(false);
  const [rosterError, setRosterError] = useState<string | null>(null);
  const [memberForm, setMemberForm] = useState<MemberFormState>(DEFAULT_MEMBER_FORM);
  const [selectedMemberId, setSelectedMemberId] = useState<string>("");
  const [filterStatus, setFilterStatus] = useState<TeamMemberStatus | "all">("all");
  const [search, setSearch] = useState("");
  const [notice, setNotice] = useState<string | null>(null);

  function resolveTeamRoleLabel(value: TeamRole | string) {
    return isTeamRoleValue(value) ? tr(`team.roster.roles.${value}` as MessageKey) : value;
  }

  function formatTeamRoleValue(value: TeamRole | string) {
    const label = resolveTeamRoleLabel(value);
    return label === value ? value : `${label} (${value})`;
  }

  function formatTeamTimestamp(value: string) {
    const normalized = value.trim();
    if (!normalized) {
      return tr("common.notAvailable" as MessageKey);
    }
    return formatDateTime(normalized, locale) ?? normalized;
  }

  const activeCount = useMemo(() => roster.filter((r) => r.status === "active").length, [roster]);
  const invitedCount = useMemo(() => roster.filter((r) => r.status === "invited").length, [roster]);
  const disabledCount = useMemo(() => roster.filter((r) => r.status === "disabled").length, [roster]);

  const filteredRoster = useMemo(() => {
    const query = search.trim().toLowerCase();
    return roster.filter((record) => {
      const matchesStatus = filterStatus === "all" ? true : record.status === filterStatus;
      const matchesSearch =
        !query ||
        record.email.toLowerCase().includes(query) ||
        record.name.toLowerCase().includes(query) ||
        record.role.toLowerCase().includes(query) ||
        resolveTeamRoleLabel(record.role).toLowerCase().includes(query);
      return matchesStatus && matchesSearch;
    });
  }, [filterStatus, roster, search]);

  useEffect(() => {
    setKeycloakUrl(loadKeycloakUrl());
  }, []);

  useEffect(() => {
    saveKeycloakUrl(keycloakUrl.trim());
  }, [keycloakUrl]);

  async function loadAuthContext() {
    setAuthLoading(true);
    setAuthError(null);
    setAuthContext(null);
    try {
      const res = await fetch("/api/app/auth/context", { cache: "no-store" });
      const data = (await res.json().catch(() => null)) as AuthContext | { error?: string; detail?: unknown } | null;
      if (!res.ok) {
        setAuthError(resolveApiErrorMessage(t, data, tr("team.errors.loadAuthContext" as MessageKey)));
        setAuthLoading(false);
        return;
      }
      setAuthContext(data as AuthContext);
      setAuthLoading(false);
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : tr("team.errors.loadAuthContext" as MessageKey));
      setAuthLoading(false);
    }
  }

  useEffect(() => {
    loadAuthContext().catch(() => undefined);
  }, []);

  async function loadRoster() {
    setRosterLoading(true);
    setRosterError(null);
    try {
      const res = await fetch("/api/app/team/users", { cache: "no-store" });
      const data = (await res.json().catch(() => null)) as
        | { data?: TeamMemberRecord[]; error?: string; detail?: unknown }
        | null;
      if (!res.ok) {
        setRosterError(resolveApiErrorMessage(t, data, tr("team.errors.loadRoster" as MessageKey)));
        setRosterLoading(false);
        return;
      }
      setRoster(Array.isArray(data?.data) ? data.data : []);
      setRosterLoading(false);
    } catch (err) {
      setRosterError(err instanceof Error ? err.message : tr("team.errors.loadRoster" as MessageKey));
      setRosterLoading(false);
    }
  }

  useEffect(() => {
    loadRoster().catch(() => undefined);
  }, []);

  useEffect(() => {
    const nextFilterStatus = searchParams.get("filter_status");
    const nextSearch = searchParams.get("search");
    const nextMemberId = searchParams.get("member_id");
    const nextEmail = searchParams.get("email");
    const nextName = searchParams.get("name");
    const nextRole = parseTeamRole(searchParams.get("role"));
    const nextStatus = parseTeamStatus(searchParams.get("status"));
    const nextNote = searchParams.get("note");

    if (nextFilterStatus === "all" || nextFilterStatus === "active" || nextFilterStatus === "invited" || nextFilterStatus === "disabled") {
      setFilterStatus(nextFilterStatus);
    }
    if (nextSearch !== null) {
      setSearch(nextSearch);
    }

    if (!roster.length) {
      if (nextEmail || nextName || nextRole || nextStatus || nextNote) {
        setMemberForm((current) => ({
          ...current,
          email: nextEmail ?? current.email,
          name: nextName ?? current.name,
          role: nextRole ?? current.role,
          status: nextStatus ?? current.status,
          note: nextNote ?? current.note
        }));
      }
      return;
    }

    const matchedMember = roster.find((entry) => {
      if (nextMemberId && entry.member_id === nextMemberId) return true;
      if (nextEmail && entry.email.toLowerCase() === nextEmail.toLowerCase()) return true;
      return false;
    });

    if (matchedMember) {
      selectMember(matchedMember.member_id);
      return;
    }

    if (nextEmail || nextName || nextRole || nextStatus || nextNote) {
      setSelectedMemberId("");
      setMemberForm((current) => ({
        ...current,
        email: nextEmail ?? current.email,
        name: nextName ?? current.name,
        role: nextRole ?? current.role,
        status: nextStatus ?? current.status,
        note: nextNote ?? current.note
      }));
    }
  }, [roster, searchParams]);

  function updateMemberForm<K extends keyof MemberFormState>(key: K, value: MemberFormState[K]) {
    setMemberForm((current) => ({ ...current, [key]: value }));
  }

  function selectMember(memberId: string) {
    setSelectedMemberId(memberId);
    const member = roster.find((entry) => entry.member_id === memberId);
    if (!member) {
      return;
    }
    setMemberForm({
      name: member.name,
      email: member.email,
      role: member.role,
      status: member.status,
      note: member.note
    });
  }

  function resetForm() {
    setSelectedMemberId("");
    setMemberForm(DEFAULT_MEMBER_FORM);
  }

  async function disableMember(memberId: string) {
    setNotice(null);
    setRosterError(null);
    const res = await fetch(`/api/app/team/users/${encodeURIComponent(memberId)}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ status: "disabled" })
    });
    const data = (await res.json().catch(() => null)) as TeamMemberRecord | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setRosterError(resolveApiErrorMessage(t, data, tr("team.errors.disableMember" as MessageKey)));
      return;
    }
    const record = data as TeamMemberRecord;
    setRoster((current) => replaceMemberById(current, memberId, () => record));
    if (selectedMemberId === memberId) {
      setSelectedMemberId(memberId);
      setMemberForm({
        name: record.name,
        email: record.email,
        role: record.role,
        status: record.status,
        note: record.note
      });
    }
    setNotice(tr("team.notice.memberDisabled" as MessageKey));
  }

  async function onSaveMember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNotice(null);
    setRosterError(null);

    const email = memberForm.email.trim().toLowerCase();
    if (!email) {
      return;
    }

    const payload = {
      name: memberForm.name.trim(),
      email,
      role: memberForm.role,
      status: memberForm.status,
      note: memberForm.note.trim()
    };
    const isEditing = Boolean(selectedMemberId);
    const res = await fetch(isEditing ? `/api/app/team/users/${encodeURIComponent(selectedMemberId)}` : "/api/app/team/users", {
      method: isEditing ? "PATCH" : "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = (await res.json().catch(() => null)) as TeamMemberRecord | { error?: string; detail?: unknown } | null;
    if (!res.ok) {
      setRosterError(resolveApiErrorMessage(t, data, tr("team.errors.saveMember" as MessageKey)));
      return;
    }

    const record = data as TeamMemberRecord;
    setRoster((current) => upsertMember(current, record));
    setSelectedMemberId(record.member_id);
    setMemberForm({
      name: record.name,
      email: record.email,
      role: record.role,
      status: record.status,
      note: record.note
    });
    setNotice(tr("team.notice.memberSaved" as MessageKey));
  }

  return (
    <AppShell
      title={tr("team.title" as MessageKey)}
      subtitle={tr("team.subtitle" as MessageKey)}
      activePath="/team"
      actions={<Pill>{tr("team.active" as MessageKey)}</Pill>}
    >
      <MetricGrid>
        <MetricCard label={tr("team.stats.total" as MessageKey)} value={roster.length} meta={tr("team.stats.totalMeta" as MessageKey)} />
        <MetricCard label={tr("team.stats.active" as MessageKey)} value={activeCount} meta={tr("team.stats.activeMeta" as MessageKey)} accent />
        <MetricCard label={tr("team.stats.invited" as MessageKey)} value={invitedCount} meta={tr("team.stats.invitedMeta" as MessageKey)} />
        <MetricCard label={tr("team.stats.disabled" as MessageKey)} value={disabledCount} meta={tr("team.stats.disabledMeta" as MessageKey)} />
      </MetricGrid>

      <Panel
        title={tr("team.auth.title" as MessageKey)}
        description={tr("team.auth.description" as MessageKey)}
        actions={
          <div className="otc-controls">
            <button className="otc-button" type="button" onClick={() => loadAuthContext()} disabled={authLoading}>
              {authLoading ? tr("team.auth.loading" as MessageKey) : tr("team.auth.refresh" as MessageKey)}
            </button>
          </div>
        }
      >
        {authError ? <Message tone="error">{authError}</Message> : null}
        {authContext ? (
          <CodeBlock>{JSON.stringify(authContext, null, 2)}</CodeBlock>
        ) : (
          <Message>{tr("team.auth.empty" as MessageKey)}</Message>
        )}
      </Panel>

      <Panel title={tr("team.identity.title" as MessageKey)} description={tr("team.identity.description" as MessageKey)}>
        <div className="otc-grid otc-grid--counterparty-form">
          <label className="otc-field">
            {tr("team.identity.keycloakUrl" as MessageKey)}
            <input className="otc-input" value={keycloakUrl} onChange={(event) => setKeycloakUrl(event.target.value)} placeholder="http://localhost:8088" />
          </label>
        </div>
        <div className="otc-controls otc-controls--spaced">
          <a className="otc-button otc-button--ghost" href={keycloakUrl || undefined} target="_blank" rel="noreferrer">
            {tr("team.identity.openKeycloak" as MessageKey)}
          </a>
          <button className="otc-button otc-button--ghost" type="button" onClick={() => exportRosterJson(roster)} disabled={!roster.length}>
            {tr("team.roster.export" as MessageKey)}
          </button>
        </div>
      </Panel>

      <Panel title={tr("team.roster.title" as MessageKey)} description={tr("team.roster.description" as MessageKey)}>
        <form className="otc-stack" onSubmit={onSaveMember}>
          <div className="otc-grid otc-grid--counterparty-form">
            <label className="otc-field">
              {tr("team.roster.form.name" as MessageKey)}
              <input className="otc-input" value={memberForm.name} onChange={(event) => updateMemberForm("name", event.target.value)} />
            </label>
            <label className="otc-field">
              {tr("team.roster.form.email" as MessageKey)}
              <input className="otc-input" type="email" value={memberForm.email} onChange={(event) => updateMemberForm("email", event.target.value)} required />
            </label>
            <label className="otc-field">
              {tr("team.roster.form.role" as MessageKey)}
              <select
                className="otc-select"
                data-testid="team-role-select"
                value={memberForm.role}
                onChange={(event) => updateMemberForm("role", event.target.value as TeamRole)}
              >
                {TEAM_ROLE_VALUES.map((role) => (
                  <option key={role} value={role}>
                    {formatTeamRoleValue(role)}
                  </option>
                ))}
              </select>
            </label>
            <label className="otc-field">
              {tr("team.roster.form.status" as MessageKey)}
              <select className="otc-select" value={memberForm.status} onChange={(event) => updateMemberForm("status", event.target.value as TeamMemberStatus)}>
                <option value="active">{tr("team.roster.status.active" as MessageKey)}</option>
                <option value="invited">{tr("team.roster.status.invited" as MessageKey)}</option>
                <option value="disabled">{tr("team.roster.status.disabled" as MessageKey)}</option>
              </select>
            </label>
          </div>

          <label className="otc-field">
            {tr("team.roster.form.note" as MessageKey)}
            <textarea className="otc-textarea" rows={3} value={memberForm.note} onChange={(event) => updateMemberForm("note", event.target.value)} />
          </label>

          <div className="otc-controls">
            <button className="otc-button otc-button--accent" type="submit">
              {selectedMemberId ? tr("team.roster.form.update" as MessageKey) : tr("team.roster.form.add" as MessageKey)}
            </button>
            <button className="otc-button" type="button" onClick={resetForm}>
              {tr("team.roster.form.reset" as MessageKey)}
            </button>
          </div>
          {notice ? <Message tone="success">{notice}</Message> : null}
          {rosterError ? <Message tone="error">{rosterError}</Message> : null}
        </form>

        <div className="otc-controls otc-controls--spaced">
          <label className="otc-field">
            {tr("team.roster.filters.status" as MessageKey)}
            <select className="otc-select" value={filterStatus} onChange={(event) => setFilterStatus(event.target.value as TeamMemberStatus | "all")}>
              <option value="all">{tr("team.roster.filters.all" as MessageKey)}</option>
              <option value="active">{tr("team.roster.status.active" as MessageKey)}</option>
              <option value="invited">{tr("team.roster.status.invited" as MessageKey)}</option>
              <option value="disabled">{tr("team.roster.status.disabled" as MessageKey)}</option>
            </select>
          </label>
          <label className="otc-field">
            {tr("team.roster.filters.search" as MessageKey)}
            <input className="otc-input" data-testid="team-search-input" value={search} onChange={(event) => setSearch(event.target.value)} />
          </label>
        </div>

        {filteredRoster.length ? (
          <table className="otc-table otc-table--spaced">
            <thead>
              <tr>
                <th>{tr("team.roster.table.name" as MessageKey)}</th>
                <th>{tr("team.roster.table.email" as MessageKey)}</th>
                <th>{tr("team.roster.table.role" as MessageKey)}</th>
                <th>{tr("team.roster.table.status" as MessageKey)}</th>
                <th>{tr("team.roster.table.updated" as MessageKey)}</th>
                <th>{tr("team.roster.table.actions" as MessageKey)}</th>
              </tr>
            </thead>
            <tbody>
              {filteredRoster.map((record) => (
                <tr key={record.member_id} data-testid="team-row">
                  <td><strong>{record.name || record.email}</strong></td>
                  <td>{record.email}</td>
                  <td>
                    <Pill
                      tone={
                        record.role === "ADMIN"
                          ? "danger"
                          : record.role === "COMPLIANCE_OFFICER" || record.role === "LEGAL_REVIEWER" || record.role === "REVIEWER"
                            ? "warning"
                            : undefined
                      }
                    >
                      {formatTeamRoleValue(record.role)}
                    </Pill>
                  </td>
                  <td data-testid="team-row-status">
                    <Pill tone={record.status === "disabled" ? "danger" : record.status === "invited" ? "warning" : undefined}>
                      {tr(`team.roster.status.${record.status}` as MessageKey)}
                    </Pill>
                  </td>
                  <td data-testid="team-row-updated">{formatTeamTimestamp(record.updated_at)}</td>
                  <td>
                    <div className="otc-controls">
                      <button className="otc-button otc-button--ghost" type="button" onClick={() => selectMember(record.member_id)}>
                        {tr("team.roster.table.edit" as MessageKey)}
                      </button>
                      <a className="otc-button otc-button--ghost" href={buildBillingHref(record)}>
                        {tr("team.roster.table.openBilling" as MessageKey)}
                      </a>
                      <button className="otc-button otc-button--ghost" type="button" onClick={() => disableMember(record.member_id)}>
                        {tr("team.roster.table.remove" as MessageKey)}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : rosterLoading ? (
          <Message>{t("common.loading")}</Message>
        ) : (
          <Message>{tr("team.roster.table.empty" as MessageKey)}</Message>
        )}
      </Panel>

      <Panel title={tr("team.about.title" as MessageKey)} description={tr("team.about.description" as MessageKey)}>
        <ul className="otc-list">
          <li>{tr("team.about.point1" as MessageKey)}</li>
          <li>{tr("team.about.point2" as MessageKey)}</li>
          <li>{tr("team.about.point3" as MessageKey)}</li>
        </ul>
      </Panel>
    </AppShell>
  );
}

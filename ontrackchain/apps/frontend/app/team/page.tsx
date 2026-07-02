"use client";

import { useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import { useI18n } from "../../components/i18n-provider";
import type { MessageKey } from "../lib/i18n";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";

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

type TeamRole = "ADMIN" | "ANALYST" | "COMPLIANCE_OFFICER" | "LEGAL_REVIEWER";
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
};

type MemberFormState = {
  name: string;
  email: string;
  role: TeamRole;
  status: TeamMemberStatus;
  note: string;
};

const STORAGE_KEY = "otc-team-roster";
const KEYCLOAK_URL_KEY = "otc-team-keycloak-url";

const DEFAULT_MEMBER_FORM: MemberFormState = {
  name: "",
  email: "",
  role: "ANALYST",
  status: "invited",
  note: ""
};

function parseTeamRole(value: string | null): TeamRole | null {
  if (value === "ADMIN" || value === "ANALYST" || value === "COMPLIANCE_OFFICER" || value === "LEGAL_REVIEWER") {
    return value;
  }
  return null;
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

function loadRoster(): TeamMemberRecord[] {
  if (typeof window === "undefined") {
    return [];
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveRoster(records: TeamMemberRecord[]) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
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
  const { t } = useI18n();
  const tr = (key: MessageKey, values?: Record<string, string | number>) => t(key, values);

  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const [keycloakUrl, setKeycloakUrl] = useState("");

  const [roster, setRoster] = useState<TeamMemberRecord[]>([]);
  const [memberForm, setMemberForm] = useState<MemberFormState>(DEFAULT_MEMBER_FORM);
  const [selectedMemberId, setSelectedMemberId] = useState<string>("");
  const [filterStatus, setFilterStatus] = useState<TeamMemberStatus | "all">("all");
  const [search, setSearch] = useState("");
  const [notice, setNotice] = useState<string | null>(null);

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
        record.role.toLowerCase().includes(query);
      return matchesStatus && matchesSearch;
    });
  }, [filterStatus, roster, search]);

  useEffect(() => {
    setRoster(loadRoster());
    setKeycloakUrl(loadKeycloakUrl());
  }, []);

  useEffect(() => {
    saveRoster(roster);
  }, [roster]);

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

  function removeMember(memberId: string) {
    setRoster((current) => current.filter((entry) => entry.member_id !== memberId));
    if (selectedMemberId === memberId) {
      resetForm();
    }
    setNotice(tr("team.notice.memberRemoved" as MessageKey));
  }

  function onSaveMember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNotice(null);

    const email = memberForm.email.trim().toLowerCase();
    if (!email) {
      return;
    }

    const now = new Date().toISOString();
    const memberId = selectedMemberId || crypto.randomUUID();
    const record: TeamMemberRecord = {
      member_id: memberId,
      name: memberForm.name.trim(),
      email,
      role: memberForm.role,
      status: memberForm.status,
      note: memberForm.note.trim(),
      created_at: selectedMemberId ? roster.find((entry) => entry.member_id === selectedMemberId)?.created_at ?? now : now,
      updated_at: now
    };
    setRoster((current) => upsertMember(current, record));
    setSelectedMemberId(memberId);
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
              <select className="otc-select" value={memberForm.role} onChange={(event) => updateMemberForm("role", event.target.value as TeamRole)}>
                <option value="ADMIN">ADMIN</option>
                <option value="ANALYST">ANALYST</option>
                <option value="COMPLIANCE_OFFICER">COMPLIANCE_OFFICER</option>
                <option value="LEGAL_REVIEWER">LEGAL_REVIEWER</option>
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
            <input className="otc-input" value={search} onChange={(event) => setSearch(event.target.value)} />
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
                <tr key={record.member_id}>
                  <td><strong>{record.name || record.email}</strong></td>
                  <td>{record.email}</td>
                  <td><Pill tone={record.role === "ADMIN" ? "danger" : record.role === "COMPLIANCE_OFFICER" ? "warning" : undefined}>{record.role}</Pill></td>
                  <td><Pill tone={record.status === "disabled" ? "danger" : record.status === "invited" ? "warning" : undefined}>{tr(`team.roster.status.${record.status}` as MessageKey)}</Pill></td>
                  <td>{record.updated_at}</td>
                  <td>
                    <div className="otc-controls">
                      <button className="otc-button otc-button--ghost" type="button" onClick={() => selectMember(record.member_id)}>
                        {tr("team.roster.table.edit" as MessageKey)}
                      </button>
                      <a className="otc-button otc-button--ghost" href={buildBillingHref(record)}>
                        {tr("team.roster.table.openBilling" as MessageKey)}
                      </a>
                      <button className="otc-button otc-button--ghost" type="button" onClick={() => removeMember(record.member_id)}>
                        {tr("team.roster.table.remove" as MessageKey)}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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

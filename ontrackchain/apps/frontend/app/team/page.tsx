"use client";

import { useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { AppShell, CodeBlock, ConfirmDialog, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import { useI18n } from "../../components/i18n-provider";
import { canManageFederatedIdentity, canReadBilling } from "../lib/authz";
import type { MessageKey } from "../lib/i18n";
import { formatDateTime } from "../lib/date-format";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { TEAM_ROLE_VALUES, isTeamRoleValue, normalizeTeamRoleValue } from "../lib/team-catalog";

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

type TeamExternalIdentityRecord = {
  provider: string;
  external_subject: string;
  email_snapshot?: string | null;
  role_snapshot?: string | null;
  created_at: string;
  last_seen_at?: string | null;
};

type FederatedDirectoryUserRecord = {
  provider: string;
  external_subject: string;
  email?: string | null;
  username?: string | null;
  organization_id?: string | null;
  role_snapshot?: string | null;
  enabled: boolean;
  match_status: string;
  linked_user_id?: string | null;
  linked_user_email?: string | null;
  role_validation_status: string;
  warnings: string[];
};

type FederatedDirectoryFilter = "all" | "ready" | "linked" | "review";
type FederatedDirectorySort = "priority" | "alphabetical";
type FederatedDirectoryContextNotice = "restored" | "cleared" | null;
type TeamConfirmDialogState =
  | {
      kind: "clear_federated";
      count: number;
    }
  | {
      kind: "unlink_identity";
      identity: TeamExternalIdentityRecord;
      memberEmail: string;
    }
  | null;

type MemberFormState = {
  name: string;
  email: string;
  role: TeamRole;
  status: TeamMemberStatus;
  note: string;
};

type IdentityLinkFormState = {
  provider: string;
  externalSubject: string;
  emailSnapshot: string;
  roleSnapshot: string;
};

const KEYCLOAK_URL_KEY = "otc-team-keycloak-url";
const FEDERATED_DIRECTORY_FILTER_KEY = "otc-team-federated-filter";
const FEDERATED_DIRECTORY_SORT_KEY = "otc-team-federated-sort";
const FEDERATED_DIRECTORY_QUERY_KEY = "otc-team-federated-query";

const DEFAULT_MEMBER_FORM: MemberFormState = {
  name: "",
  email: "",
  role: "ANALYST",
  status: "invited",
  note: ""
};

const DEFAULT_IDENTITY_LINK_FORM: IdentityLinkFormState = {
  provider: "keycloak",
  externalSubject: "",
  emailSnapshot: "",
  roleSnapshot: ""
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

function parseFederatedDirectoryFilter(value: string | null): FederatedDirectoryFilter | null {
  if (value === "all" || value === "ready" || value === "linked" || value === "review") {
    return value;
  }
  return null;
}

function parseFederatedDirectorySort(value: string | null): FederatedDirectorySort | null {
  if (value === "priority" || value === "alphabetical") {
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

function buildIdentityAuditHref(memberId: string) {
  const params = new URLSearchParams({
    preset: "identity-federated",
    resource_id: memberId
  });
  return `/audit?${params.toString()}`;
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

function loadFederatedDirectoryFilter(): FederatedDirectoryFilter {
  if (typeof window === "undefined") {
    return "all";
  }
  try {
    return parseFederatedDirectoryFilter(window.localStorage.getItem(FEDERATED_DIRECTORY_FILTER_KEY)) ?? "all";
  } catch {
    return "all";
  }
}

function saveFederatedDirectoryFilter(value: FederatedDirectoryFilter) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(FEDERATED_DIRECTORY_FILTER_KEY, value);
}

function loadFederatedDirectorySort(): FederatedDirectorySort {
  if (typeof window === "undefined") {
    return "priority";
  }
  try {
    return parseFederatedDirectorySort(window.localStorage.getItem(FEDERATED_DIRECTORY_SORT_KEY)) ?? "priority";
  } catch {
    return "priority";
  }
}

function saveFederatedDirectorySort(value: FederatedDirectorySort) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(FEDERATED_DIRECTORY_SORT_KEY, value);
}

function loadFederatedDirectoryQuery() {
  if (typeof window === "undefined") {
    return "";
  }
  try {
    return window.localStorage.getItem(FEDERATED_DIRECTORY_QUERY_KEY) ?? "";
  } catch {
    return "";
  }
}

function saveFederatedDirectoryQuery(value: string) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(FEDERATED_DIRECTORY_QUERY_KEY, value);
}

function resolveInitialFederatedDirectoryContextNotice(): FederatedDirectoryContextNotice {
  const hasRestoredContext =
    loadFederatedDirectoryQuery().trim().length > 0 ||
    loadFederatedDirectoryFilter() !== "all" ||
    loadFederatedDirectorySort() !== "priority";
  return hasRestoredContext ? "restored" : null;
}

function upsertMember(current: TeamMemberRecord[], record: TeamMemberRecord) {
  const next = [record, ...current.filter((entry) => entry.member_id !== record.member_id)];
  next.sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || ""));
  return next;
}

function replaceMemberById(current: TeamMemberRecord[], memberId: string, updater: (record: TeamMemberRecord) => TeamMemberRecord) {
  return current.map((entry) => (entry.member_id === memberId ? updater(entry) : entry));
}

function buildExternalIdentityKey(identity: Pick<TeamExternalIdentityRecord, "provider" | "external_subject">) {
  return `${identity.provider}::${identity.external_subject}`;
}

function buildFederatedCandidateKey(candidate: Pick<FederatedDirectoryUserRecord, "provider" | "external_subject">) {
  return `${candidate.provider}::${candidate.external_subject}`;
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

  const [keycloakUrl, setKeycloakUrl] = useState(loadKeycloakUrl);

  const [roster, setRoster] = useState<TeamMemberRecord[]>([]);
  const [rosterLoading, setRosterLoading] = useState(false);
  const [rosterError, setRosterError] = useState<string | null>(null);
  const [memberForm, setMemberForm] = useState<MemberFormState>(DEFAULT_MEMBER_FORM);
  const [identityLinkForm, setIdentityLinkForm] = useState<IdentityLinkFormState>(DEFAULT_IDENTITY_LINK_FORM);
  const [identityLinking, setIdentityLinking] = useState(false);
  const [selectedMemberIdentities, setSelectedMemberIdentities] = useState<TeamExternalIdentityRecord[]>([]);
  const [identityDetailsLoading, setIdentityDetailsLoading] = useState(false);
  const [identityDetailsError, setIdentityDetailsError] = useState<string | null>(null);
  const [identityUnlinkingKey, setIdentityUnlinkingKey] = useState<string | null>(null);
  const [federatedDirectoryQuery, setFederatedDirectoryQuery] = useState(loadFederatedDirectoryQuery);
  const [federatedDirectoryLoading, setFederatedDirectoryLoading] = useState(false);
  const [federatedDirectoryError, setFederatedDirectoryError] = useState<string | null>(null);
  const [federatedDirectoryResults, setFederatedDirectoryResults] = useState<FederatedDirectoryUserRecord[]>([]);
  const [federatedDirectoryActionKey, setFederatedDirectoryActionKey] = useState<string | null>(null);
  const [federatedDirectoryFilter, setFederatedDirectoryFilter] = useState<FederatedDirectoryFilter>(loadFederatedDirectoryFilter);
  const [federatedDirectorySort, setFederatedDirectorySort] = useState<FederatedDirectorySort>(loadFederatedDirectorySort);
  const [federatedDirectoryContextNotice, setFederatedDirectoryContextNotice] =
    useState<FederatedDirectoryContextNotice>(resolveInitialFederatedDirectoryContextNotice);
  const [confirmDialogState, setConfirmDialogState] = useState<TeamConfirmDialogState>(null);
  const [selectedMemberId, setSelectedMemberId] = useState<string>("");
  const [filterStatus, setFilterStatus] = useState<TeamMemberStatus | "all">("all");
  const [search, setSearch] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const canManageIdentity = canManageFederatedIdentity(authContext?.role);
  const canOpenBilling = authContext ? canReadBilling(authContext.role) : false;
  const federatedDirectoryQueryTrimmed = federatedDirectoryQuery.trim();
  const federatedDirectoryClearRequiresConfirm = federatedDirectoryResults.length > 0;

  const confirmDialogConfig = useMemo(() => {
    if (!confirmDialogState) {
      return null;
    }

    if (confirmDialogState.kind === "clear_federated") {
      return {
        title: tr("team.federatedDirectory.clearContextConfirmTitle" as MessageKey),
        description: tr("team.federatedDirectory.clearContextConfirm" as MessageKey, { count: confirmDialogState.count }),
        confirmLabel: tr("team.federatedDirectory.clearContextConfirmAction" as MessageKey),
        cancelLabel: tr("common.cancel" as MessageKey),
        tone: "danger" as const,
        testId: "team-confirm-dialog-clear-context"
      };
    }

    return {
      title: tr("team.identity.unlinkConfirmTitle" as MessageKey),
      description: tr("team.identity.unlinkConfirm" as MessageKey, {
        provider: confirmDialogState.identity.provider,
        externalSubject: confirmDialogState.identity.external_subject,
        email: confirmDialogState.memberEmail
      }),
      confirmLabel: tr("team.identity.unlinkConfirmAction" as MessageKey),
      cancelLabel: tr("common.cancel" as MessageKey),
      tone: "danger" as const,
      testId: "team-confirm-dialog-unlink-identity"
    };
  }, [confirmDialogState, tr]);

  function resolveTeamRoleLabel(value: TeamRole | string) {
    const normalizedRole = normalizeTeamRoleValue(value);
    return normalizedRole ? tr(`team.roster.roles.${normalizedRole}` as MessageKey) : value;
  }

  function formatTeamRoleValue(value: TeamRole | string) {
    const label = resolveTeamRoleLabel(value);
    return label === value ? value : `${label} (${value})`;
  }

  function resolveTeamRoleTone(value: TeamRole | string): "warning" | "danger" | undefined {
    const normalizedRole = normalizeTeamRoleValue(value);
    if (normalizedRole === "ADMIN") {
      return "danger";
    }
    if (normalizedRole === "COMPLIANCE_OFFICER" || normalizedRole === "LEGAL_REVIEWER" || normalizedRole === "REVIEWER") {
      return "warning";
    }
    return undefined;
  }

  function formatTeamTimestamp(value: string) {
    const normalized = value.trim();
    if (!normalized) {
      return tr("common.notAvailable" as MessageKey);
    }
    return formatDateTime(normalized, locale) ?? normalized;
  }

  function getIdentityState(record: TeamMemberRecord): "linked" | "pending" {
    return (record.linked_identity_count ?? 0) > 0 ? "linked" : "pending";
  }

  function resolveFederatedMatchTone(matchStatus: string): "success" | "warning" | "danger" {
    switch (matchStatus) {
      case "linked":
        return "success";
      case "suggested":
      case "org_match_only":
        return "warning";
      default:
        return "danger";
    }
  }

  function resolveFederatedMatchLabel(matchStatus: string) {
    const keyByStatus: Record<string, MessageKey> = {
      linked: "team.federatedDirectory.matchStatus.linked",
      suggested: "team.federatedDirectory.matchStatus.suggested",
      org_match_only: "team.federatedDirectory.matchStatus.orgMatchOnly",
      org_mismatch: "team.federatedDirectory.matchStatus.orgMismatch"
    };
    const key = keyByStatus[matchStatus];
    return key ? tr(key) : matchStatus;
  }

  function resolveFederatedRoleValidationTone(status: string): "success" | "warning" | "danger" {
    switch (status) {
      case "valid":
        return "success";
      case "mismatch":
        return "danger";
      case "missing":
      case "unknown":
      default:
        return "warning";
    }
  }

  function resolveFederatedRoleValidationLabel(status: string) {
    const keyByStatus: Record<string, MessageKey> = {
      valid: "team.federatedDirectory.roleValidation.valid",
      missing: "team.federatedDirectory.roleValidation.missing",
      unknown: "team.federatedDirectory.roleValidation.unknown",
      mismatch: "team.federatedDirectory.roleValidation.mismatch"
    };
    const key = keyByStatus[status];
    return key ? tr(key) : status;
  }

  function resolveFederatedWarningLabel(warningCode: string) {
    const keyByWarning: Record<string, MessageKey> = {
      candidate_org_missing: "team.federatedDirectory.warning.candidateOrgMissing",
      candidate_org_mismatch: "team.federatedDirectory.warning.candidateOrgMismatch",
      candidate_email_missing: "team.federatedDirectory.warning.candidateEmailMissing",
      candidate_email_mismatch: "team.federatedDirectory.warning.candidateEmailMismatch",
      candidate_role_missing: "team.federatedDirectory.warning.candidateRoleMissing",
      candidate_role_unknown: "team.federatedDirectory.warning.candidateRoleUnknown",
      candidate_role_mismatch: "team.federatedDirectory.warning.candidateRoleMismatch",
      candidate_already_linked: "team.federatedDirectory.warning.candidateAlreadyLinked",
      candidate_already_linked_to_member: "team.federatedDirectory.warning.candidateAlreadyLinkedToMember"
    };
    const key = keyByWarning[warningCode];
    return key ? tr(key) : warningCode;
  }

  function resolveFederatedMatchReasonLabel(matchReason: string) {
    const keyByReason: Record<string, MessageKey> = {
      ready: "team.federatedDirectory.matchReason.ready",
      already_linked: "team.federatedDirectory.matchReason.alreadyLinked",
      org_mismatch: "team.federatedDirectory.matchReason.orgMismatch",
      email_mismatch: "team.federatedDirectory.matchReason.emailMismatch",
      role_missing: "team.federatedDirectory.matchReason.roleMissing",
      role_unknown: "team.federatedDirectory.matchReason.roleUnknown",
      role_mismatch: "team.federatedDirectory.matchReason.roleMismatch",
      unknown: "team.federatedDirectory.matchReason.unknown"
    };
    const key = keyByReason[matchReason];
    return key ? tr(key) : matchReason;
  }

  function buildFederatedCannotLinkMessage(matchReason?: string, warnings?: string[]) {
    const reasonLabel = resolveFederatedMatchReasonLabel(String(matchReason || "unknown"));
    const firstWarning = Array.isArray(warnings) && warnings.length ? resolveFederatedWarningLabel(warnings[0]) : null;
    if (firstWarning) {
      return tr("team.federatedDirectory.errors.cannotLinkWithWarning" as MessageKey, {
        reason: reasonLabel,
        warning: firstWarning
      });
    }
    return tr("team.federatedDirectory.errors.cannotLink" as MessageKey, { reason: reasonLabel });
  }

  function isFederatedCandidateLinkable(candidate: FederatedDirectoryUserRecord) {
    return candidate.match_status === "suggested" && candidate.role_validation_status === "valid" && !candidate.linked_user_id;
  }

  function resolveFederatedCandidateActionTitle(candidate: FederatedDirectoryUserRecord) {
    if (isFederatedCandidateLinkable(candidate)) {
      return tr("team.federatedDirectory.link" as MessageKey);
    }
    if (candidate.warnings?.length) {
      return resolveFederatedWarningLabel(candidate.warnings[0]);
    }
    return resolveFederatedMatchLabel(candidate.match_status);
  }

  function resolveFederatedCandidateSortRank(candidate: FederatedDirectoryUserRecord) {
    if (isFederatedCandidateLinkable(candidate)) {
      return 0;
    }
    if (!candidate.linked_user_id) {
      return 1;
    }
    return 2;
  }

  function performResetFederatedDirectoryContext() {
    setFederatedDirectoryQuery("");
    setFederatedDirectoryFilter("all");
    setFederatedDirectorySort("priority");
    setFederatedDirectoryResults([]);
    setFederatedDirectoryError(null);
    setFederatedDirectoryActionKey(null);
    setFederatedDirectoryContextNotice("cleared");
  }

  function resetFederatedDirectoryContext() {
    if (federatedDirectoryClearRequiresConfirm) {
      setConfirmDialogState({
        kind: "clear_federated",
        count: federatedDirectoryResults.length
      });
      return;
    }

    performResetFederatedDirectoryContext();
  }

  const activeCount = useMemo(() => roster.filter((r) => r.status === "active").length, [roster]);
  const invitedCount = useMemo(() => roster.filter((r) => r.status === "invited").length, [roster]);
  const disabledCount = useMemo(() => roster.filter((r) => r.status === "disabled").length, [roster]);
  const federatedDirectorySummary = useMemo(() => {
    const total = federatedDirectoryResults.length;
    const ready = federatedDirectoryResults.filter((candidate) => isFederatedCandidateLinkable(candidate)).length;
    const linked = federatedDirectoryResults.filter((candidate) => Boolean(candidate.linked_user_id)).length;
    const review = Math.max(total - ready - linked, 0);
    return { total, ready, linked, review };
  }, [federatedDirectoryResults]);
  const filteredFederatedDirectoryResults = useMemo(() => {
    switch (federatedDirectoryFilter) {
      case "ready":
        return federatedDirectoryResults.filter((candidate) => isFederatedCandidateLinkable(candidate));
      case "linked":
        return federatedDirectoryResults.filter((candidate) => Boolean(candidate.linked_user_id));
      case "review":
        return federatedDirectoryResults.filter(
          (candidate) => !isFederatedCandidateLinkable(candidate) && !candidate.linked_user_id
        );
      case "all":
      default:
        return federatedDirectoryResults;
    }
  }, [federatedDirectoryFilter, federatedDirectoryResults]);
  const orderedFederatedDirectoryResults = useMemo(() => {
    return [...filteredFederatedDirectoryResults].sort((left, right) => {
      if (federatedDirectorySort === "alphabetical") {
        const leftIdentity = `${left.email || ""}::${left.external_subject || ""}`.toLowerCase();
        const rightIdentity = `${right.email || ""}::${right.external_subject || ""}`.toLowerCase();
        return leftIdentity.localeCompare(rightIdentity);
      }

      const rankDifference = resolveFederatedCandidateSortRank(left) - resolveFederatedCandidateSortRank(right);
      if (rankDifference !== 0) {
        return rankDifference;
      }

      if (left.enabled !== right.enabled) {
        return left.enabled ? -1 : 1;
      }

      const leftWarnings = left.warnings?.length ?? 0;
      const rightWarnings = right.warnings?.length ?? 0;
      if (leftWarnings !== rightWarnings) {
        return leftWarnings - rightWarnings;
      }

      const leftIdentity = `${left.email || ""}::${left.external_subject || ""}`.toLowerCase();
      const rightIdentity = `${right.email || ""}::${right.external_subject || ""}`.toLowerCase();
      return leftIdentity.localeCompare(rightIdentity);
    });
  }, [federatedDirectorySort, filteredFederatedDirectoryResults]);
  const hasFederatedDirectoryContext = useMemo(() => {
    return (
      federatedDirectoryQuery.trim().length > 0 ||
      federatedDirectoryFilter !== "all" ||
      federatedDirectorySort !== "priority" ||
      federatedDirectoryResults.length > 0 ||
      Boolean(federatedDirectoryError)
    );
  }, [
    federatedDirectoryError,
    federatedDirectoryFilter,
    federatedDirectoryQuery,
    federatedDirectoryResults.length,
    federatedDirectorySort
  ]);
  const selectedMember = useMemo(
    () => roster.find((entry) => entry.member_id === selectedMemberId) ?? null,
    [roster, selectedMemberId]
  );

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
    saveKeycloakUrl(keycloakUrl.trim());
  }, [keycloakUrl]);

  useEffect(() => {
    saveFederatedDirectoryFilter(federatedDirectoryFilter);
  }, [federatedDirectoryFilter]);

  useEffect(() => {
    saveFederatedDirectorySort(federatedDirectorySort);
  }, [federatedDirectorySort]);

  useEffect(() => {
    saveFederatedDirectoryQuery(federatedDirectoryQuery);
  }, [federatedDirectoryQuery]);

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

  async function loadSelectedMemberIdentities(memberId: string) {
    if (!memberId || !canManageIdentity) {
      setSelectedMemberIdentities([]);
      setIdentityDetailsError(null);
      setIdentityDetailsLoading(false);
      return;
    }

    setIdentityDetailsLoading(true);
    setIdentityDetailsError(null);
    try {
      const res = await fetch(`/api/app/team/users/${encodeURIComponent(memberId)}/external-identities`, { cache: "no-store" });
      const data = (await res.json().catch(() => null)) as
        | { data?: TeamExternalIdentityRecord[]; error?: string; detail?: unknown }
        | null;
      if (!res.ok) {
        setSelectedMemberIdentities([]);
        setIdentityDetailsError(resolveApiErrorMessage(t, data, tr("team.errors.loadIdentityDetails" as MessageKey)));
        setIdentityDetailsLoading(false);
        return;
      }

      setSelectedMemberIdentities(Array.isArray(data?.data) ? data.data : []);
      setIdentityDetailsLoading(false);
    } catch (err) {
      setSelectedMemberIdentities([]);
      setIdentityDetailsError(err instanceof Error ? err.message : tr("team.errors.loadIdentityDetails" as MessageKey));
      setIdentityDetailsLoading(false);
    }
  }

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

  useEffect(() => {
    if (!selectedMemberId || !canManageIdentity) {
      setSelectedMemberIdentities([]);
      setIdentityDetailsError(null);
      setIdentityDetailsLoading(false);
      return;
    }
    loadSelectedMemberIdentities(selectedMemberId).catch(() => undefined);
  }, [canManageIdentity, selectedMemberId]);

  function updateMemberForm<K extends keyof MemberFormState>(key: K, value: MemberFormState[K]) {
    setMemberForm((current) => ({ ...current, [key]: value }));
  }

  function syncIdentityLinkForm(record: TeamMemberRecord | null) {
    if (!record) {
      setIdentityLinkForm(DEFAULT_IDENTITY_LINK_FORM);
      return;
    }
    setIdentityLinkForm({
      provider: "keycloak",
      externalSubject: "",
      emailSnapshot: record.email,
      roleSnapshot: record.role
    });
  }

  function updateIdentityLinkForm<K extends keyof IdentityLinkFormState>(key: K, value: IdentityLinkFormState[K]) {
    setIdentityLinkForm((current) => ({ ...current, [key]: value }));
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
    syncIdentityLinkForm(member);
  }

  function resetForm() {
    setSelectedMemberId("");
    setMemberForm(DEFAULT_MEMBER_FORM);
    syncIdentityLinkForm(null);
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

  async function onLinkExternalIdentity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canManageIdentity) {
      setRosterError(tr("apiErrors.teamFederatedIdentityLinkRoleRequired" as MessageKey));
      return;
    }
    if (!selectedMemberId) {
      setRosterError(tr("team.errors.identityRequiresMember" as MessageKey));
      return;
    }

    setNotice(null);
    setRosterError(null);
    setIdentityLinking(true);

    const payload = {
      provider: identityLinkForm.provider.trim().toLowerCase(),
      external_subject: identityLinkForm.externalSubject.trim(),
      email_snapshot: identityLinkForm.emailSnapshot.trim(),
      role_snapshot: identityLinkForm.roleSnapshot.trim()
    };

    try {
      const res = await fetch(`/api/app/team/users/${encodeURIComponent(selectedMemberId)}/external-identities`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = (await res.json().catch(() => null)) as TeamMemberRecord | { error?: string; detail?: unknown } | null;
      if (!res.ok) {
        setRosterError(resolveApiErrorMessage(t, data, tr("team.errors.linkIdentity" as MessageKey)));
        setIdentityLinking(false);
        return;
      }

      const record = data as TeamMemberRecord;
      setRoster((current) => replaceMemberById(current, selectedMemberId, () => record));
      setSelectedMemberId(record.member_id);
      setMemberForm({
        name: record.name,
        email: record.email,
        role: record.role,
        status: record.status,
        note: record.note
      });
      syncIdentityLinkForm(record);
      await loadSelectedMemberIdentities(record.member_id);
      setNotice(tr("team.notice.identityLinked" as MessageKey));
      setIdentityLinking(false);
    } catch (err) {
      setRosterError(err instanceof Error ? err.message : tr("team.errors.linkIdentity" as MessageKey));
      setIdentityLinking(false);
    }
  }

  async function performUnlinkExternalIdentity(identity: TeamExternalIdentityRecord) {
    if (!canManageIdentity) {
      setRosterError(tr("apiErrors.teamFederatedIdentityUnlinkRoleRequired" as MessageKey));
      return;
    }
    if (!selectedMemberId || !selectedMember) {
      setRosterError(tr("team.errors.identityRequiresMember" as MessageKey));
      return;
    }

    setNotice(null);
    setRosterError(null);
    setIdentityDetailsError(null);
    const identityKey = buildExternalIdentityKey(identity);
    setIdentityUnlinkingKey(identityKey);

    try {
      const res = await fetch(`/api/app/team/users/${encodeURIComponent(selectedMemberId)}/external-identities`, {
        method: "DELETE",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          provider: identity.provider,
          external_subject: identity.external_subject
        })
      });
      const data = (await res.json().catch(() => null)) as TeamMemberRecord | { error?: string; detail?: unknown } | null;
      if (!res.ok) {
        setRosterError(resolveApiErrorMessage(t, data, tr("team.errors.unlinkIdentity" as MessageKey)));
        setIdentityUnlinkingKey(null);
        return;
      }

      const record = data as TeamMemberRecord;
      setRoster((current) => replaceMemberById(current, selectedMemberId, () => record));
      setSelectedMemberId(record.member_id);
      setMemberForm({
        name: record.name,
        email: record.email,
        role: record.role,
        status: record.status,
        note: record.note
      });
      syncIdentityLinkForm(record);
      await loadSelectedMemberIdentities(record.member_id);
      setNotice(tr("team.notice.identityUnlinked" as MessageKey));
      setIdentityUnlinkingKey(null);
    } catch (err) {
      setRosterError(err instanceof Error ? err.message : tr("team.errors.unlinkIdentity" as MessageKey));
      setIdentityUnlinkingKey(null);
    }
  }

  function onUnlinkExternalIdentity(identity: TeamExternalIdentityRecord) {
    if (!selectedMember) {
      setRosterError(tr("team.errors.identityRequiresMember" as MessageKey));
      return;
    }

    setConfirmDialogState({
      kind: "unlink_identity",
      identity,
      memberEmail: selectedMember.email
    });
  }

  async function onConfirmDialog() {
    if (!confirmDialogState) {
      return;
    }

    const pendingDialog = confirmDialogState;
    setConfirmDialogState(null);

    if (pendingDialog.kind === "clear_federated") {
      performResetFederatedDirectoryContext();
      return;
    }

    await performUnlinkExternalIdentity(pendingDialog.identity);
  }

  async function onSearchFederatedDirectory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFederatedDirectoryError(null);
    setFederatedDirectoryResults([]);
    setFederatedDirectoryActionKey(null);
    setFederatedDirectoryContextNotice(null);

    if (!canManageIdentity) {
      setFederatedDirectoryError(tr("team.federatedDirectory.adminOnly" as MessageKey));
      return;
    }

    if (!federatedDirectoryQueryTrimmed) {
      setFederatedDirectoryError(tr("team.federatedDirectory.errors.queryRequired" as MessageKey));
      return;
    }

    setFederatedDirectoryLoading(true);
    try {
      const params = new URLSearchParams({ query: federatedDirectoryQueryTrimmed, limit: "20" });
      const res = await fetch(`/api/app/team/federated-directory/users?${params.toString()}`, { cache: "no-store" });
      const data = (await res.json().catch(() => null)) as
        | { data?: FederatedDirectoryUserRecord[]; error?: string; detail?: unknown }
        | null;
      if (!res.ok) {
        setFederatedDirectoryError(resolveApiErrorMessage(t, data, tr("team.federatedDirectory.errors.search" as MessageKey)));
        setFederatedDirectoryLoading(false);
        return;
      }
      setFederatedDirectoryResults(Array.isArray(data?.data) ? data.data : []);
      setFederatedDirectoryLoading(false);
    } catch (err) {
      setFederatedDirectoryError(err instanceof Error ? err.message : tr("team.federatedDirectory.errors.search" as MessageKey));
      setFederatedDirectoryLoading(false);
    }
  }

  async function onLinkFederatedCandidate(candidate: FederatedDirectoryUserRecord) {
    if (!selectedMemberId || !selectedMember) {
      setRosterError(tr("team.errors.identityRequiresMember" as MessageKey));
      return;
    }
    if (!canManageIdentity) {
      setRosterError(tr("team.federatedDirectory.adminOnly" as MessageKey));
      return;
    }

    setNotice(null);
    setRosterError(null);
    setFederatedDirectoryError(null);

    const actionKey = buildFederatedCandidateKey(candidate);
    setFederatedDirectoryActionKey(actionKey);

    try {
      const suggestionRes = await fetch("/api/app/team/federated-directory/suggestions", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          member_id: selectedMemberId,
          provider: candidate.provider,
          external_subject: candidate.external_subject
        })
      });
      const suggestionPayload = (await suggestionRes.json().catch(() => null)) as
        | {
            can_link?: boolean;
            match_reason?: string;
            warnings?: string[];
            error?: string;
            detail?: unknown;
          }
        | null;
      if (!suggestionRes.ok) {
        setFederatedDirectoryError(resolveApiErrorMessage(t, suggestionPayload, tr("team.federatedDirectory.errors.suggest" as MessageKey)));
        setFederatedDirectoryActionKey(null);
        return;
      }
      if (!suggestionPayload?.can_link) {
        setFederatedDirectoryError(buildFederatedCannotLinkMessage(suggestionPayload?.match_reason, suggestionPayload?.warnings));
        setFederatedDirectoryActionKey(null);
        return;
      }

      const linkRes = await fetch(`/api/app/team/users/${encodeURIComponent(selectedMemberId)}/external-identities`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          provider: candidate.provider,
          external_subject: candidate.external_subject,
          email_snapshot: candidate.email ?? selectedMember.email,
          role_snapshot: candidate.role_snapshot ?? selectedMember.role
        })
      });
      const linkData = (await linkRes.json().catch(() => null)) as TeamMemberRecord | { error?: string; detail?: unknown } | null;
      if (!linkRes.ok) {
        setRosterError(resolveApiErrorMessage(t, linkData, tr("team.errors.linkIdentity" as MessageKey)));
        setFederatedDirectoryActionKey(null);
        return;
      }

      const record = linkData as TeamMemberRecord;
      setRoster((current) => replaceMemberById(current, selectedMemberId, () => record));
      setSelectedMemberId(record.member_id);
      setMemberForm({
        name: record.name,
        email: record.email,
        role: record.role,
        status: record.status,
        note: record.note
      });
      syncIdentityLinkForm(record);
      await loadSelectedMemberIdentities(record.member_id);
      setNotice(tr("team.notice.identityLinked" as MessageKey));
      setFederatedDirectoryActionKey(null);
    } catch (err) {
      setFederatedDirectoryError(err instanceof Error ? err.message : tr("team.federatedDirectory.errors.suggest" as MessageKey));
      setFederatedDirectoryActionKey(null);
    }
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
          <a
            className="otc-button otc-button--ghost"
            href={selectedMember ? buildIdentityAuditHref(selectedMember.member_id) : undefined}
            data-testid="team-open-identity-audit-button"
            aria-disabled={!selectedMember}
          >
            {tr("team.identity.openAudit" as MessageKey)}
          </a>
          <button className="otc-button otc-button--ghost" type="button" onClick={() => exportRosterJson(roster)} disabled={!roster.length}>
            {tr("team.roster.export" as MessageKey)}
          </button>
        </div>
        {canManageIdentity ? (
          <form className="otc-stack" onSubmit={onLinkExternalIdentity}>
            <Message tone={selectedMember ? "success" : undefined}>
              {selectedMember
                ? tr("team.identity.selectedMember" as MessageKey, { email: selectedMember.email })
                : tr("team.identity.selectMemberHint" as MessageKey)}
            </Message>
            <Message>{tr("team.identity.manualLinkHint" as MessageKey)}</Message>
            <div className="otc-grid otc-grid--counterparty-form">
              <label className="otc-field">
                {tr("team.identity.provider" as MessageKey)}
                <input
                  className="otc-input"
                  data-testid="team-identity-provider-input"
                  value={identityLinkForm.provider}
                  onChange={(event) => updateIdentityLinkForm("provider", event.target.value)}
                  placeholder="keycloak"
                />
              </label>
              <label className="otc-field">
                {tr("team.identity.externalSubject" as MessageKey)}
                <input
                  className="otc-input"
                  data-testid="team-identity-subject-input"
                  value={identityLinkForm.externalSubject}
                  onChange={(event) => updateIdentityLinkForm("externalSubject", event.target.value)}
                  placeholder="7b7b1d5c-..."
                />
              </label>
              <label className="otc-field">
                {tr("team.identity.emailSnapshot" as MessageKey)}
                <input
                  className="otc-input"
                  data-testid="team-identity-email-input"
                  value={identityLinkForm.emailSnapshot}
                  onChange={(event) => updateIdentityLinkForm("emailSnapshot", event.target.value)}
                  type="email"
                />
              </label>
              <label className="otc-field">
                {tr("team.identity.roleSnapshot" as MessageKey)}
                <input
                  className="otc-input"
                  data-testid="team-identity-role-input"
                  value={identityLinkForm.roleSnapshot}
                  onChange={(event) => updateIdentityLinkForm("roleSnapshot", event.target.value)}
                />
              </label>
            </div>
            <div className="otc-controls">
              <button
                className="otc-button otc-button--accent"
                type="submit"
                data-testid="team-link-identity-button"
                disabled={identityLinking || !selectedMemberId}
              >
                {identityLinking ? tr("team.identity.linking" as MessageKey) : tr("team.identity.link" as MessageKey)}
              </button>
            </div>
          </form>
        ) : (
          <Message data-testid="team-identity-manual-link-restricted">{tr("team.identity.manualLinkRestricted" as MessageKey)}</Message>
        )}
        <div className="otc-stack" data-testid="team-identity-linked-section">
          <h3>{tr("team.identity.currentTitle" as MessageKey)}</h3>
          <Message>
            {canManageIdentity
              ? tr("team.identity.currentDescription" as MessageKey)
              : tr("team.identity.adminOnlyHint" as MessageKey)}
          </Message>
          {identityDetailsError ? <Message tone="error">{identityDetailsError}</Message> : null}
          {!selectedMember ? (
            <Message>{tr("team.identity.currentEmptySelection" as MessageKey)}</Message>
          ) : !canManageIdentity ? null : identityDetailsLoading ? (
            <Message>{tr("team.identity.currentLoading" as MessageKey)}</Message>
          ) : selectedMemberIdentities.length ? (
            <div className="otc-stack">
              {selectedMemberIdentities.map((identity) => {
                const identityKey = buildExternalIdentityKey(identity);
                return (
                  <div key={identityKey} className="otc-card" data-testid="team-identity-linked-item">
                    <div className="otc-controls otc-controls--spaced">
                      <strong>{identity.provider}</strong>
                      <div className="otc-controls">
                        <a
                          className="otc-button otc-button--ghost"
                          href={selectedMember ? buildIdentityAuditHref(selectedMember.member_id) : undefined}
                          data-testid="team-identity-open-audit-button"
                          aria-disabled={!selectedMember}
                        >
                          {tr("team.identity.openAudit" as MessageKey)}
                        </a>
                        <button
                          className="otc-button otc-button--ghost"
                          type="button"
                          data-testid="team-identity-unlink-button"
                          onClick={() => onUnlinkExternalIdentity(identity)}
                          disabled={identityUnlinkingKey === identityKey}
                        >
                          {identityUnlinkingKey === identityKey
                            ? tr("team.identity.unlinking" as MessageKey)
                            : tr("team.identity.unlink" as MessageKey)}
                        </button>
                      </div>
                    </div>
                    <div className="otc-stack">
                      <div>
                        <strong>{tr("team.identity.externalSubject" as MessageKey)}:</strong> {identity.external_subject}
                      </div>
                      <div>
                        <strong>{tr("team.identity.emailSnapshot" as MessageKey)}:</strong>{" "}
                        {identity.email_snapshot || tr("common.notAvailable" as MessageKey)}
                      </div>
                      <div>
                        <strong>{tr("team.identity.roleSnapshot" as MessageKey)}:</strong>{" "}
                        {identity.role_snapshot || tr("common.notAvailable" as MessageKey)}
                      </div>
                      <div>
                        <strong>{tr("team.identity.createdAt" as MessageKey)}:</strong> {formatTeamTimestamp(identity.created_at)}
                      </div>
                      <div>
                        <strong>{tr("team.identity.lastSeenLabel" as MessageKey)}:</strong>{" "}
                        {identity.last_seen_at
                          ? formatTeamTimestamp(identity.last_seen_at)
                          : tr("team.identity.lastSeenEmpty" as MessageKey)}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <Message>{tr("team.identity.currentEmpty" as MessageKey)}</Message>
          )}
        </div>
      </Panel>

      <Panel title={tr("team.federatedDirectory.title" as MessageKey)} description={tr("team.federatedDirectory.description" as MessageKey)}>
        <Message tone={selectedMember ? "success" : undefined}>
          {selectedMember
            ? tr("team.federatedDirectory.selectedMember" as MessageKey, { email: selectedMember.email })
            : tr("team.federatedDirectory.selectMemberHint" as MessageKey)}
        </Message>
        {!canManageIdentity ? <Message>{tr("team.federatedDirectory.adminOnly" as MessageKey)}</Message> : null}
        {federatedDirectoryError ? <Message tone="error">{federatedDirectoryError}</Message> : null}
        {federatedDirectoryContextNotice ? (
          <Message tone="success" data-testid="team-federated-context-notice">
            {federatedDirectoryContextNotice === "restored"
              ? tr("team.federatedDirectory.context.restored" as MessageKey)
              : tr("team.federatedDirectory.context.cleared" as MessageKey)}
          </Message>
        ) : null}
        <form className="otc-controls otc-controls--spaced" onSubmit={onSearchFederatedDirectory} data-testid="team-federated-search-form">
          <label className="otc-field">
            {tr("team.federatedDirectory.searchLabel" as MessageKey)}
            <input
              className="otc-input"
              data-testid="team-federated-search-input"
              value={federatedDirectoryQuery}
              onChange={(event) => setFederatedDirectoryQuery(event.target.value)}
              placeholder={tr("team.federatedDirectory.searchPlaceholder" as MessageKey)}
              aria-describedby="team-federated-search-hint"
              disabled={!canManageIdentity}
            />
            <span className="otc-muted" id="team-federated-search-hint" data-testid="team-federated-search-hint">
              {tr("team.federatedDirectory.searchHint" as MessageKey)}
            </span>
          </label>
          <button
            className="otc-button otc-button--accent"
            type="submit"
            data-testid="team-federated-search-button"
            disabled={federatedDirectoryLoading || !canManageIdentity || !federatedDirectoryQueryTrimmed}
          >
            {federatedDirectoryLoading
              ? tr("team.federatedDirectory.searching" as MessageKey)
              : tr("team.federatedDirectory.searchButton" as MessageKey)}
          </button>
          <button
            className="otc-button otc-button--ghost"
            type="button"
            data-testid="team-federated-clear-context-button"
            onClick={resetFederatedDirectoryContext}
            disabled={federatedDirectoryLoading || !canManageIdentity || !hasFederatedDirectoryContext}
            title={tr(
              federatedDirectoryClearRequiresConfirm
                ? ("team.federatedDirectory.clearContextHintWithResults" as MessageKey)
                : ("team.federatedDirectory.clearContextHintLocal" as MessageKey)
            )}
          >
            {tr("team.federatedDirectory.clearContext" as MessageKey)}
          </button>
        </form>

        {federatedDirectoryResults.length ? (
          <div className="otc-stack">
            <MetricGrid>
              <div data-testid="team-federated-summary-total">
                <MetricCard
                  label={tr("team.federatedDirectory.summary.total" as MessageKey)}
                  value={federatedDirectorySummary.total}
                  meta={tr("team.federatedDirectory.summary.totalMeta" as MessageKey)}
                />
              </div>
              <div data-testid="team-federated-summary-ready">
                <MetricCard
                  label={tr("team.federatedDirectory.summary.ready" as MessageKey)}
                  value={federatedDirectorySummary.ready}
                  meta={tr("team.federatedDirectory.summary.readyMeta" as MessageKey)}
                  accent
                />
              </div>
              <div data-testid="team-federated-summary-linked">
                <MetricCard
                  label={tr("team.federatedDirectory.summary.linked" as MessageKey)}
                  value={federatedDirectorySummary.linked}
                  meta={tr("team.federatedDirectory.summary.linkedMeta" as MessageKey)}
                />
              </div>
              <div data-testid="team-federated-summary-review">
                <MetricCard
                  label={tr("team.federatedDirectory.summary.review" as MessageKey)}
                  value={federatedDirectorySummary.review}
                  meta={tr("team.federatedDirectory.summary.reviewMeta" as MessageKey)}
                />
              </div>
            </MetricGrid>

            <div className="otc-controls otc-controls--spaced" data-testid="team-federated-filter-bar">
              <button
                className={federatedDirectoryFilter === "all" ? "otc-button otc-button--accent" : "otc-button otc-button--ghost"}
                type="button"
                data-testid="team-federated-filter-all"
                onClick={() => setFederatedDirectoryFilter("all")}
              >
                {tr("team.federatedDirectory.filters.all" as MessageKey)}
              </button>
              <button
                className={federatedDirectoryFilter === "ready" ? "otc-button otc-button--accent" : "otc-button otc-button--ghost"}
                type="button"
                data-testid="team-federated-filter-ready"
                onClick={() => setFederatedDirectoryFilter("ready")}
              >
                {tr("team.federatedDirectory.filters.ready" as MessageKey)}
              </button>
              <button
                className={federatedDirectoryFilter === "linked" ? "otc-button otc-button--accent" : "otc-button otc-button--ghost"}
                type="button"
                data-testid="team-federated-filter-linked"
                onClick={() => setFederatedDirectoryFilter("linked")}
              >
                {tr("team.federatedDirectory.filters.linked" as MessageKey)}
              </button>
              <button
                className={federatedDirectoryFilter === "review" ? "otc-button otc-button--accent" : "otc-button otc-button--ghost"}
                type="button"
                data-testid="team-federated-filter-review"
                onClick={() => setFederatedDirectoryFilter("review")}
              >
                {tr("team.federatedDirectory.filters.review" as MessageKey)}
              </button>
            </div>

            <div className="otc-controls otc-controls--spaced" data-testid="team-federated-sort-bar">
              <button
                className={federatedDirectorySort === "priority" ? "otc-button otc-button--accent" : "otc-button otc-button--ghost"}
                type="button"
                data-testid="team-federated-sort-priority"
                onClick={() => setFederatedDirectorySort("priority")}
              >
                {tr("team.federatedDirectory.sort.priority" as MessageKey)}
              </button>
              <button
                className={federatedDirectorySort === "alphabetical" ? "otc-button otc-button--accent" : "otc-button otc-button--ghost"}
                type="button"
                data-testid="team-federated-sort-alphabetical"
                onClick={() => setFederatedDirectorySort("alphabetical")}
              >
                {tr("team.federatedDirectory.sort.alphabetical" as MessageKey)}
              </button>
            </div>

            {filteredFederatedDirectoryResults.length ? (
              <table className="otc-table otc-table--spaced" data-testid="team-federated-results-table">
                <thead>
                  <tr>
                    <th>{tr("team.federatedDirectory.table.email" as MessageKey)}</th>
                    <th>{tr("team.federatedDirectory.table.subject" as MessageKey)}</th>
                    <th>{tr("team.federatedDirectory.table.username" as MessageKey)}</th>
                    <th>{tr("team.federatedDirectory.table.org" as MessageKey)}</th>
                    <th>{tr("team.federatedDirectory.table.role" as MessageKey)}</th>
                    <th>{tr("team.federatedDirectory.table.status" as MessageKey)}</th>
                    <th>{tr("team.federatedDirectory.table.match" as MessageKey)}</th>
                    <th>{tr("team.federatedDirectory.table.validation" as MessageKey)}</th>
                    <th>{tr("team.federatedDirectory.table.warnings" as MessageKey)}</th>
                    <th>{tr("team.federatedDirectory.table.actions" as MessageKey)}</th>
                  </tr>
                </thead>
                <tbody>
                  {orderedFederatedDirectoryResults.map((candidate) => {
                    const actionKey = buildFederatedCandidateKey(candidate);
                    const isLinking = federatedDirectoryActionKey === actionKey;
                    const candidateCanLink = isFederatedCandidateLinkable(candidate);
                    return (
                      <tr key={actionKey} data-testid="team-federated-result-row">
                        <td>{candidate.email || tr("common.notAvailable" as MessageKey)}</td>
                        <td>{candidate.external_subject}</td>
                        <td>{candidate.username || tr("common.notAvailable" as MessageKey)}</td>
                        <td>{candidate.organization_id || tr("common.notAvailable" as MessageKey)}</td>
                        <td>{candidate.role_snapshot || tr("common.notAvailable" as MessageKey)}</td>
                        <td>
                          <Pill tone={candidate.enabled ? "success" : "danger"}>
                            {candidate.enabled
                              ? tr("team.federatedDirectory.status.enabled" as MessageKey)
                              : tr("team.federatedDirectory.status.disabled" as MessageKey)}
                          </Pill>
                        </td>
                        <td data-testid="team-federated-match-status-cell">
                          <Pill tone={resolveFederatedMatchTone(candidate.match_status)} data-testid="team-federated-match-status">
                            {resolveFederatedMatchLabel(candidate.match_status)}
                          </Pill>
                        </td>
                        <td data-testid="team-federated-role-validation-cell">
                          <Pill
                            tone={resolveFederatedRoleValidationTone(candidate.role_validation_status)}
                            data-testid="team-federated-role-validation"
                          >
                            {resolveFederatedRoleValidationLabel(candidate.role_validation_status)}
                          </Pill>
                        </td>
                        <td>
                          <div className="otc-stack">
                            {(candidate.warnings || []).length ? (
                              (candidate.warnings || []).slice(0, 3).map((warning) => (
                                <span key={warning} className="otc-muted">
                                  {resolveFederatedWarningLabel(warning)}
                                </span>
                              ))
                            ) : (
                              <span className="otc-muted">{tr("team.federatedDirectory.warnings.none" as MessageKey)}</span>
                            )}
                          </div>
                        </td>
                        <td>
                          <button
                            className="otc-button otc-button--ghost"
                            type="button"
                            data-testid="team-federated-link-button"
                            onClick={() => onLinkFederatedCandidate(candidate)}
                            disabled={!selectedMemberId || !canManageIdentity || isLinking || !candidateCanLink}
                            title={resolveFederatedCandidateActionTitle(candidate)}
                          >
                            {isLinking
                              ? tr("team.federatedDirectory.linking" as MessageKey)
                              : tr("team.federatedDirectory.link" as MessageKey)}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <Message>{tr("team.federatedDirectory.filters.empty" as MessageKey)}</Message>
            )}
          </div>
        ) : federatedDirectoryLoading ? (
          <Message>{t("common.loading")}</Message>
        ) : (
          <Message>{tr("team.federatedDirectory.empty" as MessageKey)}</Message>
        )}
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
          {rosterError ? <Message tone="error" data-testid="team-roster-message">{rosterError}</Message> : null}
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
                <th>{tr("team.roster.table.identity" as MessageKey)}</th>
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
                    <Pill tone={resolveTeamRoleTone(record.role)} data-testid="team-row-role">
                      {formatTeamRoleValue(record.role)}
                    </Pill>
                  </td>
                  <td data-testid="team-row-status">
                    <Pill tone={record.status === "disabled" ? "danger" : record.status === "invited" ? "warning" : undefined}>
                      {tr(`team.roster.status.${record.status}` as MessageKey)}
                    </Pill>
                  </td>
                  <td data-testid="team-row-identity">
                    <div className="otc-stack">
                      <Pill tone={getIdentityState(record) === "linked" ? "success" : "warning"}>
                        {tr(`team.roster.identity.${getIdentityState(record)}` as MessageKey)}
                      </Pill>
                      <div className="otc-muted">
                        {record.last_identity_seen_at
                          ? tr("team.roster.identity.lastSeen" as MessageKey, {
                              value: formatTeamTimestamp(record.last_identity_seen_at)
                            })
                          : tr("team.roster.identity.lastSeenEmpty" as MessageKey)}
                      </div>
                    </div>
                  </td>
                  <td data-testid="team-row-updated">{formatTeamTimestamp(record.updated_at)}</td>
                  <td>
                    <div className="otc-controls">
                      <button className="otc-button otc-button--ghost" type="button" onClick={() => selectMember(record.member_id)}>
                        {tr("team.roster.table.edit" as MessageKey)}
                      </button>
                      <a
                        className="otc-button otc-button--ghost"
                        href={buildIdentityAuditHref(record.member_id)}
                        data-testid="team-row-open-audit"
                      >
                        {tr("team.roster.table.openAudit" as MessageKey)}
                      </a>
                      {canOpenBilling ? (
                        <a className="otc-button otc-button--ghost" href={buildBillingHref(record)}>
                          {tr("team.roster.table.openBilling" as MessageKey)}
                        </a>
                      ) : null}
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
          <Message data-testid="team-roster-message">{t("common.loading")}</Message>
        ) : rosterError ? null : (
          <Message data-testid="team-roster-message">{tr("team.roster.table.empty" as MessageKey)}</Message>
        )}
      </Panel>

      <Panel title={tr("team.about.title" as MessageKey)} description={tr("team.about.description" as MessageKey)}>
        <ul className="otc-list">
          <li>{tr("team.about.point1" as MessageKey)}</li>
          <li>{tr("team.about.point2" as MessageKey)}</li>
          <li>{tr("team.about.point3" as MessageKey)}</li>
        </ul>
      </Panel>
      {confirmDialogConfig ? (
        <ConfirmDialog
          open
          title={confirmDialogConfig.title}
          description={confirmDialogConfig.description}
          confirmLabel={confirmDialogConfig.confirmLabel}
          cancelLabel={confirmDialogConfig.cancelLabel}
          onCancel={() => setConfirmDialogState(null)}
          onConfirm={() => {
            onConfirmDialog().catch(() => undefined);
          }}
          tone={confirmDialogConfig.tone}
          busy={identityUnlinkingKey !== null}
          testId={confirmDialogConfig.testId}
        />
      ) : null}
    </AppShell>
  );
}

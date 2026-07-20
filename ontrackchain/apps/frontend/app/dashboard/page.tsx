import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AppShell, MetricCard, MetricGrid, ModuleCard, ModuleGrid, Panel, Pill } from "../../components/ui";
import { DashboardQuickActions } from "./dashboard-quick-actions";
import { canManageFederatedIdentity, canReadBilling } from "../lib/authz";
import { formatDateTime } from "../lib/date-format";
import { LOCALE_COOKIE_NAME, normalizeLocale, translate, type MessageKey } from "../lib/i18n";
import {
  buildOperationalContextLinks,
  type OperationalContext,
  type OperationalContextLink
} from "../lib/operational-context";

import { ensureHttpUrl } from "../lib/api-url";

type BillingBalanceResponse = {
  credits_available: number;
  credits_reserved: number;
  credits_used_total: number;
};

type Watchlist = {
  id: string;
  name: string;
  priority: string;
};

type OperationsSnapshot = {
  queue: {
    ready: number;
    waiting: number;
    retry_pending: number;
    retry_due: number;
    wake_signals: number;
  };
  concurrency: {
    org_active: number;
    org_limit: number;
    global_active: number;
    global_limit: number;
    plan: string;
  };
  throughput: {
    completed_last_hour: number;
    failed_last_hour: number;
    billing_recalc_last_hour: number;
    avg_duration_ms_last_20: number;
  };
  states: {
    queued: number;
    processing: number;
    dlq_failed: number;
    dlq_resolved: number;
  };
  recent_cases: Array<{
    case_id: string;
    status: string;
    target_address: string;
    target_chain: string;
    created_at: string | null;
    completed_at: string | null;
    queue_state: string | null;
    last_error: string | null;
    attempt_count: number;
    report_type_canonical: string | null;
    charged_cost: number | null;
    duration_ms: number | null;
  }>;
  generated_at: string;
};

type PlatformOperationalAlertsSnapshot = {
  total_count: number;
};

async function validateDashboardRole(token: string, requestId: string): Promise<string | null> {
  const authBaseUrl = ensureHttpUrl(process.env.INTERNAL_AUTH_BASE_URL, "http://auth-service:9000");
  const validateRes = await fetch(`${authBaseUrl}/validate`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });
  if (!validateRes.ok) {
    return null;
  }
  return validateRes.headers.get("X-Role");
}

function buildDashboardOperationalContext(entry: OperationsSnapshot["recent_cases"][number]): OperationalContext {
  return {
    caseId: entry.case_id,
    requestId: entry.case_id,
    reportId: "",
    fileHash: "",
    resourceType: "case",
    resourceId: entry.case_id,
    address: entry.target_address,
    chain: entry.target_chain || "ethereum",
    counterpartyId: "",
    legalName: "",
    documentNumber: "",
    rosId: "",
    reportType: entry.report_type_canonical ?? "",
    blockId: ""
  };
}

function buildDashboardContextLinks(entry: OperationsSnapshot["recent_cases"][number]) {
  const labelKeyByKind: Partial<Record<OperationalContextLink["kind"], MessageKey>> = {
    case: "dashboard.cases.open",
    audit: "dashboard.cases.openAudit",
    evidence: "dashboard.cases.openEvidence",
    reports: "dashboard.cases.openReports",
    sanctions: "dashboard.cases.openSanctions",
    blocks: "dashboard.cases.openBlocks"
  };

  return buildOperationalContextLinks(buildDashboardOperationalContext(entry), {
    includeEvidence: true,
    evidenceDomain: "all"
  })
    .filter(
      (link: OperationalContextLink) =>
        link.kind === "case" ||
        link.kind === "audit" ||
        link.kind === "evidence" ||
        link.kind === "reports" ||
        link.kind === "sanctions" ||
        link.kind === "blocks"
    )
    .map((link: OperationalContextLink) => ({
      ...link,
      labelKey: labelKeyByKind[link.kind] ?? "dashboard.cases.open"
    }));
}

async function fetchJson<T>(input: RequestInfo, init: RequestInit): Promise<{ ok: true; data: T } | { ok: false; status: number }> {
  const res = await fetch(input, init);
  if (!res.ok) {
    return { ok: false, status: res.status };
  }
  const data = (await res.json().catch(() => null)) as T | null;
  if (!data) {
    return { ok: false, status: 502 };
  }
  return { ok: true, data };
}

export default async function DashboardPage() {
  const cookieStore = cookies();
  const token = cookieStore.get("otc_token")?.value;
  const twofa = cookieStore.get("otc_2fa")?.value;
  const locale = normalizeLocale(cookieStore.get(LOCALE_COOKIE_NAME)?.value);
  const t = (key: MessageKey) => translate(locale, key);
  const hasAcceptedSecondFactor =
    twofa === "ok" || twofa === "managed_externally" || twofa === "managed_externally_homologated";

  if (!token || !hasAcceptedSecondFactor) {
    redirect("/login");
  }

  const requestId = crypto.randomUUID();
  const baseUrl = ensureHttpUrl(process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL, "http://traefik");
  const headers = { Authorization: `Bearer ${token}`, "X-Request-Id": requestId };
  const dashboardRole = await validateDashboardRole(token, requestId);
  const showTeamModule = canManageFederatedIdentity(dashboardRole);
  const showBillingQuickAction = canReadBilling(dashboardRole);
  let watchlistsCount: number | null = null;
  let creditsAvailable: number | null = null;
  let creditsReserved: number | null = null;
  let creditsUsedTotal: number | null = null;
  let orgActive: number | null = null;
  let orgLimit: number | null = null;
  let queuedCount: number | null = null;
  let processingCount: number | null = null;
  let firingPendingAlertsTotal: number | null = null;
  let recentCases: OperationsSnapshot["recent_cases"] = [];
  let operationsAvailable = false;

  const [watchlistsRes, billingRes, operationsRes, platformAlertsRes] = await Promise.all([
    fetchJson<Watchlist[]>(`${baseUrl}/api/v1/monitoring/watchlists`, { method: "GET", headers, cache: "no-store" }),
    fetchJson<BillingBalanceResponse>(`${baseUrl}/api/v1/billing/balance`, { method: "GET", headers, cache: "no-store" }),
    fetchJson<OperationsSnapshot>(`${baseUrl}/api/v1/investigation/admin/operations`, { method: "GET", headers, cache: "no-store" }),
    fetchJson<PlatformOperationalAlertsSnapshot>(
      `${baseUrl}/api/v1/monitoring/operational-alerts?status=firing&triage_status=pending&limit=1`,
      { method: "GET", headers, cache: "no-store" }
    )
  ]);

  watchlistsCount = watchlistsRes.ok ? watchlistsRes.data.length : null;
  creditsAvailable = billingRes.ok ? billingRes.data.credits_available : null;
  creditsReserved = billingRes.ok ? billingRes.data.credits_reserved : null;
  creditsUsedTotal = billingRes.ok ? billingRes.data.credits_used_total : null;
  orgActive = operationsRes.ok ? operationsRes.data.concurrency.org_active : null;
  orgLimit = operationsRes.ok ? operationsRes.data.concurrency.org_limit : null;
  queuedCount = operationsRes.ok ? operationsRes.data.states.queued : null;
  processingCount = operationsRes.ok ? operationsRes.data.states.processing : null;
  firingPendingAlertsTotal = platformAlertsRes.ok ? platformAlertsRes.data.total_count : null;
  recentCases = operationsRes.ok ? operationsRes.data.recent_cases.slice(0, 10) : [];
  operationsAvailable = operationsRes.ok;

  return (
    <AppShell
      title={t("dashboard.title")}
      subtitle={t("dashboard.subtitle")}
      activePath="/dashboard"
      actions={<div data-testid="user-menu" className="otc-ghost-pill">{t("dashboard.sessionActive")}</div>}
    >
      <MetricGrid>
        <MetricCard
          label={t("dashboard.kpis.queue")}
          value={queuedCount === null ? t("common.notAvailable") : queuedCount}
          meta={t("dashboard.kpis.queueMeta")}
        />
        <MetricCard
          label={t("dashboard.kpis.processing")}
          value={processingCount === null ? t("common.notAvailable") : processingCount}
          meta={t("dashboard.kpis.processingMeta")}
        />
        <MetricCard
          label={t("dashboard.kpis.orgConcurrency")}
          value={orgActive === null || orgLimit === null ? t("common.notAvailable") : `${orgActive} / ${orgLimit}`}
          meta={t("dashboard.kpis.orgConcurrencyMeta")}
          accent
        />
        <MetricCard
          label={t("dashboard.kpis.watchlists")}
          value={watchlistsCount === null ? t("common.notAvailable") : watchlistsCount}
          meta={t("dashboard.kpis.watchlistsMeta")}
        />
      </MetricGrid>

      <MetricGrid>
        <MetricCard
          label={t("dashboard.kpis.alertsFiring")}
          value={firingPendingAlertsTotal === null ? t("common.notAvailable") : firingPendingAlertsTotal}
          meta={t("dashboard.kpis.alertsFiringMeta")}
          accent
        />
        <MetricCard
          label={t("dashboard.kpis.credits")}
          value={creditsAvailable === null ? t("common.notAvailable") : String(creditsAvailable)}
          meta={t("dashboard.kpis.creditsMeta")}
        />
        <MetricCard
          label={t("dashboard.kpis.creditsReserved")}
          value={creditsReserved === null ? t("common.notAvailable") : String(creditsReserved)}
          meta={t("dashboard.kpis.creditsReservedMeta")}
        />
        <MetricCard
          label={t("dashboard.kpis.creditsUsed")}
          value={creditsUsedTotal === null ? t("common.notAvailable") : String(creditsUsedTotal)}
          meta={t("dashboard.kpis.creditsUsedMeta")}
        />
      </MetricGrid>

      <Panel title={t("dashboard.quickActions.title")} description={t("dashboard.quickActions.description")}>
        <DashboardQuickActions showBillingLink={showBillingQuickAction} showTeamLink={showTeamModule} />
      </Panel>

      <Panel title={t("dashboard.cases.title")} description={t("dashboard.cases.description")}>
        <table className="otc-table">
          <thead>
            <tr>
              <th>{t("dashboard.cases.caseId")}</th>
              <th>{t("dashboard.cases.reportType")}</th>
              <th>{t("dashboard.cases.status")}</th>
              <th>{t("dashboard.cases.chain")}</th>
              <th>{t("dashboard.cases.createdAt")}</th>
              <th>{t("dashboard.cases.completedAt")}</th>
              <th>{t("dashboard.cases.cost")}</th>
              <th>{t("dashboard.cases.actions")}</th>
            </tr>
          </thead>
          <tbody>
            {recentCases.length ? (
              recentCases.map((entry) => (
                <tr key={entry.case_id} data-testid={`dashboard-case-row-${entry.case_id}`}>
                  <td>
                    <strong>{entry.case_id}</strong>
                    {entry.last_error ? <div className="otc-muted">{entry.last_error}</div> : null}
                  </td>
                  <td>{entry.report_type_canonical ?? t("common.notAvailable")}</td>
                  <td data-testid={`dashboard-case-status-${entry.case_id}`}>{entry.status}</td>
                  <td>{entry.target_chain}</td>
                  <td data-testid={`dashboard-case-created-at-${entry.case_id}`}>
                    {formatDateTime(entry.created_at, locale) ?? t("common.notAvailable")}
                  </td>
                  <td data-testid={`dashboard-case-completed-at-${entry.case_id}`}>
                    {formatDateTime(entry.completed_at, locale) ?? t("common.notAvailable")}
                  </td>
                  <td>{typeof entry.charged_cost === "number" ? entry.charged_cost : t("common.notAvailable")}</td>
                  <td>
                    <div className="otc-controls">
                      {buildDashboardContextLinks(entry).map((link: OperationalContextLink & { labelKey: MessageKey }) => (
                        <a key={`${entry.case_id}-${link.testIdSuffix}`} className="otc-link-button" href={link.href}>
                          {t(link.labelKey)}
                        </a>
                      ))}
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={8} className="otc-muted">
                  {operationsAvailable ? t("dashboard.cases.empty") : t("dashboard.cases.unavailable")}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Panel>

      <Panel title={t("dashboard.modules.title")} description={t("dashboard.modules.description")}>
        <ModuleGrid>
          <ModuleCard
            href="/monitoring"
            title={t("dashboard.modules.watchlists.title")}
            description={t("dashboard.modules.watchlists.description")}
            badge={<Pill>{t("dashboard.modules.active")}</Pill>}
            footer={t("dashboard.modules.watchlists.footer")}
          />
          <ModuleCard
            href="/audit"
            title={t("dashboard.modules.risk.title")}
            description={t("dashboard.modules.risk.description")}
            badge={<Pill>{t("dashboard.modules.active")}</Pill>}
            footer={t("dashboard.modules.risk.footer")}
          />
          <ModuleCard
            href="/investigate"
            title={t("dashboard.modules.dueDiligence.title")}
            description={t("dashboard.modules.dueDiligence.description")}
            badge={<Pill>{t("dashboard.modules.active")}</Pill>}
            footer={t("dashboard.modules.dueDiligence.footer")}
          />
          <ModuleCard
            href="/counterparties"
            title={t("dashboard.modules.counterparties.title")}
            description={t("dashboard.modules.counterparties.description")}
            badge={<Pill>{t("dashboard.modules.active")}</Pill>}
            footer={t("dashboard.modules.counterparties.footer")}
          />
          <ModuleCard
            href="/sanctions"
            title={t("dashboard.modules.sanctions.title")}
            description={t("dashboard.modules.sanctions.description")}
            badge={<Pill>{t("dashboard.modules.active")}</Pill>}
            footer={t("dashboard.modules.sanctions.footer")}
          />
          <ModuleCard
            href="/blocks"
            title={t("dashboard.modules.blocks.title")}
            description={t("dashboard.modules.blocks.description")}
            badge={<Pill>{t("dashboard.modules.active")}</Pill>}
            footer={t("dashboard.modules.blocks.footer")}
          />
          <ModuleCard
            href="/evidence"
            title={t("dashboard.modules.evidence.title")}
            description={t("dashboard.modules.evidence.description")}
            badge={<Pill>{t("dashboard.modules.active")}</Pill>}
            footer={t("dashboard.modules.evidence.footer")}
          />
          <ModuleCard
            href="/alerts"
            title={t("dashboard.modules.alerts.title")}
            description={t("dashboard.modules.alerts.description")}
            badge={<Pill>{t("dashboard.modules.active")}</Pill>}
            footer={t("dashboard.modules.alerts.footer")}
          />
          <ModuleCard
            title={t("dashboard.modules.reports.title")}
            description={t("dashboard.modules.reports.description")}
            href="/reports"
            badge={<Pill>{t("dashboard.modules.active")}</Pill>}
            footer={t("dashboard.modules.reports.footer")}
          />
          {showTeamModule ? (
            <ModuleCard
              href="/team"
              testId="dashboard-module-team"
              title={t("dashboard.modules.team.title")}
              description={t("dashboard.modules.team.description")}
              badge={<Pill>{t("dashboard.modules.active")}</Pill>}
              footer={t("dashboard.modules.team.footer")}
            />
          ) : null}
        </ModuleGrid>
      </Panel>
    </AppShell>
  );
}

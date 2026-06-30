import { cookies } from "next/headers";
import { isConfiguredDevAuthButDisabled, resolveEffectiveAuthMode } from "./lib/auth-runtime";
import { AppShell, CodeBlock, MetricCard, MetricGrid, ModuleCard, ModuleGrid, Panel, Pill } from "../components/ui";
import { LOCALE_COOKIE_NAME, normalizeLocale, translate, type MessageKey } from "./lib/i18n";

type CatalogItem = {
  canonical: string;
  label: string;
  description: string;
  cost_credits: number;
  available: boolean;
  upgrade_required: string | null;
  min_plan: string;
  aliases_accepted: string[];
  deprecated_aliases: string[];
  chains_supported: string[];
  avg_duration_seconds: number;
  output_format: string;
  regulatory_reference: string | null;
  tags: string[];
};

type ReportTypeCatalogResponse = {
  plan: string;
  total: number;
  generated_at: string;
  types: CatalogItem[];
  note_deprecated: string;
};

type OperationCatalogResponse = {
  plan: string;
  total: number;
  generated_at: string;
  operations: CatalogItem[];
  note_deprecated: string;
};

type DashboardBundle = {
  reportTypes: ReportTypeCatalogResponse | null;
  complianceOperations: OperationCatalogResponse | null;
  monitoringOperations: OperationCatalogResponse | null;
};

async function fetchAuthorizedJson<T>(path: string, token: string): Promise<T | null> {
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik:8080";
  const res = await fetch(`${baseUrl}${path}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  if (!res.ok) return null;
  return (await res.json()) as T;
}

async function fetchReportTypes(token: string): Promise<ReportTypeCatalogResponse | null> {
  return fetchAuthorizedJson<ReportTypeCatalogResponse>("/api/v1/report-types?include_unavailable=true&include_deprecated=true", token);
}

async function fetchComplianceOperations(token: string): Promise<OperationCatalogResponse | null> {
  return fetchAuthorizedJson<OperationCatalogResponse>("/api/v1/compliance/operations?include_unavailable=true&include_deprecated=true", token);
}

async function fetchMonitoringOperations(token: string): Promise<OperationCatalogResponse | null> {
  return fetchAuthorizedJson<OperationCatalogResponse>("/api/v1/monitoring/operations?include_unavailable=true&include_deprecated=true", token);
}

async function fetchDashboardBundle(token: string): Promise<DashboardBundle> {
  const [reportTypes, complianceOperations, monitoringOperations] = await Promise.all([
    fetchReportTypes(token),
    fetchComplianceOperations(token),
    fetchMonitoringOperations(token)
  ]);

  return {
    reportTypes,
    complianceOperations,
    monitoringOperations
  };
}

function renderCatalogSection(title: string, items: CatalogItem[], description: string, emptyMessage: string) {
  return (
    <Panel title={title} description={description}>
      {items.length > 0 ? <CodeBlock>{JSON.stringify(items, null, 2)}</CodeBlock> : <div className="otc-message">{emptyMessage}</div>}
    </Panel>
  );
}

export default async function Home() {
  const cookieStore = cookies();
  const locale = normalizeLocale(cookieStore.get(LOCALE_COOKIE_NAME)?.value);
  const t = (key: MessageKey, values?: Record<string, string | number>) => translate(locale, key, values);
  const authMode = resolveEffectiveAuthMode();
  const devAuthDisabled = isConfiguredDevAuthButDisabled();
  const sessionToken = cookieStore.get("otc_token")?.value?.trim() ?? "";
  const authenticated = sessionToken.length > 0;
  const sessionBundle = authenticated
    ? await fetchDashboardBundle(sessionToken)
    : {
        reportTypes: null,
        complianceOperations: null,
        monitoringOperations: null
      };

  const availableReports = sessionBundle.reportTypes?.types.filter((item) => item.available) ?? [];
  const availableCompliance = sessionBundle.complianceOperations?.operations.filter((item) => item.available) ?? [];
  const availableMonitoring = sessionBundle.monitoringOperations?.operations.filter((item) => item.available) ?? [];
  const availableOperationCount = availableCompliance.length + availableMonitoring.length;

  return (
    <AppShell
      title={t("home.title")}
      subtitle={t("home.subtitle")}
      activePath="/dashboard"
      actions={<a href="/dashboard" className="otc-link-button">{t("home.openDashboard")}</a>}
    >
      <MetricGrid>
        <MetricCard label={t("home.stats.authMode")} value={authMode.toUpperCase()} meta={devAuthDisabled ? t("home.stats.authMetaDevBlocked") : t("home.stats.authMetaEffective")} />
        <MetricCard
          label={t("home.stats.session")}
          value={authenticated ? t("home.stats.sessionConnectedValue") : t("home.stats.sessionAnonymousValue")}
          meta={authenticated ? t("home.stats.sessionMetaAuthenticated") : t("home.stats.sessionMetaAnonymous")}
        />
        <MetricCard label={t("home.stats.catalogTypes")} value={authenticated ? availableReports.length : "--"} meta={t("home.stats.catalogTypesMeta")} />
        <MetricCard label={t("home.stats.catalogOps")} value={authenticated ? availableOperationCount : "--"} meta={t("home.stats.catalogOpsMeta")} accent />
      </MetricGrid>

      <Panel title={t("home.summary.title")} description={t("home.summary.description")}>
        <ModuleGrid>
          <ModuleCard href="/dashboard" title={t("home.summary.panel")} description={t("home.summary.panelDesc")} badge={<Pill>{t("dashboard.modules.active")}</Pill>} />
          <ModuleCard href="/investigate" title={t("home.summary.investigations")} description={t("home.summary.investigationsDesc")} badge={<Pill>{t("dashboard.modules.active")}</Pill>} />
          <ModuleCard href="/monitoring" title={t("home.summary.monitoring")} description={t("home.summary.monitoringDesc")} badge={<Pill>{t("dashboard.modules.active")}</Pill>} />
          <ModuleCard href="/audit" title={t("home.summary.audit")} description={t("home.summary.auditDesc")} badge={<Pill>{t("dashboard.modules.active")}</Pill>} />
        </ModuleGrid>
      </Panel>

      <Panel title={t("home.session.title")} description={t("home.session.description")}>
        <div className="otc-message">{authenticated ? t("home.session.authenticated") : t("home.session.loginRequired")}</div>
      </Panel>

      {!authenticated ? (
        <Panel title={t("home.authNotice.title")} description={t("home.authNotice.description")}>
          <div className="otc-message">
            {devAuthDisabled ? t("home.authNotice.devBlocked") : t("home.authNotice.loginRequired")}
          </div>
        </Panel>
      ) : null}

      {renderCatalogSection(
        t("home.catalog.reports"),
        availableReports,
        t("home.catalog.authenticatedDescription"),
        t("home.catalog.empty")
      )}
      {renderCatalogSection(
        t("home.catalog.compliance"),
        availableCompliance,
        t("home.catalog.authenticatedDescription"),
        t("home.catalog.empty")
      )}
      {renderCatalogSection(
        t("home.catalog.monitoring"),
        availableMonitoring,
        t("home.catalog.authenticatedDescription"),
        t("home.catalog.empty")
      )}

      <Panel title={t("home.flow.title")} description={t("home.flow.description")}>
        <CodeBlock>
          {JSON.stringify(
            {
              compliance: [
                "GET /api/v1/compliance/operations",
                "POST /api/v1/compliance/estimate",
                "POST /api/v1/compliance/start",
                "POST /api/v1/compliance/cases/{case_id}/report"
              ],
              monitoring: [
                "GET /api/v1/monitoring/operations",
                "POST /api/v1/monitoring/estimate",
                "POST /api/v1/monitoring/start"
              ]
            },
            null,
            2
          )}
        </CodeBlock>
      </Panel>
    </AppShell>
  );
}

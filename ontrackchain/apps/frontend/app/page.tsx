import { cookies } from "next/headers";
import { isConfiguredDevAuthButDisabled, isFrontendStandaloneShowcaseMode, resolveEffectiveAuthMode } from "./lib/auth-runtime";
import { STANDALONE_SHOWCASE_HOME_CATALOGS } from "./lib/standalone-showcase";
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
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
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
  const standaloneShowcaseMode = isFrontendStandaloneShowcaseMode();
  const sessionToken = cookieStore.get("otc_token")?.value?.trim() ?? "";
  const authenticated = standaloneShowcaseMode || sessionToken.length > 0;
  const sessionBundle = standaloneShowcaseMode
    ? STANDALONE_SHOWCASE_HOME_CATALOGS
    : authenticated
    ? await fetchDashboardBundle(sessionToken)
    : {
        reportTypes: null,
        complianceOperations: null,
        monitoringOperations: null
      };

  const reportCatalog = sessionBundle.reportTypes as ReportTypeCatalogResponse | null;
  const complianceCatalog = sessionBundle.complianceOperations as OperationCatalogResponse | null;
  const monitoringCatalog = sessionBundle.monitoringOperations as OperationCatalogResponse | null;

  const availableReports = reportCatalog?.types.filter((item: CatalogItem) => item.available) ?? [];
  const availableCompliance = complianceCatalog?.operations.filter((item: CatalogItem) => item.available) ?? [];
  const availableMonitoring = monitoringCatalog?.operations.filter((item: CatalogItem) => item.available) ?? [];
  const availableOperationCount = availableCompliance.length + availableMonitoring.length;

  return (
    <AppShell
      title={t("home.title")}
      subtitle={t("home.subtitle")}
      activePath="/dashboard"
      actions={standaloneShowcaseMode ? <Pill tone="warning">{t("home.demo.badge" as MessageKey)}</Pill> : <a href="/dashboard" className="otc-link-button">{t("home.openDashboard")}</a>}
    >
      {standaloneShowcaseMode ? (
        <Panel title={t("home.demo.title" as MessageKey)} description={t("home.demo.description" as MessageKey)}>
          <div className="otc-message">{t("home.demo.notice" as MessageKey)}</div>
        </Panel>
      ) : null}
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
          <ModuleCard href="/dashboard" title={t("home.summary.panel")} description={t("home.summary.panelDesc")} badge={<Pill>{standaloneShowcaseMode ? t("home.demo.badge" as MessageKey) : t("dashboard.modules.active")}</Pill>} />
          <ModuleCard href="/investigate" title={t("home.summary.investigations")} description={t("home.summary.investigationsDesc")} badge={<Pill>{standaloneShowcaseMode ? t("home.demo.badge" as MessageKey) : t("dashboard.modules.active")}</Pill>} />
          <ModuleCard href="/monitoring" title={t("home.summary.monitoring")} description={t("home.summary.monitoringDesc")} badge={<Pill>{standaloneShowcaseMode ? t("home.demo.badge" as MessageKey) : t("dashboard.modules.active")}</Pill>} />
          <ModuleCard href="/audit" title={t("home.summary.audit")} description={t("home.summary.auditDesc")} badge={<Pill>{standaloneShowcaseMode ? t("home.demo.badge" as MessageKey) : t("dashboard.modules.active")}</Pill>} />
        </ModuleGrid>
      </Panel>

      <Panel title={t("home.session.title")} description={t("home.session.description")}>
        <div className="otc-message">{authenticated ? t("home.session.authenticated") : t("home.session.loginRequired")}</div>
      </Panel>

      {!authenticated ? (
        <Panel title={t("home.authNotice.title")} description={t("home.authNotice.description")}>
          <div className="otc-message">
            {standaloneShowcaseMode ? t("home.demo.authBlocked" as MessageKey) : devAuthDisabled ? t("home.authNotice.devBlocked") : t("home.authNotice.loginRequired")}
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

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AppShell, MetricCard, MetricGrid, ModuleCard, ModuleGrid, Panel, Pill } from "../../components/ui";
import { LOCALE_COOKIE_NAME, normalizeLocale, translate, type MessageKey } from "../lib/i18n";

export default function DashboardPage() {
  const cookieStore = cookies();
  const token = cookieStore.get("otc_token")?.value;
  const twofa = cookieStore.get("otc_2fa")?.value;
  const locale = normalizeLocale(cookieStore.get(LOCALE_COOKIE_NAME)?.value);
  const t = (key: MessageKey) => translate(locale, key);

  if (!token || twofa !== "ok") {
    redirect("/login");
  }

  return (
    <AppShell
      title={t("dashboard.title")}
      subtitle={t("dashboard.subtitle")}
      activePath="/dashboard"
      actions={<div data-testid="user-menu" className="otc-ghost-pill">{t("dashboard.sessionActive")}</div>}
    >
      <MetricGrid>
        <MetricCard label={t("dashboard.stats.researches")} value="90" meta={t("dashboard.stats.researchesMeta")} />
        <MetricCard label={t("dashboard.stats.activeAnalysts")} value="2 / 3" meta={t("dashboard.stats.activeAnalystsMeta")} />
        <MetricCard label={t("dashboard.stats.monitoredWallets")} value="2" meta={t("dashboard.stats.monitoredWalletsMeta")} />
        <MetricCard label={t("dashboard.stats.avgScore")} value="24 / 100" meta={t("dashboard.stats.avgScoreMeta")} accent />
      </MetricGrid>

      <Panel title={t("dashboard.history.title")} description={t("dashboard.history.description")}>
        <table className="otc-table">
          <thead>
            <tr>
              <th>{t("dashboard.history.user")}</th>
              <th>{t("dashboard.history.role")}</th>
              <th>{t("dashboard.history.researches")}</th>
              <th>{t("dashboard.history.status")}</th>
              <th>{t("dashboard.history.score")}</th>
              <th>{t("dashboard.history.network")}</th>
              <th>{t("dashboard.history.lastResearch")}</th>
              <th>{t("dashboard.history.actions")}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>
                <strong>System User</strong>
                <div className="otc-muted">system@ontrackchain.com</div>
              </td>
              <td>{t("dashboard.history.admin")}</td>
              <td>
                <strong>88</strong>
              </td>
              <td>
                <span style={{ color: "#7ff0c2" }}>74 ok</span> • <span style={{ color: "#ff9daa" }}>14 fail</span>
              </td>
              <td>
                <strong style={{ color: "#7ff0ff" }}>13 / 100</strong>
              </td>
              <td>ETHEREUM</td>
              <td>18/06/2026, 00:01</td>
              <td>
                <a className="otc-link-button" href="/audit">
                  {t("dashboard.history.view")}
                </a>
              </td>
            </tr>
            <tr>
              <td>
                <strong>KMD</strong>
                <div className="otc-muted">kmd@ontrackchain.com</div>
              </td>
              <td>{t("dashboard.history.tester")}</td>
              <td>
                <strong>2</strong>
              </td>
              <td>
                <span style={{ color: "#7ff0c2" }}>2 ok</span>
              </td>
              <td>
                <strong style={{ color: "#7ff0ff" }}>35 / 70</strong>
              </td>
              <td>BITCOIN</td>
              <td>18/06/2026, 15:38</td>
              <td>
                <a className="otc-link-button" href="/audit">
                  {t("dashboard.history.view")}
                </a>
              </td>
            </tr>
            <tr>
              <td>
                <strong>JIBSO</strong>
                <div className="otc-muted">jibso@ontrackchain.com</div>
              </td>
              <td>{t("dashboard.history.admin")}</td>
              <td>0</td>
              <td>--</td>
              <td>-- / --</td>
              <td>--</td>
              <td>--</td>
              <td className="otc-muted">{t("dashboard.history.noRecords")}</td>
            </tr>
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
            title={t("dashboard.modules.counterparties.title")}
            description={t("dashboard.modules.counterparties.description")}
            badge={<Pill tone="warning">{t("dashboard.modules.soon")}</Pill>}
            footer={t("dashboard.modules.counterparties.footer")}
          />
          <ModuleCard
            title={t("dashboard.modules.sanctions.title")}
            description={t("dashboard.modules.sanctions.description")}
            badge={<Pill tone="warning">{t("dashboard.modules.soon")}</Pill>}
            footer={t("dashboard.modules.sanctions.footer")}
          />
          <ModuleCard
            title={t("dashboard.modules.evidence.title")}
            description={t("dashboard.modules.evidence.description")}
            badge={<Pill tone="warning">{t("dashboard.modules.soon")}</Pill>}
            footer={t("dashboard.modules.evidence.footer")}
          />
          <ModuleCard
            title={t("dashboard.modules.alerts.title")}
            description={t("dashboard.modules.alerts.description")}
            badge={<Pill tone="warning">{t("dashboard.modules.soon")}</Pill>}
            footer={t("dashboard.modules.alerts.footer")}
          />
          <ModuleCard
            title={t("dashboard.modules.reports.title")}
            description={t("dashboard.modules.reports.description")}
            badge={<Pill tone="warning">{t("dashboard.modules.soon")}</Pill>}
            footer={t("dashboard.modules.reports.footer")}
          />
          <ModuleCard
            href="/billing"
            title={t("dashboard.modules.team.title")}
            description={t("dashboard.modules.team.description")}
            badge={<Pill tone="warning">{t("dashboard.modules.soon")}</Pill>}
            footer={t("dashboard.modules.team.footer")}
          />
        </ModuleGrid>
      </Panel>
    </AppShell>
  );
}

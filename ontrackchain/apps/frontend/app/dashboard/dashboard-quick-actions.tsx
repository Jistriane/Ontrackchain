"use client";

import { useI18n } from "../../components/i18n-provider";

type DashboardQuickActionsProps = {
  showBillingLink: boolean;
  showTeamLink: boolean;
};

export function DashboardQuickActions({ showBillingLink, showTeamLink }: DashboardQuickActionsProps) {
  const { t } = useI18n();

  return (
    <div className="otc-controls">
      <a className="otc-link-button" href="/alerts?status=firing&triage_status=pending">
        {t("dashboard.quickActions.openPendingAlerts")}
      </a>
      <a className="otc-link-button" href="/monitoring">
        {t("dashboard.quickActions.openMonitoring")}
      </a>
      <a className="otc-link-button" href="/reports">
        {t("dashboard.quickActions.openReports")}
      </a>
      <a className="otc-link-button" href="/evidence">
        {t("dashboard.quickActions.openEvidence")}
      </a>
      {showBillingLink ? (
        <a className="otc-link-button" href="/billing" data-testid="dashboard-quick-action-billing">
          {t("dashboard.quickActions.openBilling")}
        </a>
      ) : null}
      {showTeamLink ? (
        <a className="otc-link-button" href="/team" data-testid="dashboard-quick-action-team">
          {t("dashboard.quickActions.openTeam")}
        </a>
      ) : null}
    </div>
  );
}

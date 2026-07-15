"use client";

import { useEffect, useMemo, useState } from "react";
import { useI18n } from "../../components/i18n-provider";
import { canManageFederatedIdentity, canReadBilling } from "../lib/authz";
import { fetchAuthContext, type AuthContext } from "../lib/ownership";

export function DashboardQuickActions() {
  const { t } = useI18n();
  const [authContext, setAuthContext] = useState<AuthContext | null | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;

    fetchAuthContext()
      .then((context) => {
        if (!cancelled) {
          setAuthContext(context);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAuthContext(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const showBillingLink = useMemo(() => {
    if (authContext === undefined) {
      return false;
    }
    return canReadBilling(authContext?.role);
  }, [authContext]);
  const showTeamLink = useMemo(() => {
    if (authContext === undefined) {
      return false;
    }
    return canManageFederatedIdentity(authContext?.role);
  }, [authContext]);

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

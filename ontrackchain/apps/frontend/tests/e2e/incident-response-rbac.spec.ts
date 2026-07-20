import { expect, test, type Page, type Route } from "@playwright/test";

import { seedFrontendAuth } from "./seed-frontend-auth";

async function seedIncidentResponsePage(page: Page, role: string) {
  await seedFrontendAuth(page, { role });

  await page.route("**/api/app/investigation/operations", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        queue: { ready: 0, waiting: 0, retry_pending: 0, retry_due: 0, wake_signals: 0 },
        concurrency: { org_active: 0, org_limit: 0, global_active: 0, global_limit: 0, plan: "professional" },
        throughput: { completed_last_hour: 0, failed_last_hour: 0, billing_recalc_last_hour: 0, avg_duration_ms_last_20: 0 },
        states: { queued: 0, processing: 0, dlq_failed: 0, dlq_resolved: 0 },
        recent_cases: [],
        security: {
          manual_package_mfa_violations_last_hour: 0,
          manual_package_mfa_2fa_required_last_hour: 0,
          manual_package_mfa_provider_not_homologated_last_hour: 0
        },
        generated_at: "2026-07-14T12:00:00Z"
      })
    });
  });

  await page.route("**/api/app/investigation/alerts", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        generated_at: "2026-07-14T12:00:00Z",
        open_total: 2,
        critical_open_total: 1,
        alerts: [
          {
            code: "worker-critical-1",
            severity: "critical",
            status: "open",
            metric: "queue_lag",
            value: 12,
            threshold: 5,
            title: "Worker critical",
            message: "Queue lag critical",
            recommended_action: "Scale workers"
          },
          {
            code: "worker-warning-1",
            severity: "warning",
            status: "open",
            metric: "retry_rate",
            value: 4,
            threshold: 2,
            title: "Worker warning",
            message: "Retry rate warning",
            recommended_action: "Inspect downstream RPC"
          }
        ]
      })
    });
  });

  await page.route("**/api/app/investigation/metrics", async (route: Route) => {
    await route.fulfill({ status: 200, contentType: "text/plain", body: "metrics_ok 1" });
  });

  await page.route("**/api/app/investigation/dlq?**", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        count: 1,
        credits_available: 120,
        filters: { state: "failed_permanent", target_chain: null, can_requeue: false, limit: 50 },
        cases: [
          {
            case_id: "case-dlq-1",
            target_chain: "ethereum",
            report_type_canonical: "technical_basic",
            attempt_count: 3,
            max_attempts: 3,
            credits_estimated: 12,
            dlq_requeue_count: 1,
            dlq_state: "failed_permanent",
            failure_reason: "rpc_timeout",
            dlq_failed_at: "2026-07-14T12:00:00Z",
            completed_at: null,
            dlq_acknowledged_at: null,
            dlq_acknowledged_by: null,
            dlq_resolution_note: null,
            can_requeue: true
          }
        ],
        generated_at: "2026-07-14T12:00:00Z"
      })
    });
  });
}

test.describe("incident response RBAC", () => {
  test("analyst recebe negação preventiva no cockpit dedicado", async ({ page }) => {
    await seedIncidentResponsePage(page, "ANALYST");
    await page.goto("/incident-response");

    await expect(page.locator('aside a[href="/incident-response"]')).toHaveCount(0);
    await expect(page.getByTestId("monitoring-worker-read-restricted")).toContainText(
      "Os painéis administrativos de investigation estão ocultos nesta sessão porque a role atual não possui leitura privilegiada ADMIN/AUDITOR."
    );
    await expect(page.getByTestId("dlq-read-restricted")).toContainText(
      "A remediação administrativa da DLQ está oculta nesta sessão porque a role atual não possui leitura privilegiada ADMIN/AUDITOR."
    );
    await expect(page.getByTestId("dlq-requeue-btn-case-dlq-1")).toHaveCount(0);
  });

  test("auditor recebe negação semântica tardia nas superfícies de investigation em vez de snapshot vazio", async ({ page }) => {
    await seedIncidentResponsePage(page, "AUDITOR");

    await page.route("**/api/app/investigation/operations", async (route: Route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "not_authenticated" })
      });
    });

    await page.route("**/api/app/investigation/alerts", async (route: Route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "not_authenticated" })
      });
    });

    await page.route("**/api/app/investigation/metrics", async (route: Route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "not_authenticated" })
      });
    });

    await page.goto("/incident-response");

    await expect(page.getByText("Sua sessão expirou ou não foi autenticada.")).toBeVisible();
    await expect(page.getByTestId("worker-metric-ready")).toHaveCount(0);
    await expect(page.getByTestId("worker-operational-alert")).toHaveCount(0);
    await expect(page.getByTestId("worker-metrics-preview")).toHaveCount(0);
  });

  test("auditor recebe leitura privilegiada read-only sem mutações administrativas de DLQ", async ({ page }) => {
    await seedIncidentResponsePage(page, "AUDITOR");
    await page.goto("/incident-response");

    await expect(page.locator('aside a[href="/incident-response"]')).toHaveCount(1);
    await expect(page.getByTestId("worker-generated-at")).toContainText("snapshot:");
    await expect(page.getByTestId("dlq-case-row")).toHaveCount(1);
    await expect(page.getByTestId("dlq-mutation-restricted")).toContainText(
      "As mutações administrativas da DLQ estão ocultas nesta sessão porque a role atual não possui papel administrativo ADMIN."
    );
    await expect(page.getByTestId("dlq-requeue-btn-case-dlq-1")).toHaveCount(0);
    await expect(page.getByTestId("dlq-ack-btn-case-dlq-1")).toHaveCount(0);
    await expect(page.getByTestId("dlq-discard-btn-case-dlq-1")).toHaveCount(0);
  });

  test("handoff vindo de alerts destaca o contexto e filtra alertas operacionais por severidade", async ({ page }) => {
    await seedIncidentResponsePage(page, "AUDITOR");
    await page.goto("/incident-response?alertId=alert-rbac-01&alertName=Alert%20RBAC&severity=critical");

    await expect(page.getByTestId("incident-response-handoff-context")).toContainText("alert_id=alert-rbac-01");
    await expect(page.getByTestId("incident-response-open-alerts")).toHaveAttribute(
      "href",
      "/alerts?alertId=alert-rbac-01&alertName=Alert%20RBAC&severity=critical"
    );
    await expect(page.getByTestId("worker-operational-alert-handoff")).toContainText("Alert RBAC");
    await expect(page.getByTestId("worker-operational-alert-worker-critical-1")).toBeVisible();
    await expect(page.getByTestId("worker-operational-alert-worker-warning-1")).toHaveCount(0);
  });
});

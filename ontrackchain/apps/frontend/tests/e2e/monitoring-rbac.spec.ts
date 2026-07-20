import { expect, test, type Page, type Route } from "@playwright/test";

import { seedFrontendAuth } from "./seed-frontend-auth";

async function seedMonitoringPage(page: Page, role: string) {
  const calls = {
    watchlists: 0,
    watchlistItems: 0,
    alerts: 0
  };

  await seedFrontendAuth(page, { role });

  await page.route("**/api/app/monitoring/watchlists", async (route: Route) => {
    calls.watchlists += 1;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        data: [{ id: "watchlist-1", name: "VIP Wallets", priority: "high" }]
      })
    });
  });

  await page.route("**/api/app/monitoring/watchlists/watchlist-1/items?limit=20", async (route: Route) => {
    calls.watchlistItems += 1;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        data: [{ id: "item-1", watchlist_id: "watchlist-1", address: "0xabc", chain: "ethereum", created_at: "2026-07-14T12:00:00Z" }]
      })
    });
  });

  await page.route("**/api/app/monitoring/alerts?**", async (route: Route) => {
    calls.alerts += 1;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ data: [] })
    });
  });

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
        open_total: 0,
        critical_open_total: 0,
        alerts: []
      })
    });
  });

  await page.route("**/api/app/monitoring/operational-alert-filter-options", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ services: [], receivers: [], severities: [] })
    });
  });

  await page.route("**/api/app/monitoring/operational-alerts?**", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        data: [
          {
            id: "platform-alert-1",
            alertname: "QueueBacklogHigh",
            severity: "critical",
            status: "firing",
            triage_status: "pending",
            receiver: "platform-oncall",
            service: "investigation-worker",
            delivery_count: 2,
            first_received_at: "2026-07-14T12:00:00Z",
            last_received_at: "2026-07-14T12:05:00Z",
            resolved_at: null,
            triaged_at: null,
            triaged_by: null,
            triage_note: null,
            annotations: { summary: "Backlog alto", description: "Fila acima do limiar" },
            labels: { severity: "critical", queue: "investigation" }
          }
        ],
        count: 1,
        total_count: 1,
        limit: 50,
        has_more: false,
        next_cursor: null
      })
    });
  });

  await page.route("**/api/app/operations/work-items?module=alerts&resource_type=operational_alert&limit=100", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ data: [] })
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

  await page.route("**/api/app/monitoring/trigger-alert", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ alert_id: "alert-1", status: "created" })
    });
  });

  return calls;
}

test.describe("monitoring RBAC", () => {
  test("analyst nao recebe superficies administrativas privilegiadas", async ({ page }) => {
    await seedMonitoringPage(page, "ANALYST");
    await page.goto("/monitoring");

    await expect(page.locator('[data-testid="watchlist-item"]')).toBeVisible();
    await expect(page.locator('[data-testid="trigger-alert-btn"]')).toHaveCount(0);
    await expect(page.getByTestId("monitoring-incident-response-restricted")).toContainText(
      "A resposta a incidentes dedicada está oculta nesta sessão porque a role atual não possui leitura privilegiada ADMIN/AUDITOR."
    );
    await expect(page.getByTestId("monitoring-global-alerts-restricted")).toContainText(
      "A triagem administrativa de incidentes globais está oculta nesta sessão porque a role atual não possui leitura privilegiada ADMIN/AUDITOR."
    );
    await expect(page.getByTestId("platform-alerts-ack-batch-btn")).toHaveCount(0);
    await expect(page.locator('aside a[href="/incident-response"]')).toHaveCount(0);
  });

  test("reviewer recebe bloqueio preventivo antes de carregar o core de monitoring", async ({ page }) => {
    const calls = await seedMonitoringPage(page, "REVIEWER");
    await page.goto("/monitoring");

    await expect(page.getByTestId("monitoring-core-read-restricted")).toContainText(
      "A carteira operacional de monitoring está oculta nesta sessão porque a role atual não possui leitura compatível: ADMIN, ANALYST, AUDITOR, VIEWER ou TESTER."
    );
    await expect(page.getByTestId("monitoring-alerts-read-restricted")).toContainText(
      "A carteira operacional de monitoring está oculta nesta sessão porque a role atual não possui leitura compatível: ADMIN, ANALYST, AUDITOR, VIEWER ou TESTER."
    );
    await expect(page.locator('[data-testid="watchlist-item"]')).toHaveCount(0);
    await expect(page.locator('[data-testid="trigger-alert-btn"]')).toHaveCount(0);
    expect(calls.watchlists).toBe(0);
    expect(calls.watchlistItems).toBe(0);
    expect(calls.alerts).toBe(0);
  });

  test("auditor recebe negacao semantica nas watchlists em vez de vazio sintetico", async ({ page }) => {
    await seedMonitoringPage(page, "AUDITOR");

    await page.route("**/api/app/monitoring/watchlists", async (route: Route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "not_authenticated" })
      });
    });

    await page.goto("/monitoring");

    await expect(page.getByTestId("watchlist-load-error")).toContainText("Sua sessão expirou ou não foi autenticada.");
    await expect(page.getByTestId("watchlist-empty")).toHaveCount(0);
    await expect(page.getByTestId("watchlist-item")).toHaveCount(0);
  });

  test("tester recebe CTA de trigger-alert", async ({ page }) => {
    await seedMonitoringPage(page, "TESTER");
    await page.goto("/monitoring");

    await expect(page.locator('[data-testid="watchlist-item"]')).toBeVisible();
    await expect(page.locator('[data-testid="trigger-alert-btn"]')).toBeVisible();
  });

  test("alias OTK_TESTER recebe CTA de trigger-alert", async ({ page }) => {
    await seedMonitoringPage(page, "OTK_TESTER");
    await page.goto("/monitoring");

    await expect(page.locator('[data-testid="watchlist-item"]')).toBeVisible();
    await expect(page.locator('[data-testid="trigger-alert-btn"]')).toBeVisible();
  });

  test("alias OTK_VIEWER recebe leitura core sem CTA de trigger-alert", async ({ page }) => {
    await seedMonitoringPage(page, "OTK_VIEWER");
    await page.goto("/monitoring");

    await expect(page.locator('[data-testid="watchlist-item"]')).toBeVisible();
    await expect(page.locator('[data-testid="trigger-alert-btn"]')).toHaveCount(0);
  });

  test("auditor recebe leitura privilegiada read-only sem mutacoes administrativas", async ({ page }) => {
    await seedMonitoringPage(page, "AUDITOR");
    await page.goto("/monitoring");

    await expect(page.locator('aside a[href="/incident-response"]')).toHaveCount(1);
    await expect(page.getByTestId("monitoring-open-incident-response")).toHaveAttribute("href", "/incident-response");
    await expect(page.getByTestId("monitoring-open-global-alerts")).toHaveAttribute("href", "/alerts");
    await expect(page.getByTestId("monitoring-open-alerts-from-incident-response")).toHaveAttribute("href", "/alerts");
    await expect(page.getByTestId("monitoring-global-alerts-summary")).toBeVisible();
    await expect(page.getByTestId("monitoring-global-alerts-total")).toContainText("1");
    await expect(page.getByTestId("monitoring-global-alerts-pending")).toContainText("1");
    await expect(page.getByTestId("monitoring-global-alerts-acknowledged")).toContainText("0");
    await expect(page.getByTestId("monitoring-global-alerts-tracked")).toContainText("0");
    await expect(page.getByTestId("platform-alert-ack-btn-platform-alert-1")).toHaveCount(0);
  });

  test("auditor recebe negacao semantica tardia na triagem global em vez de estado vazio", async ({ page }) => {
    await seedMonitoringPage(page, "AUDITOR");

    await page.route("**/api/app/monitoring/operational-alert-filter-options", async (route: Route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "monitoring_read_role_required" })
      });
    });

    await page.route("**/api/app/monitoring/operational-alerts?**", async (route: Route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "monitoring_read_role_required" })
      });
    });

    await page.goto("/monitoring");

    await expect(page.getByTestId("monitoring-global-alerts-load-error")).toContainText(
      "A leitura core de monitoring exige papel compatível: ADMIN, ANALYST, AUDITOR, VIEWER ou TESTER."
    );
    await expect(page.getByTestId("monitoring-global-alerts-summary")).toHaveCount(0);
  });

  test("auditor recebe negacao semantica da fila rastreada em vez de lista vazia silenciosa", async ({ page }) => {
    await seedMonitoringPage(page, "AUDITOR");

    await page.route("**/api/app/operations/work-items?module=alerts&resource_type=operational_alert&limit=100", async (route: Route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "not_authenticated" })
      });
    });

    await page.goto("/monitoring");

    await expect(page.getByText("Sua sessão expirou ou não foi autenticada.").first()).toBeVisible();
    await expect(page.getByTestId("monitoring-global-alerts-summary")).toBeVisible();
    await expect(page.getByTestId("monitoring-global-alerts-total")).toContainText("1");
    await expect(page.getByTestId("monitoring-global-alerts-tracked")).toContainText("0");
  });
});

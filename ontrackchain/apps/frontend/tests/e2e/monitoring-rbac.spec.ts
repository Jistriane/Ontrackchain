import { expect, test, type Page, type Route } from "@playwright/test";

async function seedFrontendAuth(page: Page, role: string) {
  await page.context().addCookies([
    {
      name: "otc_token",
      value: "pw-e2e-token",
      domain: "localhost",
      path: "/",
      httpOnly: false,
      secure: false,
      sameSite: "Lax"
    }
  ]);

  await page.route("**/api/app/auth/context", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        org_id: "org-e2e",
        user_id: "user-e2e",
        linked_user_id: "linked-e2e",
        role,
        plan: "professional",
        auth_method: "jwt",
        mfa_mode: "totp",
        mfa_provider_homologated: "true"
      })
    });
  });

  await page.route("**/api/app/monitoring/watchlists", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        data: [{ id: "watchlist-1", name: "VIP Wallets", priority: "high" }]
      })
    });
  });

  await page.route("**/api/app/monitoring/watchlists/watchlist-1/items?limit=20", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        data: [{ id: "item-1", watchlist_id: "watchlist-1", address: "0xabc", chain: "ethereum", created_at: "2026-07-14T12:00:00Z" }]
      })
    });
  });

  await page.route("**/api/app/monitoring/alerts?**", async (route: Route) => {
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
}

test.describe("monitoring RBAC", () => {
  test("analyst nao recebe superficies administrativas privilegiadas", async ({ page }) => {
    await seedFrontendAuth(page, "ANALYST");
    await page.goto("/monitoring");

    await expect(page.locator('[data-testid="watchlist-item"]')).toBeVisible();
    await expect(page.locator('[data-testid="trigger-alert-btn"]')).toHaveCount(0);
    await expect(page.getByTestId("monitoring-worker-read-restricted")).toContainText(
      "Os painéis administrativos de investigation estão ocultos nesta sessão porque a role atual não possui leitura privilegiada ADMIN/AUDITOR."
    );
    await expect(page.getByTestId("platform-alert-read-restricted")).toContainText(
      "A triagem administrativa de incidentes globais está oculta nesta sessão porque a role atual não possui leitura privilegiada ADMIN/AUDITOR."
    );
    await expect(page.getByTestId("dlq-read-restricted")).toContainText(
      "A remediação administrativa da DLQ está oculta nesta sessão porque a role atual não possui leitura privilegiada ADMIN/AUDITOR."
    );
    await expect(page.getByTestId("platform-alerts-ack-batch-btn")).toHaveCount(0);
    await expect(page.getByTestId("dlq-requeue-btn-case-dlq-1")).toHaveCount(0);
  });

  test("tester recebe CTA de trigger-alert", async ({ page }) => {
    await seedFrontendAuth(page, "TESTER");
    await page.goto("/monitoring");

    await expect(page.locator('[data-testid="watchlist-item"]')).toBeVisible();
    await expect(page.locator('[data-testid="trigger-alert-btn"]')).toBeVisible();
  });

  test("auditor recebe leitura privilegiada read-only sem mutacoes administrativas", async ({ page }) => {
    await seedFrontendAuth(page, "AUDITOR");
    await page.goto("/monitoring");

    await expect(page.getByTestId("worker-generated-at")).toContainText("snapshot:");
    await expect(page.getByTestId("platform-alert-row")).toHaveCount(1);
    await expect(page.getByTestId("platform-alert-mutation-restricted")).toContainText(
      "As mutações e exportações administrativas de incidentes globais estão ocultas nesta sessão porque a role atual não possui papel administrativo ADMIN."
    );
    await expect(page.getByTestId("platform-alerts-ack-batch-btn")).toHaveCount(0);
    await expect(page.getByTestId("platform-alert-ack-btn-platform-alert-1")).toHaveCount(0);
    await expect(page.getByTestId("platform-alert-select-all")).toHaveCount(0);
    await expect(page.getByTestId("dlq-case-row")).toHaveCount(1);
    await expect(page.getByTestId("dlq-mutation-restricted")).toContainText(
      "As mutações administrativas da DLQ estão ocultas nesta sessão porque a role atual não possui papel administrativo ADMIN."
    );
    await expect(page.getByTestId("dlq-requeue-btn-case-dlq-1")).toHaveCount(0);
    await expect(page.getByTestId("dlq-ack-btn-case-dlq-1")).toHaveCount(0);
    await expect(page.getByTestId("dlq-discard-btn-case-dlq-1")).toHaveCount(0);
  });
});

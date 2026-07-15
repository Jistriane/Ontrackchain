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
}

async function seedDelayedFrontendAuth(page: Page, role: string, delayMs: number) {
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
    await new Promise((resolve) => setTimeout(resolve, delayMs));
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
}

async function seedAlertsReadApis(page: Page) {
  await page.route("**/api/app/monitoring/operational-alert-filter-options", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        services: ["aml-monitor"],
        receivers: ["slack"],
        generated_at: "2026-07-06T12:00:00.000Z"
      })
    });
  });

  await page.route("**/api/app/monitoring/operational-alerts?**", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        generated_at: "2026-07-06T12:00:00.000Z",
        receiver_filter: null,
        service_filter: null,
        severity_filter: null,
        status_filter: null,
        triage_status_filter: null,
        cursor: null,
        limit: 20,
        count: 1,
        total_count: 1,
        has_more: false,
        next_cursor: null,
        data: [
          {
            id: "alert-rbac-01",
            receiver: "slack",
            status: "firing",
            triage_status: "pending",
            alertname: "Alert RBAC",
            service: "aml-monitor",
            severity: "critical",
            fingerprint: "fp-alert-rbac-01",
            labels: {},
            annotations: {
              summary: "Resumo RBAC",
              description: "Descrição RBAC"
            },
            first_received_at: "2026-07-06T12:00:00.000Z",
            last_received_at: "2026-07-06T12:05:00.000Z",
            delivery_count: 2,
            resolved_at: null,
            triaged_at: null,
            triaged_by: null,
            triage_note: null
          }
        ]
      })
    });
  });

  await page.route("**/api/app/operations/work-items?module=alerts&resource_type=operational_alert&limit=100", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        data: [
          {
            id: "work-item-alert-rbac-01",
            module: "alerts",
            resource_type: "operational_alert",
            resource_id: "alert-rbac-01",
            owner_user_id: "owner-rbac-01",
            queue_status: "UNDER_REVIEW",
            priority: "high",
            due_at: null,
            note: "seed",
            metadata: {
              domain: "monitoring",
              containment_status: "in_progress",
              incident_commander: "Ops QA"
            },
            last_activity_at: "2026-07-06T12:06:00.000Z",
            updated_at: "2026-07-06T12:06:00.000Z"
          }
        ]
      })
    });
  });

  await page.route("**/api/app/operations/work-items/work-item-alert-rbac-01/timeline", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        item: {
          id: "work-item-alert-rbac-01",
          module: "alerts",
          resource_type: "operational_alert",
          resource_id: "alert-rbac-01",
          owner_user_id: "owner-rbac-01",
          queue_status: "UNDER_REVIEW",
          priority: "high",
          due_at: null,
          note: "seed",
          metadata: {
            domain: "monitoring",
            containment_status: "in_progress",
            incident_commander: "Ops QA"
          },
          last_activity_at: "2026-07-06T12:06:00.000Z",
          updated_at: "2026-07-06T12:06:00.000Z"
        },
        events: [],
        comments: []
      })
    });
  });
}

test.describe("alerts RBAC", () => {
  test("sidebar nao pisca link privilegiado antes de resolver auth", async ({ page }) => {
    await seedDelayedFrontendAuth(page, "AUDITOR", 1200);
    await seedAlertsReadApis(page);

    await page.goto("/alerts");

    await expect(page.locator('aside a[href="/alerts"]')).toHaveCount(0);
    await expect(page.locator('aside a[href="/counterparties"]')).toHaveCount(0);

    await expect(page.locator('aside a[href="/alerts"]')).toHaveCount(1);
  });

  test("analyst nao recebe leitura privilegiada da central de alertas", async ({ page }) => {
    await seedFrontendAuth(page, "ANALYST");

    await page.goto("/alerts");

    await expect(page.locator('aside a[href="/alerts"]')).toHaveCount(0);
    await expect(page.getByTestId("platform-alert-read-restricted")).toContainText(
      "A triagem administrativa de incidentes globais está oculta nesta sessão porque a role atual não possui leitura privilegiada ADMIN/AUDITOR."
    );
    await expect(page.getByTestId("platform-alert-rca-read-restricted")).toContainText(
      "A triagem administrativa de incidentes globais está oculta nesta sessão porque a role atual não possui leitura privilegiada ADMIN/AUDITOR."
    );
    await expect(page.getByTestId("platform-alert-row-alert-rbac-01")).toHaveCount(0);
    await expect(page.getByTestId("platform-alerts-ack-batch-btn")).toHaveCount(0);
    await expect(page.getByTestId("platform-alerts-export-filtered-btn")).toHaveCount(0);
  });

  test("auditor recebe leitura read-only sem mutacoes administrativas", async ({ page }) => {
    await seedFrontendAuth(page, "AUDITOR");
    await seedAlertsReadApis(page);
    await page.goto("/alerts");

    await expect(page.locator('aside a[href="/alerts"]')).toHaveCount(1);
    await expect(page.getByTestId("platform-alert-row-alert-rbac-01")).toContainText("Alert RBAC");
    await expect(page.getByTestId("platform-alert-mutation-restricted")).toContainText(
      "As mutações e exportações administrativas de incidentes globais estão ocultas nesta sessão porque a role atual não possui papel administrativo ADMIN."
    );
    await expect(page.getByTestId("platform-alerts-ack-batch-btn")).toHaveCount(0);
    await expect(page.getByTestId("platform-alerts-export-filtered-btn")).toHaveCount(0);
    await expect(page.getByTestId("platform-alert-track-btn-alert-rbac-01")).toHaveCount(0);
    await expect(page.getByTestId("platform-alert-ack-btn-alert-rbac-01")).toHaveCount(0);
    await page.getByRole("button", { name: "Ver timeline" }).click();
    await expect(page.getByTestId("platform-alert-rca-mutation-restricted")).toContainText(
      "As mutações e exportações administrativas de incidentes globais estão ocultas nesta sessão porque a role atual não possui papel administrativo ADMIN."
    );
    await expect(page.getByTestId("platform-alert-rca-save")).toHaveCount(0);
  });
});

import { expect, test, type Page, type Route } from "@playwright/test";

import { seedFrontendAuth } from "./seed-frontend-auth";

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
    await seedFrontendAuth(page, { role: "AUDITOR", authContextDelayMs: 1200 });
    await seedAlertsReadApis(page);

    await page.goto("/alerts");

    await expect(page.locator('aside a[href="/alerts"]')).toHaveCount(0);
    await expect(page.locator('aside a[href="/counterparties"]')).toHaveCount(0);

    await expect(page.locator('aside a[href="/alerts"]')).toHaveCount(1);
  });

  test("analyst nao recebe leitura privilegiada da central de alertas", async ({ page }) => {
    await seedFrontendAuth(page, { role: "ANALYST" });

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
    await seedFrontendAuth(page, { role: "AUDITOR" });
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
    await expect(page.getByTestId("platform-alert-open-incident-response-alert-rbac-01")).toHaveAttribute(
      "href",
      "/incident-response?alertId=alert-rbac-01&alertName=Alert%20RBAC&severity=critical"
    );
    await page.getByRole("button", { name: "Ver timeline" }).click();
    await expect(page.getByTestId("platform-alert-rca-mutation-restricted")).toContainText(
      "As mutações e exportações administrativas de incidentes globais estão ocultas nesta sessão porque a role atual não possui papel administrativo ADMIN."
    );
    await expect(page.getByTestId("platform-alert-rca-save")).toHaveCount(0);
  });

  test("retorno contextual de incident-response reabre o alerta de origem no cockpit canônico", async ({ page }) => {
    await seedFrontendAuth(page, { role: "AUDITOR" });
    await seedAlertsReadApis(page);
    await page.goto("/alerts?alertId=alert-rbac-01&alertName=Alert%20RBAC&severity=critical");

    await expect(page.getByTestId("platform-alert-return-context")).toContainText("alert_id=alert-rbac-01");
    await expect(page.getByTestId("platform-alert-return-marker-alert-rbac-01")).toContainText(
      "Alerta de origem reaberto neste cockpit."
    );
    await expect(page.getByTestId("work-item-timeline-panel")).toBeVisible();
  });

  test("auditor recebe negacao semantica da fila rastreada em vez de silencio operacional", async ({ page }) => {
    await seedFrontendAuth(page, { role: "AUDITOR" });
    await seedAlertsReadApis(page);

    await page.route("**/api/app/operations/work-items?module=alerts&resource_type=operational_alert&limit=100", async (route: Route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "not_authenticated" })
      });
    });

    await page.goto("/alerts");

    await expect(page.getByText("Sua sessão expirou ou não foi autenticada.").first()).toBeVisible();
    await expect(page.getByTestId("platform-alert-row-alert-rbac-01")).toContainText("Alert RBAC");
    await expect(page.getByTestId("platform-alert-queue-alert-rbac-01")).toHaveCount(0);
    await expect(page.getByTestId("platform-alert-rca-summary-alert-rbac-01")).toHaveCount(0);
  });
});

import { expect, test, type Page, type Route } from "@playwright/test";

async function seedFrontendAuth(page: Page) {
  await page.context().addCookies([
    {
      name: "otc_token",
      value: "pw-e2e-token",
      domain: "localhost",
      path: "/",
      httpOnly: false,
      secure: false,
      sameSite: "Lax"
    },
    {
      name: "otc_2fa",
      value: "ok",
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
        role: "ANALYST",
        plan: "professional",
        auth_method: "jwt",
        mfa_mode: "totp",
        mfa_provider_homologated: "true"
      })
    });
  });
}

test.describe("alerts and dashboard context links", () => {
  test("alerts deriva links contextuais na linha operacional", async ({ page }: { page: Page }) => {
    const caseId = "55555555-5555-4555-8555-555555555555";
    const reportId = "rep-alert-01";
    const address = "0xcccccccccccccccccccccccccccccccccccccccc";

    await seedFrontendAuth(page);

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

    await page.route("**/api/app/operations/work-items?module=alerts**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
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
              id: "alert-e2e-01",
              receiver: "slack",
              status: "firing",
              triage_status: "pending",
              alertname: "Alert E2E",
              service: "aml-monitor",
              severity: "critical",
              fingerprint: "fp-alert-e2e-01",
              labels: {
                case_id: caseId,
                request_id: caseId,
                report_id: reportId,
                address,
                chain: "ethereum"
              },
              annotations: {
                summary: "Resumo do alerta",
                description: "Descricao do alerta"
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

    await page.goto("/alerts");

    await expect(page.getByTestId("platform-alert-row")).toContainText("Alert E2E");
    await expect(page.locator(`a[href="/cases/${caseId}"]`)).toBeVisible();
    await expect(
      page.locator(`a[href="/audit?resource_type=case&resource_id=${caseId}&request_id=${caseId}&report_id=${reportId}"]`)
    ).toBeVisible();
    await expect(
      page.locator(`a[href="/evidence?domain=all&resource_type=case&resource_id=${caseId}&request_id=${caseId}&report_id=${reportId}"]`)
    ).toBeVisible();
    await expect(
      page.locator(
        `a[href="/investigate?address=${encodeURIComponent(address)}&chain=ethereum&report_type=technical_basic&case_id=${caseId}"]`
      )
    ).toBeVisible();
    await expect(
      page.locator(
        `a[href="/sanctions?address=${encodeURIComponent(address)}&chain=ethereum&autostart=1&case_id=${caseId}"]`
      )
    ).toBeVisible();
  });

  test("dashboard deriva links contextuais na tabela de casos recentes", async ({ page }: { page: Page }) => {
    const caseId = "66666666-6666-4666-8666-666666666666";
    const address = "0xdddddddddddddddddddddddddddddddddddddddd";

    await seedFrontendAuth(page);
    await page.goto("/dashboard");

    await expect(page.getByText(caseId)).toBeVisible();
    await expect(page.locator(`a[href="/cases/${caseId}"]`)).toBeVisible();
    await expect(
      page.locator(`a[href="/audit?resource_type=case&resource_id=${caseId}&request_id=${caseId}"]`)
    ).toBeVisible();
    await expect(
      page.locator(`a[href="/evidence?domain=all&resource_type=case&resource_id=${caseId}&request_id=${caseId}"]`)
    ).toBeVisible();
    await expect(
      page.locator(`a[href="/reports?case_id=${caseId}&report_type=coaf_ready_report"]`)
    ).toBeVisible();
    await expect(
      page.locator(
        `a[href="/sanctions?address=${encodeURIComponent(address)}&chain=ethereum&autostart=1&case_id=${caseId}"]`
      )
    ).toBeVisible();
    await expect(
      page.locator(
        `a[href="/blocks?address=${encodeURIComponent(address)}&chain=ethereum&autostart=1&case_id=${caseId}"]`
      )
    ).toBeVisible();
  });
});

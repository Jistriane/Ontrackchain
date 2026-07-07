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
        role: "AUDITOR",
        plan: "professional",
        auth_method: "jwt",
        mfa_mode: "totp",
        mfa_provider_homologated: "true"
      })
    });
  });
}

test.describe("audit labels", () => {
  test("renderiza acao e tipo de recurso com label amigavel e codigo tecnico preservado", async ({ page }) => {
    await seedFrontendAuth(page);

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const url = new URL(route.request().url());
      const action = url.searchParams.get("action");
      const resourceType = url.searchParams.get("resource_type");

      const allRows = [
        {
          id: "audit-log-01",
          user_id: "user-e2e",
          action: "report_generated",
          resource_type: "report",
          resource_id: "report-001",
          request_id: "req-audit-001",
          report_id: "report-001",
          file_hash_sha256: "a".repeat(64),
          metadata: {
            case_id: "case-001",
            request_id: "req-audit-001"
          },
          created_at: "2026-07-07T12:00:00.000Z"
        },
        {
          id: "audit-log-02",
          user_id: "user-e2e",
          action: "authorization_denied",
          resource_type: "operational_alerts",
          resource_id: "alert-001",
          request_id: "req-audit-002",
          report_id: null,
          file_hash_sha256: null,
          metadata: {
            detail: "admin_role_required"
          },
          created_at: "2026-07-07T12:05:00.000Z"
        }
      ];

      const filteredRows = allRows.filter((row) => {
        if (action && row.action !== action) {
          return false;
        }
        if (resourceType && row.resource_type !== resourceType) {
          return false;
        }
        return true;
      });

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: filteredRows,
          page: 1,
          count: filteredRows.length,
          limit: 50,
          total: filteredRows.length,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.goto("/audit");

    await expect(page.locator('[data-testid="audit-filter-action"] option[value="report_generated"]')).toHaveText(
      "Relatório gerado (report_generated)"
    );
    await expect(page.locator('[data-testid="audit-filter-resource-type"] option[value="report"]')).toHaveText(
      "Relatório (report)"
    );

    await page.selectOption('[data-testid="audit-filter-action"]', "report_generated");
    await page.click('[data-testid="audit-search-btn"]');

    const filteredRow = page.locator('[data-testid="audit-row"]').first();
    await expect(filteredRow).toContainText("Relatório gerado (report_generated)");
    await expect(filteredRow).toContainText("Relatório (report)");

    await filteredRow.click();

    await expect(page.locator('[data-testid="audit-details-panel"]')).toContainText(
      "Relatório gerado (report_generated)"
    );
    await expect(page.locator('[data-testid="audit-details-panel"]')).toContainText("Relatório (report)");
  });
});

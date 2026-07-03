import { expect, test } from "@playwright/test";

test.describe("reports history backend", () => {
  test("carrega historico backend e aplica filtro por report_type", async ({ page }) => {
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

    await page.route("**/api/app/report-types?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          generated_at: "2026-07-03T12:00:00.000Z",
          types: [
            {
              canonical: "technical_basic",
              label: "Technical Basic",
              available: true,
              cost_credits: 1,
              min_plan: "starter",
              format: "pdf",
              deprecated: false
            },
            {
              canonical: "coaf_ready_report",
              label: "COAF Ready",
              available: true,
              cost_credits: 2,
              min_plan: "professional",
              format: "pdf",
              deprecated: false
            }
          ]
        })
      });
    });

    await page.route("**/api/app/investigation/cases?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ page: 1, limit: 20, data: [] })
      });
    });

    await page.route("**/api/app/operations/work-items?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/reports/list?**", async (route) => {
      const url = new URL(route.request().url());
      const reportType = url.searchParams.get("report_type");

      const allRows = [
        {
          report_id: "rep-all-01",
          case_id: "11111111-1111-4111-8111-111111111111",
          report_type_requested: "technical",
          report_type: "technical_basic",
          content_type: "application/pdf",
          file_hash_sha256: "a".repeat(64),
          onchain_hash: null,
          created_at: "2026-07-03T10:00:00.000Z",
          has_download_audit: true
        },
        {
          report_id: "rep-all-02",
          case_id: "22222222-2222-4222-8222-222222222222",
          report_type_requested: "coaf",
          report_type: "coaf_ready_report",
          content_type: "application/pdf",
          file_hash_sha256: "b".repeat(64),
          onchain_hash: null,
          created_at: "2026-07-03T09:00:00.000Z",
          has_download_audit: false
        }
      ];

      const filteredRows = reportType ? allRows.filter((row) => row.report_type === reportType) : allRows;

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: filteredRows,
          page: 1,
          limit: 20,
          total: filteredRows.length,
          has_more: false
        })
      });
    });

    await page.goto("/reports");

    await expect(page.getByTestId("reports-history-table")).toBeVisible();
    await expect(page.getByTestId("reports-history-row")).toHaveCount(2);
    await expect(page.getByTestId("reports-history-table")).toContainText("rep-all-01");
    await expect(page.getByTestId("reports-history-table")).toContainText("rep-all-02");

    const reportTypeField = page.locator("label:has-text('Report type') select");
    await reportTypeField.selectOption("technical_basic");
    await page.getByTestId("reports-history-apply").click();

    await expect(page.getByTestId("reports-history-row")).toHaveCount(1);
    await expect(page.getByTestId("reports-history-table")).toContainText("rep-all-01");
    await expect(page.getByTestId("reports-history-table")).not.toContainText("rep-all-02");
  });
});

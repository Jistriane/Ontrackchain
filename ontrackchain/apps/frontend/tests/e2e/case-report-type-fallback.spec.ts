import { expect, test, type Route } from "@playwright/test";

test.describe("case report type fallback", () => {
  test("preserva fallback amigavel quando o catalogo de tipos nao carrega", async ({ page }) => {
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

    await page.route("**/api/app/investigation/status?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "completed" })
      });
    });

    await page.route("**/api/app/report-types?**", async (route: Route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: "catalog_unavailable" })
      });
    });

    await page.goto("/cases/11111111-1111-4111-8111-111111111111");

    await expect(page.locator('[data-testid="case-report-type-select"] option[value="technical_basic"]')).toHaveText(
      "Technical Basic (technical_basic)"
    );
    await expect(page.getByText("Technical Basic (technical_basic)").first()).toBeVisible();
  });
});

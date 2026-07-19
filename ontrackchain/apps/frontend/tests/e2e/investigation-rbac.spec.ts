import { expect, test, type Page, type Route } from "@playwright/test";

import { seedFrontendAuth } from "./seed-frontend-auth";

async function seedInvestigationPage(page: Page, role: string) {
  const calls = {
    estimate: 0,
    start: 0
  };

  await seedFrontendAuth(page, { role });

  await page.route("**/api/app/report-types?**", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        types: [
          {
            canonical: "technical_basic",
            label: "Technical Basic",
            available: true,
            cost_credits: 12
          }
        ]
      })
    });
  });

  await page.route("**/api/app/investigation/estimate", async (route: Route) => {
    calls.estimate += 1;
    if (role === "VIEWER") {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "investigation_operational_role_required" })
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        quote_id: "quote-e2e-1",
        total_credits: 12,
        plan: "professional",
        can_proceed: true
      })
    });
  });

  await page.route("**/api/app/investigation/start", async (route: Route) => {
    calls.start += 1;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ case_id: "11111111-1111-1111-1111-111111111111" })
    });
  });

  return calls;
}

test.describe("investigation RBAC", () => {
  test("viewer recebe bloqueio preventivo antes de gerar quote", async ({ page }) => {
    const calls = await seedInvestigationPage(page, "VIEWER");
    await page.goto("/investigate");

    await page.fill('[data-testid="wallet-address"]', "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");
    await page.selectOption('[data-testid="chain-select"]', "ethereum");
    await page.selectOption('[data-testid="report-type"]', "technical_basic");

    await expect(page.getByTestId("start-investigation-btn")).toHaveCount(0);
    await expect(page.getByTestId("investigate-generate-quote-restricted")).toContainText(
      "A geração de quote está oculta nesta sessão porque a role atual não possui autorização operacional ADMIN/ANALYST/OTK_ANALYST."
    );
    await expect(page.locator('[data-testid="quote-preview"]')).toHaveCount(0);
    expect(calls.estimate).toBe(0);
  });

  test("analyst continua conseguindo gerar quote", async ({ page }) => {
    const calls = await seedInvestigationPage(page, "ANALYST");
    await page.goto("/investigate");

    await page.fill('[data-testid="wallet-address"]', "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb");
    await page.selectOption('[data-testid="chain-select"]', "ethereum");
    await page.selectOption('[data-testid="report-type"]', "technical_basic");
    await page.click('[data-testid="start-investigation-btn"]');

    await expect(page.locator('[data-testid="quote-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="quote-credits"]')).toHaveText("12");
    expect(calls.estimate).toBe(1);
  });

  test("alias OTK_ANALYST continua conseguindo gerar quote", async ({ page }) => {
    const calls = await seedInvestigationPage(page, "OTK_ANALYST");
    await page.goto("/investigate");

    await page.fill('[data-testid="wallet-address"]', "0xcccccccccccccccccccccccccccccccccccccccc");
    await page.selectOption('[data-testid="chain-select"]', "ethereum");
    await page.selectOption('[data-testid="report-type"]', "technical_basic");
    await page.click('[data-testid="start-investigation-btn"]');

    await expect(page.locator('[data-testid="quote-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="quote-credits"]')).toHaveText("12");
    expect(calls.estimate).toBe(1);
  });
});

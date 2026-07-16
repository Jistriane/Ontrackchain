import { expect, test } from "@playwright/test";

import { loginIntoShowcase, showcaseOnly } from "./showcase-helpers";

test.describe("standalone showcase monitoring", () => {
  test.skip(!showcaseOnly, "requer TEST_SHOWCASE_MODE=true");

  test("exibe e preserva a triagem do incidente critico", async ({ page }) => {
    await loginIntoShowcase(page);

    await page.goto("/monitoring");
    await page.selectOption('[data-testid="platform-alert-filter-severity"]', "critical");
    await page.click('[data-testid="platform-alerts-refresh-btn"]');

    const row = page.locator('[data-testid="platform-alert-row"]').filter({ hasText: "IndexerLagHigh" }).first();
    await expect(row).toBeVisible();
    const rowTextBefore = (await row.textContent()) ?? "";

    if (rowTextBefore.includes("triagem=Pendente")) {
      await page.click('[data-testid="platform-alerts-ack-batch-btn"]');
      await expect(page.locator('[data-testid="platform-alert-confirm-dialog-filtered"]')).toBeVisible();
      await page.click('[data-testid="platform-alert-confirm-dialog-filtered-confirm"]');

      await expect(page.locator('[data-testid="platform-alert-message"]')).toContainText("reconhecidos em lote");
    }

    await page.selectOption('[data-testid="platform-alert-filter-triage"]', "acknowledged");
    await page.click('[data-testid="platform-alerts-refresh-btn"]');
    await expect(row).toContainText("triagem=Reconhecido");
  });
});

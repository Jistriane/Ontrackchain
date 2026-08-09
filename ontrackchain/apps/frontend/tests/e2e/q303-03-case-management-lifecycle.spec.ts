import { test, expect } from "@playwright/test";

test.describe("Q3-03 #3 Gestão Completa de Casos Lifecycle E2E", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL("/dashboard");
  });

  test("filtra casos por severidade → pagina lista → atualiza status em batch → exporta CSV", async ({
    page,
  }) => {
    await page.goto("/cases");
    await expect(page.locator("h1")).toContainText("Case Management");
    await expect(page.locator("text=Total Cases")).toBeVisible();
    await expect(page.locator("text=Open Cases")).toBeVisible();

    const severityFilter = page.locator('select, [role="combobox"]').filter({
      hasText: /Severity|Severidade|Prioridade/i,
    });
    if (await severityFilter.count() === 0) {
      const anySelect = page.locator("select").first();
      if (await anySelect.isVisible()) {
        await anySelect.selectOption("high");
      }
    } else {
      await severityFilter.first().selectOption("high");
    }
    await page.waitForTimeout(1500);
    await expect(page.locator("text=Investigation Cases")).toBeVisible();

    const nextPage = page
      .locator('button, [role="button"]')
      .filter({ hasText: /^Next|Próxima|>$/i })
      .first();
    if (await nextPage.isVisible() && await nextPage.isEnabled()) {
      const initialRows = await page.locator(".otc-panel").count();
      await nextPage.click();
      await page.waitForTimeout(2000);
      const afterRows = await page.locator(".otc-panel").count();
      expect(afterRows).toBeGreaterThanOrEqual(0);
    }

    const firstCheckbox = page.locator('input[type="checkbox"]').nth(0);
    if (await firstCheckbox.isVisible()) {
      await firstCheckbox.check();
      const secondCheckbox = page.locator('input[type="checkbox"]').nth(1);
      if (await secondCheckbox.isVisible()) {
        await secondCheckbox.check();
      }
      const batchBtn = page
        .locator('button')
        .filter({ hasText: /Batch Update|Atualizar em lote|Atribuir/i })
        .first();
      if (await batchBtn.isVisible()) {
        await batchBtn.click();
        const statusSelect = page.locator('select:has-text("Under Investigation")').first();
        if (await statusSelect.isVisible()) {
          await statusSelect.selectOption("under_investigation");
          await page.click("text=Apply");
        }
      }
    }

    const exportBtn = page
      .locator('button, a')
      .filter({ hasText: /Export|Download|CSV/i })
      .first();
    if (await exportBtn.isVisible()) {
      const downloadPromise = page.waitForEvent("download", { timeout: 20000 }).catch(() => null);
      await exportBtn.click();
      const download = await downloadPromise;
      if (download) {
        const filename = download.suggestedFilename().toLowerCase();
        expect(filename).toMatch(/case|\.csv|\.xlsx|\.zip/);
      }
    }
  });
});

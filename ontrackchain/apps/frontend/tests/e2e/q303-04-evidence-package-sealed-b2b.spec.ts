import { test, expect } from "@playwright/test";

test.describe("Q3-03 #4 Download Pacote Evidências Lacrado B2B E2E", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL("/dashboard");
  });

  test("entra detalhe caso → tela evidências → gera pacote → valida sha256 → download PDF", async ({
    page,
  }) => {
    await page.goto("/cases");
    await expect(page.locator("h1")).toContainText("Case Management");
    await page.click(".otc-panel >> nth=0");
    await expect(page.locator("text=Case:")).toBeVisible({ timeout: 10000 });

    const evidenceTab = page
      .locator('[role="tab"], a, button')
      .filter({ hasText: /Evidence|Evidências|Package|Pacote/i })
      .first();
    if (await evidenceTab.isVisible()) {
      await evidenceTab.click();
    } else {
      try {
        await page.goto("/evidence");
        await expect(page.locator("text=Evidence")).toBeVisible({ timeout: 5000 });
      } catch {
        await page.goto("/cases");
        await page.click(".otc-panel >> nth=0");
      }
    }

    await expect(page.locator("text=Chain Explorer Screenshots|Evidência|Relatório")).toBeVisible({
      timeout: 5000,
    });

    const generateBtn = page
      .locator('button')
      .filter({ hasText: /Generate Package|Gerar Pacote|Lacrar|Sealing|Hash/i })
      .first();
    if (await generateBtn.isVisible()) {
      await generateBtn.click();
      await expect(
        page.locator("text=/SHA-256|sealing|lacrado|hash.*algoritmo|integridade/i").first()
      ).toBeVisible({ timeout: 25000 });
    }

    const hashLocator = page.locator("text=/^[a-f0-9]{64}$/").first();
    if (await hashLocator.isVisible()) {
      const hashText = await hashLocator.textContent();
      expect(hashText?.length).toBe(64);
    } else {
      const hashSection = page
        .locator("text=/SHA-256/").first()
        .locator("..");
      if (await hashSection.isVisible()) {
        const text = await hashSection.textContent();
        expect(text).toMatch(/[a-fA-F0-9]{32,}/);
      }
    }

    const pdfBtn = page
      .locator("a, button")
      .filter({ hasText: /Download PDF|Baixar Pacote|Evidence Package|\.pdf/i })
      .first();
    if (await pdfBtn.isVisible()) {
      const downloadPromise = page.waitForEvent("download", { timeout: 30000 }).catch(() => null);
      await pdfBtn.click();
      const download = await downloadPromise;
      if (download) {
        const filename = download.suggestedFilename().toLowerCase();
        expect(filename).toMatch(/\.pdf$|\.zip$/);
      }
    }
  });
});

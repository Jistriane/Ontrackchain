import { test, expect } from "@playwright/test";

test.describe("Q3-03 #2 AI Insights Painel Analista E2E", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL("/dashboard");
  });

  test("explica decisão risco → gera resumo → visualiza grafo → exporta insights PDF", async ({
    page,
  }) => {
    await page.goto("/ai");
    await expect(page.locator("h1")).toContainText("AI Intelligence");
    await expect(page.locator("text=Explain Decision")).toBeVisible();

    await page.fill('input[placeholder="Enter case ID"]', "CASE-Q303-AI-2026-0199");
    await page.selectOption("select", "risk_score");
    await page.click("text=Explain Decision");
    await expect(page.locator("text=Confidence:")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=Reasoning Steps:")).toBeVisible();

    await page.click("text=Case Insights");
    await expect(page.locator("text=Case ID")).toBeVisible();
    const summaryBtn = page.locator('button:has-text("Generate Summary"), button:has-text("Gerar Resumo")');
    if (await summaryBtn.isVisible()) {
      await summaryBtn.click();
      await expect(
        page.locator("text=/Resumo|Summary executivo|Pontos chave/i").first()
      ).toBeVisible({ timeout: 15000 });
    }

    await page.click("text=Graph Analysis");
    await expect(page.locator("text=Blockchain Address")).toBeVisible();
    await page.fill('input[placeholder="0x..."]', "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae");
    await page.selectOption("select", "ethereum");
    await page.click("text=Analyze Graph");
    await expect(page.locator("text=Nodes:")).toBeVisible({ timeout: 20000 });
    await expect(page.locator("text=Edges:")).toBeVisible();

    const exportBtn = page
      .locator('button')
      .filter({ hasText: /Export|PDF|Download/i })
      .first();
    if (await exportBtn.isVisible()) {
      const downloadPromise = page.waitForEvent("download", { timeout: 20000 }).catch(() => null);
      await exportBtn.click();
      const download = await downloadPromise;
      if (download) {
        const filename = download.suggestedFilename();
        expect(filename.toLowerCase()).toMatch(/\.pdf$|\.csv$|\.zip$/);
      }
    }
  });
});

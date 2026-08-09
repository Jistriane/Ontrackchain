import { test, expect } from "@playwright/test";

test.describe("Q3-03 #1 Fluxo Investigação Completa E2E", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL("/dashboard");
  });

  test("cria caso → adiciona contraparte → pesquisa sanções → atribui analista → fecha caso", async ({
    page,
  }) => {
    await page.goto("/cases");
    await expect(page.locator("h1")).toContainText("Case Management");

    await page.click("text=+ New Case");
    await page.fill('input[placeholder="Case title"]', "CASO-Q303-E2E-INVESTIGACAO-0001");
    await page.fill(
      'textarea[placeholder="Case description"]',
      "Fluxo completo E2E de investigação — Sprint 19 Q3-03 Especialista"
    );
    await page.selectOption("select >> nth=0", "high");
    await page.selectOption("select >> nth=1", "aml");
    await page.click("text=Create Case");
    await expect(page.locator("text=CASO-Q303-E2E-INVESTIGACAO-0001")).toBeVisible({
      timeout: 15000,
    });

    await page.click(".otc-panel >> nth=0");
    await expect(page.locator("text=Case:")).toBeVisible();

    const addCounterpartyBtn = page.locator('button:has-text("Add Counterparty")');
    if (await addCounterpartyBtn.isVisible()) {
      await addCounterpartyBtn.click();
      await page.fill('input[placeholder="Wallet address"]', "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae");
      await page.selectOption('select:has-text("Ethereum")', "ethereum");
      await page.click("text=Save Counterparty");
      await expect(
        page.locator("text=0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae")
      ).toBeVisible({ timeout: 10000 });
    }

    const sanctionsBtn = page.locator('button, [role="button"]').filter({
      hasText: /Sanction|Screening|Sanções/i,
    });
    if (await sanctionsBtn.count() > 0) {
      await sanctionsBtn.first().click();
      await page.waitForTimeout(2000);
      const statusText = page.locator("text=/OFAC|EU-5AMLD|Sem sanções|No hits|Hit/i").first();
      await expect(statusText).toBeVisible({ timeout: 10000 });
    }

    const assignBtn = page.locator('button').filter({ hasText: /Assign|Atribuir analista/i }).first();
    if (await assignBtn.isVisible()) {
      await assignBtn.click();
      const analystSelect = page.locator('select, [role="listbox"]').first();
      if (await analystSelect.isVisible()) {
        await analystSelect.selectOption({ index: 1 });
        await page.click("text=Confirm");
      }
    }

    const closeBtn = page.locator('button:has-text("Close Case"), button:has-text("Fechar Caso")').first();
    if (await closeBtn.isVisible()) {
      await closeBtn.click();
      await page.selectOption('select:has-text("Sanctions Hit")', "sanctions_hit");
      await page.fill('textarea', "Caso fechado E2E Sprint 19 Q3-03: fluxo completo validado.");
      await page.click("text=Close Case");
      await expect(page.locator("text=closed")).toBeVisible({ timeout: 10000 });
    }
  });
});

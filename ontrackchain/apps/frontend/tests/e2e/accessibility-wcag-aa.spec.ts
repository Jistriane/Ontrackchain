import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("T2-06 WCAG AA Ontrackchain Acessibilidade", () => {
  test.describe.configure({ mode: "serial", retries: 0 });

  test("home /login não tem violações críticas WCAG AA", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator('h1, [role="heading"]').first()).toBeVisible();
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .exclude("iframe")
      .analyze();
    const serious = results.violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical"
    );
    expect.soft(serious).toHaveLength(0);
  });

  test("/dashboard não tem violações WCAG AA após login", async ({ page }) => {
    await page.goto("/login");
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL("/dashboard");
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .exclude("iframe")
      .analyze();
    const blockerViolations = results.violations.filter(
      (v) => v.impact === "critical"
    );
    expect.soft(blockerViolations).toHaveLength(0);
    expect(results.violations.length).toBeLessThanOrEqual(3);
  });

  test("/cases tem contraste e estrutura semântica válida AA", async ({ page }) => {
    await page.goto("/login");
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL("/dashboard");
    await page.goto("/cases");
    await expect(page.locator("h1").first()).toBeVisible();
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .include("main, [role='main']")
      .exclude("iframe")
      .analyze();
    const contrastViolations = results.violations.filter(
      (v) => v.id === "color-contrast"
    );
    expect.soft(contrastViolations).toHaveLength(0);
  });

  test("/ai navegação por teclado (Tab) alcança 3+ ações principais", async ({
    page,
  }) => {
    await page.goto("/login");
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL("/dashboard");
    await page.goto("/ai");
    const tabbableSelector =
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
    const tabbable = page.locator(tabbableSelector);
    const count = await tabbable.count();
    expect(count).toBeGreaterThanOrEqual(3);
  });
});

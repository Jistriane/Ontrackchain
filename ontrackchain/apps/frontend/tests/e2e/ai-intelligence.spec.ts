import { test, expect } from "@playwright/test";

test.describe("AI Intelligence Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL("/dashboard");
  });

  test("should navigate to AI page", async ({ page }) => {
    await page.goto("/ai");
    await expect(page.locator("h1")).toContainText("AI Intelligence");
  });

  test("should show explain tab by default", async ({ page }) => {
    await page.goto("/ai");
    await expect(page.locator("text=Explain Decision")).toBeVisible();
  });

  test("should switch between tabs", async ({ page }) => {
    await page.goto("/ai");
    
    // Click Graph Analysis tab
    await page.click("text=Graph Analysis");
    await expect(page.locator("text=Blockchain Address")).toBeVisible();
    
    // Click Case Insights tab
    await page.click("text=Case Insights");
    await expect(page.locator("text=Case ID")).toBeVisible();
  });

  test("should explain a risk score decision", async ({ page }) => {
    await page.goto("/ai");
    
    // Fill in case ID
    await page.fill('input[placeholder="Enter case ID"]', "CASE-2026-0156");
    
    // Select decision type
    await page.selectOption("select", "risk_score");
    
    // Click explain button
    await page.click("text=Explain Decision");
    
    // Wait for results
    await expect(page.locator("text=Confidence:")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Reasoning Steps:")).toBeVisible();
  });

  test("should analyze a blockchain address", async ({ page }) => {
    await page.goto("/ai");
    
    // Click Graph Analysis tab
    await page.click("text=Graph Analysis");
    
    // Fill in address
    await page.fill('input[placeholder="0x..."]', "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae");
    
    // Select chain
    await page.selectOption("select", "ethereum");
    
    // Click analyze button
    await page.click("text=Analyze Graph");
    
    // Wait for results
    await expect(page.locator("text=Nodes:")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Edges:")).toBeVisible();
  });
});

test.describe("Case Management Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL("/dashboard");
  });

  test("should navigate to cases page", async ({ page }) => {
    await page.goto("/cases");
    await expect(page.locator("h1")).toContainText("Case Management");
  });

  test("should show case metrics", async ({ page }) => {
    await page.goto("/cases");
    await expect(page.locator("text=Total Cases")).toBeVisible();
    await expect(page.locator("text=Open Cases")).toBeVisible();
    await expect(page.locator("text=Closed Cases")).toBeVisible();
  });

  test("should show case list", async ({ page }) => {
    await page.goto("/cases");
    await expect(page.locator("text=Investigation Cases")).toBeVisible();
    await expect(page.locator("text=+ New Case")).toBeVisible();
  });

  test("should create a new case", async ({ page }) => {
    await page.goto("/cases");
    
    // Click new case button
    await page.click("text=+ New Case");
    
    // Fill in case details
    await page.fill('input[placeholder="Case title"]', "Test Investigation Case");
    await page.fill('textarea[placeholder="Case description"]', "This is a test case for E2E testing");
    
    // Select priority and category
    await page.selectOption("select >> nth=0", "high");
    await page.selectOption("select >> nth=1", "aml");
    
    // Click create button
    await page.click("text=Create Case");
    
    // Wait for case to appear in list
    await expect(page.locator("text=Test Investigation Case")).toBeVisible({ timeout: 10000 });
  });

  test("should view case details", async ({ page }) => {
    await page.goto("/cases");
    
    // Click on first case
    await page.click(".otc-panel >> nth=0");
    
    // Wait for details to appear
    await expect(page.locator("text=Case:")).toBeVisible();
    await expect(page.locator("text=Close")).toBeVisible();
  });
});

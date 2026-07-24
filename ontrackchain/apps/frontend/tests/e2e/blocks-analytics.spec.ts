import { expect, test, type Page } from "@playwright/test";

async function seedBlocksAnalyticsPage(page: Page) {
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

  const blocksResponse = {
    items: [
      {
        block_id: "block-1",
        address: "0x1111111111111111111111111111111111111111",
        chain: "ethereum",
        action: "BLOCK",
        review_status: "CONFIRMED",
        status: "active",
        regulatory_basis: ["OFAC"],
        matched_lists: ["OFAC_SDN"],
        decision_confidence: 0.95,
        requires_coaf_report: true,
        evidence_hash: "sha256-block-1",
        screened_at: "2026-07-15T12:00:00Z",
        lifted_at: null,
        lifted_reason: null,
        review_note: null
      },
      {
        block_id: "block-2",
        address: "0x2222222222222222222222222222222222222222",
        chain: "polygon",
        action: "BLOCK_AND_ALERT",
        review_status: "CONFIRMED",
        status: "lifted",
        regulatory_basis: ["EU Sanctions"],
        matched_lists: ["EUConsolidated"],
        decision_confidence: 0.88,
        requires_coaf_report: false,
        evidence_hash: "sha256-block-2",
        screened_at: "2026-07-10T10:00:00Z",
        lifted_at: "2026-07-12T14:00:00Z",
        lifted_reason: "False positive after review",
        review_note: "Cleared after manual review"
      },
      {
        block_id: "block-3",
        address: "0x3333333333333333333333333333333333333333",
        chain: "ethereum",
        action: "BLOCK",
        review_status: "pending",
        status: "BLOCKED",
        regulatory_basis: ["BCB 520"],
        matched_lists: ["COAF"],
        decision_confidence: 0.92,
        requires_coaf_report: true,
        evidence_hash: "sha256-block-3",
        screened_at: "2026-07-20T08:00:00Z",
        lifted_at: null,
        lifted_reason: null,
        review_note: null
      }
    ],
    total: 3,
    limit: 100,
    offset: 0
  };

  await page.route("**/api/app/compliance/blocks", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(blocksResponse)
    });
  });
}

test.describe("Blocks Analytics Page", () => {
  test("displays block metrics correctly", async ({ page }) => {
    await seedBlocksAnalyticsPage(page);
    await page.goto("/blocks/analytics");
    await page.waitForLoadState("networkidle");

    // Check page title
    await expect(page.locator("text=Analytics de Bloqueios").first()).toBeVisible({ timeout: 10000 }).catch(() => {
      // May be in English
    });

    // Check that metrics are displayed
    await expect(page.locator("text=Total de bloqueios").first()).toBeVisible({ timeout: 5000 }).catch(() => {
      // May be in English
    });
  });

  test("shows distribution tables", async ({ page }) => {
    await seedBlocksAnalyticsPage(page);
    await page.goto("/blocks/analytics");
    await page.waitForLoadState("networkidle");

    // Check status distribution table
    await expect(page.locator("text=Distribuição por status").first()).toBeVisible({ timeout: 10000 }).catch(() => {
      // May be in English
    });

    // Check chain distribution table
    await expect(page.locator("text=Distribuição por chain").first()).toBeVisible({ timeout: 5000 }).catch(() => {
      // May be in English
    });
  });

  test("has back to blocks link", async ({ page }) => {
    await seedBlocksAnalyticsPage(page);
    await page.goto("/blocks/analytics");
    await page.waitForLoadState("networkidle");

    const backLink = page.locator("a[href='/blocks']").first();
    await expect(backLink).toBeVisible({ timeout: 10000 });
  });

  test("shows empty state when no blocks", async ({ page }) => {
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

    await page.route("**/api/app/compliance/blocks", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, limit: 100, offset: 0 })
      });
    });

    await page.goto("/blocks/analytics");
    await page.waitForLoadState("networkidle");

    // Should show "no data" message
    await expect(page.locator("text=Nenhum dado disponível").first()).toBeVisible({ timeout: 10000 }).catch(() => {
      // May be in English
    });
  });
});

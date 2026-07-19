import { expect, test, type Page, type Route } from "@playwright/test";

const SANCTIONS_ADDRESS = "0x1111111111111111111111111111111111111111";

async function seedSanctionsPage(page: Page, role: string) {
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

  await page.route("**/api/app/auth/context", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        org_id: "org-e2e",
        user_id: "user-e2e",
        linked_user_id: "linked-e2e",
        role,
        plan: "professional",
        auth_method: "jwt",
        mfa_mode: "totp",
        mfa_provider_homologated: "true"
      })
    });
  });

  await page.route("**/api/app/operations/work-items?module=sanctions&resource_type=sanctions_screening&limit=100", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ data: [] })
    });
  });

  await page.route("**/api/app/operations/work-items", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "ws-sanctions-rbac-01",
        module: "sanctions",
        resource_type: "sanctions_screening",
        resource_id: "resource-sanctions-rbac-01",
        queue_status: "UNDER_REVIEW",
        priority: "high",
        due_at: null,
        note: "seed",
        owner_user_id: null,
        case_id: "55555555-5555-4555-8555-555555555555",
        metadata: {
          workspace_id: "0x1111111111111111111111111111111111111111:ethereum:2026-07-15T12:00:00Z",
          address: "0x1111111111111111111111111111111111111111",
          chain: "ethereum",
          lists: ["OFAC", "UN"],
          provider: "sanctions_lists_cache",
          provider_status: "live",
          capability_status: "live",
          matched_lists: ["OFAC"],
          hit: true,
          entity_name: "Entity QA",
          designation_date: "2026-01-01",
          checked_at: "2026-07-15T12:00:00Z",
          local_workspace_status: "UNDER_REVIEW"
        },
        last_activity_at: "2026-07-15T12:00:00Z",
        updated_at: "2026-07-15T12:00:00Z"
      })
    });
  });
}

async function submitSanctionsCheck(page: Page) {
  await page.getByTestId("sanctions-address").fill(SANCTIONS_ADDRESS);
  await page.getByTestId("sanctions-chain").selectOption("ethereum");
  await expect(page.getByTestId("sanctions-check-btn")).toBeEnabled();
  await page.getByTestId("sanctions-check-btn").click();
}

test.describe("sanctions RBAC", () => {
  test("viewer nao recebe o CTA de sanctions-check", async ({ page }) => {
    await seedSanctionsPage(page, "VIEWER");
    await page.goto("/sanctions");

    await expect(page.getByTestId("sanctions-check-btn")).toHaveCount(0);
    await expect(page.getByTestId("sanctions-check-restricted")).toContainText(
      "A verificação de sanções está oculta nesta sessão porque o papel atual não possui autorização operacional de compliance."
    );
  });

  test("analyst recebe erro semantico quando o BFF recusa a verificacao", async ({ page }) => {
    await seedSanctionsPage(page, "ANALYST");
    let sanctionsCheckHits = 0;
    await page.route("**/api/app/compliance/sanctions-check**", async (route: Route) => {
      sanctionsCheckHits += 1;
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "sanctions_check_role_required" })
      });
    });

    await page.goto("/sanctions");
    await submitSanctionsCheck(page);
    await expect.poll(() => sanctionsCheckHits).toBe(1);

    await expect(page.getByText("A verificação de sanções exige papel operacional de compliance: ADMIN, ANALYST ou COMPLIANCE_OFFICER.")).toBeVisible();
  });

  test("compliance officer continua conseguindo executar o screening", async ({ page }) => {
    await seedSanctionsPage(page, "COMPLIANCE_OFFICER");
    let sanctionsCheckHits = 0;
    await page.route("**/api/app/compliance/sanctions-check**", async (route: Route) => {
      sanctionsCheckHits += 1;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          address: SANCTIONS_ADDRESS,
          chain: "ethereum",
          provider: "sanctions_lists_cache",
          provider_status: "live",
          degraded_reason: null,
          capability_status: "live",
          lists: ["OFAC", "UN"],
          hit: true,
          matched_lists: ["OFAC"],
          entity_name: "Entity QA",
          designation_date: "2026-01-01",
          checked_at: "2026-07-15T12:00:00Z"
        })
      });
    });

    await page.goto("/sanctions");
    await submitSanctionsCheck(page);
    await expect.poll(() => sanctionsCheckHits).toBe(1);

    await expect(page.getByText("HIT detectado: revisão imediata recomendada.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Marcar em revisão" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Escalar" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Marcar clear" })).toBeVisible();
  });

  test("alias OTK_COMPLIANCE_OFFICER continua conseguindo executar o screening", async ({ page }) => {
    await seedSanctionsPage(page, "OTK_COMPLIANCE_OFFICER");
    let sanctionsCheckHits = 0;
    await page.route("**/api/app/compliance/sanctions-check**", async (route: Route) => {
      sanctionsCheckHits += 1;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          address: SANCTIONS_ADDRESS,
          chain: "ethereum",
          provider: "sanctions_lists_cache",
          provider_status: "live",
          degraded_reason: null,
          capability_status: "live",
          lists: ["OFAC", "UN"],
          hit: true,
          matched_lists: ["OFAC"],
          entity_name: "Entity QA",
          designation_date: "2026-01-01",
          checked_at: "2026-07-15T12:00:00Z"
        })
      });
    });

    await page.goto("/sanctions");
    await submitSanctionsCheck(page);
    await expect.poll(() => sanctionsCheckHits).toBe(1);

    await expect(page.getByText("HIT detectado: revisão imediata recomendada.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Marcar em revisão" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Escalar" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Marcar clear" })).toBeVisible();
  });
});

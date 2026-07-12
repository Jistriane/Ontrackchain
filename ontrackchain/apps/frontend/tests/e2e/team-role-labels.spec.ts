import { expect, test, type Page, type Route } from "@playwright/test";

async function seedFrontendAuth(page: Page) {
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
        role: "ADMIN",
        plan: "professional",
        auth_method: "jwt",
        mfa_mode: "totp",
        mfa_provider_homologated: "true"
      })
    });
  });
}

test.describe("team role labels", () => {
  test("renderiza roles com label amigavel e permite busca pelo label traduzido", async ({ page }) => {
    await seedFrontendAuth(page);
    await page.goto("/team");

    await expect(page.locator('[data-testid="team-role-select"] option[value="COMPLIANCE_OFFICER"]')).toHaveText(
      "Oficial de Compliance (COMPLIANCE_OFFICER)"
    );

    await page.locator('input[type="email"]').fill("compliance@ontrackchain.local");
    await page.locator('[data-testid="team-role-select"]').selectOption("COMPLIANCE_OFFICER");
    await page.getByRole("button", { name: "Adicionar" }).click();

    const row = page.locator('[data-testid="team-row"]').first();
    await expect(row).toContainText("Oficial de Compliance (COMPLIANCE_OFFICER)");
    await expect(row.getByTestId("team-row-status")).toContainText("convidado");
    await expect(row.getByTestId("team-row-updated")).not.toContainText(/T\d{2}:\d{2}:\d{2}\.\d{3}Z/);

    await page.locator('[data-testid="team-search-input"]').fill("oficial");
    await expect(page.locator('[data-testid="team-row"]')).toHaveCount(1);
    await expect(page.locator('[data-testid="team-row"]').first()).toContainText("compliance@ontrackchain.local");
  });

  test("exibe os novos papeis canonicos incrementais no seletor", async ({ page }) => {
    await seedFrontendAuth(page);
    await page.goto("/team");

    await expect(page.locator('[data-testid="team-role-select"] option[value="REVIEWER"]')).toHaveText("Revisor (REVIEWER)");
    await expect(page.locator('[data-testid="team-role-select"] option[value="BILLING_ADMIN"]')).toHaveText(
      "Administrador de Billing (BILLING_ADMIN)"
    );
  });
});

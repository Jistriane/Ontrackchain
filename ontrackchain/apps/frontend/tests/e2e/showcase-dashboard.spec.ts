import { expect, test } from "@playwright/test";

import { loginIntoShowcase, showcaseOnly } from "./showcase-helpers";

test.describe("standalone showcase dashboard", () => {
  test.skip(!showcaseOnly, "requer TEST_SHOWCASE_MODE=true");

  test("healthz expõe o modelo standalone showcase e não exige backend interno", async ({ request }) => {
    const response = await request.get("/api/healthz");
    const payload = (await response.json()) as {
      status: string;
      deploymentModel: string;
      standaloneShowcaseMode: boolean;
      missingEnvKeys: string[];
    };

    expect(payload.deploymentModel).toBe("render-frontend-standalone-showcase");
    expect(payload.standaloneShowcaseMode).toBe(true);
    expect(payload.missingEnvKeys).not.toContain("INTERNAL_API_BASE_URL");
    expect(payload.missingEnvKeys).not.toContain("INTERNAL_AUTH_BASE_URL");
    expect(payload.missingEnvKeys).not.toContain("INTERNAL_KEYCLOAK_BASE_URL");
    expect(payload.missingEnvKeys).not.toContain("NEXT_PUBLIC_API_BASE_URL");

    if (response.ok()) {
      expect(payload.status).toBe("ok");
      expect(payload.missingEnvKeys).toEqual([]);
    } else {
      expect(payload.status).toBe("degraded");
      expect(payload.missingEnvKeys).toEqual(
        expect.arrayContaining([
          "APP_ENV",
          "AUTH_MODE",
          "NEXT_PUBLIC_APP_ENV",
          "NEXT_PUBLIC_AUTH_MODE",
          "NEXT_PUBLIC_FRONTEND_STANDALONE_SHOWCASE_MODE"
        ])
      );
    }
  });

  test("dashboard seeded expõe dados operacionais e atalhos funcionais", async ({ page }) => {
    await loginIntoShowcase(page);

    await expect(page.getByRole("heading", { name: "Painel Compliance" })).toBeVisible();
    await expect(page.getByTestId("user-menu")).toContainText("Standalone Showcase");
    await expect(page.getByText("Watchlists", { exact: true })).toBeVisible();
    await expect(page.getByText("Créditos disponíveis", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Casos recentes" })).toBeVisible();
    await expect(page.getByText("Páginas de acompanhamento e classificação")).toBeVisible();
    await expect(page.getByTestId("dashboard-quick-action-alerts")).toBeVisible();
    await expect(page.getByTestId("dashboard-quick-action-monitoring")).toBeVisible();
    await expect(page.getByTestId("dashboard-quick-action-reports")).toBeVisible();
    await expect(page.getByTestId("dashboard-quick-action-evidence")).toBeVisible();
    await expect(page.getByTestId("dashboard-quick-action-billing")).toBeVisible();
    await expect(page.getByTestId("dashboard-quick-action-team")).toBeVisible();

    await page.getByTestId("dashboard-quick-action-alerts").click();
    await expect(page).toHaveURL(/\/alerts\?status=firing&triage_status=pending$/);

    await page.goto("/dashboard");
    await page.getByTestId("dashboard-quick-action-monitoring").click();
    await expect(page).toHaveURL(/\/monitoring$/);

    await page.goto("/dashboard");
    await page.getByTestId("dashboard-quick-action-reports").click();
    await expect(page).toHaveURL(/\/reports$/);

    await page.goto("/dashboard");
    await page.getByTestId("dashboard-quick-action-evidence").click();
    await expect(page).toHaveURL(/\/evidence$/);

    await page.goto("/dashboard");
    await page.getByTestId("dashboard-quick-action-billing").click();
    await expect(page).toHaveURL(/\/billing$/);

    await page.goto("/dashboard");
    await page.getByTestId("dashboard-quick-action-team").click();
    await expect(page).toHaveURL(/\/team$/);
  });
});

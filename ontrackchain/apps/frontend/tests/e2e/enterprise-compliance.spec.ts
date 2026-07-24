import { test, expect } from "@playwright/test";

import { seedFrontendAuth } from "./seed-frontend-auth";

test.describe("enterprise compliance", () => {
  test("renderiza cockpit enterprise com modulos P4-P7", async ({ page }) => {
    await seedFrontendAuth(page);
    await page.goto("/enterprise-compliance");

    await expect(page.getByText("Cockpit Enterprise")).toBeVisible();
    await expect(page.getByText("P4: Bridge & Mixer Risk")).toBeVisible();
    await expect(page.getByText("P5: Auto-Filing COAF")).toBeVisible();
    await expect(page.getByText("P6: Travel Rule")).toBeVisible();
    await expect(page.getByText("P7: AI Legal Dossier")).toBeVisible();
  });

  test("P4 analise de mixer retorna risk score alto para endereco Tornado", async ({ page }) => {
    await seedFrontendAuth(page);
    await page.goto("/enterprise-compliance");

    await page.getByText("P4: Bridge & Mixer Risk").click();
    await page.getByText("Analisar Risco de Mixer").click();

    await expect(page.getByText("Score de Risco P4: 100/100 | Recomendação: REJECT")).toBeVisible();
  });

  test("P5 gera lote SISCOAF com protocolo", async ({ page }) => {
    await seedFrontendAuth(page);
    await page.goto("/enterprise-compliance");

    await page.getByText("P5: Auto-Filing COAF").click();
    await page.getByText("Gerar Lote de Remessa").click();

    await expect(page.getByText("Lote Gerado:")).toBeVisible();
    await expect(page.getByText("Protocolo SISCOAF:")).toBeVisible();
  });

  test("P6 valida travel rule VASP", async ({ page }) => {
    await seedFrontendAuth(page);
    await page.goto("/enterprise-compliance");

    await page.getByText("P6: Travel Rule").click();
    await page.getByText("Validar Transferência VASP").click();

    await expect(page.getByText("Status: ALLOW_TRANSFER")).toBeVisible();
    await expect(page.getByText("Hash IVMS101:")).toBeVisible();
  });

  test("P7 gera parecer forense", async ({ page }) => {
    await seedFrontendAuth(page);
    await page.goto("/enterprise-compliance");

    await page.getByText("P7: AI Legal Dossier").click();
    await page.getByText("Gerar Parecer Forense").click();

    await expect(page.locator(".otc-message").filter({ hasText: "DOSSIÊ FORENSE AUTOMATIZADO" })).toBeVisible();
  });
});

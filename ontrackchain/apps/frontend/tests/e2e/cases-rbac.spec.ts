import { expect, test, type Page, type Route } from "@playwright/test";

import { seedFrontendAuth } from "./seed-frontend-auth";

async function seedCasesPageAuth(
  page: Page,
  role: string,
  options?: {
    authMethod?: string;
    mfaMode?: string;
    mfaProviderHomologated?: string;
    twoFactor?: string;
  }
) {
  await seedFrontendAuth(page, {
    role,
    authMethod: options?.authMethod,
    mfaMode: options?.mfaMode,
    mfaProviderHomologated: options?.mfaProviderHomologated,
    secondFactor: options?.twoFactor
  });
}

async function seedCaseReadApis(page: Page) {
  await page.route("**/api/app/investigation/status?case_id=case-rbac-01", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "completed" })
    });
  });

  await page.route("**/api/app/report-types?include_unavailable=true&include_deprecated=false", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        types: [
          { canonical: "technical_basic", label: "Technical Basic", available: true, cost_credits: 10 },
          { canonical: "legal_report", label: "Legal Report", available: true, cost_credits: 30 }
        ]
      })
    });
  });
}

test.describe("cases RBAC", () => {
  test("viewer nao recebe ctas de geração e export sensível no case", async ({ page }) => {
    await seedCasesPageAuth(page, "VIEWER");
    await seedCaseReadApis(page);

    await page.goto("/cases/case-rbac-01");

    await expect(page.getByTestId("case-report-generate-restricted")).toContainText(
      "A geração de relatórios deste case está oculta nesta sessão porque a role atual não possui papel operacional ADMIN/ANALYST."
    );
    await expect(page.getByTestId("case-export-evidence-restricted")).toContainText(
      "A exportação do bundle de evidências do case está oculta nesta sessão porque a role atual não possui leitura privilegiada ADMIN/AUDITOR."
    );
    await expect(page.getByTestId("download-report-btn")).toHaveCount(0);
    await expect(page.getByTestId("case-export-evidence-btn")).toHaveCount(0);
  });

  test("auditor mantém export sensível mas não gera relatório do case", async ({ page }) => {
    let exportCalled = false;
    await seedCasesPageAuth(page, "AUDITOR");
    await seedCaseReadApis(page);
    await page.route("**/api/app/audit/evidence-export", async (route: Route) => {
      exportCalled = true;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        headers: {
          "content-disposition": 'attachment; filename="case-rbac-evidence.json"'
        },
        body: JSON.stringify({ exported: true })
      });
    });

    await page.goto("/cases/case-rbac-01");

    await expect(page.getByTestId("case-report-generate-restricted")).toContainText(
      "A geração de relatórios deste case está oculta nesta sessão porque a role atual não possui papel operacional ADMIN/ANALYST."
    );
    await expect(page.getByTestId("download-report-btn")).toHaveCount(0);
    await expect(page.getByTestId("case-export-evidence-btn")).toBeVisible();
    await page.getByTestId("case-export-evidence-btn").click();
    await expect(page.getByText("Bundle de evidências exportado com sucesso.")).toBeVisible();
    expect(exportCalled).toBeTruthy();
  });

  test("analyst pode gerar legal_report, mas o download fica oculto sem strong auth administrativo", async ({ page }) => {
    await seedCasesPageAuth(page, "ANALYST");
    await seedCaseReadApis(page);
    await page.route("**/api/app/reports/generate", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          report_id: "rep-legal-01",
          created_at: "2026-07-15T12:00:00.000Z",
          report_type: "legal_report",
          file_hash_sha256: "abc123legalhash",
          content_type: "application/pdf"
        })
      });
    });

    await page.goto("/cases/case-rbac-01");
    await page.getByTestId("case-report-type-select").selectOption("legal_report");
    await page.getByTestId("download-report-btn").click();

    await expect(page.getByTestId("report-status")).toContainText("completed");
    await expect(page.getByTestId("stored-report-hash")).toContainText("abc123legalhash");
    await expect(page.getByTestId("case-report-download-restricted")).toContainText(
      "O download de legal_report está oculto nesta sessão porque exige JWT local com papel ADMIN e segundo fator válido, ou MFA externo homologado com trilho JWT."
    );
    await expect(page.getByTestId("download-link")).toHaveCount(0);
  });
});

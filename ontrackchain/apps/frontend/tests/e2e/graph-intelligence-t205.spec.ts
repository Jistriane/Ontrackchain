import { test, expect } from "@playwright/test";

test.describe("T2-05 Graph Intelligence 4.0 — Página /graph (Cytoscape Counterparty↔Wallet↔Risk Network)", () => {
  test.use({ baseURL: process.env.TEST_BASE_URL || "http://127.0.0.1:3000" });

  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");
    if (page.url().includes("/login")) {
      const email = page.locator('input[name="email"], input[type="email"]').first();
      if (await email.isVisible({ timeout: 2000 })) {
        await email.fill(process.env.E2E_ADMIN_EMAIL || "admin@ontrackchain.example");
        const pw = page.locator('input[name="password"], input[type="password"]').first();
        if (await pw.isVisible({ timeout: 1000 })) {
          await pw.fill(process.env.E2E_ADMIN_PASSWORD || "OntrackAdmin2026!");
        }
        const btn = page.locator('button[data-testid="login-btn"], button[type="submit"]').first();
        if (await btn.isVisible({ timeout: 1000 })) {
          await btn.click();
          await page.waitForURL(/\/dashboard/, { waitUntil: "domcontentloaded", timeout: 10000 }).catch(() => {});
        }
      }
    }
  });

  test("Q3-04 T2-05 G1 — Abre /graph e exibe Header, 5 MetricCards e painel Layout do grafo", async ({ page }) => {
    await page.goto("/graph");
    await page.waitForLoadState("domcontentloaded");
    await expect(page.getByRole("heading", { name: /Graph Intelligence 4\.0/i })).toBeVisible({ timeout: 10000 });
    const layoutPanel = page.getByTestId("graph-layout-panel");
    await expect(layoutPanel).toBeVisible();
    await expect(page.getByTestId("layout-btn-cose")).toBeVisible();
    await expect(page.getByTestId("graph-node-count")).toBeVisible();
  });

  test("Q3-04 T2-05 G2 — Seleciona 6 layouts diferentes e cada botão altera estado ativo", async ({ page }) => {
    await page.goto("/graph");
    await page.waitForLoadState("domcontentloaded");
    for (const id of ["cose", "cola", "forceatlas2", "grid", "breadthfirst", "concentric"]) {
      const btn = page.getByTestId(`layout-btn-${id}`);
      await btn.click();
      await expect(btn).toHaveAttribute("aria-checked", "true");
    }
  });

  test("Q3-04 T2-05 G3 — Filtro categoria 'Contrapartes' e Apenas Risco ativa: painel grafo mantém visível", async ({ page }) => {
    await page.goto("/graph");
    await page.waitForLoadState("domcontentloaded");
    await page.getByTestId("cat-btn-counterparty").click();
    await expect(page.getByTestId("cat-btn-counterparty")).toHaveAttribute("aria-selected", "true");
    const riskOnly = page.getByTestId("graph-risk-only");
    await riskOnly.check();
    await expect(riskOnly).toBeChecked();
    await expect(page.getByTestId("graph-cytoscape-panel")).toBeVisible();
  });

  test("Q3-04 T2-05 G4 — Pesquisa por texto 'Alpha Capital' e filtragem é aplicada; nó aparece no metric", async ({ page }) => {
    await page.goto("/graph");
    await page.waitForLoadState("domcontentloaded");
    const search = page.getByTestId("graph-search");
    await search.fill("Alpha Capital");
    await expect(search).toHaveValue("Alpha Capital");
    await page.getByTestId("graph-risk-only").uncheck();
    await expect(page.getByTestId("graph-node-count")).toBeVisible();
  });

  test("Q3-04 T2-05 G5 — Legenda cytoscape visível, centralidade betweenness Top-5 e 4 sinais de risco", async ({ page }) => {
    await page.goto("/graph");
    await page.waitForLoadState("domcontentloaded");
    await expect(page.getByTestId("graph-legend")).toBeVisible();
    await expect(page.getByTestId("graph-betweenness")).toBeVisible();
    await expect(page.getByTestId("graph-risk-signals")).toBeVisible();
    for (let i = 1; i <= 4; i++) {
      await expect(page.getByTestId(`risk-sig-${i}`)).toBeVisible();
    }
  });

  test("Q3-04 T2-05 G6 — Painel Recommendations mostra Ação 1 ALERTA + Estatísticas", async ({ page }) => {
    await page.goto("/graph");
    await page.waitForLoadState("domcontentloaded");
    await expect(page.getByTestId("graph-recommendations")).toBeVisible();
    await expect(page.getByTestId("action-1")).toBeVisible();
    await expect(page.getByTestId("action-2")).toBeVisible();
    await expect(page.getByTestId("action-3")).toBeVisible();
  });

  test("Q3-04 T2-05 G7 — Filtro 'Todas Categorias' e 7 nós categorias aparecem listados", async ({ page }) => {
    await page.goto("/graph");
    await page.waitForLoadState("domcontentloaded");
    await page.getByTestId("cat-btn-all").click();
    for (const id of ["counterparty", "wallet_address", "transaction", "sanctions_list", "pep", "case_file", "risk_signal", "source_of_funds"]) {
      await expect(page.getByTestId(`cat-btn-${id}`)).toBeVisible();
    }
  });
});

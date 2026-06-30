import { test, expect } from "@playwright/test";

test("home renderiza com catálogos principais", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "OnTrackChain" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Tipos de Relatório" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Compliance" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Monitoring" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Fluxo Canônico" })).toBeVisible();
  await expect(page.getByText("Nenhuma sessão autenticada detectada.")).toBeVisible();
});

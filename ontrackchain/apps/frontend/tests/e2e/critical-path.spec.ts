import { test, expect, type APIRequestContext, type Page } from "@playwright/test";
import crypto from "crypto";
import fs from "fs";

import { loginWithOidc, readAuthConfig } from "./oidc";

const API_KEY = process.env.ONTRACKCHAIN_API_KEY || "otc_live_demo_key";
const OIDC_ADMIN_USER = process.env.ONTRACKCHAIN_OIDC_ADMIN_USER || "jibso@ontrackchain.com";
const OIDC_ADMIN_PASSWORD = process.env.ONTRACKCHAIN_OIDC_ADMIN_PASSWORD || "JIBSOPass123!";
const OIDC_ANALYST_USER = process.env.ONTRACKCHAIN_OIDC_ANALYST_USER || "analyst@ontrackchain.com";
const OIDC_ANALYST_PASSWORD = process.env.ONTRACKCHAIN_OIDC_ANALYST_PASSWORD || "AnalystPass123!";

type QuoteResponse = {
  quote_id: string;
};

async function loginAsAnalyst(page: Page, request: APIRequestContext, baseURL: string | undefined) {
  const config = await readAuthConfig(request);
  test.skip(config.effective_auth_mode !== "oidc", "Fluxo OIDC habilitado apenas quando o ambiente estiver em AUTH_MODE=oidc.");

  await loginWithOidc(page, request, baseURL, {
    username: OIDC_ANALYST_USER,
    password: OIDC_ANALYST_PASSWORD
  });

  await expect(page).toHaveURL(/\/dashboard$/);

  const cookies = await page.context().cookies();
  expect(cookies.some((cookie) => cookie.name === "otc_token" && Boolean(cookie.value))).toBeTruthy();
  expect(
    cookies.some(
      (cookie) =>
        cookie.name === "otc_2fa" &&
        ["ok", "managed_externally", "managed_externally_homologated"].includes(cookie.value)
    )
  ).toBeTruthy();

  const loginButtonVisible = await page.getByTestId("login-btn").isVisible().catch(() => false);
  expect(loginButtonVisible).toBeFalsy();
}

async function loginAsAdmin(page: Page, request: APIRequestContext, baseURL: string | undefined) {
  const config = await readAuthConfig(request);
  test.skip(config.effective_auth_mode !== "oidc", "Fluxo OIDC habilitado apenas quando o ambiente estiver em AUTH_MODE=oidc.");

  await loginWithOidc(page, request, baseURL, {
    username: OIDC_ADMIN_USER,
    password: OIDC_ADMIN_PASSWORD
  });

  await expect(page).toHaveURL(/\/dashboard$/);
}

async function sha256File(path: string) {
  const buf = fs.readFileSync(path);
  const hash = crypto.createHash("sha256");
  hash.update(new Uint8Array(buf));
  return hash.digest("hex");
}

async function readNumericText(locator: ReturnType<Page["locator"]>) {
  await expect(locator).not.toHaveText("loading");
  const raw = (await locator.textContent()) ?? "";
  const value = parseFloat(raw);
  expect(Number.isFinite(value)).toBeTruthy();
  return value;
}

test("login OIDC do analyst funciona end-to-end", async ({ page, request, baseURL }) => {
  await loginAsAnalyst(page, request, baseURL);
});

test("investigação é submetida e entra em processamento", async ({ page, request, baseURL }) => {
  await loginAsAnalyst(page, request, baseURL);
  await page.goto("/investigate");

  await page.fill('[data-testid="wallet-address"]', "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045");
  await page.selectOption('[data-testid="chain-select"]', "ethereum");
  await page.selectOption('[data-testid="report-type"]', "technical_basic");
  await page.click('[data-testid="start-investigation-btn"]');

  await expect(page.locator('[data-testid="quote-preview"]')).toBeVisible();
  const quoteCredits = await readNumericText(page.locator('[data-testid="quote-credits"]'));
  expect(quoteCredits).toBeGreaterThan(0);

  await page.click('[data-testid="confirm-investigation-btn"]');
  await expect(page).toHaveURL(/\/cases\/[0-9a-f-]{36}/);
  await expect(page.locator('[data-testid="case-status"]')).toContainText(/queued|processing|completed/i);
});

test("investigação evolui para completed via worker assíncrono", async ({ page, request, baseURL }) => {
  await loginAsAnalyst(page, request, baseURL);
  await page.goto("/investigate");

  await page.fill('[data-testid="wallet-address"]', "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb");
  await page.selectOption('[data-testid="chain-select"]', "ethereum");
  await page.selectOption('[data-testid="report-type"]', "technical_basic");
  await page.click('[data-testid="start-investigation-btn"]');
  await expect(page.locator('[data-testid="quote-preview"]')).toBeVisible();
  await page.click('[data-testid="confirm-investigation-btn"]');

  await expect(page).toHaveURL(/\/cases\/[0-9a-f-]{36}/);
  await expect(page.locator('[data-testid="case-status"]')).toContainText(/queued|processing|completed/i);
  await expect(page.locator('[data-testid="case-status"]')).toContainText(/completed/i, { timeout: 20000 });
});

test("relatório PDF pode ser baixado após geração", async ({ page, request, baseURL }) => {
  await loginAsAnalyst(page, request, baseURL);
  await page.goto("/investigate");

  await page.fill('[data-testid="wallet-address"]', "0x9999999999999999999999999999999999999999");
  await page.selectOption('[data-testid="chain-select"]', "ethereum");
  await page.selectOption('[data-testid="report-type"]', "technical_basic");
  await page.click('[data-testid="start-investigation-btn"]');
  await expect(page.locator('[data-testid="quote-preview"]')).toBeVisible();
  await page.click('[data-testid="confirm-investigation-btn"]');
  await expect(page).toHaveURL(/\/cases\/[0-9a-f-]{36}/);

  await page.click('[data-testid="download-report-btn"]');
  await expect(page.locator('[data-testid="download-link"]')).toBeVisible();
  const storedHash = await page.locator('[data-testid="stored-report-hash"]').textContent();
  expect(storedHash).toBeTruthy();

  const downloadPromise = page.waitForEvent("download");
  await page.click('[data-testid="download-link"]');
  const download = await downloadPromise;
  expect(download.suggestedFilename().endsWith(".pdf")).toBeTruthy();
  const path = await download.path();
  expect(path).toBeTruthy();

  const downloadedHash = await sha256File(path!);
  expect(downloadedHash).toBe(storedHash);
});

test("créditos são debitados corretamente após investigação", async ({ page, request, baseURL }) => {
  const config = await readAuthConfig(request);
  test.skip(config.effective_auth_mode !== "oidc", "Fluxo OIDC habilitado apenas quando o ambiente estiver em AUTH_MODE=oidc.");

  await loginWithOidc(page, request, baseURL, {
    username: OIDC_ADMIN_USER,
    password: OIDC_ADMIN_PASSWORD
  });

  await page.goto("/billing");
  const initialCredits = await readNumericText(page.locator('[data-testid="credits-balance"]'));

  await page.goto("/investigate");
  await page.fill('[data-testid="wallet-address"]', "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");
  await page.selectOption('[data-testid="chain-select"]', "ethereum");
  await page.selectOption('[data-testid="report-type"]', "technical_basic");
  await page.click('[data-testid="start-investigation-btn"]');
  await expect(page.locator('[data-testid="quote-preview"]')).toBeVisible();
  const quoteCredits = await readNumericText(page.locator('[data-testid="quote-credits"]'));
  await page.click('[data-testid="confirm-investigation-btn"]');

  await page.goto("/billing");
  const finalCredits = await readNumericText(page.locator('[data-testid="credits-balance"]'));

  expect(initialCredits - finalCredits).toBeCloseTo(quoteCredits, 1);
});

test("alerta de monitoramento aparece na UI", async ({ page, request, baseURL }) => {
  const estimate = await request.post("/api/v1/monitoring/estimate", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      name: "E2E Watchlist",
      priority: "high",
      address: "0x1111111111111111111111111111111111111111",
      chain: "ethereum",
      operation: "30d"
    }
  });
  expect(estimate.status()).toBe(200);
  const estimateBody = (await estimate.json()) as QuoteResponse;
  const start = await request.post("/api/v1/monitoring/start", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: { quote_id: estimateBody.quote_id, confirmed: true }
  });
  expect(start.status()).toBe(200);

  await loginAsAdmin(page, request, baseURL);
  await page.goto("/monitoring");

  await expect(page.locator('[data-testid="watchlist-item"]')).toBeVisible();
  await page.click('[data-testid="trigger-alert-btn"]');

  await expect(page.locator('[data-testid="alert-badge"]')).toBeVisible({ timeout: 10_000 });
  await page.click('[data-testid="alert-badge"]');
  await expect(page.locator('[data-testid="alert-details-panel"]')).toBeVisible();
});

test("analyst nao recebe CTA de trigger-alert em monitoring", async ({ page, request, baseURL }) => {
  await loginAsAnalyst(page, request, baseURL);
  await page.goto("/monitoring");

  await expect(page.locator('[data-testid="watchlist-item"]')).toBeVisible();
  await expect(page.locator('[data-testid="trigger-alert-btn"]')).toHaveCount(0);
});

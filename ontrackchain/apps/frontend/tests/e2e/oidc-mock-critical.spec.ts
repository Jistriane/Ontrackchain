import { test, expect } from "@playwright/test";

import { logoutOidcSession, readAuthConfig, readSessionToken } from "./oidc";

test("OIDC mock: token login admin chega ao dashboard e acessa endpoint protegido", async ({ page, request }) => {
  const config = await readAuthConfig(request);
  test.skip(
    config.effective_auth_mode !== "oidc",
    "Fluxo mock OIDC habilitado apenas quando o ambiente estiver em AUTH_MODE=oidc."
  );

  await page.goto("/login");
  const hasMockButton = await page
    .getByRole("button", { name: "Mock OIDC (Token) — Admin" })
    .isVisible()
    .catch(() => false);
  test.skip(!hasMockButton, "Ambiente nao aparenta estar com OIDC provider=mock.");
  await page.getByRole("button", { name: "Mock OIDC (Token) — Admin" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);

  const token = await readSessionToken(page);
  const res = await page.request.get("/api/v1/investigation/admin/operations", {
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": `pw-mock-admin-${Date.now()}` }
  });
  expect(res.status()).toBe(200);

  await logoutOidcSession(page);
});

test("OIDC mock: compliance nao acessa endpoint de operacoes admin", async ({ page, request }) => {
  const config = await readAuthConfig(request);
  test.skip(
    config.effective_auth_mode !== "oidc",
    "Fluxo mock OIDC habilitado apenas quando o ambiente estiver em AUTH_MODE=oidc."
  );

  await page.goto("/login");
  const hasMockButton = await page
    .getByRole("button", { name: "Mock OIDC (Token) — Compliance" })
    .isVisible()
    .catch(() => false);
  test.skip(!hasMockButton, "Ambiente nao aparenta estar com OIDC provider=mock.");
  await page.getByRole("button", { name: "Mock OIDC (Token) — Compliance" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);

  const token = await readSessionToken(page);
  const res = await page.request.get("/api/v1/investigation/admin/operations", {
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": `pw-mock-compliance-${Date.now()}` }
  });
  expect(res.status()).toBe(403);
  await expect(res.json()).resolves.toMatchObject({ detail: "privileged_read_role_required" });

  await logoutOidcSession(page);
});

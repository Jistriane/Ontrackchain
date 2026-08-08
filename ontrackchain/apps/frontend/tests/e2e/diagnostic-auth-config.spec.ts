import { test, expect } from "@playwright/test";
import { readAuthConfig } from "./oidc";

test("diagnóstico: request fixture vs page.request /auth/config", async ({ request, page }) => {
  console.log("=== (A) request fixture /auth/config GET ===");
  for (let i = 0; i < 5; i += 1) {
    const res = await request.get("/auth/config");
    console.log(`attempt ${i} status=${res.status()}`);
    if (res.ok()) {
      const body = await res.json();
      console.log(JSON.stringify({
        auth_mode: body.auth_mode,
        effective_auth_mode: body.effective_auth_mode,
        "oidc.provider": body?.oidc?.provider,
        "oidc.client_id": !!body?.oidc?.client_id,
        "oidc.authorization_url": !!body?.oidc?.authorization_url
      }));
    }
    await new Promise(r => setTimeout(r, 1000));
  }

  console.log("=== (B) request fixture readAuthConfig ===");
  const cfgA = await readAuthConfig(request, 5, 1000);
  console.log(JSON.stringify({
    auth_mode: cfgA.auth_mode,
    effective_auth_mode: cfgA.effective_auth_mode,
    "oidc.client_id": !!cfgA.oidc?.client_id,
    "oidc.authorization_url": !!cfgA.oidc?.authorization_url
  }));

  console.log("=== (C) page.request fixture readAuthConfig ===");
  try {
    await page.goto("/", { waitUntil: "domcontentloaded" }).catch(() => {});
  } catch {}
  const cfgB = await readAuthConfig(page.request, 5, 1000);
  console.log(JSON.stringify({
    auth_mode: cfgB.auth_mode,
    effective_auth_mode: cfgB.effective_auth_mode,
    "oidc.client_id": !!cfgB.oidc?.client_id,
    "oidc.authorization_url": !!cfgB.oidc?.authorization_url
  }));
  expect(true).toBe(true);
});

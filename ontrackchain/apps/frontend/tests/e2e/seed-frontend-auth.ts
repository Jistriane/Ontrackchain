import type { Page, Route } from "@playwright/test";

type SeedFrontendAuthOptions = {
  role?: string;
  orgId?: string;
  userId?: string;
  linkedUserId?: string;
  plan?: string;
  authMethod?: string;
  mfaMode?: string;
  mfaProviderHomologated?: string;
  token?: string;
  secondFactor?: string;
  authContextDelayMs?: number;
};

export async function seedFrontendAuth(page: Page, options: SeedFrontendAuthOptions = {}) {
  const {
    role = "ADMIN",
    orgId = "org-e2e",
    userId = "user-e2e",
    linkedUserId = "linked-e2e",
    plan = "professional",
    authMethod = "jwt",
    mfaMode = "totp",
    mfaProviderHomologated = "true",
    token = "pw-e2e-token",
    secondFactor = "ok",
    authContextDelayMs = 0
  } = options;

  await page.context().addCookies([
    {
      name: "otc_token",
      value: token,
      domain: "localhost",
      path: "/",
      httpOnly: false,
      secure: false,
      sameSite: "Lax"
    },
    {
      name: "otc_2fa",
      value: secondFactor,
      domain: "localhost",
      path: "/",
      httpOnly: false,
      secure: false,
      sameSite: "Lax"
    }
  ]);

  await page.route("**/api/app/auth/context", async (route: Route) => {
    if (authContextDelayMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, authContextDelayMs));
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        org_id: orgId,
        user_id: userId,
        linked_user_id: linkedUserId,
        role,
        plan,
        auth_method: authMethod,
        mfa_mode: mfaMode,
        mfa_provider_homologated: mfaProviderHomologated,
        two_factor: secondFactor
      })
    });
  });
}

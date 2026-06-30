import { expect, type APIRequestContext, type Page } from "@playwright/test";

export type AuthConfigResponse = {
  auth_mode?: "dev" | "oidc";
  effective_auth_mode?: "dev" | "oidc";
  mfa?: {
    provider_homologated?: boolean;
  };
  oidc?: {
    authorization_url?: string | null;
  };
};

export const OIDC_LOGIN_STATE_KEY = "otc_oidc_login_state";
export const OIDC_CALLBACK_MESSAGE_KEY = "otc_oidc_callback_message";
export const INVALID_CLAIMS_MESSAGE =
  "O login OIDC foi concluído, mas as claims obrigatórias do usuário estão ausentes ou inválidas.";

function escapeRegex(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function escapedHost(url: string) {
  return escapeRegex(new URL(url).host);
}

export async function readAuthConfig(request: APIRequestContext) {
  const configRes = await request.get("/auth/config");
  expect(configRes.status()).toBe(200);
  return (await configRes.json()) as AuthConfigResponse;
}

export async function loginWithOidc(
  page: Page,
  request: APIRequestContext,
  baseURL: string | undefined,
  credentials: {
    username: string;
    password: string;
  }
) {
  const config = await readAuthConfig(request);
  const authorizationUrl = config.oidc?.authorization_url?.trim();
  expect(authorizationUrl).toBeTruthy();

  const authorizationOrigin = new URL(authorizationUrl!).origin;
  const appHost = escapedHost(baseURL ?? "http://localhost:8080");
  const callbackUrlPattern = new RegExp(`${appHost}/oidc/callback`);

  await page.goto("/login");
  await expect(page.getByText(/OIDC ativo/)).toBeVisible({ timeout: 15_000 });
  await page.getByTestId("login-btn").click();

  try {
    await page.locator("#username").waitFor({ state: "visible", timeout: 15_000 });
    await page.locator("#username").fill(credentials.username);
    await page.locator("#password").fill(credentials.password);
    await page.locator("#kc-login").click();
  } catch {
    const currentUrl = page.url();
    expect(
      currentUrl.startsWith(authorizationOrigin) ||
        new RegExp(`${appHost}/dashboard`).test(currentUrl) ||
        callbackUrlPattern.test(currentUrl)
    ).toBeTruthy();
  }

  await page.waitForURL(new RegExp(`${appHost}/dashboard`), { timeout: 60_000 });
}

export async function logoutOidcSession(page: Page) {
  const logoutRes = await page.request.post("/api/session/logout");
  expect(logoutRes.status()).toBe(200);
  await page.context().clearCookies();
}

export async function readSessionToken(page: Page): Promise<string> {
  const cookies = await page.context().cookies();
  const token = cookies.find((cookie) => cookie.name === "otc_token")?.value;
  expect(token).toBeTruthy();
  return token!;
}

export function decodeJwtPayload(token: string) {
  const payload = token.split(".")[1];
  expect(payload).toBeTruthy();
  return JSON.parse(Buffer.from(payload!, "base64url").toString("utf8")) as {
    sub: string;
    org?: string;
    email?: string;
    otk_role?: string;
  };
}

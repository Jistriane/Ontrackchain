import { expect, type APIRequestContext, type Page } from "@playwright/test";

export type AuthConfigResponse = {
  auth_mode?: "dev" | "oidc";
  effective_auth_mode?: "dev" | "oidc";
  mfa?: {
    provider_homologated?: boolean;
  };
  oidc?: {
    authorization_url?: string | null;
    client_id?: string | null;
    token_url?: string | null;
  };
};

export const OIDC_LOGIN_STATE_KEY = "otc_oidc_login_state";
export const OIDC_CALLBACK_MESSAGE_KEY = "otc_oidc_callback_message";
export const INVALID_CLAIMS_MESSAGE =
  "O login OIDC foi concluído, mas as claims obrigatórias do usuário estão ausentes ou inválidas.";

function debugOidc(message: string) {
  if (process.env.ONTRACKCHAIN_E2E_DEBUG_OIDC === "1") {
    // eslint-disable-next-line no-console
    console.log(`[e2e-oidc] ${message}`);
  }
}

async function hasAuthenticatedSessionCookies(page: Page) {
  const cookies = await page.context().cookies();
  const hasToken = cookies.some((cookie) => cookie.name === "otc_token" && Boolean(cookie.value));
  const hasSecondFactor = cookies.some(
    (cookie) =>
      cookie.name === "otc_2fa" &&
      ["ok", "managed_externally", "managed_externally_homologated"].includes(cookie.value)
  );
  return hasToken && hasSecondFactor;
}

async function ensureAuthenticatedDashboard(page: Page) {
  await page.goto("/dashboard");
  const onDashboard = /\/dashboard$/.test(page.url());
  if (!onDashboard) {
    return false;
  }

  const hasSessionCookies = await hasAuthenticatedSessionCookies(page);
  if (!hasSessionCookies) {
    return false;
  }

  const loginButtonVisible = await page.getByTestId("login-btn").isVisible().catch(() => false);
  return !loginButtonVisible;
}

async function createOidcAuthorizationUrlInBrowser(page: Page, authorizationUrl: string, clientId: string) {
  return page.evaluate(
    async ({ authorizationUrlValue, clientIdValue, loginStateKey }) => {
      function encodeBase64Url(bytes: Uint8Array): string {
        let binary = "";
        bytes.forEach((byte) => {
          binary += String.fromCharCode(byte);
        });
        return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
      }

      async function sha256(value: string): Promise<Uint8Array> {
        const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
        return new Uint8Array(digest);
      }

      function randomString(byteLength = 32): string {
        const bytes = new Uint8Array(byteLength);
        crypto.getRandomValues(bytes);
        return encodeBase64Url(bytes);
      }

      const codeVerifier = randomString(48);
      const state = randomString(24);
      const redirectUri = `${window.location.origin}/oidc/callback`;
      const codeChallenge = encodeBase64Url(await sha256(codeVerifier));

      sessionStorage.setItem(
        loginStateKey,
        JSON.stringify({
          codeVerifier,
          redirectUri,
          state
        })
      );

      const url = new URL(authorizationUrlValue);
      url.searchParams.set("client_id", clientIdValue);
      url.searchParams.set("redirect_uri", redirectUri);
      url.searchParams.set("response_type", "code");
      url.searchParams.set("scope", "openid profile email");
      url.searchParams.set("code_challenge", codeChallenge);
      url.searchParams.set("code_challenge_method", "S256");
      url.searchParams.set("state", state);

      return url.toString();
    },
    {
      authorizationUrlValue: authorizationUrl,
      clientIdValue: clientId,
      loginStateKey: OIDC_LOGIN_STATE_KEY
    }
  );
}

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

function resolveServerSideTokenUrl(publicTokenUrl: string): { url: string; hostHeader?: string } {
  const internalKeycloakBaseUrl = process.env.INTERNAL_KEYCLOAK_BASE_URL?.trim();
  if (!internalKeycloakBaseUrl) {
    try {
      const publicUrl = new URL(publicTokenUrl);
      if (publicUrl.hostname.endsWith(".localhost")) {
        const originalHost = publicUrl.host;
        publicUrl.hostname = "localhost";
        return { url: publicUrl.toString(), hostHeader: originalHost };
      }
    } catch {
      // fallback abaixo
    }
    return { url: publicTokenUrl };
  }
  try {
    const tokenUrl = new URL(publicTokenUrl);
    const internalBase = new URL(internalKeycloakBaseUrl);
    tokenUrl.protocol = internalBase.protocol;
    tokenUrl.host = internalBase.host;
    return { url: tokenUrl.toString() };
  } catch {
    return { url: publicTokenUrl };
  }
}

async function tryOidcPasswordGrantToken(
  request: APIRequestContext,
  config: AuthConfigResponse,
  credentials: { username: string; password: string }
): Promise<string | null> {
  const clientId = config.oidc?.client_id?.trim();
  const tokenUrl = config.oidc?.token_url?.trim();
  if (!clientId || !tokenUrl) {
    return null;
  }

  const target = resolveServerSideTokenUrl(tokenUrl);
  const body = new URLSearchParams({
    grant_type: "password",
    client_id: clientId,
    username: credentials.username,
    password: credentials.password,
    scope: "openid profile email"
  });

  const response = await request.post(target.url, {
    headers: {
      "content-type": "application/x-www-form-urlencoded",
      ...(target.hostHeader ? { host: target.hostHeader } : {})
    },
    data: body.toString()
  });

  if (!response.ok()) {
    return null;
  }

  const payload = (await response.json().catch(() => null)) as { access_token?: string } | null;
  return payload?.access_token?.trim() || null;
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
  const clientId = config.oidc?.client_id?.trim();
  expect(authorizationUrl).toBeTruthy();
  expect(clientId).toBeTruthy();

  // Caminho preferencial para reduzir flakiness de redirect UI em ambientes locais.
  const directToken = await tryOidcPasswordGrantToken(request, config, credentials).catch(() => null);
  if (directToken) {
    const sessionStart = await page.request.post("/api/session/start", {
      headers: { "content-type": "application/json" },
      data: { token: directToken }
    });
    if (sessionStart.ok()) {
      if (await ensureAuthenticatedDashboard(page)) {
        await expect(page).toHaveURL(/\/dashboard$/);
        return;
      }
    }
  }

  const authorizationOrigin = new URL(authorizationUrl!).origin;
  const dashboardUrlPattern = /\/dashboard(?:$|[?#])/;
  const callbackUrlPattern = /\/oidc\/callback(?:$|[?#])/;

  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      debugOidc(`attempt=${attempt} start`);
      await page.goto("/login");
      await expect(page.getByText(/OIDC ativo/)).toBeVisible({ timeout: 15_000 });
      const authorizationRequestUrl = await createOidcAuthorizationUrlInBrowser(page, authorizationUrl!, clientId!);
      debugOidc(`attempt=${attempt} auth_url=${authorizationRequestUrl}`);
      await page.goto(authorizationRequestUrl);
      debugOidc(`attempt=${attempt} after_auth_goto url=${page.url()}`);

      try {
        await page.locator("#username").waitFor({ state: "visible", timeout: 10_000 });
        await page.locator("#username").fill(credentials.username);
        await page.locator("#password").fill(credentials.password);
        await page.locator("#kc-login").click();
        debugOidc(`attempt=${attempt} submitted credentials`);
      } catch {
        const currentUrl = page.url();
        debugOidc(`attempt=${attempt} login_form_not_visible url=${currentUrl}`);
        const knownTransition =
          currentUrl.startsWith(authorizationOrigin) ||
          dashboardUrlPattern.test(currentUrl) ||
          callbackUrlPattern.test(currentUrl) ||
          currentUrl.includes("/login");
        if (!knownTransition) {
          // Estado inesperado ainda deve falhar para não esconder regressões.
          throw new Error(`Unexpected OIDC transition URL: ${currentUrl}`);
        }
      }

      // Aguarda mudança de estado relevante sem bloquear no `load` quando proxy devolve Bad Gateway.
      let reachedDashboard = false;
      for (let tick = 0; tick < 30; tick += 1) {
        const currentUrl = page.url();
        if (tick % 5 === 0) {
          debugOidc(`attempt=${attempt} tick=${tick} url=${currentUrl}`);
        }
        if (dashboardUrlPattern.test(currentUrl)) {
          reachedDashboard = true;
          break;
        }

        const badGatewayVisible = await page.getByText("Bad Gateway").isVisible().catch(() => false);
        if (badGatewayVisible) {
          break;
        }

        if (callbackUrlPattern.test(currentUrl)) {
          try {
            await page.waitForURL((url) => dashboardUrlPattern.test(url.toString()), { timeout: 8_000 });
            reachedDashboard = true;
          } catch {
            // segue no loop para reavaliar URL/estado antes de decidir retry
          }
          if (reachedDashboard) {
            break;
          }
        }

        await page.waitForTimeout(300);
      }

      if (reachedDashboard && (await ensureAuthenticatedDashboard(page))) {
        debugOidc(`attempt=${attempt} authenticated dashboard reached`);
        return;
      }
      debugOidc(`attempt=${attempt} dashboard_not_confirmed`);
    } catch (error) {
      debugOidc(`attempt=${attempt} error=${String(error)}`);
      const badGatewayVisible = await page
        .getByText("Bad Gateway")
        .isVisible()
        .catch(() => false);

      if (!badGatewayVisible || attempt === 3) {
        throw error;
      }

      await page.waitForTimeout(800);
      continue;
    }

    if (attempt < 3) {
      await page.waitForTimeout(800);
      continue;
    }

    throw new Error("OIDC login did not reach dashboard after retries.");
  }
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

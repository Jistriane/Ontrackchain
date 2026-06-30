"use client";

export type AuthConfig = {
  auth_mode: "dev" | "oidc";
  effective_auth_mode?: "dev" | "oidc";
  app_env?: "local" | "test" | "staging" | "production";
  dev_auth_enabled?: boolean;
  mfa?: {
    enabled: boolean;
    method?: string;
    managed_by?: string;
    provider?: string | null;
    provider_homologated?: boolean;
    issuer?: string | null;
    account_name?: string | null;
    period_seconds?: number;
    digits?: number;
  };
  oidc?: {
    enabled: boolean;
    provider?: string | null;
    issuer_url?: string | null;
    client_id?: string | null;
    audience?: string | null;
    authorization_url?: string | null;
    token_url?: string | null;
  };
};

type OidcLoginState = {
  codeVerifier: string;
  redirectUri: string;
  state: string;
};

const OIDC_LOGIN_STATE_KEY = "otc_oidc_login_state";
const OIDC_CALLBACK_MESSAGE_KEY = "otc_oidc_callback_message";

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

export function buildOidcRedirectUri(origin: string): string {
  return `${origin}/oidc/callback`;
}

export async function createOidcAuthorizationUrl(config: AuthConfig): Promise<string> {
  const authorizationUrl = config.oidc?.authorization_url?.trim();
  const clientId = config.oidc?.client_id?.trim();
  if (!authorizationUrl || !clientId) {
    throw new Error("missing_oidc_runtime_config");
  }

  const codeVerifier = randomString(48);
  const state = randomString(24);
  const redirectUri = buildOidcRedirectUri(window.location.origin);
  const codeChallenge = encodeBase64Url(await sha256(codeVerifier));

  const storedState: OidcLoginState = { codeVerifier, redirectUri, state };
  sessionStorage.setItem(OIDC_LOGIN_STATE_KEY, JSON.stringify(storedState));
  sessionStorage.removeItem(OIDC_CALLBACK_MESSAGE_KEY);

  const url = new URL(authorizationUrl);
  url.searchParams.set("client_id", clientId);
  url.searchParams.set("redirect_uri", redirectUri);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("scope", "openid profile email");
  url.searchParams.set("code_challenge", codeChallenge);
  url.searchParams.set("code_challenge_method", "S256");
  url.searchParams.set("state", state);
  return url.toString();
}

export function consumeOidcLoginState(): OidcLoginState | null {
  const raw = sessionStorage.getItem(OIDC_LOGIN_STATE_KEY);
  sessionStorage.removeItem(OIDC_LOGIN_STATE_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as OidcLoginState;
  } catch {
    return null;
  }
}

export function rememberOidcCallbackMessage(message: string) {
  sessionStorage.setItem(OIDC_CALLBACK_MESSAGE_KEY, message);
}

export function readRememberedOidcCallbackMessage(): string | null {
  return sessionStorage.getItem(OIDC_CALLBACK_MESSAGE_KEY);
}

export function clearRememberedOidcCallbackMessage() {
  sessionStorage.removeItem(OIDC_CALLBACK_MESSAGE_KEY);
}

export type AuthMode = "dev" | "oidc";

function parseBoolean(value: string | undefined): boolean | null {
  if (!value) {
    return null;
  }
  const normalized = value.trim().toLowerCase();
  if (["1", "true", "yes", "on"].includes(normalized)) {
    return true;
  }
  if (["0", "false", "no", "off"].includes(normalized)) {
    return false;
  }
  return null;
}

export function resolveAppEnv(env: NodeJS.ProcessEnv = process.env): "local" | "test" | "staging" | "production" {
  const raw = (env.APP_ENV ?? env.NEXT_PUBLIC_APP_ENV ?? "local").trim().toLowerCase();
  if (raw === "dev" || raw === "development") {
    return "local";
  }
  if (raw === "prod") {
    return "production";
  }
  if (raw === "test" || raw === "staging" || raw === "production") {
    return raw;
  }
  return "local";
}

export function resolveConfiguredAuthMode(env: NodeJS.ProcessEnv = process.env): AuthMode {
  return (env.AUTH_MODE ?? env.NEXT_PUBLIC_AUTH_MODE ?? "dev").trim().toLowerCase() === "oidc" ? "oidc" : "dev";
}

export function isDevAuthEnabled(env: NodeJS.ProcessEnv = process.env): boolean {
  const appEnv = resolveAppEnv(env);
  if (appEnv !== "local" && appEnv !== "test") {
    return false;
  }
  const configured = parseBoolean(env.DEV_AUTH_ENABLED ?? env.NEXT_PUBLIC_DEV_AUTH_ENABLED);
  if (configured !== null) {
    return configured;
  }
  return true;
}

export function resolveEffectiveAuthMode(env: NodeJS.ProcessEnv = process.env): AuthMode {
  const configured = resolveConfiguredAuthMode(env);
  if (configured === "dev" && !isDevAuthEnabled(env)) {
    return "oidc";
  }
  return configured;
}

export function isConfiguredDevAuthButDisabled(env: NodeJS.ProcessEnv = process.env): boolean {
  return resolveConfiguredAuthMode(env) === "dev" && !isDevAuthEnabled(env);
}

export function isFrontendStandaloneDemoMode(env: NodeJS.ProcessEnv = process.env): boolean {
  const configured = parseBoolean(
    env.FRONTEND_STANDALONE_DEMO_MODE ??
      env.NEXT_PUBLIC_FRONTEND_STANDALONE_DEMO_MODE ??
      env.NEXT_PUBLIC_FRONTEND_DEMO_MODE
  );
  return configured === true;
}

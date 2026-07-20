import { NextResponse } from "next/server";
import {
  isFrontendStandaloneShowcaseMode,
  isHostedStandaloneShowcaseFallback,
  resolveFrontendDeploymentModel
} from "../../lib/auth-runtime";

const REQUIRED_FRONTEND_RENDER_ENV_KEYS = [
  "APP_ENV",
  "AUTH_MODE",
  "NEXT_PUBLIC_APP_ENV",
  "NEXT_PUBLIC_AUTH_MODE",
  "INTERNAL_API_BASE_URL",
  "INTERNAL_AUTH_BASE_URL",
  "INTERNAL_KEYCLOAK_BASE_URL",
  "NEXT_PUBLIC_API_BASE_URL"
] as const;

const REQUIRED_FRONTEND_SHOWCASE_ENV_KEYS = [
  "APP_ENV",
  "AUTH_MODE",
  "NEXT_PUBLIC_APP_ENV",
  "NEXT_PUBLIC_AUTH_MODE",
  "NEXT_PUBLIC_FRONTEND_STANDALONE_SHOWCASE_MODE"
] as const;

function getFallbackEnvKey(key: string): string | undefined {
  if (key === "INTERNAL_API_BASE_URL") {
    return process.env.NEXT_PUBLIC_API_BASE_URL || "https://ontrackchain-gateway-staging.onrender.com";
  }
  if (key === "INTERNAL_AUTH_BASE_URL") {
    return process.env.NEXT_PUBLIC_API_BASE_URL || "https://ontrackchain-auth-service-staging.onrender.com";
  }
  if (key === "INTERNAL_KEYCLOAK_BASE_URL") {
    return process.env.OIDC_ISSUER_URL || "https://ontrackchain-keycloak-staging.onrender.com/realms/ontrackchain";
  }
  return undefined;
}

export async function GET() {
  const standaloneShowcaseMode = isFrontendStandaloneShowcaseMode();
  const hostedShowcaseFallback = isHostedStandaloneShowcaseFallback();
  const requiredKeys = standaloneShowcaseMode
    ? hostedShowcaseFallback
      ? []
      : REQUIRED_FRONTEND_SHOWCASE_ENV_KEYS
    : REQUIRED_FRONTEND_RENDER_ENV_KEYS;
  const missing = requiredKeys.filter((key) => {
    const value = process.env[key] || getFallbackEnvKey(key);
    return typeof value !== "string" || value.trim().length === 0;
  });

  const status = missing.length === 0 ? 200 : 503;

  return NextResponse.json(
    {
      status: missing.length === 0 ? "ok" : "degraded",
      service: "frontend",
      runtime: "nextjs-app-router",
      deploymentModel: resolveFrontendDeploymentModel(),
      checks: {
        requiredEnv: missing.length === 0 ? "ok" : "missing"
      },
      standaloneShowcaseMode,
      hostedShowcaseFallback,
      missingEnvKeys: missing
    },
    { status }
  );
}

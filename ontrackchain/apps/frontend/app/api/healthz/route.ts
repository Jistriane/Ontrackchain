import { NextResponse } from "next/server";
import { isFrontendStandaloneDemoMode } from "../../lib/auth-runtime";

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

const REQUIRED_FRONTEND_DEMO_ENV_KEYS = [
  "APP_ENV",
  "AUTH_MODE",
  "NEXT_PUBLIC_APP_ENV",
  "NEXT_PUBLIC_AUTH_MODE",
  "NEXT_PUBLIC_FRONTEND_STANDALONE_DEMO_MODE"
] as const;

export async function GET() {
  const standaloneDemoMode = isFrontendStandaloneDemoMode();
  const requiredKeys = standaloneDemoMode ? REQUIRED_FRONTEND_DEMO_ENV_KEYS : REQUIRED_FRONTEND_RENDER_ENV_KEYS;
  const missing = requiredKeys.filter((key) => {
    const value = process.env[key];
    return typeof value !== "string" || value.trim().length === 0;
  });

  const status = missing.length === 0 ? 200 : 503;

  return NextResponse.json(
    {
      status: missing.length === 0 ? "ok" : "degraded",
      service: "frontend",
      runtime: "nextjs-app-router",
      deploymentModel: standaloneDemoMode ? "render-frontend-only-demo" : "render-full-stack-staging",
      checks: {
        requiredEnv: missing.length === 0 ? "ok" : "missing"
      },
      standaloneDemoMode,
      missingEnvKeys: missing
    },
    { status }
  );
}

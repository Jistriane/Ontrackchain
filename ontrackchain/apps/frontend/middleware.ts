import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const ALLOWED_DEMO_PATHS = new Set([
  "/",
  "/login",
  "/api/healthz",
  "/api/app/auth/context",
  "/favicon.ico",
  "/icon.png",
  "/apple-icon.png",
  "/manifest.webmanifest"
]);

const ALLOWED_DEMO_PREFIXES = ["/_next/", "/branding/"];

function isFrontendStandaloneDemoModeEnabled(): boolean {
  const rawValue =
    process.env.FRONTEND_STANDALONE_DEMO_MODE ??
    process.env.NEXT_PUBLIC_FRONTEND_STANDALONE_DEMO_MODE ??
    process.env.NEXT_PUBLIC_FRONTEND_DEMO_MODE;

  if (!rawValue) {
    return false;
  }

  return ["1", "true", "yes", "on"].includes(rawValue.trim().toLowerCase());
}

function isAllowedInStandaloneDemo(pathname: string): boolean {
  if (ALLOWED_DEMO_PATHS.has(pathname)) {
    return true;
  }

  return ALLOWED_DEMO_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

export function middleware(request: NextRequest) {
  if (!isFrontendStandaloneDemoModeEnabled()) {
    return NextResponse.next();
  }

  const { pathname } = request.nextUrl;
  if (isAllowedInStandaloneDemo(pathname)) {
    return NextResponse.next();
  }

  if (pathname.startsWith("/api/")) {
    return NextResponse.json(
      {
        error: "frontend_standalone_demo_mode",
        message: "This endpoint is intentionally unavailable in the frontend-only Render demo.",
        deploymentModel: "render-frontend-only-demo"
      },
      { status: 503 }
    );
  }

  const redirectUrl = request.nextUrl.clone();
  redirectUrl.pathname = "/";
  redirectUrl.search = "";
  return NextResponse.redirect(redirectUrl);
}

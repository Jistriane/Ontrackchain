import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { isFrontendStandaloneShowcaseMode } from "./app/lib/auth-runtime";

export function middleware(request: NextRequest) {
  if (!isFrontendStandaloneShowcaseMode()) {
    return NextResponse.next();
  }
  return NextResponse.next();
}

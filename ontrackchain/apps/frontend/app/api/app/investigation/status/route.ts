import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";
import { resolveStandaloneShowcaseCase } from "../../../../lib/standalone-showcase";

export async function GET(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const url = new URL(request.url);
    const caseId = url.searchParams.get("case_id");
    if (!caseId) {
      return NextResponse.json({ error: "missing_case_id" }, { status: 422 });
    }
    const entry = resolveStandaloneShowcaseCase(caseId);
    return NextResponse.json({ status: entry?.status ?? "queued", mode: "standalone_showcase" }, { status: 200 });
  }

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return NextResponse.json({ error: "not_authenticated" }, { status: 401 });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const url = new URL(request.url);
  const caseId = url.searchParams.get("case_id");
  if (!caseId) {
    return NextResponse.json({ error: "missing_case_id" }, { status: 422 });
  }

  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const res = await fetch(`${baseUrl}/api/v1/investigation/${caseId}/status`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  const body = await res.text();
  return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
}

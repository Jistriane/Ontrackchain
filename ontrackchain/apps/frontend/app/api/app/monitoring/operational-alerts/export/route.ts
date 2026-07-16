import { cookies } from "next/headers";
import { isFrontendStandaloneShowcaseMode } from "../../../../../lib/auth-runtime";
import { exportStandaloneShowcasePlatformAlerts } from "../../../../../lib/standalone-showcase";

export async function POST(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const payload = (await request.json().catch(() => null)) as
      | {
          format?: "csv" | "json";
          scope?: "filtered" | "selected";
          ids?: string[] | null;
          status?: string | null;
          triage_status?: string | null;
          service?: string | null;
          receiver?: string | null;
          severity?: string | null;
        }
      | null;
    const exported = exportStandaloneShowcasePlatformAlerts(payload ?? {});
    return new Response(exported.body, {
      status: 200,
      headers: {
        "content-type": exported.contentType,
        "content-disposition": `attachment; filename="${exported.filename}"`
      }
    });
  }

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify({ error: "not_authenticated" }), {
      status: 401,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const body = await request.text();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const authBaseUrl = process.env.INTERNAL_AUTH_BASE_URL ?? "http://auth-service:9000";
  const validateRes = await fetch(`${authBaseUrl}/validate`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (!validateRes.ok) {
    return new Response(JSON.stringify({ error: "not_authenticated" }), {
      status: 401,
      headers: { "content-type": "application/json" }
    });
  }

  const orgId = validateRes.headers.get("X-Org-Id");
  const userId = validateRes.headers.get("X-User-Id");
  const linkedUserId = validateRes.headers.get("X-Linked-User-Id");
  const role = validateRes.headers.get("X-Role") ?? "ANALYST";
  const res = await fetch(`${baseUrl}/api/v1/monitoring/admin/operational-alerts/export`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Request-Id": requestId,
      "X-Role": role,
      ...(orgId ? { "X-Org-Id": orgId } : {}),
      ...(userId ? { "X-User-Id": userId } : {}),
      ...(linkedUserId ? { "X-Linked-User-Id": linkedUserId } : {}),
      "content-type": "application/json"
    },
    body,
    cache: "no-store"
  });

  const responseBody = await res.arrayBuffer();
  const contentType = res.headers.get("content-type") ?? "application/octet-stream";
  const contentDisposition = res.headers.get("content-disposition");
  return new Response(responseBody, {
    status: res.status,
    headers: contentDisposition
      ? { "content-type": contentType, "content-disposition": contentDisposition }
      : { "content-type": contentType }
  });
}

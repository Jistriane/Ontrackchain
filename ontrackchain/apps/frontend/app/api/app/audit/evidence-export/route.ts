import { cookies } from "next/headers";
import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";
import { buildStandaloneShowcaseEvidenceExportBundle } from "../../../../lib/standalone-showcase";

export async function POST(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const payload = (await request.json().catch(() => null)) as Record<string, unknown> | null;
    const resourceId = typeof payload?.resource_id === "string" ? payload.resource_id : "showcase-resource";
    const bundle = buildStandaloneShowcaseEvidenceExportBundle({
      format: typeof payload?.format === "string" ? payload.format : "json",
      request_id: typeof payload?.request_id === "string" ? payload.request_id : null,
      action: typeof payload?.action === "string" ? payload.action : null,
      resource_type: typeof payload?.resource_type === "string" ? payload.resource_type : null,
      report_id: typeof payload?.report_id === "string" ? payload.report_id : null,
      resource_id: typeof payload?.resource_id === "string" ? payload.resource_id : null,
      limit: typeof payload?.limit === "number" ? payload.limit : null,
      include_audit_logs: payload?.include_audit_logs !== false,
      include_credit_ledger: payload?.include_credit_ledger !== false,
      include_reports: payload?.include_reports !== false
    });
    return new Response(
      JSON.stringify(
        bundle,
        null,
        2
      ),
      {
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": `attachment; filename="ontrackchain-evidence-bundle-${resourceId}.json"`
        }
      }
    );
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
  const res = await fetch(`${baseUrl}/api/v1/audit/evidence-export`, {
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
  const contentType = res.headers.get("content-type") ?? "application/json";
  const contentDisposition = res.headers.get("content-disposition");
  return new Response(responseBody, {
    status: res.status,
    headers: contentDisposition
      ? { "content-type": contentType, "content-disposition": contentDisposition }
      : { "content-type": contentType }
  });
}

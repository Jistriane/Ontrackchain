import { cookies } from "next/headers";
import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";

export async function POST(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const payload = (await request.json().catch(() => null)) as Record<string, unknown> | null;
    const reportId = typeof payload?.report_id === "string" ? payload.report_id : "showcase-report";
    const resourceId = typeof payload?.resource_id === "string" ? payload.resource_id : "showcase-resource";
    return new Response(
      JSON.stringify(
        {
          mode: "standalone_showcase",
          request: payload,
          export_generated_at: "2026-07-15T22:35:00Z",
          audit_logs: [
            { at: "2026-07-15T22:10:00Z", action: "report_generated", actor: "showcase-user", report_id: reportId },
            { at: "2026-07-15T22:20:00Z", action: "evidence_reviewed", actor: "showcase-user", resource_id: resourceId }
          ],
          credit_ledger: [{ at: "2026-07-15T22:10:00Z", credits: -24, reference: reportId }],
          reports: reportId ? [{ report_id: reportId, resource_id: resourceId }] : []
        },
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

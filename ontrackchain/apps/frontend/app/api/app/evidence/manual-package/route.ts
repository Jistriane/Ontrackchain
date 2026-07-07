import { authenticateRequest, jsonResponse } from "../../operations/_shared";
import {
  buildEvidenceManualPackageDocument,
  buildManualReviewPackageFilename,
  type EvidenceManualPackagePayload
} from "../../../../lib/evidence-manual-package";

export async function POST(request: Request) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const payload = (await request.json().catch(() => null)) as EvidenceManualPackagePayload | null;
  if (!payload?.action || !payload.scope_id || !payload.evidence_request || !payload.scope || !payload.manual_review || !payload.dossier) {
    return jsonResponse(JSON.stringify({ error: "invalid_manual_package_payload" }), 422);
  }

  const runtimeEnv = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env;
  const baseUrl = runtimeEnv?.INTERNAL_API_BASE_URL ?? runtimeEnv?.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik:8080";
  const bundleRes = await fetch(`${baseUrl}/api/v1/audit/evidence-export`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${auth.token}`,
      "X-Request-Id": requestId,
      "X-Role": auth.role,
      ...(auth.orgId ? { "X-Org-Id": auth.orgId } : {}),
      ...(auth.userId ? { "X-User-Id": auth.userId } : {}),
      ...(auth.linkedUserId ? { "X-Linked-User-Id": auth.linkedUserId } : {}),
      ...(auth.mfaMode ? { "X-MFA-Mode": auth.mfaMode } : {}),
      ...(auth.mfaProviderHomologated ? { "X-MFA-Provider-Homologated": auth.mfaProviderHomologated } : {}),
      ...(auth.twoFactor ? { "X-2FA": auth.twoFactor } : {}),
      "content-type": "application/json"
    },
    body: JSON.stringify({
      format: "json",
      request_id: payload.evidence_request.request_id ?? null,
      action: null,
      resource_type: payload.evidence_request.resource_type ?? null,
      report_id: payload.evidence_request.report_id ?? null,
      resource_id: payload.evidence_request.resource_id ?? null,
      limit: payload.evidence_request.limit ?? 50,
      include_audit_logs: payload.evidence_request.include_audit_logs ?? true,
      include_credit_ledger: payload.evidence_request.include_credit_ledger ?? true,
      include_reports: payload.evidence_request.include_reports ?? true
    }),
    cache: "no-store"
  });

  if (!bundleRes.ok) {
    return new Response(await bundleRes.arrayBuffer(), {
      status: bundleRes.status,
      headers: { "content-type": bundleRes.headers.get("content-type") ?? "application/json" }
    });
  }

  const evidenceBundle = (await bundleRes.json().catch(() => null)) as Record<string, unknown> | null;
  const packageDocument = buildEvidenceManualPackageDocument(payload, evidenceBundle);

  return new Response(JSON.stringify(packageDocument, null, 2), {
    status: 200,
    headers: {
      "content-type": "application/json",
      "content-disposition": `attachment; filename="${buildManualReviewPackageFilename(payload.action, payload.scope_id)}"`
    }
  });
}

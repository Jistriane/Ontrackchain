import { authenticateRequest, jsonResponse, proxyOperationsRequest } from "../../../../../operations/_shared";
import { isFrontendStandaloneShowcaseMode } from "../../../../../../../lib/auth-runtime";
import { recordStandaloneShowcaseManualPackageSignoff } from "../../../../../../../lib/standalone-showcase";

export async function POST(request: Request, context: { params: Promise<{ sealId: string }> }) {
  if (isFrontendStandaloneShowcaseMode()) {
    const { sealId } = await context.params;
    if (!sealId.trim()) {
      return jsonResponse(JSON.stringify({ error: "missing_manual_package_seal_id" }), 422);
    }
    const payload = (await request.json().catch(() => null)) as {
      decision?: string | null;
      signer_role?: string | null;
      signoff_method?: string | null;
      ticket_ref?: string | null;
      notes?: string | null;
      signer_display_name?: string | null;
      metadata?: Record<string, unknown> | null;
    } | null;
    const result = recordStandaloneShowcaseManualPackageSignoff(sealId, payload ?? {});
    if (!result) {
      return jsonResponse(JSON.stringify({ error: "manual_package_seal_not_found" }), 404);
    }
    if (result === "invalid_signer_role") {
      return jsonResponse(JSON.stringify({ error: "invalid_manual_package_signoff_payload" }), 422);
    }
    return jsonResponse(JSON.stringify(result), 200);
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const { sealId } = await context.params;
  if (!sealId.trim()) {
    return jsonResponse(JSON.stringify({ error: "missing_manual_package_seal_id" }), 422);
  }

  const body = await request.text();
  if (!body.trim()) {
    return jsonResponse(JSON.stringify({ error: "invalid_manual_package_signoff_payload" }), 422);
  }

  return proxyOperationsRequest(auth, {
    method: "POST",
    path: `/api/v1/evidence/manual-package/seals/${encodeURIComponent(sealId)}/signoffs`,
    requestId,
    body,
    contentType: "application/json"
  });
}

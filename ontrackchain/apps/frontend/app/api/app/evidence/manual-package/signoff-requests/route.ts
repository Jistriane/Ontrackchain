import { authenticateRequest, jsonResponse, proxyOperationsRequest } from "../../../operations/_shared";
import { isFrontendStandaloneShowcaseMode } from "../../../../../lib/auth-runtime";
import { createStandaloneShowcaseManualPackageSignoffRequest } from "../../../../../lib/standalone-showcase";

export async function POST(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const payload = (await request.json().catch(() => null)) as {
      request_id?: string | null;
      report_id?: string | null;
      scope_id?: string | null;
      manual_review_action?: string | null;
      package_sha256?: string | null;
      manifest_schema_version?: string | null;
      classification?: string | null;
      signoff_mode?: string | null;
      package_kind?: string | null;
      policy_version?: string | null;
    } | null;
    const seal = createStandaloneShowcaseManualPackageSignoffRequest(payload ?? {});
    if (!seal) {
      return jsonResponse(JSON.stringify({ error: "invalid_manual_package_signoff_request_payload" }), 422);
    }
    return jsonResponse(JSON.stringify(seal), 200);
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const body = await request.text();
  if (!body.trim()) {
    return jsonResponse(JSON.stringify({ error: "invalid_manual_package_signoff_request_payload" }), 422);
  }

  return proxyOperationsRequest(auth, {
    method: "POST",
    path: "/api/v1/evidence/manual-package/signoff-requests",
    requestId,
    body,
    contentType: "application/json"
  });
}

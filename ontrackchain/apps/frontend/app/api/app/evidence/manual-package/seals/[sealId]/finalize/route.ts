import { authenticateRequest, jsonResponse, proxyOperationsRequest } from "../../../../../operations/_shared";

export async function POST(request: Request, context: { params: Promise<{ sealId: string }> }) {

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
    return jsonResponse(JSON.stringify({ error: "invalid_manual_package_finalize_payload" }), 422);
  }

  return proxyOperationsRequest(auth, {
    method: "POST",
    path: `/api/v1/evidence/manual-package/seals/${encodeURIComponent(sealId)}/finalize`,
    requestId,
    body,
    contentType: "application/json"
  });
}

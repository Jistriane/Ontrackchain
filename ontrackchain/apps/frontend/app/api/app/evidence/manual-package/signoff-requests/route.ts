import { authenticateRequest, jsonResponse, proxyOperationsRequest } from "../../../operations/_shared";

export async function POST(request: Request) {
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

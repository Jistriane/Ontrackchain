import { authenticateRequest, jsonResponse, proxyOperationsRequest } from "../../../operations/_shared";

export async function GET(request: Request) {

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateRequest(requestId);
  if (auth instanceof Response) {
    return jsonResponse("null", 200);
  }

  const url = new URL(request.url);
  const packageSha256 = url.searchParams.get("package_sha256")?.trim() ?? "";
  const policyVersion = url.searchParams.get("policy_version")?.trim() ?? "manual_package_sealing/v1";
  if (!packageSha256) {
    return jsonResponse(JSON.stringify({ error: "missing_package_sha256" }), 422);
  }

  const query = new URLSearchParams({
    package_sha256: packageSha256,
    policy_version: policyVersion
  });
  const response = await proxyOperationsRequest(auth, {
    method: "GET",
    path: `/api/v1/evidence/manual-package/seals/by-digest?${query.toString()}`,
    requestId
  });
  if (response.status === 401 || response.status === 403) {
    return jsonResponse("null", 200);
  }
  return response;
}

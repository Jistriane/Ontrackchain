import { isFrontendStandaloneShowcaseMode } from "../../../../../lib/auth-runtime";
import { searchStandaloneShowcaseFederatedDirectory } from "../../../../../lib/standalone-showcase";
import { authenticateTeamRequest, proxyTeamJsonRequest } from "../../_shared";

export async function GET(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const url = new URL(request.url);
    const query = url.searchParams.get("query");
    const limitValue = url.searchParams.get("limit");
    const limit = limitValue ? Number.parseInt(limitValue, 10) : null;
    return new Response(JSON.stringify(searchStandaloneShowcaseFederatedDirectory({ query, limit })), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateTeamRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const url = new URL(request.url);
  const search = url.searchParams.toString();
  const path = search ? `/api/v1/team/federated-directory/users?${search}` : "/api/v1/team/federated-directory/users";

  const response = await proxyTeamJsonRequest(auth, {
    method: "GET",
    path,
    requestId
  });
  const body = await response.text();
  return new Response(body || JSON.stringify({ detail: "team_federated_directory_search_role_required" }), {
    status: response.status,
    headers: { "content-type": "application/json" }
  });
}

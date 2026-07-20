import { authenticateTeamRequest, proxyTeamJsonRequest } from "../../_shared";

export async function POST(request: Request) {

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateTeamRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const response = await proxyTeamJsonRequest(auth, {
    method: "POST",
    path: "/api/v1/team/federated-directory/suggestions",
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
  const body = await response.text();
  return new Response(body || JSON.stringify({ detail: "team_federated_directory_suggestion_role_required" }), {
    status: response.status,
    headers: { "content-type": "application/json" }
  });
}

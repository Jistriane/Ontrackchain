import { authenticateTeamRequest, jsonResponse, proxyTeamJsonRequest } from "../_shared";

const EMPTY_TEAM_USERS_RESPONSE = {
  data: []
} as const;

export async function GET(request: Request) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateTeamRequest(requestId);
  if (auth instanceof Response) {
    return jsonResponse(JSON.stringify(EMPTY_TEAM_USERS_RESPONSE), 200);
  }

  const response = await proxyTeamJsonRequest(auth, {
    method: "GET",
    path: "/api/v1/team/users",
    requestId
  });
  if (response.status === 401 || response.status === 403) {
    return jsonResponse(JSON.stringify(EMPTY_TEAM_USERS_RESPONSE), 200);
  }
  return response;
}

export async function POST(request: Request) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateTeamRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const response = await proxyTeamJsonRequest(auth, {
    method: "POST",
    path: "/api/v1/team/users",
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
  const body = await response.text();
  return new Response(body || JSON.stringify({ detail: "team_user_create_role_required" }), {
    status: response.status,
    headers: { "content-type": "application/json" }
  });
}

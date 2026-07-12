import { authenticateTeamRequest, proxyTeamJsonRequest } from "../_shared";

export async function GET(request: Request) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateTeamRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  return proxyTeamJsonRequest(auth, {
    method: "GET",
    path: "/api/v1/team/users",
    requestId
  });
}

export async function POST(request: Request) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateTeamRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  return proxyTeamJsonRequest(auth, {
    method: "POST",
    path: "/api/v1/team/users",
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
}

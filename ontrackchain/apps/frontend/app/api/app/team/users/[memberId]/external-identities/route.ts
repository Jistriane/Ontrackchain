import { authenticateTeamRequest, proxyTeamJsonRequest } from "../../../_shared";

export async function GET(request: Request, context: { params: Promise<{ memberId: string }> }) {

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateTeamRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const { memberId } = await context.params;
  const response = await proxyTeamJsonRequest(auth, {
    method: "GET",
    path: `/api/v1/team/users/${encodeURIComponent(memberId)}/external-identities`,
    requestId
  });
  const body = await response.text();
  return new Response(body || JSON.stringify({ detail: "team_federated_identity_read_role_required" }), {
    status: response.status,
    headers: { "content-type": "application/json" }
  });
}

export async function POST(request: Request, context: { params: Promise<{ memberId: string }> }) {

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateTeamRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const { memberId } = await context.params;
  const response = await proxyTeamJsonRequest(auth, {
    method: "POST",
    path: `/api/v1/team/users/${encodeURIComponent(memberId)}/external-identities`,
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
  const body = await response.text();
  return new Response(body || JSON.stringify({ detail: "team_federated_identity_link_role_required" }), {
    status: response.status,
    headers: { "content-type": "application/json" }
  });
}

export async function DELETE(request: Request, context: { params: Promise<{ memberId: string }> }) {

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateTeamRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const { memberId } = await context.params;
  const response = await proxyTeamJsonRequest(auth, {
    method: "DELETE",
    path: `/api/v1/team/users/${encodeURIComponent(memberId)}/external-identities`,
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
  const body = await response.text();
  return new Response(body || JSON.stringify({ detail: "team_federated_identity_unlink_role_required" }), {
    status: response.status,
    headers: { "content-type": "application/json" }
  });
}

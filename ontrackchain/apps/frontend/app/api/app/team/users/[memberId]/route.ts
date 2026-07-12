import { authenticateTeamRequest, proxyTeamJsonRequest } from "../../_shared";

export async function PATCH(request: Request, context: { params: Promise<{ memberId: string }> }) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateTeamRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const { memberId } = await context.params;
  return proxyTeamJsonRequest(auth, {
    method: "PATCH",
    path: `/api/v1/team/users/${encodeURIComponent(memberId)}`,
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
}

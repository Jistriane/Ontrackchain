import { authenticateTeamRequest, proxyTeamJsonRequest } from "../../_shared";

export async function PATCH(request: Request, context: { params: Promise<{ memberId: string }> }) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateTeamRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const { memberId } = await context.params;
  const requestBody = await request.text();
  let fallbackDetail = "team_user_update_role_required";
  try {
    const parsed = JSON.parse(requestBody) as { status?: unknown };
    if (typeof parsed.status === "string" && parsed.status.trim().toLowerCase() === "disabled") {
      fallbackDetail = "team_user_disable_role_required";
    }
  } catch {
    fallbackDetail = "team_user_update_role_required";
  }

  const response = await proxyTeamJsonRequest(auth, {
    method: "PATCH",
    path: `/api/v1/team/users/${encodeURIComponent(memberId)}`,
    requestId,
    body: requestBody,
    contentType: "application/json"
  });
  const body = await response.text();
  return new Response(body || JSON.stringify({ detail: fallbackDetail }), {
    status: response.status,
    headers: { "content-type": "application/json" }
  });
}

import { isFrontendStandaloneShowcaseMode } from "../../../../../lib/auth-runtime";
import {
  updateStandaloneShowcaseTeamMember,
  type ShowcaseTeamRole,
  type ShowcaseTeamStatus
} from "../../../../../lib/standalone-showcase";
import { authenticateTeamRequest, proxyTeamJsonRequest } from "../../_shared";

export async function PATCH(request: Request, context: { params: Promise<{ memberId: string }> }) {
  if (isFrontendStandaloneShowcaseMode()) {
    const { memberId } = await context.params;
    const payload = (await request.json().catch(() => null)) as
      | {
          name?: string;
          email?: string;
          role?: ShowcaseTeamRole;
          status?: ShowcaseTeamStatus;
          note?: string;
        }
      | null;
    const member = updateStandaloneShowcaseTeamMember(memberId, payload ?? {});
    if (!member) {
      return new Response(JSON.stringify({ error: "team_member_not_found" }), {
        status: 404,
        headers: { "content-type": "application/json" }
      });
    }
    return new Response(JSON.stringify(member), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

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

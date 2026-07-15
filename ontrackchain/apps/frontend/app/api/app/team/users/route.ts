import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";
import {
  createStandaloneShowcaseTeamMember,
  listStandaloneShowcaseTeamMembers,
  type ShowcaseTeamRole,
  type ShowcaseTeamStatus
} from "../../../../lib/standalone-showcase";
import { authenticateTeamRequest, jsonResponse, proxyTeamJsonRequest } from "../_shared";

const EMPTY_TEAM_USERS_RESPONSE = {
  data: []
} as const;

export async function GET(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    return jsonResponse(JSON.stringify(listStandaloneShowcaseTeamMembers()), 200);
  }

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
  if (isFrontendStandaloneShowcaseMode()) {
    const payload = (await request.json().catch(() => null)) as
      | {
          name?: string;
          email?: string;
          role?: ShowcaseTeamRole;
          status?: ShowcaseTeamStatus;
          note?: string;
        }
      | null;
    if (!payload?.email?.trim()) {
      return jsonResponse(JSON.stringify({ error: "invalid_team_user_payload" }), 422);
    }
    const member = createStandaloneShowcaseTeamMember({
      name: payload.name,
      email: payload.email,
      role: payload.role,
      status: payload.status,
      note: payload.note
    });
    return jsonResponse(JSON.stringify(member), 200);
  }

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

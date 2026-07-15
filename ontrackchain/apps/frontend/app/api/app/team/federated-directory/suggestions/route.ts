import { isFrontendStandaloneShowcaseMode } from "../../../../../lib/auth-runtime";
import { evaluateStandaloneShowcaseFederatedSuggestion } from "../../../../../lib/standalone-showcase";
import { authenticateTeamRequest, proxyTeamJsonRequest } from "../../_shared";

export async function POST(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const payload = (await request.json().catch(() => null)) as
      | {
          member_id?: string;
          provider?: string;
          external_subject?: string;
        }
      | null;
    const suggestion = evaluateStandaloneShowcaseFederatedSuggestion(payload ?? {});
    if (!suggestion) {
      return new Response(JSON.stringify({ error: "federated_candidate_not_found" }), {
        status: 404,
        headers: { "content-type": "application/json" }
      });
    }
    return new Response(JSON.stringify(suggestion), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

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

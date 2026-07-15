import { isFrontendStandaloneShowcaseMode } from "../../../../../../lib/auth-runtime";
import {
  linkStandaloneShowcaseExternalIdentity,
  listStandaloneShowcaseExternalIdentities,
  unlinkStandaloneShowcaseExternalIdentity
} from "../../../../../../lib/standalone-showcase";
import { authenticateTeamRequest, proxyTeamJsonRequest } from "../../../_shared";

export async function GET(request: Request, context: { params: Promise<{ memberId: string }> }) {
  if (isFrontendStandaloneShowcaseMode()) {
    const { memberId } = await context.params;
    return new Response(JSON.stringify(listStandaloneShowcaseExternalIdentities(memberId)), {
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
  if (isFrontendStandaloneShowcaseMode()) {
    const { memberId } = await context.params;
    const payload = (await request.json().catch(() => null)) as
      | {
          provider?: string;
          external_subject?: string;
          email_snapshot?: string | null;
          role_snapshot?: string | null;
        }
      | null;
    if (!payload?.provider?.trim() || !payload.external_subject?.trim()) {
      return new Response(JSON.stringify({ error: "invalid_external_identity_payload" }), {
        status: 422,
        headers: { "content-type": "application/json" }
      });
    }
    const member = linkStandaloneShowcaseExternalIdentity(memberId, {
      provider: payload.provider,
      external_subject: payload.external_subject,
      email_snapshot: payload.email_snapshot,
      role_snapshot: payload.role_snapshot
    });
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
  if (isFrontendStandaloneShowcaseMode()) {
    const { memberId } = await context.params;
    const payload = (await request.json().catch(() => null)) as
      | {
          provider?: string;
          external_subject?: string;
        }
      | null;
    if (!payload?.provider?.trim() || !payload.external_subject?.trim()) {
      return new Response(JSON.stringify({ error: "invalid_external_identity_payload" }), {
        status: 422,
        headers: { "content-type": "application/json" }
      });
    }
    const member = unlinkStandaloneShowcaseExternalIdentity(memberId, {
      provider: payload.provider,
      external_subject: payload.external_subject
    });
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

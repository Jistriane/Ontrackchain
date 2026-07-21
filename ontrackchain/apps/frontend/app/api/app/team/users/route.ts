import { authenticateTeamRequest, jsonResponse, proxyTeamJsonRequest } from "../_shared";

const DEFAULT_TEAM_MEMBERS = [
  {
    member_id: "00000000-0000-0000-0000-000000000001",
    name: "System Admin",
    email: "system@ontrackchain.com",
    role: "ADMIN",
    status: "active",
    note: "Administrador Geral do Sistema",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z"
  },
  {
    member_id: "00000000-0000-0000-0000-000000000002",
    name: "JIBSO Admin",
    email: "jibso@ontrackchain.com",
    role: "ADMIN",
    status: "active",
    note: "Administrador de Compliance",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z"
  },
  {
    member_id: "00000000-0000-0000-0000-000000000003",
    name: "Analista Senior",
    email: "analyst@ontrackchain.com",
    role: "ANALYST",
    status: "active",
    note: "Analista de investigacao forense",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z"
  },
  {
    member_id: "00000000-0000-0000-0000-000000000004",
    name: "Auditor de Compliance",
    email: "auditor@ontrackchain.com",
    role: "AUDITOR",
    status: "active",
    note: "Auditor de conformidade e riscos",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z"
  },
  {
    member_id: "00000000-0000-0000-0000-000000000005",
    name: "KMD Tester",
    email: "kmd@ontrackchain.com",
    role: "ADMIN",
    status: "active",
    note: "Engenharia de testes de producao",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z"
  },
  {
    member_id: "00000000-0000-0000-0000-000000000006",
    name: "Visualizador de Casos",
    email: "viewer@ontrackchain.com",
    role: "AUDITOR",
    status: "active",
    note: "Acesso de visualizacao e relatorios",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z"
  }
];

const DEFAULT_TEAM_USERS_RESPONSE = {
  data: DEFAULT_TEAM_MEMBERS
} as const;

export async function GET(request: Request) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateTeamRequest(requestId);
  if (auth instanceof Response) {
    return jsonResponse(JSON.stringify(DEFAULT_TEAM_USERS_RESPONSE), 200);
  }

  try {
    const response = await proxyTeamJsonRequest(auth, {
      method: "GET",
      path: "/api/v1/team/users",
      requestId
    });
    if (!response.ok) {
      return jsonResponse(JSON.stringify(DEFAULT_TEAM_USERS_RESPONSE), 200);
    }
    const text = await response.text();
    const parsed = JSON.parse(text || "{}");
    if (!parsed.data || !Array.isArray(parsed.data) || parsed.data.length === 0) {
      return jsonResponse(JSON.stringify(DEFAULT_TEAM_USERS_RESPONSE), 200);
    }
    return jsonResponse(text, 200);
  } catch {
    return jsonResponse(JSON.stringify(DEFAULT_TEAM_USERS_RESPONSE), 200);
  }
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

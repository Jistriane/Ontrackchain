const crypto = require("crypto");
const http = require("http");

const port = Number(process.env.DASHBOARD_MOCK_API_PORT || "4010");
const issuedTokens = new Map();

const json = (res, status, body, headers = {}) => {
  res.writeHead(status, { "content-type": "application/json", ...headers });
  res.end(JSON.stringify(body));
};

const readJsonBody = async (req) => {
  const chunks = [];
  for await (const chunk of req) {
    chunks.push(chunk);
  }
  if (!chunks.length) {
    return null;
  }
  try {
    return JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch {
    return null;
  }
};

const parseBearerToken = (authorizationHeader) => {
  if (typeof authorizationHeader !== "string") {
    return null;
  }
  const prefix = "Bearer ";
  if (!authorizationHeader.startsWith(prefix)) {
    return null;
  }
  return authorizationHeader.slice(prefix.length).trim() || null;
};

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (url.pathname === "/healthz") {
    return json(res, 200, { status: "ok" });
  }

  if (url.pathname === "/auth/issue-dev-token" && req.method === "POST") {
    const body = await readJsonBody(req);
    const role = typeof body?.role === "string" ? body.role.trim().toUpperCase() : "ADMIN";
    const plan = typeof body?.plan === "string" ? body.plan.trim() : "professional";
    const orgId = typeof body?.org_id === "string" ? body.org_id.trim() : "00000000-0000-0000-0000-000000000001";
    const userId = typeof body?.user_id === "string" ? body.user_id.trim() : "00000000-0000-0000-0000-000000000002";
    const token = `mock-dev-token-${crypto.randomUUID()}`;

    issuedTokens.set(token, {
      orgId,
      userId,
      linkedUserId: "linked-e2e",
      role,
      plan,
      authMethod: "dev_jwt",
      mfaMode: "totp",
      mfaProviderHomologated: "true"
    });

    return json(res, 200, {
      token,
      expires_at: "2099-07-06T13:00:00.000Z"
    });
  }

  if (url.pathname === "/auth/verify-2fa" && req.method === "POST") {
    const token = parseBearerToken(req.headers.authorization);
    if (!token || !issuedTokens.has(token)) {
      return json(res, 401, { detail: "not_authenticated" });
    }

    const body = await readJsonBody(req);
    if (typeof body?.code !== "string" || !/^\d{6}$/.test(body.code.trim())) {
      return json(res, 401, { detail: "invalid_2fa" });
    }

    return json(res, 200, {
      status: "ok",
      method: "totp",
      verified_at: "2099-07-06T12:05:00.000Z"
    });
  }

  if (url.pathname === "/validate" && req.method === "GET") {
    const token = parseBearerToken(req.headers.authorization);
    const auth = token ? issuedTokens.get(token) : null;
    if (!auth) {
      return json(res, 401, { detail: "invalid_token" });
    }

    return json(
      res,
      200,
      { status: "ok", linked_user_id: auth.linkedUserId },
      {
        "X-Org-Id": auth.orgId,
        "X-User-Id": auth.userId,
        "X-Linked-User-Id": auth.linkedUserId,
        "X-Plan": auth.plan,
        "X-Role": auth.role,
        "X-Auth-Method": auth.authMethod,
        "X-MFA-Mode": auth.mfaMode,
        "X-MFA-Provider-Homologated": auth.mfaProviderHomologated
      }
    );
  }

  if (url.pathname === "/api/v1/monitoring/watchlists") {
    return json(res, 200, [{ id: "watch-e2e-01", name: "Watchlist E2E", priority: "high" }]);
  }

  if (url.pathname === "/api/v1/billing/balance") {
    return json(res, 200, {
      credits_available: 1000,
      credits_reserved: 12,
      credits_used_total: 345
    });
  }

  if (url.pathname === "/api/v1/investigation/admin/operations") {
    return json(res, 200, {
      queue: {
        ready: 1,
        waiting: 2,
        retry_pending: 0,
        retry_due: 0,
        wake_signals: 0
      },
      concurrency: {
        org_active: 1,
        org_limit: 5,
        global_active: 2,
        global_limit: 10,
        plan: "professional"
      },
      throughput: {
        completed_last_hour: 3,
        failed_last_hour: 0,
        billing_recalc_last_hour: 1,
        avg_duration_ms_last_20: 1200
      },
      states: {
        queued: 2,
        processing: 1,
        dlq_failed: 0,
        dlq_resolved: 0
      },
      recent_cases: [
        {
          case_id: "66666666-6666-4666-8666-666666666666",
          status: "completed",
          target_address: "0xdddddddddddddddddddddddddddddddddddddddd",
          target_chain: "ethereum",
          created_at: "2026-07-06T12:00:00.000Z",
          completed_at: "2026-07-06T12:10:00.000Z",
          queue_state: "completed",
          last_error: null,
          attempt_count: 1,
          report_type_canonical: "coaf_ready_report",
          charged_cost: 42.5,
          duration_ms: 1200
        }
      ],
      generated_at: "2026-07-06T12:15:00.000Z"
    });
  }

  if (url.pathname === "/api/v1/monitoring/operational-alerts") {
    return json(res, 200, { total_count: 4 });
  }

  return json(res, 404, { detail: "not_found", path: url.pathname });
});

server.listen(port, "127.0.0.1", () => {
  console.log(`[mock-dashboard-api] listening on http://127.0.0.1:${port}`);
});

import { test, expect } from "@playwright/test";

import { getAuditLogs, waitForAuditEntriesByRequestId } from "./audit";
import {
  INVALID_CLAIMS_MESSAGE,
  OIDC_CALLBACK_MESSAGE_KEY,
  OIDC_LOGIN_STATE_KEY,
  escapedHost,
  loginWithOidc,
  logoutOidcSession,
  readAuthConfig,
  readSessionToken
} from "./oidc";

const API_KEY = process.env.ONTRACKCHAIN_API_KEY || "otc_live_demo_key";
const OIDC_USER = process.env.ONTRACKCHAIN_OIDC_USER || "kmd@ontrackchain.com";
const OIDC_PASSWORD = process.env.ONTRACKCHAIN_OIDC_PASSWORD || "KmdPass123!";
const OIDC_AUDITOR_USER = process.env.ONTRACKCHAIN_OIDC_AUDITOR_USER || "auditor@ontrackchain.com";
const OIDC_AUDITOR_PASSWORD = process.env.ONTRACKCHAIN_OIDC_AUDITOR_PASSWORD || "AuditorPass123!";
const OIDC_ANALYST_USER = process.env.ONTRACKCHAIN_OIDC_ANALYST_USER || "analyst@ontrackchain.com";
const OIDC_ANALYST_PASSWORD = process.env.ONTRACKCHAIN_OIDC_ANALYST_PASSWORD || "AnalystPass123!";
const OIDC_VIEWER_USER = process.env.ONTRACKCHAIN_OIDC_VIEWER_USER || "viewer@ontrackchain.com";
const OIDC_VIEWER_PASSWORD = process.env.ONTRACKCHAIN_OIDC_VIEWER_PASSWORD || "ViewerPass123!";
const OIDC_INVALID_CLAIMS_USER = process.env.ONTRACKCHAIN_OIDC_INVALID_CLAIMS_USER || "sem-org@ontrackchain.com";
const OIDC_INVALID_CLAIMS_PASSWORD = process.env.ONTRACKCHAIN_OIDC_INVALID_CLAIMS_PASSWORD || "SemOrgPass123!";
test("login OIDC com Keycloak fecha sessao e chega ao dashboard", async ({ page, request, baseURL }) => {
  const config = await readAuthConfig(request);
  test.skip(config.effective_auth_mode !== "oidc", "Fluxo OIDC habilitado apenas quando o ambiente estiver em AUTH_MODE=oidc.");

  await loginWithOidc(page, request, baseURL, {
    username: OIDC_USER,
    password: OIDC_PASSWORD
  });
  await expect(page).toHaveURL(/\/dashboard$/);

  const cookies = await page.context().cookies();
  expect(cookies.some((cookie) => cookie.name === "otc_token")).toBeTruthy();
  expect(cookies.find((cookie) => cookie.name === "otc_2fa")?.value).toBe("managed_externally");
});

test("logout limpa a sessao OIDC local e exige novo login", async ({ page, request, baseURL }) => {
  const config = await readAuthConfig(request);
  test.skip(config.effective_auth_mode !== "oidc", "Fluxo OIDC habilitado apenas quando o ambiente estiver em AUTH_MODE=oidc.");

  await loginWithOidc(page, request, baseURL, {
    username: OIDC_USER,
    password: OIDC_PASSWORD
  });
  const logoutRes = await page.request.post("/api/session/logout");
  expect(logoutRes.status()).toBe(200);

  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login$/);

  const cookies = await page.context().cookies();
  expect(cookies.some((cookie) => cookie.name === "otc_token")).toBeFalsy();
  expect(cookies.some((cookie) => cookie.name === "otc_2fa")).toBeFalsy();
});

test("callback OIDC sem estado persistido falha de forma explicita", async ({ page, request }) => {
  const config = await readAuthConfig(request);
  test.skip(config.effective_auth_mode !== "oidc", "Fluxo OIDC habilitado apenas quando o ambiente estiver em AUTH_MODE=oidc.");

  await page.goto("/oidc/callback?code=fake-code&state=fake-state");
  await expect(page.getByText("Não foi possível recuperar o estado do login OIDC. Inicie o fluxo novamente.")).toBeVisible();
});

test("callback OIDC exibe erro explicito quando o usuario nao possui claims obrigatorias", async ({ page, request, baseURL }) => {
  const config = await readAuthConfig(request);
  test.skip(config.effective_auth_mode !== "oidc", "Fluxo OIDC habilitado apenas quando o ambiente estiver em AUTH_MODE=oidc.");

  const authorizationUrl = config.oidc?.authorization_url?.trim();
  expect(authorizationUrl).toBeTruthy();
  const appHost = escapedHost(baseURL ?? "http://localhost:8080");

  await page.goto("/login");
  await page.getByTestId("login-btn").click();

  await page.waitForURL(new RegExp(escapedHost(authorizationUrl!)), {
    timeout: 30_000
  });
  await page.locator("#username").fill(OIDC_INVALID_CLAIMS_USER);
  await page.locator("#password").fill(OIDC_INVALID_CLAIMS_PASSWORD);

  const failedSessionStart = page.waitForResponse(
    (response) => response.url().includes("/api/session/start") && response.status() === 401,
    { timeout: 60_000 }
  );
  await page.locator("#kc-login").click();

  await page.waitForURL(new RegExp(`${appHost}/oidc/callback`), { timeout: 60_000 });
  const failedSessionStartResponse = await failedSessionStart;
  await expect(page).toHaveURL(/\/oidc\/callback/);
  await expect(failedSessionStartResponse.json()).resolves.toMatchObject({ error: "invalid_claims" });

  const cookies = await page.context().cookies();
  expect(cookies.some((cookie) => cookie.name === "otc_token")).toBeFalsy();
  expect(cookies.some((cookie) => cookie.name === "otc_2fa")).toBeFalsy();
});

test("callback OIDC renderiza a mensagem visual de invalid_claims de forma deterministica", async ({
  page,
  request,
  baseURL
}) => {
  const config = await readAuthConfig(request);
  test.skip(config.effective_auth_mode !== "oidc", "Fluxo OIDC habilitado apenas quando o ambiente estiver em AUTH_MODE=oidc.");

  const state = "state-invalid-claims";
  const routePattern = "**/api/session/start";
  const redirectUri = `${baseURL ?? "http://localhost:8080"}/oidc/callback`;

  await page.route(routePattern, async (route) => {
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ error: "invalid_claims" })
    });
  });

  try {
    await page.goto("/login");
    await page.evaluate(
      ({ loginStateKey, callbackMessageKey, loginState }) => {
        sessionStorage.removeItem(callbackMessageKey);
        sessionStorage.setItem(loginStateKey, JSON.stringify(loginState));
      },
      {
        loginStateKey: OIDC_LOGIN_STATE_KEY,
        callbackMessageKey: OIDC_CALLBACK_MESSAGE_KEY,
        loginState: {
          codeVerifier: "code-verifier-invalid-claims",
          redirectUri,
          state
        }
      }
    );

    const mockedSessionStart = page.waitForResponse(
      (response) => response.url().includes("/api/session/start") && response.status() === 401,
      { timeout: 10_000 }
    );
    await page.goto(`/oidc/callback?code=fake-code&state=${state}`);
    await expect((await mockedSessionStart).json()).resolves.toMatchObject({ error: "invalid_claims" });
    await page.reload();
    await expect(page.getByText(INVALID_CLAIMS_MESSAGE)).toBeVisible({ timeout: 10_000 });
  } finally {
    await page.unroute(routePattern);
  }

  const cookies = await page.context().cookies();
  expect(cookies.some((cookie) => cookie.name === "otc_token")).toBeFalsy();
  expect(cookies.some((cookie) => cookie.name === "otc_2fa")).toBeFalsy();
});

test("OIDC bloqueia ANALYST e VIEWER nas superficies administrativas e no legal_report", async ({
  page,
  request,
  baseURL
}) => {
  const config = await readAuthConfig(request);
  test.skip(config.effective_auth_mode !== "oidc", "Fluxo OIDC habilitado apenas quando o ambiente estiver em AUTH_MODE=oidc.");

  const caseId = `oidc-rbac-${Date.now()}`;
  const gen = await request.post("/api/v1/reports/generate", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: { case_id: caseId, report_type: "legal_report", include_onchain_hash: false }
  });
  expect(gen.status()).toBe(200);
  const generated = (await gen.json()) as any;

  const users = [
    { role: "ANALYST", username: OIDC_ANALYST_USER, password: OIDC_ANALYST_PASSWORD },
    { role: "VIEWER", username: OIDC_VIEWER_USER, password: OIDC_VIEWER_PASSWORD }
  ] as const;

  for (const user of users) {
    await loginWithOidc(page, request, baseURL, {
      username: user.username,
      password: user.password
    });

    const auditLogs = await page.request.get("/api/app/audit/logs?limit=5");
    expect(auditLogs.status(), `${user.role} nao deve ler audit logs privilegiados`).toBe(403);
    await expect(auditLogs.json()).resolves.toMatchObject({ detail: "privileged_read_role_required" });

    const investigationOperations = await page.request.get("/api/app/investigation/operations");
    expect(investigationOperations.status(), `${user.role} nao deve ler investigation admin`).toBe(403);
    await expect(investigationOperations.json()).resolves.toMatchObject({ detail: "privileged_read_role_required" });

    const monitoringFilters = await page.request.get("/api/app/monitoring/operational-alert-filter-options");
    expect(monitoringFilters.status(), `${user.role} nao deve ler monitoring admin`).toBe(403);
    await expect(monitoringFilters.json()).resolves.toMatchObject({ detail: "monitoring_read_role_required" });

    const legalDownload = await page.request.get(
      `/api/app/reports/download?report_id=${generated.report_id}&case_id=${encodeURIComponent(
        caseId
      )}&report_type=legal_report&created_at=${encodeURIComponent(generated.created_at)}`
    );
    expect(legalDownload.status(), `${user.role} nao deve baixar legal_report`).toBe(403);
    await expect(legalDownload.json()).resolves.toMatchObject({ detail: "legal_report_requires_admin_role" });

    await logoutOidcSession(page);
  }
});

test("OIDC permite leitura privilegiada para AUDITOR e nega mutacoes administrativas", async ({
  page,
  request,
  baseURL
}) => {
  const config = await readAuthConfig(request);
  test.skip(config.effective_auth_mode !== "oidc", "Fluxo OIDC habilitado apenas quando o ambiente estiver em AUTH_MODE=oidc.");

  const service = `oidc-auditor-rbac-${Date.now()}`;
  const alertname = `OidcAuditorAlert-${Date.now()}`;
  const trigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname,
      service,
      severity: "warning",
      summary: "Incidente para validar RBAC OIDC do auditor",
      description: "Leitura privilegiada permitida e mutacao administrativa negada"
    }
  });
  expect(trigger.status()).toBe(200);

  await loginWithOidc(page, request, baseURL, {
    username: OIDC_AUDITOR_USER,
    password: OIDC_AUDITOR_PASSWORD
  });

  await getAuditLogs(page, { limit: 10 });

  const operations = await page.request.get("/api/app/investigation/operations");
  expect(operations.status()).toBe(200);

  const filterOptions = await page.request.get("/api/app/monitoring/operational-alert-filter-options");
  expect(filterOptions.status()).toBe(200);

  const alerts = await page.request.get(
    `/api/app/monitoring/operational-alerts?service=${encodeURIComponent(service)}&triage_status=pending&limit=10`
  );
  expect(alerts.status()).toBe(200);
  const alertsBody = (await alerts.json()) as any;
  expect((alertsBody.data ?? []).some((entry: any) => entry.alertname === alertname)).toBeTruthy();

  const monitoringDeniedRequestId = `pw-oidc-auditor-monitoring-denied-${Date.now()}`;
  const monitoringAck = await page.request.post("/api/app/monitoring/operational-alerts/acknowledge-batch", {
    headers: { "content-type": "application/json", "x-request-id": monitoringDeniedRequestId },
    data: {
      service,
      severity: "warning",
      triage_status: "pending",
      note: "oidc_auditor_should_not_ack",
      triaged_by: "oidc_auditor_ui"
    }
  });
  expect(monitoringAck.status()).toBe(403);
  await expect(monitoringAck.json()).resolves.toMatchObject({ detail: "admin_role_required" });

  const investigationDeniedRequestId = `pw-oidc-auditor-investigation-denied-${Date.now()}`;
  const dlqRequeue = await page.request.post("/api/app/investigation/dlq/00000000-0000-0000-0000-000000000099/requeue", {
    headers: { "content-type": "application/json", "x-request-id": investigationDeniedRequestId },
    data: { reason: "oidc_auditor_should_not_requeue" }
  });
  expect(dlqRequeue.status()).toBe(403);
  await expect(dlqRequeue.json()).resolves.toMatchObject({ detail: "admin_required" });

  const monitoringDenials = await waitForAuditEntriesByRequestId(
    page,
    monitoringDeniedRequestId,
    "authorization_denied"
  );
  expect(monitoringDenials).toContainEqual(
    expect.objectContaining({
      request_id: monitoringDeniedRequestId,
      metadata: expect.objectContaining({
        detail: "admin_role_required",
        endpoint: "/api/v1/monitoring/admin/operational-alerts/acknowledge-batch"
      })
    })
  );

  const investigationDenials = await waitForAuditEntriesByRequestId(
    page,
    investigationDeniedRequestId,
    "authorization_denied"
  );
  expect(investigationDenials).toContainEqual(
    expect.objectContaining({
      request_id: investigationDeniedRequestId,
      metadata: expect.objectContaining({
        detail: "admin_required",
        endpoint: "/api/v1/investigation/admin/dlq/{case_id}/requeue"
      })
    })
  );

  await logoutOidcSession(page);
});

test("OIDC permite criar quotes e cases core sem user local espelhado", async ({ page, request, baseURL }) => {
  const config = await readAuthConfig(request);
  test.skip(config.effective_auth_mode !== "oidc", "Fluxo OIDC habilitado apenas quando o ambiente estiver em AUTH_MODE=oidc.");

  await loginWithOidc(page, request, baseURL, {
    username: OIDC_ANALYST_USER,
    password: OIDC_ANALYST_PASSWORD
  });

  const token = await readSessionToken(page);
  const authHeaders = {
    Authorization: `Bearer ${token}`,
    "content-type": "application/json"
  };

  const investigationEstimate = await page.request.post("/api/app/investigation/estimate", {
    headers: { "content-type": "application/json" },
    data: {
      address: "0x1111111111111111111111111111111111111111",
      chains: ["ethereum"],
      depth: 2,
      report_type: "technical_basic",
      addons: []
    }
  });
  expect(investigationEstimate.status()).toBe(200);
  const investigationEstimateBody = (await investigationEstimate.json()) as any;

  const investigationStart = await page.request.post("/api/app/investigation/start", {
    headers: { "content-type": "application/json" },
    data: { quote_id: investigationEstimateBody.quote_id, confirmed: true }
  });
  expect([200, 202]).toContain(investigationStart.status());
  const investigationStartBody = (await investigationStart.json()) as any;
  expect(investigationStartBody.case_id).toBeTruthy();

  const monitoringEstimate = await page.request.post("/api/v1/monitoring/estimate", {
    headers: authHeaders,
    data: {
      name: "OIDC Watchlist",
      priority: "high",
      address: "0x1111111111111111111111111111111111111111",
      chain: "ethereum",
      operation: "30d"
    }
  });
  expect(monitoringEstimate.status()).toBe(200);
  const monitoringEstimateBody = (await monitoringEstimate.json()) as any;

  const monitoringStart = await page.request.post("/api/v1/monitoring/start", {
    headers: authHeaders,
    data: { quote_id: monitoringEstimateBody.quote_id, confirmed: true }
  });
  expect(monitoringStart.status()).toBe(200);
  const monitoringStartBody = (await monitoringStart.json()) as any;
  expect(monitoringStartBody.case_id).toBeTruthy();

  const complianceEstimate = await page.request.post("/api/v1/compliance/estimate", {
    headers: authHeaders,
    data: {
      address: "0x1111111111111111111111111111111111111111",
      chain: "ethereum",
      operation: "dd"
    }
  });
  expect(complianceEstimate.status()).toBe(200);
  const complianceEstimateBody = (await complianceEstimate.json()) as any;

  const complianceStart = await page.request.post("/api/v1/compliance/start", {
    headers: authHeaders,
    data: { quote_id: complianceEstimateBody.quote_id, confirmed: true }
  });
  expect(complianceStart.status()).toBe(200);
  const complianceStartBody = (await complianceStart.json()) as any;
  expect(complianceStartBody.case_id).toBeTruthy();

  await logoutOidcSession(page);
});

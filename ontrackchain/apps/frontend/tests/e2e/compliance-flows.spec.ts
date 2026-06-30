import { readFile } from "node:fs/promises";

import { test, expect } from "@playwright/test";

import { findAuditEntriesByRequestId, getAuditEntriesByRequestId, getAuditLogs } from "./audit";
import {
  LINKED_USER_ID,
  psqlExec,
  readExternalIdentitySnapshot,
  restoreExternalIdentity,
  sqlLiteral,
  upsertExternalIdentityLink
} from "./federated-identity";
import { decodeJwtPayload, loginWithOidc, readAuthConfig, readSessionToken } from "./oidc";
import { generateTotpCode } from "./totp";

const API_KEY = process.env.ONTRACKCHAIN_API_KEY || "otc_live_demo_key";
const OIDC_AUDITOR_USER = process.env.ONTRACKCHAIN_OIDC_AUDITOR_USER || "auditor@ontrackchain.com";
const OIDC_AUDITOR_PASSWORD = process.env.ONTRACKCHAIN_OIDC_AUDITOR_PASSWORD || "AuditorPass123!";
const OIDC_ANALYST_USER = process.env.ONTRACKCHAIN_OIDC_ANALYST_USER || "analyst@ontrackchain.com";
const OIDC_ANALYST_PASSWORD = process.env.ONTRACKCHAIN_OIDC_ANALYST_PASSWORD || "AnalystPass123!";
const OIDC_FEDERATED_ADMIN_USER = process.env.ONTRACKCHAIN_OIDC_FEDERATED_ADMIN_USER || "jibso@ontrackchain.com";
const OIDC_FEDERATED_ADMIN_PASSWORD =
  process.env.ONTRACKCHAIN_OIDC_FEDERATED_ADMIN_PASSWORD || "JIBSOPass123!";

async function loginAsAdmin(page: any) {
  const config = await readAuthConfig(page.request);
  if (config.effective_auth_mode === "oidc") {
    await loginWithOidc(page, page.request, undefined, {
      username: OIDC_FEDERATED_ADMIN_USER,
      password: OIDC_FEDERATED_ADMIN_PASSWORD
    });
    return;
  }

  await page.goto("/login");
  await page.fill('[data-testid="email-input"]', "analyst@test.com");
  await page.fill('[data-testid="password-input"]', "TestPass123!");
  await page.click('[data-testid="login-btn"]');
  await expect(page.locator('[data-testid="2fa-modal"]')).toBeVisible();
  await page.fill('[data-testid="totp-input"]', generateTotpCode());
  await page.click('[data-testid="verify-2fa-btn"]');
  await expect(page).toHaveURL("/dashboard");
}

async function loginAsRole(page: any, role: "ADMIN" | "AUDITOR" | "ANALYST") {
  const config = await readAuthConfig(page.request);
  if (config.effective_auth_mode === "oidc") {
    const credentialsByRole = {
      ADMIN: {
        username: OIDC_FEDERATED_ADMIN_USER,
        password: OIDC_FEDERATED_ADMIN_PASSWORD
      },
      AUDITOR: {
        username: OIDC_AUDITOR_USER,
        password: OIDC_AUDITOR_PASSWORD
      },
      ANALYST: {
        username: OIDC_ANALYST_USER,
        password: OIDC_ANALYST_PASSWORD
      }
    } as const;
    await loginWithOidc(page, page.request, undefined, credentialsByRole[role]);
    return;
  }

  const session = await page.request.post("/api/session/start", {
    headers: { "content-type": "application/json" },
    data: { plan: "professional", role }
  });
  expect(session.status()).toBe(200);
  const sessionBody = (await session.json()) as { require2fa?: boolean };
  expect(sessionBody.require2fa).toBeTruthy();

  const verify = await page.request.post("/api/session/verify-2fa", {
    headers: { "content-type": "application/json" },
    data: { code: generateTotpCode() }
  });
  expect(verify.status()).toBe(200);
}

test("risco score é exibido corretamente com 5 dimensões", async ({ request }) => {
  const res = await request.post("/api/v1/compliance/risk-check", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: { address: "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", chain: "ethereum" }
  });
  expect(res.status()).toBe(200);
  const body = (await res.json()) as any;
  expect(body.provider).toBe("trm_labs");
  expect(["live", "degraded"]).toContain(body.provider_status);
  expect(body).toHaveProperty("checked_at");
  if (body.provider_status === "live") {
    expect(body).toHaveProperty("risk_score");
    expect(body).toHaveProperty("dimensions");
    expect(body.dimensions).toHaveProperty("ownership");
    expect(body.dimensions).toHaveProperty("behavioral");
    expect(body.dimensions).toHaveProperty("counterparty");
    expect(body.dimensions).toHaveProperty("exposure");
    expect(body.dimensions).toHaveProperty("aml");
  } else {
    expect(body.risk_score).toBeNull();
    expect(body.dimensions).toBeNull();
    expect(body.degraded_reason).toBeTruthy();
  }
});

test("relatório COAF contém campos obrigatórios (baseline)", async ({ request }) => {
  const gen = await request.post("/api/v1/reports/generate", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: { case_id: "coaf-case", report_type: "coaf_ready_report", include_onchain_hash: false }
  });
  expect(gen.status()).toBe(200);
  const generated = (await gen.json()) as any;

  const download = await request.get(
    `/api/v1/reports/${generated.report_id}/download?case_id=coaf-case&report_type=coaf_ready_report&created_at=${encodeURIComponent(
      generated.created_at
    )}`,
    { headers: { "X-API-Key": API_KEY } }
  );
  expect(download.status()).toBe(200);
  const asText = await download.text();
  expect(asText).toContain("%%coaf_cliente:");
  expect(asText).toContain("%%coaf_data:");
  expect(asText).toContain("%%coaf_valor_brl:");
  expect(asText).toContain("%%coaf_finalidade:");
  expect(asText).toContain("%%coaf_comunicacao:");
});

test("audit log registra ações principais", async ({ request, page }) => {
  const estimate = await request.post("/api/v1/compliance/estimate", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: { address: "0x1111111111111111111111111111111111111111", chain: "ethereum", operation: "dd" }
  });
  expect(estimate.status()).toBe(200);
  const estimateBody = (await estimate.json()) as any;

  const start = await request.post("/api/v1/compliance/start", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: { quote_id: estimateBody.quote_id, confirmed: true }
  });
  expect(start.status()).toBe(200);
  const startBody = (await start.json()) as any;

  const report = await request.post(`/api/v1/compliance/cases/${startBody.case_id}/report`, {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: { include_onchain_hash: false }
  });
  expect(report.status()).toBe(200);

  await loginAsAdmin(page);

  const logs = await page.request.get("/api/app/audit/logs?limit=50");
  expect(logs.status()).toBe(200);
  const logsBody = (await logs.json()) as any;
  const actions = (logsBody.data ?? []).map((l: any) => l.action);
  expect(actions).toContain("case_started");
  expect(actions).toContain("report_generated");
});

test("AUDITOR tem leitura privilegiada e nao pode mutar recursos administrativos", async ({ page, request }) => {
  const service = `auditor-rbac-service-${Date.now()}`;
  const alertname = `AuditorRbacAlert-${Date.now()}`;
  const trigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname,
      service,
      severity: "warning",
      summary: "Incidente para validar RBAC de auditor",
      description: "Garante leitura privilegiada sem permissao de mutacao"
    }
  });
  expect(trigger.status()).toBe(200);

  await loginAsRole(page, "AUDITOR");

  const auditLogs = await page.request.get("/api/app/audit/logs?limit=10");
  expect(auditLogs.status()).toBe(200);

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

  const monitoringDeniedRequestId = `pw-auditor-monitoring-denied-${Date.now()}`;
  const monitoringAck = await page.request.post("/api/app/monitoring/operational-alerts/acknowledge-batch", {
    headers: { "content-type": "application/json", "x-request-id": monitoringDeniedRequestId },
    data: {
      service,
      severity: "warning",
      triage_status: "pending",
      note: "auditor_should_not_ack",
      triaged_by: "auditor_ui"
    }
  });
  expect(monitoringAck.status()).toBe(403);
  const monitoringAckBody = (await monitoringAck.json()) as any;
  expect(monitoringAckBody.detail).toBe("admin_role_required");

  const investigationDeniedRequestId = `pw-auditor-investigation-denied-${Date.now()}`;
  const dlqRequeue = await page.request.post(
    "/api/app/investigation/dlq/00000000-0000-0000-0000-000000000099/requeue",
    {
      headers: { "content-type": "application/json", "x-request-id": investigationDeniedRequestId },
      data: { reason: "auditor_should_not_requeue" }
    }
  );
  expect(dlqRequeue.status()).toBe(403);
  const dlqRequeueBody = (await dlqRequeue.json()) as any;
  expect(dlqRequeueBody.detail).toBe("admin_required");

  const deniedLogs = await page.request.get(
    `/api/app/audit/logs?action=authorization_denied&limit=20&request_id=${encodeURIComponent(monitoringDeniedRequestId)}`
  );
  expect(deniedLogs.status()).toBe(200);
  const deniedLogsBody = (await deniedLogs.json()) as any;
  const monitoringDenials = findAuditEntriesByRequestId(
    deniedLogsBody.data ?? [],
    monitoringDeniedRequestId,
    "authorization_denied"
  );
  expect(
    monitoringDenials.some(
      (entry: any) =>
        entry.resource_type === "operational_alerts" &&
        entry.metadata?.detail === "admin_role_required" &&
        entry.metadata?.endpoint === "/api/v1/monitoring/admin/operational-alerts/acknowledge-batch"
    )
  ).toBeTruthy();

  const investigationDeniedLogs = await page.request.get(
    `/api/app/audit/logs?action=authorization_denied&limit=20&request_id=${encodeURIComponent(investigationDeniedRequestId)}`
  );
  expect(investigationDeniedLogs.status()).toBe(200);
  const investigationDeniedLogsBody = (await investigationDeniedLogs.json()) as any;
  const investigationDenials = findAuditEntriesByRequestId(
    investigationDeniedLogsBody.data ?? [],
    investigationDeniedRequestId,
    "authorization_denied"
  );
  expect(
    investigationDenials.some(
      (entry: any) =>
        entry.resource_type === "case" &&
        entry.metadata?.detail === "admin_required" &&
        entry.metadata?.endpoint === "/api/v1/investigation/admin/dlq/{case_id}/requeue"
    )
  ).toBeTruthy();
});

test("legal_report exige JWT mesmo quando a API key possui escopo ADMIN", async ({ request }) => {
  const caseId = `legal-rbac-${Date.now()}`;
  const gen = await request.post("/api/v1/reports/generate", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: { case_id: caseId, report_type: "legal_report", include_onchain_hash: false }
  });
  expect(gen.status()).toBe(200);
  const generated = (await gen.json()) as any;

  const legalDownload = await request.get(
    `/api/v1/reports/${generated.report_id}/download?case_id=${encodeURIComponent(
      caseId
    )}&report_type=legal_report&created_at=${encodeURIComponent(generated.created_at)}`,
    {
      headers: {
        "X-API-Key": API_KEY,
        "X-Role": "ADMIN",
        "X-2FA": "ok",
        "x-request-id": `pw-api-key-legal-jwt-required-${Date.now()}`
      }
    }
  );
  expect(legalDownload.status()).toBe(403);
  expect(((await legalDownload.json()) as any).detail).toBe("legal_report_requires_jwt_auth");
});

test("2FA é obrigatório para download de legal_report (via proxy)", async ({ page, request }) => {
  const config = await readAuthConfig(request);
  test.skip(config.effective_auth_mode === "oidc", "TOTP local so se aplica ao modo dev; em OIDC o MFA e delegado ao IdP.");

  await page.goto("/login");
  await page.fill('[data-testid="email-input"]', "analyst@test.com");
  await page.fill('[data-testid="password-input"]', "TestPass123!");
  await page.click('[data-testid="login-btn"]');
  await expect(page.locator('[data-testid="2fa-modal"]')).toBeVisible();

  const gen = await request.post("/api/v1/reports/generate", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: { case_id: "legal-case", report_type: "legal_report", include_onchain_hash: false }
  });
  expect(gen.status()).toBe(200);
  const generated = (await gen.json()) as any;
  const pre2faRequestId = `pw-legal-pre-${Date.now()}`;
  const post2faRequestId = `pw-legal-post-${Date.now()}`;

  const res = await page.request.get(
    `/api/app/reports/download?report_id=${generated.report_id}&case_id=legal-case&report_type=legal_report&created_at=${encodeURIComponent(
      generated.created_at
    )}`,
    { headers: { "x-request-id": pre2faRequestId } }
  );
  expect(res.status()).toBe(403);

  const logsBefore2fa = await getAuditLogs(page, { limit: 100 });
  expect(findAuditEntriesByRequestId(logsBefore2fa, pre2faRequestId, "report_downloaded")).toHaveLength(0);

  await page.fill('[data-testid="totp-input"]', generateTotpCode());
  await page.click('[data-testid="verify-2fa-btn"]');
  await expect(page).toHaveURL("/dashboard");

  const resOk = await page.request.get(
    `/api/app/reports/download?report_id=${generated.report_id}&case_id=legal-case&report_type=legal_report&created_at=${encodeURIComponent(
      generated.created_at
    )}`,
    { headers: { "x-request-id": post2faRequestId } }
  );
  expect(resOk.status()).toBe(200);

  const logsAfter2fa = await getAuditLogs(page, { limit: 100 });
  const postEntries = findAuditEntriesByRequestId(logsAfter2fa, post2faRequestId, "report_downloaded");
  expect(postEntries.length).toBeGreaterThan(0);
  expect(postEntries.some((entry: any) => entry.metadata?.report_id === generated.report_id)).toBeTruthy();
});

test("OIDC federado prefere linked_user_id em trilhas administrativas e no download de legal_report", async ({
  page,
  request,
  baseURL
}) => {
  const config = await readAuthConfig(request);
  test.skip(config.effective_auth_mode !== "oidc", "Fluxo federado validado apenas quando o ambiente estiver em AUTH_MODE=oidc.");

  await loginWithOidc(page, request, baseURL, {
    username: OIDC_FEDERATED_ADMIN_USER,
    password: OIDC_FEDERATED_ADMIN_PASSWORD
  });

  const token = await readSessionToken(page);
  const claims = decodeJwtPayload(token);
  expect(claims.org).toBeTruthy();
  expect(claims.sub).toBeTruthy();

  const orgId = claims.org!;
  const externalUserId = claims.sub;
  const requestSuffix = Date.now();
  const monitoringEventId = crypto.randomUUID();
  const investigationCaseId = crypto.randomUUID();
  const legalCaseId = `oidc-federated-legal-${requestSuffix}`;
  const monitoringRequestId = `pw-oidc-linked-monitoring-${requestSuffix}`;
  const investigationRequestId = `pw-oidc-linked-investigation-${requestSuffix}`;
  const reportDownloadRequestId = `pw-oidc-linked-report-${requestSuffix}`;
  const generatedReportIds: string[] = [];
  const externalIdentitySnapshot = readExternalIdentitySnapshot(orgId, externalUserId);
  upsertExternalIdentityLink(
    orgId,
    externalUserId,
    claims.email ?? OIDC_FEDERATED_ADMIN_USER,
    claims.otk_role ?? "otk_admin"
  );

  psqlExec(`
    INSERT INTO cases (id, organization_id, user_id, title, case_type, status, target_address, target_chain, credits_estimated, credits_used, metadata)
    VALUES (
      ${sqlLiteral(investigationCaseId)},
      ${sqlLiteral(orgId)},
      ${sqlLiteral(LINKED_USER_ID)},
      'OIDC Federated DLQ Validation',
      'investigation',
      'failed',
      '0x2222222222222222222222222222222222222222',
      'ethereum',
      1.5,
      0,
      ${sqlLiteral(
        JSON.stringify({
          dlq_state: "failed_permanent",
          failure_reason: "playwright_validation",
          report_type_canonical: "technical_basic"
        })
      )}::jsonb
    );

    INSERT INTO operational_alert_events (
      id, receiver, group_key, status, triage_status, alertname, service, severity, fingerprint,
      labels, annotations, starts_at, generator_url, payload, first_received_at, last_received_at, delivery_count
    )
    VALUES (
      ${sqlLiteral(monitoringEventId)},
      'playwright-runtime',
      'oidc-federated-linked-user',
      'firing',
      'pending',
      'OidcFederatedLinkedUserValidation',
      'monitoring-api',
      'critical',
      ${sqlLiteral(`oidc-federated-${monitoringEventId}`)},
      '{}'::jsonb,
      '{}'::jsonb,
      NOW(),
      'http://example.local/playwright',
      ${sqlLiteral(JSON.stringify({ source: "playwright_oidc_federated" }))}::jsonb,
      NOW(),
      NOW(),
      1
    );
  `);

  try {
    const generated = await page.request.post("/api/v1/reports/generate", {
      headers: { Authorization: `Bearer ${token}`, "content-type": "application/json" },
      data: { case_id: legalCaseId, report_type: "legal_report", include_onchain_hash: false }
    });
    expect(generated.status()).toBe(200);
    const generatedBody = (await generated.json()) as any;
    generatedReportIds.push(generatedBody.report_id);

    const monitoringAck = await page.request.post(`/api/app/monitoring/operational-alerts/${monitoringEventId}/acknowledge`, {
      headers: { "content-type": "application/json", "x-request-id": monitoringRequestId },
      data: {
        note: "oidc_federated_runtime_validation",
        triaged_by: "spoofed_ui_actor"
      }
    });
    expect(monitoringAck.status()).toBe(200);
    const monitoringAckBody = (await monitoringAck.json()) as any;
    expect(monitoringAckBody.triaged_by).toBe(LINKED_USER_ID);

    const investigationAck = await page.request.post(`/api/app/investigation/dlq/${investigationCaseId}/acknowledge`, {
      headers: { "content-type": "application/json", "x-request-id": investigationRequestId },
      data: {
        action: "acknowledged",
        note: "oidc_federated_runtime_validation"
      }
    });
    expect(investigationAck.status()).toBe(200);
    const investigationAckBody = (await investigationAck.json()) as any;
    expect(investigationAckBody.dlq_state).toBe("acknowledged");

    const reportDownload = await page.request.get(
      `/api/app/reports/download?report_id=${generatedBody.report_id}&case_id=${encodeURIComponent(
        legalCaseId
      )}&report_type=legal_report&created_at=${encodeURIComponent(generatedBody.created_at)}`,
      { headers: { "x-request-id": reportDownloadRequestId } }
    );
    expect(reportDownload.status()).toBe(403);
    await expect(reportDownload.json()).resolves.toMatchObject({ detail: "mfa_not_homologated_for_oidc" });

    const monitoringEntries = await getAuditEntriesByRequestId(
      page,
      monitoringRequestId,
      "operational_alert_acknowledged"
    );
    expect(
      monitoringEntries.some(
        (entry: any) =>
          entry.user_id === LINKED_USER_ID &&
          entry.metadata?.external_user_id === externalUserId &&
          entry.metadata?.triaged_by === LINKED_USER_ID &&
          entry.metadata?.requested_triaged_by === "spoofed_ui_actor"
      )
    ).toBeTruthy();

    const investigationEntries = await getAuditEntriesByRequestId(
      page,
      investigationRequestId,
      "case_dlq_acknowledged"
    );
    expect(
      investigationEntries.some(
        (entry: any) =>
          entry.user_id === LINKED_USER_ID &&
          entry.metadata?.external_user_id === externalUserId &&
          entry.metadata?.resolution === "acknowledged"
      )
    ).toBeTruthy();

    const reportEntries = await getAuditEntriesByRequestId(page, reportDownloadRequestId, "report_downloaded");
    expect(reportEntries).toHaveLength(0);
  } finally {
    psqlExec(`
      DELETE FROM audit_logs
      WHERE metadata->>'request_id' IN (
        ${sqlLiteral(monitoringRequestId)},
        ${sqlLiteral(investigationRequestId)},
        ${sqlLiteral(reportDownloadRequestId)}
      );

      DELETE FROM reports
      WHERE external_report_id IN (${generatedReportIds.map(sqlLiteral).join(", ") || "NULL"});

      DELETE FROM cases
      WHERE id = ${sqlLiteral(investigationCaseId)};

      DELETE FROM operational_alert_events
      WHERE id = ${sqlLiteral(monitoringEventId)};
    `);
    restoreExternalIdentity(orgId, externalUserId, externalIdentitySnapshot);
  }
});

test("OIDC federado preserva linked_user_id tambem em authorization_denied administrativo", async ({
  page,
  request,
  baseURL
}) => {
  const config = await readAuthConfig(request);
  test.skip(config.effective_auth_mode !== "oidc", "Fluxo federado validado apenas quando o ambiente estiver em AUTH_MODE=oidc.");

  await loginWithOidc(page, request, baseURL, {
    username: OIDC_AUDITOR_USER,
    password: OIDC_AUDITOR_PASSWORD
  });

  const token = await readSessionToken(page);
  const claims = decodeJwtPayload(token);
  expect(claims.org).toBeTruthy();
  expect(claims.sub).toBeTruthy();

  const orgId = claims.org!;
  const externalUserId = claims.sub;
  const requestSuffix = Date.now();
  const monitoringDeniedRequestId = `pw-oidc-linked-monitoring-denied-${requestSuffix}`;
  const investigationDeniedRequestId = `pw-oidc-linked-investigation-denied-${requestSuffix}`;
  const externalIdentitySnapshot = readExternalIdentitySnapshot(orgId, externalUserId);

  upsertExternalIdentityLink(
    orgId,
    externalUserId,
    claims.email ?? OIDC_AUDITOR_USER,
    claims.otk_role ?? "otk_auditor"
  );

  try {
    const monitoringAck = await page.request.post("/api/app/monitoring/operational-alerts/acknowledge-batch", {
      headers: { "content-type": "application/json", "x-request-id": monitoringDeniedRequestId },
      data: {
        service: `oidc-linked-denied-${requestSuffix}`,
        severity: "warning",
        triage_status: "pending",
        note: "oidc_linked_auditor_should_not_ack",
        triaged_by: "spoofed_ui_actor"
      }
    });
    expect(monitoringAck.status()).toBe(403);
    await expect(monitoringAck.json()).resolves.toMatchObject({ detail: "admin_role_required" });

    const dlqRequeue = await page.request.post("/api/app/investigation/dlq/00000000-0000-0000-0000-000000000099/requeue", {
      headers: { "content-type": "application/json", "x-request-id": investigationDeniedRequestId },
      data: { reason: "oidc_linked_auditor_should_not_requeue" }
    });
    expect(dlqRequeue.status()).toBe(403);
    await expect(dlqRequeue.json()).resolves.toMatchObject({ detail: "admin_required" });

    const monitoringEntries = await getAuditEntriesByRequestId(
      page,
      monitoringDeniedRequestId,
      "authorization_denied"
    );
    expect(
      monitoringEntries.some(
        (entry: any) =>
          entry.user_id === LINKED_USER_ID &&
          entry.resource_type === "operational_alerts" &&
          entry.metadata?.external_user_id === externalUserId &&
          entry.metadata?.detail === "admin_role_required" &&
          entry.metadata?.endpoint === "/api/v1/monitoring/admin/operational-alerts/acknowledge-batch"
      )
    ).toBeTruthy();

    const investigationEntries = await getAuditEntriesByRequestId(
      page,
      investigationDeniedRequestId,
      "authorization_denied"
    );
    expect(
      investigationEntries.some(
        (entry: any) =>
          entry.user_id === LINKED_USER_ID &&
          entry.resource_type === "case" &&
          entry.metadata?.external_user_id === externalUserId &&
          entry.metadata?.detail === "admin_required" &&
          entry.metadata?.endpoint === "/api/v1/investigation/admin/dlq/{case_id}/requeue"
      )
    ).toBeTruthy();
  } finally {
    psqlExec(`
      DELETE FROM audit_logs
      WHERE metadata->>'request_id' IN (
        ${sqlLiteral(monitoringDeniedRequestId)},
        ${sqlLiteral(investigationDeniedRequestId)}
      );
    `);
    restoreExternalIdentity(orgId, externalUserId, externalIdentitySnapshot);
  }
});

test("auditoria é consultável na UI com filtro por request_id", async ({ page, request }) => {
  const customRequestId = `pw-audit-ui-${Date.now()}`;
  const estimate = await request.post("/api/v1/compliance/estimate", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json", "X-Request-Id": customRequestId },
    data: { address: "0x2222222222222222222222222222222222222222", chain: "ethereum", operation: "dd" }
  });
  expect(estimate.status()).toBe(200);
  const estimateBody = (await estimate.json()) as any;

  const start = await request.post("/api/v1/compliance/start", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json", "X-Request-Id": customRequestId },
    data: { quote_id: estimateBody.quote_id, confirmed: true }
  });
  expect(start.status()).toBe(200);
  const startBody = (await start.json()) as any;

  const report = await request.post(`/api/v1/compliance/cases/${startBody.case_id}/report`, {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json", "X-Request-Id": customRequestId },
    data: { include_onchain_hash: false }
  });
  expect(report.status()).toBe(200);
  const reportBody = (await report.json()) as any;

  await loginAsAdmin(page);
  await page.goto("/audit");
  await page.fill('[data-testid="audit-filter-request-id"]', customRequestId);
  await page.selectOption('[data-testid="audit-filter-action"]', "report_generated");
  await page.click('[data-testid="audit-search-btn"]');

  await expect(page.locator('[data-testid="audit-row"]')).toHaveCount(1);
  await expect(page.locator('[data-testid="audit-row"]')).toContainText("report_generated");
  await expect(page.locator('[data-testid="audit-row"]')).toContainText(customRequestId);
  await expect(page.locator('[data-testid="audit-details-panel"]')).toContainText(reportBody.report_id);
  await expect(page.locator('[data-testid="audit-metadata"]')).toContainText(customRequestId);
});

test("monitoring exibe snapshot operacional do investigation-worker", async ({ page, request }) => {
  const estimate = await request.post("/api/v1/investigation/estimate", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      address: "0x3333333333333333333333333333333333333333",
      chains: ["ethereum"],
      depth: 3,
      report_type: "technical_basic",
      addons: []
    }
  });
  expect(estimate.status()).toBe(200);
  const estimateBody = (await estimate.json()) as any;

  const start = await request.post("/api/v1/investigation/start", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: { quote_id: estimateBody.quote_id, confirmed: true }
  });
  expect([200, 202]).toContain(start.status());
  const startBody = (await start.json()) as any;

  await loginAsAdmin(page);
  await page.goto("/monitoring");
  await page.click('[data-testid="worker-refresh-btn"]');

  await expect(page.locator('[data-testid="worker-metric-concurrency"]')).toContainText("org");
  await expect(page.locator('[data-testid="worker-case-row"]').first()).toBeVisible();
  await expect(page.locator('[data-testid="worker-case-row"]').first()).toContainText(startBody.case_id);
});

test("monitoring permite reprocessar case em DLQ", async ({ page, request }) => {
  const estimate = await request.post("/api/v1/investigation/estimate", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      address: "0xfeed000000000000000000000000000000000000",
      chains: ["ethereum"],
      depth: 3,
      report_type: "technical_basic",
      addons: []
    }
  });
  expect(estimate.status()).toBe(200);
  const estimateBody = (await estimate.json()) as any;

  const start = await request.post("/api/v1/investigation/start", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: { quote_id: estimateBody.quote_id, confirmed: true }
  });
  expect([200, 202]).toContain(start.status());
  const startBody = (await start.json()) as any;

  let currentStatus = "queued";
  for (let i = 0; i < 30; i += 1) {
    const status = await request.get(`/api/v1/investigation/${startBody.case_id}/status`, {
      headers: { "X-API-Key": API_KEY }
    });
    expect(status.status()).toBe(200);
    const statusBody = (await status.json()) as any;
    currentStatus = statusBody.status;
    if (currentStatus === "failed") {
      break;
    }
    await page.waitForTimeout(1000);
  }
  expect(currentStatus).toBe("failed");

  await loginAsAdmin(page);
  await page.goto("/monitoring");
  await page.click('[data-testid="dlq-refresh-btn"]');

  const requeueButton = page.locator(`[data-testid="dlq-requeue-btn-${startBody.case_id}"]`);
  await expect(requeueButton).toBeVisible();
  await requeueButton.click();
  await expect(page.locator('[data-testid="dlq-message"]')).toContainText(startBody.case_id);

  let terminalStatus = "queued";
  for (let i = 0; i < 20; i += 1) {
    const status = await request.get(`/api/v1/investigation/${startBody.case_id}/status`, {
      headers: { "X-API-Key": API_KEY }
    });
    expect(status.status()).toBe(200);
    const statusBody = (await status.json()) as any;
    terminalStatus = statusBody.status;
    if (terminalStatus === "completed") {
      break;
    }
    await page.waitForTimeout(1000);
  }
  expect(terminalStatus).toBe("completed");
});

test("monitoring permite arquivar case em DLQ e filtrar resolvidos", async ({ page, request }) => {
  const estimate = await request.post("/api/v1/investigation/estimate", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      address: "0xfeed100000000000000000000000000000000000",
      chains: ["ethereum"],
      depth: 3,
      report_type: "technical_basic",
      addons: []
    }
  });
  expect(estimate.status()).toBe(200);
  const estimateBody = (await estimate.json()) as any;

  const start = await request.post("/api/v1/investigation/start", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: { quote_id: estimateBody.quote_id, confirmed: true }
  });
  expect([200, 202]).toContain(start.status());
  const startBody = (await start.json()) as any;

  let currentStatus = "queued";
  for (let i = 0; i < 30; i += 1) {
    const status = await request.get(`/api/v1/investigation/${startBody.case_id}/status`, {
      headers: { "X-API-Key": API_KEY }
    });
    expect(status.status()).toBe(200);
    const statusBody = (await status.json()) as any;
    currentStatus = statusBody.status;
    if (currentStatus === "failed") {
      break;
    }
    await page.waitForTimeout(1000);
  }
  expect(currentStatus).toBe("failed");

  await loginAsAdmin(page);
  await page.goto("/monitoring");
  await page.click('[data-testid="dlq-refresh-btn"]');

  const ackButton = page.locator(`[data-testid="dlq-ack-btn-${startBody.case_id}"]`);
  await expect(ackButton).toBeVisible();
  await ackButton.click();
  await expect(page.locator('[data-testid="dlq-message"]')).toContainText("acknowledged");
  await expect(page.locator(`[data-testid="dlq-ack-btn-${startBody.case_id}"]`)).toHaveCount(0);

  await page.selectOption('[data-testid="dlq-filter-state"]', "resolved");
  await page.click('[data-testid="dlq-refresh-btn"]');

  const resolvedRow = page.locator('[data-testid="dlq-case-row"]').filter({ hasText: startBody.case_id });
  await expect(resolvedRow).toBeVisible();
  await expect(resolvedRow).toContainText("ack_from_monitoring_ui");
});

test("monitoring exibe alerta operacional quando ha item aberto em DLQ", async ({ page, request }) => {
  const estimate = await request.post("/api/v1/investigation/estimate", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      address: "0xfeed200000000000000000000000000000000000",
      chains: ["ethereum"],
      depth: 3,
      report_type: "technical_basic",
      addons: []
    }
  });
  expect(estimate.status()).toBe(200);
  const estimateBody = (await estimate.json()) as any;

  const start = await request.post("/api/v1/investigation/start", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: { quote_id: estimateBody.quote_id, confirmed: true }
  });
  expect([200, 202]).toContain(start.status());
  const startBody = (await start.json()) as any;

  let currentStatus = "queued";
  for (let i = 0; i < 30; i += 1) {
    const status = await request.get(`/api/v1/investigation/${startBody.case_id}/status`, {
      headers: { "X-API-Key": API_KEY }
    });
    expect(status.status()).toBe(200);
    const statusBody = (await status.json()) as any;
    currentStatus = statusBody.status;
    if (currentStatus === "failed") {
      break;
    }
    await page.waitForTimeout(1000);
  }
  expect(currentStatus).toBe("failed");

  await loginAsAdmin(page);
  await page.goto("/monitoring");
  await page.click('[data-testid="worker-alerts-refresh-btn"]');

  await expect(page.locator('[data-testid="worker-alerts-summary"]')).toContainText("abertos:");
  const alertRow = page.locator('[data-testid="worker-operational-alert"]').filter({ hasText: "Itens abertos em DLQ" });
  await expect(alertRow).toBeVisible();
  await expect(alertRow).toContainText("critical");
  await expect(page.locator('[data-testid="worker-metrics-preview"]')).toContainText("ontrack_investigation_states_dlq_failed");
});

test("monitoring exibe incidentes globais recebidos do Alertmanager", async ({ page, request }) => {
  const alertname = `SyntheticPlatformVisible-${Date.now()}`;
  const trigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname,
      service: "platform",
      severity: "warning",
      summary: "Incidente sintetico para visibilidade na UI",
      description: "Garante um incidente global deterministico na listagem administrativa"
    }
  });
  expect(trigger.status()).toBe(200);

  await loginAsAdmin(page);
  await page.goto("/monitoring");
  await page.selectOption('[data-testid="platform-alert-filter-status"]', "firing");
  await page.selectOption('[data-testid="platform-alert-filter-triage"]', "pending");
  await page.selectOption('[data-testid="platform-alert-filter-service"]', "platform");
  await page.selectOption('[data-testid="platform-alert-filter-severity"]', "warning");
  await page.click('[data-testid="platform-alerts-refresh-btn"]');

  await expect(page.locator('[data-testid="platform-alerts-summary"]')).toContainText("incidentes:");
  const watchdogRow = page.locator('[data-testid="platform-alert-row"]').filter({ hasText: alertname });
  await expect(watchdogRow).toBeVisible();
  await expect(watchdogRow).toContainText("platform");
  await expect(watchdogRow).toContainText("monitoring-webhook");
});

test("monitoring admin operational alerts suporta cursor pagination", async ({ request }) => {
  const service = `pagination-service-${Date.now()}`;
  const createdAlertNames: string[] = [];

  for (let index = 0; index < 3; index += 1) {
    const alertname = `SyntheticPagination-${Date.now()}-${index}`;
    createdAlertNames.push(alertname);
    const trigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
      headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
      data: {
        alertname,
        service,
        severity: "warning",
        summary: "Incidente sintetico para paginação",
        description: "Valida paginação cursor-based de incidentes operacionais"
      }
    });
    expect(trigger.status()).toBe(200);
  }

  const firstPage = await request.get(`/api/v1/monitoring/admin/operational-alerts?service=${encodeURIComponent(service)}&limit=2`, {
    headers: { "X-API-Key": API_KEY, "X-Role": "ADMIN" }
  });
  expect(firstPage.status()).toBe(200);
  const firstBody = (await firstPage.json()) as any;
  expect(firstBody.severity_filter).toBeNull();
  expect(firstBody.total_count).toBe(3);
  expect(firstBody.count).toBe(2);
  expect(firstBody.has_more).toBeTruthy();
  expect(typeof firstBody.next_cursor).toBe("string");

  const firstIds = new Set((firstBody.data ?? []).map((entry: any) => entry.id));
  const firstNames = new Set((firstBody.data ?? []).map((entry: any) => entry.alertname));

  const secondPage = await request.get(
    `/api/v1/monitoring/admin/operational-alerts?service=${encodeURIComponent(service)}&limit=2&cursor=${encodeURIComponent(firstBody.next_cursor)}`,
    { headers: { "X-API-Key": API_KEY, "X-Role": "ADMIN" } }
  );
  expect(secondPage.status()).toBe(200);
  const secondBody = (await secondPage.json()) as any;
  expect(secondBody.severity_filter).toBeNull();
  expect(secondBody.total_count).toBe(3);
  expect(secondBody.count).toBe(1);
  expect(secondBody.has_more).toBeFalsy();
  expect(secondBody.next_cursor).toBeNull();

  const secondNames = new Set((secondBody.data ?? []).map((entry: any) => entry.alertname));
  for (const entry of secondBody.data ?? []) {
    expect(firstIds.has(entry.id)).toBeFalsy();
  }

  const combinedNames = new Set([...firstNames, ...secondNames]);
  expect(combinedNames).toEqual(new Set(createdAlertNames));
});

test("monitoring navega entre paginas de incidentes globais", async ({ page, request }) => {
  const prefix = `SyntheticPlatformPage-${Date.now()}`;

  for (let index = 0; index < 21; index += 1) {
    const trigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
      headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
      data: {
        alertname: `${prefix}-${index}`,
        service: "platform",
        severity: "warning",
        summary: "Incidente sintetico para navegacao paginada",
        description: "Valida os botoes Anterior e Proxima na UI administrativa"
      }
    });
    expect(trigger.status()).toBe(200);
  }

  await loginAsAdmin(page);
  await page.goto("/monitoring");
  await page.selectOption('[data-testid="platform-alert-filter-status"]', "firing");
  await page.selectOption('[data-testid="platform-alert-filter-triage"]', "pending");
  await page.selectOption('[data-testid="platform-alert-filter-service"]', "platform");
  await page.selectOption('[data-testid="platform-alert-filter-severity"]', "warning");
  await page.click('[data-testid="platform-alerts-refresh-btn"]');

  const summary = page.locator('[data-testid="platform-alerts-summary"]');
  const prevButton = page.locator('[data-testid="platform-alerts-prev-btn"]');
  const nextButton = page.locator('[data-testid="platform-alerts-next-btn"]');
  const syntheticRows = page.locator('[data-testid="platform-alert-row"]').filter({ hasText: prefix });

  await expect(summary).toContainText("incidentes:");
  await expect(summary).toContainText("/");
  await expect(summary).toContainText("página 1 de");
  await expect(prevButton).toBeDisabled();
  await expect(nextButton).toBeEnabled();
  await expect(syntheticRows.first()).toBeVisible();

  await nextButton.click();
  await expect(summary).toContainText("página 2 de");
  await expect(prevButton).toBeEnabled();
  await expect(syntheticRows.first()).toBeVisible();

  await prevButton.click();
  await expect(summary).toContainText("página 1 de");
  await expect(prevButton).toBeDisabled();
  await expect(syntheticRows.first()).toBeVisible();
});

test("monitoring permite reconhecer incidente global de plataforma", async ({ page, request }) => {
  const alertname = `SyntheticPlatformAck-${Date.now()}`;
  const trigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname,
      service: "platform",
      severity: "warning",
      summary: "Incidente sintetico para triagem",
      description: "Fluxo de reconhecimento manual via UI"
    }
  });
  expect(trigger.status()).toBe(200);

  await loginAsAdmin(page);
  await page.goto("/monitoring");
  await page.selectOption('[data-testid="platform-alert-filter-status"]', "firing");
  await page.selectOption('[data-testid="platform-alert-filter-triage"]', "pending");
  await page.selectOption('[data-testid="platform-alert-filter-service"]', "platform");
  await page.selectOption('[data-testid="platform-alert-filter-severity"]', "warning");
  await page.click('[data-testid="platform-alerts-refresh-btn"]');

  const incidentRow = page.locator('[data-testid="platform-alert-row"]').filter({ hasText: alertname });
  await expect(incidentRow).toBeVisible();
  const ackButton = incidentRow.locator("button").filter({ hasText: "Reconhecer" });
  await ackButton.click();

  await expect(page.locator('[data-testid="platform-alert-message"]')).toContainText("acknowledged");
  await expect(incidentRow).toHaveCount(0);

  await page.selectOption('[data-testid="platform-alert-filter-triage"]', "acknowledged");
  await page.click('[data-testid="platform-alerts-refresh-btn"]');
  const acknowledgedRow = page.locator('[data-testid="platform-alert-row"]').filter({ hasText: alertname });
  await expect(acknowledgedRow).toBeVisible();
  await expect(acknowledgedRow).toContainText("triagem=Reconhecido");
});

test("monitoring admin operational alerts suporta reconhecimento em lote", async ({ request }) => {
  const service = `batch-ack-service-${Date.now()}`;

  for (let index = 0; index < 2; index += 1) {
    const trigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
      headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
      data: {
        alertname: `SyntheticBatchAck-${Date.now()}-${index}`,
        service,
        severity: "warning",
        summary: "Incidente para reconhecimento em lote",
        description: "Valida o endpoint administrativo de ack em lote"
      }
    });
    expect(trigger.status()).toBe(200);
  }

  const batchAck = await request.post("/api/v1/monitoring/admin/operational-alerts/acknowledge-batch", {
    headers: { "X-API-Key": API_KEY, "X-Role": "ADMIN", "content-type": "application/json" },
    data: {
      service,
      severity: "warning",
      note: "ack_batch_from_monitoring_ui",
      triaged_by: "admin_ui"
    }
  });
  expect(batchAck.status()).toBe(200);
  const batchBody = (await batchAck.json()) as any;
  expect(batchBody.updated_count).toBe(2);
  expect(batchBody.selected_count).toBe(0);
  expect(batchBody.service_filter).toBe(service);
  expect(batchBody.severity_filter).toBe("warning");
  expect(batchBody.triage_status).toBe("acknowledged");

  const pending = await request.get(
    `/api/v1/monitoring/admin/operational-alerts?service=${encodeURIComponent(service)}&severity=warning&triage_status=pending&limit=10`,
    { headers: { "X-API-Key": API_KEY, "X-Role": "ADMIN" } }
  );
  expect(pending.status()).toBe(200);
  const pendingBody = (await pending.json()) as any;
  expect(pendingBody.total_count).toBe(0);
});

test("monitoring admin operational alerts suporta filtro por severity", async ({ request }) => {
  const service = `severity-filter-service-${Date.now()}`;
  const warningAlert = `SyntheticSeverityWarning-${Date.now()}`;
  const criticalAlert = `SyntheticSeverityCritical-${Date.now()}`;

  const warningTrigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname: warningAlert,
      service,
      severity: "warning",
      summary: "Incidente warning para filtro",
      description: "Valida filtro administrativo por severity"
    }
  });
  expect(warningTrigger.status()).toBe(200);

  const criticalTrigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname: criticalAlert,
      service,
      severity: "critical",
      summary: "Incidente critical para filtro",
      description: "Valida filtro administrativo por severity"
    }
  });
  expect(criticalTrigger.status()).toBe(200);

  const filtered = await request.get(
    `/api/v1/monitoring/admin/operational-alerts?service=${encodeURIComponent(service)}&severity=critical&limit=10`,
    { headers: { "X-API-Key": API_KEY, "X-Role": "ADMIN" } }
  );
  expect(filtered.status()).toBe(200);
  const body = (await filtered.json()) as any;
  expect(body.severity_filter).toBe("critical");
  expect(body.total_count).toBe(1);
  expect(body.count).toBe(1);
  expect((body.data ?? []).map((entry: any) => entry.alertname)).toEqual([criticalAlert]);
});

test("monitoring admin operational alerts suporta filtro por receiver", async ({ request }) => {
  const service = `receiver-filter-service-${Date.now()}`;
  const webhookAlert = `SyntheticReceiverWebhook-${Date.now()}`;
  const testAlert = `SyntheticReceiverTest-${Date.now()}`;

  const webhookTrigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname: webhookAlert,
      service,
      receiver: "monitoring-webhook",
      severity: "warning",
      summary: "Incidente webhook para filtro",
      description: "Valida filtro administrativo por receiver"
    }
  });
  expect(webhookTrigger.status()).toBe(200);

  const testTrigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname: testAlert,
      service,
      receiver: "monitoring-test",
      severity: "warning",
      summary: "Incidente test para filtro",
      description: "Valida filtro administrativo por receiver"
    }
  });
  expect(testTrigger.status()).toBe(200);

  const filtered = await request.get(
    `/api/v1/monitoring/admin/operational-alerts?service=${encodeURIComponent(service)}&receiver=monitoring-test&limit=10`,
    { headers: { "X-API-Key": API_KEY, "X-Role": "ADMIN" } }
  );
  expect(filtered.status()).toBe(200);
  const body = (await filtered.json()) as any;
  expect(body.receiver_filter).toBe("monitoring-test");
  expect(body.total_count).toBe(1);
  expect(body.count).toBe(1);
  expect((body.data ?? []).map((entry: any) => entry.alertname)).toEqual([testAlert]);
});

test("monitoring admin operational alerts expõe opcoes dinamicas de service e receiver", async ({ request }) => {
  const service = `dynamic-service-${Date.now()}`;
  const receiver = `dynamic-receiver-${Date.now()}`;
  const trigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname: `SyntheticDynamicFilterOptions-${Date.now()}`,
      service,
      receiver,
      severity: "warning",
      summary: "Incidente para opcoes dinamicas",
      description: "Valida catalogo dinamico de service e receiver"
    }
  });
  expect(trigger.status()).toBe(200);

  const options = await request.get("/api/v1/monitoring/admin/operational-alerts/filter-options", {
    headers: { "X-API-Key": API_KEY, "X-Role": "ADMIN" }
  });
  expect(options.status()).toBe(200);
  const body = (await options.json()) as any;
  expect(body.services).toContain(service);
  expect(body.receivers).toContain(receiver);
});

test("monitoring admin operational alerts exporta recorte filtrado em csv", async ({ request }) => {
  const service = `export-filtered-service-${Date.now()}`;
  const receiver = `export-filtered-receiver-${Date.now()}`;
  const includedAlert = `SyntheticExportFilteredIncluded-${Date.now()}`;
  const excludedAlert = `SyntheticExportFilteredExcluded-${Date.now()}`;

  const includedTrigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname: includedAlert,
      service,
      receiver,
      severity: "warning",
      summary: "Incidente incluso no export filtrado",
      description: "Valida export csv do recorte filtrado"
    }
  });
  expect(includedTrigger.status()).toBe(200);

  const excludedTrigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname: excludedAlert,
      service,
      receiver: "monitoring-webhook",
      severity: "warning",
      summary: "Incidente fora do export filtrado",
      description: "Valida exclusao por filtro no export csv"
    }
  });
  expect(excludedTrigger.status()).toBe(200);

  const exported = await request.post("/api/v1/monitoring/admin/operational-alerts/export", {
    headers: { "X-API-Key": API_KEY, "X-Role": "ADMIN", "content-type": "application/json" },
    data: {
      format: "csv",
      scope: "filtered",
      status: "firing",
      triage_status: "pending",
      service,
      receiver,
      severity: "warning"
    }
  });
  expect(exported.status()).toBe(200);
  expect(exported.headers()["content-type"]).toContain("text/csv");
  expect(exported.headers()["content-disposition"]).toContain("operational-alerts-filtered-");
  const csv = await exported.text();
  expect(csv).toContain(includedAlert);
  expect(csv).not.toContain(excludedAlert);
});

test("monitoring registra auditoria do export administrativo por request_id", async ({ page, request }) => {
  const service = `export-audit-service-${Date.now()}`;
  const receiver = `export-audit-receiver-${Date.now()}`;
  const requestId = `pw-monitoring-export-audit-${Date.now()}`;
  const alertname = `SyntheticExportAudit-${Date.now()}`;

  const trigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname,
      service,
      receiver,
      severity: "warning",
      summary: "Incidente para auditoria do export",
      description: "Valida audit_logs do export administrativo"
    }
  });
  expect(trigger.status()).toBe(200);

  await loginAsAdmin(page);
  const exported = await page.request.post("/api/app/monitoring/operational-alerts/export", {
    headers: { "content-type": "application/json", "x-request-id": requestId },
    data: {
      format: "json",
      scope: "filtered",
      status: "firing",
      triage_status: "pending",
      service,
      receiver,
      severity: "warning"
    }
  });
  expect(exported.status()).toBe(200);

  const logs = await page.request.get(
    `/api/app/audit/logs?request_id=${encodeURIComponent(requestId)}&action=operational_alerts_exported&limit=20`
  );
  expect(logs.status()).toBe(200);
  const logsBody = (await logs.json()) as any;
  const entries = logsBody.data ?? [];
  expect(entries.length).toBeGreaterThan(0);
  const entry = entries[0];
  expect(entry.action).toBe("operational_alerts_exported");
  expect(entry.resource_type).toBe("operational_alerts");
  expect(entry.metadata?.request_id).toBe(requestId);
  expect(entry.metadata?.format).toBe("json");
  expect(entry.metadata?.scope).toBe("filtered");
  expect(entry.metadata?.filters?.service).toBe(service);
  expect(entry.metadata?.filters?.receiver).toBe(receiver);
  expect(entry.metadata?.exported_count).toBeGreaterThanOrEqual(1);
});

test("monitoring permite filtrar incidentes globais por receiver", async ({ page, request }) => {
  const service = "report-api";
  const webhookAlert = `SyntheticReceiverUiWebhook-${Date.now()}`;
  const testAlert = `SyntheticReceiverUiTest-${Date.now()}`;

  const webhookTrigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname: webhookAlert,
      service,
      receiver: "monitoring-webhook",
      severity: "warning",
      summary: "Incidente webhook para filtro UI",
      description: "Valida filtro de receiver na UI"
    }
  });
  expect(webhookTrigger.status()).toBe(200);

  const testTrigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname: testAlert,
      service,
      receiver: "monitoring-test",
      severity: "warning",
      summary: "Incidente test para filtro UI",
      description: "Valida filtro de receiver na UI"
    }
  });
  expect(testTrigger.status()).toBe(200);

  await loginAsAdmin(page);
  await page.goto("/monitoring");
  await page.selectOption('[data-testid="platform-alert-filter-status"]', "firing");
  await page.selectOption('[data-testid="platform-alert-filter-triage"]', "pending");
  await page.selectOption('[data-testid="platform-alert-filter-service"]', service);
  await page.selectOption('[data-testid="platform-alert-filter-receiver"]', "monitoring-test");
  await page.selectOption('[data-testid="platform-alert-filter-severity"]', "warning");
  await page.click('[data-testid="platform-alerts-refresh-btn"]');

  await expect(page.locator('[data-testid="platform-alert-row"]').filter({ hasText: testAlert }).first()).toBeVisible();
  await expect(page.locator('[data-testid="platform-alert-row"]').filter({ hasText: webhookAlert })).toHaveCount(0);
});

test("monitoring carrega dinamicamente opcoes de service e receiver na UI", async ({ page, request }) => {
  const service = `dynamic-ui-service-${Date.now()}`;
  const receiver = `dynamic-ui-receiver-${Date.now()}`;
  const selectedAlert = `SyntheticDynamicUiSelected-${Date.now()}`;
  const otherAlert = `SyntheticDynamicUiOther-${Date.now()}`;

  const selectedTrigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname: selectedAlert,
      service,
      receiver,
      severity: "warning",
      summary: "Incidente para opcoes dinamicas na UI",
      description: "Valida select dinamico de service e receiver"
    }
  });
  expect(selectedTrigger.status()).toBe(200);

  const otherTrigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname: otherAlert,
      service,
      receiver: "monitoring-webhook",
      severity: "warning",
      summary: "Incidente alternativo para opcoes dinamicas na UI",
      description: "Garante filtragem correta por receiver dinamico"
    }
  });
  expect(otherTrigger.status()).toBe(200);

  await loginAsAdmin(page);
  await page.goto("/monitoring");
  await page.selectOption('[data-testid="platform-alert-filter-status"]', "firing");
  await page.selectOption('[data-testid="platform-alert-filter-triage"]', "pending");
  await page.selectOption('[data-testid="platform-alert-filter-service"]', service);
  await page.selectOption('[data-testid="platform-alert-filter-receiver"]', receiver);
  await page.selectOption('[data-testid="platform-alert-filter-severity"]', "warning");
  await page.click('[data-testid="platform-alerts-refresh-btn"]');

  await expect(page.locator('[data-testid="platform-alert-row"]').filter({ hasText: selectedAlert }).first()).toBeVisible();
  await expect(page.locator('[data-testid="platform-alert-row"]').filter({ hasText: otherAlert })).toHaveCount(0);
});

test("monitoring exporta incidentes selecionados em json pela UI", async ({ page, request }) => {
  const service = `export-selected-service-${Date.now()}`;
  const receiver = `export-selected-receiver-${Date.now()}`;
  const selectedAlert = `SyntheticExportSelected-${Date.now()}`;
  const unselectedAlert = `SyntheticExportUnselected-${Date.now()}`;

  const selectedTrigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname: selectedAlert,
      service,
      receiver,
      severity: "warning",
      summary: "Incidente selecionado para export json",
      description: "Valida export json de incidentes selecionados"
    }
  });
  expect(selectedTrigger.status()).toBe(200);

  const unselectedTrigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname: unselectedAlert,
      service,
      receiver,
      severity: "warning",
      summary: "Incidente nao selecionado para export json",
      description: "Valida escopo selected no export json"
    }
  });
  expect(unselectedTrigger.status()).toBe(200);

  await loginAsAdmin(page);
  await page.goto("/monitoring");
  await page.selectOption('[data-testid="platform-alert-filter-status"]', "firing");
  await page.selectOption('[data-testid="platform-alert-filter-triage"]', "pending");
  await page.selectOption('[data-testid="platform-alert-filter-service"]', service);
  await page.selectOption('[data-testid="platform-alert-filter-receiver"]', receiver);
  await page.selectOption('[data-testid="platform-alert-filter-severity"]', "warning");
  await page.click('[data-testid="platform-alerts-refresh-btn"]');

  const selectedRow = page.locator('[data-testid="platform-alert-row"]').filter({ hasText: selectedAlert }).first();
  await expect(selectedRow).toBeVisible();
  await selectedRow.locator('input[type="checkbox"]').check();
  await expect(page.locator('[data-testid="platform-alerts-summary"]')).toContainText("selecionados: 1");
  await page.selectOption('[data-testid="platform-alert-export-format"]', "json");

  const downloadPromise = page.waitForEvent("download");
  await page.click('[data-testid="platform-alerts-export-selected-btn"]');
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain("operational-alerts-selected-");
  expect(download.suggestedFilename()).toContain(".json");

  const downloadPath = await download.path();
  expect(downloadPath).toBeTruthy();
  const exported = await readFile(downloadPath!, "utf8");
  expect(exported).toContain(selectedAlert);
  expect(exported).not.toContain(unselectedAlert);
  await expect(page.locator('[data-testid="platform-alert-message"]')).toContainText("Exportação concluída");
});

test("monitoring permite reconhecer em lote os incidentes filtrados", async ({ page, request }) => {
  const prefix = `SyntheticBatchUi-${Date.now()}`;

  for (let index = 0; index < 2; index += 1) {
    const trigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
      headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
      data: {
        alertname: `${prefix}-${index}`,
        service: "report-api",
        severity: "critical",
        summary: "Incidente para ack em lote pela UI",
        description: "Valida a ação Reconhecer filtrados no monitoring"
      }
    });
    expect(trigger.status()).toBe(200);
  }

  await loginAsAdmin(page);
  await page.goto("/monitoring");
  await page.selectOption('[data-testid="platform-alert-filter-status"]', "firing");
  await page.selectOption('[data-testid="platform-alert-filter-triage"]', "pending");
  await page.selectOption('[data-testid="platform-alert-filter-service"]', "report-api");
  await page.selectOption('[data-testid="platform-alert-filter-severity"]', "critical");
  await page.click('[data-testid="platform-alerts-refresh-btn"]');

  const rows = page.locator('[data-testid="platform-alert-row"]').filter({ hasText: prefix });
  await expect(rows.first()).toBeVisible();

  page.once("dialog", (dialog) => dialog.accept());
  await page.click('[data-testid="platform-alerts-ack-batch-btn"]');

  await expect(page.locator('[data-testid="platform-alert-message"]')).toContainText("reconhecidos em lote");
  await expect(page.locator('[data-testid="platform-alert-row"]').filter({ hasText: prefix })).toHaveCount(0);

  await page.selectOption('[data-testid="platform-alert-filter-triage"]', "acknowledged");
  await page.click('[data-testid="platform-alerts-refresh-btn"]');
  await expect(page.locator('[data-testid="platform-alert-row"]').filter({ hasText: prefix }).first()).toBeVisible();
});

test("monitoring permite selecionar manualmente incidentes e reconhecer apenas os escolhidos", async ({ page, request }) => {
  const prefix = `SyntheticManualSelect-${Date.now()}`;

  for (let index = 0; index < 3; index += 1) {
    const trigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
      headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
      data: {
        alertname: `${prefix}-${index}`,
        service: "monitoring-api",
        severity: "warning",
        summary: "Incidente para selecao manual",
        description: "Valida ack parcial por ids na UI"
      }
    });
    expect(trigger.status()).toBe(200);
  }

  await loginAsAdmin(page);
  await page.goto("/monitoring");
  await page.selectOption('[data-testid="platform-alert-filter-status"]', "firing");
  await page.selectOption('[data-testid="platform-alert-filter-triage"]', "pending");
  await page.selectOption('[data-testid="platform-alert-filter-service"]', "monitoring-api");
  await page.selectOption('[data-testid="platform-alert-filter-severity"]', "warning");
  await page.click('[data-testid="platform-alerts-refresh-btn"]');

  const rows = page.locator('[data-testid="platform-alert-row"]').filter({ hasText: prefix });
  await expect(rows).toHaveCount(3);

  const selectedRow = rows.nth(0);
  const selectedName = (await selectedRow.locator("strong").textContent()) ?? "";
  await selectedRow.locator('input[type="checkbox"]').check();
  await expect(page.locator('[data-testid="platform-alerts-ack-selected-btn"]')).toContainText("(1)");

  page.once("dialog", (dialog) => dialog.accept());
  await page.click('[data-testid="platform-alerts-ack-selected-btn"]');

  await expect(page.locator('[data-testid="platform-alert-message"]')).toContainText("1 incidentes selecionados reconhecidos");
  await expect(page.locator('[data-testid="platform-alert-row"]').filter({ hasText: selectedName })).toHaveCount(0);
  await expect(page.locator('[data-testid="platform-alert-row"]').filter({ hasText: prefix })).toHaveCount(2);

  await page.selectOption('[data-testid="platform-alert-filter-triage"]', "acknowledged");
  await page.click('[data-testid="platform-alerts-refresh-btn"]');
  await expect(page.locator('[data-testid="platform-alert-row"]').filter({ hasText: selectedName }).first()).toBeVisible();
});

test("monitoring preserva selecao manual entre paginas do mesmo recorte", async ({ page, request }) => {
  const prefix = `SyntheticSelectionPersistence-${Date.now()}`;

  for (let index = 0; index < 21; index += 1) {
    const trigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
      headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
      data: {
        alertname: `${prefix}-${index}`,
        service: "monitoring-api",
        severity: "warning",
        summary: "Incidente para persistencia de selecao",
        description: "Valida selecao manual em multiplas paginas"
      }
    });
    expect(trigger.status()).toBe(200);
  }

  await loginAsAdmin(page);
  await page.goto("/monitoring");
  await page.selectOption('[data-testid="platform-alert-filter-status"]', "firing");
  await page.selectOption('[data-testid="platform-alert-filter-triage"]', "pending");
  await page.selectOption('[data-testid="platform-alert-filter-service"]', "monitoring-api");
  await page.selectOption('[data-testid="platform-alert-filter-severity"]', "warning");
  await page.click('[data-testid="platform-alerts-refresh-btn"]');

  const summary = page.locator('[data-testid="platform-alerts-summary"]');
  const firstPageRows = page.locator('[data-testid="platform-alert-row"]').filter({ hasText: prefix });
  await expect(firstPageRows).toHaveCount(20);

  const firstSelectedRow = firstPageRows.nth(0);
  const firstSelectedName = (await firstSelectedRow.locator("strong").textContent()) ?? "";
  await firstSelectedRow.locator('input[type="checkbox"]').check();
  await expect(summary).toContainText("selecionados: 1");

  await page.click('[data-testid="platform-alerts-next-btn"]');
  const secondPageRows = page.locator('[data-testid="platform-alert-row"]').filter({ hasText: prefix });
  await expect(secondPageRows).toHaveCount(1);
  await expect(summary).toContainText("selecionados: 1");

  const secondSelectedRow = secondPageRows.nth(0);
  const secondSelectedName = (await secondSelectedRow.locator("strong").textContent()) ?? "";
  await secondSelectedRow.locator('input[type="checkbox"]').check();
  await expect(summary).toContainText("selecionados: 2");
  await expect(page.locator('[data-testid="platform-alerts-ack-selected-btn"]')).toContainText("(2)");

  page.once("dialog", (dialog) => dialog.accept());
  await page.click('[data-testid="platform-alerts-ack-selected-btn"]');
  await expect(page.locator('[data-testid="platform-alert-message"]')).toContainText("2 incidentes selecionados reconhecidos");
  await expect(summary).toContainText("selecionados: 0");

  await page.selectOption('[data-testid="platform-alert-filter-triage"]', "acknowledged");
  await page.click('[data-testid="platform-alerts-refresh-btn"]');
  await expect(page.locator('[data-testid="platform-alert-row"]').filter({ hasText: firstSelectedName }).first()).toBeVisible();
  await expect(page.locator('[data-testid="platform-alert-row"]').filter({ hasText: secondSelectedName }).first()).toBeVisible();
});

test("monitoring limpa selecao quando o recorte logico muda", async ({ page, request }) => {
  const prefix = `SyntheticSelectionScopeReset-${Date.now()}`;

  const trigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
    headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
    data: {
      alertname: prefix,
      service: "report-api",
      severity: "critical",
      summary: "Incidente para reset de recorte",
      description: "Valida limpeza da selecao ao mudar filtros"
    }
  });
  expect(trigger.status()).toBe(200);

  await loginAsAdmin(page);
  await page.goto("/monitoring");
  await page.selectOption('[data-testid="platform-alert-filter-status"]', "firing");
  await page.selectOption('[data-testid="platform-alert-filter-triage"]', "pending");
  await page.selectOption('[data-testid="platform-alert-filter-service"]', "report-api");
  await page.selectOption('[data-testid="platform-alert-filter-severity"]', "critical");
  await page.click('[data-testid="platform-alerts-refresh-btn"]');

  const row = page.locator('[data-testid="platform-alert-row"]').filter({ hasText: prefix }).first();
  await expect(row).toBeVisible();
  await row.locator('input[type="checkbox"]').check();
  await expect(page.locator('[data-testid="platform-alerts-summary"]')).toContainText("selecionados: 1");

  await page.selectOption('[data-testid="platform-alert-filter-severity"]', "warning");
  await expect(page.locator('[data-testid="platform-alerts-summary"]')).toContainText("selecionados: 0");
  await expect(page.locator('[data-testid="platform-alerts-ack-selected-btn"]')).toContainText("(0)");
});

test("monitoring preserva recorte e selecao manual apos refresh da pagina", async ({ page, request }) => {
  const prefix = `SyntheticSelectionReload-${Date.now()}`;
  const service = `selection-refresh-service-${Date.now()}`;
  const receiver = `selection-refresh-receiver-${Date.now()}`;

  for (let index = 0; index < 21; index += 1) {
    const trigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
      headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
      data: {
        alertname: `${prefix}-${index}`,
        service,
        receiver,
        severity: "critical",
        summary: "Incidente para persistencia apos refresh",
        description: "Valida sessionStorage da selecao manual e da paginacao no monitoring"
      }
    });
    expect(trigger.status()).toBe(200);
  }

  await loginAsAdmin(page);
  await page.goto("/monitoring");
  await page.selectOption('[data-testid="platform-alert-filter-status"]', "firing");
  await page.selectOption('[data-testid="platform-alert-filter-triage"]', "pending");
  await page.selectOption('[data-testid="platform-alert-filter-service"]', service);
  await page.selectOption('[data-testid="platform-alert-filter-receiver"]', receiver);
  await page.selectOption('[data-testid="platform-alert-filter-severity"]', "critical");
  await page.click('[data-testid="platform-alerts-refresh-btn"]');

  const summary = page.locator('[data-testid="platform-alerts-summary"]');
  await expect(summary).toContainText("página 1 de 2");

  const firstPageRows = page.locator('[data-testid="platform-alert-row"]').filter({ hasText: prefix });
  await expect(firstPageRows).toHaveCount(20);
  await page.click('[data-testid="platform-alerts-next-btn"]');

  const row = page.locator('[data-testid="platform-alert-row"]').filter({ hasText: prefix }).first();
  await expect(row).toBeVisible();
  await expect(summary).toContainText("página 2 de 2");
  const checkbox = row.locator('input[type="checkbox"]');
  await checkbox.check();
  await expect(summary).toContainText("selecionados: 1");

  await page.reload();

  await expect(page.locator('[data-testid="platform-alert-filter-status"]')).toHaveValue("firing");
  await expect(page.locator('[data-testid="platform-alert-filter-triage"]')).toHaveValue("pending");
  await expect(page.locator('[data-testid="platform-alert-filter-service"]')).toHaveValue(service);
  await expect(page.locator('[data-testid="platform-alert-filter-receiver"]')).toHaveValue(receiver);
  await expect(page.locator('[data-testid="platform-alert-filter-severity"]')).toHaveValue("critical");
  await expect(summary).toContainText("selecionados: 1");
  await expect(summary).toContainText("página 2 de 2");

  const restoredRow = page.locator('[data-testid="platform-alert-row"]').filter({ hasText: prefix }).first();
  await expect(restoredRow).toBeVisible();
  await expect(restoredRow.locator('input[type="checkbox"]')).toBeChecked();
  await expect(page.locator('[data-testid="platform-alerts-prev-btn"]')).toBeEnabled();
  await expect(page.locator('[data-testid="platform-alerts-ack-selected-btn"]')).toContainText("(1)");
});

test("monitoring admin operational alerts suporta reconhecimento em lote por ids", async ({ request }) => {
  const service = `batch-ids-service-${Date.now()}`;
  const createdIds: string[] = [];

  for (let index = 0; index < 3; index += 1) {
    const trigger = await request.post("/api/v1/monitoring/test/trigger-operational-alert", {
      headers: { "X-API-Key": API_KEY, "content-type": "application/json" },
      data: {
        alertname: `SyntheticBatchIds-${Date.now()}-${index}`,
        service,
        severity: "warning",
        summary: "Incidente para ack por ids",
        description: "Valida o endpoint administrativo com ids explicitos"
      }
    });
    expect(trigger.status()).toBe(200);
  }

  const current = await request.get(
    `/api/v1/monitoring/admin/operational-alerts?service=${encodeURIComponent(service)}&severity=warning&triage_status=pending&limit=10`,
    { headers: { "X-API-Key": API_KEY, "X-Role": "ADMIN" } }
  );
  expect(current.status()).toBe(200);
  const currentBody = (await current.json()) as any;
  expect(currentBody.total_count).toBe(3);
  for (const entry of currentBody.data ?? []) {
    createdIds.push(entry.id);
  }

  const selectedIds = createdIds.slice(0, 2);
  const batchAck = await request.post("/api/v1/monitoring/admin/operational-alerts/acknowledge-batch", {
    headers: { "X-API-Key": API_KEY, "X-Role": "ADMIN", "content-type": "application/json" },
    data: {
      ids: selectedIds,
      service,
      severity: "warning",
      triage_status: "pending",
      note: "ack_selected_from_monitoring_ui",
      triaged_by: "admin_ui"
    }
  });
  expect(batchAck.status()).toBe(200);
  const batchBody = (await batchAck.json()) as any;
  expect(batchBody.updated_count).toBe(2);
  expect(batchBody.selected_count).toBe(2);

  const pendingAfter = await request.get(
    `/api/v1/monitoring/admin/operational-alerts?service=${encodeURIComponent(service)}&severity=warning&triage_status=pending&limit=10`,
    { headers: { "X-API-Key": API_KEY, "X-Role": "ADMIN" } }
  );
  expect(pendingAfter.status()).toBe(200);
  const pendingAfterBody = (await pendingAfter.json()) as any;
  expect(pendingAfterBody.total_count).toBe(1);
});

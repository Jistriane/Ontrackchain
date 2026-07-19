import { expect, test, type Page, type Route } from "@playwright/test";

import { type PersistedPlatformAlertSelectionState } from "../../app/lib/monitoring-platform-alerts";
import { LINKED_USER_ID, psqlExec, sqlLiteral } from "./federated-identity";
import { seedFrontendAuth } from "./seed-frontend-auth";
import { generateTotpCode } from "./totp";

type WorkItemUpdateMetadata = {
  domain?: string;
  affected_domains?: string[];
  incident_commander?: string;
  containment_status?: string;
  runbook_ref?: string;
  impact_summary?: string;
  suspected_root_cause?: string;
  confirmed_root_cause?: string;
  corrective_actions?: string[];
  evidence_refs?: string[];
  [key: string]: unknown;
};

type WorkItemUpdatePayload = {
  queue_status?: string;
  note?: string | null;
  metadata?: WorkItemUpdateMetadata;
};

type WorkItemCommentPayload = {
  comment_type?: string;
  body?: string;
};

type WorkItemCommentRecord = {
  id: string;
  work_item_id: string;
  author_user_id: string;
  comment_type: string;
  body: string;
  created_at: string;
};

type TrackedAlertWorkItem = {
  id: string;
  resource_id: string;
  queue_status: string;
  priority: string;
  due_at: string | null;
  note: string | null;
  metadata: WorkItemUpdateMetadata;
  last_activity_at: string;
  updated_at: string;
};

type LegacyPersistedPlatformAlertSelectionState = PersistedPlatformAlertSelectionState & {
  selected_ids?: string[];
  scope?: string;
  saved_at?: string;
};

type DevSessionStartResponse = {
  require2fa?: boolean;
};

async function loginAsDevRole(page: Page, role: "ADMIN" | "ANALYST") {
  const session = await page.request.post("/api/session/start", {
    headers: { "content-type": "application/json" },
    data: { plan: "professional", role }
  });
  expect(session.status()).toBe(200);
  const sessionBody = (await session.json()) as DevSessionStartResponse;
  expect(sessionBody.require2fa).toBeTruthy();

  const verify = await page.request.post("/api/session/verify-2fa", {
    headers: { "content-type": "application/json" },
    data: { code: generateTotpCode() }
  });
  expect(verify.status()).toBe(200);
}

async function readPersistedPlatformAlertSelection(page: Page) {
  return page.evaluate(() => {
    const raw = window.sessionStorage.getItem("monitoring-platform-alert-selection");
    return raw ? (JSON.parse(raw) as PersistedPlatformAlertSelectionState) : null;
  });
}

async function readPersistedPlatformAlertSelectionRaw(page: Page) {
  return page.evaluate(() => {
    const raw = window.sessionStorage.getItem("monitoring-platform-alert-selection");
    return raw ? (JSON.parse(raw) as LegacyPersistedPlatformAlertSelectionState) : null;
  });
}

test.describe("alerts and dashboard context links", () => {
  test("alerts deriva links contextuais na linha operacional", async ({ page }: { page: Page }) => {
    const caseId = "55555555-5555-4555-8555-555555555555";
    const reportId = "rep-alert-01";
    const address = "0xcccccccccccccccccccccccccccccccccccccccc";

    await seedFrontendAuth(page);

    await page.route("**/api/app/monitoring/operational-alert-filter-options", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          services: ["aml-monitor"],
          receivers: ["slack"],
          generated_at: "2026-07-06T12:00:00.000Z"
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=alerts**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "work-item-alert-e2e-01",
              resource_id: "alert-e2e-01",
              queue_status: "UNDER_REVIEW",
              priority: "high",
              due_at: "2026-07-06T12:30:00.000Z",
              note: "seed",
              metadata: {
                case_id: caseId,
                report_id: reportId,
                address,
                chain: "ethereum"
              },
              last_activity_at: "2026-07-06T12:06:00.000Z",
              updated_at: "2026-07-06T12:06:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/monitoring/operational-alerts?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          generated_at: "2026-07-06T12:00:00.000Z",
          receiver_filter: null,
          service_filter: null,
          severity_filter: null,
          status_filter: null,
          triage_status_filter: null,
          cursor: null,
          limit: 20,
          count: 1,
          total_count: 1,
          has_more: false,
          next_cursor: null,
          data: [
            {
              id: "alert-e2e-01",
              receiver: "slack",
              status: "firing",
              triage_status: "pending",
              alertname: "Alert E2E",
              service: "aml-monitor",
              severity: "critical",
              fingerprint: "fp-alert-e2e-01",
              labels: {
                case_id: caseId,
                request_id: caseId,
                report_id: reportId,
                address,
                chain: "ethereum"
              },
              annotations: {
                summary: "Resumo do alerta",
                description: "Descricao do alerta"
              },
              first_received_at: "2026-07-06T12:00:00.000Z",
              last_received_at: "2026-07-06T12:05:00.000Z",
              delivery_count: 2,
              resolved_at: null,
              triaged_at: null,
              triaged_by: null,
              triage_note: null
            }
          ]
        })
      });
    });

    await page.goto("/alerts");

    await expect(page.getByTestId("platform-alert-row-alert-e2e-01")).toContainText("Alert E2E");
    await expect(page.getByTestId("platform-alert-state-alert-e2e-01")).toContainText("Critical");
    await expect(page.getByTestId("platform-alert-state-alert-e2e-01")).toContainText("Firing");
    await expect(page.getByTestId("platform-alert-state-alert-e2e-01")).toContainText("triagem=Pendente");
    await expect(page.getByTestId("platform-alert-queue-alert-e2e-01")).toContainText("em revisão");
    await expect(page.getByTestId("platform-alert-timestamps-alert-e2e-01")).not.toContainText("2026-07-06T12:00:00.000Z");
    await expect(page.locator(`a[href="/cases/${caseId}"]`)).toBeVisible();
    await expect(
      page.locator(`a[href="/audit?resource_type=case&resource_id=${caseId}&request_id=${caseId}&report_id=${reportId}"]`)
    ).toBeVisible();
    await expect(
      page.locator(`a[href="/evidence?domain=all&resource_type=case&resource_id=${caseId}&request_id=${caseId}&report_id=${reportId}"]`)
    ).toBeVisible();
    await expect(
      page.locator(
        `a[href="/investigate?address=${encodeURIComponent(address)}&chain=ethereum&report_type=technical_basic&case_id=${caseId}"]`
      )
    ).toBeVisible();
    await expect(
      page.locator(
        `a[href="/sanctions?address=${encodeURIComponent(address)}&chain=ethereum&autostart=1&case_id=${caseId}"]`
      )
    ).toBeVisible();
  });

  test("alerts persiste RCA leve no work-item rastreado", async ({ page }: { page: Page }) => {
    const caseId = "75757575-7575-4757-8757-757575757575";
    const reportId = "rep-alert-rca-01";
    const address = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    const workItemId = "work-item-alert-e2e-rca";
    let savedPayload: WorkItemUpdatePayload | null = null;
    let savedCommentPayload: WorkItemCommentPayload | null = null;
    let savedCommentBody = "";
    let comments: WorkItemCommentRecord[] = [];
    let workItem: TrackedAlertWorkItem = {
      id: workItemId,
      resource_id: "alert-e2e-rca-01",
      queue_status: "UNDER_REVIEW",
      priority: "high",
      due_at: null,
      note: "seed",
      metadata: {
        case_id: caseId,
        report_id: reportId,
        address,
        chain: "ethereum",
        severity: "critical",
        status: "firing",
        triage_status: "pending",
        alertname: "Alert RCA E2E",
        service: "aml-monitor"
      },
      last_activity_at: "2026-07-06T12:06:00.000Z",
      updated_at: "2026-07-06T12:06:00.000Z"
    };

    await seedFrontendAuth(page);

    await page.route("**/api/app/monitoring/operational-alert-filter-options", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          services: ["aml-monitor"],
          receivers: ["slack"],
          generated_at: "2026-07-06T12:00:00.000Z"
        })
      });
    });

    await page.route("**/api/app/monitoring/operational-alerts?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          generated_at: "2026-07-06T12:00:00.000Z",
          receiver_filter: null,
          service_filter: null,
          severity_filter: null,
          status_filter: null,
          triage_status_filter: null,
          cursor: null,
          limit: 20,
          count: 1,
          total_count: 1,
          has_more: false,
          next_cursor: null,
          data: [
            {
              id: "alert-e2e-rca-01",
              receiver: "slack",
              status: "firing",
              triage_status: "pending",
              alertname: "Alert RCA E2E",
              service: "aml-monitor",
              severity: "critical",
              fingerprint: "fp-alert-rca-e2e-01",
              labels: {
                case_id: caseId,
                request_id: caseId,
                report_id: reportId,
                address,
                chain: "ethereum"
              },
              annotations: {
                summary: "Resumo do alerta RCA",
                description: "Descricao do alerta RCA"
              },
              first_received_at: "2026-07-06T12:00:00.000Z",
              last_received_at: "2026-07-06T12:05:00.000Z",
              delivery_count: 2,
              resolved_at: null,
              triaged_at: null,
              triaged_by: null,
              triage_note: null
            }
          ]
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=alerts**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [workItem] })
      });
    });

    await page.route(`**/api/app/operations/work-items/${workItemId}`, async (route: Route) => {
      if (route.request().method() !== "PATCH") {
        await route.continue();
        return;
      }

      const payload = (route.request().postDataJSON() ?? {}) as WorkItemUpdatePayload;
      savedPayload = payload;
      workItem = {
        ...workItem,
        queue_status: String(payload.queue_status ?? workItem.queue_status),
        note: typeof payload.note === "string" || payload.note === null ? payload.note : workItem.note,
        metadata: payload.metadata ?? workItem.metadata,
        updated_at: "2026-07-06T12:10:00.000Z",
        last_activity_at: "2026-07-06T12:10:00.000Z"
      };

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(workItem)
      });
    });

    await page.route(`**/api/app/operations/work-items/${workItemId}/timeline`, async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          item: workItem,
          events: [],
          comments
        })
      });
    });

    await page.route(`**/api/app/operations/work-items/${workItemId}/comments`, async (route: Route) => {
      const payload = (route.request().postDataJSON() ?? {}) as WorkItemCommentPayload;
      savedCommentPayload = payload;
      savedCommentBody = typeof payload.body === "string" ? payload.body : "";
      comments = [
        {
          id: "comment-alert-rca-01",
          work_item_id: workItemId,
          author_user_id: "user-qa",
          comment_type: payload.comment_type ?? "decision",
          body: payload.body ?? "",
          created_at: "2026-07-06T12:10:30.000Z"
        }
      ];
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(comments[0])
      });
    });

    await page.goto("/alerts");

    await page.getByRole("button", { name: "Ver timeline" }).click();
    await expect(page.getByTestId("platform-alert-rca-panel")).toBeVisible();
    await page.getByTestId("platform-alert-rca-domain").fill("compliance");
    await page.getByTestId("platform-alert-rca-affected-domains").fill("compliance, monitoring");
    await page.getByTestId("platform-alert-rca-incident-commander").fill("Compliance QA");
    await page.getByTestId("platform-alert-rca-containment-status").selectOption("contained");
    await page.getByTestId("platform-alert-rca-runbook-ref").fill("runbook-18");
    await page.getByTestId("platform-alert-rca-impact-summary").fill("Atraso na triagem e risco de SLA.");
    await page.getByTestId("platform-alert-rca-suspected-root-cause").fill("Webhook intermitente.");
    await page.getByTestId("platform-alert-rca-confirmed-root-cause").fill("Retry insuficiente no receiver.");
    await page.getByTestId("platform-alert-rca-corrective-actions").fill("aumentar retry, revisar timeout");
    await page.getByTestId("platform-alert-rca-evidence-refs").fill("audit-log-1, export-rca-1");
    await page.getByTestId("platform-alert-rca-queue-status").selectOption("READY");
    await page.getByTestId("platform-alert-rca-save").click();

    await expect(page.getByTestId("platform-alert-message")).toContainText("persistida com comentário automático");
    await expect(page.getByTestId("platform-alert-rca-summary-alert-e2e-rca-01")).toContainText("domínio=compliance");
    await expect(page.getByTestId("platform-alert-rca-summary-alert-e2e-rca-01")).toContainText("contenção=contido");
    await expect(page.getByTestId("platform-alert-rca-summary-alert-e2e-rca-01")).toContainText("causa confirmada=Retry insuficiente no receiver.");
    await expect(page.getByTestId("platform-alert-history-rca-alert-e2e-rca-01")).toContainText("compliance");
    await expect(page.getByTestId("platform-alert-history-rca-alert-e2e-rca-01")).toContainText("contido");
    await expect(page.getByTestId("platform-alert-history-rca-alert-e2e-rca-01")).toContainText("Retry insuficiente no receiver.");
    await expect(page.getByText("RCA atualizada automaticamente")).toBeVisible();
    await expect(page.getByText("Causa confirmada: Retry insuficiente no receiver.")).toBeVisible();
    expect(savedPayload).not.toBeNull();
    expect(savedPayload).toMatchObject({
      queue_status: "READY",
      metadata: {
        domain: "compliance",
        affected_domains: ["compliance", "monitoring"],
        incident_commander: "Compliance QA",
        containment_status: "contained",
        runbook_ref: "runbook-18",
        impact_summary: "Atraso na triagem e risco de SLA.",
        suspected_root_cause: "Webhook intermitente.",
        confirmed_root_cause: "Retry insuficiente no receiver.",
        corrective_actions: ["aumentar retry", "revisar timeout"],
        evidence_refs: ["audit-log-1", "export-rca-1"]
      }
    });
    expect(savedCommentPayload).toMatchObject({
      comment_type: "decision"
    });
    expect(savedCommentBody).toContain("RCA atualizada automaticamente");
    expect(savedCommentBody).toContain("Status da fila: pronto");
    expect(savedCommentBody).toContain("Causa confirmada: Retry insuficiente no receiver.");
  });

  test("alerts persiste selecao manual no contrato canonico e reidrata no reload", async ({ page }: { page: Page }) => {
    await seedFrontendAuth(page);

    await page.route("**/api/app/monitoring/operational-alert-filter-options", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          services: ["aml-monitor"],
          receivers: ["slack"],
          generated_at: "2026-07-06T12:00:00.000Z"
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=alerts**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/monitoring/operational-alerts?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          generated_at: "2026-07-06T12:00:00.000Z",
          receiver_filter: null,
          service_filter: null,
          severity_filter: null,
          status_filter: null,
          triage_status_filter: null,
          cursor: null,
          limit: 20,
          count: 1,
          total_count: 1,
          has_more: false,
          next_cursor: null,
          data: [
            {
              id: "alert-persist-e2e-01",
              receiver: "slack",
              status: "firing",
              triage_status: "pending",
              alertname: "Alert Persist E2E",
              service: "aml-monitor",
              severity: "warning",
              fingerprint: "fp-alert-persist-e2e-01",
              labels: {},
              annotations: {
                summary: "Resumo do alerta persistido",
                description: "Descricao do alerta persistido"
              },
              first_received_at: "2026-07-06T12:00:00.000Z",
              last_received_at: "2026-07-06T12:05:00.000Z",
              delivery_count: 2,
              resolved_at: null,
              triaged_at: null,
              triaged_by: null,
              triage_note: null
            }
          ]
        })
      });
    });

    await page.goto("/alerts");
    await page.evaluate(() => window.sessionStorage.clear());
    await page.reload();
    await expect(page.getByTestId("platform-alerts-summary")).toContainText("selecionados: 0");

    await page.click('[data-testid="platform-alert-select-alert-persist-e2e-01"]');
    await expect(page.getByTestId("platform-alerts-summary")).toContainText("selecionados: 1");
    await expect(page.getByTestId("platform-alerts-ack-selected-btn")).toContainText("Reconhecer selecionados (1)");

    await expect.poll(() => readPersistedPlatformAlertSelection(page)).toMatchObject({
      status: "all",
      triageStatus: "all",
      service: "all",
      receiver: "all",
      severity: "all",
      cursor: null,
      cursorHistory: [],
      selectionScope: JSON.stringify({
        status: "all",
        triageStatus: "all",
        service: "all",
        receiver: "all",
        severity: "all"
      }),
      selectedIds: ["alert-persist-e2e-01"]
    });

    const persisted = (await readPersistedPlatformAlertSelectionRaw(page)) as LegacyPersistedPlatformAlertSelectionState;
    expect(persisted.selected_ids).toBeUndefined();
    expect(persisted.scope).toBeUndefined();
    expect(persisted.saved_at).toBeUndefined();

    await page.reload();
    await expect(page.getByTestId("platform-alert-select-alert-persist-e2e-01")).toBeChecked();
    await expect(page.getByTestId("platform-alerts-summary")).toContainText("selecionados: 1");
    await expect(page.getByTestId("platform-alerts-ack-selected-btn")).toContainText("Reconhecer selecionados (1)");
  });

  test("monitoring exibe resumo read-only de RCA para alerta rastreado", async ({ page }: { page: Page }) => {
    await seedFrontendAuth(page);

    await page.route("**/api/app/monitoring/watchlists", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [{ id: "watchlist-01", name: "Main watchlist", priority: "high" }]
        })
      });
    });

    await page.route("**/api/app/monitoring/alerts?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/investigation/operations", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          generated_at: "2026-07-06T12:00:00.000Z",
          queue: { ready: 1, waiting: 0, retry_pending: 0, retry_due: 0, wake_signals: 0 },
          concurrency: { org_active: 1, org_limit: 5, global_active: 1, global_limit: 20, plan: "professional" },
          throughput: { completed_last_hour: 2, failed_last_hour: 0, billing_recalc_last_hour: 0, avg_duration_ms_last_20: 42 },
          states: { queued: 1, processing: 0, dlq_failed: 0, dlq_resolved: 0 },
          recent_cases: [],
          security: {
            manual_package_mfa_violations_last_hour: 0,
            manual_package_mfa_2fa_required_last_hour: 0,
            manual_package_mfa_provider_not_homologated_last_hour: 0
          }
        })
      });
    });

    await page.route("**/api/app/investigation/alerts", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          generated_at: "2026-07-06T12:00:00.000Z",
          open_total: 0,
          critical_open_total: 0,
          alerts: []
        })
      });
    });

    await page.route("**/api/app/investigation/metrics", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "text/plain",
        body: "metrics ok"
      });
    });

    await page.route("**/api/app/investigation/dlq?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          generated_at: "2026-07-06T12:00:00.000Z",
          count: 0,
          credits_available: 100,
          filters: { state: "failed_permanent", target_chain: null, can_requeue: true, limit: 20 },
          cases: []
        })
      });
    });

    await page.route("**/api/app/monitoring/operational-alert-filter-options", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          services: ["aml-monitor"],
          receivers: ["slack"],
          generated_at: "2026-07-06T12:00:00.000Z"
        })
      });
    });

    await page.route("**/api/app/monitoring/operational-alerts?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status_filter: null,
          triage_status_filter: null,
          service_filter: null,
          receiver_filter: null,
          severity_filter: null,
          cursor: null,
          limit: 20,
          total_count: 1,
          count: 1,
          has_more: false,
          next_cursor: null,
          data: [
            {
              id: "alert-monitoring-rca-01",
              receiver: "slack",
              status: "firing",
              triage_status: "pending",
              alertname: "Alert Monitoring RCA",
              service: "aml-monitor",
              severity: "critical",
              fingerprint: "fp-monitoring-rca-01",
              labels: {},
              annotations: {
                summary: "Resumo monitoring RCA"
              },
              first_received_at: "2026-07-06T12:00:00.000Z",
              last_received_at: "2026-07-06T12:05:00.000Z",
              delivery_count: 3,
              resolved_at: null,
              triaged_at: null,
              triaged_by: null,
              triage_note: null
            }
          ]
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=alerts**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "work-item-monitoring-rca-01",
              module: "alerts",
              resource_type: "operational_alert",
              resource_id: "alert-monitoring-rca-01",
              case_id: null,
              owner_user_id: "incident-commander-01",
              assigned_by_user_id: null,
              queue_status: "READY",
              priority: "critical",
              due_at: null,
              sla_breached: false,
              title: "Alert Monitoring RCA",
              note: "seed monitoring",
              metadata: {
                domain: "compliance",
                affected_domains: ["compliance", "monitoring"],
                incident_commander: "Compliance QA",
                containment_status: "contained",
                suspected_root_cause: "Webhook intermitente.",
                confirmed_root_cause: "Retry insuficiente no receiver."
              },
              updated_at: "2026-07-06T12:06:00.000Z",
              last_activity_at: "2026-07-06T12:06:00.000Z"
            }
          ]
        })
      });
    });

    await page.goto("/monitoring");

    await expect(page.locator('[data-testid="platform-alert-row"]').filter({ hasText: "Alert Monitoring RCA" }).first()).toBeVisible();
    await expect(page.getByTestId("monitoring-platform-alert-rca-summary-alert-monitoring-rca-01")).toContainText("fila=pronto");
    await expect(page.getByTestId("monitoring-platform-alert-rca-summary-alert-monitoring-rca-01")).toContainText("contenção=contido");
    await expect(page.getByTestId("monitoring-platform-alert-rca-summary-alert-monitoring-rca-01")).toContainText("domínio=compliance");
    await expect(page.getByTestId("monitoring-platform-alert-rca-summary-alert-monitoring-rca-01")).toContainText(
      "causa confirmada=Retry insuficiente no receiver."
    );
  });

  test("dashboard deriva links contextuais na tabela de casos recentes", async ({ page }: { page: Page }) => {
    const caseId = "66666666-6666-4666-8666-666666666666";
    const address = "0xdddddddddddddddddddddddddddddddddddddddd";
    try {
      psqlExec(`
        DELETE FROM agent_runs WHERE case_id = ${sqlLiteral(caseId)};
        DELETE FROM cases WHERE id = ${sqlLiteral(caseId)};

        INSERT INTO cases (
          id,
          organization_id,
          user_id,
          title,
          case_type,
          status,
          target_address,
          target_chain,
          credits_estimated,
          credits_used,
          created_at,
          completed_at,
          metadata
        )
        VALUES (
          ${sqlLiteral(caseId)},
          '00000000-0000-0000-0000-000000000001',
          ${sqlLiteral(LINKED_USER_ID)},
          'Dashboard Recent Case',
          'investigation',
          'completed',
          ${sqlLiteral(address)},
          'ethereum',
          1.5,
          1.5,
          '2099-07-06T12:00:00.000Z'::timestamptz,
          '2099-07-06T12:10:00.000Z'::timestamptz,
          ${sqlLiteral(JSON.stringify({ report_type_canonical: "coaf_ready_report", charged_cost: 1.5 }))}::jsonb
        );
      `);

      await loginAsDevRole(page, "ADMIN");
      await page.goto("/dashboard");

      await expect(page.getByTestId(`dashboard-case-row-${caseId}`)).toContainText(caseId);
      await expect(page.getByTestId(`dashboard-case-status-${caseId}`)).toContainText("completed");
      await expect(page.getByTestId(`dashboard-case-created-at-${caseId}`)).not.toContainText("2026-07-06T12:00:00.000Z");
      await expect(page.getByTestId(`dashboard-case-completed-at-${caseId}`)).not.toContainText("2026-07-06T12:10:00.000Z");
      await expect(page.locator(`a[href="/cases/${caseId}"]`)).toBeVisible();
      await expect(
        page.locator(`a[href="/audit?resource_type=case&resource_id=${caseId}&request_id=${caseId}"]`)
      ).toBeVisible();
      await expect(
        page.locator(`a[href="/evidence?domain=all&resource_type=case&resource_id=${caseId}&request_id=${caseId}"]`)
      ).toBeVisible();
      await expect(
        page.locator(`a[href="/reports?case_id=${caseId}&report_type=coaf_ready_report"]`)
      ).toBeVisible();
      await expect(
        page.locator(
          `a[href="/sanctions?address=${encodeURIComponent(address)}&chain=ethereum&autostart=1&case_id=${caseId}"]`
        )
      ).toBeVisible();
      await expect(
        page.locator(
          `a[href="/blocks?address=${encodeURIComponent(address)}&chain=ethereum&autostart=1&case_id=${caseId}"]`
        )
      ).toBeVisible();
    } finally {
      psqlExec(`
        DELETE FROM agent_runs WHERE case_id = ${sqlLiteral(caseId)};
        DELETE FROM cases WHERE id = ${sqlLiteral(caseId)};
      `);
    }
  });

  test("dashboard esconde handoffs administrativos para analyst e exibe para admin", async ({ page }: { page: Page }) => {
    await loginAsDevRole(page, "ANALYST");
    await page.goto("/dashboard");
    await expect(page.getByTestId("dashboard-quick-action-billing")).toHaveCount(0);
    await expect(page.getByTestId("dashboard-quick-action-team")).toHaveCount(0);
    await expect(page.getByTestId("dashboard-module-team")).toHaveCount(0);
    await expect(page.locator('aside a[href="/billing"]')).toHaveCount(0);
    await expect(page.locator('aside a[href="/team"]')).toHaveCount(0);

    await loginAsDevRole(page, "ADMIN");
    await page.goto("/dashboard");
    await expect(page.getByTestId("dashboard-quick-action-billing")).toBeVisible();
    await expect(page.getByTestId("dashboard-quick-action-team")).toBeVisible();
    await expect(page.getByTestId("dashboard-module-team")).toBeVisible();
    await expect(page.locator('aside a[href="/billing"]')).toHaveCount(1);
    await expect(page.locator('aside a[href="/team"]')).toHaveCount(1);
  });
});

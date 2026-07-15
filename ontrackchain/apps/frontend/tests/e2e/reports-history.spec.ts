import { expect, test, type Page, type Route } from "@playwright/test";

import { expectDownloadLikeResponse } from "./download-helpers";

type EvidenceExportPayload = {
  report_id?: string;
  request_id?: string;
  resource_type?: string;
  resource_id?: string;
  include_reports?: boolean;
};

type FormalDossierReportPayload = {
  report_id?: string;
  case_id?: string;
  report_type?: string;
};

type FormalDossierWorkspaceSummaryPayload = {
  case_id?: string;
  owner?: string;
  priority?: string;
  status?: string;
  source?: string;
};

type FormalDossierPayload = {
  report?: FormalDossierReportPayload;
  workspace_summary?: FormalDossierWorkspaceSummaryPayload;
  has_download_audit?: boolean;
};

type ReportsAuthContextPayload = {
  org_id: string;
  user_id: string;
  linked_user_id: string;
  role: string;
  plan: string;
  auth_method: string;
  mfa_mode: string | null;
  mfa_provider_homologated: string | null;
  two_factor: string | null;
};

const LEGAL_REPORT_ROW = {
  report_id: "rep-legal-01",
  case_id: "33333333-3333-4333-8333-333333333333",
  report_type_requested: "legal",
  report_type: "legal_report",
  content_type: "application/pdf",
  file_hash_sha256: "c".repeat(64),
  onchain_hash: null,
  created_at: "2026-07-03T11:00:00.000Z",
  has_download_audit: true
} as const;

function isJsonObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readOptionalString(value: unknown) {
  return typeof value === "string" ? value : undefined;
}

function readOptionalBoolean(value: unknown) {
  return typeof value === "boolean" ? value : undefined;
}

function parseEvidenceExportPayload(route: Route): EvidenceExportPayload {
  const payload = route.request().postDataJSON();
  if (!isJsonObject(payload)) {
    return {};
  }

  return {
    report_id: readOptionalString(payload.report_id),
    request_id: readOptionalString(payload.request_id),
    resource_type: readOptionalString(payload.resource_type),
    resource_id: readOptionalString(payload.resource_id),
    include_reports: readOptionalBoolean(payload.include_reports)
  };
}

function parseFormalDossierPayload(route: Route): FormalDossierPayload {
  const payload = route.request().postDataJSON();
  if (!isJsonObject(payload)) {
    return {};
  }

  const report = isJsonObject(payload.report)
    ? {
        report_id: readOptionalString(payload.report.report_id),
        case_id: readOptionalString(payload.report.case_id),
        report_type: readOptionalString(payload.report.report_type)
      }
    : undefined;

  const workspace_summary = isJsonObject(payload.workspace_summary)
    ? {
        case_id: readOptionalString(payload.workspace_summary.case_id),
        owner: readOptionalString(payload.workspace_summary.owner),
        priority: readOptionalString(payload.workspace_summary.priority),
        status: readOptionalString(payload.workspace_summary.status),
        source: readOptionalString(payload.workspace_summary.source)
      }
    : undefined;

  return {
    report,
    workspace_summary,
    has_download_audit: readOptionalBoolean(payload.has_download_audit)
  };
}

async function seedLegalReportDetailPage(page: Page, authContext: ReportsAuthContextPayload) {
  await page.context().addCookies([
    {
      name: "otc_token",
      value: "pw-e2e-token",
      domain: "localhost",
      path: "/",
      httpOnly: false,
      secure: false,
      sameSite: "Lax"
    }
  ]);

  await page.route("**/api/app/auth/context", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(authContext)
    });
  });

  await page.route("**/api/app/report-types?**", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        generated_at: "2026-07-03T12:00:00.000Z",
        types: [
          {
            canonical: "legal_report",
            label: "Legal Report",
            available: true,
            cost_credits: 3,
            min_plan: "enterprise",
            format: "pdf",
            deprecated: false
          }
        ]
      })
    });
  });

  await page.route("**/api/app/investigation/cases?**", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ page: 1, limit: 20, data: [] })
    });
  });

  await page.route("**/api/app/operations/work-items?**", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ data: [] })
    });
  });

  await page.route("**/api/app/reports/list?**", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        data: [LEGAL_REPORT_ROW],
        page: 1,
        limit: 20,
        total: 1,
        has_more: false
      })
    });
  });

  await page.route("**/api/app/reports/rep-*", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(LEGAL_REPORT_ROW)
    });
  });
}

test.describe("reports history backend", () => {
  test("carrega historico backend, reidrata filtros e aplica recorte por report_id e janela temporal", async ({ page }) => {
    await page.context().addCookies([
      {
        name: "otc_token",
        value: "pw-e2e-token",
        domain: "localhost",
        path: "/",
        httpOnly: false,
        secure: false,
        sameSite: "Lax"
      }
    ]);

    await page.route("**/api/app/auth/context", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          org_id: "org-reports-e2e",
          user_id: "user-reports-e2e",
          linked_user_id: "linked-reports-e2e",
          role: "AUDITOR",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/report-types?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          generated_at: "2026-07-03T12:00:00.000Z",
          types: [
            {
              canonical: "technical_basic",
              label: "Technical Basic",
              available: true,
              cost_credits: 1,
              min_plan: "starter",
              format: "pdf",
              deprecated: false
            },
            {
              canonical: "coaf_ready_report",
              label: "COAF Ready",
              available: true,
              cost_credits: 2,
              min_plan: "professional",
              format: "pdf",
              deprecated: false
            }
          ]
        })
      });
    });

    await page.route("**/api/app/investigation/cases?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ page: 1, limit: 20, data: [] })
      });
    });

    await page.route("**/api/app/operations/work-items?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "work-report-02",
              resource_id: "22222222-2222-4222-8222-222222222222",
              owner_user_id: "linked-user-report-02",
              queue_status: "UNDER_REVIEW",
              priority: "high",
              due_at: "2026-07-04T15:30:00.000Z",
              note: "Aguardando validação operacional do handoff COAF.",
              metadata: {
                case_id: "22222222-2222-4222-8222-222222222222",
                target_address: "0x2222222222222222222222222222222222222222",
                target_chain: "ethereum",
                report_type: "coaf_ready_report",
                owner_label: "Compliance QA",
                local_workspace_status: "in_review",
                note: "Aguardando validação operacional do handoff COAF."
              },
              last_activity_at: "2026-07-04T12:00:00.000Z",
              updated_at: "2026-07-04T12:00:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/reports/list?**", async (route) => {
      const url = new URL(route.request().url());
      const reportId = url.searchParams.get("report_id");
      const reportType = url.searchParams.get("report_type");
      const caseId = url.searchParams.get("case_id");
      const createdFrom = url.searchParams.get("created_from");
      const createdTo = url.searchParams.get("created_to");

      const allRows = [
        {
          report_id: "rep-all-01",
          case_id: "11111111-1111-4111-8111-111111111111",
          report_type_requested: "technical",
          report_type: "technical_basic",
          content_type: "application/pdf",
          file_hash_sha256: "a".repeat(64),
          onchain_hash: null,
          created_at: "2026-07-03T10:00:00.000Z",
          has_download_audit: true
        },
        {
          report_id: "rep-all-02",
          case_id: "22222222-2222-4222-8222-222222222222",
          report_type_requested: "coaf",
          report_type: "coaf_ready_report",
          content_type: "application/pdf",
          file_hash_sha256: "b".repeat(64),
          onchain_hash: null,
          created_at: "2026-07-03T09:00:00.000Z",
          has_download_audit: false
        }
      ];

      const filteredRows = allRows.filter((row) => {
        if (reportId && row.report_id !== reportId) {
          return false;
        }
        if (reportType && row.report_type !== reportType) {
          return false;
        }
        if (caseId && row.case_id !== caseId) {
          return false;
        }
        if (createdFrom && row.created_at < createdFrom) {
          return false;
        }
        if (createdTo && row.created_at > createdTo) {
          return false;
        }
        return true;
      });

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: filteredRows,
          page: 1,
          limit: 20,
          total: filteredRows.length,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/reports/rep-*", async (route: Route) => {
      const reportId = route.request().url().split("/").pop()?.split("?")[0];
      if (reportId !== "rep-all-02") {
        await route.fulfill({
          status: 404,
          contentType: "application/json",
          body: JSON.stringify({ detail: "report_not_found" })
        });
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          report_id: "rep-all-02",
          case_id: "22222222-2222-4222-8222-222222222222",
          report_type_requested: "coaf",
          report_type: "coaf_ready_report",
          created_at: "2026-07-03T09:00:00.000Z",
          file_hash_sha256: "b".repeat(64),
          onchain_hash: null,
          content_type: "application/pdf"
        })
      });
    });

    await page.route("**/api/app/audit/evidence-export", async (route: Route) => {
      const payload = parseEvidenceExportPayload(route);
      expect(payload.report_id).toBe("rep-all-02");
      expect(payload.request_id).toBe("22222222-2222-4222-8222-222222222222");
      expect(payload.resource_type).toBe("case");
      expect(payload.resource_id).toBe("22222222-2222-4222-8222-222222222222");
      expect(payload.include_reports).toBeTruthy();

      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": 'attachment; filename="ontrackchain-evidence-bundle-rep-all-02.json"'
        },
        body: JSON.stringify({
          sections: {
            audit_logs: { count: 1 },
            reports: { count: 1 }
          }
        })
      });
    });

    await page.route("**/api/app/reports/formal-dossier", async (route: Route) => {
      const payload = parseFormalDossierPayload(route);
      const report = payload.report;
      const workspaceSummary = payload.workspace_summary;

      expect(report?.report_id).toBe("rep-all-02");
      expect(report?.case_id).toBe("22222222-2222-4222-8222-222222222222");
      expect(report?.report_type).toBe("coaf_ready_report");
      expect(payload.has_download_audit).toBeFalsy();
      expect(workspaceSummary?.case_id).toBe("22222222-2222-4222-8222-222222222222");
      expect(workspaceSummary?.owner).toBe("Compliance QA");
      expect(workspaceSummary?.priority).toBe("high");
      expect(workspaceSummary?.status).toBe("in_review");
      expect(workspaceSummary?.source).toBe("server");

      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": 'attachment; filename="ontrackchain-report-dossier-rep-all-02.json"'
        },
        body: JSON.stringify({
          package_type: "coaf_ready_report_dossier",
          workspace_summary: {
            owner: "Compliance QA",
            priority: "high"
          }
        })
      });
    });

    await page.goto(
      "/reports?history_report_id=rep-all-02&history_created_from=2026-07-03T08:30:00.000Z&history_created_to=2026-07-03T09:30:00.000Z"
    );

    await expect(page.getByTestId("reports-history-table")).toBeVisible();
    await expect(page.getByTestId("reports-history-row")).toHaveCount(1);
    await expect(page.getByTestId("reports-history-table")).toContainText("rep-all-02");
    await expect(page.getByTestId("reports-history-table")).not.toContainText("rep-all-01");
    await expect(page.getByTestId("reports-history-table")).toContainText("COAF Ready");
    await expect(page.getByTestId("reports-history-table")).toContainText("coaf_ready_report");
    await expect(page.getByTestId("reports-history-report-id")).toHaveValue("rep-all-02");
    await expect(page.locator('[data-testid="reports-history-report-type"] option[value="coaf_ready_report"]')).toHaveText(
      "COAF Ready (coaf_ready_report)"
    );
    await expect(page.locator('[data-testid="reports-cases-report-type"] option[value="coaf_ready_report"]')).toHaveText(
      "COAF Ready (coaf_ready_report)"
    );
    await expect(page.getByTestId("reports-history-created-from")).not.toHaveValue("");
    await expect(page.getByTestId("reports-history-created-to")).not.toHaveValue("");
    await expect(page.getByTestId("reports-detail-table")).toContainText("rep-all-02");
    await expect(page.getByTestId("reports-detail-table")).toContainText("COAF Ready");
    await expect(page.getByTestId("reports-detail-table")).toContainText("coaf");
    await expect(page.getByTestId("reports-detail-table")).toContainText("coaf_ready_report");
    await expect(page.getByTestId("reports-dossier-table")).toContainText("coaf_ready_report_dossier");
    await expect(page.getByTestId("reports-dossier-table")).toContainText("dossiê formal COAF-ready");
    await expect(page.getByTestId("reports-dossier-table")).toContainText("restricted_regulatory");
    await expect(page.getByTestId("reports-dossier-table")).toContainText("regulatório restrito");
    await expect(page.getByTestId("reports-dossier-table")).toContainText("download_not_audited");
    await expect(page.getByTestId("reports-dossier-table")).toContainText("download não auditado");
    await expect(page.getByTestId("reports-dossier-table")).toContainText("hash_bound");
    await expect(page.getByTestId("reports-dossier-table")).toContainText("hash vinculado");
    await expect(page.getByTestId("reports-dossier-table")).toContainText("regulatory_authority_distribution");
    await expect(page.getByTestId("reports-dossier-table")).toContainText("distribuição para autoridade regulatória");
    await expect(page.getByTestId("reports-dossier-table")).toContainText("regulatory_extended_retention");
    await expect(page.getByTestId("reports-dossier-table")).toContainText("retenção regulatória estendida");
    await expect(page.getByTestId("reports-detail-workspace-table")).toContainText("22222222-2222-4222-8222-222222222222");
    await expect(page.getByTestId("reports-detail-workspace-table")).toContainText("Compliance QA");
    await expect(page.getByTestId("reports-detail-workspace-table")).toContainText("alta");
    await expect(page.getByTestId("reports-detail-workspace-table")).toContainText("em revisão");
    await expect(page.getByTestId("reports-detail-workspace-table")).toContainText("Aguardando validação operacional do handoff COAF.");
    await expect(page.getByTestId("reports-workspace-row-22222222-2222-4222-8222-222222222222")).toContainText(
      "22222222-2222-4222-8222-222222222222"
    );
    await expect(page.getByTestId("reports-workspace-priority-22222222-2222-4222-8222-222222222222")).toContainText("alta");
    await expect(page.getByTestId("reports-workspace-source-22222222-2222-4222-8222-222222222222")).toContainText("servidor");
    await expect(page.getByTestId("reports-workspace-sla-22222222-2222-4222-8222-222222222222")).toContainText("No prazo");
    await expect(page.getByTestId("reports-workspace-deadline-22222222-2222-4222-8222-222222222222")).not.toContainText(
      "2026-07-04T15:30:00.000Z"
    );
    await expect(page.getByTestId("reports-detail-actions").locator("a")).toHaveCount(4);
    await expect(page.getByTestId("reports-detail-actions").locator('a[href*="report_id=rep-all-02"]').nth(1)).toBeVisible();

    await expectDownloadLikeResponse(
      page,
      {
        urlPart: "/api/app/audit/evidence-export",
        method: "POST",
        expectedFilename: "ontrackchain-evidence-bundle-rep-all-02.json"
      },
      async () => {
        await page.getByTestId("reports-detail-export-evidence").click();
      }
    );

    await expectDownloadLikeResponse(
      page,
      {
        urlPart: "/api/app/reports/formal-dossier",
        method: "POST",
        expectedFilename: "ontrackchain-report-dossier-rep-all-02.json"
      },
      async () => {
        await page.getByTestId("reports-detail-export-dossier").click();
      }
    );

    await page.getByTestId("reports-history-clear").click();

    await expect(page.getByTestId("reports-history-row")).toHaveCount(2);
    await expect(page.getByTestId("reports-history-table")).toContainText("rep-all-01");
    await expect(page.getByTestId("reports-history-table")).toContainText("rep-all-02");
    await expect(page.getByTestId("reports-detail-empty")).toBeVisible();

    const reportTypeField = page.getByTestId("reports-history-report-type");
    await reportTypeField.selectOption("technical_basic");
    await page.getByTestId("reports-history-apply").click();

    await expect(page.getByTestId("reports-history-row")).toHaveCount(1);
    await expect(page.getByTestId("reports-history-table")).toContainText("rep-all-01");
    await expect(page.getByTestId("reports-history-table")).not.toContainText("rep-all-02");
  });

  test("viewer nao recebe ctas de export sensivel no detalhe do report", async ({ page }) => {
    await page.context().addCookies([
      {
        name: "otc_token",
        value: "pw-e2e-token",
        domain: "localhost",
        path: "/",
        httpOnly: false,
        secure: false,
        sameSite: "Lax"
      }
    ]);

    await page.route("**/api/app/auth/context", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          org_id: "org-reports-e2e",
          user_id: "user-reports-e2e",
          linked_user_id: "linked-reports-e2e",
          role: "VIEWER",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/report-types?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          generated_at: "2026-07-03T12:00:00.000Z",
          types: [
            {
              canonical: "coaf_ready_report",
              label: "COAF Ready",
              available: true,
              cost_credits: 2,
              min_plan: "professional",
              format: "pdf",
              deprecated: false
            }
          ]
        })
      });
    });

    await page.route("**/api/app/investigation/cases?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ page: 1, limit: 20, data: [] })
      });
    });

    await page.route("**/api/app/operations/work-items?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "work-report-02",
              resource_id: "22222222-2222-4222-8222-222222222222",
              owner_user_id: "linked-user-report-02",
              queue_status: "UNDER_REVIEW",
              priority: "high",
              due_at: "2026-07-04T15:30:00.000Z",
              note: "Aguardando validação operacional do handoff COAF.",
              metadata: {
                case_id: "22222222-2222-4222-8222-222222222222",
                target_address: "0x2222222222222222222222222222222222222222",
                target_chain: "ethereum",
                report_type: "coaf_ready_report",
                owner_label: "Compliance QA",
                local_workspace_status: "in_review",
                note: "Aguardando validação operacional do handoff COAF."
              },
              last_activity_at: "2026-07-04T12:00:00.000Z",
              updated_at: "2026-07-04T12:00:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/reports/list?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              report_id: "rep-all-02",
              case_id: "22222222-2222-4222-8222-222222222222",
              report_type_requested: "coaf",
              report_type: "coaf_ready_report",
              content_type: "application/pdf",
              file_hash_sha256: "b".repeat(64),
              onchain_hash: null,
              created_at: "2026-07-03T09:00:00.000Z",
              has_download_audit: false
            }
          ],
          page: 1,
          limit: 20,
          total: 1,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/reports/rep-*", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          report_id: "rep-all-02",
          case_id: "22222222-2222-4222-8222-222222222222",
          report_type_requested: "coaf",
          report_type: "coaf_ready_report",
          created_at: "2026-07-03T09:00:00.000Z",
          file_hash_sha256: "b".repeat(64),
          onchain_hash: null,
          content_type: "application/pdf"
        })
      });
    });

    await page.goto("/reports?history_report_id=rep-all-02");

    await expect(page.getByTestId("reports-detail-table")).toHaveCount(0);
    await expect(page.getByTestId("reports-detail-empty")).toContainText(
      "O detalhe operacional do relatório está oculto nesta sessão porque a role atual não possui autorização operacional ADMIN/AUDITOR/ANALYST."
    );
    await expect(page.getByTestId("reports-detail-export-evidence")).toHaveCount(0);
    await expect(page.getByTestId("reports-detail-export-dossier")).toHaveCount(0);
    await expect(page.getByTestId("reports-detail-download")).toHaveCount(0);
  });

  test("analyst recebe CTA de download para report comum", async ({ page }) => {
    await page.context().addCookies([
      {
        name: "otc_token",
        value: "pw-e2e-token",
        domain: "localhost",
        path: "/",
        httpOnly: false,
        secure: false,
        sameSite: "Lax"
      }
    ]);

    await page.route("**/api/app/auth/context", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          org_id: "org-reports-e2e",
          user_id: "user-reports-e2e",
          linked_user_id: "linked-reports-e2e",
          role: "ANALYST",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/report-types?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          generated_at: "2026-07-03T12:00:00.000Z",
          types: [
            {
              canonical: "coaf_ready_report",
              label: "COAF Ready",
              available: true,
              cost_credits: 2,
              min_plan: "professional",
              format: "pdf",
              deprecated: false
            }
          ]
        })
      });
    });

    await page.route("**/api/app/investigation/cases?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ page: 1, limit: 20, data: [] })
      });
    });

    await page.route("**/api/app/operations/work-items?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/reports/list?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              report_id: "rep-all-04",
              case_id: "44444444-4444-4444-8444-444444444444",
              report_type_requested: "coaf",
              report_type: "coaf_ready_report",
              content_type: "application/pdf",
              file_hash_sha256: "d".repeat(64),
              onchain_hash: null,
              created_at: "2026-07-03T09:00:00.000Z",
              has_download_audit: false
            }
          ],
          page: 1,
          limit: 20,
          total: 1,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/reports/rep-*", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          report_id: "rep-all-04",
          case_id: "44444444-4444-4444-8444-444444444444",
          report_type_requested: "coaf",
          report_type: "coaf_ready_report",
          created_at: "2026-07-03T09:00:00.000Z",
          file_hash_sha256: "d".repeat(64),
          onchain_hash: null,
          content_type: "application/pdf"
        })
      });
    });

    await page.goto("/reports?history_report_id=rep-all-04");

    await expect(page.getByTestId("reports-detail-table")).toContainText("rep-all-04");
    await expect(page.getByTestId("reports-detail-download")).toBeVisible();
    await expect(page.getByTestId("reports-detail-empty")).toHaveCount(0);
    await expect(page.getByText("O download do artefato do relatório está oculto nesta sessão porque a role atual não possui autorização operacional ADMIN/AUDITOR/ANALYST.")).toHaveCount(0);
  });

  test("admin recebe erro semântico ao exportar dossiê formal quando o bff recusa a operação", async ({ page }) => {
    await page.context().addCookies([
      {
        name: "otc_token",
        value: "pw-e2e-token",
        domain: "localhost",
        path: "/",
        httpOnly: false,
        secure: false,
        sameSite: "Lax"
      }
    ]);

    await page.route("**/api/app/auth/context", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          org_id: "org-reports-e2e",
          user_id: "user-reports-e2e",
          linked_user_id: "linked-reports-e2e",
          role: "ADMIN",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true",
          two_factor: "ok"
        })
      });
    });

    await page.route("**/api/app/report-types?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          generated_at: "2026-07-03T12:00:00.000Z",
          types: [
            {
              canonical: "coaf_ready_report",
              label: "COAF Ready",
              available: true,
              cost_credits: 2,
              min_plan: "professional",
              format: "pdf",
              deprecated: false
            }
          ]
        })
      });
    });

    await page.route("**/api/app/investigation/cases?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ page: 1, limit: 20, data: [] })
      });
    });

    await page.route("**/api/app/operations/work-items?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "work-report-03",
              resource_id: "33333333-3333-4333-8333-333333333333",
              owner_user_id: "linked-user-report-03",
              queue_status: "UNDER_REVIEW",
              priority: "medium",
              due_at: "2026-07-05T15:30:00.000Z",
              note: "Aguardando auditoria do dossiê formal.",
              metadata: {
                case_id: "33333333-3333-4333-8333-333333333333",
                report_type: "coaf_ready_report",
                owner_label: "Auditoria Interna",
                local_workspace_status: "in_review",
                note: "Aguardando auditoria do dossiê formal."
              },
              last_activity_at: "2026-07-04T12:00:00.000Z",
              updated_at: "2026-07-04T12:00:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/reports/list?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              report_id: "rep-all-03",
              case_id: "33333333-3333-4333-8333-333333333333",
              report_type_requested: "coaf",
              report_type: "coaf_ready_report",
              content_type: "application/pdf",
              file_hash_sha256: "c".repeat(64),
              onchain_hash: null,
              created_at: "2026-07-03T09:00:00.000Z",
              has_download_audit: false
            }
          ],
          page: 1,
          limit: 20,
          total: 1,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/reports/rep-*", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          report_id: "rep-all-03",
          case_id: "33333333-3333-4333-8333-333333333333",
          report_type_requested: "coaf",
          report_type: "coaf_ready_report",
          created_at: "2026-07-03T09:00:00.000Z",
          file_hash_sha256: "c".repeat(64),
          onchain_hash: null,
          content_type: "application/pdf"
        })
      });
    });

    await page.route("**/api/app/reports/formal-dossier", async (route: Route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "report_formal_dossier_role_required" })
      });
    });

    await page.goto("/reports?history_report_id=rep-all-03");

    await expect(page.getByTestId("reports-detail-export-dossier")).toBeVisible();
    await page.getByTestId("reports-detail-export-dossier").click();

    await expect(page.getByText("A exportação do dossiê formal exige papel privilegiado ADMIN/AUDITOR.")).toBeVisible();
    await expect(page.getByText("report_formal_dossier_role_required")).toHaveCount(0);
  });

  test("admin com jwt e 2fa valido recebe CTA de download para legal_report", async ({ page }) => {
    await seedLegalReportDetailPage(page, {
      org_id: "org-reports-e2e",
      user_id: "user-reports-e2e",
      linked_user_id: "linked-reports-e2e",
      role: "ADMIN",
      plan: "enterprise",
      auth_method: "jwt",
      mfa_mode: "local_totp",
      mfa_provider_homologated: "false",
      two_factor: "ok"
    });

    await page.goto("/reports?history_report_id=rep-legal-01");

    await expect(page.getByTestId("reports-detail-table")).toContainText("rep-legal-01");
    await expect(page.getByTestId("reports-detail-download")).toBeVisible();
    await expect(page.getByTestId("reports-detail-download")).toHaveAttribute("href", /report_type=legal_report/);
    await expect(
      page.getByText(
        "O download de legal_report está oculto nesta sessão porque exige JWT local com papel ADMIN e segundo fator válido, ou MFA externo homologado com trilho JWT."
      )
    ).toHaveCount(0);
  });

  test("admin federado via oidc nao recebe CTA de download para legal_report", async ({ page }) => {
    await seedLegalReportDetailPage(page, {
      org_id: "org-reports-e2e",
      user_id: "user-reports-e2e",
      linked_user_id: "linked-reports-e2e",
      role: "ADMIN",
      plan: "enterprise",
      auth_method: "oidc",
      mfa_mode: "external_provider",
      mfa_provider_homologated: "true",
      two_factor: "managed_externally_homologated"
    });

    await page.goto("/reports?history_report_id=rep-legal-01");

    await expect(page.getByTestId("reports-detail-table")).toContainText("rep-legal-01");
    await expect(page.getByTestId("reports-detail-download")).toHaveCount(0);
    await expect(
      page.getByText(
        "O download de legal_report está oculto nesta sessão porque exige JWT local com papel ADMIN e segundo fator válido, ou MFA externo homologado com trilho JWT."
      )
    ).toBeVisible();
  });
});

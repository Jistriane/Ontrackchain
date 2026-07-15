import { expect, test, type Page, type Request, type Route } from "@playwright/test";

import { expectDownloadLikeResponse, expectDownloadLikeResponseWithRequest } from "./download-helpers";

type WorkItemPatchPayload = {
  queue_status?: string;
};

type EvidenceExportPayload = {
  request_id?: string;
  report_id?: string | null;
  resource_type?: string;
  resource_id?: string;
  include_reports?: boolean;
};

type ManualPackageEvidenceRequestPayload = {
  request_id?: string;
  report_id?: string | null;
};

type ManualPackageDossierPayload = {
  package_type?: string;
  signoff_mode?: string;
};

type ManualReviewPayload = {
  counterparty_context?: string;
  purpose?: string;
  amount?: number;
};

type ManualPackageWorkspaceSummaryPayload = {
  event_id?: string;
};

type ManualPackagePayload = {
  action?: string;
  scope_id?: string;
  evidence_request?: ManualPackageEvidenceRequestPayload;
  dossier?: ManualPackageDossierPayload;
  manual_review?: ManualReviewPayload;
  workspace_summary?: ManualPackageWorkspaceSummaryPayload;
};

type SignoffRequestPayload = {
  request_id?: string;
  scope_id?: string;
  manual_review_action?: string;
  package_sha256?: string;
  signoff_mode?: string;
};

type SealSignoffPayload = {
  signer_role?: string;
  decision?: string;
  signoff_method?: string;
};

type FinalizeSealPayload = {
  metadata?: {
    source?: string;
    request_id?: string;
    report_id?: string;
    package_sha256?: string;
  };
};

type TicketedPayload = {
  ticket_ref?: string;
  reason?: string;
};

type SupersedeSealPayload = TicketedPayload & {
  superseded_by_seal_id?: string;
};

function isJsonObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readOptionalString(value: unknown) {
  return typeof value === "string" ? value : undefined;
}

function readNullableString(value: unknown) {
  return typeof value === "string" || value === null ? value : undefined;
}

function readOptionalBoolean(value: unknown) {
  return typeof value === "boolean" ? value : undefined;
}

function readOptionalNumber(value: unknown) {
  return typeof value === "number" ? value : undefined;
}

function readOptionalObject(value: unknown) {
  return isJsonObject(value) ? value : undefined;
}

function readRouteJsonObject(route: Route) {
  const raw = route.request().postData();
  if (!raw) {
    return {};
  }

  try {
    const payload = JSON.parse(raw) as unknown;
    return isJsonObject(payload) ? payload : {};
  } catch {
    return {};
  }
}

function readRequestJsonObject(request: Request) {
  const raw = request.postData();
  if (!raw) {
    return {};
  }

  try {
    const payload = JSON.parse(raw) as unknown;
    return isJsonObject(payload) ? payload : {};
  } catch {
    return {};
  }
}

function parseWorkItemPatchPayload(route: Route): WorkItemPatchPayload {
  const payload = readRouteJsonObject(route);
  return {
    queue_status: readOptionalString(payload.queue_status)
  };
}

function parseEvidenceExportPayload(route: Route): EvidenceExportPayload {
  const payload = readRouteJsonObject(route);
  return {
    request_id: readOptionalString(payload.request_id),
    report_id: readNullableString(payload.report_id),
    resource_type: readOptionalString(payload.resource_type),
    resource_id: readOptionalString(payload.resource_id),
    include_reports: readOptionalBoolean(payload.include_reports)
  };
}

function parseManualPackagePayloadFromRequest(request: Request): ManualPackagePayload {
  const payload = readRequestJsonObject(request);
  const evidenceRequest = readOptionalObject(payload.evidence_request);
  const dossier = readOptionalObject(payload.dossier);
  const manualReview = readOptionalObject(payload.manual_review);
  const workspaceSummary = readOptionalObject(payload.workspace_summary);

  return {
    action: readOptionalString(payload.action),
    scope_id: readOptionalString(payload.scope_id),
    evidence_request: evidenceRequest
      ? {
          request_id: readOptionalString(evidenceRequest.request_id),
          report_id: readNullableString(evidenceRequest.report_id)
        }
      : undefined,
    dossier: dossier
      ? {
          package_type: readOptionalString(dossier.package_type),
          signoff_mode: readOptionalString(dossier.signoff_mode)
        }
      : undefined,
    manual_review: manualReview
      ? {
          counterparty_context: readOptionalString(manualReview.counterparty_context),
          purpose: readOptionalString(manualReview.purpose),
          amount: readOptionalNumber(manualReview.amount)
        }
      : undefined,
    workspace_summary: workspaceSummary
      ? {
          event_id: readOptionalString(workspaceSummary.event_id)
        }
      : undefined
  };
}

function parseSignoffRequestPayload(route: Route): SignoffRequestPayload {
  const payload = readRouteJsonObject(route);
  return {
    request_id: readOptionalString(payload.request_id),
    scope_id: readOptionalString(payload.scope_id),
    manual_review_action: readOptionalString(payload.manual_review_action),
    package_sha256: readOptionalString(payload.package_sha256),
    signoff_mode: readOptionalString(payload.signoff_mode)
  };
}

function parseSealSignoffPayload(route: Route): SealSignoffPayload {
  const payload = readRouteJsonObject(route);
  return {
    signer_role: readOptionalString(payload.signer_role),
    decision: readOptionalString(payload.decision),
    signoff_method: readOptionalString(payload.signoff_method)
  };
}

function parseFinalizeSealPayload(route: Route): FinalizeSealPayload {
  const payload = readRouteJsonObject(route);
  const metadata = readOptionalObject(payload.metadata);
  return {
    metadata: metadata
      ? {
          source: readOptionalString(metadata.source),
          request_id: readOptionalString(metadata.request_id),
          report_id: readOptionalString(metadata.report_id),
          package_sha256: readOptionalString(metadata.package_sha256)
        }
      : undefined
  };
}

function parseTicketedPayload(route: Route): TicketedPayload {
  const payload = readRouteJsonObject(route);
  return {
    ticket_ref: readOptionalString(payload.ticket_ref),
    reason: readOptionalString(payload.reason)
  };
}

function parseSupersedeSealPayload(route: Route): SupersedeSealPayload {
  const payload = readRouteJsonObject(route);
  return {
    superseded_by_seal_id: readOptionalString(payload.superseded_by_seal_id),
    ticket_ref: readOptionalString(payload.ticket_ref),
    reason: readOptionalString(payload.reason)
  };
}

async function expectManualPackageExport(
  page: Page,
  options: {
    expectedFilename: string;
    assertPayload: (payload: ManualPackagePayload) => void;
  },
  trigger: () => Promise<void>
) {
  await expectDownloadLikeResponseWithRequest(
    page,
    {
      urlPart: "/api/app/evidence/manual-package",
      requestUrlPart: "/api/app/evidence/manual-package",
      method: "POST",
      expectedFilename: options.expectedFilename,
      parseRequest: parseManualPackagePayloadFromRequest,
      assertPayload: options.assertPayload
    },
    trigger
  );
}

test.describe("evidence custody flow", () => {
  test("foca a cadeia correlacionada e exporta o bundle da seleção atual", async ({ page }: { page: Page }) => {
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
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "AUDITOR",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=evidence**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const url = new URL(route.request().url());
      const requestId = url.searchParams.get("request_id");
      const reportId = url.searchParams.get("report_id");
      const resourceType = url.searchParams.get("resource_type");

      const allRows = [
        {
          id: "audit-evi-01",
          user_id: "user-e2e",
          action: "report_generated",
          resource_type: "case",
          resource_id: "11111111-1111-4111-8111-111111111111",
          request_id: "req-evi-01",
          report_id: "rep-evi-02",
          file_hash_sha256: "a".repeat(64),
          created_at: "2026-07-04T10:00:00.000Z",
          metadata: {
            case_id: "11111111-1111-4111-8111-111111111111",
            request_id: "req-evi-01",
            report_id: "rep-evi-02",
            file_hash_sha256: "a".repeat(64)
          }
        },
        {
          id: "audit-evi-02",
          user_id: "user-e2e",
          action: "report_downloaded",
          resource_type: "report",
          resource_id: "rep-evi-02",
          request_id: "req-evi-01",
          report_id: "rep-evi-02",
          file_hash_sha256: "a".repeat(64),
          created_at: "2026-07-04T10:05:00.000Z",
          metadata: {
            case_id: "11111111-1111-4111-8111-111111111111",
            request_id: "req-evi-01",
            report_id: "rep-evi-02",
            file_hash_sha256: "a".repeat(64)
          }
        },
        {
          id: "audit-evi-03",
          user_id: "user-e2e",
          action: "evidence_bundle_exported",
          resource_type: "case",
          resource_id: "11111111-1111-4111-8111-111111111111",
          request_id: "req-evi-01",
          report_id: "rep-evi-02",
          file_hash_sha256: null,
          created_at: "2026-07-04T10:10:00.000Z",
          metadata: {
            case_id: "11111111-1111-4111-8111-111111111111",
            request_id: "req-evi-01",
            report_id: "rep-evi-02"
          }
        },
        {
          id: "audit-evi-04",
          user_id: "user-e2e",
          action: "counterparty_created",
          resource_type: "counterparty",
          resource_id: "cp-01",
          request_id: "req-other",
          report_id: null,
          file_hash_sha256: null,
          created_at: "2026-07-04T09:00:00.000Z",
          metadata: {
            counterparty_id: "cp-01"
          }
        }
      ];

      const filtered = allRows.filter((row) => {
        if (requestId && row.request_id !== requestId) {
          return false;
        }
        if (reportId && row.report_id !== reportId) {
          return false;
        }
        if (resourceType && row.resource_type !== resourceType) {
          return false;
        }
        return true;
      });

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: filtered,
          page: 1,
          count: filtered.length,
          limit: 50,
          total: filtered.length,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/operations/work-items/work-evi-dd-01", async (route: Route) => {
      if (route.request().method() !== "PATCH") {
        await route.fallback();
        return;
      }
      expect(route.request().method()).toBe("PATCH");
      const payload = parseWorkItemPatchPayload(route);
      expect(payload.queue_status).toBe("CLOSED");

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "work-evi-dd-01",
          resource_id: "audit-dd-workspace-01",
          owner_user_id: "linked-user-dd-01",
          queue_status: "CLOSED",
          priority: "high",
          due_at: "2026-07-05T18:30:00.000Z",
          note: "Aguardando validação humana do pacote DD.",
          metadata: {
            event_id: "audit-dd-workspace-01",
            audit_action: "compliance_due_diligence_checked",
            audit_resource_type: "address",
            audit_resource_id: "0xdddddddddddddddddddddddddddddddddddddddd",
            request_id: "req-dd-1",
            owner_label: "Compliance QA",
            local_workspace_status: "sealed",
            note: "Aguardando validação humana do pacote DD."
          },
          last_activity_at: "2026-07-05T12:30:00.000Z",
          updated_at: "2026-07-05T12:30:00.000Z"
        })
      });
    });

    await page.route("**/api/app/operations/work-items/work-evi-dd-01/timeline**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          item: {
            id: "work-evi-dd-01",
            resource_id: "audit-dd-workspace-01",
            owner_user_id: "linked-user-dd-01",
            queue_status: "UNDER_REVIEW",
            priority: "high",
            due_at: "2026-07-05T18:30:00.000Z",
            note: "Aguardando validação humana do pacote DD.",
            metadata: {
              event_id: "audit-dd-workspace-01",
              audit_action: "compliance_due_diligence_checked",
              audit_resource_type: "address",
              audit_resource_id: "0xdddddddddddddddddddddddddddddddddddddddd",
              request_id: "req-dd-1",
              owner_label: "Compliance QA",
              local_workspace_status: "reviewing",
              note: "Aguardando validação humana do pacote DD."
            },
            last_activity_at: "2026-07-05T12:00:00.000Z",
            updated_at: "2026-07-05T12:00:00.000Z"
          },
          events: [
            {
              id: "event-dd-timeline-01",
              event_type: "STATUS_CHANGED",
              from_status: "UNDER_REVIEW",
              to_status: "ESCALATED",
              actor_user_id: "linked-user-dd-01",
              payload: { owner: "Compliance QA" },
              created_at: "2026-07-05T12:00:00.000Z"
            }
          ],
          comments: [
            {
              id: "comment-dd-timeline-01",
              comment_type: "handoff",
              actor_user_id: "linked-user-dd-01",
              body: "handoff manual carregado do painel DD",
              created_at: "2026-07-05T12:05:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/audit/evidence-export", async (route: Route) => {
      const payload = parseEvidenceExportPayload(route);
      expect(payload.request_id).toBe("req-evi-01");
      expect(payload.report_id).toBe("rep-evi-02");
      expect(payload.resource_type).toBe("case");
      expect(payload.resource_id).toBe("11111111-1111-4111-8111-111111111111");
      expect(payload.include_reports).toBeTruthy();

      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": 'attachment; filename="ontrackchain-evidence-chain-rep-evi-02.json"'
        },
        body: JSON.stringify({
          sections: {
            audit_logs: { count: 3 },
            reports: { count: 1 }
          }
        })
      });
    });

    await page.goto("/evidence?report_id=rep-evi-02");

    await expect(page.locator('[data-testid="evidence-filter-action"] option[value="report_generated"]')).toHaveText(
      "Relatório gerado (report_generated)"
    );
    await expect(page.locator('[data-testid="evidence-filter-resource-type"] option[value="report"]')).toHaveText(
      "Relatório (report)"
    );
    await expect(page.getByRole("button", { name: /^Relatório gerado \(report_generated\)/i })).toBeVisible();
    await expect(page.getByTestId("evidence-chain-panel")).toBeVisible();
    await expect(page.getByTestId("evidence-chain-summary")).toContainText("rep-evi-02");
    await expect(page.getByTestId("evidence-chain-summary")).toContainText("04/07/2026");
    await page.getByRole("button", { name: /^Relatório gerado \(report_generated\)/i }).click();
    await expect(page.getByTestId("evidence-details-panel")).toContainText("Relatório gerado (report_generated)");
    await expect(page.getByTestId("evidence-details-panel")).toContainText("Caso (case)");

    await page.getByTestId("evidence-focus-chain").click();

    await expectDownloadLikeResponse(
      page,
      {
        urlPart: "/api/app/audit/evidence-export",
        method: "POST",
        expectedFilename: "ontrackchain-evidence-chain-rep-evi-02.json"
      },
      async () => {
        await page.getByTestId("evidence-export-selected-chain").click();
      }
    );
  });

  test("viewer nao recebe ctas de export sensivel da trilha de evidencias", async ({ page }: { page: Page }) => {
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
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "VIEWER",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=evidence**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const url = new URL(route.request().url());
      const requestId = url.searchParams.get("request_id");
      const reportId = url.searchParams.get("report_id");
      const resourceType = url.searchParams.get("resource_type");

      const allRows = [
        {
          id: "audit-evi-01",
          user_id: "user-e2e",
          action: "report_generated",
          resource_type: "case",
          resource_id: "11111111-1111-4111-8111-111111111111",
          request_id: "req-evi-01",
          report_id: "rep-evi-02",
          file_hash_sha256: "a".repeat(64),
          created_at: "2026-07-04T10:00:00.000Z",
          metadata: {
            case_id: "11111111-1111-4111-8111-111111111111",
            request_id: "req-evi-01",
            report_id: "rep-evi-02",
            file_hash_sha256: "a".repeat(64)
          }
        },
        {
          id: "audit-evi-02",
          user_id: "user-e2e",
          action: "report_downloaded",
          resource_type: "report",
          resource_id: "rep-evi-02",
          request_id: "req-evi-01",
          report_id: "rep-evi-02",
          file_hash_sha256: "a".repeat(64),
          created_at: "2026-07-04T10:05:00.000Z",
          metadata: {
            case_id: "11111111-1111-4111-8111-111111111111",
            request_id: "req-evi-01",
            report_id: "rep-evi-02",
            file_hash_sha256: "a".repeat(64)
          }
        },
        {
          id: "audit-evi-03",
          user_id: "user-e2e",
          action: "evidence_bundle_exported",
          resource_type: "case",
          resource_id: "11111111-1111-4111-8111-111111111111",
          request_id: "req-evi-01",
          report_id: "rep-evi-02",
          file_hash_sha256: null,
          created_at: "2026-07-04T10:10:00.000Z",
          metadata: {
            case_id: "11111111-1111-4111-8111-111111111111",
            request_id: "req-evi-01",
            report_id: "rep-evi-02"
          }
        }
      ];

      const filtered = allRows.filter((row) => {
        if (requestId && row.request_id !== requestId) {
          return false;
        }
        if (reportId && row.report_id !== reportId) {
          return false;
        }
        if (resourceType && row.resource_type !== resourceType) {
          return false;
        }
        return true;
      });

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: filtered,
          page: 1,
          count: filtered.length,
          limit: 50,
          total: filtered.length,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.goto("/evidence?report_id=rep-evi-02");

    await page.getByRole("button", { name: /^Relatório gerado \(report_generated\)/i }).click();
    await page.getByTestId("evidence-focus-chain").click();

    await expect(page.getByTestId("evidence-export-selected-chain")).toHaveCount(0);
    await expect(page.getByTestId("evidence-export-manual-package")).toHaveCount(0);
    await expect(
      page.getByText(
        "As exportações sensíveis da trilha de evidências estão ocultas nesta sessão porque a role atual não possui autorização privilegiada ADMIN/AUDITOR."
      )
    ).toBeVisible();
  });

  test("expõe handoff operacional do pacote manual com workspace correlacionado", async ({ page }: { page: Page }) => {
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
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "ANALYST",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=evidence**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "work-evi-dd-01",
              resource_id: "audit-dd-workspace-01",
              owner_user_id: "linked-user-dd-01",
              queue_status: "UNDER_REVIEW",
              priority: "high",
              due_at: "2026-07-05T18:30:00.000Z",
              note: "Aguardando validação humana do pacote DD.",
              metadata: {
                event_id: "audit-dd-workspace-01",
                audit_action: "compliance_due_diligence_checked",
                audit_resource_type: "address",
                audit_resource_id: "0xdddddddddddddddddddddddddddddddddddddddd",
                request_id: "req-dd-1",
                owner_label: "Compliance QA",
                local_workspace_status: "reviewing",
                note: "Aguardando validação humana do pacote DD."
              },
              last_activity_at: "2026-07-05T12:00:00.000Z",
              updated_at: "2026-07-05T12:00:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const url = new URL(route.request().url());
      const requestId = url.searchParams.get("request_id");
      const allRows = [
        {
          id: "audit-dd-01",
          user_id: "user-e2e",
          action: "compliance_due_diligence_checked",
          resource_type: "address",
          resource_id: "0xdddddddddddddddddddddddddddddddddddddddd",
          request_id: "req-dd-1",
          report_id: null,
          file_hash_sha256: "d".repeat(64),
          created_at: "2026-07-05T10:00:00.000Z",
          metadata: {
            request_id: "req-dd-1",
            address: "0xdddddddddddddddddddddddddddddddddddddddd",
            chain: "ethereum",
            provider: "manual_review",
            provider_status: "degraded",
            degraded_reason: "manual_review_required",
            capability_status: "degraded",
            delivery_mode: "manual_review_pending",
            requires_human_review: true,
            counterparty_context: "cliente OTC high risk"
          }
        }
      ];

      const filtered = allRows.filter((row) => {
        if (requestId && row.request_id !== requestId) {
          return false;
        }
        return true;
      });

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: filtered,
          page: 1,
          count: filtered.length,
          limit: 50,
          total: filtered.length,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/audit/evidence-export", async (route: Route) => {
      const payload = parseEvidenceExportPayload(route);
      expect(payload.request_id).toBe("req-dd-1");
      expect(payload.resource_type).toBe("address");
      expect(payload.resource_id).toBe("0xdddddddddddddddddddddddddddddddddddddddd");

      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": 'attachment; filename="ontrackchain-manual-review-due-diligence-req-dd-1.json"'
        },
        body: JSON.stringify({
          sections: {
            audit_logs: { count: 1 }
          }
        })
      });
    });

    await page.route("**/api/app/evidence/manual-package", async (route: Route) => {
      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": 'attachment; filename="ontrackchain-manual-review-due-diligence-req-dd-1.json"'
        },
        body: JSON.stringify({
          package_type: "due_diligence_manual_review_package",
          workspace_summary: { event_id: "audit-dd-workspace-01" }
        })
      });
    });

    await page.goto(
      "/evidence?request_id=req-dd-1&domain=due_diligence&action=compliance_due_diligence_checked&resource_type=address&audit_origin=manual_package"
    );

    await expect(page.locator('[data-testid="evidence-filter-action"] option[value="compliance_due_diligence_checked"]')).toHaveText(
      "Due diligence verificada (compliance_due_diligence_checked)"
    );
    await expect(page.locator('[data-testid="evidence-filter-resource-type"] option[value="address"]')).toHaveText(
      "Endereço (address)"
    );
    await expect(page.getByTestId("evidence-audit-return-banner")).toContainText(
      "Retorno da trilha auditável manual"
    );
    await expect(page.getByTestId("evidence-audit-return-banner")).toContainText(
      "Due diligence verificada"
    );
    await expect(page.getByTestId("evidence-audit-return-banner")).toContainText("Due diligence");
    await expect(page.getByTestId("evidence-audit-return-banner")).toContainText("req-dd-1");
    await expect(page.getByTestId("evidence-audit-return-open-audit")).toHaveAttribute(
      "href",
      "/audit?action=evidence_manual_review_package_exported&resource_type=audit_log&request_id=req-dd-1"
    );
    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("manual_review_pending");
    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("Revisão manual pendente");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("due_diligence_manual_review_package");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("Pacote manual de due diligence");
    await expect(page.getByTestId("evidence-manual-package-focus-chain")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-package-export-chain")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-package-export-package")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-package-open-audit-preset")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-package-open-audit")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-package-open-reports")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-package-open-investigate")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-package-open-sanctions")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-package-open-blocks")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("audit-dd-workspace-01");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("Endereço (address)");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("0xdddddddddddddddddddddddddddddddddddddddd");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("req-dd-1");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("n/a");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("file_hash_sha256");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("Compliance QA");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("alta");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("em revisão");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("servidor");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("Aguardando validação humana do pacote DD.");
    await expect(page.getByTestId("evidence-manual-workspace-load")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-workspace-open-timeline")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-workspace-mark-sealed")).toBeVisible();

    await page.getByTestId("evidence-manual-workspace-load").click();
    await expect(page.getByLabel("Owner")).toHaveValue("Compliance QA");
    await page.getByTestId("evidence-manual-workspace-open-timeline").click();
    await expect(page.getByTestId("work-item-timeline-summary")).toContainText("audit-dd-workspace-01");
    await page.getByTestId("evidence-manual-workspace-mark-sealed").click();
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("selado");

    await expectDownloadLikeResponse(
      page,
      {
        urlPart: "/api/app/audit/evidence-export",
        method: "POST",
        expectedFilename: "ontrackchain-manual-review-due-diligence-req-dd-1.json"
      },
      async () => {
        await page.getByTestId("evidence-manual-package-export-chain").click();
      }
    );
    await expect(page.getByTestId("evidence-manual-package-open-audit-preset")).toHaveAttribute(
      "href",
      "/audit?action=evidence_manual_review_package_exported&resource_type=audit_log&request_id=req-dd-1"
    );
    await expect(page.getByTestId("evidence-manual-package-open-audit")).toHaveAttribute("href", /\/audit/);
    await expect(page.getByTestId("evidence-manual-package-open-reports")).toHaveAttribute("href", /\/reports/);
    await expect(page.getByTestId("evidence-manual-package-open-investigate")).toHaveAttribute("href", /\/investigate\?address=0xdddddddddddddddddddddddddddddddddddddddd/);
    await expect(page.getByTestId("evidence-manual-package-open-sanctions")).toHaveAttribute("href", /\/sanctions\?address=0xdddddddddddddddddddddddddddddddddddddddd/);
    await expect(page.getByTestId("evidence-manual-package-open-blocks")).toHaveAttribute("href", /\/blocks\?address=0xdddddddddddddddddddddddddddddddddddddddd/);

  });

  test("expõe manifesto institucional do pacote manual de due diligence", async ({ page }: { page: Page }) => {
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
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "ANALYST",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=evidence**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-dd-manifest-01",
              user_id: "user-e2e",
              action: "compliance_due_diligence_checked",
              resource_type: "address",
              resource_id: "0xdddddddddddddddddddddddddddddddddddddddd",
              request_id: "req-dd-1",
              report_id: "rep-dd-1",
              file_hash_sha256: "d".repeat(64),
              created_at: "2026-07-04T11:00:00.000Z",
              metadata: {
                case_id: "33333333-3333-4333-8333-333333333333",
                request_id: "req-dd-1",
                report_id: "rep-dd-1",
                address: "0xdddddddddddddddddddddddddddddddddddddddd",
                chain: "ethereum",
                file_hash_sha256: "d".repeat(64),
                provider: "manual_review",
                provider_status: "degraded",
                degraded_reason: "manual_review_required",
                capability_status: "degraded",
                delivery_mode: "manual_review_pending",
                requires_human_review: true,
                counterparty_context: "exchange_with_nested_wallets"
              }
            }
          ],
          page: 1,
          count: 1,
          limit: 50,
          total: 1,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/audit/evidence-export", async (route: Route) => {
      const payload = parseEvidenceExportPayload(route);
      expect(payload.request_id).toBe("req-dd-1");
      expect(payload.report_id).toBe("rep-dd-1");
      expect(payload.include_reports).toBeTruthy();

      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": 'attachment; filename="ontrackchain-manual-review-due-diligence-req-dd-1.json"'
        },
        body: JSON.stringify({
          sections: {
            audit_logs: { count: 1 },
            reports: { count: 1 }
          }
        })
      });
    });

    await page.route("**/api/app/evidence/manual-package", async (route: Route) => {
      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": 'attachment; filename="ontrackchain-manual-review-due-diligence-req-dd-1.json"'
        },
        body: JSON.stringify({
          package_type: "due_diligence_manual_review_package",
          dossier: { signoff_mode: "compliance_dd_signoff" }
        })
      });
    });

    await page.goto("/evidence");

    await page.getByRole("button", { name: /^Due diligence verificada \(compliance_due_diligence_checked\)/i }).click();
    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("manual_review_pending");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("due_diligence_manual_review_package");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("regulated_ops_human_review_required");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("compliance_dd_signoff");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("human_signoff_required");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("chain_correlated");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("hash_materialized_offchain");

    await expectManualPackageExport(
      page,
      {
        expectedFilename: "ontrackchain-manual-review-due-diligence-req-dd-1.json",
        assertPayload: (payload) => {
          expect(payload.action).toBe("compliance_due_diligence_checked");
          expect(payload.scope_id).toBe("req-dd-1");
          expect(payload.evidence_request?.report_id).toBe("rep-dd-1");
          expect(payload.dossier?.signoff_mode).toBe("compliance_dd_signoff");
        }
      },
      async () => {
        await page.getByTestId("evidence-manual-package-export-package").click();
      }
    );
  });

  test("expõe contrato manual de due diligence no cockpit de evidências", async ({ page }: { page: Page }) => {
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
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "ANALYST",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=evidence**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const url = new URL(route.request().url());
      const action = url.searchParams.get("action");
      const resourceType = url.searchParams.get("resource_type");
      const requestId = url.searchParams.get("request_id");

      const allRows = [
        {
          id: "audit-dd-01",
          user_id: "user-e2e",
          action: "compliance_due_diligence_checked",
          resource_type: "address",
          resource_id: "0xdef",
          request_id: "req-dd-1",
          report_id: null,
          file_hash_sha256: null,
          created_at: "2026-07-05T11:00:00.000Z",
          metadata: {
            address: "0xdef",
            chain: "polygon",
            provider: "manual_review",
            provider_status: "degraded",
            degraded_reason: "manual_review_required",
            capability_status: "degraded",
            delivery_mode: "manual_review_pending",
            counterparty_context: "exchange settlement",
            counterparty_context_present: true
          }
        },
        {
          id: "audit-dd-02",
          user_id: "user-e2e",
          action: "compliance_source_of_funds_checked",
          resource_type: "address",
          resource_id: "0x123",
          request_id: "req-sof-1",
          report_id: null,
          file_hash_sha256: null,
          created_at: "2026-07-05T11:05:00.000Z",
          metadata: {
            address: "0x123",
            chain: "arbitrum",
            provider: "manual_review",
            provider_status: "degraded",
            degraded_reason: "manual_review_required",
            capability_status: "degraded",
            delivery_mode: "manual_review_pending",
            purpose: "treasury top-up",
            amount: 1200.5,
            requires_human_review: true
          }
        }
      ];

      const filtered = allRows.filter((row) => {
        if (action && row.action !== action) {
          return false;
        }
        if (resourceType && row.resource_type !== resourceType) {
          return false;
        }
        if (requestId && row.request_id !== requestId) {
          return false;
        }
        return true;
      });

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: filtered,
          page: 1,
          count: filtered.length,
          limit: 50,
          total: filtered.length,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/audit/evidence-export", async (route: Route) => {
      const payload = parseEvidenceExportPayload(route);
      expect(payload.request_id).toBe("req-dd-1");
      expect(payload.report_id).toBeNull();
      expect(payload.resource_type).toBe("address");
      expect(payload.resource_id).toBe("0xdef");

      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": 'attachment; filename="ontrackchain-evidence-chain-req-dd-1.json"'
        },
        body: JSON.stringify({ sections: { audit_logs: { count: 1 } } })
      });
    });

    await page.route("**/api/app/evidence/manual-package", async (route: Route) => {
      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": 'attachment; filename="ontrackchain-manual-review-due-diligence-req-dd-1.json"'
        },
        body: JSON.stringify({
          package_type: "due_diligence_manual_review_package",
          manual_review: { counterparty_context: "exchange settlement" }
        })
      });
    });

    await page.goto("/evidence");
    await page.getByRole("button", { name: /Due diligence/i }).click();

    await expect(page.locator('[data-testid="evidence-filter-action"] option[value="compliance_due_diligence_checked"]')).toHaveText(
      "Due diligence verificada (compliance_due_diligence_checked)"
    );
    await expect(page.locator('[data-testid="evidence-filter-resource-type"] option[value="address"]')).toHaveText("Endereço (address)");
    await expect(page.getByRole("button", { name: /^Due diligence verificada \(compliance_due_diligence_checked\)/i })).toBeVisible();

    await page.getByRole("button", { name: /^Due diligence verificada \(compliance_due_diligence_checked\)/i }).click();
    await expect(page.getByTestId("evidence-details-panel")).toContainText(
      "Due diligence verificada (compliance_due_diligence_checked)"
    );
    await expect(page.getByTestId("evidence-details-panel")).toContainText("Endereço (address)");
    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("manual_review_pending");
    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("Revisão manual pendente");
    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("exchange settlement");
    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("manual_review_required");
    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("Revisão manual obrigatória");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("due_diligence_manual_review_package");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("Pacote manual de due diligence");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("restricted_regulatory");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("Restrito regulatório");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("Restrito regulatório");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("Status do provider");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("provider_status");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("Validar contraparte");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("validate_counterparty");

    await expectManualPackageExport(
      page,
      {
        expectedFilename: "ontrackchain-manual-review-due-diligence-req-dd-1.json",
        assertPayload: (payload) => {
          expect(payload.action).toBe("compliance_due_diligence_checked");
          expect(payload.scope_id).toBe("req-dd-1");
          expect(payload.manual_review?.counterparty_context).toBe("exchange settlement");
        }
      },
      async () => {
        await page.getByTestId("evidence-manual-package-export-package").click();
      }
    );
  });

  test("expõe contrato manual de source of funds no cockpit de evidências", async ({ page }: { page: Page }) => {
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
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "ANALYST",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=evidence**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const url = new URL(route.request().url());
      const requestId = url.searchParams.get("request_id");
      const allRows = [
        {
          id: "audit-sof-01",
          user_id: "user-e2e",
          action: "compliance_source_of_funds_checked",
          resource_type: "address",
          resource_id: "0x5555555555555555555555555555555555555555",
          request_id: "req-sof-1",
          report_id: null,
          file_hash_sha256: "e".repeat(64),
          created_at: "2026-07-05T11:00:00.000Z",
          metadata: {
            request_id: "req-sof-1",
            address: "0x5555555555555555555555555555555555555555",
            chain: "ethereum",
            provider: "manual_review",
            provider_status: "degraded",
            degraded_reason: "manual_review_required",
            capability_status: "degraded",
            delivery_mode: "manual_review_pending",
            requires_human_review: true,
            purpose: "origem declarada tesouraria OTC",
            amount: 125000
          }
        }
      ];

      const filtered = allRows.filter((row) => {
        if (requestId && row.request_id !== requestId) {
          return false;
        }
        return true;
      });

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: filtered,
          page: 1,
          count: filtered.length,
          limit: 50,
          total: filtered.length,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/audit/evidence-export", async (route: Route) => {
      const payload = parseEvidenceExportPayload(route);
      expect(payload.request_id).toBe("req-sof-1");
      expect(payload.resource_type).toBe("address");
      expect(payload.resource_id).toBe("0x5555555555555555555555555555555555555555");

      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": 'attachment; filename="ontrackchain-manual-review-source-of-funds-req-sof-1.json"'
        },
        body: JSON.stringify({
          sections: {
            audit_logs: { count: 1 }
          }
        })
      });
    });

    await page.route("**/api/app/evidence/manual-package", async (route: Route) => {
      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": 'attachment; filename="ontrackchain-manual-review-source-of-funds-req-sof-1.json"'
        },
        body: JSON.stringify({
          package_type: "source_of_funds_manual_review_package",
          manual_review: { purpose: "origem declarada tesouraria OTC", amount: 125000 }
        })
      });
    });

    await page.goto("/evidence?request_id=req-sof-1&domain=source_of_funds");

    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("manual_review_pending");
    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("origem declarada tesouraria OTC");
    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("125000");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("source_of_funds_manual_review_package");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("Pacote manual de origem de fundos");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("compliance_sof_signoff");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("Sign-off de compliance SoF");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("human_signoff_required");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("Sign-off humano obrigatório");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("Sign-off humano obrigatório");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("Propósito");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("purpose");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("Confirmar racional financeiro");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("confirm_financial_rationale");
    await expect(page.getByTestId("evidence-manual-package-open-investigate")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-package-open-sanctions")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-package-open-blocks")).toBeVisible();

    await expectManualPackageExport(
      page,
      {
        expectedFilename: "ontrackchain-manual-review-source-of-funds-req-sof-1.json",
        assertPayload: (payload) => {
          expect(payload.action).toBe("compliance_source_of_funds_checked");
          expect(payload.scope_id).toBe("req-sof-1");
          expect(payload.manual_review?.purpose).toBe("origem declarada tesouraria OTC");
          expect(payload.manual_review?.amount).toBe(125000);
        }
      },
      async () => {
        await page.getByTestId("evidence-manual-package-export-package").click();
      }
    );
  });

  test("expõe handoff operacional do pacote manual de source of funds com workspace correlacionado", async ({ page }: { page: Page }) => {
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
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "ANALYST",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=evidence**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "work-evi-sof-01",
              resource_id: "audit-sof-workspace-01",
              owner_user_id: "linked-user-sof-01",
              queue_status: "UNDER_REVIEW",
              priority: "high",
              due_at: "2026-07-06T17:00:00.000Z",
              note: "Aguardando evidência documental complementar da origem dos fundos.",
              metadata: {
                event_id: "audit-sof-workspace-01",
                audit_action: "compliance_source_of_funds_checked",
                audit_resource_type: "address",
                audit_resource_id: "0x5555555555555555555555555555555555555555",
                request_id: "req-sof-1",
                owner_label: "Ops SoF",
                local_workspace_status: "reviewing",
                note: "Aguardando evidência documental complementar da origem dos fundos."
              },
              last_activity_at: "2026-07-05T14:00:00.000Z",
              updated_at: "2026-07-05T14:00:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/operations/work-items/work-evi-sof-01", async (route: Route) => {
      expect(route.request().method()).toBe("PATCH");
      const payload = parseWorkItemPatchPayload(route);
      expect(payload.queue_status).toBe("CLOSED");

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "work-evi-sof-01",
          resource_id: "audit-sof-workspace-01",
          owner_user_id: "linked-user-sof-01",
          queue_status: "CLOSED",
          priority: "high",
          due_at: "2026-07-06T17:00:00.000Z",
          note: "Aguardando evidência documental complementar da origem dos fundos.",
          metadata: {
            event_id: "audit-sof-workspace-01",
            audit_action: "compliance_source_of_funds_checked",
            audit_resource_type: "address",
            audit_resource_id: "0x5555555555555555555555555555555555555555",
            request_id: "req-sof-1",
            owner_label: "Ops SoF",
            local_workspace_status: "sealed",
            note: "Aguardando evidência documental complementar da origem dos fundos."
          },
          last_activity_at: "2026-07-05T14:30:00.000Z",
          updated_at: "2026-07-05T14:30:00.000Z"
        })
      });
    });

    await page.route("**/api/app/operations/work-items/work-evi-sof-01/timeline**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          item: {
            id: "work-evi-sof-01",
            resource_id: "audit-sof-workspace-01",
            owner_user_id: "linked-user-sof-01",
            queue_status: "UNDER_REVIEW",
            priority: "high",
            due_at: "2026-07-06T17:00:00.000Z",
            note: "Aguardando evidência documental complementar da origem dos fundos.",
            metadata: {
              event_id: "audit-sof-workspace-01",
              audit_action: "compliance_source_of_funds_checked",
              audit_resource_type: "address",
              audit_resource_id: "0x5555555555555555555555555555555555555555",
              request_id: "req-sof-1",
              owner_label: "Ops SoF",
              local_workspace_status: "reviewing",
              note: "Aguardando evidência documental complementar da origem dos fundos."
            },
            last_activity_at: "2026-07-05T14:00:00.000Z",
            updated_at: "2026-07-05T14:00:00.000Z"
          },
          events: [
            {
              id: "event-sof-timeline-01",
              event_type: "STATUS_CHANGED",
              from_status: "UNDER_REVIEW",
              to_status: "ESCALATED",
              actor_user_id: "linked-user-sof-01",
              payload: { owner: "Ops SoF" },
              created_at: "2026-07-05T14:00:00.000Z"
            }
          ],
          comments: [
            {
              id: "comment-sof-timeline-01",
              comment_type: "handoff",
              actor_user_id: "linked-user-sof-01",
              body: "handoff manual carregado do painel SoF",
              created_at: "2026-07-05T14:05:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const url = new URL(route.request().url());
      const requestId = url.searchParams.get("request_id");
      const allRows = [
        {
          id: "audit-sof-01",
          user_id: "user-e2e",
          action: "compliance_source_of_funds_checked",
          resource_type: "address",
          resource_id: "0x5555555555555555555555555555555555555555",
          request_id: "req-sof-1",
          report_id: null,
          file_hash_sha256: "e".repeat(64),
          created_at: "2026-07-05T11:00:00.000Z",
          metadata: {
            request_id: "req-sof-1",
            address: "0x5555555555555555555555555555555555555555",
            chain: "ethereum",
            provider: "manual_review",
            provider_status: "degraded",
            degraded_reason: "manual_review_required",
            capability_status: "degraded",
            delivery_mode: "manual_review_pending",
            requires_human_review: true,
            purpose: "origem declarada tesouraria OTC",
            amount: 125000
          }
        }
      ];

      const filtered = allRows.filter((row) => {
        if (requestId && row.request_id !== requestId) {
          return false;
        }
        return true;
      });

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: filtered,
          page: 1,
          count: filtered.length,
          limit: 50,
          total: filtered.length,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/audit/evidence-export", async (route: Route) => {
      const payload = parseEvidenceExportPayload(route);
      expect(payload.request_id).toBe("req-sof-1");
      expect(payload.resource_type).toBe("address");
      expect(payload.resource_id).toBe("0x5555555555555555555555555555555555555555");

      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": 'attachment; filename="ontrackchain-manual-review-source-of-funds-req-sof-1.json"'
        },
        body: JSON.stringify({
          sections: {
            audit_logs: { count: 1 }
          }
        })
      });
    });

    await page.route("**/api/app/evidence/manual-package", async (route: Route) => {
      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": 'attachment; filename="ontrackchain-manual-review-source-of-funds-req-sof-1.json"'
        },
        body: JSON.stringify({
          package_type: "source_of_funds_manual_review_package",
          workspace_summary: { event_id: "audit-sof-workspace-01" }
        })
      });
    });

    await page.goto("/evidence?request_id=req-sof-1&domain=source_of_funds");

    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("manual_review_pending");
    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("origem declarada tesouraria OTC");
    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("125000");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("source_of_funds_manual_review_package");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("audit-sof-workspace-01");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("Ops SoF");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("alta");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("em revisão");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("Endereço (address)");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("servidor");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("Origem");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("Aguardando evidência documental complementar da origem dos fundos.");
    await expect(page.getByTestId("evidence-manual-workspace-load")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-workspace-open-timeline")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-workspace-mark-sealed")).toBeVisible();

    await page.getByTestId("evidence-manual-workspace-load").click();
    await expect(page.getByLabel("Owner")).toHaveValue("Ops SoF");
    await page.getByTestId("evidence-manual-workspace-open-timeline").click();
    await expect(page.getByTestId("work-item-timeline-summary")).toContainText("audit-sof-workspace-01");
    await expect(page.getByTestId("work-item-timeline-comment").first()).toContainText("handoff manual carregado do painel SoF");
    await page.getByTestId("evidence-manual-workspace-mark-sealed").click();
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toContainText("selado");

    await expectManualPackageExport(
      page,
      {
        expectedFilename: "ontrackchain-manual-review-source-of-funds-req-sof-1.json",
        assertPayload: (payload) => {
          expect(payload.action).toBe("compliance_source_of_funds_checked");
          expect(payload.scope_id).toBe("req-sof-1");
          expect(payload.workspace_summary?.event_id).toBe("audit-sof-workspace-01");
          expect(payload.dossier?.signoff_mode).toBe("compliance_sof_signoff");
        }
      },
      async () => {
        await page.getByTestId("evidence-manual-package-export-package").click();
      }
    );
  });
  test("materializa a selagem institucional pelo package_sha256 correlacionado", async ({ page }: { page: Page }) => {
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
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "ADMIN",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=evidence**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-dd-seal-01",
              user_id: "user-e2e",
              action: "compliance_due_diligence_checked",
              resource_type: "address",
              resource_id: "0xsealdddddddddddddddddddddddddddddddddddddd",
              request_id: "req-dd-seal-1",
              report_id: "rep-dd-seal-1",
              file_hash_sha256: "a".repeat(64),
              created_at: "2026-07-08T10:00:00.000Z",
              metadata: {
                request_id: "req-dd-seal-1",
                report_id: "rep-dd-seal-1",
                address: "0xsealdddddddddddddddddddddddddddddddddddddd",
                chain: "ethereum",
                provider: "manual_review",
                provider_status: "degraded",
                degraded_reason: "manual_review_required",
                capability_status: "degraded",
                delivery_mode: "manual_review_pending",
                requires_human_review: true
              }
            },
            {
              id: "audit-dd-seal-02",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_exported",
              resource_type: "audit_log",
              resource_id: "audit-dd-seal-02",
              request_id: "req-dd-seal-1",
              report_id: "rep-dd-seal-1",
              file_hash_sha256: null,
              created_at: "2026-07-08T10:05:00.000Z",
              metadata: {
                request_id: "req-dd-seal-1",
                report_id: "rep-dd-seal-1",
                scope_id: "req-dd-seal-1",
                filename: "ontrackchain-manual-review-due-diligence-req-dd-seal-1.json",
                package_sha256: "f".repeat(64),
                manual_review_action: "compliance_due_diligence_checked"
              }
            }
          ],
          page: 1,
          count: 2,
          limit: 50,
          total: 2,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/evidence/manual-package/seal?**", async (route: Route) => {
      const url = new URL(route.request().url());
      expect(url.searchParams.get("package_sha256")).toBe("f".repeat(64));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          seal_id: "seal-dd-01",
          organization_id: "org-e2e",
          package_kind: "manual_review_package",
          request_id: "req-dd-seal-1",
          report_id: "rep-dd-seal-1",
          scope_id: "req-dd-seal-1",
          manual_review_action: "compliance_due_diligence_checked",
          package_sha256: "f".repeat(64),
          manifest_schema_version: "manual_review_package/v2",
          classification: "restricted_regulatory",
          signoff_mode: "compliance_ops_signoff",
          seal_status: "sealed",
          seal_format: "jws_json_flattened",
          signature_algorithm: "HS256",
          kms_key_ref: null,
          certificate_fingerprint_sha256: null,
          certificate_bundle_ref: "local-hs256-trust-bundle",
          policy_version: "manual_package_sealing/v1",
          sealed_at: "2026-07-08T10:06:00.000Z",
          sealed_by_user_id: "user-e2e",
          revoked_at: null,
          superseded_by_seal_id: null,
          required_signers: ["compliance_owner", "ops_owner"],
          completed_signoffs: 2,
          approved_required_signoffs: 2,
          required_signoffs: 2,
          signoffs: [
            {
              id: "signoff-dd-01",
              seal_id: "seal-dd-01",
              organization_id: "org-e2e",
              signer_role: "compliance_owner",
              signer_user_id: "user-e2e",
              signer_display_name: "Compliance Owner",
              decision: "approved",
              signoff_method: "platform_authenticated_2fa",
              ticket_ref: "CMP-1",
              notes: null,
              signed_at: "2026-07-08T10:01:00.000Z",
              metadata: {}
            },
            {
              id: "signoff-dd-02",
              seal_id: "seal-dd-01",
              organization_id: "org-e2e",
              signer_role: "ops_owner",
              signer_user_id: "user-e2e",
              signer_display_name: "Ops Owner",
              decision: "approved",
              signoff_method: "platform_authenticated_2fa",
              ticket_ref: "OPS-1",
              notes: null,
              signed_at: "2026-07-08T10:02:00.000Z",
              metadata: {}
            }
          ],
          seal_envelope: {
            protected: "header",
            payload: "payload",
            signature: "signature"
          },
          verification_summary: {
            verified: true,
            verification_method: "local_hs256_self_check",
            seal_backend: "local_hs256",
            signature_algorithm: "HS256",
            issuer: "ontrackchain-investigation-api",
            key_id: "manual-package-local-hs256"
          },
          created_at: "2026-07-08T10:00:00.000Z",
          updated_at: "2026-07-08T10:06:00.000Z"
        })
      });
    });

    await page.goto("/evidence?request_id=req-dd-seal-1&domain=due_diligence&action=compliance_due_diligence_checked&resource_type=address");

    await expect(page.getByTestId("evidence-hash-context")).toContainText(`Hash principal do contexto${"f".repeat(64)}`);
    await expect(page.getByTestId("evidence-hash-context")).toContainText("manifesto do pacote manual");
    await expect(page.getByTestId("evidence-manual-package-export-hash")).toContainText("f".repeat(64));
    await expect(page.getByTestId("evidence-manual-package-export-filename")).toContainText(
      "ontrackchain-manual-review-due-diligence-req-dd-seal-1.json"
    );
    await expect(page.getByTestId("evidence-manual-package-seal-panel")).toContainText("Selagem institucional");
    await expect(page.getByTestId("evidence-manual-package-seal-panel")).toContainText("Selado");
    await expect(page.getByTestId("evidence-manual-package-seal-panel")).toContainText("2/2");
    await expect(page.getByTestId("evidence-manual-package-seal-panel")).toContainText("Compliance Owner");
    await expect(page.getByTestId("evidence-manual-package-seal-panel")).toContainText("Ops Owner");
    await expect(page.getByTestId("evidence-manual-package-seal-panel")).toContainText("local-hs256-trust-bundle");
    await expect(page.getByTestId("evidence-manual-package-seal-panel")).toContainText("local_hs256_self_check");
    await expect(page.getByTestId("evidence-manual-package-seal-panel")).toContainText("ontrackchain-investigation-api");
    await expect(page.getByTestId("evidence-manual-package-seal-panel")).toContainText("manual-package-local-hs256");
    await expect(page.getByTestId("evidence-manual-package-open-audit-governance")).toHaveAttribute(
      "href",
      "/audit?preset=governanca&seal_id=seal-dd-01&report_id=rep-dd-seal-1"
    );
  });

  test("inicializa a trilha institucional e registra o primeiro sign-off obrigatório", async ({ page }: { page: Page }) => {
    let currentSeal:
      | {
          seal_id: string;
          organization_id: string;
          package_kind: string;
          request_id: string;
          report_id: string | null;
          scope_id: string;
          manual_review_action: string;
          package_sha256: string;
          manifest_schema_version: string;
          classification: string;
          signoff_mode: string;
          seal_status: string;
          seal_format: string;
          signature_algorithm: string | null;
          kms_key_ref: string | null;
          certificate_fingerprint_sha256: string | null;
          certificate_bundle_ref: string | null;
          policy_version: string;
          sealed_at: string | null;
          sealed_by_user_id: string | null;
          revoked_at: string | null;
          superseded_by_seal_id: string | null;
          required_signers: string[];
          completed_signoffs: number;
          approved_required_signoffs: number;
          required_signoffs: number;
          signoffs: Array<Record<string, unknown>>;
          seal_envelope: Record<string, unknown>;
          verification_summary: Record<string, unknown>;
          created_at: string | null;
          updated_at: string | null;
        }
      | null = null;

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
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "ADMIN",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=evidence**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-dd-write-01",
              user_id: "user-e2e",
              action: "compliance_due_diligence_checked",
              resource_type: "address",
              resource_id: "0xwriteeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
              request_id: "req-dd-write-1",
              report_id: "rep-dd-write-1",
              file_hash_sha256: "a".repeat(64),
              created_at: "2026-07-08T10:00:00.000Z",
              metadata: {
                request_id: "req-dd-write-1",
                report_id: "rep-dd-write-1",
                address: "0xwriteeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                chain: "ethereum",
                provider: "manual_review",
                provider_status: "degraded",
                degraded_reason: "manual_review_required",
                capability_status: "degraded",
                delivery_mode: "manual_review_pending",
                requires_human_review: true
              }
            },
            {
              id: "audit-dd-write-02",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_exported",
              resource_type: "audit_log",
              resource_id: "audit-dd-write-02",
              request_id: "req-dd-write-1",
              report_id: "rep-dd-write-1",
              file_hash_sha256: null,
              created_at: "2026-07-08T10:05:00.000Z",
              metadata: {
                request_id: "req-dd-write-1",
                report_id: "rep-dd-write-1",
                scope_id: "req-dd-write-1",
                filename: "ontrackchain-manual-review-due-diligence-req-dd-write-1.json",
                package_sha256: "b".repeat(64),
                manual_review_action: "compliance_due_diligence_checked"
              }
            }
          ],
          page: 1,
          count: 2,
          limit: 50,
          total: 2,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/evidence/manual-package/seal?**", async (route: Route) => {
      const url = new URL(route.request().url());
      expect(url.searchParams.get("package_sha256")).toBe("b".repeat(64));
      if (!currentSeal) {
        await route.fulfill({
          status: 404,
          contentType: "application/json",
          body: JSON.stringify({ error: "manual_package_seal_not_found" })
        });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(currentSeal)
      });
    });

    await page.route("**/api/app/evidence/manual-package/signoff-requests", async (route: Route) => {
      const payload = parseSignoffRequestPayload(route);
      expect(payload.request_id).toBe("req-dd-write-1");
      expect(payload.scope_id).toBe("req-dd-write-1");
      expect(payload.manual_review_action).toBe("compliance_due_diligence_checked");
      expect(payload.package_sha256).toBe("b".repeat(64));
      expect(payload.signoff_mode).toBe("compliance_ops_signoff");

      currentSeal = {
        seal_id: "seal-dd-write-01",
        organization_id: "org-e2e",
        package_kind: "manual_review_package",
        request_id: "req-dd-write-1",
        report_id: "rep-dd-write-1",
        scope_id: "req-dd-write-1",
        manual_review_action: "compliance_due_diligence_checked",
        package_sha256: "b".repeat(64),
        manifest_schema_version: "manual_review_package/v2",
        classification: "restricted_regulatory",
        signoff_mode: "compliance_ops_signoff",
        seal_status: "pending_signoff",
        seal_format: "jws_json_flattened",
        signature_algorithm: null,
        kms_key_ref: null,
        certificate_fingerprint_sha256: null,
        certificate_bundle_ref: null,
        policy_version: "manual_package_sealing/v1",
        sealed_at: null,
        sealed_by_user_id: null,
        revoked_at: null,
        superseded_by_seal_id: null,
        required_signers: ["compliance_owner", "ops_owner"],
        completed_signoffs: 0,
        approved_required_signoffs: 0,
        required_signoffs: 2,
        signoffs: [],
        seal_envelope: {},
        verification_summary: {},
        created_at: "2026-07-08T10:06:00.000Z",
        updated_at: "2026-07-08T10:06:00.000Z"
      };

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(currentSeal)
      });
    });

    await page.route("**/api/app/evidence/manual-package/seals/seal-dd-write-01/signoffs", async (route: Route) => {
      const payload = parseSealSignoffPayload(route);
      expect(payload.signer_role).toBe("compliance_owner");
      expect(payload.decision).toBe("approved");
      expect(payload.signoff_method).toBe("platform_authenticated_2fa");

      currentSeal = {
        ...(currentSeal as NonNullable<typeof currentSeal>),
        seal_status: "pending_signoff",
        completed_signoffs: 1,
        approved_required_signoffs: 1,
        signoffs: [
          {
            id: "signoff-dd-write-01",
            seal_id: "seal-dd-write-01",
            organization_id: "org-e2e",
            signer_role: "compliance_owner",
            signer_user_id: "user-e2e",
            signer_display_name: "Compliance Owner",
            decision: "approved",
            signoff_method: "platform_authenticated_2fa",
            ticket_ref: null,
            notes: "Primeira aprovação",
            signed_at: "2026-07-08T10:07:00.000Z",
            metadata: {
              source: "evidence_manual_package_ui"
            }
          }
        ],
        updated_at: "2026-07-08T10:07:00.000Z"
      };

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(currentSeal)
      });
    });

    await page.goto("/evidence?request_id=req-dd-write-1&domain=due_diligence&action=compliance_due_diligence_checked&resource_type=address");

    const sealPanel = page.locator('[data-testid="evidence-manual-package-seal-panel"]').last();
    const signoffForm = page.locator('[data-testid="evidence-manual-package-signoff-form"]').last();
    await expect(page.getByTestId("evidence-manual-package-signoff-init-panel")).toContainText(
      "A inicialização cria a trilha institucional por hash"
    );
    await page.getByTestId("evidence-manual-package-init-signoff-request").click();
    await expect(sealPanel).toContainText("Seal ID");
    await expect(sealPanel).toContainText("seal-dd-write-01");
    await expect(signoffForm).toContainText("Registrar sign-off institucional");
    await expect(page.getByTestId("evidence-manual-package-signoff-role")).toHaveValue("compliance_owner");
    await page.getByTestId("evidence-manual-package-signoff-display-name").fill("Compliance Owner");
    await page.getByTestId("evidence-manual-package-signoff-notes").fill("Primeira aprovação");
    await page.getByTestId("evidence-manual-package-record-signoff").click();

    await expect(sealPanel).toContainText("1/2");
    await expect(sealPanel).toContainText(
      "Compliance Owner • Responsável de Compliance (compliance_owner) • Aprovado (approved)"
    );
    await expect(sealPanel).toContainText(
      "Responsável de Operações (ops_owner)"
    );
  });

  test("finaliza a selagem institucional quando o quorum obrigatório está completo", async ({ page }: { page: Page }) => {
    let currentSeal:
      | {
          seal_id: string;
          organization_id: string;
          package_kind: string;
          request_id: string;
          report_id: string | null;
          scope_id: string;
          manual_review_action: string;
          package_sha256: string;
          manifest_schema_version: string;
          classification: string;
          signoff_mode: string;
          seal_status: string;
          seal_format: string;
          signature_algorithm: string | null;
          kms_key_ref: string | null;
          certificate_fingerprint_sha256: string | null;
          certificate_bundle_ref: string | null;
          policy_version: string;
          sealed_at: string | null;
          sealed_by_user_id: string | null;
          revoked_at: string | null;
          superseded_by_seal_id: string | null;
          required_signers: string[];
          completed_signoffs: number;
          approved_required_signoffs: number;
          required_signoffs: number;
          signoffs: Array<Record<string, unknown>>;
          seal_envelope: Record<string, unknown>;
          verification_summary: Record<string, unknown>;
          created_at: string | null;
          updated_at: string | null;
        }
      | null = {
        seal_id: "seal-dd-final-01",
        organization_id: "org-e2e",
        package_kind: "manual_review_package",
        request_id: "req-dd-final-1",
        report_id: "rep-dd-final-1",
        scope_id: "req-dd-final-1",
        manual_review_action: "compliance_due_diligence_checked",
        package_sha256: "d".repeat(64),
        manifest_schema_version: "manual_review_package/v2",
        classification: "restricted_regulatory",
        signoff_mode: "compliance_ops_signoff",
        seal_status: "ready_to_seal",
        seal_format: "jws_json_flattened",
        signature_algorithm: null,
        kms_key_ref: null,
        certificate_fingerprint_sha256: null,
        certificate_bundle_ref: null,
        policy_version: "manual_package_sealing/v1",
        sealed_at: null,
        sealed_by_user_id: null,
        revoked_at: null,
        superseded_by_seal_id: null,
        required_signers: ["compliance_owner", "ops_owner"],
        completed_signoffs: 2,
        approved_required_signoffs: 2,
        required_signoffs: 2,
        signoffs: [
          {
            id: "signoff-dd-final-01",
            seal_id: "seal-dd-final-01",
            organization_id: "org-e2e",
            signer_role: "compliance_owner",
            signer_user_id: "user-e2e",
            signer_display_name: "Compliance Owner",
            decision: "approved",
            signoff_method: "platform_authenticated_2fa",
            ticket_ref: null,
            notes: "Aprovado por compliance",
            signed_at: "2026-07-08T10:07:00.000Z",
            metadata: { source: "evidence_manual_package_ui" }
          },
          {
            id: "signoff-dd-final-02",
            seal_id: "seal-dd-final-01",
            organization_id: "org-e2e",
            signer_role: "ops_owner",
            signer_user_id: "user-e2e",
            signer_display_name: "Ops Owner",
            decision: "approved",
            signoff_method: "platform_authenticated_2fa",
            ticket_ref: null,
            notes: "Aprovado por operações",
            signed_at: "2026-07-08T10:08:00.000Z",
            metadata: { source: "evidence_manual_package_ui" }
          }
        ],
        seal_envelope: {},
        verification_summary: {},
        created_at: "2026-07-08T10:06:00.000Z",
        updated_at: "2026-07-08T10:08:00.000Z"
      };

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
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "ADMIN",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=evidence**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-dd-final-01",
              user_id: "user-e2e",
              action: "compliance_due_diligence_checked",
              resource_type: "address",
              resource_id: "0xfinaleeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
              request_id: "req-dd-final-1",
              report_id: "rep-dd-final-1",
              file_hash_sha256: "c".repeat(64),
              created_at: "2026-07-08T10:00:00.000Z",
              metadata: {
                request_id: "req-dd-final-1",
                report_id: "rep-dd-final-1",
                address: "0xfinaleeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                chain: "ethereum",
                provider: "manual_review",
                provider_status: "degraded",
                degraded_reason: "manual_review_required",
                capability_status: "degraded",
                delivery_mode: "manual_review_pending",
                requires_human_review: true
              }
            },
            {
              id: "audit-dd-final-02",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_exported",
              resource_type: "audit_log",
              resource_id: "audit-dd-final-02",
              request_id: "req-dd-final-1",
              report_id: "rep-dd-final-1",
              file_hash_sha256: null,
              created_at: "2026-07-08T10:05:00.000Z",
              metadata: {
                request_id: "req-dd-final-1",
                report_id: "rep-dd-final-1",
                scope_id: "req-dd-final-1",
                filename: "ontrackchain-manual-review-due-diligence-req-dd-final-1.json",
                package_sha256: "d".repeat(64),
                manual_review_action: "compliance_due_diligence_checked"
              }
            }
          ],
          page: 1,
          count: 2,
          limit: 50,
          total: 2,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/evidence/manual-package/seal?**", async (route: Route) => {
      const url = new URL(route.request().url());
      expect(url.searchParams.get("package_sha256")).toBe("d".repeat(64));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(currentSeal)
      });
    });

    await page.route("**/api/app/evidence/manual-package/seals/seal-dd-final-01/finalize", async (route: Route) => {
      const payload = parseFinalizeSealPayload(route);
      expect(payload.metadata?.source).toBe("evidence_manual_package_ui");
      expect(payload.metadata?.request_id).toBe("req-dd-final-1");
      expect(payload.metadata?.report_id).toBe("rep-dd-final-1");
      expect(payload.metadata?.package_sha256).toBe("d".repeat(64));

      currentSeal = {
        ...(currentSeal as NonNullable<typeof currentSeal>),
        seal_status: "sealed",
        signature_algorithm: "HS256",
        kms_key_ref: "manual-package-local-hs256",
        certificate_bundle_ref: "local-hs256-trust-bundle",
        sealed_at: "2026-07-08T10:09:00.000Z",
        seal_envelope: {
          protected: "header",
          payload: "payload",
          signature: "signature"
        },
        verification_summary: {
          verified: true,
          verification_method: "local_hs256_self_check",
          issuer: "ontrackchain-investigation-api",
          key_id: "manual-package-local-hs256"
        },
        updated_at: "2026-07-08T10:09:00.000Z"
      };

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(currentSeal)
      });
    });

    await page.goto("/evidence?request_id=req-dd-final-1&domain=due_diligence&action=compliance_due_diligence_checked&resource_type=address");

    const sealPanel = page.locator('[data-testid="evidence-manual-package-seal-panel"]').last();
    const readyPanel = page.locator('[data-testid="evidence-manual-package-ready-to-seal"]').last();
    await expect(readyPanel).toContainText("Quorum obrigatório completo. O pacote está pronto para a etapa de selagem final.");
    await page.getByTestId("evidence-manual-package-finalize").click();

    await expect(sealPanel).toContainText("Selado");
    await expect(sealPanel).toContainText("HS256");
    await expect(sealPanel).toContainText("local-hs256-trust-bundle");
    await expect(sealPanel).toContainText("Sim");
    await expect(sealPanel).toContainText("local_hs256_self_check");
    await expect(sealPanel).toContainText("ontrackchain-investigation-api");
    await expect(page.getByTestId("evidence-manual-package-sealed-notice")).toContainText(
      "O pacote já possui selo institucional persistido e verificado."
    );
  });

  test("revoga o selo institucional com ticket e motivo", async ({ page }: { page: Page }) => {
    const seal = {
      seal_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      organization_id: "org-e2e",
      package_kind: "manual_review_package",
      request_id: "req-dd-revoke-1",
      report_id: "rep-dd-revoke-1",
      scope_id: "req-dd-revoke-1",
      manual_review_action: "compliance_due_diligence_checked",
      package_sha256: "e".repeat(64),
      manifest_schema_version: "manual_review_package/v2",
      classification: "restricted_regulatory",
      signoff_mode: "compliance_ops_signoff",
      seal_status: "pending_signoff",
      seal_format: "jws_json_flattened",
      signature_algorithm: null,
      kms_key_ref: null,
      certificate_fingerprint_sha256: null,
      certificate_bundle_ref: null,
      policy_version: "manual_package_sealing/v1",
      sealed_at: null,
      sealed_by_user_id: null,
      revoked_at: null,
      superseded_by_seal_id: null,
      required_signers: ["compliance_owner", "ops_owner"],
      completed_signoffs: 0,
      approved_required_signoffs: 0,
      required_signoffs: 2,
      signoffs: [],
      seal_envelope: {},
      verification_summary: {},
      created_at: "2026-07-08T10:00:00.000Z",
      updated_at: "2026-07-08T10:00:00.000Z"
    };

    await page.context().addCookies([
      { name: "otc_token", value: "pw-e2e-token", domain: "localhost", path: "/", httpOnly: false, secure: false, sameSite: "Lax" }
    ]);

    await page.route("**/api/app/auth/context", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "ADMIN",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=evidence**", async (route: Route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ data: [] }) });
    });

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-dd-revoke-01",
              user_id: "user-e2e",
              action: "compliance_due_diligence_checked",
              resource_type: "address",
              resource_id: "0xrevokeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
              request_id: "req-dd-revoke-1",
              report_id: "rep-dd-revoke-1",
              file_hash_sha256: "f".repeat(64),
              created_at: "2026-07-08T10:00:00.000Z",
              metadata: { request_id: "req-dd-revoke-1", report_id: "rep-dd-revoke-1", address: "0xrevokeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", chain: "ethereum" }
            },
            {
              id: "audit-dd-revoke-02",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_exported",
              resource_type: "audit_log",
              resource_id: "audit-dd-revoke-02",
              request_id: "req-dd-revoke-1",
              report_id: "rep-dd-revoke-1",
              file_hash_sha256: null,
              created_at: "2026-07-08T10:05:00.000Z",
              metadata: {
                request_id: "req-dd-revoke-1",
                report_id: "rep-dd-revoke-1",
                scope_id: "req-dd-revoke-1",
                filename: "ontrackchain-manual-review-due-diligence-req-dd-revoke-1.json",
                package_sha256: "e".repeat(64),
                manual_review_action: "compliance_due_diligence_checked"
              }
            }
          ],
          page: 1,
          count: 2,
          limit: 50,
          total: 2,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/evidence/manual-package/seal?**", async (route: Route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(seal) });
    });

    await page.route("**/api/app/evidence/manual-package/seals/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/revoke", async (route: Route) => {
      const payload = parseTicketedPayload(route);
      expect(payload.ticket_ref).toBe("GOV-123");
      expect(payload.reason).toBe("Documento substituído");
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ...seal, seal_status: "revoked", revoked_at: "2026-07-08T10:06:00.000Z" })
      });
    });

    await page.goto("/evidence?request_id=req-dd-revoke-1&domain=due_diligence&action=compliance_due_diligence_checked&resource_type=address");

    await page.getByTestId("evidence-manual-package-revoke-ticket-ref").fill("GOV-123");
    await page.getByTestId("evidence-manual-package-revoke-reason").fill("Documento substituído");
    await page.getByTestId("evidence-manual-package-revoke").click();

    await expect(page.getByTestId("evidence-manual-package-revoked-notice")).toContainText(
      "O pacote está com selo institucional revogado."
    );
    await expect(page.locator('[data-testid="evidence-manual-package-seal-panel"]').last()).toContainText("Revogado");
  });

  test("supersede o selo institucional apontando para um novo seal_id selado", async ({ page }: { page: Page }) => {
    const seal = {
      seal_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
      organization_id: "org-e2e",
      package_kind: "manual_review_package",
      request_id: "req-dd-supersede-1",
      report_id: "rep-dd-supersede-1",
      scope_id: "req-dd-supersede-1",
      manual_review_action: "compliance_due_diligence_checked",
      package_sha256: "0".repeat(64),
      manifest_schema_version: "manual_review_package/v2",
      classification: "restricted_regulatory",
      signoff_mode: "compliance_ops_signoff",
      seal_status: "sealed",
      seal_format: "jws_json_flattened",
      signature_algorithm: "HS256",
      kms_key_ref: "manual-package-local-hs256",
      certificate_fingerprint_sha256: null,
      certificate_bundle_ref: "local-hs256-trust-bundle",
      policy_version: "manual_package_sealing/v1",
      sealed_at: "2026-07-08T10:06:00.000Z",
      sealed_by_user_id: "user-e2e",
      revoked_at: null,
      superseded_by_seal_id: null,
      required_signers: ["compliance_owner", "ops_owner"],
      completed_signoffs: 2,
      approved_required_signoffs: 2,
      required_signoffs: 2,
      signoffs: [],
      seal_envelope: {},
      verification_summary: { verified: true, verification_method: "local_hs256_self_check" },
      created_at: "2026-07-08T10:00:00.000Z",
      updated_at: "2026-07-08T10:06:00.000Z"
    };

    await page.context().addCookies([
      { name: "otc_token", value: "pw-e2e-token", domain: "localhost", path: "/", httpOnly: false, secure: false, sameSite: "Lax" }
    ]);

    await page.route("**/api/app/auth/context", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "ADMIN",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/operations/work-items?module=evidence**", async (route: Route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ data: [] }) });
    });

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-dd-supersede-01",
              user_id: "user-e2e",
              action: "compliance_due_diligence_checked",
              resource_type: "address",
              resource_id: "0xsupersedeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
              request_id: "req-dd-supersede-1",
              report_id: "rep-dd-supersede-1",
              file_hash_sha256: "1".repeat(64),
              created_at: "2026-07-08T10:00:00.000Z",
              metadata: { request_id: "req-dd-supersede-1", report_id: "rep-dd-supersede-1", address: "0xsupersedeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", chain: "ethereum" }
            },
            {
              id: "audit-dd-supersede-02",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_exported",
              resource_type: "audit_log",
              resource_id: "audit-dd-supersede-02",
              request_id: "req-dd-supersede-1",
              report_id: "rep-dd-supersede-1",
              file_hash_sha256: null,
              created_at: "2026-07-08T10:05:00.000Z",
              metadata: {
                request_id: "req-dd-supersede-1",
                report_id: "rep-dd-supersede-1",
                scope_id: "req-dd-supersede-1",
                filename: "ontrackchain-manual-review-due-diligence-req-dd-supersede-1.json",
                package_sha256: "0".repeat(64),
                manual_review_action: "compliance_due_diligence_checked"
              }
            }
          ],
          page: 1,
          count: 2,
          limit: 50,
          total: 2,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/evidence/manual-package/seal?**", async (route: Route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(seal) });
    });

    await page.route("**/api/app/evidence/manual-package/seals/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb/supersede", async (route: Route) => {
      const payload = parseSupersedeSealPayload(route);
      expect(payload.superseded_by_seal_id).toBe("cccccccc-cccc-cccc-cccc-cccccccccccc");
      expect(payload.ticket_ref).toBe("GOV-555");
      expect(payload.reason).toBe("Nova versão do pacote");
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ...seal, seal_status: "superseded", superseded_by_seal_id: "cccccccc-cccc-cccc-cccc-cccccccccccc" })
      });
    });

    await page.goto("/evidence?request_id=req-dd-supersede-1&domain=due_diligence&action=compliance_due_diligence_checked&resource_type=address");

    await page.getByTestId("evidence-manual-package-supersede-seal-id").fill("cccccccc-cccc-cccc-cccc-cccccccccccc");
    await page.getByTestId("evidence-manual-package-supersede-ticket-ref").fill("GOV-555");
    await page.getByTestId("evidence-manual-package-supersede-reason").fill("Nova versão do pacote");
    await page.getByTestId("evidence-manual-package-supersede").click();

    await expect(page.getByTestId("evidence-manual-package-superseded-notice")).toContainText(
      "O pacote foi supersedido pelo seal_id cccccccc-cccc-cccc-cccc-cccccccccccc."
    );
  });
});

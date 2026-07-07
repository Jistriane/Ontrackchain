import { expect, test, type Page, type Route } from "@playwright/test";

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
      const payload = route.request().postDataJSON() as Record<string, unknown>;
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
      const payload = route.request().postDataJSON() as Record<string, unknown>;
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

    const evidenceDownload = page.waitForEvent("download");
    await page.getByTestId("evidence-export-selected-chain").click();
    const download = await evidenceDownload;
    expect(download.suggestedFilename()).toContain("ontrackchain-evidence-chain-rep-evi-02.json");
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
      const payload = route.request().postDataJSON() as Record<string, unknown>;
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
      const payload = route.request().postDataJSON() as Record<string, unknown>;
      expect(payload.action).toBe("compliance_due_diligence_checked");
      expect(payload.scope_id).toBe("req-dd-1");
      expect((payload.evidence_request as Record<string, unknown>).request_id).toBe("req-dd-1");
      expect((payload.dossier as Record<string, unknown>).package_type).toBe("due_diligence_manual_review_package");

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

    await page.goto("/evidence?request_id=req-dd-1&domain=due_diligence");

    await expect(page.locator('[data-testid="evidence-filter-action"] option[value="compliance_due_diligence_checked"]')).toHaveText(
      "Due diligence verificada (compliance_due_diligence_checked)"
    );
    await expect(page.locator('[data-testid="evidence-filter-resource-type"] option[value="address"]')).toHaveText(
      "Endereço (address)"
    );
    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("manual_review_pending");
    await expect(page.getByTestId("evidence-manual-review-panel")).toContainText("Revisão manual pendente");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("due_diligence_manual_review_package");
    await expect(page.getByTestId("evidence-manual-package-panel")).toContainText("Pacote manual de due diligence");
    await expect(page.getByTestId("evidence-manual-package-focus-chain")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-package-export-chain")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-package-export-package")).toBeVisible();
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

    const chainDownloadFromPackage = page.waitForEvent("download");
    await page.getByTestId("evidence-manual-package-export-chain").click();
    const chainDownload = await chainDownloadFromPackage;
    expect(chainDownload.suggestedFilename()).toContain("ontrackchain-manual-review-due-diligence-req-dd-1.json");
    await expect(page.getByTestId("evidence-manual-package-open-audit")).toHaveAttribute("href", /\/audit/);
    await expect(page.getByTestId("evidence-manual-package-open-reports")).toHaveAttribute("href", /\/reports/);
    await expect(page.getByTestId("evidence-manual-package-open-investigate")).toHaveAttribute("href", /\/investigate\?address=0xdddddddddddddddddddddddddddddddddddddddd/);
    await expect(page.getByTestId("evidence-manual-package-open-sanctions")).toHaveAttribute("href", /\/sanctions\?address=0xdddddddddddddddddddddddddddddddddddddddd/);
    await expect(page.getByTestId("evidence-manual-package-open-blocks")).toHaveAttribute("href", /\/blocks\?address=0xdddddddddddddddddddddddddddddddddddddddd/);

    const evidenceDownload = page.waitForEvent("download");
    await page.getByTestId("evidence-export-manual-package").click();
    const download = await evidenceDownload;
    expect(download.suggestedFilename()).toContain("ontrackchain-manual-review-due-diligence-req-dd-1.json");
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
      const payload = route.request().postDataJSON() as Record<string, unknown>;
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
      const payload = route.request().postDataJSON() as Record<string, unknown>;
      expect(payload.action).toBe("compliance_due_diligence_checked");
      expect(payload.scope_id).toBe("req-dd-1");
      expect((payload.evidence_request as Record<string, unknown>).report_id).toBe("rep-dd-1");
      expect((payload.dossier as Record<string, unknown>).signoff_mode).toBe("compliance_dd_signoff");

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

    const evidenceDownload = page.waitForEvent("download");
    await page.getByTestId("evidence-export-manual-package").click();
    const download = await evidenceDownload;
    expect(download.suggestedFilename()).toContain("ontrackchain-manual-review-due-diligence-req-dd-1.json");
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
      const payload = route.request().postDataJSON() as Record<string, unknown>;
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
      const payload = route.request().postDataJSON() as Record<string, unknown>;
      expect(payload.action).toBe("compliance_due_diligence_checked");
      expect(payload.scope_id).toBe("req-dd-1");
      expect((payload.manual_review as Record<string, unknown>).counterparty_context).toBe("exchange settlement");

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

    await expect(page.getByLabel("Ação de auditoria")).toHaveValue("compliance_due_diligence_checked");
    await expect(page.getByLabel("Tipo de recurso")).toHaveValue("address");
    await expect(page.locator('[data-testid="evidence-filter-action"] option[value="compliance_due_diligence_checked"]')).toHaveText(
      "Due diligence verificada (compliance_due_diligence_checked)"
    );
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

    const evidenceDownload = page.waitForEvent("download");
    await page.getByTestId("evidence-export-manual-package").click();
    const download = await evidenceDownload;
    expect(download.suggestedFilename()).toContain("ontrackchain-manual-review-due-diligence-req-dd-1.json");
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
      const payload = route.request().postDataJSON() as Record<string, unknown>;
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
      const payload = route.request().postDataJSON() as Record<string, unknown>;
      expect(payload.action).toBe("compliance_source_of_funds_checked");
      expect(payload.scope_id).toBe("req-sof-1");
      expect((payload.manual_review as Record<string, unknown>).purpose).toBe("origem declarada tesouraria OTC");
      expect((payload.manual_review as Record<string, unknown>).amount).toBe(125000);

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

    const evidenceDownload = page.waitForEvent("download");
    await page.getByTestId("evidence-export-manual-package").click();
    const download = await evidenceDownload;
    expect(download.suggestedFilename()).toContain("ontrackchain-manual-review-source-of-funds-req-sof-1.json");
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
      const payload = route.request().postDataJSON() as Record<string, unknown>;
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
      const payload = route.request().postDataJSON() as Record<string, unknown>;
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
      const payload = route.request().postDataJSON() as Record<string, unknown>;
      expect(payload.action).toBe("compliance_source_of_funds_checked");
      expect(payload.scope_id).toBe("req-sof-1");
      expect((payload.workspace_summary as Record<string, unknown>).event_id).toBe("audit-sof-workspace-01");
      expect((payload.dossier as Record<string, unknown>).signoff_mode).toBe("compliance_sof_signoff");

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

    const evidenceDownload = page.waitForEvent("download");
    await page.getByTestId("evidence-export-manual-package").click();
    const download = await evidenceDownload;
    expect(download.suggestedFilename()).toContain("ontrackchain-manual-review-source-of-funds-req-sof-1.json");
  });
});

import { expect, test, type Page, type Route } from "@playwright/test";
import { expectDownloadLikeResponse } from "./download-helpers";

test.describe("evidence ros-coaf dossier", () => {
  test("exporta dossiê regulatório ROS/COAF quando ros_id é resolvido via report_id", async ({ page }: { page: Page }) => {
    const rosId = "88888888-8888-4888-8888-888888888888";

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
          generated_at: "2026-07-04T10:00:00.000Z",
          page: 1,
          limit: 50,
          count: 1,
          total: 1,
          has_more: false,
          data: [
            {
              id: "audit-evi-ros-01",
              user_id: "user-e2e",
              action: "report_generated",
              resource_type: "case",
              resource_id: "11111111-1111-4111-8111-111111111111",
              request_id: "req-evi-ros-01",
              report_id: "rep-evi-02",
              file_hash_sha256: "a".repeat(64),
              created_at: "2026-07-04T10:00:00.000Z",
              metadata: {
                case_id: "11111111-1111-4111-8111-111111111111",
                request_id: "req-evi-ros-01",
                report_id: "rep-evi-02",
                file_hash_sha256: "a".repeat(64)
              }
            }
          ]
        })
      });
    });

    await page.route("**/api/app/reports/rep-evi-02/ros-coaf-ref", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ report_id: "rep-evi-02", ros_id: rosId })
      });
    });

    await page.route("**/api/app/reports/ros-coaf/*/regulatory-dossier", async (route: Route) => {
      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": `attachment; filename="ontrackchain-ros-coaf-regulatory-dossier-${rosId}.json"`,
          "x-ontrack-dossier-sha256": "b".repeat(64)
        },
        body: JSON.stringify({
          version: "v1",
          generated_at: "2026-07-04T10:00:00.000Z",
          dossier_sha256: "b".repeat(64),
          ros_record: { ros_id: rosId, audit: [] },
          work_item: null,
          work_events: [],
          work_comments: [],
          unified_timeline: []
        })
      });
    });

    await page.goto("/evidence?report_id=rep-evi-02");

    await page.getByRole("button", { name: /^Relatório gerado \(report_generated\)/i }).click();

    await expect(page.getByTestId("evidence-export-ros-dossier")).toBeVisible();
    await expect(page.getByTestId("evidence-log-timestamp-audit-evi-ros-01")).not.toContainText("2026-07-04T10:00:00.000Z");

    await expectDownloadLikeResponse(
      page,
      {
        urlPart: "/api/app/reports/ros-coaf/",
        expectedFilename: `ontrackchain-ros-coaf-regulatory-dossier-${rosId}.json`
      },
      async () => {
        await page.getByTestId("evidence-export-ros-dossier").click();
      }
    );
    await expect(page.getByTestId("evidence-hash-context")).toContainText("Hash principal do contexto");
    await expect(page.getByTestId("evidence-hash-context")).toContainText("b".repeat(64));
    await expect(page.getByTestId("evidence-hash-context")).toContainText("Origem do hash exibido");
    await expect(page.getByTestId("evidence-hash-context")).toContainText("dossie regulatorio");
    await expect(page.getByTestId("evidence-hash-context")).toContainText("Tipo de artefato resolvido");
    await expect(page.getByTestId("evidence-hash-context")).toContainText("artefato regulatorio consolidado");
    await expect(page.getByTestId("evidence-dossier-detail-context")).toContainText("Contexto regulatorio do dossie");
    await expect(page.getByTestId("evidence-dossier-detail-context")).toContainText("Arquivo do dossie");
    await expect(page.getByTestId("evidence-dossier-detail-context")).toContainText(
      `ontrackchain-ros-coaf-regulatory-dossier-${rosId}.json`
    );
    await expect(page.getByTestId("evidence-dossier-detail-context")).toContainText("Hash do dossie");
    await expect(page.getByTestId("evidence-dossier-detail-context")).toContainText("b".repeat(64));
    await expect(page.getByTestId("evidence-dossier-detail-open-report")).toHaveAttribute(
      "href",
      "/reports?history_report_id=rep-evi-02"
    );
    await expect(page.getByTestId("evidence-dossier-detail-open-roscoaf")).toHaveAttribute(
      "href",
      `/ros-coaf?ros_id=${rosId}&report_id=rep-evi-02`
    );
    await expect(page.getByTestId("evidence-chain-hash-source")).toContainText("Origem do hash exibido");
    await expect(page.getByTestId("evidence-chain-hash-source")).toContainText("dossie regulatorio");
    await expect(page.getByTestId("evidence-chain-artifact-type")).toContainText("Tipo de artefato resolvido");
    await expect(page.getByTestId("evidence-chain-artifact-type")).toContainText("artefato regulatorio consolidado");
    await expect(page.getByTestId("evidence-chain-first-event")).not.toContainText("2026-07-04T10:00:00.000Z");
    await expect(page.getByTestId("evidence-chain-last-event")).not.toContainText("2026-07-04T10:00:00.000Z");
    await expect(page.getByTestId("evidence-chain-dossier-context")).toContainText("Contexto regulatorio do dossie");
    await expect(page.getByTestId("evidence-chain-dossier-context")).toContainText("Arquivo do dossie");
    await expect(page.getByTestId("evidence-chain-dossier-context")).toContainText(
      `ontrackchain-ros-coaf-regulatory-dossier-${rosId}.json`
    );
    await expect(page.getByTestId("evidence-chain-dossier-context")).toContainText("Hash do dossie");
    await expect(page.getByTestId("evidence-chain-dossier-context")).toContainText("b".repeat(64));
    await expect(page.getByTestId("evidence-chain-open-report")).toHaveAttribute(
      "href",
      "/reports?history_report_id=rep-evi-02"
    );
    await expect(page.getByTestId("evidence-chain-open-roscoaf")).toHaveAttribute(
      "href",
      `/ros-coaf?ros_id=${rosId}&report_id=rep-evi-02`
    );
  });

  test("preserva a negacao semantica ao resolver a referencia ROS/COAF a partir do report_id", async ({ page }: { page: Page }) => {
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
          generated_at: "2026-07-04T10:00:00.000Z",
          page: 1,
          limit: 50,
          count: 1,
          total: 1,
          has_more: false,
          data: [
            {
              id: "audit-evi-ros-02",
              user_id: "user-e2e",
              action: "report_generated",
              resource_type: "case",
              resource_id: "11111111-1111-4111-8111-111111111111",
              request_id: "req-evi-ros-02",
              report_id: "rep-evi-03",
              file_hash_sha256: "a".repeat(64),
              created_at: "2026-07-04T10:00:00.000Z",
              metadata: {
                case_id: "11111111-1111-4111-8111-111111111111",
                request_id: "req-evi-ros-02",
                report_id: "rep-evi-03",
                file_hash_sha256: "a".repeat(64)
              }
            }
          ]
        })
      });
    });

    await page.route("**/api/app/reports/rep-evi-03/ros-coaf-ref", async (route: Route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "report_read_role_required" })
      });
    });

    await page.goto("/evidence?report_id=rep-evi-03");
    await page.getByRole("button", { name: /^Relatório gerado \(report_generated\)/i }).click();

    await expect(page.getByTestId("evidence-linked-ros-message")).toContainText(
      "A leitura/listagem de relatórios exige papel operacional: ADMIN, AUDITOR, ANALYST ou VIEWER."
    );
    await expect(page.getByTestId("evidence-export-ros-dossier")).toHaveCount(0);
  });
});

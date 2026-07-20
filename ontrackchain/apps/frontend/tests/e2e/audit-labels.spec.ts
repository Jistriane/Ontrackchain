import { expect, test, type Page, type Route } from "@playwright/test";

import { expectDownloadLikeResponse } from "./download-helpers";
import { seedFrontendAuth } from "./seed-frontend-auth";

type AuditMetadata = {
  [key: string]: unknown;
};

type AuditLogRow<TMetadata extends AuditMetadata = AuditMetadata> = {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  request_id: string;
  report_id: string | null;
  file_hash_sha256: string | null;
  metadata: TMetadata;
  created_at: string;
};

type ManualPackageMfaViolationMetadata = AuditMetadata & {
  request_id?: string;
  report_id?: string;
  seal_id?: string;
  scope_id?: string;
  package_sha256?: string;
  manual_review_action?: string;
  auth_role?: string;
  asserted_signer_role?: string;
  mfa_mode?: string;
  two_factor_status?: string;
  mfa_provider_homologated?: boolean;
  detail?: string;
};

type ManualPackageExportMetadata = AuditMetadata & {
  request_id?: string;
  report_id?: string;
  scope_id?: string;
  filename?: string;
  package_sha256?: string;
  manual_review_action?: string;
  workspace_status?: string;
  case_id?: string;
};

type ManualPackageMfaAuditRow = AuditLogRow<ManualPackageMfaViolationMetadata | ManualPackageExportMetadata>;

async function seedAuditPage(page: Page, options?: { role?: string }) {
  await seedFrontendAuth(page, { role: options?.role ?? "AUDITOR" });
}

test.describe("audit labels", () => {
  test("preserva a negacao semantica da leitura auditavel quando a sessao esta ausente", async ({ page }) => {
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
          mfa_provider_homologated: "true",
          two_factor: "ok"
        })
      });
    });

    await page.goto("/audit");

    await expect(page.getByText("Falha ao carregar auditoria: Sua sessão expirou ou não foi autenticada.")).toBeVisible();
    await expect(page.getByTestId("audit-empty")).toHaveCount(0);
  });

  test("renderiza acao e tipo de recurso com label amigavel e codigo tecnico preservado", async ({ page }) => {
    await seedAuditPage(page);

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const url = new URL(route.request().url());
      const action = url.searchParams.get("action");
      const resourceType = url.searchParams.get("resource_type");
      const resourceId = url.searchParams.get("resource_id");

      const allRows = [
        {
          id: "audit-log-01",
          user_id: "user-e2e",
          action: "report_generated",
          resource_type: "report",
          resource_id: "report-001",
          request_id: "req-audit-001",
          report_id: "report-001",
          file_hash_sha256: "a".repeat(64),
          metadata: {
            case_id: "case-001",
            request_id: "req-audit-001"
          },
          created_at: "2026-07-07T12:00:00.000Z"
        },
        {
          id: "audit-log-02",
          user_id: "user-e2e",
          action: "authorization_denied",
          resource_type: "operational_alerts",
          resource_id: "alert-001",
          request_id: "req-audit-002",
          report_id: null,
          file_hash_sha256: null,
          metadata: {
            detail: "admin_role_required"
          },
          created_at: "2026-07-07T12:05:00.000Z"
        },
        {
          id: "audit-log-03",
          user_id: "user-e2e",
          action: "coaf_regulatory_dossier_downloaded",
          resource_type: "ros_record",
          resource_id: "99999999-9999-4999-8999-999999999999",
          request_id: "req-audit-003",
          report_id: "rep-ros-dossier-01",
          file_hash_sha256: null,
          metadata: {
            filename: "ontrackchain-ros-coaf-regulatory-dossier-99999999-9999-4999-8999-999999999999.json",
            dossier_sha256: "a".repeat(64)
          },
          created_at: "2026-07-07T12:10:00.000Z"
        },
        {
          id: "audit-log-04",
          user_id: "user-e2e",
          action: "evidence_manual_review_package_exported",
          resource_type: "audit_log",
          resource_id: "audit-log-manual-001",
          request_id: "req-dd-1",
          report_id: "rep-dd-1",
          file_hash_sha256: null,
          metadata: {
            scope_id: "req-dd-1",
            filename: "ontrackchain-manual-review-due-diligence-req-dd-1.json",
            package_sha256: "c".repeat(64),
            manual_review_action: "compliance_due_diligence_checked",
            workspace_status: "reviewing",
            case_id: "case-dd-1",
            address: "0xabc123",
            chain: "ethereum"
          },
          created_at: "2026-07-07T12:15:00.000Z"
        },
        {
          id: "audit-log-identity-01",
          user_id: "linked-user-e2e",
          action: "team_external_identity_linked",
          resource_type: "team_user",
          resource_id: "team-member-audit-01",
          request_id: "req-team-identity-01",
          report_id: null,
          file_hash_sha256: null,
          metadata: {
            member_id: "team-member-audit-01",
            provider: "keycloak",
            external_subject: "kc-user-01",
            email_snapshot: "ops@ontrackchain.local",
            role_snapshot: "ADMIN",
            actor_user_id: "user-e2e",
            linked_user_id: "linked-user-e2e",
            auth_method: "jwt",
            tenant_role: "ADMIN"
          },
          created_at: "2026-07-07T12:14:00.000Z"
        },
        {
          id: "audit-log-05",
          user_id: "user-e2e",
          action: "evidence_manual_review_package_sealed",
          resource_type: "evidence_package_seal",
          resource_id: "seal-001",
          request_id: "req-dd-1",
          report_id: "rep-dd-1",
          file_hash_sha256: null,
          metadata: {
            seal_id: "seal-001",
            scope_id: "req-dd-1",
            package_sha256: "c".repeat(64),
            manual_review_action: "compliance_due_diligence_checked",
            signature_algorithm: "HS256",
            certificate_bundle_ref: "local-hs256-trust-bundle",
            verification_summary: {
              verification_method: "local_hs256_self_check"
            }
          },
          created_at: "2026-07-07T12:16:00.000Z"
        }
      ];

      const filteredRows = allRows.filter((row) => {
        if (action && row.action !== action) {
          return false;
        }
        if (resourceType && row.resource_type !== resourceType) {
          return false;
        }
        if (resourceId && row.resource_id !== resourceId) {
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
          count: filteredRows.length,
          limit: 50,
          total: filteredRows.length,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.goto("/audit");

    await expect(page.locator('[data-testid="audit-filter-action"] option[value="report_generated"]')).toHaveText(
      "Relatório gerado (report_generated)"
    );
    await expect(
      page.locator('[data-testid="audit-filter-action"] option[value="coaf_regulatory_dossier_downloaded"]')
    ).toHaveText("Dossie regulatorio COAF exportado (coaf_regulatory_dossier_downloaded)");
    await expect(
      page.locator('[data-testid="audit-filter-action"] option[value="evidence_manual_review_package_exported"]')
    ).toHaveText("Pacote manual regulatorio exportado (evidence_manual_review_package_exported)");
    await expect(
      page.locator('[data-testid="audit-filter-action"] option[value="evidence_manual_review_package_sealed"]')
    ).toHaveText("Pacote manual regulatorio selado (evidence_manual_review_package_sealed)");
    await expect(
      page.locator('[data-testid="audit-filter-action"] option[value="evidence_manual_review_package_seal_revoked"]')
    ).toHaveText("Selo institucional do pacote revogado (evidence_manual_review_package_seal_revoked)");
    await expect(
      page.locator('[data-testid="audit-filter-action"] option[value="evidence_manual_review_package_seal_superseded"]')
    ).toHaveText("Selo institucional do pacote supersedido (evidence_manual_review_package_seal_superseded)");
    await expect(
      page.locator('[data-testid="audit-filter-action"] option[value="team_external_identity_linked"]')
    ).toHaveText("Identidade federada vinculada ao usuário local (team_external_identity_linked)");
    await expect(
      page.locator('[data-testid="audit-filter-action"] option[value="team_external_identity_unlinked"]')
    ).toHaveText("Identidade federada desvinculada do usuário local (team_external_identity_unlinked)");
    await expect(page.locator('[data-testid="audit-filter-resource-type"] option[value="report"]')).toHaveText(
      "Relatório (report)"
    );
    await expect(page.locator('[data-testid="audit-filter-resource-type"] option[value="ros_record"]')).toHaveText(
      "ROS/COAF (ros_record)"
    );
    await expect(page.locator('[data-testid="audit-filter-resource-type"] option[value="team_user"]')).toHaveText(
      "Usuário do tenant (team_user)"
    );
    await expect(page.locator('[data-testid="audit-filter-resource-type"] option[value="audit_log"]')).toHaveText(
      "Log de auditoria (audit_log)"
    );
    await expect(
      page.locator('[data-testid="audit-filter-resource-type"] option[value="evidence_package_seal"]')
    ).toHaveText("Selo institucional do pacote (evidence_package_seal)");

    await page.selectOption('[data-testid="audit-filter-action"]', "report_generated");
    await page.click('[data-testid="audit-search-btn"]');

    const filteredRow = page.locator('[data-testid="audit-row"]').first();
    await expect(filteredRow).toContainText("Relatório gerado (report_generated)");
    await expect(filteredRow).toContainText("Relatório (report)");

    await filteredRow.click();

    await expect(page.locator('[data-testid="audit-details-panel"]')).toContainText(
      "Relatório gerado (report_generated)"
    );
    await expect(page.locator('[data-testid="audit-details-panel"]')).toContainText("Relatório (report)");
  });

  test("ativa preset de identidade federada e expõe contexto auditável com retorno ao Team", async ({ page }) => {
    await seedAuditPage(page, { role: "ADMIN" });

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const url = new URL(route.request().url());
      const rows = [
        {
          id: "audit-log-fed-01",
          user_id: "linked-user-e2e",
          action: "team_external_identity_unlinked",
          resource_type: "team_user",
          resource_id: "team-member-fed-01",
          request_id: "req-fed-01",
          report_id: null,
          file_hash_sha256: null,
          metadata: {
            member_id: "team-member-fed-01",
            provider: "keycloak",
            external_subject: "kc-user-fed-01",
            actor_user_id: "user-e2e",
            linked_user_id: "linked-user-e2e",
            external_user_id: "oidc-sub-fed-actor",
            auth_method: "jwt",
            tenant_role: "ADMIN"
          },
          created_at: "2026-07-07T12:25:00.000Z"
        },
        {
          id: "audit-log-fed-02",
          user_id: "linked-user-e2e",
          action: "team_external_identity_linked",
          resource_type: "team_user",
          resource_id: "team-member-fed-01",
          request_id: "req-fed-00",
          report_id: null,
          file_hash_sha256: null,
          metadata: {
            member_id: "team-member-fed-01",
            provider: "keycloak",
            external_subject: "kc-user-fed-00",
            email_snapshot: "admin@ontrackchain.local",
            role_snapshot: "ADMIN",
            actor_user_id: "user-e2e",
            linked_user_id: "linked-user-e2e",
            auth_method: "jwt",
            tenant_role: "ADMIN"
          },
          created_at: "2026-07-07T12:20:00.000Z"
        }
      ].filter((row) => {
        const action = url.searchParams.get("action");
        const resourceType = url.searchParams.get("resource_type");
        const resourceId = url.searchParams.get("resource_id");
        return (!action || row.action === action) && (!resourceType || row.resource_type === resourceType) && (!resourceId || row.resource_id === resourceId);
      });

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: rows,
          page: 1,
          count: rows.length,
          limit: 200,
          total: rows.length,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.goto("/audit?preset=identity-federated&resource_id=team-member-fed-01");

    await expect(page.getByTestId("audit-federated-identity-preset-notice")).toContainText(
      "Preset ativo: trilha auditada de identidade federada para team-member-fed-01."
    );
    await expect(page.getByText("Eventos federados", { exact: true })).toBeVisible();
    await expect(page.getByText("Vínculos persistidos", { exact: true })).toBeVisible();
    await expect(page.getByText("Desvínculos persistidos", { exact: true })).toBeVisible();
    await expect(page.getByText("Membros afetados", { exact: true })).toBeVisible();
    await expect(page.getByText("Último provider", { exact: true })).toBeVisible();
    await expect(page.getByText("Último external_subject", { exact: true })).toBeVisible();
    await expect(page.getByTestId("audit-federated-identity-open-team")).toHaveAttribute(
      "href",
      "/team?member_id=team-member-fed-01"
    );
    await expect(page.locator('[data-testid="audit-filter-resource-type"]')).toHaveValue("team_user");
    await expect(page.locator('[data-testid="audit-filter-resource-id"]')).toHaveValue("team-member-fed-01");

    const federatedRow = page.locator('[data-testid="audit-row"]').first();
    await expect(federatedRow).toContainText("Identidade federada desvinculada do usuário local (team_external_identity_unlinked)");
    await expect(federatedRow).toContainText("Usuário do tenant (team_user)");
    await federatedRow.click();

    const detail = page.getByTestId("audit-federated-identity-detail-context");
    await expect(detail).toContainText("Contexto auditável da identidade federada");
    await expect(detail).toContainText("Provider: keycloak");
    await expect(detail).toContainText("External subject: kc-user-fed-01");
    await expect(detail).toContainText("Actor user ID: user-e2e");
    await expect(detail).toContainText("Linked user ID: linked-user-e2e");
    await expect(detail).toContainText("External user ID: oidc-sub-fed-actor");
    await expect(detail).toContainText("Método de autenticação: jwt");
    await expect(detail).toContainText("Papel do tenant: ADMIN");
    await expect(page.getByTestId("audit-federated-identity-detail-open-team")).toHaveAttribute(
      "href",
      "/team?member_id=team-member-fed-01"
    );
  });

  test("renderiza contexto auditavel do pacote manual com hash principal do manifesto", async ({ page }) => {
    await seedAuditPage(page);

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-log-manual-01",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_exported",
              resource_type: "audit_log",
              resource_id: "audit-log-manual-01",
              request_id: "req-dd-1",
              report_id: "rep-dd-1",
              file_hash_sha256: null,
              metadata: {
                scope_id: "req-dd-1",
                filename: "ontrackchain-manual-review-due-diligence-req-dd-1.json",
                package_sha256: "d".repeat(64),
                manual_review_action: "compliance_due_diligence_checked",
                workspace_status: "sealed",
                case_id: "case-dd-1",
                address: "0xabc123",
                chain: "ethereum"
              },
              created_at: "2026-07-07T12:15:00.000Z"
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

    await page.goto("/audit?action=evidence_manual_review_package_exported&resource_type=audit_log&request_id=req-dd-1");

    const manualRow = page.locator('[data-testid="audit-row"]').first();
    await expect(manualRow).toContainText("Pacote manual regulatorio exportado (evidence_manual_review_package_exported)");
    await expect(manualRow).toContainText("Log de auditoria (audit_log)");
    await manualRow.click();

    await expect(page.getByTestId("audit-hash-context")).toContainText(`Hash principal do contexto: ${"d".repeat(64)}`);
    await expect(page.getByTestId("audit-hash-context")).toContainText(
      "Origem do hash exibido: manifesto do pacote manual"
    );
    await expect(page.getByTestId("audit-hash-context")).toContainText(
      "Tipo de artefato resolvido: artefato manual regulatorio selado por manifesto"
    );
    await expect(page.getByTestId("audit-manual-package-detail-context")).toContainText(
      "Contexto auditavel do pacote manual"
    );
    await expect(page.getByTestId("audit-manual-package-detail-context")).toContainText(
      "Arquivo do pacote: ontrackchain-manual-review-due-diligence-req-dd-1.json"
    );
    await expect(page.getByTestId("audit-manual-package-detail-context")).toContainText(
      `Hash do pacote: ${"d".repeat(64)}`
    );
    await expect(page.getByTestId("audit-manual-package-detail-context")).toContainText(
      "Acao manual originadora: Due diligence verificada"
    );
    await expect(page.getByTestId("audit-manual-package-detail-context")).toContainText("Scope ID: req-dd-1");
    await expect(page.getByTestId("audit-manual-package-detail-context")).toContainText(
      "Status local do workspace: sealed"
    );
    await expect(page.getByTestId("audit-manual-package-detail-open-evidence-source")).toHaveAttribute(
      "href",
      "/evidence?request_id=req-dd-1&action=compliance_due_diligence_checked&resource_type=address&audit_origin=manual_package&domain=due_diligence&report_id=rep-dd-1"
    );
  });

  test("correlaciona evento de selagem ao contexto manual exportado e expõe resumo criptográfico", async ({ page }) => {
    await seedAuditPage(page);

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-log-manual-10",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_sealed",
              resource_type: "evidence_package_seal",
              resource_id: "seal-dd-01",
              request_id: "req-dd-seal-1",
              report_id: "rep-dd-seal-1",
              file_hash_sha256: null,
              metadata: {
                seal_id: "seal-dd-01",
                scope_id: "req-dd-seal-1",
                package_sha256: "f".repeat(64),
                manual_review_action: "compliance_due_diligence_checked",
                seal_status: "sealed",
                signature_algorithm: "HS256",
                certificate_bundle_ref: "local-hs256-trust-bundle",
                verification_summary: {
                  verification_method: "local_hs256_self_check"
                }
              },
              created_at: "2026-07-07T12:16:00.000Z"
            },
            {
              id: "audit-log-manual-11",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_exported",
              resource_type: "audit_log",
              resource_id: "audit-log-manual-11",
              request_id: "req-dd-seal-1",
              report_id: "rep-dd-seal-1",
              file_hash_sha256: null,
              metadata: {
                scope_id: "req-dd-seal-1",
                filename: "ontrackchain-manual-review-due-diligence-req-dd-seal-1.json",
                package_sha256: "f".repeat(64),
                manual_review_action: "compliance_due_diligence_checked",
                workspace_status: "sealed",
                case_id: "case-dd-seal-1",
                address: "0xabc123",
                chain: "ethereum"
              },
              created_at: "2026-07-07T12:15:00.000Z"
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

    await page.goto("/audit?action=evidence_manual_review_package_sealed&resource_type=evidence_package_seal&request_id=req-dd-seal-1");

    await expect(page.getByTestId("audit-manual-preset-notice")).toContainText(
      "Preset ativo: trilha auditada do pacote manual para request_id req-dd-seal-1."
    );
    const sealRow = page.locator('[data-testid="audit-row"]').first();
    await expect(sealRow).toContainText("Pacote manual regulatorio selado (evidence_manual_review_package_sealed)");
    await expect(sealRow).toContainText("Selo institucional do pacote (evidence_package_seal)");
    await sealRow.click();

    await expect(page.getByTestId("audit-hash-context")).toContainText(`Hash principal do contexto: ${"f".repeat(64)}`);
    await expect(page.getByTestId("audit-manual-package-detail-context")).toContainText(
      "Etapa auditavel: Pacote manual regulatorio selado (evidence_manual_review_package_sealed)"
    );
    await expect(page.getByTestId("audit-manual-package-detail-context")).toContainText(
      "Arquivo do pacote: ontrackchain-manual-review-due-diligence-req-dd-seal-1.json"
    );
    await expect(page.getByTestId("audit-manual-package-detail-context")).toContainText("Status da selagem: Selado");
    await expect(page.getByTestId("audit-manual-package-detail-context")).toContainText("Seal ID: seal-dd-01");
    await expect(page.getByTestId("audit-manual-package-detail-context")).toContainText(
      "Algoritmo de assinatura: HS256"
    );
    await expect(page.getByTestId("audit-manual-package-detail-context")).toContainText(
      "Trust bundle: local-hs256-trust-bundle"
    );
    await expect(page.getByTestId("audit-manual-package-detail-context")).toContainText(
      "Metodo de verificacao: local_hs256_self_check"
    );
    await expect(page.getByTestId("audit-manual-package-detail-open-evidence-source")).toHaveAttribute(
      "href",
      "/evidence?request_id=req-dd-seal-1&action=compliance_due_diligence_checked&resource_type=address&audit_origin=manual_package&domain=due_diligence&report_id=rep-dd-seal-1"
    );
  });

  test("expõe contexto de governança no detalhe de revogação do selo institucional", async ({ page }) => {
    await seedAuditPage(page);

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-log-manual-revoke-01",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_seal_revoked",
              resource_type: "evidence_package_seal",
              resource_id: "seal-dd-revoke-01",
              request_id: "req-dd-revoke-1",
              report_id: "rep-dd-revoke-1",
              file_hash_sha256: null,
              metadata: {
                seal_id: "seal-dd-revoke-01",
                scope_id: "req-dd-revoke-1",
                package_sha256: "9".repeat(64),
                manual_review_action: "compliance_due_diligence_checked",
                seal_status: "revoked",
                ticket_ref: "GOV-123",
                reason: "Documento substituido por versao retificada"
              },
              created_at: "2026-07-07T12:18:30.000Z"
            },
            {
              id: "audit-log-manual-revoke-02",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_exported",
              resource_type: "audit_log",
              resource_id: "audit-log-manual-revoke-02",
              request_id: "req-dd-revoke-1",
              report_id: "rep-dd-revoke-1",
              file_hash_sha256: null,
              metadata: {
                scope_id: "req-dd-revoke-1",
                filename: "ontrackchain-manual-review-due-diligence-req-dd-revoke-1.json",
                package_sha256: "9".repeat(64),
                manual_review_action: "compliance_due_diligence_checked",
                workspace_status: "sealed"
              },
              created_at: "2026-07-07T12:15:00.000Z"
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

    await page.goto(
      "/audit?action=evidence_manual_review_package_seal_revoked&resource_type=evidence_package_seal&request_id=req-dd-revoke-1"
    );

    const revokedRow = page.locator('[data-testid="audit-row"]').first();
    await expect(revokedRow).toContainText(
      "Selo institucional do pacote revogado (evidence_manual_review_package_seal_revoked)"
    );
    await revokedRow.click();

    const detail = page.getByTestId("audit-manual-package-detail-context");
    await expect(detail).toContainText("Status da selagem: Revogado");
    await expect(detail).toContainText("Ticket de governanca: GOV-123");
    await expect(detail).toContainText("Motivo de governanca: Documento substituido por versao retificada");
    await expect(detail).toContainText("Revogado em:");
    await expect(detail).not.toContainText("2026-07-07T12:18:30.000Z");
    await expect(page.getByTestId("audit-manual-package-detail-open-evidence-source")).toHaveAttribute(
      "href",
      "/evidence?request_id=req-dd-revoke-1&action=compliance_due_diligence_checked&resource_type=address&audit_origin=manual_package&domain=due_diligence&report_id=rep-dd-revoke-1"
    );
  });

  test("expõe contexto de governança no detalhe de supersedência do selo institucional", async ({ page }) => {
    await seedAuditPage(page);

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-log-manual-supersede-01",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_seal_superseded",
              resource_type: "evidence_package_seal",
              resource_id: "seal-dd-supersede-01",
              request_id: "req-dd-supersede-1",
              report_id: "rep-dd-supersede-1",
              file_hash_sha256: null,
              metadata: {
                seal_id: "seal-dd-supersede-01",
                scope_id: "req-dd-supersede-1",
                package_sha256: "8".repeat(64),
                manual_review_action: "compliance_due_diligence_checked",
                seal_status: "superseded",
                ticket_ref: "GOV-555",
                reason: "Nova versão do pacote aprovada",
                superseded_by_seal_id: "seal-dd-supersede-02"
              },
              created_at: "2026-07-07T12:19:30.000Z"
            },
            {
              id: "audit-log-manual-supersede-02",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_exported",
              resource_type: "audit_log",
              resource_id: "audit-log-manual-supersede-02",
              request_id: "req-dd-supersede-1",
              report_id: "rep-dd-supersede-1",
              file_hash_sha256: null,
              metadata: {
                scope_id: "req-dd-supersede-1",
                filename: "ontrackchain-manual-review-due-diligence-req-dd-supersede-1.json",
                package_sha256: "8".repeat(64),
                manual_review_action: "compliance_due_diligence_checked",
                workspace_status: "sealed"
              },
              created_at: "2026-07-07T12:15:00.000Z"
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

    await page.goto(
      "/audit?action=evidence_manual_review_package_seal_superseded&resource_type=evidence_package_seal&request_id=req-dd-supersede-1"
    );

    const supersededRow = page.locator('[data-testid="audit-row"]').first();
    await expect(supersededRow).toContainText(
      "Selo institucional do pacote supersedido (evidence_manual_review_package_seal_superseded)"
    );
    await supersededRow.click();

    const detail = page.getByTestId("audit-manual-package-detail-context");
    await expect(detail).toContainText("Status da selagem: Substituído");
    await expect(detail).toContainText("Ticket de governanca: GOV-555");
    await expect(detail).toContainText("Motivo de governanca: Nova versão do pacote aprovada");
    await expect(detail).toContainText("Supersedido por: seal-dd-supersede-02");
    await expect(detail).toContainText("Supersedido em:");
    await expect(detail).not.toContainText("2026-07-07T12:19:30.000Z");
    await expect(page.getByTestId("audit-manual-package-detail-open-evidence-source")).toHaveAttribute(
      "href",
      "/evidence?request_id=req-dd-supersede-1&action=compliance_due_diligence_checked&resource_type=address&audit_origin=manual_package&domain=due_diligence&report_id=rep-dd-supersede-1"
    );
  });

  test("ativa preset dedicado do dossie regulatorio via query string", async ({ page }) => {
    await seedAuditPage(page);

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const url = new URL(route.request().url());
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-log-preset-01",
              user_id: "user-e2e",
              action: "coaf_regulatory_dossier_downloaded",
              resource_type: "ros_record",
              resource_id: "99999999-9999-4999-8999-999999999999",
              request_id: "req-audit-preset-01",
              report_id: "rep-ros-dossier-01",
              file_hash_sha256: "f".repeat(64),
              metadata: {
                filename: "ontrackchain-ros-coaf-regulatory-dossier-99999999-9999-4999-8999-999999999999.json",
                dossier_sha256: "b".repeat(64)
              },
              created_at: "2026-07-07T12:10:00.000Z"
            }
          ].filter((row) => {
            const action = url.searchParams.get("action");
            const resourceType = url.searchParams.get("resource_type");
            const resourceId = url.searchParams.get("resource_id");
            return (!action || row.action === action) && (!resourceType || row.resource_type === resourceType) && (!resourceId || row.resource_id === resourceId);
          }),
          page: 1,
          count: 1,
          limit: 50,
          total: 1,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.goto(
      "/audit?action=coaf_regulatory_dossier_downloaded&resource_type=ros_record&resource_id=99999999-9999-4999-8999-999999999999&report_id=rep-ros-dossier-01"
    );

    await expect(page.getByTestId("audit-dossier-preset-notice")).toContainText(
      "Preset ativo: emissoes auditadas do dossie regulatorio ROS/COAF para 99999999-9999-4999-8999-999999999999."
    );
    await expect(page.getByTestId("audit-dossier-preset-latest-context")).toContainText(
      "Ultimo artefato visivel neste recorte:"
    );
    await expect(page.getByTestId("audit-dossier-preset-latest-context")).toContainText(
      "report_id: rep-ros-dossier-01"
    );
    await expect(page.getByTestId("audit-dossier-preset-latest-context")).toContainText(
      "arquivo: ontrackchain-ros-coaf-regulatory-dossier-99999999-9999-4999-8999-999999999999.json"
    );
    await expect(page.getByText("Downloads do dossie")).toBeVisible();
    await expect(page.getByText("ROS unicos")).toBeVisible();
    await expect(page.getByText("Ultimo hash do dossie")).toBeVisible();
    await expect(page.getByText("Ultimo report_id")).toBeVisible();
    await expect(page.getByText("Ultimo arquivo")).toBeVisible();
    await expect(page.getByText("bbbbbbbbbbbbbbbb...")).toBeVisible();
    await expect(page.getByTestId("audit-dossier-preset-latest-context")).toContainText("rep-ros-dossier-01");
    await expect(
      page.getByTestId("audit-dossier-preset-latest-context")
    ).toContainText("ontrackchain-ros-coaf-regulatory-dossier-99999999-9999-4999-8999-999999999999.json");
    await expect(page.getByTestId("audit-dossier-open-latest-report")).toHaveAttribute(
      "href",
      "/reports?history_report_id=rep-ros-dossier-01"
    );
    await expect(page.getByTestId("audit-dossier-open-roscoaf")).toHaveAttribute(
      "href",
      "/ros-coaf?ros_id=99999999-9999-4999-8999-999999999999&report_id=rep-ros-dossier-01"
    );
    await expect(page.locator('[data-testid="audit-filter-action"]')).toHaveValue("coaf_regulatory_dossier_downloaded");
    await expect(page.locator('[data-testid="audit-filter-resource-type"]')).toHaveValue("ros_record");
    await expect(page.locator('[data-testid="audit-filter-resource-id"]')).toHaveValue(
      "99999999-9999-4999-8999-999999999999"
    );
    const dossierRow = page.locator('[data-testid="audit-row"]').first();
    await expect(dossierRow).toContainText(
      "Dossie regulatorio COAF exportado (coaf_regulatory_dossier_downloaded)"
    );
    await expect(page.getByTestId("audit-row-timestamp-audit-log-preset-01")).not.toContainText("2026-07-07T12:10:00.000Z");
    await dossierRow.click();
    await expect(page.getByTestId("audit-hash-context")).toContainText(`Hash principal do contexto: ${"b".repeat(64)}`);
    await expect(page.getByTestId("audit-hash-context")).toContainText(
      "Origem do hash exibido: dossie regulatorio"
    );
    await expect(page.getByTestId("audit-hash-context")).toContainText(
      "Tipo de artefato resolvido: artefato regulatorio consolidado"
    );
    await expect(page.getByTestId("audit-dossier-detail-context")).toContainText("Contexto regulatorio do dossie");
    await expect(page.getByTestId("audit-dossier-detail-context")).toContainText(
      "Arquivo do dossie: ontrackchain-ros-coaf-regulatory-dossier-99999999-9999-4999-8999-999999999999.json"
    );
    await expect(page.getByTestId("audit-dossier-detail-context")).toContainText(
      `Hash do dossie: ${"b".repeat(64)}`
    );
    await expect(page.getByTestId("audit-dossier-detail-open-report")).toHaveAttribute(
      "href",
      "/reports?history_report_id=rep-ros-dossier-01"
    );
    await expect(page.getByTestId("audit-dossier-detail-open-roscoaf")).toHaveAttribute(
      "href",
      "/ros-coaf?ros_id=99999999-9999-4999-8999-999999999999&report_id=rep-ros-dossier-01"
    );
  });

  test("ativa preset dedicado do pacote manual via query string", async ({ page }) => {
    await seedAuditPage(page);

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const url = new URL(route.request().url());
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-log-manual-preset-01",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_exported",
              resource_type: "audit_log",
              resource_id: "audit-log-manual-preset-01",
              request_id: "req-dd-preset-01",
              report_id: "rep-dd-preset-01",
              file_hash_sha256: null,
              metadata: {
                scope_id: "req-dd-preset-01",
                filename: "ontrackchain-manual-review-due-diligence-req-dd-preset-01.json",
                package_sha256: "e".repeat(64),
                manual_review_action: "compliance_due_diligence_checked",
                workspace_status: "sealed",
                case_id: "case-dd-preset-01"
              },
              created_at: "2026-07-07T12:20:00.000Z"
            },
            {
              id: "audit-log-manual-preset-02",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_signoff_recorded",
              resource_type: "evidence_package_seal",
              resource_id: "seal-preset-01",
              request_id: "req-dd-preset-01",
              report_id: "rep-dd-preset-01",
              file_hash_sha256: null,
              metadata: {
                seal_id: "seal-preset-01",
                scope_id: "req-dd-preset-01",
                package_sha256: "e".repeat(64),
                manual_review_action: "compliance_due_diligence_checked",
                signer_role: "compliance_owner",
                decision: "approved",
                seal_status: "pending_signoff"
              },
              created_at: "2026-07-07T12:21:00.000Z"
            },
            {
              id: "audit-log-manual-preset-03",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_sealed",
              resource_type: "evidence_package_seal",
              resource_id: "seal-preset-01",
              request_id: "req-dd-preset-01",
              report_id: "rep-dd-preset-01",
              file_hash_sha256: null,
              metadata: {
                seal_id: "seal-preset-01",
                scope_id: "req-dd-preset-01",
                package_sha256: "e".repeat(64),
                manual_review_action: "compliance_due_diligence_checked",
                seal_status: "sealed",
                signature_algorithm: "HS256",
                certificate_bundle_ref: "local-hs256-trust-bundle",
                verification_summary: {
                  verification_method: "local_hs256_self_check"
                }
              },
              created_at: "2026-07-07T12:22:00.000Z"
            }
          ].filter((row) => {
            const action = url.searchParams.get("action");
            const resourceType = url.searchParams.get("resource_type");
            const requestId = url.searchParams.get("request_id");
            return (!action || row.action === action) && (!resourceType || row.resource_type === resourceType) && (!requestId || row.request_id === requestId);
          }),
          page: 1,
          count: 1,
          limit: 50,
          total: 1,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.goto(
      "/audit?action=evidence_manual_review_package_exported&resource_type=audit_log&request_id=req-dd-preset-01&report_id=rep-dd-preset-01"
    );

    await expect(page.getByTestId("audit-manual-preset-notice")).toContainText(
      "Preset ativo: trilha auditada do pacote manual para request_id req-dd-preset-01."
    );
    await expect(page.getByTestId("audit-manual-preset-latest-context")).toContainText(
      "Ultimo artefato visivel neste recorte:"
    );
    await expect(page.getByTestId("audit-manual-preset-latest-context")).toContainText(
      "scope_id: req-dd-preset-01"
    );
    await expect(page.getByTestId("audit-manual-preset-latest-context")).toContainText(
      "acao manual: Due diligence verificada"
    );
    await expect(page.getByTestId("audit-manual-preset-latest-context")).toContainText(
      "etapa: Pacote manual regulatorio selado (evidence_manual_review_package_sealed)"
    );
    await expect(page.getByTestId("audit-manual-preset-latest-context")).toContainText(
      "report_id: rep-dd-preset-01"
    );
    await expect(page.getByTestId("audit-manual-preset-latest-context")).toContainText(
      "arquivo: ontrackchain-manual-review-due-diligence-req-dd-preset-01.json"
    );
    await expect(page.getByText("Eventos manuais")).toBeVisible();
    await expect(page.getByText("Exports manuais")).toBeVisible();
    await expect(page.getByText("Sign-offs")).toBeVisible();
    await expect(page.getByText("Selagens")).toBeVisible();
    await expect(page.getByText("Scopes unicos")).toBeVisible();
    await expect(page.getByText("Ultimo hash do pacote")).toBeVisible();
    await expect(page.getByText("Ultima etapa")).toBeVisible();
    await expect(page.getByText("Ultimo pacote")).toBeVisible();
    await expect(page.getByText("eeeeeeeeeeeeeeee...")).toBeVisible();
    await expect(page.getByTestId("audit-manual-open-evidence")).toHaveAttribute(
      "href",
      "/evidence?request_id=req-dd-preset-01&action=compliance_due_diligence_checked&resource_type=address&audit_origin=manual_package&domain=due_diligence&report_id=rep-dd-preset-01"
    );
    await expect(page.getByTestId("audit-manual-open-latest-report")).toHaveAttribute(
      "href",
      "/reports?history_report_id=rep-dd-preset-01"
    );
    await expect(page.locator('[data-testid="audit-filter-action"]')).toHaveValue("evidence_manual_review_package_exported");
    await expect(page.locator('[data-testid="audit-filter-resource-type"]')).toHaveValue("audit_log");
    await expect(page.locator('[data-testid="audit-filter-request-id"]')).toHaveValue("req-dd-preset-01");
    const manualPresetRow = page.locator('[data-testid="audit-row"]').first();
    await expect(manualPresetRow).toContainText(
      "Pacote manual regulatorio exportado (evidence_manual_review_package_exported)"
    );
    await expect(page.getByTestId("audit-row-timestamp-audit-log-manual-preset-01")).not.toContainText(
      "2026-07-07T12:20:00.000Z"
    );
  });

  test("ativa preset explicito de governanca pos-selagem via query string", async ({ page }) => {
    await seedAuditPage(page);

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const url = new URL(route.request().url());

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-log-governance-01",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_exported",
              resource_type: "audit_log",
              resource_id: "audit-log-governance-01",
              request_id: "req-dd-gov-01",
              report_id: "rep-dd-gov-01",
              file_hash_sha256: null,
              metadata: {
                scope_id: "req-dd-gov-01",
                filename: "ontrackchain-manual-review-due-diligence-req-dd-gov-01.json",
                package_sha256: "g".repeat(64),
                manual_review_action: "compliance_due_diligence_checked",
                workspace_status: "sealed",
                case_id: "case-dd-gov-01"
              },
              created_at: "2026-07-07T12:10:00.000Z"
            },
            {
              id: "audit-log-governance-02",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_signoff_recorded",
              resource_type: "evidence_package_seal",
              resource_id: "seal-gov-01",
              request_id: "req-dd-gov-01",
              report_id: "rep-dd-gov-01",
              file_hash_sha256: null,
              metadata: {
                seal_id: "seal-gov-01",
                scope_id: "req-dd-gov-01",
                package_sha256: "g".repeat(64),
                manual_review_action: "compliance_due_diligence_checked",
                signer_role: "compliance_owner",
                decision: "approved",
                seal_status: "pending_signoff"
              },
              created_at: "2026-07-07T12:11:00.000Z"
            },
            {
              id: "audit-log-governance-03",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_sealed",
              resource_type: "evidence_package_seal",
              resource_id: "seal-gov-01",
              request_id: "req-dd-gov-01",
              report_id: "rep-dd-gov-01",
              file_hash_sha256: null,
              metadata: {
                seal_id: "seal-gov-01",
                scope_id: "req-dd-gov-01",
                package_sha256: "g".repeat(64),
                manual_review_action: "compliance_due_diligence_checked",
                seal_status: "sealed",
                signature_algorithm: "HS256",
                certificate_bundle_ref: "local-hs256-trust-bundle",
                verification_summary: {
                  verification_method: "local_hs256_self_check"
                }
              },
              created_at: "2026-07-07T12:13:00.000Z"
            },
            {
              id: "audit-log-governance-04",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_seal_revoked",
              resource_type: "evidence_package_seal",
              resource_id: "seal-gov-01",
              request_id: "req-dd-gov-01",
              report_id: "rep-dd-gov-01",
              file_hash_sha256: null,
              metadata: {
                seal_id: "seal-gov-01",
                scope_id: "req-dd-gov-01",
                package_sha256: "g".repeat(64),
                manual_review_action: "compliance_due_diligence_checked",
                seal_status: "revoked",
                ticket_ref: "GOV-777",
                reason: "Falha de validacao detectada"
              },
              created_at: "2026-07-07T12:14:00.000Z"
            },
            {
              id: "audit-log-governance-05",
              user_id: "user-e2e",
              action: "evidence_manual_review_package_seal_superseded",
              resource_type: "evidence_package_seal",
              resource_id: "seal-gov-01",
              request_id: "req-dd-gov-01",
              report_id: "rep-dd-gov-01",
              file_hash_sha256: null,
              metadata: {
                seal_id: "seal-gov-01",
                scope_id: "req-dd-gov-01",
                package_sha256: "g".repeat(64),
                manual_review_action: "compliance_due_diligence_checked",
                seal_status: "superseded",
                ticket_ref: "GOV-888",
                reason: "Nova versão substituiu o pacote",
                superseded_by_seal_id: "seal-gov-02"
              },
              created_at: "2026-07-07T12:15:00.000Z"
            }
          ].filter((row) => {
            const requestId = url.searchParams.get("request_id");
            return !requestId || row.request_id === requestId;
          }),
          page: 1,
          count: 5,
          limit: 200,
          total: 5,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.goto("/audit?preset=governanca&request_id=req-dd-gov-01");

    await expect(page.getByTestId("audit-governance-preset-notice")).toContainText(
      "Preset ativo: governanca pos-selagem do pacote manual para request_id req-dd-gov-01."
    );
    await expect(page.getByTestId("audit-governance-open-evidence")).toHaveAttribute(
      "href",
      "/evidence?request_id=req-dd-gov-01&action=compliance_due_diligence_checked&resource_type=address&audit_origin=manual_package&domain=due_diligence&report_id=rep-dd-gov-01"
    );
    await expect(page.getByText("Revogacoes")).toBeVisible();
    await expect(page.getByText("Supersedencias")).toBeVisible();
    await expect(page.getByText("Export -> selagem")).toBeVisible();
    await expect(page.getByText("Selagem -> governanca")).toBeVisible();
    await expect(page.getByText("3 min")).toBeVisible();
    await expect(page.getByText("2 min")).toBeVisible();

    const governanceRow = page
      .locator('[data-testid="audit-row"]')
      .filter({ hasText: "Selo institucional do pacote supersedido (evidence_manual_review_package_seal_superseded)" })
      .first();
    await expect(governanceRow).toBeVisible();
  });

  test("resolve preset de governanca por seal_id e hidrata a familia completa do request", async ({ page }) => {
    await seedAuditPage(page);

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const url = new URL(route.request().url());
      const requestId = url.searchParams.get("request_id");
      const resourceType = url.searchParams.get("resource_type");
      const resourceId = url.searchParams.get("resource_id");

      if (resourceType === "evidence_package_seal" && resourceId === "seal-gov-resolve-01") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            data: [
              {
                id: "audit-log-governance-resolve-01",
                user_id: "user-e2e",
                action: "evidence_manual_review_package_seal_revoked",
                resource_type: "evidence_package_seal",
                resource_id: "seal-gov-resolve-01",
                request_id: "req-dd-gov-seal-01",
                report_id: "rep-dd-gov-seal-01",
                file_hash_sha256: null,
                metadata: {
                  seal_id: "seal-gov-resolve-01",
                  scope_id: "req-dd-gov-seal-01",
                  package_sha256: "h".repeat(64),
                  manual_review_action: "compliance_due_diligence_checked",
                  seal_status: "revoked",
                  ticket_ref: "GOV-991",
                  reason: "Revogacao usada apenas para resolver o contexto"
                },
                created_at: "2026-07-07T12:13:00.000Z"
              }
            ],
            page: 1,
            count: 1,
            limit: 200,
            total: 1,
            total_pages: 1,
            has_more: false
          })
        });
        return;
      }

      if (requestId === "req-dd-gov-seal-01") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            data: [
              {
                id: "audit-log-governance-family-01",
                user_id: "user-e2e",
                action: "evidence_manual_review_package_exported",
                resource_type: "audit_log",
                resource_id: "audit-log-governance-family-01",
                request_id: "req-dd-gov-seal-01",
                report_id: "rep-dd-gov-seal-01",
                file_hash_sha256: null,
                metadata: {
                  scope_id: "req-dd-gov-seal-01",
                  filename: "ontrackchain-manual-review-due-diligence-req-dd-gov-seal-01.json",
                  package_sha256: "h".repeat(64),
                  manual_review_action: "compliance_due_diligence_checked",
                  workspace_status: "sealed",
                  case_id: "case-dd-gov-seal-01"
                },
                created_at: "2026-07-07T12:10:00.000Z"
              },
              {
                id: "audit-log-governance-family-02",
                user_id: "user-e2e",
                action: "evidence_manual_review_package_signoff_recorded",
                resource_type: "evidence_package_seal",
                resource_id: "seal-gov-resolve-01",
                request_id: "req-dd-gov-seal-01",
                report_id: "rep-dd-gov-seal-01",
                file_hash_sha256: null,
                metadata: {
                  seal_id: "seal-gov-resolve-01",
                  scope_id: "req-dd-gov-seal-01",
                  package_sha256: "h".repeat(64),
                  manual_review_action: "compliance_due_diligence_checked",
                  signer_role: "ops_owner",
                  decision: "approved",
                  seal_status: "pending_signoff"
                },
                created_at: "2026-07-07T12:11:00.000Z"
              },
              {
                id: "audit-log-governance-family-03",
                user_id: "user-e2e",
                action: "evidence_manual_review_package_sealed",
                resource_type: "evidence_package_seal",
                resource_id: "seal-gov-resolve-01",
                request_id: "req-dd-gov-seal-01",
                report_id: "rep-dd-gov-seal-01",
                file_hash_sha256: null,
                metadata: {
                  seal_id: "seal-gov-resolve-01",
                  scope_id: "req-dd-gov-seal-01",
                  package_sha256: "h".repeat(64),
                  manual_review_action: "compliance_due_diligence_checked",
                  seal_status: "sealed",
                  signature_algorithm: "HS256",
                  certificate_bundle_ref: "local-hs256-trust-bundle",
                  verification_summary: {
                    verification_method: "local_hs256_self_check"
                  }
                },
                  created_at: "2026-07-07T12:13:00.000Z"
              },
              {
                id: "audit-log-governance-family-04",
                user_id: "user-e2e",
                action: "evidence_manual_review_package_seal_superseded",
                resource_type: "evidence_package_seal",
                resource_id: "seal-gov-resolve-01",
                request_id: "req-dd-gov-seal-01",
                report_id: "rep-dd-gov-seal-01",
                file_hash_sha256: null,
                metadata: {
                  seal_id: "seal-gov-resolve-01",
                  scope_id: "req-dd-gov-seal-01",
                  package_sha256: "h".repeat(64),
                  manual_review_action: "compliance_due_diligence_checked",
                  seal_status: "superseded",
                  ticket_ref: "GOV-992",
                  reason: "Nova versao aprovada",
                  superseded_by_seal_id: "seal-gov-resolve-02"
                },
                  created_at: "2026-07-07T12:17:00.000Z"
              }
            ],
            page: 1,
            count: 4,
            limit: 200,
            total: 4,
            total_pages: 1,
            has_more: false
          })
        });
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [],
          page: 1,
          count: 0,
          limit: 200,
          total: 0,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.goto("/audit?preset=governanca&seal_id=seal-gov-resolve-01");

    await expect(page.getByTestId("audit-governance-preset-notice")).toContainText(
      "Preset ativo: governanca pos-selagem do pacote manual para request_id req-dd-gov-seal-01."
    );
    await expect(page.getByTestId("audit-governance-open-evidence")).toHaveAttribute(
      "href",
      "/evidence?request_id=req-dd-gov-seal-01&action=compliance_due_diligence_checked&resource_type=address&audit_origin=manual_package&domain=due_diligence&report_id=rep-dd-gov-seal-01"
    );
    await expect(page.getByText("Supersedencias")).toBeVisible();
    await expect(page.getByText("Export -> selagem")).toBeVisible();
    await expect(page.getByText("Selagem -> governanca")).toBeVisible();
    await expect(page.getByText("4 min")).toBeVisible();
    await expect(
      page
        .locator('[data-testid="audit-row"]')
        .filter({ hasText: "Selo institucional do pacote supersedido (evidence_manual_review_package_seal_superseded)" })
        .first()
    ).toBeVisible();
  });

  test("agrupa violacoes MFA por familia e permite drill-down no preset dedicado", async ({ page }) => {
    await seedAuditPage(page);

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const url = new URL(route.request().url());
      const requestId = url.searchParams.get("request_id");
      const resourceId = url.searchParams.get("resource_id");
      const action = url.searchParams.get("action");

      const mfaRows: ManualPackageMfaAuditRow[] = [
        {
          id: "audit-log-mfa-01",
          user_id: "user-e2e",
          action: "evidence_manual_review_package_mfa_violation",
          resource_type: "evidence_package_seal",
          resource_id: "seal-mfa-01",
          request_id: "req-mfa-01",
          report_id: "rep-mfa-01",
          file_hash_sha256: null,
          metadata: {
            request_id: "req-mfa-01",
            report_id: "rep-mfa-01",
            seal_id: "seal-mfa-01",
            scope_id: "req-mfa-01",
            package_sha256: "m".repeat(64),
            manual_review_action: "compliance_due_diligence_checked",
            auth_role: "COMPLIANCE_OFFICER",
            asserted_signer_role: "compliance_owner",
            mfa_mode: "local_totp",
            two_factor_status: "pending",
            mfa_provider_homologated: true,
            detail: "2fa_required"
          },
          created_at: "2026-07-07T12:20:00.000Z"
        },
        {
          id: "audit-log-mfa-02",
          user_id: "user-e2e",
          action: "evidence_manual_review_package_mfa_violation",
          resource_type: "evidence_package_seal",
          resource_id: "seal-mfa-01",
          request_id: "req-mfa-01",
          report_id: "rep-mfa-01",
          file_hash_sha256: null,
          metadata: {
            request_id: "req-mfa-01",
            report_id: "rep-mfa-01",
            seal_id: "seal-mfa-01",
            scope_id: "req-mfa-01",
            package_sha256: "m".repeat(64),
            manual_review_action: "compliance_due_diligence_checked",
            auth_role: "COMPLIANCE_OFFICER",
            asserted_signer_role: "compliance_owner",
            mfa_mode: "external_provider",
            two_factor_status: "managed_externally",
            mfa_provider_homologated: false,
            detail: "mfa_not_homologated_for_oidc"
          },
          created_at: "2026-07-07T12:22:00.000Z"
        },
        {
          id: "audit-log-mfa-03",
          user_id: "user-e2e",
          action: "evidence_manual_review_package_mfa_violation",
          resource_type: "evidence_package_seal",
          resource_id: "seal-mfa-02",
          request_id: "req-mfa-02",
          report_id: "rep-mfa-02",
          file_hash_sha256: null,
          metadata: {
            request_id: "req-mfa-02",
            report_id: "rep-mfa-02",
            seal_id: "seal-mfa-02",
            scope_id: "req-mfa-02",
            package_sha256: "n".repeat(64),
            manual_review_action: "compliance_source_of_funds_checked",
            auth_role: "LEGAL_REVIEWER",
            asserted_signer_role: "legal_owner_optional",
            mfa_mode: "local_totp",
            two_factor_status: "pending",
            mfa_provider_homologated: true,
            detail: "2fa_required"
          },
        created_at: "2026-07-07T12:30:00.000Z"
        }
      ];
      const exportRows: ManualPackageMfaAuditRow[] = [
        {
          id: "audit-log-mfa-export-01",
          user_id: "user-e2e",
          action: "evidence_manual_review_package_exported",
          resource_type: "audit_log",
          resource_id: "audit-log-mfa-export-01",
          request_id: "req-mfa-01",
          report_id: "rep-mfa-01",
          file_hash_sha256: null,
          metadata: {
            request_id: "req-mfa-01",
            report_id: "rep-mfa-01",
            scope_id: "req-mfa-01",
            filename: "ontrackchain-manual-review-due-diligence-req-mfa-01.json",
            package_sha256: "m".repeat(64),
            manual_review_action: "compliance_due_diligence_checked",
            workspace_status: "sealed",
            case_id: "case-mfa-01"
          },
          created_at: "2026-07-07T12:10:00.000Z"
        },
        {
          id: "audit-log-mfa-export-02",
          user_id: "user-e2e",
          action: "evidence_manual_review_package_exported",
          resource_type: "audit_log",
          resource_id: "audit-log-mfa-export-02",
          request_id: "req-mfa-02",
          report_id: "rep-mfa-02",
          file_hash_sha256: null,
          metadata: {
            request_id: "req-mfa-02",
            report_id: "rep-mfa-02",
            scope_id: "req-mfa-02",
            filename: "ontrackchain-manual-review-source-of-funds-req-mfa-02.json",
            package_sha256: "n".repeat(64),
            manual_review_action: "compliance_source_of_funds_checked",
            workspace_status: "sealed",
            case_id: "case-mfa-02"
          },
          created_at: "2026-07-07T12:09:00.000Z"
        }
      ];

      let data: ManualPackageMfaAuditRow[] = mfaRows;
      if (requestId && !action) {
        data = [...exportRows, ...mfaRows.filter((row) => row.request_id === requestId)];
      } else if (requestId || resourceId) {
        data = mfaRows.filter((row) => {
          return (!requestId || row.request_id === requestId) && (!resourceId || row.resource_id === resourceId);
        });
      }

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data,
          page: 1,
          count: data.length,
          limit: 200,
          total: data.length,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.goto("/audit?preset=manual-package-mfa&action=evidence_manual_review_package_mfa_violation&resource_type=evidence_package_seal");

    await expect(page.getByTestId("audit-manual-mfa-preset-notice")).toContainText(
      "Preset ativo: violacoes MFA na selagem institucional de manual-package."
    );
    await expect(page.getByText("Violacoes MFA", { exact: true })).toBeVisible();
    await expect(page.getByText("Requests afetados", { exact: true })).toBeVisible();
    await expect(page.getByText("Selos afetados", { exact: true })).toBeVisible();
    await expect(page.locator(".otc-stat__label").filter({ hasText: "Provider nao homologado" }).first()).toBeVisible();
    await expect(page.getByText("Resumo por tipo de violacao", { exact: true })).toBeVisible();
    await expect(page.getByTestId("audit-manual-mfa-type-summary")).toContainText("2FA ausente");
    await expect(page.getByTestId("audit-manual-mfa-type-summary")).toContainText("Participacao: 67%");
    await expect(page.getByTestId("audit-manual-mfa-type-summary")).toContainText("Provider nao homologado");
    await expect(page.getByTestId("audit-manual-mfa-type-summary")).toContainText("Participacao: 33%");
    await expect(page.getByText("Resumo por papel", { exact: true })).toBeVisible();
    await expect(page.getByText("Papel autenticado", { exact: true })).toBeVisible();
    await expect(page.getByText("Signer role", { exact: true })).toBeVisible();
    await expect(page.getByText("Familias de violacao MFA", { exact: true })).toBeVisible();
    await expect(page.getByText("ordenado por recorrencia e criticidade operacional", { exact: false })).toBeVisible();
    await expect(page.locator('[data-testid="audit-manual-mfa-auth-role-row"]').first()).toContainText("COMPLIANCE_OFFICER");
    await expect(page.locator('[data-testid="audit-manual-mfa-auth-role-row"]').first()).toContainText("2");
    await expect(page.locator('[data-testid="audit-manual-mfa-signer-role-row"]').first()).toContainText(
      "Responsável de Compliance"
    );
    await expect(page.locator('[data-testid="audit-manual-mfa-signer-role-row"]').first()).toContainText("2");
    await expect(page.locator('[data-testid="audit-manual-mfa-family-row"]')).toHaveCount(2);

    const firstFamily = page.locator('[data-testid="audit-manual-mfa-family-row"]').first();
    await expect(firstFamily).toContainText("request_id: req-mfa-01");
    await expect(firstFamily).toContainText("seal_id: seal-mfa-01");
    await expect(firstFamily.getByTestId("audit-manual-mfa-family-dominant-pill")).toContainText("Provider nao homologado");
    await expect(firstFamily).toContainText("eventos: 2");
    await expect(firstFamily).toContainText("2FA ausente: 1");
    await expect(firstFamily).toContainText("provider nao homologado: 1");

    const familyOpenLink = firstFamily.getByTestId("audit-manual-mfa-family-open");
    await expect(familyOpenLink).toHaveAttribute(
      "href",
      "/audit?preset=manual-package-mfa&action=evidence_manual_review_package_mfa_violation&resource_type=evidence_package_seal&request_id=req-mfa-01&resource_id=seal-mfa-01"
    );

    await familyOpenLink.click();

    await expect(page).toHaveURL(
      /\/audit\?preset=manual-package-mfa&action=evidence_manual_review_package_mfa_violation&resource_type=evidence_package_seal&request_id=req-mfa-01&resource_id=seal-mfa-01/
    );
    await expect(page.getByTestId("audit-manual-mfa-open-all")).toHaveAttribute(
      "href",
      "/audit?preset=manual-package-mfa&action=evidence_manual_review_package_mfa_violation&resource_type=evidence_package_seal"
    );
    await expect(page.locator('[data-testid="audit-manual-mfa-family-row"]').first()).toContainText("Familia atual");

    await page.locator('[data-testid="audit-row"]').nth(1).click();

    const detail = page.getByTestId("audit-details-panel");
    await expect(detail).toContainText("Papel autenticado: COMPLIANCE_OFFICER");
    await expect(detail).toContainText("Modo MFA: external_provider");
    await expect(detail).toContainText("Status 2FA: managed_externally");
    await expect(detail).toContainText("Provider MFA homologado: false");
    await expect(detail).toContainText("Detalhe da violacao MFA: mfa_not_homologated_for_oidc");
  });

  test("monitoring navega para o preset MFA do audit e preserva o drill-down da familia", async ({ page }) => {
    await seedAuditPage(page, { role: "ADMIN" });

    const mfaRows: ManualPackageMfaAuditRow[] = [
      {
        id: "audit-log-monitoring-mfa-01",
        user_id: "user-e2e",
        action: "evidence_manual_review_package_mfa_violation",
        resource_type: "evidence_package_seal",
        resource_id: "seal-monitoring-mfa-01",
        request_id: "req-monitoring-mfa-01",
        report_id: "rep-monitoring-mfa-01",
        file_hash_sha256: null,
        metadata: {
          request_id: "req-monitoring-mfa-01",
          report_id: "rep-monitoring-mfa-01",
          seal_id: "seal-monitoring-mfa-01",
          scope_id: "req-monitoring-mfa-01",
          package_sha256: "p".repeat(64),
          manual_review_action: "compliance_due_diligence_checked",
          auth_role: "COMPLIANCE_OFFICER",
          asserted_signer_role: "compliance_owner",
          mfa_mode: "external_provider",
          two_factor_status: "managed_externally",
          mfa_provider_homologated: false,
          detail: "mfa_not_homologated_for_oidc"
        },
        created_at: "2026-07-07T12:22:00.000Z"
      }
    ];
    const exportRows: ManualPackageMfaAuditRow[] = [
      {
        id: "audit-log-monitoring-mfa-export-01",
        user_id: "user-e2e",
        action: "evidence_manual_review_package_exported",
        resource_type: "audit_log",
        resource_id: "audit-log-monitoring-mfa-export-01",
        request_id: "req-monitoring-mfa-01",
        report_id: "rep-monitoring-mfa-01",
        file_hash_sha256: null,
        metadata: {
          request_id: "req-monitoring-mfa-01",
          report_id: "rep-monitoring-mfa-01",
          scope_id: "req-monitoring-mfa-01",
          filename: "ontrackchain-manual-review-due-diligence-req-monitoring-mfa-01.json",
          package_sha256: "p".repeat(64),
          manual_review_action: "compliance_due_diligence_checked",
          workspace_status: "sealed",
          case_id: "case-monitoring-mfa-01"
        },
        created_at: "2026-07-07T12:10:00.000Z"
      }
    ];

    await page.route("**/api/app/monitoring/watchlists", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });
    await page.route("**/api/app/monitoring/alerts?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });
    await page.route("**/api/app/monitoring/operational-alert-filter-options", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          services: [],
          receivers: [],
          generated_at: "2026-07-07T12:00:00.000Z"
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
          total_count: 0,
          count: 0,
          has_more: false,
          next_cursor: null,
          data: []
        })
      });
    });
    await page.route("**/api/app/investigation/operations", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          queue: { ready: 0, waiting: 0, retry_pending: 0, retry_due: 0, wake_signals: 0 },
          concurrency: { org_active: 0, org_limit: 5, global_active: 0, global_limit: 10, plan: "professional" },
          throughput: { completed_last_hour: 0, failed_last_hour: 0, billing_recalc_last_hour: 0, avg_duration_ms_last_20: 0 },
          states: { queued: 0, processing: 0, dlq_failed: 0, dlq_resolved: 0 },
          recent_cases: [],
          security: {
            manual_package_mfa_violations_last_hour: 1,
            manual_package_mfa_2fa_required_last_hour: 0,
            manual_package_mfa_provider_not_homologated_last_hour: 1
          },
          generated_at: "2026-07-07T12:30:00.000Z"
        })
      });
    });
    await page.route("**/api/app/investigation/alerts", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          generated_at: "2026-07-07T12:30:00.000Z",
          open_total: 1,
          critical_open_total: 0,
          alerts: [
            {
              code: "investigation_manual_package_mfa_violations",
              severity: "warning",
              status: "open",
              metric: "security.manual_package_mfa_violations_last_hour",
              value: 1,
              threshold: 1,
              title: "Violacoes MFA em selagem manual",
              message: "Houve violacoes recentes de MFA no fluxo institucional de manual-package.",
              recommended_action: "Revisar a trilha de auditoria do selo e validar headers MFA/2FA no fluxo de signoff."
            }
          ]
        })
      });
    });
    await page.route("**/api/app/investigation/metrics", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "text/plain",
        body: "ontrack_investigation_platform_manual_package_mfa_violations_last_hour 1\n"
      });
    });
    await page.route("**/api/app/investigation/dlq?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          count: 0,
          credits_available: 0,
          filters: { state: "failed_permanent", target_chain: null, can_requeue: null, limit: 20 },
          cases: [],
          generated_at: "2026-07-07T12:30:00.000Z"
        })
      });
    });
    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const url = new URL(route.request().url());
      const requestId = url.searchParams.get("request_id");
      const resourceId = url.searchParams.get("resource_id");
      const action = url.searchParams.get("action");

      let data: ManualPackageMfaAuditRow[] = mfaRows;
      if (requestId && !action) {
        data = [...exportRows, ...mfaRows.filter((row) => row.request_id === requestId)];
      } else if (requestId || resourceId) {
        data = mfaRows.filter((row) => {
          return (!requestId || row.request_id === requestId) && (!resourceId || row.resource_id === resourceId);
        });
      }

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data,
          page: 1,
          count: data.length,
          limit: 200,
          total: data.length,
          total_pages: 1,
          has_more: false
        })
      });
    });
    await page.route("**/api/app/reports/rep-monitoring-mfa-01/ros-coaf-ref", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ report_id: "rep-monitoring-mfa-01", ros_id: null })
      });
    });

    await page.goto("/monitoring");

    const mfaCard = page.getByTestId("worker-metric-manual-package-mfa");
    await expect(mfaCard).toContainText("MFA manual-package 1h");
    await expect(mfaCard).toContainText("total 1");
    await expect(mfaCard).toContainText("provider não homologado 1");

    const openAuditLink = mfaCard.getByRole("link", { name: "Abrir audit" });
    await expect(openAuditLink).toHaveAttribute(
      "href",
      "/audit?preset=manual-package-mfa&action=evidence_manual_review_package_mfa_violation&resource_type=evidence_package_seal"
    );

    await Promise.all([
      page.waitForURL(
        /\/audit\?preset=manual-package-mfa&action=evidence_manual_review_package_mfa_violation&resource_type=evidence_package_seal/
      ),
      openAuditLink.click()
    ]);

    await expect(page.getByTestId("audit-manual-mfa-preset-notice")).toContainText(
      "Preset ativo: violacoes MFA na selagem institucional de manual-package."
    );
    await expect(page.getByTestId("audit-manual-mfa-type-summary")).toContainText("Provider nao homologado");
    await expect(page.getByTestId("audit-manual-mfa-type-summary")).toContainText("Participacao: 100%");
    await expect(page.getByTestId("audit-manual-mfa-role-summary")).toContainText("COMPLIANCE_OFFICER");
    await expect(page.getByTestId("audit-manual-mfa-role-summary")).toContainText("Responsável de Compliance");
    await expect(page.locator('[data-testid="audit-manual-mfa-family-row"]').first().getByTestId("audit-manual-mfa-family-dominant-pill")).toContainText(
      "Provider nao homologado"
    );

    const familyOpenLink = page.getByTestId("audit-manual-mfa-family-open");
    await expect(familyOpenLink).toHaveAttribute(
      "href",
      "/audit?preset=manual-package-mfa&action=evidence_manual_review_package_mfa_violation&resource_type=evidence_package_seal&request_id=req-monitoring-mfa-01&resource_id=seal-monitoring-mfa-01"
    );

    await Promise.all([
      page.waitForURL(
        /\/audit\?preset=manual-package-mfa&action=evidence_manual_review_package_mfa_violation&resource_type=evidence_package_seal&request_id=req-monitoring-mfa-01&resource_id=seal-monitoring-mfa-01/
      ),
      familyOpenLink.click()
    ]);

    await expect(page.getByTestId("audit-manual-mfa-open-all")).toHaveAttribute(
      "href",
      "/audit?preset=manual-package-mfa&action=evidence_manual_review_package_mfa_violation&resource_type=evidence_package_seal"
    );
    await expect(page.locator('[data-testid="audit-manual-mfa-family-row"]').first()).toContainText("Familia atual");
    await expect(page.getByTestId("audit-details-panel")).toContainText("Detalhe da violacao MFA: mfa_not_homologated_for_oidc");
  });

  test("desempata familias MFA por criticidade quando o volume e igual", async ({ page }) => {
    await seedAuditPage(page);

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const mfaRows: ManualPackageMfaAuditRow[] = [
        {
          id: "audit-log-mfa-tie-01",
          user_id: "user-e2e",
          action: "evidence_manual_review_package_mfa_violation",
          resource_type: "evidence_package_seal",
          resource_id: "seal-mfa-tie-01",
          request_id: "req-mfa-tie-01",
          report_id: "rep-mfa-tie-01",
          file_hash_sha256: null,
          metadata: {
            request_id: "req-mfa-tie-01",
            report_id: "rep-mfa-tie-01",
            seal_id: "seal-mfa-tie-01",
            auth_role: "COMPLIANCE_OFFICER",
            asserted_signer_role: "compliance_owner",
            mfa_mode: "external_provider",
            mfa_provider_homologated: false,
            detail: "mfa_not_homologated_for_oidc"
          },
          created_at: "2026-07-07T12:10:00.000Z"
        },
        {
          id: "audit-log-mfa-tie-02",
          user_id: "user-e2e",
          action: "evidence_manual_review_package_mfa_violation",
          resource_type: "evidence_package_seal",
          resource_id: "seal-mfa-tie-01",
          request_id: "req-mfa-tie-01",
          report_id: "rep-mfa-tie-01",
          file_hash_sha256: null,
          metadata: {
            request_id: "req-mfa-tie-01",
            report_id: "rep-mfa-tie-01",
            seal_id: "seal-mfa-tie-01",
            auth_role: "COMPLIANCE_OFFICER",
            asserted_signer_role: "compliance_owner",
            mfa_mode: "local_totp",
            two_factor_status: "pending",
            detail: "2fa_required"
          },
          created_at: "2026-07-07T12:11:00.000Z"
        },
        {
          id: "audit-log-mfa-tie-03",
          user_id: "user-e2e",
          action: "evidence_manual_review_package_mfa_violation",
          resource_type: "evidence_package_seal",
          resource_id: "seal-mfa-tie-02",
          request_id: "req-mfa-tie-02",
          report_id: "rep-mfa-tie-02",
          file_hash_sha256: null,
          metadata: {
            request_id: "req-mfa-tie-02",
            report_id: "rep-mfa-tie-02",
            seal_id: "seal-mfa-tie-02",
            auth_role: "LEGAL_REVIEWER",
            asserted_signer_role: "legal_owner_optional",
            mfa_mode: "local_totp",
            two_factor_status: "pending",
            detail: "2fa_required"
          },
          created_at: "2026-07-07T12:20:00.000Z"
        },
        {
          id: "audit-log-mfa-tie-04",
          user_id: "user-e2e",
          action: "evidence_manual_review_package_mfa_violation",
          resource_type: "evidence_package_seal",
          resource_id: "seal-mfa-tie-02",
          request_id: "req-mfa-tie-02",
          report_id: "rep-mfa-tie-02",
          file_hash_sha256: null,
          metadata: {
            request_id: "req-mfa-tie-02",
            report_id: "rep-mfa-tie-02",
            seal_id: "seal-mfa-tie-02",
            auth_role: "LEGAL_REVIEWER",
            asserted_signer_role: "legal_owner_optional",
            mfa_mode: "local_totp",
            two_factor_status: "pending",
            detail: "2fa_required"
          },
          created_at: "2026-07-07T12:21:00.000Z"
        }
      ];

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: mfaRows,
          page: 1,
          count: mfaRows.length,
          limit: 200,
          total: mfaRows.length,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.goto("/audit?preset=manual-package-mfa&action=evidence_manual_review_package_mfa_violation&resource_type=evidence_package_seal");

    const families = page.locator('[data-testid="audit-manual-mfa-family-row"]');
    await expect(families).toHaveCount(2);

    const firstFamily = families.first();
    await expect(firstFamily).toContainText("request_id: req-mfa-tie-01");
    await expect(firstFamily).toContainText("eventos: 2");
    await expect(firstFamily.getByTestId("audit-manual-mfa-family-dominant-pill")).toContainText("Provider nao homologado");

    const secondFamily = families.nth(1);
    await expect(secondFamily).toContainText("request_id: req-mfa-tie-02");
    await expect(secondFamily).toContainText("eventos: 2");
    await expect(secondFamily.getByTestId("audit-manual-mfa-family-dominant-pill")).toContainText("2FA ausente");
  });

  test("classifica familia MFA residual como outros tipos", async ({ page }) => {
    await seedAuditPage(page);

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      const rows: ManualPackageMfaAuditRow[] = [
        {
          id: "audit-log-mfa-residual-01",
          user_id: "user-e2e",
          action: "evidence_manual_review_package_mfa_violation",
          resource_type: "evidence_package_seal",
          resource_id: "seal-mfa-residual-01",
          request_id: "req-mfa-residual-01",
          report_id: "rep-mfa-residual-01",
          file_hash_sha256: null,
          metadata: {
            request_id: "req-mfa-residual-01",
            report_id: "rep-mfa-residual-01",
            seal_id: "seal-mfa-residual-01",
            auth_role: "COMPLIANCE_OFFICER",
            asserted_signer_role: "compliance_owner",
            mfa_mode: "external_provider",
            detail: "mfa_evidence_missing"
          },
          created_at: "2026-07-07T12:40:00.000Z"
        }
      ];

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: rows,
          page: 1,
          count: rows.length,
          limit: 200,
          total: rows.length,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.goto("/audit?preset=manual-package-mfa&action=evidence_manual_review_package_mfa_violation&resource_type=evidence_package_seal");

    await expect(page.getByTestId("audit-manual-mfa-type-summary")).toContainText("Outros tipos");
    await expect(page.getByTestId("audit-manual-mfa-type-summary")).toContainText("Participacao: 100%");

    const family = page.locator('[data-testid="audit-manual-mfa-family-row"]').first();
    await expect(family).toContainText("request_id: req-mfa-residual-01");
    await expect(family).toContainText("eventos: 1");
    await expect(family.getByTestId("audit-manual-mfa-family-dominant-pill")).toContainText("Outros tipos");
    await expect(family).toContainText("ultimo detalhe: mfa_evidence_missing");
  });

  test("exporta dossie regulatorio ROS/COAF quando o ros_id e resolvido via report_id", async ({ page }) => {
    await seedAuditPage(page);

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-log-ros-01",
              user_id: "user-e2e",
              action: "report_generated",
              resource_type: "report",
              resource_id: "rep-audit-ros-01",
              request_id: "req-audit-ros-01",
              report_id: "rep-audit-ros-01",
              file_hash_sha256: "a".repeat(64),
              metadata: {
                case_id: "case-audit-ros-01",
                request_id: "req-audit-ros-01",
                report_id: "rep-audit-ros-01"
              },
              created_at: "2026-07-07T12:00:00.000Z"
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

    await page.route("**/api/app/reports/rep-audit-ros-01/ros-coaf-ref", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          report_id: "rep-audit-ros-01",
          ros_id: "99999999-9999-4999-8999-999999999999"
        })
      });
    });

    await page.route("**/api/app/reports/ros-coaf/*/regulatory-dossier", async (route: Route) => {
      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "content-disposition": 'attachment; filename="ontrackchain-ros-coaf-regulatory-dossier-99999999-9999-4999-8999-999999999999.json"',
          "x-ontrack-dossier-sha256": "c".repeat(64)
        },
        body: JSON.stringify({
          version: "v1",
          generated_at: "2026-07-07T12:05:00.000Z",
          dossier_sha256: "c".repeat(64),
          ros_record: { ros_id: "99999999-9999-4999-8999-999999999999", audit: [] },
          work_item: null,
          work_events: [],
          work_comments: [],
          unified_timeline: []
        })
      });
    });

    await page.goto("/audit");

    const filteredRow = page.locator('[data-testid="audit-row"]').first();
    await filteredRow.click();

    await expect(page.locator('[data-testid="audit-details-panel"]')).toContainText("rep-audit-ros-01");
    await expect(page.getByTestId("audit-export-ros-dossier")).toBeVisible();

    await expectDownloadLikeResponse(
      page,
      {
        urlPart: "/api/app/reports/ros-coaf/",
        expectedFilename: "ontrackchain-ros-coaf-regulatory-dossier-99999999-9999-4999-8999-999999999999.json"
      },
      async () => {
        await page.getByTestId("audit-export-ros-dossier").click();
      }
    );
  });

  test("preserva a negacao semantica ao resolver a referencia ROS/COAF do evento auditavel", async ({ page }) => {
    await seedAuditPage(page);

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-ros-dossier-03",
              organization_id: "org-e2e",
              request_id: "req-audit-ros-03",
              action: "report_generated",
              resource_type: "report",
              resource_id: "rep-audit-ros-03",
              report_id: "rep-audit-ros-03",
              actor_user_id: "user-e2e",
              created_at: "2026-07-07T12:00:00.000Z",
              metadata: {
                report_id: "rep-audit-ros-03",
                request_id: "req-audit-ros-03"
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

    await page.route("**/api/app/reports/rep-audit-ros-03/ros-coaf-ref", async (route: Route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "report_read_role_required" })
      });
    });

    await page.goto("/audit");
    await page.locator('[data-testid="audit-row"]').first().click();

    await expect(page.getByTestId("audit-linked-ros-message")).toContainText(
      "A leitura/listagem de relatórios exige papel operacional: ADMIN, AUDITOR, ANALYST ou VIEWER."
    );
    await expect(page.getByTestId("audit-export-ros-dossier")).toHaveCount(0);
  });

  test("bloqueia export do dossie ROS/COAF na auditoria quando falta linked_user_id persistido", async ({ page }) => {
    await seedAuditPage(page);

    await page.unroute("**/api/app/auth/context");
    await page.route("**/api/app/auth/context", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: null,
          role: "AUDITOR",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/audit/logs?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "audit-ros-dossier-02",
              organization_id: "org-e2e",
              request_id: "req-audit-ros-02",
              action: "coaf_regulatory_dossier_downloaded",
              resource_type: "ros_record",
              resource_id: "99999999-9999-4999-8999-999999999999",
              report_id: "rep-audit-ros-02",
              actor_user_id: "user-e2e",
              created_at: "2026-07-07T12:00:00.000Z",
              metadata: {
                filename: "ontrackchain-ros-coaf-regulatory-dossier-99999999-9999-4999-8999-999999999999.json",
                dossier_sha256: "d".repeat(64),
                report_id: "rep-audit-ros-02",
                ros_id: "99999999-9999-4999-8999-999999999999"
              }
            }
          ],
          page: 1,
          limit: 50,
          total: 1,
          total_pages: 1,
          has_more: false
        })
      });
    });

    await page.route("**/api/app/reports/rep-audit-ros-02/ros-coaf-ref", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          report_id: "rep-audit-ros-02",
          ros_id: "99999999-9999-4999-8999-999999999999"
        })
      });
    });

    await page.goto("/audit");
    await page.locator('[data-testid="audit-row"]').first().click();

    await expect(page.getByTestId("audit-export-ros-dossier")).toBeDisabled();
    await expect(page.getByTestId("audit-export-ros-dossier-prereq-block")).toContainText(
      "ROS/COAF exige um usuário federado vinculado ao tenant atual."
    );
  });
});

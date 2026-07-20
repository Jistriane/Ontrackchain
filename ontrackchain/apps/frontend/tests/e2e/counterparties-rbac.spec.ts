import { expect, test, type Page, type Route } from "@playwright/test";

const COUNTERPARTY_ID = "22222222-2222-4222-8222-222222222222";

type CounterpartySeedOptions = {
  denyHistory?: boolean;
  denyWorkspace?: boolean;
};

async function seedCounterpartiesPage(page: Page, role: string, options: CounterpartySeedOptions = {}) {
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
        role,
        plan: "professional",
        auth_method: "jwt",
        mfa_mode: "totp",
        mfa_provider_homologated: "true"
      })
    });
  });

  await page.route("**/api/app/compliance/counterparties?**", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            id: COUNTERPARTY_ID,
            legal_name: "Counterparty QA",
            counterparty_type: "individual",
            document_type: "cpf",
            document_number: "12345678900",
            risk_level: 3,
            kyc_status: "PENDING",
            sanctions_cleared: false,
            is_pep: false,
            enhanced_dd_required: true,
            next_review_date: "2026-08-01T00:00:00Z",
            status: "UNDER_REVIEW",
            created_at: "2026-07-14T12:00:00Z",
            dd_review_status: "pending",
            dd_review_note: "",
            sof_description: "",
            sof_document_ref: "",
            last_reviewed_at: null
          }
        ],
        total: 1
      })
    });
  });

  await page.route("**/api/app/operations/work-items?**", async (route: Route) => {
    if (options.denyWorkspace) {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "not_authenticated" })
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        data: [
          {
            id: "ws-counterparty-rbac-01",
            module: "counterparties",
            resource_type: "counterparty",
            resource_id: COUNTERPARTY_ID,
            queue_status: "UNDER_REVIEW",
            priority: "high",
            due_at: "2026-07-20T18:00:00.000Z",
            note: "seed",
            owner_user_id: null,
            case_id: "33333333-3333-4333-8333-333333333333",
            metadata: {
              counterparty_id: COUNTERPARTY_ID,
              legal_name: "Counterparty QA",
              counterparty_type: "individual",
              document_type: "cpf",
              document_number: "12345678900",
              wallet_chain: "ethereum",
              wallet_address: "",
              wallet_label: "",
              risk_level: 3,
              kyc_status: "PENDING",
              sanctions_cleared: false,
              is_pep: false,
              enhanced_dd_required: true,
              next_review_date: "2026-08-01T00:00:00Z",
              status: "UNDER_REVIEW",
              created_at: "2026-07-14T12:00:00Z",
              dd_review_status: "pending",
              dd_review_note: "",
              sof_description: "",
              sof_document_ref: "",
              local_workspace_status: "UNDER_REVIEW"
            },
            last_activity_at: "2026-07-14T12:00:00.000Z",
            updated_at: "2026-07-14T12:00:00.000Z"
          }
        ]
      })
    });
  });

  await page.route(`**/api/app/compliance/counterparties/${COUNTERPARTY_ID}`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        counterparty_id: COUNTERPARTY_ID,
        legal_name: "Counterparty QA",
        counterparty_type: "individual",
        document_type: "cpf",
        document_number: "12345678900",
        document_country: "BRA",
        registration_data: {},
        beneficial_owners: [],
        wallet_addresses: [],
        risk_level: 3,
        risk_rationale: "High-risk corridor under enhanced due diligence.",
        onchain_risk_score: 77,
        onchain_analysis: {},
        is_pep: false,
        pep_detail: {},
        sanctions_cleared: false,
        sanctions_hits: [],
        kyc_status: "PENDING",
        enhanced_dd_required: true,
        next_review_date: "2026-08-01T00:00:00Z",
        status: "UNDER_REVIEW",
        created_at: "2026-07-14T12:00:00Z",
        review_snapshot: {
          dd_review_status: "pending",
          dd_review_note: "",
          sof_description: "",
          sof_document_ref: "",
          last_reviewed_at: null
        }
      })
    });
  });

  await page.route(`**/api/app/compliance/counterparties/${COUNTERPARTY_ID}/history?**`, async (route: Route) => {
    if (options.denyHistory) {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "counterparty_review_role_required" })
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            id: "history-counterparty-1",
            counterparty_id: COUNTERPARTY_ID,
            changed_by_user_id: "reviewer-user-1",
            change_type: "DD_REVIEW_UPDATED",
            field_changed: "enhanced_dd_status",
            old_value: "pending",
            new_value: "completed",
            change_reason: "Documentacao validada.",
            changed_at: "2026-07-15T11:00:00Z",
            evidence_hash: "hash-counterparty-1"
          }
        ],
        total: 1,
        limit: 20,
        offset: 0
      })
    });
  });
}

test.describe("counterparties RBAC", () => {
  test("viewer nao recebe formulario de onboarding regulado", async ({ page }) => {
    await seedCounterpartiesPage(page, "VIEWER");
    await page.goto("/counterparties");

    await expect(page.locator('aside a[href="/counterparties"]')).toHaveCount(0);
    await expect(page.getByTestId("create-counterparty-btn")).toHaveCount(0);
    await expect(page.getByTestId("counterparties-list-read-restricted")).toContainText(
      "A carteira operacional de contrapartes está oculta nesta sessão porque o papel atual não possui leitura operacional regulatória."
    );
    await expect(page.getByTestId("counterparties-workspace-read-restricted")).toContainText(
      "O workspace operacional de contrapartes está oculto nesta sessão porque o papel atual não possui leitura operacional regulatória."
    );
    await expect(page.getByTestId(`counterparties-workspace-row-${COUNTERPARTY_ID}`)).toHaveCount(0);
    await expect(
      page.getByText("O onboarding de contraparte está oculto nesta sessão porque o papel atual não possui autorização operacional de compliance.")
    ).toBeVisible();
  });

  test("analyst mantém acesso ao cockpit e ao menu lateral de contrapartes", async ({ page }) => {
    await seedCounterpartiesPage(page, "ANALYST");
    await page.goto("/counterparties");

    await expect(page.locator('aside a[href="/counterparties"]')).toHaveCount(1);
    await expect(page.getByTestId("create-counterparty-btn")).toBeVisible();
    await expect(page.getByTestId(`counterparties-workspace-row-${COUNTERPARTY_ID}`)).toBeVisible();
  });

  test("analyst nao recebe painel formal de DD review", async ({ page }) => {
    await seedCounterpartiesPage(page, "ANALYST");
    await page.goto("/counterparties");

    await expect(page.getByTestId(`counterparties-workspace-row-${COUNTERPARTY_ID}`)).toContainText("Counterparty QA");
    await expect(page.getByTestId("create-counterparty-btn")).toBeVisible();
    await expect(page.getByTestId("counterparty-dd-review-panel")).toHaveCount(0);
    await expect(
      page.getByText("A revisão formal DD/SoF está oculta nesta sessão porque o papel atual não possui autorização regulatória.")
    ).toBeVisible();
  });

  test("analyst recebe dossie oficial, mas o historico formal degrada com negacao semantica", async ({ page }) => {
    await seedCounterpartiesPage(page, "ANALYST", { denyHistory: true });
    await page.goto("/counterparties");

    await expect(page.getByTestId("counterparty-official-detail-panel")).toBeVisible();
    await expect(page.getByTestId("counterparty-official-detail-legal-name")).toContainText("Counterparty QA");
    await expect(page.getByTestId("counterparty-official-history-message")).toContainText(
      "A revisão formal de contraparte exige papel regulatório: ADMIN, COMPLIANCE_OFFICER ou REVIEWER."
    );
  });

  test("reviewer preserva dossie oficial quando o workspace compartilhado falha semanticamente", async ({ page }) => {
    await seedCounterpartiesPage(page, "REVIEWER", { denyWorkspace: true });
    await page.goto("/counterparties");

    await expect(page.getByTestId("counterparty-official-detail-panel")).toBeVisible();
    await expect(page.getByTestId("counterparty-official-detail-legal-name")).toContainText("Counterparty QA");
    await expect(page.getByTestId("counterparty-official-history-panel")).toContainText("DD_REVIEW_UPDATED");
    await expect(page.getByTestId("counterparties-workspace-message")).toContainText(
      "Sua sessão expirou ou não foi autenticada."
    );
    await expect(page.getByText("Nenhuma contraparte foi registrada ainda no workspace compartilhado.")).toHaveCount(0);
  });

  test("reviewer recebe painel formal de DD review", async ({ page }) => {
    await seedCounterpartiesPage(page, "REVIEWER");
    await page.goto("/counterparties");

    await expect(page.getByTestId(`counterparties-workspace-row-${COUNTERPARTY_ID}`)).toContainText("Counterparty QA");
    await expect(page.getByTestId("counterparty-dd-review-panel")).toBeVisible();
    await expect(page.getByTestId("counterparty-dd-review-panel")).toContainText("Status da revisão DD");
    await expect(page.getByTestId("counterparty-official-detail-panel")).toBeVisible();
    await expect(page.getByTestId("counterparty-official-history-panel")).toContainText("DD_REVIEW_UPDATED");
  });

  test("alias OTK_REVIEWER mantém o painel formal de DD review", async ({ page }) => {
    await seedCounterpartiesPage(page, "OTK_REVIEWER");
    await page.goto("/counterparties");

    await expect(page.getByTestId(`counterparties-workspace-row-${COUNTERPARTY_ID}`)).toContainText("Counterparty QA");
    await expect(page.getByTestId("counterparty-dd-review-panel")).toBeVisible();
    await expect(page.getByTestId("counterparty-dd-review-panel")).toContainText("Status da revisão DD");
  });

  test("alias OTK_COMPLIANCE_OFFICER mantém o painel formal de DD review", async ({ page }) => {
    await seedCounterpartiesPage(page, "OTK_COMPLIANCE_OFFICER");
    await page.goto("/counterparties");

    await expect(page.locator('aside a[href="/counterparties"]')).toHaveCount(1);
    await expect(page.getByTestId("create-counterparty-btn")).toBeVisible();
    await expect(page.getByTestId(`counterparties-workspace-row-${COUNTERPARTY_ID}`)).toContainText("Counterparty QA");
    await expect(page.getByTestId("counterparty-dd-review-panel")).toBeVisible();
    await expect(page.getByTestId("counterparty-dd-review-panel")).toContainText("Status da revisão DD");
  });
});

import { expect, test, type Page, type Route } from "@playwright/test";

const COUNTERPARTY_ID = "22222222-2222-4222-8222-222222222222";

async function seedCounterpartiesPage(page: Page, role: string) {
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

  test("reviewer recebe painel formal de DD review", async ({ page }) => {
    await seedCounterpartiesPage(page, "REVIEWER");
    await page.goto("/counterparties");

    await expect(page.getByTestId(`counterparties-workspace-row-${COUNTERPARTY_ID}`)).toContainText("Counterparty QA");
    await expect(page.getByTestId("counterparty-dd-review-panel")).toBeVisible();
    await expect(page.getByTestId("counterparty-dd-review-panel")).toContainText("Status da revisão DD");
  });
});

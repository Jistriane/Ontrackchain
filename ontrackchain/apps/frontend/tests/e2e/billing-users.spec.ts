import { expect, test, type Page, type Route } from "@playwright/test";

async function seedFrontendAuth(page: Page) {
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
}

test.describe("billing users table", () => {
  test("mantem o cockpit financeiro sem projetar roster lateral de team", async ({ page }) => {
    let teamUsersCalled = false;
    await seedFrontendAuth(page);

    await page.route("**/api/app/billing/balance", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          credits_available: 1000,
          credits_reserved: 12,
          credits_used_total: 345
        })
      });
    });

    await page.route("**/api/app/billing/reconciliation?limit=5", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          generated_at: "2026-07-06T12:16:00.000Z",
          balance: {
            credits_available: 1000,
            credits_reserved: 12,
            credits_used_total: 345
          },
          quotes: {
            investigation: { open_total: 2, expired_total: 1 },
            compliance: { open_total: 1, expired_total: 0 },
            monitoring: { open_total: 3, expired_total: 2 },
            open_total: 6,
            expired_total: 3
          },
          ledger: {
            total_entries: 3,
            action_totals: [
              { action: "CONFIRMED", entry_count: 2, amount_total: 7.5 },
              { action: "PRE_HOLD", entry_count: 1, amount_total: 3.0 }
            ],
            recent: [
              {
                id: "ledger-1",
                case_id: "case-1",
                action: "CONFIRMED",
                amount: 4.5,
                balance_after: 120,
                request_id: "req-1",
                quote_id: "quote-1",
                metadata: {},
                created_at: "2026-07-06T12:14:00.000Z"
              }
            ]
          }
        })
      });
    });

    await page.route("**/api/app/billing/reconciliation/export?limit=25", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        headers: {
          "content-disposition": 'attachment; filename="billing-export.json"'
        },
        body: JSON.stringify({ exported: true })
      });
    });

    await page.route("**/api/app/auth/context", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "BILLING_ADMIN",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/team/users", async (route: Route) => {
      teamUsersCalled = true;
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "unexpected_team_users_fetch" })
      });
    });

    await page.route("**/api/app/investigation/operations", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          concurrency: {
            org_active: 1,
            org_limit: 5,
            global_active: 2,
            global_limit: 10,
            plan: "professional"
          },
          generated_at: "2026-07-06T12:15:00.000Z"
        })
      });
    });

    await page.goto("/billing");

    await expect(page.locator('aside a[href="/billing"]')).toHaveCount(1);
    await expect(page.getByText("Gestão de equipe")).toBeVisible();
    await expect(
      page.getByText(
        "O cockpit financeiro não projeta mais o roster real do tenant. Use `Team` para onboarding, status, identidades federadas e operações administrativas de membros."
      )
    ).toBeVisible();
    await expect(page.getByTestId("billing-reconciliation-open-total")).toHaveText("6");
    await expect(page.getByTestId("billing-ledger-action-CONFIRMED")).toContainText("7.5");
    await expect(page.getByTestId("billing-ledger-row-ledger-1")).toContainText("req-1");
    await expect(page.getByTestId("billing-export-link")).toHaveAttribute("href", "/api/app/billing/reconciliation/export?limit=25");
    await expect(page.getByTestId("billing-open-team-action")).toBeVisible();
    await expect(page.getByTestId("billing-team-handoff-link")).toBeVisible();
    await expect(page.locator('a[href="/team?filter_status=invited"]')).toBeVisible();
    expect(teamUsersCalled).toBeFalsy();
    await expect(page.getByTestId("billing-user-row-billing-member-e2e-01")).toHaveCount(0);
  });

  test("exibe erro amigavel quando billing exige role financeira", async ({ page }) => {
    await seedFrontendAuth(page);

    await page.route("**/api/app/billing/balance", async (route: Route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "billing_balance_role_required" })
      });
    });

    await page.route("**/api/app/billing/reconciliation?limit=5", async (route: Route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "billing_reconciliation_role_required" })
      });
    });

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

    await page.route("**/api/app/investigation/operations", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          concurrency: {
            org_active: 1,
            org_limit: 5,
            global_active: 2,
            global_limit: 10,
            plan: "professional"
          },
          generated_at: "2026-07-06T12:15:00.000Z"
        })
      });
    });

    await page.goto("/billing");

    await expect(page.locator('aside a[href="/billing"]')).toHaveCount(0);
    await expect(page.getByTestId("billing-access-denied")).toContainText(
      "A leitura de billing exige papel financeiro: ADMIN ou BILLING_ADMIN."
    );
    await expect(page.getByTestId("credits-balance")).toHaveCount(0);
    await expect(page.getByTestId("billing-reconciliation-open-total")).toHaveCount(0);
    await expect(page.getByTestId("billing-export-link")).toHaveCount(0);
    await expect(page.getByTestId("billing-user-row-billing-member-e2e-01")).toHaveCount(0);
  });
});

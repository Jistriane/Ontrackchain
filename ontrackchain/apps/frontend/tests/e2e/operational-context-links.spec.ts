import { expect, test, type Page, type Route } from "@playwright/test";

type BlockEvaluationPayload = {
  address?: string;
  chain?: string;
};

function isJsonObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readOptionalString(value: unknown) {
  return typeof value === "string" ? value : undefined;
}

function parseBlockEvaluationPayload(route: Route): BlockEvaluationPayload {
  const payload = route.request().postDataJSON() as unknown;
  if (!isJsonObject(payload)) {
    return {};
  }

  return {
    address: readOptionalString(payload.address),
    chain: readOptionalString(payload.chain)
  };
}

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
}

test.describe("operational context links", () => {
  test("sanctions deriva links contextuais no workspace e no resultado", async ({ page }: { page: Page }) => {
    const workspaceCaseId = "11111111-1111-4111-8111-111111111111";
    const resultCaseId = "22222222-2222-4222-8222-222222222222";
    const address = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    await seedFrontendAuth(page);

    await page.route("**/api/app/operations/work-items?module=sanctions**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "work-sanctions-01",
              case_id: workspaceCaseId,
              resource_id: "sanctions-screening-01",
              owner_user_id: "linked-sanctions-owner",
              queue_status: "UNDER_REVIEW",
              priority: "high",
              due_at: "2026-07-06T14:00:00.000Z",
              note: "triagem workspace",
              metadata: {
                workspace_id: "sanctions-ws-01",
                address,
                chain: "ethereum",
                lists: ["ofac"],
                owner_label: "Compliance QA",
                provider: "chainalysis",
                provider_status: "live",
                capability_status: "live",
                matched_lists: ["ofac"],
                hit: true,
                entity_name: "Counterparty WS",
                designation_date: "2026-07-05T10:00:00.000Z",
                checked_at: "2026-07-05T10:05:00.000Z",
                triage_note: "triagem workspace"
              },
              last_activity_at: "2026-07-05T10:10:00.000Z",
              updated_at: "2026-07-05T10:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/compliance/sanctions-check?**", async (route: Route) => {
      const url = new URL(route.request().url());
      expect(url.searchParams.get("address")).toBe(address);
      expect(url.searchParams.get("chain")).toBe("ethereum");

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          address,
          chain: "ethereum",
          provider: "chainalysis",
          provider_status: "live",
          degraded_reason: null,
          capability_status: "live",
          lists: ["ofac"],
          hit: true,
          matched_lists: ["ofac"],
          entity_name: "Counterparty Result",
          designation_date: "2026-07-06T11:00:00.000Z",
          checked_at: "2026-07-06T11:05:00.000Z"
        })
      });
    });

    await page.goto("/sanctions");

    await expect(page.locator(`a[href="/cases/${workspaceCaseId}"]`).first()).toBeVisible();
    await expect(
      page.locator(
        `a[href="/audit?resource_type=case&resource_id=${workspaceCaseId}&request_id=${workspaceCaseId}"]`
      ).first()
    ).toBeVisible();
    await expect(
      page.locator(
        `a[href="/evidence?domain=sanctions&resource_type=case&resource_id=${workspaceCaseId}&request_id=${workspaceCaseId}"]`
      ).first()
    ).toBeVisible();

    await page.getByTestId("sanctions-address").fill(address);
    await page.getByTestId("sanctions-chain").selectOption("ethereum");
    await page.getByTestId("sanctions-case-id").fill(resultCaseId);
    await page.getByTestId("sanctions-check-btn").click();

    await expect(page.locator(`a[href="/cases/${resultCaseId}"]`).nth(0)).toBeVisible();
    await expect(
      page.locator(
        `a[href="/audit?resource_type=case&resource_id=${resultCaseId}&request_id=${resultCaseId}"]`
      ).nth(0)
    ).toBeVisible();
    await expect(
      page.locator(
        `a[href="/evidence?domain=sanctions&resource_type=case&resource_id=${resultCaseId}&request_id=${resultCaseId}"]`
      ).nth(0)
    ).toBeVisible();
    await expect(
      page.locator(
        `a[href="/investigate?address=${encodeURIComponent(address)}&chain=ethereum&report_type=technical_basic"]`
      )
    ).toBeVisible();
  });

  test("blocks deriva links contextuais no workspace e no resultado", async ({ page }: { page: Page }) => {
    const workspaceCaseId = "33333333-3333-4333-8333-333333333333";
    const resultCaseId = "44444444-4444-4444-8444-444444444444";
    const address = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

    await seedFrontendAuth(page);

    await page.route("**/api/app/operations/work-items?module=blocks**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "work-blocks-01",
              resource_id: "block-ws-01",
              owner_user_id: "linked-blocks-owner",
              queue_status: "UNDER_REVIEW",
              priority: "high",
              due_at: "2026-07-06T15:00:00.000Z",
              note: "workspace note",
              metadata: {
                workspace_id: "block-ws-01",
                block_id: "block-ws-01",
                address,
                chain: "ethereum",
                entity_name: "Entity WS",
                entity_document: "12345678900",
                local_case_id: workspaceCaseId,
                owner_label: "Ops Blocks",
                local_block_status: "BLOCKED",
                action: "block_required",
                requires_coaf_report: true,
                decision_confidence: 0.94,
                regulatory_basis: ["ofac_match"],
                matched_lists: ["ofac"],
                evidence_hash: "f".repeat(64),
                screened_at: "2026-07-05T15:00:00.000Z"
              },
              last_activity_at: "2026-07-05T15:10:00.000Z",
              updated_at: "2026-07-05T15:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/compliance/blocks/evaluate", async (route: Route) => {
      const payload = parseBlockEvaluationPayload(route);
      expect(payload.address).toBe(address);
      expect(payload.chain).toBe("ethereum");

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          address,
          chain: "ethereum",
          action: "block_required",
          block_id: "block-result-01",
          evidence_hash: "e".repeat(64),
          matched_lists: ["ofac"],
          regulatory_basis: ["ofac_match"],
          screened_at: "2026-07-06T16:00:00.000Z",
          requires_coaf_report: true,
          decision_confidence: 0.97
        })
      });
    });

    await page.goto("/blocks");

    await expect(page.locator(`a[href="/cases/${workspaceCaseId}"]`).first()).toBeVisible();
    await expect(
      page.locator(
        `a[href="/audit?resource_type=case&resource_id=${workspaceCaseId}&request_id=${workspaceCaseId}&report_id=block-ws-01"]`
      ).first()
    ).toBeVisible();
    await expect(
      page.locator(
        `a[href="/evidence?domain=all&resource_type=case&resource_id=${workspaceCaseId}&request_id=${workspaceCaseId}&report_id=block-ws-01"]`
      ).first()
    ).toBeVisible();

    await page.getByTestId("blocks-address").fill(address);
    await page.getByTestId("blocks-chain").selectOption("ethereum");
    await page.getByTestId("blocks-case-id").fill(resultCaseId);
    await page.getByTestId("blocks-evaluate-btn").click();

    await expect(page.locator(`a[href="/cases/${resultCaseId}"]`).nth(0)).toBeVisible();
    await expect(
      page.locator(
        `a[href="/audit?resource_type=case&resource_id=${resultCaseId}&request_id=${resultCaseId}&report_id=block-result-01"]`
      ).nth(0)
    ).toBeVisible();
    await expect(
      page.locator(
        `a[href="/evidence?domain=all&resource_type=case&resource_id=${resultCaseId}&request_id=${resultCaseId}&report_id=block-result-01"]`
      ).nth(0)
    ).toBeVisible();
    await expect(
      page.locator(
        `a[href="/investigate?address=${encodeURIComponent(address)}&chain=ethereum&report_type=technical_basic"]`
      )
    ).toBeVisible();
  });
});

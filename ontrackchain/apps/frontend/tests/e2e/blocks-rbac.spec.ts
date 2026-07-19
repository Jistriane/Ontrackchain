import { expect, test, type Page } from "@playwright/test";

async function seedBlocksPage(page: Page, role: string) {
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

  await page.addInitScript(({ currentRole }) => {
    const originalFetch = window.fetch.bind(window);
    const evaluationResponse = {
      address: "0x1111111111111111111111111111111111111111",
      chain: "ethereum",
      action: "BLOCK_AND_ALERT",
      requires_coaf_report: false,
      decision_confidence: 0.97,
      regulatory_basis: ["BCB 520 Art. 43 §2° V"],
      matched_lists: ["OFAC_SDN"],
      evidence_hash: "sha256-block-rbac",
      block_id: "block-rbac-1",
      screened_at: "2026-07-15T12:00:00Z"
    };

    window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      const request = typeof input === "string" ? new Request(input, init) : input instanceof URL ? new Request(input, init) : input;
      const url = request.url;
      const method = request.method.toUpperCase();

      if (url.includes("/api/app/auth/context")) {
        return new Response(
          JSON.stringify({
            org_id: "org-e2e",
            user_id: "user-e2e",
            linked_user_id: "linked-e2e",
            role: currentRole,
            plan: "professional",
            auth_method: "jwt",
            mfa_mode: "external_provider",
            mfa_provider_homologated: "true"
          }),
          {
            status: 200,
            headers: { "content-type": "application/json" }
          }
        );
      }

      if (url.includes("/api/app/operations/work-items")) {
        if (method === "GET") {
          return new Response(JSON.stringify({ data: [] }), {
            status: 200,
            headers: { "content-type": "application/json" }
          });
        }

        return new Response(JSON.stringify({ detail: "noop_mock" }), {
          status: 200,
          headers: { "content-type": "application/json" }
        });
      }

      if (url.includes("/api/app/compliance/blocks/evaluate")) {
        return new Response(JSON.stringify(evaluationResponse), {
          status: 200,
          headers: { "content-type": "application/json" }
        });
      }

      if (url.includes("/api/app/compliance/blocks/block-rbac-1/lift")) {
        return new Response(
          JSON.stringify({
            block_id: "block-rbac-1",
            status: "LIFTED",
            review_status: "COMPLETED",
            lifted_at: "2026-07-15T12:05:00Z"
          }),
          {
            status: 200,
            headers: { "content-type": "application/json" }
          }
        );
      }

      return originalFetch(input, init);
    };
  }, { currentRole: role });
}

async function fillAndEvaluate(page: Page) {
  await page.goto("/blocks");
  await expect(page.getByTestId("blocks-evaluate-btn")).toBeVisible();
  await page.getByTestId("blocks-address").fill("0x1111111111111111111111111111111111111111");
  await page.getByTestId("blocks-chain").selectOption("ethereum");
  await page.getByTestId("blocks-evaluate-btn").click();
  await expect(page.getByText("Ação recomendada: BLOCK_AND_ALERT")).toBeVisible();
}

test.describe("blocks RBAC", () => {
  test("viewer nao recebe a superficie de avaliacao preventiva", async ({ page }) => {
    await seedBlocksPage(page, "VIEWER");
    await page.goto("/blocks");

    await expect(page.getByTestId("blocks-evaluate-btn")).toHaveCount(0);
    await expect(
      page.getByText("A avaliação preventiva está oculta nesta sessão porque o papel atual não possui autorização operacional de compliance.")
    ).toBeVisible();
  });

  test("analyst avalia mas nao recebe o painel de lift", async ({ page }) => {
    await seedBlocksPage(page, "ANALYST");

    await fillAndEvaluate(page);

    await expect(page.getByTestId("blocks-lift-panel")).toHaveCount(0);
    await expect(
      page.getByText("O lift está oculto nesta sessão porque o papel atual não possui autorização regulatória operacional.")
    ).toBeVisible();
  });

  test("compliance officer recebe painel e consegue executar o lift", async ({ page }) => {
    await seedBlocksPage(page, "COMPLIANCE_OFFICER");

    await fillAndEvaluate(page);

    await expect(page.getByTestId("blocks-lift-panel")).toBeVisible();
    await page.locator("textarea").fill("Liberacao aprovada apos validacao regulatoria.");
    await page.getByTestId("blocks-lift-btn").click();

    await expect(page.getByText("Lift executado com sucesso. Status atual: LIFTED.")).toBeVisible();
  });

  test("alias OTK_COMPLIANCE_OFFICER recebe painel e consegue executar o lift", async ({ page }) => {
    await seedBlocksPage(page, "OTK_COMPLIANCE_OFFICER");

    await fillAndEvaluate(page);

    await expect(page.getByTestId("blocks-lift-panel")).toBeVisible();
    await page.locator("textarea").fill("Liberacao aprovada apos validacao regulatoria.");
    await page.getByTestId("blocks-lift-btn").click();

    await expect(page.getByText("Lift executado com sucesso. Status atual: LIFTED.")).toBeVisible();
  });
});

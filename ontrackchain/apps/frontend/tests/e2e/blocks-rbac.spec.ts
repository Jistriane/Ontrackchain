import { expect, test, type Page } from "@playwright/test";

type BlocksSeedOptions = {
  denyEvaluate?: boolean;
  denyLift?: boolean;
  seedOfficialList?: boolean;
  denyWorkspace?: boolean;
};

async function seedBlocksPage(page: Page, role: string, options: BlocksSeedOptions = {}) {
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
  const currentRole = role;
  const denyEvaluate = options.denyEvaluate ?? false;
  const denyLift = options.denyLift ?? false;
  const seedOfficialList = options.seedOfficialList ?? false;
  const denyWorkspace = options.denyWorkspace ?? false;

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
  const officialListResponse = {
    items: seedOfficialList
      ? [
          {
            block_id: "bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f",
            case_id: "case-rbac-1",
            address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
            chain: "ethereum",
            action: "BLOCK",
            review_status: "CONFIRMED",
            status: "CONFIRMED",
            regulatory_basis: ["OFAC corroborated hit"],
            matched_lists: ["OFAC"],
            decision_confidence: 0.94,
            requires_coaf_report: true,
            evidence_hash: "sha256-official-block",
            screened_at: "2026-07-15T11:50:00Z",
            lifted_at: null,
            lifted_reason: null,
            review_note: "Persistido no backend oficial."
          }
        ]
      : [],
    total: seedOfficialList ? 1 : 0,
    limit: 100,
    offset: 0
  };

  await page.route("**/api/app/auth/context", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        org_id: "org-e2e",
        user_id: "user-e2e",
        linked_user_id: "linked-e2e",
        role: currentRole,
        plan: "professional",
        auth_method: "jwt",
        mfa_mode: "external_provider",
        mfa_provider_homologated: "true"
      })
    });
  });

  await page.route(/\/api\/app\/compliance\/blocks(?:\?.*)?$/, async (route) => {
    if (currentRole === "VIEWER") {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "preventive_block_read_role_required" })
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(officialListResponse)
    });
  });

  await page.route(/\/api\/app\/operations\/work-items(?:\?.*)?$/, async (route) => {
    if (route.request().method().toUpperCase() === "GET") {
      if (denyWorkspace) {
        await route.fulfill({
          status: 401,
          contentType: "application/json",
          body: JSON.stringify({ detail: "not_authenticated" })
        });
        return;
      }

      if (currentRole === "VIEWER") {
        await route.fulfill({
          status: 403,
          contentType: "application/json",
          body: JSON.stringify({ detail: "preventive_block_read_role_required" })
        });
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ detail: "noop_mock" })
    });
  });

  await page.route("**/api/app/compliance/blocks/evaluate", async (route) => {
    if (denyEvaluate) {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "block_evaluate_role_required" })
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(evaluationResponse)
    });
  });

  await page.route(/\/api\/app\/compliance\/blocks\/[^/]+\/lift$/, async (route) => {
    if (denyLift) {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "block_lift_role_required" })
      });
      return;
    }

    const blockId = route.request().url().split("/api/app/compliance/blocks/")[1]?.split("/lift")[0] ?? "block-rbac-1";
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        block_id: blockId,
        status: "LIFTED",
        review_status: "COMPLETED",
        lifted_at: "2026-07-15T12:05:00Z"
      })
    });
  });
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
    const workspaceRestriction = page.getByText(
      "A leitura do workspace de bloqueios exige papel operacional de compliance: ADMIN, ANALYST ou COMPLIANCE_OFFICER."
    );
    await expect(workspaceRestriction).toHaveCount(2);
    await expect(workspaceRestriction.first()).toBeVisible();
    await expect(page.getByText("Nenhuma decisão preventiva foi registrada ainda no workspace compartilhado.")).toHaveCount(0);
  });

  test("analyst avalia mas nao recebe o painel de lift", async ({ page }) => {
    await seedBlocksPage(page, "ANALYST");

    await fillAndEvaluate(page);

    await expect(page.getByTestId("blocks-lift-panel")).toHaveCount(0);
    await expect(
      page.getByText("O lift está oculto nesta sessão porque o papel atual não possui autorização regulatória operacional.")
    ).toBeVisible();
  });

  test("analyst recebe erro semantico quando o backend recusa a avaliacao", async ({ page }) => {
    await seedBlocksPage(page, "ANALYST", { denyEvaluate: true });

    await page.goto("/blocks");
    await expect(page.getByTestId("blocks-evaluate-btn")).toBeVisible();
    await page.getByTestId("blocks-address").fill("0x1111111111111111111111111111111111111111");
    await page.getByTestId("blocks-chain").selectOption("ethereum");
    await page.getByTestId("blocks-evaluate-btn").click();

    await expect(
      page.getByText("A avaliação de bloqueio exige papel operacional de compliance: ADMIN, ANALYST ou COMPLIANCE_OFFICER.")
    ).toBeVisible();
    await expect(page.getByText("Ação recomendada: BLOCK_AND_ALERT")).toHaveCount(0);
  });

  test("analyst renderiza bloqueio oficial mesmo sem work-item compartilhado correspondente", async ({ page }) => {
    await seedBlocksPage(page, "ANALYST", { seedOfficialList: true });

    await page.goto("/blocks");

    const workspaceRow = page.getByTestId("blocks-workspace-row-bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f");
    await expect(workspaceRow).toBeVisible();
    await expect(workspaceRow.getByText("0x8ba1f109551bD432803012645Ac136ddd64DBA72")).toBeVisible();
    await expect(page.getByTestId("blocks-workspace-source-bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f")).toContainText("servidor");
  });

  test("preserva a negacao semantica do workspace compartilhado sem degradar para vazios sinteticos", async ({ page }) => {
    await seedBlocksPage(page, "ANALYST", { denyWorkspace: true });

    await page.goto("/blocks");

    await expect(page.getByTestId("blocks-workspace-message")).toContainText(
      "Sua sessão expirou ou não foi autenticada."
    );
    await expect(page.getByTestId("blocks-history-message")).toContainText(
      "Sua sessão expirou ou não foi autenticada."
    );
    await expect(page.getByText("Nenhuma decisão preventiva foi registrada ainda no workspace compartilhado.")).toHaveCount(0);
    await expect(page.getByText("Nenhum bloqueio rastreado no workspace.")).toHaveCount(0);
  });

  test("compliance officer recebe painel e consegue executar o lift", async ({ page }) => {
    await seedBlocksPage(page, "COMPLIANCE_OFFICER");

    await fillAndEvaluate(page);

    await expect(page.getByTestId("blocks-lift-panel")).toBeVisible();
    await page.locator("textarea").fill("Liberacao aprovada apos validacao regulatoria.");
    await page.getByTestId("blocks-lift-btn").click();

    await expect(page.getByText("Lift executado com sucesso. Status atual: LIFTED.")).toBeVisible();
  });

  test("compliance officer preserva contexto quando o backend recusa o lift", async ({ page }) => {
    await seedBlocksPage(page, "COMPLIANCE_OFFICER", { denyLift: true });

    await fillAndEvaluate(page);

    await expect(page.getByTestId("blocks-lift-panel")).toBeVisible();
    await page.locator("textarea").fill("Liberacao aprovada apos validacao regulatoria.");
    await page.getByTestId("blocks-lift-btn").click();

    await expect(page.getByText("O lift de bloqueio exige papel regulatório operacional: ADMIN ou COMPLIANCE_OFFICER.")).toBeVisible();
    await expect(page.getByTestId("blocks-lift-panel")).toBeVisible();
    await expect(page.getByText("Ação recomendada: BLOCK_AND_ALERT")).toBeVisible();
    await expect(page.getByText("Lift executado com sucesso. Status atual: LIFTED.")).toHaveCount(0);
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

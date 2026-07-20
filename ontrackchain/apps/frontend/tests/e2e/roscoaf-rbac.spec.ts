import { expect, test } from "@playwright/test";

import { seedRosCoafPage } from "./roscoaf-test-helpers";

test.describe("ros-coaf rbac", () => {
  test("viewer recebe apenas leitura do dossie e não ganha CTAs sensíveis", async ({ page }) => {
    const { rosId } = await seedRosCoafPage(page, { role: "VIEWER" });

    await page.goto(`/ros-coaf?ros_id=${encodeURIComponent(rosId)}`);

    await expect(page.getByTestId("roscoaf-detail-table")).toContainText(rosId);
    await expect(page.getByTestId("roscoaf-generate-btn")).toHaveCount(0);
    await expect(page.getByTestId("roscoaf-generate-access-denied")).toContainText(
      "A geração do draft do ROS exige papel operacional: ADMIN ou COMPLIANCE_OFFICER."
    );
    await expect(page.getByTestId("roscoaf-approve-btn")).toHaveCount(0);
    await expect(page.getByTestId("roscoaf-approve-access-denied")).toContainText(
      "A aprovação/rejeição do ROS exige papel de revisão formal: ADMIN, COMPLIANCE_OFFICER, LEGAL_REVIEWER ou REVIEWER."
    );
    await expect(page.getByTestId("roscoaf-submitted-btn")).toHaveCount(0);
    await expect(page.getByTestId("roscoaf-submitted-access-denied")).toContainText(
      "A submissão manual do ROS exige papel operacional: ADMIN ou COMPLIANCE_OFFICER."
    );
  });

  test("reviewer aprova, mas não ganha submissão manual", async ({ page }) => {
    const { rosId } = await seedRosCoafPage(page, { role: "REVIEWER" });

    await page.goto(`/ros-coaf?ros_id=${encodeURIComponent(rosId)}`);

    await expect(page.getByTestId("roscoaf-approve-btn")).toBeVisible();
    await expect(page.getByTestId("roscoaf-submitted-btn")).toHaveCount(0);
    await expect(page.getByTestId("roscoaf-submitted-access-denied")).toContainText(
      "A submissão manual do ROS exige papel operacional: ADMIN ou COMPLIANCE_OFFICER."
    );
  });

  test("alias OTK_LEGAL_REVIEWER mantém trilha de aprovação sem ganhar submissão manual", async ({ page }) => {
    const { rosId } = await seedRosCoafPage(page, { role: "OTK_LEGAL_REVIEWER" });

    await page.goto(`/ros-coaf?ros_id=${encodeURIComponent(rosId)}`);

    await expect(page.getByTestId("roscoaf-approve-btn")).toBeVisible();
    await expect(page.getByTestId("roscoaf-submitted-btn")).toHaveCount(0);
    await expect(page.getByTestId("roscoaf-submitted-access-denied")).toContainText(
      "A submissão manual do ROS exige papel operacional: ADMIN ou COMPLIANCE_OFFICER."
    );
  });

  test("alias OTK_COMPLIANCE_OFFICER mantém trilho operacional completo", async ({ page }) => {
    const { rosId } = await seedRosCoafPage(page, { role: "OTK_COMPLIANCE_OFFICER" });

    await page.goto(`/ros-coaf?ros_id=${encodeURIComponent(rosId)}`);

    await expect(page.getByTestId("roscoaf-generate-btn")).toBeVisible();
    await expect(page.getByTestId("roscoaf-approve-btn")).toBeVisible();
    await expect(page.getByTestId("roscoaf-submitted-btn")).toBeVisible();
    await expect(page.getByTestId("roscoaf-generate-access-denied")).toHaveCount(0);
    await expect(page.getByTestId("roscoaf-submitted-access-denied")).toHaveCount(0);
  });

  test("bloqueia cedo a trilha sensível quando falta linked_user_id persistido", async ({ page }) => {
    const { rosId } = await seedRosCoafPage(page, {
      role: "COMPLIANCE_OFFICER",
      linkedUserId: null,
      mfaMode: "external_provider",
      mfaProviderHomologated: "true"
    });

    await page.goto(`/ros-coaf?ros_id=${encodeURIComponent(rosId)}`);

    await expect(page.getByTestId("roscoaf-auth-readiness")).toContainText(
      "A sessão atual ainda não atende todos os pré-requisitos"
    );
    await expect(page.getByTestId("roscoaf-auth-linked-user-required")).toContainText(
      "ROS/COAF exige um usuário federado vinculado ao tenant atual."
    );
    await expect(page.getByTestId("roscoaf-generate-prereq-block")).toContainText("A geração do draft foi bloqueada");
    await expect(page.getByTestId("roscoaf-approve-prereq-block")).toContainText("A aprovação ou rejeição foi bloqueada");
    await expect(page.getByTestId("roscoaf-submitted-prereq-block")).toContainText("A submissão manual foi bloqueada");
    await expect(page.getByTestId("roscoaf-detail-export-dossier-prereq-block")).toContainText(
      "ROS/COAF exige um usuário federado vinculado ao tenant atual."
    );
    await expect(page.getByTestId("roscoaf-generate-btn")).toBeDisabled();
    await expect(page.getByTestId("roscoaf-approve-btn")).toBeDisabled();
    await expect(page.getByTestId("roscoaf-submitted-btn")).toBeDisabled();
    await expect(page.getByTestId("roscoaf-detail-export-dossier")).toBeDisabled();
  });

  test("tester recebe negacao semantica na listagem oficial em vez de degradar para lista vazia", async ({ page }) => {
    await seedRosCoafPage(page, {
      role: "TESTER",
      denyList: true
    });

    await page.goto("/ros-coaf");

    await expect(page.getByTestId("roscoaf-workspace-message")).toContainText(
      "A leitura/listagem de relatórios exige papel operacional: ADMIN, AUDITOR, ANALYST ou VIEWER."
    );
    await expect(page.getByText("Nenhum ROS/COAF registrado ainda no workspace compartilhado.")).toHaveCount(0);
  });

  test("auditor recebe negacao semantica do workspace compartilhado sem perder a listagem oficial", async ({ page }) => {
    const { rosId } = await seedRosCoafPage(page, {
      role: "AUDITOR",
      denyWorkspace: true
    });

    await page.goto(`/ros-coaf?ros_id=${encodeURIComponent(rosId)}`);

    await expect(page.getByTestId(`roscoaf-workspace-row-${rosId}`)).toContainText(rosId);
    await expect(page.getByTestId("roscoaf-workspace-sync-message")).toContainText(
      "Sua sessão expirou ou não foi autenticada."
    );
    await expect(page.getByText("Nenhum ROS/COAF registrado ainda no workspace compartilhado.")).toHaveCount(0);
  });

  test("tester recebe negacao semantica no detalhe oficial em vez de painel vazio", async ({ page }) => {
    const { rosId } = await seedRosCoafPage(page, {
      role: "TESTER",
      denyDetail: true
    });

    await page.goto(`/ros-coaf?ros_id=${encodeURIComponent(rosId)}`);

    await expect(
      page.getByText("A leitura/listagem de relatórios exige papel operacional: ADMIN, AUDITOR, ANALYST ou VIEWER.")
    ).toBeVisible();
    await expect(page.getByTestId("roscoaf-detail-table")).toHaveCount(0);
  });

  test("tester recebe negacao semantica ao exportar dossie oficial", async ({ page }) => {
    const { rosId } = await seedRosCoafPage(page, {
      role: "TESTER",
      denyDossier: true
    });

    await page.goto(`/ros-coaf?ros_id=${encodeURIComponent(rosId)}`);
    await expect(page.getByTestId("roscoaf-detail-table")).toContainText(rosId);

    await page.getByTestId("roscoaf-detail-export-dossier").click();

    await expect(
      page.getByText("A leitura/listagem de relatórios exige papel operacional: ADMIN, AUDITOR, ANALYST ou VIEWER.")
    ).toBeVisible();
  });
});

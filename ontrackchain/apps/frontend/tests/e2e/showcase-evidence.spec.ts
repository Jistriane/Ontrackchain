import { expect, test } from "@playwright/test";

import {
  ensureManualPackageSealed,
  exportRosCoafDossierAndReadHash,
  loginIntoShowcase,
  openSeededEvidenceEvent,
  openSeededRosCoafEvidenceEvent,
  showcaseOnly
} from "./showcase-helpers";

test.describe("standalone showcase evidence", () => {
  test.skip(!showcaseOnly, "requer TEST_SHOWCASE_MODE=true");

  test("abre timeline seeded sem flood de requests", async ({ page }) => {
    await loginIntoShowcase(page);

    let timelineRequestCount = 0;
    page.on("requestfinished", (request) => {
      if (request.url().includes("/api/app/operations/work-items/") && request.url().includes("/timeline")) {
        timelineRequestCount += 1;
      }
    });

    await openSeededEvidenceEvent(page, "req-showcase-sof-001");
    await expect(page.getByTestId("evidence-manual-workspace-panel")).toBeVisible();

    timelineRequestCount = 0;
    await page.getByTestId("evidence-manual-workspace-open-timeline").click();
    await expect(page.getByTestId("work-item-timeline-panel")).toBeVisible();
    await expect(page.getByTestId("work-item-timeline-event").first()).toBeVisible();
    await page.waitForTimeout(2500);

    expect(timelineRequestCount).toBeLessThanOrEqual(3);
  });

  test("materializa signoff e finalize do manual package", async ({ page, request }) => {
    await loginIntoShowcase(page);
    await openSeededEvidenceEvent(page, "req-showcase-dd-001");
    await ensureManualPackageSealed(page, request, "req-showcase-dd-001", "GOV-SHOWCASE-001");
  });

  test("revoga o selo do manual package", async ({ page, request }) => {
    await loginIntoShowcase(page);
    await openSeededEvidenceEvent(page, "req-showcase-dd-001");
    await ensureManualPackageSealed(page, request, "req-showcase-dd-001", "GOV-SHOWCASE-REV-001");

    if (await page.getByTestId("evidence-manual-package-revoked-notice").isVisible().catch(() => false)) {
      await expect(page.getByTestId("evidence-manual-package-revoked-notice")).toBeVisible();
      return;
    }

    await expect(page.getByTestId("evidence-manual-package-revoke-panel")).toBeVisible();
    await page.getByTestId("evidence-manual-package-revoke-ticket-ref").fill("GOV-REVOKE-001");
    await page.getByTestId("evidence-manual-package-revoke-reason").fill("Revogacao regulatoria validada no showcase.");
    await page.getByTestId("evidence-manual-package-revoke").click();

    await expect(page.getByTestId("evidence-manual-package-revoked-notice")).toBeVisible();
  });

  test("supersede o selo do manual package", async ({ page, request }) => {
    await loginIntoShowcase(page);
    await openSeededEvidenceEvent(page, "req-showcase-sof-001");
    await ensureManualPackageSealed(page, request, "req-showcase-sof-001", "GOV-SHOWCASE-SUP-001");

    const replacementSealId = "showcase-replacement-seal-001";
    if (await page.getByTestId("evidence-manual-package-superseded-notice").isVisible().catch(() => false)) {
      await expect(page.getByTestId("evidence-manual-package-superseded-notice")).toBeVisible();
      return;
    }

    await expect(page.getByTestId("evidence-manual-package-supersede-panel")).toBeVisible();
    await page.getByTestId("evidence-manual-package-supersede-seal-id").fill(replacementSealId);
    await page.getByTestId("evidence-manual-package-supersede-ticket-ref").fill("GOV-SUPERSEDE-001");
    await page.getByTestId("evidence-manual-package-supersede-reason").fill("Substituicao controlada do selo no showcase.");
    await page.getByTestId("evidence-manual-package-supersede").click();

    await expect(page.getByTestId("evidence-manual-package-superseded-notice")).toBeVisible();
    await expect(page.getByTestId("evidence-manual-package-superseded-notice")).toContainText(replacementSealId);
  });

  test("exporta o dossie ROS/COAF com hash canonico refletido na UI", async ({ page }) => {
    await loginIntoShowcase(page);
    await openSeededRosCoafEvidenceEvent(page);

    const exportedDossier = await exportRosCoafDossierAndReadHash(page);

    await expect(page.getByTestId("evidence-hash-context")).toContainText(exportedDossier.dossierSha256);
    await expect(page.getByTestId("evidence-hash-context")).toContainText("dossie regulatorio");
    await expect(page.getByTestId("evidence-dossier-detail-context")).toContainText(exportedDossier.filename);
    await expect(page.getByTestId("evidence-dossier-detail-context")).toContainText(exportedDossier.dossierSha256);
    await expect(page.getByTestId("evidence-chain-dossier-context")).toContainText(exportedDossier.filename);
    await expect(page.getByTestId("evidence-chain-dossier-context")).toContainText(exportedDossier.dossierSha256);
    await expect(page.getByTestId("evidence-dossier-detail-open-report")).toHaveAttribute(
      "href",
      "/reports?history_report_id=rep-showcase-003"
    );
    await expect(page.getByTestId("evidence-dossier-detail-open-roscoaf")).toHaveAttribute(
      "href",
      "/ros-coaf?ros_id=7c4dca53-5806-564f-91ba-ef5487dbf6ce&report_id=rep-showcase-003"
    );
  });
});

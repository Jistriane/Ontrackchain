import { expect, test } from "@playwright/test";

import { expectDownloadLikeResponse } from "./download-helpers";
import { seedRosCoafPage } from "./roscoaf-test-helpers";

test.describe("ros-coaf regulatory dossier", () => {
  test("exporta dossiê regulatório oficial via endpoint unificado", async ({ page }) => {
    const { rosId, reportId } = await seedRosCoafPage(page);

    await page.goto(`/ros-coaf?ros_id=${encodeURIComponent(rosId)}`);

    await expect(page.getByTestId("roscoaf-detail-table")).toContainText(rosId);
    await expect(page.getByTestId("roscoaf-regulatory-timeline-table")).toBeVisible();
    await expect(page.getByTestId(`roscoaf-workspace-row-${rosId}`)).toContainText(rosId);
    await expect(page.getByTestId(`roscoaf-workspace-priority-${rosId}`)).toContainText("alta");
    await expect(page.getByTestId(`roscoaf-workspace-source-${rosId}`)).toContainText("servidor");
    await expect(page.getByTestId(`roscoaf-workspace-sla-${rosId}`)).toContainText("No prazo");
    await expect(page.getByTestId(`roscoaf-workspace-phase-${rosId}`)).toContainText("gerado");
    await expect(page.getByTestId(`roscoaf-workspace-phase-${rosId}`)).toContainText("PENDING_APPROVAL");
    await expect(page.getByTestId(`roscoaf-workspace-local-deadline-${rosId}`)).not.toContainText("T15:30:00.000Z");
    await expect(page.getByTestId(`roscoaf-workspace-submission-deadline-${rosId}`)).not.toContainText("T10:00:00.000Z");
    await expect(page.getByTestId(`roscoaf-history-row-${rosId}`)).toContainText(rosId);
    await expect(page.getByTestId(`roscoaf-history-phase-${rosId}`)).toContainText("gerado");
    await expect(page.getByTestId(`roscoaf-history-source-${rosId}`)).toContainText("servidor");
    await expect(page.getByTestId(`roscoaf-history-sla-${rosId}`)).toContainText("No prazo");
    await expect(page.getByTestId(`roscoaf-history-submission-deadline-${rosId}`)).not.toContainText("T10:00:00.000Z");
    await expect(page.getByTestId(`roscoaf-history-last-action-${rosId}`)).not.toContainText("T12:00:00.000Z");
    await expect(page.getByTestId("roscoaf-dossier-history-table")).toContainText(
      `ontrackchain-ros-coaf-regulatory-dossier-${rosId}.json`
    );
    await expect(page.getByTestId("roscoaf-dossier-history-table")).toContainText("a".repeat(64));
    await expect(page.getByText("Emissoes auditadas")).toBeVisible();
    await expect(page.getByText("aaaaaaaaaaaaaaaa...")).toBeVisible();
    await expect(page.getByTestId("roscoaf-dossier-history-open-audit")).toHaveAttribute(
      "href",
      `/audit?action=coaf_regulatory_dossier_downloaded&resource_type=ros_record&resource_id=${rosId}&report_id=${reportId}`
    );

    await expectDownloadLikeResponse(
      page,
      {
        urlPart: "/api/app/reports/ros-coaf/",
        expectedFilename: `ontrackchain-ros-coaf-regulatory-dossier-${rosId}.json`
      },
      async () => {
        await page.getByTestId("roscoaf-detail-export-dossier").click();
      }
    );
  });
});

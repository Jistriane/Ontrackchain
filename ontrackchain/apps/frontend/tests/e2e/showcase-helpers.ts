import { expect, type APIRequestContext, type Page } from "@playwright/test";

export const showcaseOnly = process.env.TEST_SHOWCASE_MODE === "true";

export type FrontendHealthzPayload = {
  status: string;
  deploymentModel: string;
  standaloneShowcaseMode: boolean;
  hostedShowcaseFallback?: boolean;
  missingEnvKeys: string[];
};

const SEEDED_MANUAL_PACKAGE_ACTIONS: Record<string, string> = {
  "req-showcase-dd-001": "compliance_due_diligence_checked",
  "req-showcase-sof-001": "compliance_source_of_funds_checked"
};

const EVIDENCE_ACTION_LABELS: Record<string, string> = {
  compliance_due_diligence_checked: "Due diligence verificada",
  compliance_source_of_funds_checked: "Origem de fundos verificada",
  coaf_report_generated: "ROS/COAF gerado"
};

const SEEDED_ROS_COAF_EVIDENCE = {
  requestId: "req-showcase-ros-001",
  reportId: "rep-showcase-003",
  rosId: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
  action: "coaf_report_generated"
} as const;

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function readDownloadFilenameFromHeaders(headers: Record<string, string>) {
  const contentDisposition = headers["content-disposition"]?.trim() ?? "";
  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1]);
  }
  const quotedMatch = contentDisposition.match(/filename="([^"]+)"/i);
  if (quotedMatch?.[1]) {
    return quotedMatch[1];
  }
  const plainMatch = contentDisposition.match(/filename=([^;]+)/i);
  return plainMatch?.[1]?.trim() ?? "";
}

export async function readFrontendHealthz(page: Page): Promise<FrontendHealthzPayload> {
  const response = await page.request.get("/api/healthz");
  const payload = (await response.json()) as FrontendHealthzPayload;
  return payload;
}

export function assertStandaloneShowcasePayload(payload: FrontendHealthzPayload) {
  expect(payload.deploymentModel).toBe("render-frontend-standalone-showcase");
  expect(payload.standaloneShowcaseMode).toBe(true);
  expect(payload.missingEnvKeys).not.toContain("INTERNAL_API_BASE_URL");
  expect(payload.missingEnvKeys).not.toContain("INTERNAL_AUTH_BASE_URL");
  expect(payload.missingEnvKeys).not.toContain("INTERNAL_KEYCLOAK_BASE_URL");
  expect(payload.missingEnvKeys).not.toContain("NEXT_PUBLIC_API_BASE_URL");
  return payload;
}

export async function assertStandaloneShowcaseRuntime(page: Page) {
  return assertStandaloneShowcasePayload(await readFrontendHealthz(page));
}

export async function loginIntoShowcase(page: Page) {
  const payload = await readFrontendHealthz(page);
  if (!payload.standaloneShowcaseMode || payload.deploymentModel !== "render-frontend-standalone-showcase") {
    throw new Error(
      [
        "showcase_runtime_mismatch",
        `deploymentModel=${payload.deploymentModel}`,
        `standaloneShowcaseMode=${String(payload.standaloneShowcaseMode)}`,
        `hostedShowcaseFallback=${String(payload.hostedShowcaseFallback ?? false)}`,
        `missingEnvKeys=${payload.missingEnvKeys.join(",") || "none"}`
      ].join(" ")
    );
  }
  await page.goto("/login");
  await expect(page.getByTestId("login-btn")).toBeVisible();
  await expect(page.getByTestId("login-btn")).toBeEnabled();
  await page.getByTestId("login-btn").click();
  await expect(page).toHaveURL(/\/dashboard$/);
}

export async function openSeededEvidenceEvent(page: Page, requestId: string) {
  const preferredAction = SEEDED_MANUAL_PACKAGE_ACTIONS[requestId] ?? "";
  await page.goto(`/evidence?request_id=${encodeURIComponent(requestId)}&limit=200`);

  const preferredActionLabel = EVIDENCE_ACTION_LABELS[preferredAction] ?? "";
  const evidenceRow =
    preferredAction && preferredActionLabel
      ? page.getByRole("button", {
          name: new RegExp(`^${escapeRegExp(preferredActionLabel)} \\(${escapeRegExp(preferredAction)}\\)`, "i")
        })
      : page.locator("button").filter({ has: page.getByTestId("evidence-log-row") }).first();
  await expect(evidenceRow).toBeVisible();
  await evidenceRow.click();
  await expect(page.getByTestId("evidence-details-panel")).toBeVisible();
  await expect(page.getByTestId("evidence-details-panel")).toContainText(requestId);
  await expect(page.getByTestId("evidence-manual-package-panel")).toBeVisible();
  await expect(page.getByTestId("evidence-manual-package-seal-panel")).toBeVisible();
}

export async function openSeededRosCoafEvidenceEvent(page: Page) {
  await page.goto(`/evidence?request_id=${encodeURIComponent(SEEDED_ROS_COAF_EVIDENCE.requestId)}&limit=200`);
  const evidenceRow = page.getByRole("button", {
    name: new RegExp(
      `^${escapeRegExp(EVIDENCE_ACTION_LABELS[SEEDED_ROS_COAF_EVIDENCE.action])} \\(${escapeRegExp(SEEDED_ROS_COAF_EVIDENCE.action)}\\)`,
      "i"
    )
  });
  await expect(evidenceRow).toBeVisible();
  await evidenceRow.click();
  await expect(page.getByTestId("evidence-details-panel")).toBeVisible();
  await expect(page.getByTestId("evidence-details-panel")).toContainText(SEEDED_ROS_COAF_EVIDENCE.requestId);
  await expect(page.getByTestId("evidence-details-panel")).toContainText(SEEDED_ROS_COAF_EVIDENCE.reportId);
  await expect(page.getByTestId("evidence-details-panel")).toContainText(SEEDED_ROS_COAF_EVIDENCE.rosId);
  await expect(page.getByTestId("evidence-export-ros-dossier")).toBeVisible();
}

export async function exportRosCoafDossierAndReadHash(page: Page) {
  const exportButton = page.getByTestId("evidence-export-ros-dossier");
  const [exportResponse] = await Promise.all([
    page.waitForResponse((response) => {
      if (response.request().method() !== "GET") {
        return false;
      }
      const pathname = new URL(response.url()).pathname;
      return pathname === `/api/app/reports/ros-coaf/${SEEDED_ROS_COAF_EVIDENCE.rosId}/regulatory-dossier`;
    }),
    exportButton.click()
  ]);

  if (!exportResponse.ok()) {
    throw new Error(`ros_coaf_dossier_export_failed:${exportResponse.status()}:${await exportResponse.text()}`);
  }

  const expectedHash = exportResponse.headers()["x-ontrack-dossier-sha256"]?.trim() ?? "";
  if (!expectedHash) {
    throw new Error("ros_coaf_dossier_export_missing_hash_header");
  }

  const expectedFilename =
    readDownloadFilenameFromHeaders(exportResponse.headers()) ||
    `ontrackchain-ros-coaf-regulatory-dossier-${SEEDED_ROS_COAF_EVIDENCE.rosId}.json`;

  for (let attempt = 0; attempt < 12; attempt += 1) {
    const detailContext = page.getByTestId("evidence-dossier-detail-context");
    const chainContext = page.getByTestId("evidence-chain-dossier-context");
    const hashContext = page.getByTestId("evidence-hash-context");
    const detailText = await detailContext.textContent().catch(() => "");
    const chainText = await chainContext.textContent().catch(() => "");
    const hashText = await hashContext.textContent().catch(() => "");
    if (
      detailText?.includes(expectedHash) &&
      detailText.includes(expectedFilename) &&
      chainText?.includes(expectedHash) &&
      chainText.includes(expectedFilename) &&
      hashText?.includes(expectedHash)
    ) {
      return { dossierSha256: expectedHash, filename: expectedFilename };
    }
    await page.waitForTimeout(250);
  }

  throw new Error(`ros_coaf_dossier_hash_not_rendered:${expectedHash}`);
}

export async function readManualPackageSealId(page: Page) {
  const auditGovernanceHref = await page
    .getByRole("link", { name: "Abrir governanca do selo na auditoria" })
    .getAttribute("href")
    .catch(() => null);
  if (auditGovernanceHref) {
    const resolvedHref = new URL(auditGovernanceHref, "http://127.0.0.1:3001");
    const sealId = resolvedHref.searchParams.get("seal_id")?.trim();
    if (sealId) {
      return sealId;
    }
  }

  const panelText = await page.getByTestId("evidence-manual-package-seal-panel").textContent();
  const pageText = await page.locator("body").textContent();
  const combinedText = `${panelText ?? ""}\n${pageText ?? ""}`;
  const match = combinedText.match(/seal[_ ]id[:\s]+([0-9a-f-]{36})/i);
  if (!match) {
    throw new Error("manual_package_seal_id_not_found");
  }
  return match[1];
}

export async function readManualPackageExportHash(page: Page) {
  const exportHashValue = page.getByTestId("evidence-manual-package-export-hash").locator(".otc-kv__value");
  await expect(exportHashValue).toContainText(/[a-f0-9]{64}/i);
  const exportHashText = await exportHashValue.textContent();
  const match = exportHashText?.match(/\b[a-f0-9]{64}\b/i);
  if (!match) {
    throw new Error("manual_package_export_hash_not_found");
  }
  return match[0];
}

async function exportManualPackageAndReadHash(page: Page) {
  const exportButton = page.getByTestId("evidence-export-manual-package");
  const previousHash = await readManualPackageExportHash(page).catch(() => "");
  const [exportResponse] = await Promise.all([
    page.waitForResponse(
      (response) =>
        response.request().method() === "POST" && new URL(response.url()).pathname === "/api/app/evidence/manual-package"
    ),
    exportButton.click()
  ]);

  if (!exportResponse.ok()) {
    throw new Error(`manual_package_export_failed:${exportResponse.status()}:${await exportResponse.text()}`);
  }

  const responseHash = exportResponse.headers()["x-ontrack-manual-package-sha256"]?.trim() ?? "";
  const expectedHash = /^[a-f0-9]{64}$/i.test(responseHash) ? responseHash : "";

  for (let attempt = 0; attempt < 12; attempt += 1) {
    const currentHash = await readManualPackageExportHash(page).catch(() => "");
    if (expectedHash && currentHash === expectedHash) {
      return currentHash;
    }
    if (!expectedHash && currentHash && currentHash !== previousHash) {
      return currentHash;
    }
    await page.waitForTimeout(250);
  }

  if (expectedHash) {
    throw new Error(`manual_package_export_hash_not_rendered:${expectedHash}`);
  }

  return readManualPackageExportHash(page);
}

export async function readEvidenceReportId(page: Page) {
  const detailsText = await page.getByTestId("evidence-details-panel").textContent();
  const match = detailsText?.match(/rep-showcase-[0-9]+/i);
  if (!match) {
    throw new Error("evidence_report_id_not_found");
  }
  return match[0];
}

export async function ensureManualPackageSealed(
  page: Page,
  request: APIRequestContext,
  requestId: string,
  ticketRef: string
) {
  const sealedNotice = page.getByTestId("evidence-manual-package-sealed-notice");
  const exportButton = page.getByTestId("evidence-export-manual-package");
  let packageSha256 = "";

  if (!(await sealedNotice.isVisible().catch(() => false)) && (await exportButton.isVisible().catch(() => false))) {
    packageSha256 = await exportManualPackageAndReadHash(page);
  }

  if (!(await sealedNotice.isVisible().catch(() => false))) {
    packageSha256 = packageSha256 || (await readManualPackageExportHash(page));
    const reportId = await readEvidenceReportId(page);
    const manualReviewAction = SEEDED_MANUAL_PACKAGE_ACTIONS[requestId];
    if (!manualReviewAction) {
      throw new Error(`unsupported_manual_package_request:${requestId}`);
    }

    const signoffRequestResponse = await request.post("/api/app/evidence/manual-package/signoff-requests", {
      data: {
        request_id: requestId,
        report_id: reportId,
        scope_id: requestId,
        manual_review_action: manualReviewAction,
        package_sha256: packageSha256,
        manifest_schema_version: "manual_review_package/v2",
        classification: "restricted_regulatory",
        signoff_mode: "compliance_ops_signoff",
        package_kind: "manual_review_package",
        policy_version: "manual_package_sealing/v1"
      }
    });
    if (!signoffRequestResponse.ok()) {
      throw new Error(`manual_package_signoff_request_failed:${signoffRequestResponse.status()}:${await signoffRequestResponse.text()}`);
    }
    const signoffRequestData = (await signoffRequestResponse.json()) as { seal_id?: string };
    if (!signoffRequestData.seal_id) {
      throw new Error("manual_package_signoff_request_missing_seal_id");
    }

    const sealId = signoffRequestData.seal_id;
    const signoffResponse = await request.post(`/api/app/evidence/manual-package/seals/${encodeURIComponent(sealId)}/signoffs`, {
      data: {
        decision: "approved",
        signer_role: "compliance_owner",
        signoff_method: "platform_authenticated_2fa",
        ticket_ref: ticketRef,
        notes: "Aprovacao automatizada do fluxo seeded de showcase.",
        signer_display_name: "Showcase Compliance Owner",
        metadata: {
          source: "showcase_e2e_segmented_suite"
        }
      }
    });
    if (!signoffResponse.ok()) {
      throw new Error(`manual_package_signoff_failed:${signoffResponse.status()}:${await signoffResponse.text()}`);
    }
    const signoffData = (await signoffResponse.json()) as { seal_id?: string; seal_status?: string } | null;
    let resolvedSealId = signoffData?.seal_id?.trim() || sealId;
    let resolvedSealStatus = signoffData?.seal_status?.trim() || "";

    if (resolvedSealStatus !== "ready_to_seal" && resolvedSealStatus !== "sealed") {
      for (let attempt = 0; attempt < 3; attempt += 1) {
        await page.waitForTimeout(250);
        const sealLookupResponse = await request.get(
          `/api/app/evidence/manual-package/seal?package_sha256=${encodeURIComponent(packageSha256)}&policy_version=${encodeURIComponent("manual_package_sealing/v1")}`
        );
        if (!sealLookupResponse.ok()) {
          continue;
        }
        const sealLookupData = (await sealLookupResponse.json()) as { seal_id?: string; seal_status?: string } | null;
        resolvedSealId = sealLookupData?.seal_id?.trim() || resolvedSealId;
        resolvedSealStatus = sealLookupData?.seal_status?.trim() || resolvedSealStatus;
        if (resolvedSealStatus === "ready_to_seal" || resolvedSealStatus === "sealed") {
          break;
        }
      }
    }

    if (resolvedSealStatus !== "ready_to_seal" && resolvedSealStatus !== "sealed") {
      throw new Error(`manual_package_signoff_not_ready:${resolvedSealId}:${resolvedSealStatus || "unknown"}`);
    }

    const finalizeResponse = await request.post(`/api/app/evidence/manual-package/seals/${encodeURIComponent(resolvedSealId)}/finalize`, {
      data: {
        metadata: {
          source: "showcase_e2e_segmented_suite",
          request_id: requestId
        }
      }
    });
    if (!finalizeResponse.ok()) {
      throw new Error(`manual_package_finalize_failed:${finalizeResponse.status()}:${await finalizeResponse.text()}`);
    }

    await openSeededEvidenceEvent(page, requestId);
  }

  await expect(sealedNotice).toBeVisible();
  await expect(page.getByTestId("evidence-manual-package-seal-panel")).toContainText("ECDSA_P256_SHA256");
  await expect(page.getByTestId("evidence-manual-package-seal-panel")).toContainText("Ontrackchain Showcase Trust Service");
}

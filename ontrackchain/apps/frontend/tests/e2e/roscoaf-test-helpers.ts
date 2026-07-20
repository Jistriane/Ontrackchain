import type { Page, Route } from "@playwright/test";

type SeedRosCoafOptions = {
  role?: string;
  linkedUserId?: string | null;
  mfaMode?: string;
  mfaProviderHomologated?: string;
  denyList?: boolean;
  denyDetail?: boolean;
  denyDossier?: boolean;
  denyWorkspace?: boolean;
};

export async function seedRosCoafPage(page: Page, options: SeedRosCoafOptions = {}) {
  const rosId = "33333333-3333-4333-8333-333333333333";
  const caseId = "33333333-3333-4333-8333-333333333334";
  const reportId = "rep-ros-01";
  const workItemId = "44444444-4444-4444-8444-444444444444";
  const {
    role = "COMPLIANCE_OFFICER",
    linkedUserId = "linked-user-e2e",
    mfaMode = "external_provider",
    mfaProviderHomologated = "true",
    denyList = false,
    denyDetail = denyList,
    denyDossier = denyDetail,
    denyWorkspace = false
  } = options;

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
        linked_user_id: linkedUserId,
        role,
        plan: "professional",
        auth_method: "dev_jwt",
        mfa_mode: mfaMode,
        mfa_provider_homologated: mfaProviderHomologated
      })
    });
  });

  await page.route("**/api/app/operations/work-items?module=ros_coaf&resource_type=ros_record&**", async (route: Route) => {
    if (denyWorkspace) {
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
            id: workItemId,
            module: "ros_coaf",
            resource_type: "ros_record",
            resource_id: rosId,
            case_id: caseId,
            report_external_id: reportId,
            owner_user_id: "linked-user-e2e",
            assigned_by_user_id: "linked-user-e2e",
            queue_status: "UNDER_REVIEW",
            priority: "high",
            due_at: "2026-07-04T15:30:00.000Z",
            note: "Handoff COAF pendente.",
            metadata: {
              ros_id: rosId,
              case_id: caseId,
              report_id: reportId,
              owner_label: "Compliance QA",
              workspace_status: "PENDING_APPROVAL",
              created_at: "2026-07-03T10:00:00.000Z"
            },
            last_activity_at: "2026-07-03T12:00:00.000Z",
            updated_at: "2026-07-03T12:00:00.000Z"
          }
        ]
      })
    });
  });

  await page.route("**/api/app/reports/ros-coaf?**", async (route: Route) => {
    if (denyList) {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "report_read_role_required" })
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        data: [
          {
            ros_id: rosId,
            case_id: caseId,
            status: "PENDING_APPROVAL",
            report_id: reportId,
            created_at: "2026-07-03T10:00:00.000Z",
            approved_at: null,
            submitted_at: null,
            coaf_protocol_number: "",
            coaf_receipt_hash: "",
            rejection_reason: "",
            approval_2fa_verified: false,
            submission_deadline: "2026-07-05T10:00:00.000Z",
            deadline_breached: false,
            last_activity_at: "2026-07-03T12:00:00.000Z"
          }
        ],
        page: 1,
        limit: 100,
        total: 1,
        has_more: false
      })
    });
  });

  await page.route("**/api/app/reports/ros-coaf/*/regulatory-dossier**", async (route: Route) => {
    if (denyDossier) {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "report_read_role_required" })
      });
      return;
    }

    await route.fulfill({
      status: 200,
      headers: {
        "content-type": "application/json",
        "content-disposition": `attachment; filename="ontrackchain-ros-coaf-regulatory-dossier-${rosId}.json"`,
        "x-ontrack-dossier-sha256": "a".repeat(64)
      },
      body: JSON.stringify({
        version: "v1",
        generated_at: "2026-07-03T12:00:00.000Z",
        dossier_sha256: "a".repeat(64),
        ros_record: { ros_id: rosId, audit: [] },
        work_item: { id: workItemId, module: "ros_coaf", resource_type: "ros_record", resource_id: rosId },
        work_events: [],
        work_comments: [],
        unified_timeline: []
      })
    });
  });

  await page.route("**/api/app/reports/ros-coaf/*", async (route: Route) => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith("/regulatory-dossier")) {
      await route.fallback();
      return;
    }
    if (denyDetail) {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "report_read_role_required" })
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ros_id: rosId,
        case_id: caseId,
        report_id: reportId,
        status: "PENDING_APPROVAL",
        tipologia_code: "COAF",
        tipologia_description: "Tipologia de teste",
        trigger_reason: "trigger",
        suspected_amount_brl: 123.45,
        suspected_address: "0x3333333333333333333333333333333333333333",
        suspected_chain: "ethereum",
        pdf_hash: "c".repeat(64),
        pdf_path: "/reports/roscoaf.pdf",
        generated_at: "2026-07-03T10:00:00.000Z",
        approved_at: null,
        submitted_at: null,
        approval_2fa_verified: false,
        rejection_reason: "",
        submission_deadline: "2026-07-05T10:00:00.000Z",
        deadline_breached: false,
        coaf_protocol_number: "",
        coaf_receipt_hash: "",
        evidence_hash: "d".repeat(64),
        evidence_trail_ref: "ref-ros-e2e",
        created_at: "2026-07-03T10:00:00.000Z",
        updated_at: "2026-07-03T12:00:00.000Z",
        retain_until: "2026-08-03T12:00:00.000Z",
        audit: [
          {
            id: "55555555-5555-4555-8555-555555555555",
            action: "coaf_report_generated",
            user_id: "linked-user-e2e",
            created_at: "2026-07-03T10:00:00.000Z",
            metadata: { report_id: reportId }
          },
          {
            id: "55555555-5555-4555-8555-555555555556",
            action: "coaf_regulatory_dossier_downloaded",
            user_id: "linked-user-e2e",
            created_at: "2026-07-03T12:00:00.000Z",
            metadata: {
              report_id: reportId,
              filename: `ontrackchain-ros-coaf-regulatory-dossier-${rosId}.json`,
              dossier_sha256: "a".repeat(64)
            }
          }
        ]
      })
    });
  });

  await page.route("**/api/app/operations/work-items/*/timeline", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        item: {
          id: workItemId,
          module: "ros_coaf",
          resource_type: "ros_record",
          resource_id: rosId,
          case_id: caseId,
          report_external_id: reportId,
          owner_user_id: "linked-user-e2e",
          assigned_by_user_id: "linked-user-e2e",
          queue_status: "UNDER_REVIEW",
          priority: "high",
          due_at: "2026-07-04T15:30:00.000Z",
          note: "Handoff COAF pendente.",
          metadata: {
            ros_id: rosId,
            case_id: caseId,
            report_id: reportId,
            owner_label: "Compliance QA",
            workspace_status: "PENDING_APPROVAL"
          },
          last_activity_at: "2026-07-03T12:00:00.000Z",
          updated_at: "2026-07-03T12:00:00.000Z"
        },
        events: [
          {
            id: "66666666-6666-4666-8666-666666666666",
            event_type: "STATUS_CHANGED",
            from_status: "UNDER_REVIEW",
            to_status: "READY",
            actor_user_id: "linked-user-e2e",
            payload: { ros_id: rosId, report_id: reportId },
            created_at: "2026-07-03T11:00:00.000Z"
          }
        ],
        comments: [
          {
            id: "77777777-7777-4777-8777-777777777777",
            comment_type: "handoff",
            actor_user_id: "linked-user-e2e",
            body: "Submissão manual pendente de validação.",
            created_at: "2026-07-03T11:30:00.000Z"
          }
        ]
      })
    });
  });

  return { rosId, caseId, reportId, workItemId };
}

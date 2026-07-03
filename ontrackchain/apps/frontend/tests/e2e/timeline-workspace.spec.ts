import { expect, test, type Page } from "@playwright/test";

type TimelineFixture = {
  workItemId: string;
  pagePath: string;
  timelineSummary: RegExp;
  setupPageRoutes: (page: Page) => Promise<void>;
};

type MutableTimelineState = {
  comments: Array<{
    id: string;
    comment_type: "note" | "decision" | "handoff";
    actor_user_id: string | null;
    body: string;
    created_at: string;
  }>;
  lastCommentPayload: { comment_type: string; body: string } | null;
};

function buildTimelineState() {
  return {
    comments: [
      {
        id: "comment-seed-1",
        comment_type: "note" as const,
        actor_user_id: "qa-user",
        body: "comentario inicial de handoff",
        created_at: "2026-07-02T12:00:00.000Z"
      }
    ],
    lastCommentPayload: null
  } satisfies MutableTimelineState;
}

async function registerTimelineRoutes(page: Page, fixture: TimelineFixture, state: MutableTimelineState) {
  await page.route("**/api/app/operations/work-items/*/timeline", async (route) => {
    const url = route.request().url();
    if (!url.includes(`/${fixture.workItemId}/timeline`)) {
      await route.continue();
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        item: {
          id: fixture.workItemId,
          resource_id: fixture.workItemId,
          queue_status: "UNDER_REVIEW",
          priority: "high",
          due_at: null,
          note: null,
          metadata: {},
          last_activity_at: "2026-07-02T12:00:00.000Z",
          updated_at: "2026-07-02T12:00:00.000Z"
        },
        events: [
          {
            id: "event-seed-1",
            event_type: "STATUS_CHANGED",
            from_status: "UNDER_REVIEW",
            to_status: "ESCALATED",
            actor_user_id: "qa-user",
            payload: { owner: "Compliance QA" },
            created_at: "2026-07-02T12:00:00.000Z"
          }
        ],
        comments: state.comments
      })
    });
  });

  await page.route("**/api/app/operations/work-items/*/comments", async (route) => {
    const url = route.request().url();
    if (!url.includes(`/${fixture.workItemId}/comments`)) {
      await route.continue();
      return;
    }

    const payload = (route.request().postDataJSON() ?? {}) as { comment_type?: string; body?: string };
    state.lastCommentPayload = {
      comment_type: payload.comment_type ?? "",
      body: payload.body ?? ""
    };
    const createdComment = {
      id: `comment-${state.comments.length + 1}`,
      comment_type: (payload.comment_type === "decision" || payload.comment_type === "handoff" ? payload.comment_type : "note") as
        | "note"
        | "decision"
        | "handoff",
      actor_user_id: "qa-user",
      body: payload.body ?? "",
      created_at: "2026-07-02T12:05:00.000Z"
    };
    state.comments = [...state.comments, createdComment];

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(createdComment)
    });
  });
}

const timelineFixtures: TimelineFixture[] = [
  {
    workItemId: "11111111-1111-4111-8111-111111111111",
    pagePath: "/counterparties",
    timelineSummary: /Hist.rico operacional de Counterparty QA/i,
    setupPageRoutes: async (page) => {
      await page.route("**/api/app/compliance/counterparties?**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ items: [], total: 0 })
        });
      });
      await page.route("**/api/app/operations/work-items?**", async (route) => {
        const url = route.request().url();
        if (url.includes("module=counterparties")) {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              data: [
                {
                  id: "11111111-1111-4111-8111-111111111111",
                  resource_id: "22222222-2222-4222-8222-222222222222",
                  queue_status: "UNDER_REVIEW",
                  priority: "high",
                  due_at: "2026-07-05T18:00:00.000Z",
                  note: "seed",
                  metadata: {
                    counterparty_id: "22222222-2222-4222-8222-222222222222",
                    legal_name: "Counterparty QA",
                    counterparty_type: "CLIENTE_PJ",
                    document_type: "CNPJ",
                    document_number: "12345678000190",
                    wallet_chain: "ethereum",
                    wallet_address: "0x1111111111111111111111111111111111111111",
                    wallet_label: "treasury",
                    risk_level: 72,
                    kyc_status: "APPROVED",
                    sanctions_cleared: true,
                    is_pep: false,
                    enhanced_dd_required: false,
                    next_review_date: "2026-12-31T00:00:00.000Z",
                    status: "ACTIVE",
                    created_at: "2026-07-02T12:00:00.000Z",
                    case_id: "33333333-3333-4333-8333-333333333333",
                    owner_label: "Compliance QA",
                    local_workspace_status: "UNDER_REVIEW",
                    note: "seed"
                  },
                  last_activity_at: "2026-07-02T12:00:00.000Z",
                  updated_at: "2026-07-02T12:00:00.000Z"
                }
              ]
            })
          });
          return;
        }
        await route.continue();
      });
    }
  },
  {
    workItemId: "44444444-4444-4444-8444-444444444444",
    pagePath: "/reports?case_id=55555555-5555-4555-8555-555555555555",
    timelineSummary: /Hist.rico operacional do caso 55555555-5555-4555-8555-555555555555/i,
    setupPageRoutes: async (page) => {
      await page.route("**/api/app/report-types?**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ generated_at: "2026-07-02T12:00:00.000Z", types: [] })
        });
      });
      await page.route("**/api/app/reports/list?**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            data: [
              {
                report_id: "rep-seed-001",
                case_id: "55555555-5555-4555-8555-555555555555",
                report_type_requested: "coaf",
                report_type: "coaf_ready_report",
                content_type: "application/pdf",
                file_hash_sha256: "a".repeat(64),
                onchain_hash: null,
                created_at: "2026-07-02T12:00:00.000Z",
                has_download_audit: false
              }
            ],
            page: 1,
            limit: 20,
            total: 1,
            has_more: false
          })
        });
      });
      await page.route("**/api/app/investigation/cases?**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ page: 1, limit: 20, data: [] })
        });
      });
      await page.route("**/api/app/operations/work-items?**", async (route) => {
        const url = route.request().url();
        if (url.includes("module=reports")) {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              data: [
                {
                  id: "44444444-4444-4444-8444-444444444444",
                  resource_id: "55555555-5555-4555-8555-555555555555",
                  queue_status: "UNDER_REVIEW",
                  priority: "high",
                  due_at: "2026-07-05T18:00:00.000Z",
                  note: "seed",
                  metadata: {
                    case_id: "55555555-5555-4555-8555-555555555555",
                    target_address: "0x2222222222222222222222222222222222222222",
                    target_chain: "ethereum",
                    report_type: "coaf_ready_report",
                    owner_label: "Compliance QA",
                    local_workspace_status: "in_review",
                    note: "seed"
                  },
                  last_activity_at: "2026-07-02T12:00:00.000Z",
                  updated_at: "2026-07-02T12:00:00.000Z"
                }
              ]
            })
          });
          return;
        }
        await route.continue();
      });
    }
  },
  {
    workItemId: "66666666-6666-4666-8666-666666666666",
    pagePath: "/ros-coaf",
    timelineSummary: /Hist.rico operacional de 77777777-7777-4777-8777-777777777777/i,
    setupPageRoutes: async (page) => {
      await page.route("**/api/app/operations/work-items?**", async (route) => {
        const url = route.request().url();
        if (url.includes("module=ros_coaf")) {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              data: [
                {
                  id: "66666666-6666-4666-8666-666666666666",
                  resource_id: "77777777-7777-4777-8777-777777777777",
                  queue_status: "UNDER_REVIEW",
                  priority: "high",
                  due_at: "2026-07-05T18:00:00.000Z",
                  note: "",
                  metadata: {
                    ros_id: "77777777-7777-4777-8777-777777777777",
                    case_id: "88888888-8888-4888-8888-888888888888",
                    owner_label: "Compliance QA",
                    ros_status: "APPROVED",
                    report_id: "99999999-9999-4999-8999-999999999999",
                    created_at: "2026-07-02T12:00:00.000Z",
                    approved_at: "2026-07-02T12:01:00.000Z",
                    submitted_at: "",
                    coaf_protocol_number: "",
                    coaf_receipt_hash: ""
                  },
                  last_activity_at: "2026-07-02T12:00:00.000Z",
                  updated_at: "2026-07-02T12:00:00.000Z"
                }
              ]
            })
          });
          return;
        }
        await route.continue();
      });
    }
  },
  {
    workItemId: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    pagePath: "/evidence",
    timelineSummary: /Hist.rico operacional do evento bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb/i,
    setupPageRoutes: async (page) => {
      await page.route("**/api/app/audit/logs?**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            data: [],
            page: 1,
            count: 0,
            limit: 50,
            total: 0,
            total_pages: 1,
            has_more: false,
            filters: {}
          })
        });
      });
      await page.route("**/api/app/operations/work-items?**", async (route) => {
        const url = route.request().url();
        if (url.includes("module=evidence")) {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              data: [
                {
                  id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                  resource_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                  queue_status: "UNDER_REVIEW",
                  priority: "high",
                  due_at: "2026-07-05T18:00:00.000Z",
                  note: "seed",
                  metadata: {
                    event_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                    audit_action: "report_downloaded",
                    audit_resource_type: "report",
                    audit_resource_id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                    case_id: "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
                    request_id: "req-timeline-e2e",
                    report_id: "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
                    file_hash_sha256: "hash-seed",
                    owner_label: "Compliance QA",
                    local_workspace_status: "reviewing",
                    note: "seed"
                  },
                  last_activity_at: "2026-07-02T12:00:00.000Z",
                  updated_at: "2026-07-02T12:00:00.000Z"
                }
              ]
            })
          });
          return;
        }
        await route.continue();
      });
    }
  }
];

test.describe("timeline operacional compartilhada", () => {
  for (const fixture of timelineFixtures) {
    test(`${fixture.pagePath} carrega timeline local e persiste comentario`, async ({ page }) => {
      const state = buildTimelineState();
      await fixture.setupPageRoutes(page);
      await registerTimelineRoutes(page, fixture, state);
      await page.goto(fixture.pagePath);

      await expect(page.getByTestId("work-item-timeline-panel")).toBeVisible();
      await expect(page.getByTestId("work-item-timeline-summary")).toContainText(fixture.timelineSummary);
      await expect(page.getByTestId("work-item-timeline-comment").first()).toContainText("comentario inicial de handoff");
      await expect(page.getByTestId("work-item-timeline-event").first()).toContainText("STATUS_CHANGED: UNDER_REVIEW -> ESCALATED");

      await page.getByTestId("work-item-timeline-comment-body").fill("");
      await page.getByTestId("work-item-timeline-comment-save").click();
      await expect(page.getByTestId("work-item-timeline-error")).toContainText(/Preencha o coment.rio/i);
      expect(state.lastCommentPayload).toBeNull();

      await page.getByTestId("work-item-timeline-comment-type").selectOption("handoff");
      await page.getByTestId("work-item-timeline-comment-body").fill("novo comentario playwright");
      await page.getByTestId("work-item-timeline-comment-save").click();

      await expect(page.getByTestId("work-item-timeline-comment").last()).toContainText("novo comentario playwright");
      expect(state.lastCommentPayload).toEqual({
        comment_type: "handoff",
        body: "novo comentario playwright"
      });
    });
  }
});

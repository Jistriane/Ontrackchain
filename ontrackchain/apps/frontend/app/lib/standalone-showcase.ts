import type { WorkCommentResponse, WorkEventResponse, WorkItemTimelineResponse } from "./work-item-timeline";
import type { ReportWorkItemMetadata, WorkItemListResponse, WorkItemResponse } from "./work-items";

export const STANDALONE_SHOWCASE_AUTH_CONTEXT = {
  authenticated: true,
  org_id: "showcase-org",
  user_id: "showcase-user",
  linked_user_id: "showcase-user",
  role: "ADMIN",
  plan: "enterprise",
  auth_method: "jwt",
  mfa_mode: "external_provider",
  mfa_provider_homologated: "true",
  two_factor: "managed_externally_homologated"
} as const;

export type ShowcaseTeamRole =
  | "ADMIN"
  | "ANALYST"
  | "AUDITOR"
  | "VIEWER"
  | "REVIEWER"
  | "COMPLIANCE_OFFICER"
  | "LEGAL_REVIEWER"
  | "BILLING_ADMIN";

export type ShowcaseTeamStatus = "active" | "invited" | "disabled";

export type ShowcaseTeamMemberRecord = {
  member_id: string;
  name: string;
  email: string;
  role: ShowcaseTeamRole;
  status: ShowcaseTeamStatus;
  note: string;
  created_at: string;
  updated_at: string;
  linked_identity_count: number;
  last_identity_seen_at: string | null;
};

export type ShowcaseTeamExternalIdentityRecord = {
  provider: string;
  external_subject: string;
  email_snapshot?: string | null;
  role_snapshot?: string | null;
  created_at: string;
  last_seen_at?: string | null;
};

export type ShowcaseFederatedDirectoryUserRecord = {
  provider: string;
  external_subject: string;
  email?: string | null;
  username?: string | null;
  organization_id?: string | null;
  role_snapshot?: string | null;
  enabled: boolean;
  match_status: string;
  linked_user_id?: string | null;
  linked_user_email?: string | null;
  role_validation_status: string;
  warnings: string[];
};

type ShowcaseFederatedSuggestionResponse = {
  can_link: boolean;
  match_reason: string;
  org_match: boolean;
  email_match: boolean;
  provider: string;
  external_subject: string;
  candidate_email: string | null;
  candidate_username: string | null;
  candidate_org: string | null;
  role_snapshot: string | null;
  role_validation_status: string;
  linked_user_id: string | null;
  linked_user_email: string | null;
  warnings: string[];
};

export const STANDALONE_SHOWCASE_HOME_CATALOGS = {
  reportTypes: {
    plan: "enterprise",
    total: 2,
    generated_at: "2026-07-15T22:00:00Z",
    note_deprecated: "showcase_seed",
    types: [
      {
        canonical: "technical_basic",
        label: "Due diligence técnica",
        description: "Investigação inicial multi-chain para triagem e priorização.",
        cost_credits: 24,
        available: true,
        upgrade_required: null,
        min_plan: "starter",
        aliases_accepted: ["wallet_risk", "tech_due_diligence"],
        deprecated_aliases: [],
        chains_supported: ["ethereum", "polygon", "arbitrum", "base"],
        avg_duration_seconds: 95,
        output_format: "pdf",
        regulatory_reference: null,
        tags: ["investigation", "risk", "showcase"]
      },
      {
        canonical: "legal_report",
        label: "Relatório formal regulatório",
        description: "Dossiê formal para auditoria, jurídico e governança interna.",
        cost_credits: 68,
        available: true,
        upgrade_required: null,
        min_plan: "professional",
        aliases_accepted: ["formal_dossier"],
        deprecated_aliases: [],
        chains_supported: ["ethereum", "polygon", "bitcoin"],
        avg_duration_seconds: 180,
        output_format: "pdf",
        regulatory_reference: "COAF",
        tags: ["reports", "legal", "showcase"]
      }
    ]
  },
  complianceOperations: {
    plan: "enterprise",
    total: 2,
    generated_at: "2026-07-15T22:00:00Z",
    note_deprecated: "showcase_seed",
    operations: [
      {
        canonical: "sanctions_check",
        label: "Sanctions Check",
        description: "Triagem em bases sancionatórias e listas restritivas.",
        cost_credits: 12,
        available: true,
        upgrade_required: null,
        min_plan: "starter",
        aliases_accepted: [],
        deprecated_aliases: [],
        chains_supported: ["ethereum", "polygon", "bitcoin"],
        avg_duration_seconds: 45,
        output_format: "json",
        regulatory_reference: "OFAC/ONU",
        tags: ["compliance", "screening", "showcase"]
      },
      {
        canonical: "source_of_funds",
        label: "Source of Funds",
        description: "Análise visual do fluxo de recursos e justificativas operacionais.",
        cost_credits: 36,
        available: true,
        upgrade_required: null,
        min_plan: "professional",
        aliases_accepted: [],
        deprecated_aliases: [],
        chains_supported: ["ethereum", "arbitrum", "base"],
        avg_duration_seconds: 130,
        output_format: "json",
        regulatory_reference: null,
        tags: ["compliance", "funds", "showcase"]
      }
    ]
  },
  monitoringOperations: {
    plan: "enterprise",
    total: 2,
    generated_at: "2026-07-15T22:00:00Z",
    note_deprecated: "showcase_seed",
    operations: [
      {
        canonical: "watchlist_monitoring",
        label: "Watchlist Monitoring",
        description: "Observabilidade contínua com alertas e filtros operacionais.",
        cost_credits: 9,
        available: true,
        upgrade_required: null,
        min_plan: "starter",
        aliases_accepted: [],
        deprecated_aliases: [],
        chains_supported: ["ethereum", "polygon", "base"],
        avg_duration_seconds: 15,
        output_format: "json",
        regulatory_reference: null,
        tags: ["monitoring", "alerts", "showcase"]
      },
      {
        canonical: "platform_alert_triage",
        label: "Platform Alert Triage",
        description: "Triagem visual de alertas globais e work items correlatos.",
        cost_credits: 18,
        available: true,
        upgrade_required: null,
        min_plan: "professional",
        aliases_accepted: [],
        deprecated_aliases: [],
        chains_supported: ["ethereum", "polygon"],
        avg_duration_seconds: 30,
        output_format: "json",
        regulatory_reference: null,
        tags: ["monitoring", "triage", "showcase"]
      }
    ]
  }
} as const;

export const STANDALONE_SHOWCASE_DASHBOARD = {
  watchlistsCount: 12,
  creditsAvailable: 1840,
  creditsReserved: 210,
  creditsUsedTotal: 9620,
  orgActive: 6,
  orgLimit: 12,
  queuedCount: 14,
  processingCount: 4,
  firingPendingAlertsTotal: 3,
  recentCases: [
    {
      case_id: "case-showcase-001",
      status: "completed",
      target_address: "0x6b175474e89094c44da98b954eedeac495271d0f",
      target_chain: "ethereum",
      created_at: "2026-07-14T10:15:00Z",
      completed_at: "2026-07-14T10:24:00Z",
      queue_state: "completed",
      last_error: null,
      attempt_count: 1,
      report_type_canonical: "technical_basic",
      charged_cost: 24,
      duration_ms: 540000
    },
    {
      case_id: "case-showcase-002",
      status: "processing",
      target_address: "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
      target_chain: "bitcoin",
      created_at: "2026-07-15T08:40:00Z",
      completed_at: null,
      queue_state: "processing",
      last_error: null,
      attempt_count: 1,
      report_type_canonical: "legal_report",
      charged_cost: 68,
      duration_ms: null
    },
    {
      case_id: "case-showcase-003",
      status: "queued",
      target_address: "0x4200000000000000000000000000000000000006",
      target_chain: "base",
      created_at: "2026-07-15T09:05:00Z",
      completed_at: null,
      queue_state: "queued",
      last_error: null,
      attempt_count: 0,
      report_type_canonical: "source_of_funds",
      charged_cost: 36,
      duration_ms: null
    }
  ]
} as const;

export const STANDALONE_SHOWCASE_CASES = [
  {
    id: "case-showcase-001",
    status: "completed",
    target_address: "0x6b175474e89094c44da98b954eedeac495271d0f",
    target_chain: "ethereum",
    created_at: "2026-07-14T10:15:00Z",
    completed_at: "2026-07-14T10:24:00Z"
  },
  {
    id: "case-showcase-002",
    status: "processing",
    target_address: "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    target_chain: "bitcoin",
    created_at: "2026-07-15T08:40:00Z",
    completed_at: null
  },
  {
    id: "case-showcase-003",
    status: "queued",
    target_address: "0x4200000000000000000000000000000000000006",
    target_chain: "base",
    created_at: "2026-07-15T09:05:00Z",
    completed_at: null
  }
] as const;

export const STANDALONE_SHOWCASE_REPORT_HISTORY = [
  {
    report_id: "rep-showcase-001",
    case_id: "case-showcase-001",
    report_type_requested: "technical_basic",
    report_type: "technical_basic",
    content_type: "application/pdf",
    file_hash_sha256: "f4b79e0a4ca8ec4ba5ff0b473acdb7d2ccfca9a2f7d6a654df6f33ce2eb1f150",
    onchain_hash: "0xf4b79e0a4ca8ec4ba5ff0b473acdb7d2ccfca9a2f7d6a654df6f33ce2eb1f150",
    created_at: "2026-07-14T10:24:00Z",
    has_download_audit: true
  },
  {
    report_id: "rep-showcase-002",
    case_id: "case-showcase-002",
    report_type_requested: "legal_report",
    report_type: "legal_report",
    content_type: "application/pdf",
    file_hash_sha256: "9a9380d4f2f37ce5be779dd111b97d95d9fe5cdaeb34b483fbb3e4088ff5e8f4",
    onchain_hash: null,
    created_at: "2026-07-15T08:55:00Z",
    has_download_audit: false
  }
] as const;

const STANDALONE_SHOWCASE_WORK_ITEM_SEEDS: WorkItemResponse<ReportWorkItemMetadata>[] = [
  {
    id: "6f0d6a9d-76c4-57d2-8f41-41272e7b0a11",
    module: "reports",
    resource_type: "formal_report_case",
    resource_id: "case-showcase-001",
    case_id: "case-showcase-001",
    report_external_id: "rep-showcase-001",
    owner_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    assigned_by_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    queue_status: "READY",
    priority: "high",
    due_at: "2026-07-16T18:00:00Z",
    sla_breached: false,
    title: "Formal report case • case-showcase-001",
    note: "Caso seeded para showcase compartilhado de relatórios.",
    metadata: {
      case_id: "case-showcase-001",
      owner_label: "showcase-user",
      owner_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      workspace_status: "ready",
      local_workspace_status: "ready",
      target_address: "0x6b175474e89094c44da98b954eedeac495271d0f",
      target_chain: "ethereum",
      report_type: "technical_basic",
      report_id: "rep-showcase-001",
      note: "Caso seeded para showcase compartilhado de relatórios."
    },
    created_at: "2026-07-15T19:05:00Z",
    updated_at: "2026-07-15T19:20:00Z",
    last_activity_at: "2026-07-15T19:20:00Z"
  }
];

const STANDALONE_SHOWCASE_TIMELINE_EVENT_SEEDS: Record<string, WorkEventResponse[]> = {
  "6f0d6a9d-76c4-57d2-8f41-41272e7b0a11": [
    {
      id: "evt-showcase-reports-001",
      event_type: "WORK_ITEM_CREATED",
      from_status: null,
      to_status: "UNDER_REVIEW",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: { source: "standalone_showcase_seed" },
      created_at: "2026-07-15T19:05:00Z"
    },
    {
      id: "evt-showcase-reports-002",
      event_type: "WORK_ITEM_STATUS_CHANGED",
      from_status: "UNDER_REVIEW",
      to_status: "READY",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: { workspace_status: "ready" },
      created_at: "2026-07-15T19:20:00Z"
    }
  ]
};

const STANDALONE_SHOWCASE_TIMELINE_COMMENT_SEEDS: Record<string, WorkCommentResponse[]> = {
  "6f0d6a9d-76c4-57d2-8f41-41272e7b0a11": [
    {
      id: "cmt-showcase-reports-001",
      comment_type: "note",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      body: "Work item compartilhado seeded para demonstrar timeline e comentários persistidos localmente.",
      created_at: "2026-07-15T19:10:00Z"
    },
    {
      id: "cmt-showcase-reports-002",
      comment_type: "handoff",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      body: "Handoff demonstrativo para revisão jurídica do dossiê formal.",
      created_at: "2026-07-15T19:18:00Z"
    }
  ]
};

let standaloneShowcaseWorkItemsStore = STANDALONE_SHOWCASE_WORK_ITEM_SEEDS.map((item) => ({
  ...item,
  metadata: { ...item.metadata }
}));
let standaloneShowcaseTimelineEventsStore = Object.fromEntries(
  Object.entries(STANDALONE_SHOWCASE_TIMELINE_EVENT_SEEDS).map(([workItemId, events]) => [
    workItemId,
    events.map((event) => ({ ...event, payload: { ...event.payload } }))
  ])
) as Record<string, WorkEventResponse[]>;
let standaloneShowcaseTimelineCommentsStore = Object.fromEntries(
  Object.entries(STANDALONE_SHOWCASE_TIMELINE_COMMENT_SEEDS).map(([workItemId, comments]) => [
    workItemId,
    comments.map((comment) => ({ ...comment }))
  ])
) as Record<string, WorkCommentResponse[]>;

const STANDALONE_SHOWCASE_TEAM_MEMBER_SEEDS: ShowcaseTeamMemberRecord[] = [
  {
    member_id: "team-showcase-admin-01",
    name: "Alice Admin",
    email: "admin@ontrackchain.local",
    role: "ADMIN",
    status: "active",
    note: "Responsável pela governança do tenant no showcase standalone.",
    created_at: "2026-07-15T18:20:00Z",
    updated_at: "2026-07-15T19:10:00Z",
    linked_identity_count: 1,
    last_identity_seen_at: "2026-07-15T19:05:00Z"
  },
  {
    member_id: "team-showcase-compliance-01",
    name: "Carla Compliance",
    email: "compliance@ontrackchain.local",
    role: "COMPLIANCE_OFFICER",
    status: "active",
    note: "Lead operacional de triagem e revisão de contrapartes.",
    created_at: "2026-07-15T18:25:00Z",
    updated_at: "2026-07-15T18:55:00Z",
    linked_identity_count: 0,
    last_identity_seen_at: null
  },
  {
    member_id: "team-showcase-reviewer-01",
    name: "Rafa Reviewer",
    email: "reviewer@ontrackchain.local",
    role: "REVIEWER",
    status: "invited",
    note: "Perfil convidado para revisão cruzada e evidências.",
    created_at: "2026-07-15T18:40:00Z",
    updated_at: "2026-07-15T18:40:00Z",
    linked_identity_count: 0,
    last_identity_seen_at: null
  }
];

const STANDALONE_SHOWCASE_TEAM_EXTERNAL_IDENTITY_SEEDS: Record<string, ShowcaseTeamExternalIdentityRecord[]> = {
  "team-showcase-admin-01": [
    {
      provider: "keycloak",
      external_subject: "kc-showcase-admin-01",
      email_snapshot: "admin@ontrackchain.local",
      role_snapshot: "ADMIN",
      created_at: "2026-07-15T18:30:00Z",
      last_seen_at: "2026-07-15T19:05:00Z"
    }
  ],
  "team-showcase-compliance-01": [],
  "team-showcase-reviewer-01": []
};

const STANDALONE_SHOWCASE_FEDERATED_DIRECTORY_SEEDS: ShowcaseFederatedDirectoryUserRecord[] = [
  {
    provider: "keycloak",
    external_subject: "kc-showcase-admin-01",
    email: "admin@ontrackchain.local",
    username: "alice.admin",
    organization_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.org_id,
    role_snapshot: "ADMIN",
    enabled: true,
    match_status: "linked",
    linked_user_id: "team-showcase-admin-01",
    linked_user_email: "admin@ontrackchain.local",
    role_validation_status: "valid",
    warnings: ["candidate_already_linked_to_member"]
  },
  {
    provider: "keycloak",
    external_subject: "kc-showcase-compliance-01",
    email: "compliance@ontrackchain.local",
    username: "carla.compliance",
    organization_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.org_id,
    role_snapshot: "COMPLIANCE_OFFICER",
    enabled: true,
    match_status: "suggested",
    linked_user_id: null,
    linked_user_email: null,
    role_validation_status: "valid",
    warnings: []
  },
  {
    provider: "keycloak",
    external_subject: "kc-showcase-review-01",
    email: "review.partner@external.local",
    username: "review.partner",
    organization_id: "foreign-org",
    role_snapshot: null,
    enabled: true,
    match_status: "org_match_only",
    linked_user_id: null,
    linked_user_email: null,
    role_validation_status: "missing",
    warnings: ["candidate_org_mismatch", "candidate_role_missing", "candidate_email_mismatch"]
  }
];

let standaloneShowcaseTeamMembersStore = STANDALONE_SHOWCASE_TEAM_MEMBER_SEEDS.map((member) => ({ ...member }));
let standaloneShowcaseTeamExternalIdentitiesStore = Object.fromEntries(
  Object.entries(STANDALONE_SHOWCASE_TEAM_EXTERNAL_IDENTITY_SEEDS).map(([memberId, identities]) => [
    memberId,
    identities.map((identity) => ({ ...identity }))
  ])
) as Record<string, ShowcaseTeamExternalIdentityRecord[]>;
let standaloneShowcaseFederatedDirectoryStore = STANDALONE_SHOWCASE_FEDERATED_DIRECTORY_SEEDS.map((candidate) => ({ ...candidate }));

export function buildStandaloneShowcaseQuote(input: {
  address: string;
  chains?: string[];
  report_type?: string;
}) {
  const chain = input.chains?.[0] ?? "ethereum";
  const reportType = input.report_type?.trim() || "technical_basic";
  const catalogEntry = STANDALONE_SHOWCASE_HOME_CATALOGS.reportTypes.types.find((item) => item.canonical === reportType);
  const totalCredits = catalogEntry?.cost_credits ?? 24;
  return {
    quote_id: `quote-${reportType}-${chain}`,
    total_credits: totalCredits,
    address: input.address.trim(),
    chains: [chain],
    report_type: reportType,
    addons: [],
    mode: "standalone_showcase",
    expires_at: "2026-07-15T23:59:59Z"
  } as const;
}

export function buildStandaloneShowcaseGeneratedReport(input: { caseId: string; reportType: string }) {
  return {
    report_id: `rep-${input.caseId}-${input.reportType}`,
    created_at: "2026-07-15T22:30:00Z",
    report_type: input.reportType,
    file_hash_sha256: "7e3344272f2f1b2e22fce9c0d3108a3f1df14a0b9937cc12f5a39bfe9b9fdf12",
    content_type: "application/pdf"
  } as const;
}

export function resolveStandaloneShowcaseCase(caseId: string) {
  return STANDALONE_SHOWCASE_CASES.find((item) => item.id === caseId) ?? null;
}

export function resolveStandaloneShowcaseReport(reportId: string) {
  return STANDALONE_SHOWCASE_REPORT_HISTORY.find((item) => item.report_id === reportId) ?? null;
}

function cloneStandaloneWorkItem(item: WorkItemResponse<ReportWorkItemMetadata>): WorkItemResponse<ReportWorkItemMetadata> {
  return {
    ...item,
    metadata: { ...item.metadata }
  };
}

function ensureStandaloneWorkItemCollections(workItemId: string) {
  if (!standaloneShowcaseTimelineEventsStore[workItemId]) {
    standaloneShowcaseTimelineEventsStore[workItemId] = [];
  }
  if (!standaloneShowcaseTimelineCommentsStore[workItemId]) {
    standaloneShowcaseTimelineCommentsStore[workItemId] = [];
  }
}

export function listStandaloneShowcaseWorkItems(filters: {
  module?: string | null;
  resourceType?: string | null;
  reportExternalId?: string | null;
  limit?: number | null;
}): WorkItemListResponse<ReportWorkItemMetadata> {
  const filtered = standaloneShowcaseWorkItemsStore.filter((item) => {
    if (filters.module && item.module !== filters.module) return false;
    if (filters.resourceType && item.resource_type !== filters.resourceType) return false;
    if (filters.reportExternalId && item.report_external_id !== filters.reportExternalId) return false;
    return true;
  });
  const limit = typeof filters.limit === "number" && filters.limit > 0 ? filters.limit : 100;
  const data = filtered
    .slice()
    .sort((left, right) => right.last_activity_at.localeCompare(left.last_activity_at))
    .slice(0, limit)
    .map(cloneStandaloneWorkItem);
  return {
    data,
    page: 1,
    limit,
    total: filtered.length,
    has_more: filtered.length > limit
  };
}

export function getStandaloneShowcaseWorkItem(workItemId: string) {
  const workItem = standaloneShowcaseWorkItemsStore.find((item) => item.id === workItemId) ?? null;
  return workItem ? cloneStandaloneWorkItem(workItem) : null;
}

export function upsertStandaloneShowcaseWorkItem(
  payload: Partial<WorkItemResponse<ReportWorkItemMetadata>> & {
    module?: "reports";
    resource_type?: "formal_report_case";
    resource_id?: string;
    case_id?: string | null;
    report_external_id?: string | null;
    priority: "critical" | "high" | "normal";
    queue_status: WorkItemResponse["queue_status"];
    due_at: string | null;
    title: string;
    note: string | null;
    metadata: ReportWorkItemMetadata;
  },
  workItemId?: string
) {
  const now = new Date().toISOString();
  const existingIndex = workItemId ? standaloneShowcaseWorkItemsStore.findIndex((item) => item.id === workItemId) : -1;
  const existing = existingIndex >= 0 ? standaloneShowcaseWorkItemsStore[existingIndex] : null;
  const resolvedId = existing?.id ?? workItemId ?? crypto.randomUUID();
  const nextItem: WorkItemResponse<ReportWorkItemMetadata> = {
    id: resolvedId,
    module: "reports",
    resource_type: "formal_report_case",
    resource_id: payload.resource_id ?? payload.case_id ?? existing?.resource_id ?? resolvedId,
    case_id: payload.case_id ?? existing?.case_id ?? null,
    report_external_id: payload.report_external_id ?? existing?.report_external_id ?? null,
    owner_user_id: payload.owner_user_id ?? existing?.owner_user_id ?? STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    assigned_by_user_id: existing?.assigned_by_user_id ?? STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    queue_status: payload.queue_status,
    priority: payload.priority,
    due_at: payload.due_at,
    sla_breached: payload.sla_breached ?? existing?.sla_breached ?? false,
    title: payload.title,
    note: payload.note,
    metadata: { ...payload.metadata },
    created_at: existing?.created_at ?? now,
    updated_at: now,
    last_activity_at: now
  };

  if (existingIndex >= 0) {
    standaloneShowcaseWorkItemsStore[existingIndex] = nextItem;
  } else {
    standaloneShowcaseWorkItemsStore = [nextItem, ...standaloneShowcaseWorkItemsStore];
  }

  ensureStandaloneWorkItemCollections(resolvedId);
  standaloneShowcaseTimelineEventsStore[resolvedId] = [
    ...standaloneShowcaseTimelineEventsStore[resolvedId],
    {
      id: crypto.randomUUID(),
      event_type: existing ? "WORK_ITEM_UPDATED" : "WORK_ITEM_CREATED",
      from_status: existing?.queue_status ?? null,
      to_status: nextItem.queue_status,
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: {
        workspace_status: nextItem.metadata.workspace_status ?? null,
        report_id: nextItem.report_external_id ?? null
      },
      created_at: now
    }
  ];

  return cloneStandaloneWorkItem(nextItem);
}

export function getStandaloneShowcaseWorkItemTimeline(
  workItemId: string
): WorkItemTimelineResponse<WorkItemResponse<ReportWorkItemMetadata>> | null {
  const item = getStandaloneShowcaseWorkItem(workItemId);
  if (!item) {
    return null;
  }
  ensureStandaloneWorkItemCollections(workItemId);
  return {
    item,
    events: standaloneShowcaseTimelineEventsStore[workItemId].map((event) => ({ ...event, payload: { ...event.payload } })),
    comments: standaloneShowcaseTimelineCommentsStore[workItemId].map((comment) => ({ ...comment }))
  };
}

export function createStandaloneShowcaseWorkItemComment(
  workItemId: string,
  payload: Pick<WorkCommentResponse, "comment_type" | "body">
) {
  const item = getStandaloneShowcaseWorkItem(workItemId);
  if (!item) {
    return null;
  }
  ensureStandaloneWorkItemCollections(workItemId);
  const now = new Date().toISOString();
  const comment: WorkCommentResponse = {
    id: crypto.randomUUID(),
    comment_type: payload.comment_type,
    actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    body: payload.body.trim(),
    created_at: now
  };
  standaloneShowcaseTimelineCommentsStore[workItemId] = [...standaloneShowcaseTimelineCommentsStore[workItemId], comment];
  standaloneShowcaseTimelineEventsStore[workItemId] = [
    ...standaloneShowcaseTimelineEventsStore[workItemId],
    {
      id: crypto.randomUUID(),
      event_type: "COMMENT_ADDED",
      from_status: null,
      to_status: null,
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: { comment_type: payload.comment_type },
      created_at: now
    }
  ];
  standaloneShowcaseWorkItemsStore = standaloneShowcaseWorkItemsStore.map((entry) =>
    entry.id === workItemId ? { ...entry, updated_at: now, last_activity_at: now, metadata: { ...entry.metadata } } : entry
  );
  return { ...comment };
}

function cloneShowcaseTeamMember(member: ShowcaseTeamMemberRecord): ShowcaseTeamMemberRecord {
  return { ...member };
}

function cloneShowcaseExternalIdentity(
  identity: ShowcaseTeamExternalIdentityRecord
): ShowcaseTeamExternalIdentityRecord {
  return { ...identity };
}

function cloneShowcaseFederatedCandidate(
  candidate: ShowcaseFederatedDirectoryUserRecord
): ShowcaseFederatedDirectoryUserRecord {
  return { ...candidate, warnings: [...candidate.warnings] };
}

function getShowcaseMemberIndex(memberId: string) {
  return standaloneShowcaseTeamMembersStore.findIndex((member) => member.member_id === memberId);
}

function ensureShowcaseMemberIdentityCollection(memberId: string) {
  if (!standaloneShowcaseTeamExternalIdentitiesStore[memberId]) {
    standaloneShowcaseTeamExternalIdentitiesStore[memberId] = [];
  }
}

function recomputeShowcaseMemberIdentitySummary(memberId: string) {
  ensureShowcaseMemberIdentityCollection(memberId);
  const identities = standaloneShowcaseTeamExternalIdentitiesStore[memberId];
  const lastSeenAt = identities
    .map((identity) => identity.last_seen_at || identity.created_at)
    .filter(Boolean)
    .sort((left, right) => right.localeCompare(left))[0] ?? null;
  const memberIndex = getShowcaseMemberIndex(memberId);
  if (memberIndex < 0) {
    return null;
  }
  const current = standaloneShowcaseTeamMembersStore[memberIndex];
  const nextMember: ShowcaseTeamMemberRecord = {
    ...current,
    linked_identity_count: identities.length,
    last_identity_seen_at: lastSeenAt,
    updated_at: new Date().toISOString()
  };
  standaloneShowcaseTeamMembersStore[memberIndex] = nextMember;
  return cloneShowcaseTeamMember(nextMember);
}

function syncShowcaseFederatedDirectoryLinkState(
  member: ShowcaseTeamMemberRecord,
  identity: Pick<ShowcaseTeamExternalIdentityRecord, "provider" | "external_subject">
) {
  standaloneShowcaseFederatedDirectoryStore = standaloneShowcaseFederatedDirectoryStore.map((candidate) => {
    if (candidate.provider === identity.provider && candidate.external_subject === identity.external_subject) {
      return {
        ...candidate,
        linked_user_id: member.member_id,
        linked_user_email: member.email,
        match_status: "linked",
        warnings: ["candidate_already_linked_to_member"]
      };
    }
    return candidate;
  });
}

function clearShowcaseFederatedDirectoryLinkState(identity: Pick<ShowcaseTeamExternalIdentityRecord, "provider" | "external_subject">) {
  standaloneShowcaseFederatedDirectoryStore = standaloneShowcaseFederatedDirectoryStore.map((candidate) => {
    if (candidate.provider === identity.provider && candidate.external_subject === identity.external_subject) {
      return {
        ...candidate,
        linked_user_id: null,
        linked_user_email: null,
        match_status: candidate.organization_id === STANDALONE_SHOWCASE_AUTH_CONTEXT.org_id ? "suggested" : "org_match_only",
        warnings:
          candidate.organization_id === STANDALONE_SHOWCASE_AUTH_CONTEXT.org_id
            ? []
            : ["candidate_org_mismatch", "candidate_role_missing", "candidate_email_mismatch"]
      };
    }
    return candidate;
  });
}

export function listStandaloneShowcaseTeamMembers() {
  return {
    data: standaloneShowcaseTeamMembersStore
      .slice()
      .sort((left, right) => right.updated_at.localeCompare(left.updated_at))
      .map(cloneShowcaseTeamMember)
  };
}

export function createStandaloneShowcaseTeamMember(input: {
  name?: string;
  email: string;
  role?: ShowcaseTeamRole;
  status?: ShowcaseTeamStatus;
  note?: string;
}) {
  const now = new Date().toISOString();
  const member: ShowcaseTeamMemberRecord = {
    member_id: crypto.randomUUID(),
    name: input.name?.trim() || input.email.trim().toLowerCase(),
    email: input.email.trim().toLowerCase(),
    role: input.role ?? "ANALYST",
    status: input.status ?? "invited",
    note: input.note?.trim() ?? "",
    created_at: now,
    updated_at: now,
    linked_identity_count: 0,
    last_identity_seen_at: null
  };
  standaloneShowcaseTeamMembersStore = [member, ...standaloneShowcaseTeamMembersStore];
  ensureShowcaseMemberIdentityCollection(member.member_id);
  return cloneShowcaseTeamMember(member);
}

export function updateStandaloneShowcaseTeamMember(
  memberId: string,
  patch: Partial<Pick<ShowcaseTeamMemberRecord, "name" | "email" | "role" | "status" | "note">>
) {
  const memberIndex = getShowcaseMemberIndex(memberId);
  if (memberIndex < 0) {
    return null;
  }
  const current = standaloneShowcaseTeamMembersStore[memberIndex];
  const nextMember: ShowcaseTeamMemberRecord = {
    ...current,
    name: patch.name !== undefined ? patch.name.trim() || current.name : current.name,
    email: patch.email !== undefined ? patch.email.trim().toLowerCase() || current.email : current.email,
    role: patch.role ?? current.role,
    status: patch.status ?? current.status,
    note: patch.note !== undefined ? patch.note.trim() : current.note,
    updated_at: new Date().toISOString()
  };
  standaloneShowcaseTeamMembersStore[memberIndex] = nextMember;
  return cloneShowcaseTeamMember(nextMember);
}

export function listStandaloneShowcaseExternalIdentities(memberId: string) {
  ensureShowcaseMemberIdentityCollection(memberId);
  return {
    data: standaloneShowcaseTeamExternalIdentitiesStore[memberId].map(cloneShowcaseExternalIdentity)
  };
}

export function linkStandaloneShowcaseExternalIdentity(
  memberId: string,
  payload: {
    provider: string;
    external_subject: string;
    email_snapshot?: string | null;
    role_snapshot?: string | null;
  }
) {
  const member = standaloneShowcaseTeamMembersStore.find((entry) => entry.member_id === memberId) ?? null;
  if (!member) {
    return null;
  }
  ensureShowcaseMemberIdentityCollection(memberId);
  const now = new Date().toISOString();
  const identity: ShowcaseTeamExternalIdentityRecord = {
    provider: payload.provider.trim().toLowerCase(),
    external_subject: payload.external_subject.trim(),
    email_snapshot: payload.email_snapshot?.trim() || null,
    role_snapshot: payload.role_snapshot?.trim() || null,
    created_at: now,
    last_seen_at: null
  };
  const nextIdentities = [
    identity,
    ...standaloneShowcaseTeamExternalIdentitiesStore[memberId].filter(
      (entry) => !(entry.provider === identity.provider && entry.external_subject === identity.external_subject)
    )
  ];
  standaloneShowcaseTeamExternalIdentitiesStore[memberId] = nextIdentities;
  const nextMember = recomputeShowcaseMemberIdentitySummary(memberId);
  if (nextMember) {
    syncShowcaseFederatedDirectoryLinkState(nextMember, identity);
  }
  return nextMember;
}

export function unlinkStandaloneShowcaseExternalIdentity(
  memberId: string,
  payload: {
    provider: string;
    external_subject: string;
  }
) {
  const member = standaloneShowcaseTeamMembersStore.find((entry) => entry.member_id === memberId) ?? null;
  if (!member) {
    return null;
  }
  ensureShowcaseMemberIdentityCollection(memberId);
  standaloneShowcaseTeamExternalIdentitiesStore[memberId] = standaloneShowcaseTeamExternalIdentitiesStore[memberId].filter(
    (entry) => !(entry.provider === payload.provider.trim().toLowerCase() && entry.external_subject === payload.external_subject.trim())
  );
  const nextMember = recomputeShowcaseMemberIdentitySummary(memberId);
  clearShowcaseFederatedDirectoryLinkState({
    provider: payload.provider.trim().toLowerCase(),
    external_subject: payload.external_subject.trim()
  });
  return nextMember;
}

export function searchStandaloneShowcaseFederatedDirectory(filters: { query?: string | null; limit?: number | null }) {
  const query = filters.query?.trim().toLowerCase() ?? "";
  const limit = typeof filters.limit === "number" && filters.limit > 0 ? filters.limit : 20;
  const filtered = standaloneShowcaseFederatedDirectoryStore.filter((candidate) => {
    if (!query) {
      return true;
    }
    return [candidate.email, candidate.username, candidate.external_subject, candidate.linked_user_email]
      .filter((value): value is string => Boolean(value))
      .some((value) => value.toLowerCase().includes(query));
  });
  return {
    data: filtered.slice(0, limit).map(cloneShowcaseFederatedCandidate)
  };
}

export function evaluateStandaloneShowcaseFederatedSuggestion(input: {
  member_id?: string;
  provider?: string;
  external_subject?: string;
}): ShowcaseFederatedSuggestionResponse | null {
  const member = standaloneShowcaseTeamMembersStore.find((entry) => entry.member_id === input.member_id) ?? null;
  const candidate =
    standaloneShowcaseFederatedDirectoryStore.find(
      (entry) => entry.provider === input.provider?.trim().toLowerCase() && entry.external_subject === input.external_subject?.trim()
    ) ?? null;
  if (!member || !candidate) {
    return null;
  }

  const orgMatch = candidate.organization_id === STANDALONE_SHOWCASE_AUTH_CONTEXT.org_id;
  const emailMatch = (candidate.email?.trim().toLowerCase() ?? "") === member.email.trim().toLowerCase();
  const roleSnapshot = candidate.role_snapshot?.trim() || null;
  const warnings = [...candidate.warnings];

  let canLink = true;
  let matchReason = "ready";

  if (candidate.linked_user_id && candidate.linked_user_id !== member.member_id) {
    canLink = false;
    matchReason = "already_linked";
    if (!warnings.includes("candidate_already_linked")) {
      warnings.unshift("candidate_already_linked");
    }
  } else if (!orgMatch) {
    canLink = false;
    matchReason = "org_mismatch";
    if (!warnings.includes("candidate_org_mismatch")) {
      warnings.unshift("candidate_org_mismatch");
    }
  } else if (!candidate.email) {
    canLink = false;
    matchReason = "email_missing";
    if (!warnings.includes("candidate_email_missing")) {
      warnings.unshift("candidate_email_missing");
    }
  } else if (!emailMatch) {
    canLink = false;
    matchReason = "email_mismatch";
    if (!warnings.includes("candidate_email_mismatch")) {
      warnings.unshift("candidate_email_mismatch");
    }
  } else if (!roleSnapshot) {
    canLink = false;
    matchReason = "role_missing";
    if (!warnings.includes("candidate_role_missing")) {
      warnings.unshift("candidate_role_missing");
    }
  } else if (roleSnapshot !== member.role) {
    canLink = false;
    matchReason = "role_mismatch";
    if (!warnings.includes("candidate_role_mismatch")) {
      warnings.unshift("candidate_role_mismatch");
    }
  }

  return {
    can_link: canLink,
    match_reason: matchReason,
    org_match: orgMatch,
    email_match: emailMatch,
    provider: candidate.provider,
    external_subject: candidate.external_subject,
    candidate_email: candidate.email ?? null,
    candidate_username: candidate.username ?? null,
    candidate_org: candidate.organization_id ?? null,
    role_snapshot: roleSnapshot,
    role_validation_status: candidate.role_validation_status,
    linked_user_id: candidate.linked_user_id ?? null,
    linked_user_email: candidate.linked_user_email ?? null,
    warnings
  };
}

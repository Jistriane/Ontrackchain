import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { AuditLogEntry, AuditLogsResponse } from "./audit-log";
import {
  buildEvidenceManualPackageAuditMetadata,
  buildEvidenceManualPackageDocument,
  buildEvidenceManualPackageManifest,
  buildManualReviewPackageFilename,
  finalizeEvidenceManualPackageDocument,
  type EvidenceManualPackagePayload
} from "./evidence-manual-package";
import type { ManualPackageSeal, ManualPackageSealSignoff } from "./manual-package-seal";
import type { WorkCommentResponse, WorkEventResponse, WorkItemTimelineResponse } from "./work-item-timeline";
import type { Alert, Watchlist, WatchlistItem } from "./monitoring-api";
import type { DlqSnapshot } from "./monitoring-dlq";
import type { OperationsSnapshot, OperationalAlertsSnapshot } from "./monitoring-investigation-operations";
import type {
  PlatformAlertExportFormat,
  PlatformAlertFilterState,
  PlatformOperationalAlertFilterOptions,
  PlatformOperationalAlertsSnapshot
} from "./monitoring-platform-alerts";
import type {
  BlocksWorkItemMetadata,
  CounterpartyWorkItemMetadata,
  EvidenceWorkItemMetadata,
  ReportWorkItemMetadata,
  RosCoafWorkItemMetadata,
  SanctionsWorkItemMetadata,
  WorkItemListResponse,
  WorkItemResponse
} from "./work-items";

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

export const STANDALONE_SHOWCASE_REPORT_HISTORY: Array<{
  report_id: string;
  case_id: string | null;
  report_type_requested: string;
  report_type: string;
  content_type: string;
  file_hash_sha256: string | null;
  onchain_hash: string | null;
  created_at: string;
  has_download_audit: boolean;
}> = [
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
  },
  {
    report_id: "rep-showcase-003",
    case_id: "case-showcase-002",
    report_type_requested: "coaf_ready_report",
    report_type: "coaf_ready_report",
    content_type: "application/pdf",
    file_hash_sha256: "4f8d86d1d8dd7a32d8f7f86d7b219b7f3f95e351ee8e0f38d7fd0ce93f37b8b5",
    onchain_hash: null,
    created_at: "2026-07-15T18:42:00Z",
    has_download_audit: true
  }
];

type ShowcaseSanctionsCheckResponse = {
  address: string;
  chain: string;
  provider: string;
  provider_status: "live" | "degraded";
  degraded_reason?: string | null;
  capability_status: "live" | "degraded";
  lists: string[];
  hit?: boolean | null;
  matched_lists: string[];
  entity_name?: string | null;
  designation_date?: string | null;
  checked_at: string;
};

type ShowcaseBlockEvaluateResponse = {
  address: string;
  chain: string;
  action: string;
  requires_coaf_report: boolean;
  decision_confidence: number;
  regulatory_basis: string[];
  matched_lists: string[];
  evidence_hash?: string | null;
  block_id?: string | null;
  screened_at: string;
};

type ShowcaseBlockLiftResponse = {
  block_id: string;
  status: string;
  review_status: string;
  lifted_at: string;
};

type ShowcaseEvidenceBundle = {
  mode: "standalone_showcase";
  request: {
    format: string;
    request_id: string | null;
    action: string | null;
    resource_type: string | null;
    report_id: string | null;
    resource_id: string | null;
    limit: number;
    include_audit_logs: boolean;
    include_credit_ledger: boolean;
    include_reports: boolean;
  };
  export_generated_at: string;
  audit_logs: AuditLogEntry[];
  credit_ledger: Array<Record<string, unknown>>;
  reports: Array<Record<string, unknown>>;
};

type ShowcaseRosCoafListItem = {
  ros_id: string;
  case_id: string | null;
  status: string;
  report_id: string;
  created_at: string;
  approved_at: string | null;
  submitted_at: string | null;
  coaf_protocol_number: string;
  coaf_receipt_hash: string;
  rejection_reason: string;
  approval_2fa_verified: boolean;
  submission_deadline: string | null;
  deadline_breached: boolean;
  last_activity_at: string;
};

type ShowcaseRosCoafAuditEntry = {
  id: string;
  action: string;
  user_id: string | null;
  created_at: string;
  metadata: Record<string, unknown>;
};

type ShowcaseRosCoafDetail = ShowcaseRosCoafListItem & {
  tipologia_code: string;
  tipologia_description: string;
  trigger_reason: string;
  suspected_amount_brl: number | null;
  suspected_address: string;
  suspected_chain: string;
  pdf_hash: string;
  pdf_path: string;
  generated_at: string | null;
  evidence_hash: string;
  evidence_trail_ref: string;
  updated_at: string;
  retain_until: string;
  audit: ShowcaseRosCoafAuditEntry[];
};

type ShowcaseRosCoafGenerateResponse = {
  ros_id: string;
  report_id: string;
  report_type: string;
  status: string;
  created_at: string;
  file_hash_sha256: string;
  content_type: string;
};

type ShowcaseRosCoafApproveResponse = {
  ros_id: string;
  status: string;
  approved_at: string;
  approval_2fa_verified: boolean;
};

type ShowcaseRosCoafSubmitResponse = {
  ros_id: string;
  status: string;
  submitted_at: string;
  coaf_protocol_number: string;
  coaf_receipt_hash: string;
};

type ShowcaseWorkItemMetadata =
  | ReportWorkItemMetadata
  | CounterpartyWorkItemMetadata
  | SanctionsWorkItemMetadata
  | BlocksWorkItemMetadata
  | EvidenceWorkItemMetadata
  | RosCoafWorkItemMetadata;
type ShowcaseWorkItemRecord = WorkItemResponse<ShowcaseWorkItemMetadata>;

const STANDALONE_SHOWCASE_WORK_ITEM_SEEDS: ShowcaseWorkItemRecord[] = [
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
  },
  {
    id: "8b4aa5f0-2967-5d59-8dc0-8f37f4e75961",
    module: "counterparties",
    resource_type: "counterparty",
    resource_id: "22222222-2222-4222-8222-222222222222",
    case_id: "33333333-3333-4333-8333-333333333333",
    owner_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    assigned_by_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    queue_status: "UNDER_REVIEW",
    priority: "high",
    due_at: "2026-07-18T18:00:00Z",
    sla_breached: false,
    title: "Counterparty review • Atlas OTC Desk",
    note: "Contraparte seeded para demonstrar onboarding regulatório e workspace compartilhado.",
    metadata: {
      case_id: "33333333-3333-4333-8333-333333333333",
      owner_label: "showcase-user",
      owner_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      workspace_status: "UNDER_REVIEW",
      local_workspace_status: "UNDER_REVIEW",
      counterparty_id: "22222222-2222-4222-8222-222222222222",
      legal_name: "Atlas OTC Desk",
      counterparty_type: "PARCEIRO_COMERCIAL",
      document_type: "CNPJ",
      document_number: "12.345.678/0001-90",
      wallet_chain: "ethereum",
      wallet_address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
      wallet_label: "primary treasury",
      risk_level: 4,
      kyc_status: "PENDING",
      sanctions_cleared: false,
      is_pep: false,
      enhanced_dd_required: true,
      next_review_date: "2026-08-10T00:00:00Z",
      status: "UNDER_REVIEW",
      created_at: "2026-07-15T17:40:00Z",
      dd_review_status: "in_progress",
      dd_review_note: "Pending SoF evidence for high-volume OTC corridor.",
      sof_description: "Capital de giro próprio com reforço documental em coleta.",
      sof_document_ref: "SOF-ATLAS-2026-001",
      note: "Contraparte seeded para demonstrar onboarding regulatório e workspace compartilhado."
    },
    created_at: "2026-07-15T17:45:00Z",
    updated_at: "2026-07-15T18:20:00Z",
    last_activity_at: "2026-07-15T18:20:00Z"
  },
  {
    id: "a5c82378-7e1a-54d0-9785-1c4d0379d4c1",
    module: "sanctions",
    resource_type: "sanctions_screening",
    resource_id: "0f58c5fa-3d28-5f7f-a9f3-1ad6bb2d4e31",
    case_id: "case-showcase-002",
    report_external_id: "rep-showcase-002",
    owner_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    assigned_by_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    queue_status: "UNDER_REVIEW",
    priority: "critical",
    due_at: "2026-07-16T12:00:00Z",
    sla_breached: false,
    title: "Sanctions HIT • 0x8ba1f109551bD432803012645Ac136ddd64DBA72",
    note: "Hit seeded para demonstrar screening, triagem e navegação operacional no showcase.",
    metadata: {
      case_id: "case-showcase-002",
      local_case_id: "case-showcase-002",
      owner_label: "showcase-user",
      owner_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      workspace_status: "UNDER_REVIEW",
      local_workspace_status: "UNDER_REVIEW",
      workspace_id: "sanctions:0x8ba1f109551bD432803012645Ac136ddd64DBA72:ethereum:2026-07-15T18:26:00Z",
      address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
      chain: "ethereum",
      lists: ["OFAC", "UN", "EU", "COAF"],
      provider: "Chainalysis KYT Showcase",
      provider_status: "live",
      capability_status: "live",
      degraded_reason: "",
      matched_lists: ["OFAC", "EU"],
      hit: true,
      entity_name: "Atlas OTC Desk",
      designation_date: "2025-11-20T00:00:00Z",
      checked_at: "2026-07-15T18:26:00Z",
      triage_note: "Hit seeded para demonstrar screening, triagem e navegação operacional no showcase.",
      note: "Hit seeded para demonstrar screening, triagem e navegação operacional no showcase."
    },
    created_at: "2026-07-15T18:26:00Z",
    updated_at: "2026-07-15T18:31:00Z",
    last_activity_at: "2026-07-15T18:31:00Z"
  },
  {
    id: "c4d8dd9b-262b-5d32-840d-f9ec4f12ee89",
    module: "blocks",
    resource_type: "preventive_block",
    resource_id: "bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f",
    case_id: "case-showcase-002",
    report_external_id: "rep-showcase-002",
    owner_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    assigned_by_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    queue_status: "UNDER_REVIEW",
    priority: "critical",
    due_at: "2026-07-16T14:00:00Z",
    sla_breached: false,
    title: "Preventive block • 0x8ba1f109551bD432803012645Ac136ddd64DBA72",
    note: "Bloqueio preventivo seeded para demonstrar decisão, lift e trilha compartilhada.",
    metadata: {
      case_id: "case-showcase-002",
      local_case_id: "case-showcase-002",
      owner_label: "showcase-user",
      owner_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      workspace_status: "BLOCKED",
      local_workspace_status: "BLOCKED",
      local_block_status: "BLOCKED",
      workspace_id: "bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f",
      address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
      chain: "ethereum",
      entity_name: "Atlas OTC Desk",
      entity_document: "12.345.678/0001-90",
      action: "BLOCK",
      requires_coaf_report: true,
      decision_confidence: 0.94,
      regulatory_basis: [
        "OFAC SDN match with corroborated counterparty context",
        "Internal policy OTC-HIGH-RISK-07"
      ],
      matched_lists: ["OFAC", "EU"],
      evidence_hash: "2fb8b4823d65c11274f0e95ad1f20ee0be79b86d5f16e34f96cbe8c8fb7a9c32",
      block_id: "bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f",
      screened_at: "2026-07-15T18:35:00Z",
      lifted_at: "",
      lift_reason: "",
      note: "Bloqueio preventivo seeded para demonstrar decisão, lift e trilha compartilhada."
    },
    created_at: "2026-07-15T18:35:00Z",
    updated_at: "2026-07-15T18:38:00Z",
    last_activity_at: "2026-07-15T18:38:00Z"
  },
  {
    id: "f17b41c9-f5a7-5ec2-b970-511c4fd0b14b",
    module: "ros_coaf",
    resource_type: "ros_record",
    resource_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
    case_id: "case-showcase-002",
    report_external_id: "rep-showcase-003",
    owner_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    assigned_by_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    queue_status: "SUBMITTED",
    priority: "critical",
    due_at: "2026-07-16T09:00:00Z",
    sla_breached: false,
    title: "ROS/COAF • 7c4dca53-5806-564f-91ba-ef5487dbf6ce",
    note: "Recibo seeded para demonstrar submissao manual auditavel no showcase.",
    metadata: {
      case_id: "case-showcase-002",
      owner_label: "showcase-user",
      owner_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      workspace_status: "SUBMITTED_MANUAL",
      ros_status: "SUBMITTED_MANUAL",
      ros_phase: "submitted",
      ros_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
      report_id: "rep-showcase-003",
      created_at: "2026-07-15T18:42:00Z",
      approved_at: "2026-07-15T18:47:00Z",
      approval_2fa_verified: true,
      submitted_at: "2026-07-15T18:55:00Z",
      coaf_protocol_number: "COAF-2026-000184",
      coaf_receipt_hash: "4fcd0bdfe7f42dcd765358f8f582d7a35f992f64a3e8f53d651f44af4e5ba328",
      rejection_reason: ""
    },
    created_at: "2026-07-15T18:42:00Z",
    updated_at: "2026-07-15T18:55:00Z",
    last_activity_at: "2026-07-15T18:55:00Z"
  },
  {
    id: "7d4a7d2f-42f0-59f6-9335-75e4b33e5161",
    module: "evidence",
    resource_type: "evidence_event",
    resource_id: "audit-showcase-dd-export-001",
    case_id: "case-showcase-002",
    report_external_id: "rep-showcase-003",
    owner_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    assigned_by_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    queue_status: "UNDER_REVIEW",
    priority: "high",
    due_at: "2026-07-16T10:00:00Z",
    sla_breached: false,
    title: "Evidence manual package • req-showcase-dd-001",
    note: "Pacote manual seeded para trilha regulatoria de due diligence no showcase.",
    metadata: {
      event_id: "audit-showcase-dd-export-001",
      audit_action: "evidence_manual_review_package_exported",
      audit_resource_type: "audit_log",
      audit_resource_id: "audit-showcase-dd-export-001",
      request_id: "req-showcase-dd-001",
      report_id: "rep-showcase-003",
      file_hash_sha256: "91e49bb8a644f40d938c9334f50fca6e84bd828278dbaf3df881723b0d7f5eb3",
      provider: "Ontrackchain DD Showcase",
      provider_status: "degraded",
      degraded_reason: "manual_review_required",
      capability_status: "degraded",
      delivery_mode: "manual_review_pending",
      requires_human_review: true,
      counterparty_context_present: true,
      counterparty_context: "Atlas OTC Desk flagged during enhanced due diligence.",
      manual_review_action: "compliance_due_diligence_checked",
      package_sha256: "91e49bb8a644f40d938c9334f50fca6e84bd828278dbaf3df881723b0d7f5eb3",
      filename: "ontrackchain-manual-review-due-diligence-req-showcase-dd-001.json",
      workspace_status: "reviewing",
      local_workspace_status: "reviewing",
      note: "Pacote manual seeded para trilha regulatoria de due diligence no showcase."
    },
    created_at: "2026-07-15T19:26:00Z",
    updated_at: "2026-07-15T19:31:00Z",
    last_activity_at: "2026-07-15T19:31:00Z"
  },
  {
    id: "9a96176a-a97d-5dce-a7cf-77b9c2d4f0de",
    module: "evidence",
    resource_type: "evidence_event",
    resource_id: "audit-showcase-sof-001",
    case_id: "case-showcase-002",
    report_external_id: "rep-showcase-003",
    owner_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    assigned_by_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    queue_status: "UNDER_REVIEW",
    priority: "high",
    due_at: "2026-07-16T10:30:00Z",
    sla_breached: false,
    title: "Evidence manual package • req-showcase-sof-001",
    note: "Workspace seeded para trilha regulatoria de source of funds no showcase.",
    metadata: {
      event_id: "audit-showcase-sof-001",
      audit_action: "compliance_source_of_funds_checked",
      audit_resource_type: "address",
      audit_resource_id: "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
      request_id: "req-showcase-sof-001",
      report_id: "rep-showcase-003",
      file_hash_sha256: "4cd72d6a8f9fc5b58debb42d67f2f6871775c2cda4ff7e5814ac1cbfc8cdf44a",
      provider: "Ontrackchain SoF Showcase",
      provider_status: "degraded",
      degraded_reason: "manual_review_required",
      capability_status: "degraded",
      delivery_mode: "manual_review_pending",
      requires_human_review: true,
      purpose: "Cross-border OTC settlement",
      manual_review_action: "compliance_source_of_funds_checked",
      workspace_status: "reviewing",
      local_workspace_status: "reviewing",
      note: "Workspace seeded para trilha regulatoria de source of funds no showcase."
    },
    created_at: "2026-07-15T19:18:00Z",
    updated_at: "2026-07-15T19:24:00Z",
    last_activity_at: "2026-07-15T19:24:00Z"
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
  ],
  "8b4aa5f0-2967-5d59-8dc0-8f37f4e75961": [
    {
      id: "evt-showcase-counterparty-001",
      event_type: "WORK_ITEM_CREATED",
      from_status: null,
      to_status: "UNDER_REVIEW",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: { source: "standalone_showcase_seed", counterparty_id: "22222222-2222-4222-8222-222222222222" },
      created_at: "2026-07-15T17:45:00Z"
    },
    {
      id: "evt-showcase-counterparty-002",
      event_type: "DD_REVIEW_UPDATED",
      from_status: "UNDER_REVIEW",
      to_status: "UNDER_REVIEW",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: { dd_review_status: "in_progress", sof_document_ref: "SOF-ATLAS-2026-001" },
      created_at: "2026-07-15T18:20:00Z"
    }
  ],
  "a5c82378-7e1a-54d0-9785-1c4d0379d4c1": [
    {
      id: "evt-showcase-sanctions-001",
      event_type: "WORK_ITEM_CREATED",
      from_status: null,
      to_status: "UNDER_REVIEW",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: {
        source: "standalone_showcase_seed",
        matched_lists: ["OFAC", "EU"],
        screening_result: "hit"
      },
      created_at: "2026-07-15T18:26:00Z"
    },
    {
      id: "evt-showcase-sanctions-002",
      event_type: "SANCTIONS_HIT_TRIAGED",
      from_status: "UNDER_REVIEW",
      to_status: "UNDER_REVIEW",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: {
        triage_note: "Escalar para bloqueio preventivo e ROS/COAF se confirmado.",
        provider: "Chainalysis KYT Showcase"
      },
      created_at: "2026-07-15T18:31:00Z"
    }
  ],
  "c4d8dd9b-262b-5d32-840d-f9ec4f12ee89": [
    {
      id: "evt-showcase-blocks-001",
      event_type: "WORK_ITEM_CREATED",
      from_status: null,
      to_status: "UNDER_REVIEW",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: {
        source: "standalone_showcase_seed",
        block_id: "bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f"
      },
      created_at: "2026-07-15T18:35:00Z"
    },
    {
      id: "evt-showcase-blocks-002",
      event_type: "BLOCK_DECISION_RECORDED",
      from_status: "UNDER_REVIEW",
      to_status: "BLOCKED",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: {
        action: "BLOCK",
        requires_coaf_report: true
      },
      created_at: "2026-07-15T18:38:00Z"
    }
  ],
  "f17b41c9-f5a7-5ec2-b970-511c4fd0b14b": [
    {
      id: "evt-showcase-ros-001",
      event_type: "WORK_ITEM_CREATED",
      from_status: null,
      to_status: "UNDER_REVIEW",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: {
        source: "standalone_showcase_seed",
        ros_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
        report_id: "rep-showcase-003"
      },
      created_at: "2026-07-15T18:42:00Z"
    },
    {
      id: "evt-showcase-ros-002",
      event_type: "COAF_REPORT_APPROVED",
      from_status: "UNDER_REVIEW",
      to_status: "APPROVED",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: {
        ros_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
        approval_2fa_verified: true
      },
      created_at: "2026-07-15T18:47:00Z"
    },
    {
      id: "evt-showcase-ros-003",
      event_type: "COAF_REPORT_SUBMITTED_MANUAL",
      from_status: "APPROVED",
      to_status: "SUBMITTED",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: {
        ros_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
        coaf_protocol_number: "COAF-2026-000184"
      },
      created_at: "2026-07-15T18:55:00Z"
    }
  ],
  "7d4a7d2f-42f0-59f6-9335-75e4b33e5161": [
    {
      id: "evt-showcase-evidence-001",
      event_type: "WORK_ITEM_CREATED",
      from_status: null,
      to_status: "UNDER_REVIEW",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: {
        source: "standalone_showcase_seed",
        request_id: "req-showcase-dd-001",
        package_sha256: "91e49bb8a644f40d938c9334f50fca6e84bd828278dbaf3df881723b0d7f5eb3"
      },
      created_at: "2026-07-15T19:26:00Z"
    },
    {
      id: "evt-showcase-evidence-002",
      event_type: "MANUAL_PACKAGE_EXPORTED",
      from_status: "UNDER_REVIEW",
      to_status: "UNDER_REVIEW",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: {
        manual_review_action: "compliance_due_diligence_checked",
        filename: "ontrackchain-manual-review-due-diligence-req-showcase-dd-001.json"
      },
      created_at: "2026-07-15T19:31:00Z"
    }
  ],
  "9a96176a-a97d-5dce-a7cf-77b9c2d4f0de": [
    {
      id: "evt-showcase-evidence-sof-001",
      event_type: "WORK_ITEM_CREATED",
      from_status: null,
      to_status: "UNDER_REVIEW",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: {
        source: "standalone_showcase_seed",
        request_id: "req-showcase-sof-001",
        review_mode: "manual_review_pending"
      },
      created_at: "2026-07-15T19:18:00Z"
    },
    {
      id: "evt-showcase-evidence-sof-002",
      event_type: "SOURCE_OF_FUNDS_REVIEW_UPDATED",
      from_status: "UNDER_REVIEW",
      to_status: "UNDER_REVIEW",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: {
        purpose: "Cross-border OTC settlement",
        provider: "Ontrackchain SoF Showcase"
      },
      created_at: "2026-07-15T19:24:00Z"
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
  ],
  "8b4aa5f0-2967-5d59-8dc0-8f37f4e75961": [
    {
      id: "cmt-showcase-counterparty-001",
      comment_type: "note",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      body: "Seed regulatório com DD em andamento para demonstrar revisão, workspace e timeline.",
      created_at: "2026-07-15T18:05:00Z"
    }
  ],
  "a5c82378-7e1a-54d0-9785-1c4d0379d4c1": [
    {
      id: "cmt-showcase-sanctions-001",
      comment_type: "note",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      body: "Hit seeded com escalonamento sugerido para bloqueio preventivo e trilha auditável.",
      created_at: "2026-07-15T18:29:00Z"
    }
  ],
  "c4d8dd9b-262b-5d32-840d-f9ec4f12ee89": [
    {
      id: "cmt-showcase-blocks-001",
      comment_type: "note",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      body: "Bloqueio preventivo seeded para demonstrar handoff entre sanctions, blocks e audit.",
      created_at: "2026-07-15T18:37:00Z"
    }
  ],
  "f17b41c9-f5a7-5ec2-b970-511c4fd0b14b": [
    {
      id: "cmt-showcase-ros-001",
      comment_type: "handoff",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      body: "ROS/COAF seeded para demonstrar handoff regulatorio apos triagem de sanctions e block.",
      created_at: "2026-07-15T18:45:00Z"
    },
    {
      id: "cmt-showcase-ros-002",
      comment_type: "note",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      body: "Submissao manual registrada com protocolo e hash do recibo para auditoria cruzada.",
      created_at: "2026-07-15T18:56:00Z"
    }
  ],
  "7d4a7d2f-42f0-59f6-9335-75e4b33e5161": [
    {
      id: "cmt-showcase-evidence-001",
      comment_type: "handoff",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      body: "Pacote manual seeded para ligar due diligence, audit trail e governanca de selagem.",
      created_at: "2026-07-15T19:29:00Z"
    }
  ],
  "9a96176a-a97d-5dce-a7cf-77b9c2d4f0de": [
    {
      id: "cmt-showcase-evidence-sof-001",
      comment_type: "note",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      body: "Workspace seeded para demonstrar timeline da trilha source of funds antes da exportacao do pacote.",
      created_at: "2026-07-15T19:22:00Z"
    }
  ]
};

const STANDALONE_SHOWCASE_AUDIT_LOG_SEEDS: AuditLogEntry[] = [
  {
    id: "audit-showcase-sanctions-001",
    user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    action: "compliance_sanctions_checked",
    resource_type: "case",
    resource_id: "case-showcase-002",
    request_id: "req-showcase-sanctions-001",
    report_id: "rep-showcase-002",
    file_hash_sha256: null,
    metadata: {
      case_id: "case-showcase-002",
      address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
      chain: "ethereum",
      provider: "Chainalysis KYT Showcase",
      provider_status: "live",
      capability_status: "live",
      matched_lists: ["OFAC", "EU"],
      hit: true,
      entity_name: "Atlas OTC Desk",
      designation_date: "2025-11-20T00:00:00Z",
      checked_at: "2026-07-15T18:26:00Z",
      report_type: "legal_report"
    },
    created_at: "2026-07-15T18:26:00Z"
  },
  {
    id: "audit-showcase-block-001",
    user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    action: "preventive_block_evaluated",
    resource_type: "preventive_block",
    resource_id: "bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f",
    request_id: "req-showcase-block-001",
    report_id: "rep-showcase-002",
    file_hash_sha256: "2fb8b4823d65c11274f0e95ad1f20ee0be79b86d5f16e34f96cbe8c8fb7a9c32",
    metadata: {
      case_id: "case-showcase-002",
      address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
      chain: "ethereum",
      action: "BLOCK",
      block_id: "bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f",
      evidence_hash: "2fb8b4823d65c11274f0e95ad1f20ee0be79b86d5f16e34f96cbe8c8fb7a9c32",
      matched_lists: ["OFAC", "EU"],
      regulatory_basis: [
        "OFAC SDN match with corroborated counterparty context",
        "Internal policy OTC-HIGH-RISK-07"
      ],
      requires_coaf_report: true,
      decision_confidence: 0.94,
      screened_at: "2026-07-15T18:35:00Z",
      report_type: "legal_report"
    },
    created_at: "2026-07-15T18:35:00Z"
  },
  {
    id: "audit-showcase-team-001",
    user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    action: "team_external_identity_linked",
    resource_type: "team_user",
    resource_id: "team-showcase-admin-01",
    request_id: "req-showcase-team-link-001",
    report_id: null,
    file_hash_sha256: null,
    metadata: {
      provider: "keycloak",
      external_subject: "kc-showcase-admin-01",
      email_snapshot: "admin@ontrackchain.local",
      role_snapshot: "ADMIN",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      linked_user_id: "team-showcase-admin-01",
      external_user_id: "kc-showcase-admin-01",
      auth_method: "oidc",
      tenant_role: "ADMIN"
    },
    created_at: "2026-07-15T19:05:00Z"
  },
  {
    id: "audit-showcase-denial-001",
    user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    action: "authorization_denied",
    resource_type: "audit_log",
    resource_id: "showcase-denied-alert-export",
    request_id: "req-showcase-deny-001",
    report_id: null,
    file_hash_sha256: null,
    metadata: {
      actor_role: "VIEWER",
      attempted_action: "operational_alerts_exported",
      denial_reason: "viewer_role_required",
      route: "/api/v1/monitoring/alerts/export",
      service: "monitoring-api"
    },
    created_at: "2026-07-15T19:12:00Z"
  },
  {
    id: "audit-showcase-ros-generated-001",
    user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    action: "coaf_report_generated",
    resource_type: "ros_record",
    resource_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
    request_id: "req-showcase-ros-001",
    report_id: "rep-showcase-003",
    file_hash_sha256: "4f8d86d1d8dd7a32d8f7f86d7b219b7f3f95e351ee8e0f38d7fd0ce93f37b8b5",
    metadata: {
      case_id: "case-showcase-002",
      ros_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
      report_id: "rep-showcase-003",
      report_type: "coaf_ready_report",
      trigger_reason: "Escalonamento automatico apos block + sanctions hit.",
      file_hash_sha256: "4f8d86d1d8dd7a32d8f7f86d7b219b7f3f95e351ee8e0f38d7fd0ce93f37b8b5"
    },
    created_at: "2026-07-15T18:42:00Z"
  },
  {
    id: "audit-showcase-ros-approved-001",
    user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    action: "coaf_report_approved",
    resource_type: "ros_record",
    resource_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
    request_id: "req-showcase-ros-002",
    report_id: "rep-showcase-003",
    file_hash_sha256: "4f8d86d1d8dd7a32d8f7f86d7b219b7f3f95e351ee8e0f38d7fd0ce93f37b8b5",
    metadata: {
      ros_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
      approved_at: "2026-07-15T18:47:00Z",
      approval_2fa_verified: true,
      approver_role: STANDALONE_SHOWCASE_AUTH_CONTEXT.role
    },
    created_at: "2026-07-15T18:47:00Z"
  },
  {
    id: "audit-showcase-ros-submitted-001",
    user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    action: "coaf_report_submitted_manual",
    resource_type: "ros_record",
    resource_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
    request_id: "req-showcase-ros-003",
    report_id: "rep-showcase-003",
    file_hash_sha256: "4f8d86d1d8dd7a32d8f7f86d7b219b7f3f95e351ee8e0f38d7fd0ce93f37b8b5",
    metadata: {
      ros_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
      submitted_at: "2026-07-15T18:55:00Z",
      coaf_protocol_number: "COAF-2026-000184",
      coaf_receipt_hash: "4fcd0bdfe7f42dcd765358f8f582d7a35f992f64a3e8f53d651f44af4e5ba328"
    },
    created_at: "2026-07-15T18:55:00Z"
  },
  {
    id: "audit-showcase-ros-dossier-001",
    user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    action: "coaf_regulatory_dossier_downloaded",
    resource_type: "ros_record",
    resource_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
    request_id: "req-showcase-ros-004",
    report_id: "rep-showcase-003",
    file_hash_sha256: "4f8d86d1d8dd7a32d8f7f86d7b219b7f3f95e351ee8e0f38d7fd0ce93f37b8b5",
    metadata: {
      ros_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
      filename: "ontrackchain-ros-coaf-regulatory-dossier-7c4dca53-5806-564f-91ba-ef5487dbf6ce.json",
      dossier_sha256: "ce419a4af145cabaf0b7d8a89ddb501f712d0b5d12bb6dbec64b1ea3dfd2ea69",
      report_id: "rep-showcase-003"
    },
    created_at: "2026-07-15T19:03:00Z"
  },
  {
    id: "audit-showcase-dd-001",
    user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    action: "compliance_due_diligence_checked",
    resource_type: "address",
    resource_id: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
    request_id: "req-showcase-dd-001",
    report_id: "rep-showcase-003",
    file_hash_sha256: "91e49bb8a644f40d938c9334f50fca6e84bd828278dbaf3df881723b0d7f5eb3",
    metadata: {
      case_id: "case-showcase-002",
      address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
      chain: "ethereum",
      provider: "Ontrackchain DD Showcase",
      provider_status: "degraded",
      degraded_reason: "manual_review_required",
      capability_status: "degraded",
      delivery_mode: "manual_review_pending",
      requires_human_review: true,
      counterparty_context_present: true,
      counterparty_context: "Atlas OTC Desk flagged during enhanced due diligence.",
      file_hash_sha256: "91e49bb8a644f40d938c9334f50fca6e84bd828278dbaf3df881723b0d7f5eb3"
    },
    created_at: "2026-07-15T19:24:00Z"
  },
  {
    id: "audit-showcase-dd-export-001",
    user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    action: "evidence_manual_review_package_exported",
    resource_type: "audit_log",
    resource_id: "audit-showcase-dd-export-001",
    request_id: "req-showcase-dd-001",
    report_id: "rep-showcase-003",
    file_hash_sha256: "91e49bb8a644f40d938c9334f50fca6e84bd828278dbaf3df881723b0d7f5eb3",
    metadata: {
      case_id: "case-showcase-002",
      resource_id: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
      address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
      chain: "ethereum",
      provider: "Ontrackchain DD Showcase",
      provider_status: "degraded",
      degraded_reason: "manual_review_required",
      capability_status: "degraded",
      delivery_mode: "manual_review_pending",
      requires_human_review: true,
      counterparty_context_present: true,
      counterparty_context: "Atlas OTC Desk flagged during enhanced due diligence.",
      manual_review_action: "compliance_due_diligence_checked",
      package_sha256: "91e49bb8a644f40d938c9334f50fca6e84bd828278dbaf3df881723b0d7f5eb3",
      filename: "ontrackchain-manual-review-due-diligence-req-showcase-dd-001.json",
      hash_algorithm: "SHA-256",
      scope_id: "req-showcase-dd-001"
    },
    created_at: "2026-07-15T19:31:00Z"
  },
  {
    id: "audit-showcase-sof-001",
    user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    action: "compliance_source_of_funds_checked",
    resource_type: "address",
    resource_id: "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    request_id: "req-showcase-sof-001",
    report_id: "rep-showcase-003",
    file_hash_sha256: "4cd72d6a8f9fc5b58debb42d67f2f6871775c2cda4ff7e5814ac1cbfc8cdf44a",
    metadata: {
      case_id: "case-showcase-002",
      address: "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
      chain: "bitcoin",
      provider: "Ontrackchain SoF Showcase",
      provider_status: "degraded",
      degraded_reason: "manual_review_required",
      capability_status: "degraded",
      delivery_mode: "manual_review_pending",
      requires_human_review: true,
      purpose: "Cross-border OTC settlement",
      amount: 1845000,
      file_hash_sha256: "4cd72d6a8f9fc5b58debb42d67f2f6871775c2cda4ff7e5814ac1cbfc8cdf44a"
    },
    created_at: "2026-07-15T19:18:00Z"
  }
];

type StandaloneShowcaseEvidenceRuntime = {
  workItems: ShowcaseWorkItemRecord[];
  timelineEvents: Record<string, WorkEventResponse[]>;
  timelineComments: Record<string, WorkCommentResponse[]>;
  auditLogs: AuditLogEntry[];
  manualPackageSeals: ManualPackageSeal[];
};

const STANDALONE_SHOWCASE_EVIDENCE_RUNTIME_FILE = join(
  tmpdir(),
  "ontrackchain-standalone-showcase-evidence-runtime.json"
);

function createStandaloneShowcaseEvidenceRuntime(): StandaloneShowcaseEvidenceRuntime {
  return {
    workItems: STANDALONE_SHOWCASE_WORK_ITEM_SEEDS.map((item) => ({
      ...item,
      metadata: { ...item.metadata }
    })),
    timelineEvents: Object.fromEntries(
      Object.entries(STANDALONE_SHOWCASE_TIMELINE_EVENT_SEEDS).map(([workItemId, events]) => [
        workItemId,
        events.map((event) => ({ ...event, payload: { ...event.payload } }))
      ])
    ) as Record<string, WorkEventResponse[]>,
    timelineComments: Object.fromEntries(
      Object.entries(STANDALONE_SHOWCASE_TIMELINE_COMMENT_SEEDS).map(([workItemId, comments]) => [
        workItemId,
        comments.map((comment) => ({ ...comment }))
      ])
    ) as Record<string, WorkCommentResponse[]>,
    auditLogs: STANDALONE_SHOWCASE_AUDIT_LOG_SEEDS.map((entry) => ({
      ...entry,
      metadata: { ...entry.metadata }
    })),
    manualPackageSeals: []
  };
}

function loadStandaloneShowcaseEvidenceRuntimeFromDisk(): StandaloneShowcaseEvidenceRuntime | null {
  if (!existsSync(STANDALONE_SHOWCASE_EVIDENCE_RUNTIME_FILE)) {
    return null;
  }
  try {
    const raw = readFileSync(STANDALONE_SHOWCASE_EVIDENCE_RUNTIME_FILE, "utf8");
    const parsed = JSON.parse(raw) as Partial<StandaloneShowcaseEvidenceRuntime> | null;
    if (!parsed) {
      return null;
    }
    return {
      workItems: Array.isArray(parsed.workItems) ? (parsed.workItems as ShowcaseWorkItemRecord[]) : [],
      timelineEvents:
        parsed.timelineEvents && typeof parsed.timelineEvents === "object"
          ? (parsed.timelineEvents as Record<string, WorkEventResponse[]>)
          : {},
      timelineComments:
        parsed.timelineComments && typeof parsed.timelineComments === "object"
          ? (parsed.timelineComments as Record<string, WorkCommentResponse[]>)
          : {},
      auditLogs: Array.isArray(parsed.auditLogs) ? (parsed.auditLogs as AuditLogEntry[]) : [],
      manualPackageSeals: Array.isArray(parsed.manualPackageSeals) ? (parsed.manualPackageSeals as ManualPackageSeal[]) : []
    };
  } catch {
    return null;
  }
}

const standaloneShowcaseEvidenceGlobal = globalThis as typeof globalThis & {
  __ontrackchainStandaloneShowcaseEvidenceRuntime?: StandaloneShowcaseEvidenceRuntime;
};

const standaloneShowcaseEvidenceRuntime =
  standaloneShowcaseEvidenceGlobal.__ontrackchainStandaloneShowcaseEvidenceRuntime ??
  (standaloneShowcaseEvidenceGlobal.__ontrackchainStandaloneShowcaseEvidenceRuntime =
    loadStandaloneShowcaseEvidenceRuntimeFromDisk() ?? createStandaloneShowcaseEvidenceRuntime());

let standaloneShowcaseWorkItemsStore = standaloneShowcaseEvidenceRuntime.workItems;
let standaloneShowcaseTimelineEventsStore = standaloneShowcaseEvidenceRuntime.timelineEvents;
let standaloneShowcaseTimelineCommentsStore = standaloneShowcaseEvidenceRuntime.timelineComments;
let standaloneShowcaseAuditLogsStore = standaloneShowcaseEvidenceRuntime.auditLogs;
let standaloneShowcaseManualPackageSealsStore = standaloneShowcaseEvidenceRuntime.manualPackageSeals;

function syncStandaloneShowcaseEvidenceRuntimeStores() {
  standaloneShowcaseEvidenceRuntime.workItems = standaloneShowcaseWorkItemsStore;
  standaloneShowcaseEvidenceRuntime.timelineEvents = standaloneShowcaseTimelineEventsStore;
  standaloneShowcaseEvidenceRuntime.timelineComments = standaloneShowcaseTimelineCommentsStore;
  standaloneShowcaseEvidenceRuntime.auditLogs = standaloneShowcaseAuditLogsStore;
  standaloneShowcaseEvidenceRuntime.manualPackageSeals = standaloneShowcaseManualPackageSealsStore;
  try {
    writeFileSync(
      STANDALONE_SHOWCASE_EVIDENCE_RUNTIME_FILE,
      JSON.stringify(standaloneShowcaseEvidenceRuntime),
      "utf8"
    );
  } catch {
    // Best-effort persistence for standalone showcase in dev/test mode.
  }
}

function refreshStandaloneShowcaseEvidenceRuntimeStores() {
  const persisted = loadStandaloneShowcaseEvidenceRuntimeFromDisk();
  if (!persisted) {
    return;
  }
  standaloneShowcaseEvidenceRuntime.workItems = persisted.workItems;
  standaloneShowcaseEvidenceRuntime.timelineEvents = persisted.timelineEvents;
  standaloneShowcaseEvidenceRuntime.timelineComments = persisted.timelineComments;
  standaloneShowcaseEvidenceRuntime.auditLogs = persisted.auditLogs;
  standaloneShowcaseEvidenceRuntime.manualPackageSeals = persisted.manualPackageSeals;
  standaloneShowcaseWorkItemsStore = standaloneShowcaseEvidenceRuntime.workItems;
  standaloneShowcaseTimelineEventsStore = standaloneShowcaseEvidenceRuntime.timelineEvents;
  standaloneShowcaseTimelineCommentsStore = standaloneShowcaseEvidenceRuntime.timelineComments;
  standaloneShowcaseAuditLogsStore = standaloneShowcaseEvidenceRuntime.auditLogs;
  standaloneShowcaseManualPackageSealsStore = standaloneShowcaseEvidenceRuntime.manualPackageSeals;
}

const STANDALONE_SHOWCASE_ROS_COAF_SEEDS: ShowcaseRosCoafDetail[] = [
  {
    ros_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
    case_id: "case-showcase-002",
    status: "SUBMITTED_MANUAL",
    report_id: "rep-showcase-003",
    created_at: "2026-07-15T18:42:00Z",
    approved_at: "2026-07-15T18:47:00Z",
    submitted_at: "2026-07-15T18:55:00Z",
    coaf_protocol_number: "COAF-2026-000184",
    coaf_receipt_hash: "4fcd0bdfe7f42dcd765358f8f582d7a35f992f64a3e8f53d651f44af4e5ba328",
    rejection_reason: "",
    approval_2fa_verified: true,
    submission_deadline: "2026-07-16T09:00:00Z",
    deadline_breached: false,
    last_activity_at: "2026-07-15T19:03:00Z",
    tipologia_code: "TIP-AML-021",
    tipologia_description: "Operacao com indício de tentativa de ocultacao patrimonial por ativo virtual.",
    trigger_reason: "Escalonado apos sanctions hit e preventive block com obrigatoriedade de trilha ROS/COAF.",
    suspected_amount_brl: 1845000,
    suspected_address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
    suspected_chain: "ethereum",
    pdf_hash: "4f8d86d1d8dd7a32d8f7f86d7b219b7f3f95e351ee8e0f38d7fd0ce93f37b8b5",
    pdf_path: "/standalone-showcase/reports/rep-showcase-003.pdf",
    generated_at: "2026-07-15T18:42:00Z",
    evidence_hash: "2fb8b4823d65c11274f0e95ad1f20ee0be79b86d5f16e34f96cbe8c8fb7a9c32",
    evidence_trail_ref: "ev-trail-showcase-ros-001",
    updated_at: "2026-07-15T19:03:00Z",
    retain_until: "2031-07-15T00:00:00Z",
    audit: [
      {
        id: "ros-audit-showcase-001",
        action: "coaf_report_generated",
        user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
        created_at: "2026-07-15T18:42:00Z",
        metadata: {
          ros_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
          report_id: "rep-showcase-003",
          file_hash_sha256: "4f8d86d1d8dd7a32d8f7f86d7b219b7f3f95e351ee8e0f38d7fd0ce93f37b8b5"
        }
      },
      {
        id: "ros-audit-showcase-002",
        action: "coaf_report_approved",
        user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
        created_at: "2026-07-15T18:47:00Z",
        metadata: {
          ros_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
          approval_2fa_verified: true
        }
      },
      {
        id: "ros-audit-showcase-003",
        action: "coaf_report_submitted_manual",
        user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
        created_at: "2026-07-15T18:55:00Z",
        metadata: {
          ros_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
          coaf_protocol_number: "COAF-2026-000184",
          coaf_receipt_hash: "4fcd0bdfe7f42dcd765358f8f582d7a35f992f64a3e8f53d651f44af4e5ba328"
        }
      },
      {
        id: "ros-audit-showcase-004",
        action: "coaf_regulatory_dossier_downloaded",
        user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
        created_at: "2026-07-15T19:03:00Z",
        metadata: {
          ros_id: "7c4dca53-5806-564f-91ba-ef5487dbf6ce",
          filename: "ontrackchain-ros-coaf-regulatory-dossier-7c4dca53-5806-564f-91ba-ef5487dbf6ce.json",
          dossier_sha256: "ce419a4af145cabaf0b7d8a89ddb501f712d0b5d12bb6dbec64b1ea3dfd2ea69"
        }
      }
    ]
  }
];

let standaloneShowcaseRosCoafStore = STANDALONE_SHOWCASE_ROS_COAF_SEEDS.map((record) => ({
  ...record,
  audit: record.audit.map((entry) => ({ ...entry, metadata: { ...entry.metadata } }))
}));

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

const STANDALONE_SHOWCASE_MONITORING_WATCHLISTS: Watchlist[] = [
  { id: "watchlist-showcase-critical", name: "Critical Counterparties", priority: "high" },
  { id: "watchlist-showcase-bridges", name: "Bridge Exposure", priority: "normal" }
];

const STANDALONE_SHOWCASE_MONITORING_WATCHLIST_ITEMS: Record<string, WatchlistItem[]> = {
  "watchlist-showcase-critical": [
    {
      id: "watchlist-item-showcase-001",
      watchlist_id: "watchlist-showcase-critical",
      address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
      chain: "ethereum",
      created_at: "2026-07-15T18:12:00Z"
    },
    {
      id: "watchlist-item-showcase-002",
      watchlist_id: "watchlist-showcase-critical",
      address: "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
      chain: "bitcoin",
      created_at: "2026-07-15T18:13:00Z"
    }
  ],
  "watchlist-showcase-bridges": [
    {
      id: "watchlist-item-showcase-003",
      watchlist_id: "watchlist-showcase-bridges",
      address: "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
      chain: "base",
      created_at: "2026-07-15T18:15:00Z"
    }
  ]
};

const STANDALONE_SHOWCASE_MONITORING_ALERT_SEEDS: Alert[] = [
  {
    id: "alert-showcase-001",
    watchlist_id: "watchlist-showcase-critical",
    address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
    chain: "ethereum",
    severity: "high",
    title: "Sanctions proximity detected",
    details: { source: "showcase_seed", matched_list: "ofac", risk_score: 91 },
    created_at: "2026-07-15T18:25:00Z"
  }
];

type ShowcasePlatformAlertRecord = PlatformOperationalAlertsSnapshot["data"][number];

const STANDALONE_SHOWCASE_PLATFORM_ALERT_SEEDS: ShowcasePlatformAlertRecord[] = [
  {
    id: "platform-alert-showcase-001",
    receiver: "slack-secops",
    status: "firing",
    triage_status: "pending",
    alertname: "IndexerLagHigh",
    service: "indexer",
    severity: "critical",
    fingerprint: "fp-showcase-indexer-lag",
    labels: { env: "showcase", service: "indexer", team: "platform" },
    annotations: {
      summary: "Indexer com lag acima do limite de governança.",
      description: "Lag sustentado por 7 minutos no pipeline de indexacao regulatoria."
    },
    first_received_at: "2026-07-15T18:00:00Z",
    last_received_at: "2026-07-15T18:32:00Z",
    delivery_count: 5,
    resolved_at: null,
    triaged_at: null,
    triaged_by: null,
    triage_note: null
  },
  {
    id: "platform-alert-showcase-002",
    receiver: "pagerduty-compliance",
    status: "firing",
    triage_status: "pending",
    alertname: "RulesEngineRetryBurst",
    service: "rules-engine",
    severity: "warning",
    fingerprint: "fp-showcase-rules-retry",
    labels: { env: "showcase", service: "rules-engine", team: "compliance" },
    annotations: {
      summary: "Burst de retries em regras de screening.",
      description: "Fila de reprocessamento subiu acima da baseline operacional."
    },
    first_received_at: "2026-07-15T18:08:00Z",
    last_received_at: "2026-07-15T18:31:00Z",
    delivery_count: 3,
    resolved_at: null,
    triaged_at: null,
    triaged_by: null,
    triage_note: null
  },
  {
    id: "platform-alert-showcase-003",
    receiver: "slack-secops",
    status: "resolved",
    triage_status: "acknowledged",
    alertname: "WorkerCpuRecovered",
    service: "worker",
    severity: "info",
    fingerprint: "fp-showcase-worker-recovered",
    labels: { env: "showcase", service: "worker", team: "investigation" },
    annotations: {
      summary: "Recuperacao automatica do worker principal.",
      description: "Escalonamento horizontal estabilizou a fila de casos."
    },
    first_received_at: "2026-07-15T17:40:00Z",
    last_received_at: "2026-07-15T18:05:00Z",
    delivery_count: 2,
    resolved_at: "2026-07-15T18:06:00Z",
    triaged_at: "2026-07-15T18:07:00Z",
    triaged_by: "alice.admin",
    triage_note: "noise reduced after autoscaling"
  }
];

const STANDALONE_SHOWCASE_OPERATIONAL_ALERT_SEED_BASE: OperationalAlertsSnapshot["alerts"] = [
  {
    code: "IDX_LAG_HIGH",
    severity: "critical",
    status: "open",
    metric: "indexer_lag_seconds",
    value: 540,
    threshold: 180,
    title: "Indexer lag acima do limite",
    message: "A indexacao regulatoria esta atrasada e pode afetar UX e governanca.",
    recommended_action: "Validar backlog, workers e pressao no banco antes de ampliar ingestao."
  },
  {
    code: "RULES_RETRY_BURST",
    severity: "warning",
    status: "open",
    metric: "rules_retry_backlog",
    value: 34,
    threshold: 10,
    title: "Burst de retries em screening",
    message: "O motor de regras entrou em degradacao parcial e requer triagem.",
    recommended_action: "Revisar fila DLQ, backoff e dependencia externa de enrichment."
  }
];

type ShowcaseDlqCaseRecord = DlqSnapshot["cases"][number];

const STANDALONE_SHOWCASE_DLQ_CASE_SEEDS: ShowcaseDlqCaseRecord[] = [
  {
    case_id: "case-showcase-dlq-001",
    status: "failed",
    target_address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
    target_chain: "ethereum",
    created_at: "2026-07-15T17:20:00Z",
    completed_at: null,
    report_type_canonical: "technical_basic",
    failure_reason: "provider_timeout_chain_analytics",
    dlq_state: "failed_permanent",
    dlq_failed_at: "2026-07-15T17:31:00Z",
    dlq_requeue_count: 1,
    dlq_acknowledged_at: null,
    dlq_acknowledged_by: null,
    dlq_resolution_note: null,
    attempt_count: 3,
    max_attempts: 3,
    credits_estimated: 42,
    credits_available: 120,
    can_requeue: true
  },
  {
    case_id: "case-showcase-dlq-002",
    status: "failed",
    target_address: "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    target_chain: "bitcoin",
    created_at: "2026-07-15T16:55:00Z",
    completed_at: null,
    report_type_canonical: "wallet_screening",
    failure_reason: "manual_review_required",
    dlq_state: "acknowledged",
    dlq_failed_at: "2026-07-15T17:05:00Z",
    dlq_requeue_count: 0,
    dlq_acknowledged_at: "2026-07-15T17:12:00Z",
    dlq_acknowledged_by: "carla.compliance",
    dlq_resolution_note: "triaged_for_manual_followup",
    attempt_count: 3,
    max_attempts: 3,
    credits_estimated: 35,
    credits_available: 120,
    can_requeue: true
  }
];

const STANDALONE_SHOWCASE_OPERATIONS_BASE: Omit<OperationsSnapshot, "states" | "recent_cases" | "generated_at"> = {
  queue: {
    ready: 6,
    waiting: 14,
    retry_pending: 3,
    retry_due: 2,
    wake_signals: 9
  },
  concurrency: {
    org_active: 4,
    org_limit: 8,
    global_active: 11,
    global_limit: 20,
    plan: "enterprise"
  },
  throughput: {
    completed_last_hour: 52,
    failed_last_hour: 4,
    billing_recalc_last_hour: 7,
    avg_duration_ms_last_20: 1840
  },
  security: {
    manual_package_mfa_violations_last_hour: 1,
    manual_package_mfa_2fa_required_last_hour: 1,
    manual_package_mfa_provider_not_homologated_last_hour: 0
  }
};

const STANDALONE_SHOWCASE_OPERATION_RECENT_CASES: OperationsSnapshot["recent_cases"] = [
  {
    case_id: "case-showcase-001",
    status: "completed",
    target_address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
    target_chain: "ethereum",
    created_at: "2026-07-15T18:05:00Z",
    completed_at: "2026-07-15T18:12:00Z",
    queue_state: "completed",
    last_error: null,
    attempt_count: 1,
    report_type_canonical: "technical_basic",
    charged_cost: 18,
    duration_ms: 1280
  },
  {
    case_id: "case-showcase-dlq-001",
    status: "failed",
    target_address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
    target_chain: "ethereum",
    created_at: "2026-07-15T17:20:00Z",
    completed_at: null,
    queue_state: "dlq_failed",
    last_error: "provider_timeout_chain_analytics",
    attempt_count: 3,
    report_type_canonical: "technical_basic",
    charged_cost: null,
    duration_ms: 6400
  }
];

let standaloneShowcaseMonitoringAlertsStore = STANDALONE_SHOWCASE_MONITORING_ALERT_SEEDS.map((alert) => ({ ...alert }));
let standaloneShowcasePlatformAlertsStore = STANDALONE_SHOWCASE_PLATFORM_ALERT_SEEDS.map((alert) => ({
  ...alert,
  labels: { ...alert.labels },
  annotations: { ...alert.annotations }
}));
let standaloneShowcaseDlqStore = STANDALONE_SHOWCASE_DLQ_CASE_SEEDS.map((entry) => ({ ...entry }));

export type ShowcaseCounterpartyRecord = {
  id: string;
  legal_name: string;
  counterparty_type: string;
  document_type: string;
  document_number: string;
  risk_level: number;
  kyc_status: string;
  sanctions_cleared: boolean;
  is_pep: boolean;
  enhanced_dd_required: boolean;
  next_review_date: string | null;
  status: string;
  created_at: string;
  dd_review_status?: string;
  dd_review_note?: string;
  sof_description?: string;
  sof_document_ref?: string;
  last_reviewed_at?: string | null;
  wallet_chain?: string;
  wallet_address?: string;
  wallet_label?: string;
};

const STANDALONE_SHOWCASE_COUNTERPARTY_SEEDS: ShowcaseCounterpartyRecord[] = [
  {
    id: "22222222-2222-4222-8222-222222222222",
    legal_name: "Atlas OTC Desk",
    counterparty_type: "PARCEIRO_COMERCIAL",
    document_type: "CNPJ",
    document_number: "12.345.678/0001-90",
    risk_level: 4,
    kyc_status: "PENDING",
    sanctions_cleared: false,
    is_pep: false,
    enhanced_dd_required: true,
    next_review_date: "2026-08-10T00:00:00Z",
    status: "UNDER_REVIEW",
    created_at: "2026-07-15T17:40:00Z",
    dd_review_status: "in_progress",
    dd_review_note: "Pending SoF evidence for high-volume OTC corridor.",
    sof_description: "Capital de giro próprio com reforço documental em coleta.",
    sof_document_ref: "SOF-ATLAS-2026-001",
    last_reviewed_at: "2026-07-15T18:20:00Z",
    wallet_chain: "ethereum",
    wallet_address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
    wallet_label: "primary treasury"
  },
  {
    id: "44444444-4444-4444-8444-444444444444",
    legal_name: "Lumen DeFi Labs",
    counterparty_type: "CONTRAPARTE_DEFI",
    document_type: "FOREIGN_ID",
    document_number: "US-DEFI-99281",
    risk_level: 3,
    kyc_status: "APPROVED",
    sanctions_cleared: true,
    is_pep: false,
    enhanced_dd_required: false,
    next_review_date: "2026-09-01T00:00:00Z",
    status: "ACTIVE",
    created_at: "2026-07-14T14:10:00Z",
    dd_review_status: "completed",
    dd_review_note: "Governance and treasury evidence archived.",
    sof_description: "Treasury funded by audited governance allocation.",
    sof_document_ref: "SOF-LUMEN-2026-004",
    last_reviewed_at: "2026-07-14T16:00:00Z",
    wallet_chain: "arbitrum",
    wallet_address: "0x4200000000000000000000000000000000000006",
    wallet_label: "dao treasury"
  },
  {
    id: "55555555-5555-4555-8555-555555555555",
    legal_name: "Carla Ventures",
    counterparty_type: "CLIENTE_PF",
    document_type: "CPF",
    document_number: "123.456.789-00",
    risk_level: 2,
    kyc_status: "PENDING",
    sanctions_cleared: true,
    is_pep: true,
    enhanced_dd_required: true,
    next_review_date: "2026-07-20T00:00:00Z",
    status: "PENDING_REVIEW",
    created_at: "2026-07-15T09:30:00Z",
    dd_review_status: "pending",
    dd_review_note: "",
    sof_description: "",
    sof_document_ref: "",
    last_reviewed_at: null,
    wallet_chain: "base",
    wallet_address: "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    wallet_label: "personal wallet"
  }
];

let standaloneShowcaseCounterpartiesStore = STANDALONE_SHOWCASE_COUNTERPARTY_SEEDS.map((item) => ({ ...item }));

export type ShowcaseBillingBalanceRecord = {
  credits_available: number;
  credits_reserved: number;
  credits_used_total: number;
};

export type ShowcaseBillingActionTotalRecord = {
  action: string;
  entry_count: number;
  amount_total: number;
};

export type ShowcaseBillingLedgerEntryRecord = {
  id: string;
  case_id: string | null;
  action: string;
  amount: number | null;
  balance_after: number | null;
  request_id: string | null;
  quote_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string | null;
};

export type ShowcaseBillingReconciliationRecord = {
  generated_at: string;
  balance: ShowcaseBillingBalanceRecord;
  quotes: {
    investigation: { open_total: number; expired_total: number };
    compliance: { open_total: number; expired_total: number };
    monitoring: { open_total: number; expired_total: number };
    open_total: number;
    expired_total: number;
  };
  ledger: {
    total_entries: number;
    action_totals: ShowcaseBillingActionTotalRecord[];
    recent: ShowcaseBillingLedgerEntryRecord[];
  };
};

const STANDALONE_SHOWCASE_BILLING_BALANCE: ShowcaseBillingBalanceRecord = {
  credits_available: 1840,
  credits_reserved: 210,
  credits_used_total: 9620
};

const STANDALONE_SHOWCASE_BILLING_LEDGER_SEEDS: ShowcaseBillingLedgerEntryRecord[] = [
  {
    id: "ledger-showcase-001",
    case_id: "case-showcase-001",
    action: "CONFIRMED",
    amount: 24,
    balance_after: 1858,
    request_id: "req-showcase-report-001",
    quote_id: "quote-technical_basic-ethereum",
    metadata: { domain: "investigation", report_type: "technical_basic", mode: "standalone_showcase" },
    created_at: "2026-07-15T19:05:00Z"
  },
  {
    id: "ledger-showcase-002",
    case_id: "33333333-3333-4333-8333-333333333333",
    action: "PRE_HOLD",
    amount: 36,
    balance_after: 1822,
    request_id: "req-showcase-counterparty-001",
    quote_id: null,
    metadata: { domain: "compliance", counterparty_id: "22222222-2222-4222-8222-222222222222" },
    created_at: "2026-07-15T18:18:00Z"
  },
  {
    id: "ledger-showcase-003",
    case_id: null,
    action: "RELEASED",
    amount: -12,
    balance_after: 1834,
    request_id: "req-showcase-monitoring-001",
    quote_id: null,
    metadata: { domain: "monitoring", watchlist_id: "watchlist-showcase-critical" },
    created_at: "2026-07-15T18:32:00Z"
  },
  {
    id: "ledger-showcase-004",
    case_id: "case-showcase-002",
    action: "CONFIRMED",
    amount: 68,
    balance_after: 1766,
    request_id: "req-showcase-report-002",
    quote_id: "quote-legal_report-bitcoin",
    metadata: { domain: "reports", report_type: "legal_report", mode: "standalone_showcase" },
    created_at: "2026-07-15T17:55:00Z"
  },
  {
    id: "ledger-showcase-005",
    case_id: null,
    action: "MANUAL_ADJUSTMENT",
    amount: 74,
    balance_after: 1840,
    request_id: "req-showcase-billing-adjustment-001",
    quote_id: null,
    metadata: { domain: "billing", reason: "showcase_monthly_topup" },
    created_at: "2026-07-15T16:40:00Z"
  }
];

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

function cloneStandaloneWorkItem(item: ShowcaseWorkItemRecord): ShowcaseWorkItemRecord {
  return {
    ...item,
    metadata: { ...item.metadata }
  };
}

function cloneStandaloneAuditLog(entry: AuditLogEntry): AuditLogEntry {
  return { ...entry, metadata: { ...entry.metadata } };
}

function cloneStandaloneRosAuditEntry(entry: ShowcaseRosCoafAuditEntry): ShowcaseRosCoafAuditEntry {
  return { ...entry, metadata: { ...entry.metadata } };
}

function cloneStandaloneRosCoafRecord(record: ShowcaseRosCoafDetail): ShowcaseRosCoafDetail {
  return {
    ...record,
    audit: record.audit.map(cloneStandaloneRosAuditEntry)
  };
}

function buildStandaloneShowcaseHash(seed: string) {
  const normalized = seed.replace(/[^a-zA-Z0-9]/g, "").toLowerCase() || "showcase";
  return normalized.repeat(16).slice(0, 64);
}

function cloneStandaloneManualPackageSignoff(signoff: ManualPackageSealSignoff): ManualPackageSealSignoff {
  return {
    ...signoff,
    metadata: { ...signoff.metadata }
  };
}

function cloneStandaloneManualPackageSeal(seal: ManualPackageSeal): ManualPackageSeal {
  return {
    ...seal,
    required_signers: [...seal.required_signers],
    signoffs: seal.signoffs.map(cloneStandaloneManualPackageSignoff),
    seal_envelope: { ...seal.seal_envelope },
    verification_summary: { ...seal.verification_summary }
  };
}

function findStandaloneShowcaseManualPackageSealIndex(sealId: string) {
  refreshStandaloneShowcaseEvidenceRuntimeStores();
  return standaloneShowcaseManualPackageSealsStore.findIndex((entry) => entry.seal_id === sealId.trim());
}

function findStandaloneShowcaseManualPackageSealByDigest(packageSha256: string, policyVersion?: string | null) {
  refreshStandaloneShowcaseEvidenceRuntimeStores();
  const normalizedDigest = packageSha256.trim();
  const normalizedPolicyVersion = policyVersion?.trim() ?? "";
  return (
    standaloneShowcaseManualPackageSealsStore.find((entry) => {
      if (entry.package_sha256 !== normalizedDigest) {
        return false;
      }
      if (normalizedPolicyVersion && entry.policy_version !== normalizedPolicyVersion) {
        return false;
      }
      return true;
    }) ?? null
  );
}

function findStandaloneShowcaseManualPackageSealById(sealId: string) {
  refreshStandaloneShowcaseEvidenceRuntimeStores();
  const normalizedSealId = sealId.trim();
  return standaloneShowcaseManualPackageSealsStore.find((entry) => entry.seal_id === normalizedSealId) ?? null;
}

function normalizeStandaloneManualPackageRequest(input: {
  format?: string | null;
  request_id?: string | null;
  action?: string | null;
  resource_type?: string | null;
  report_id?: string | null;
  resource_id?: string | null;
  limit?: number | null;
  include_audit_logs?: boolean;
  include_credit_ledger?: boolean;
  include_reports?: boolean;
}): ShowcaseEvidenceBundle["request"] {
  return {
    format: input.format?.trim() || "json",
    request_id: input.request_id?.trim() || null,
    action: input.action?.trim() || null,
    resource_type: input.resource_type?.trim() || null,
    report_id: input.report_id?.trim() || null,
    resource_id: input.resource_id?.trim() || null,
    limit: typeof input.limit === "number" && input.limit > 0 ? input.limit : 50,
    include_audit_logs: input.include_audit_logs !== false,
    include_credit_ledger: input.include_credit_ledger !== false,
    include_reports: input.include_reports !== false
  };
}

function buildStandaloneShowcaseEvidenceBundleCreditLedger(request: ShowcaseEvidenceBundle["request"]) {
  const relevantReports = STANDALONE_SHOWCASE_REPORT_HISTORY.filter((entry) => {
    if (request.report_id && entry.report_id !== request.report_id) return false;
    if (request.request_id && entry.case_id !== request.request_id) return false;
    return true;
  });

  return relevantReports.slice(0, request.limit).map((entry) => ({
    at: entry.created_at,
    credits: entry.report_type === "coaf_ready_report" ? -18 : entry.report_type === "legal_report" ? -68 : -24,
    reference: entry.report_id,
    case_id: entry.case_id,
    report_type: entry.report_type
  }));
}

function buildStandaloneShowcaseEvidenceBundleReports(request: ShowcaseEvidenceBundle["request"]) {
  return STANDALONE_SHOWCASE_REPORT_HISTORY.filter((entry) => {
    if (request.report_id && entry.report_id !== request.report_id) return false;
    if (request.request_id && entry.case_id !== request.request_id) return false;
    return true;
  })
    .slice(0, request.limit)
    .map((entry) => ({
      report_id: entry.report_id,
      case_id: entry.case_id,
      report_type_requested: entry.report_type_requested,
      report_type: entry.report_type,
      content_type: entry.content_type,
      file_hash_sha256: entry.file_hash_sha256,
      onchain_hash: entry.onchain_hash,
      created_at: entry.created_at,
      has_download_audit: entry.has_download_audit
    }));
}

function buildStandaloneShowcaseManualPackageVerificationSummary(seal: ManualPackageSeal) {
  return {
    verified: seal.seal_status === "sealed",
    verification_method: seal.seal_status === "sealed" ? "x509_chain_and_manifest_digest" : "pending_signature_materialization",
    issuer: seal.seal_status === "sealed" ? "Ontrackchain Showcase Trust Service" : "pending",
    key_id: seal.seal_status === "sealed" ? "showcase-kms/manual-package-signing" : "pending",
    policy_version: seal.policy_version
  };
}

function buildStandaloneShowcaseManualPackageEnvelope(seal: ManualPackageSeal) {
  return {
    package_sha256: seal.package_sha256,
    classification: seal.classification,
    policy_version: seal.policy_version,
    signoff_mode: seal.signoff_mode,
    seal_status: seal.seal_status,
    required_signers: [...seal.required_signers],
    signoff_count: seal.signoffs.length
  };
}

function finalizeStandaloneShowcaseManualPackageSealShape(seal: ManualPackageSeal): ManualPackageSeal {
  const requiredSignerSet = new Set(seal.required_signers);
  const approvedRequiredRoles = new Set(
    seal.signoffs
      .filter((signoff) => requiredSignerSet.has(signoff.signer_role) && signoff.decision === "approved")
      .map((signoff) => signoff.signer_role)
  );
  const hasRejectedRequiredRole = seal.signoffs.some(
    (signoff) => requiredSignerSet.has(signoff.signer_role) && signoff.decision === "rejected"
  );

  let sealStatus = seal.seal_status;
  if (sealStatus !== "sealed" && sealStatus !== "revoked" && sealStatus !== "superseded") {
    if (hasRejectedRequiredRole) {
      sealStatus = "failed";
    } else if (approvedRequiredRoles.size >= seal.required_signers.length) {
      sealStatus = "ready_to_seal";
    } else {
      sealStatus = "pending_signoff";
    }
  }

  const nextSeal: ManualPackageSeal = {
    ...seal,
    seal_status: sealStatus,
    completed_signoffs: seal.signoffs.length,
    approved_required_signoffs: approvedRequiredRoles.size,
    required_signoffs: seal.required_signers.length,
    seal_envelope: buildStandaloneShowcaseManualPackageEnvelope({ ...seal, seal_status: sealStatus }),
    verification_summary: buildStandaloneShowcaseManualPackageVerificationSummary({ ...seal, seal_status: sealStatus })
  };

  return nextSeal;
}

function storeStandaloneShowcaseManualPackageSeal(seal: ManualPackageSeal) {
  const normalized = finalizeStandaloneShowcaseManualPackageSealShape({
    ...seal,
    required_signers: [...seal.required_signers],
    signoffs: seal.signoffs.map(cloneStandaloneManualPackageSignoff),
    seal_envelope: { ...seal.seal_envelope },
    verification_summary: { ...seal.verification_summary }
  });
  const index = findStandaloneShowcaseManualPackageSealIndex(normalized.seal_id);
  if (index >= 0) {
    standaloneShowcaseManualPackageSealsStore[index] = normalized;
  } else {
    standaloneShowcaseManualPackageSealsStore = [normalized, ...standaloneShowcaseManualPackageSealsStore];
  }
  syncStandaloneShowcaseEvidenceRuntimeStores();
  return cloneStandaloneManualPackageSeal(normalized);
}

function appendStandaloneShowcaseAuditLog(input: {
  action: string;
  resource_type: string;
  resource_id: string | null;
  request_id?: string | null;
  report_id?: string | null;
  file_hash_sha256?: string | null;
  metadata: Record<string, unknown>;
  created_at?: string;
}) {
  const createdAt = input.created_at ?? new Date().toISOString();
  const idSeed = `${input.action}:${input.resource_id ?? "none"}:${createdAt}`;
  const id = `audit-showcase-${buildStandaloneShowcaseHash(idSeed).slice(0, 24)}`;
  const entry: AuditLogEntry = {
    id,
    user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    action: input.action,
    resource_type: input.resource_type,
    resource_id: input.resource_id,
    request_id: input.request_id ?? null,
    report_id: input.report_id ?? null,
    file_hash_sha256: input.file_hash_sha256 ?? null,
    metadata: { ...input.metadata },
    created_at: createdAt
  };
  standaloneShowcaseAuditLogsStore = [entry, ...standaloneShowcaseAuditLogsStore];
  syncStandaloneShowcaseEvidenceRuntimeStores();
  return cloneStandaloneAuditLog(entry);
}

function findStandaloneShowcaseEvidenceWorkItemByPackageSha(packageSha256: string) {
  refreshStandaloneShowcaseEvidenceRuntimeStores();
  const normalizedDigest = packageSha256.trim();
  return (
    standaloneShowcaseWorkItemsStore.find((entry) => {
      if (entry.module !== "evidence" || entry.resource_type !== "evidence_event") {
        return false;
      }
      return ((entry.metadata as EvidenceWorkItemMetadata).package_sha256 ?? "").trim() === normalizedDigest;
    }) ?? null
  );
}

function syncStandaloneShowcaseEvidenceWorkItemFromAuditLog(auditLog: AuditLogEntry) {
  const metadata = (auditLog.metadata ?? {}) as EvidenceWorkItemMetadata;
  const existing =
    ((metadata.package_sha256 && findStandaloneShowcaseEvidenceWorkItemByPackageSha(metadata.package_sha256)) as
      | ShowcaseWorkItemRecord
      | null) ??
    standaloneShowcaseWorkItemsStore.find(
      (entry) =>
        entry.module === "evidence" &&
        entry.resource_type === "evidence_event" &&
        ((entry.metadata as EvidenceWorkItemMetadata).event_id ?? "") === auditLog.id
    ) ??
    null;

  const workspaceStatus =
    metadata.workspace_status?.trim() ||
    (existing?.metadata as EvidenceWorkItemMetadata | undefined)?.workspace_status?.trim() ||
    "reviewing";
  const queueStatus =
    workspaceStatus === "sealed" ? "CLOSED" : workspaceStatus === "failed" || workspaceStatus === "revoked" ? "REJECTED" : "UNDER_REVIEW";

  return upsertStandaloneShowcaseWorkItem(
    {
      module: "evidence",
      resource_type: "evidence_event",
      resource_id: auditLog.id,
      case_id: metadata.case_id ?? existing?.case_id ?? null,
      report_external_id: auditLog.report_id ?? metadata.report_id ?? existing?.report_external_id ?? null,
      owner_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      priority: existing?.priority ?? "high",
      queue_status: queueStatus,
      due_at: existing?.due_at ?? null,
      title:
        existing?.title ??
        `Evidence manual package • ${metadata.scope_id ?? auditLog.request_id ?? auditLog.resource_id ?? auditLog.id}`,
      note:
        (typeof metadata.filename === "string" && metadata.filename.trim()) ||
        existing?.note ||
        "Pacote manual sincronizado no showcase.",
      metadata: {
        ...(existing?.metadata ?? {}),
        ...metadata,
        event_id: auditLog.id,
        audit_action: auditLog.action,
        audit_resource_type: auditLog.resource_type,
        audit_resource_id: auditLog.resource_id ?? auditLog.id,
        request_id: auditLog.request_id ?? metadata.request_id ?? undefined,
        report_id: auditLog.report_id ?? metadata.report_id ?? undefined,
        file_hash_sha256: auditLog.file_hash_sha256 ?? metadata.file_hash_sha256 ?? undefined,
        workspace_status: workspaceStatus,
        local_workspace_status: workspaceStatus
      }
    },
    existing?.id
  );
}

function syncStandaloneShowcaseEvidenceWorkItemFromSeal(
  seal: ManualPackageSeal,
  metadata: Record<string, unknown> = {}
) {
  const existing = findStandaloneShowcaseEvidenceWorkItemByPackageSha(seal.package_sha256);
  const workspaceStatus =
    seal.seal_status === "sealed"
      ? "sealed"
      : seal.seal_status === "revoked"
        ? "revoked"
        : seal.seal_status === "superseded"
          ? "superseded"
          : seal.seal_status === "failed"
            ? "failed"
            : "reviewing";
  const queueStatus =
    seal.seal_status === "sealed"
      ? "CLOSED"
      : seal.seal_status === "revoked" || seal.seal_status === "failed"
        ? "REJECTED"
        : "UNDER_REVIEW";

  return upsertStandaloneShowcaseWorkItem(
    {
      module: "evidence",
      resource_type: "evidence_event",
      resource_id: existing?.resource_id ?? crypto.randomUUID(),
      case_id:
        existing?.case_id ??
        (typeof metadata.case_id === "string" ? metadata.case_id : null),
      report_external_id:
        existing?.report_external_id ??
        seal.report_id ??
        (typeof metadata.report_id === "string" ? metadata.report_id : null),
      owner_user_id: existing?.owner_user_id ?? STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      priority: existing?.priority ?? "high",
      queue_status: queueStatus,
      due_at: existing?.due_at ?? null,
      title: existing?.title ?? `Evidence manual package • ${seal.scope_id}`,
      note:
        existing?.note ??
        (typeof metadata.reason === "string" && metadata.reason.trim() ? metadata.reason.trim() : "Pacote manual em trilha regulatoria."),
      metadata: {
        ...(existing?.metadata ?? {}),
        request_id: seal.request_id,
        report_id: seal.report_id ?? undefined,
        manual_review_action: seal.manual_review_action,
        package_sha256: seal.package_sha256,
        workspace_status: workspaceStatus,
        local_workspace_status: workspaceStatus,
        seal_status: seal.seal_status,
        ...(seal.sealed_at ? { sealed_at: seal.sealed_at } : {}),
        ...(seal.superseded_by_seal_id ? { superseded_by_seal_id: seal.superseded_by_seal_id } : {}),
        ...metadata
      } as EvidenceWorkItemMetadata
    },
    existing?.id
  );
}

export function buildStandaloneShowcaseEvidenceExportBundle(input: {
  format?: string | null;
  request_id?: string | null;
  action?: string | null;
  resource_type?: string | null;
  report_id?: string | null;
  resource_id?: string | null;
  limit?: number | null;
  include_audit_logs?: boolean;
  include_credit_ledger?: boolean;
  include_reports?: boolean;
}): ShowcaseEvidenceBundle {
  const request = normalizeStandaloneManualPackageRequest(input);
  return {
    mode: "standalone_showcase",
    request,
    export_generated_at: new Date().toISOString(),
    audit_logs: request.include_audit_logs
      ? listStandaloneShowcaseAuditLogs({
          requestId: request.request_id,
          action: request.action,
          resourceType: request.resource_type,
          reportId: request.report_id,
          resourceId: request.resource_id,
          page: 1,
          limit: request.limit
        }).data
      : [],
    credit_ledger: request.include_credit_ledger ? buildStandaloneShowcaseEvidenceBundleCreditLedger(request) : [],
    reports: request.include_reports ? buildStandaloneShowcaseEvidenceBundleReports(request) : []
  };
}

export async function exportStandaloneShowcaseEvidenceManualPackage(
  payload: EvidenceManualPackagePayload,
  exportRequestId: string
) {
  const generatedAt = new Date().toISOString();
  const filename = buildManualReviewPackageFilename(payload.action, payload.scope_id);
  const evidenceBundle = buildStandaloneShowcaseEvidenceExportBundle({
    format: "json",
    request_id: payload.evidence_request.request_id ?? null,
    action: null,
    resource_type: payload.evidence_request.resource_type ?? null,
    report_id: payload.evidence_request.report_id ?? null,
    resource_id: payload.evidence_request.resource_id ?? null,
    limit: payload.evidence_request.limit ?? 50,
    include_audit_logs: payload.evidence_request.include_audit_logs ?? true,
    include_credit_ledger: payload.evidence_request.include_credit_ledger ?? true,
    include_reports: payload.evidence_request.include_reports ?? true
  });
  const packageDocument = buildEvidenceManualPackageDocument(payload, evidenceBundle, generatedAt);
  const manifest = await buildEvidenceManualPackageManifest({
    payload,
    evidenceBundle,
    generatedAt,
    exportRequestId,
    filename
  });
  const manualPackageAuditMetadata = buildEvidenceManualPackageAuditMetadata({
    payload,
    manifest,
    filename
  });
  const auditLog = appendStandaloneShowcaseAuditLog({
    action: "evidence_manual_review_package_exported",
    resource_type: "audit_log",
    resource_id: null,
    request_id: payload.evidence_request.request_id ?? payload.scope.request_id ?? null,
    report_id: payload.evidence_request.report_id ?? payload.scope.report_id ?? null,
    file_hash_sha256: manifest.payload_sha256,
    metadata: {
      ...manualPackageAuditMetadata,
      scope_id: payload.scope_id,
      report_id: payload.evidence_request.report_id ?? payload.scope.report_id ?? null,
      request_id: payload.evidence_request.request_id ?? payload.scope.request_id ?? null,
      resource_id: payload.scope.resource_id ?? payload.evidence_request.resource_id ?? null,
      workspace_status: (payload.workspace_summary?.status as string | null | undefined) ?? "reviewing"
    },
    created_at: generatedAt
  });
  const finalizedDocument = finalizeEvidenceManualPackageDocument(packageDocument, manifest, {
    action: auditLog.action,
    resource_type: auditLog.resource_type,
    resource_id: auditLog.resource_id ?? null,
    request_id: auditLog.request_id ?? null,
    report_id: auditLog.report_id ?? null,
    created_at: auditLog.created_at ?? generatedAt,
    metadata: { ...auditLog.metadata }
  });
  syncStandaloneShowcaseEvidenceWorkItemFromAuditLog(auditLog);
  return {
    filename,
    packageSha256: manifest.payload_sha256,
    document: finalizedDocument
  };
}

export function getStandaloneShowcaseManualPackageSealByDigest(packageSha256: string, policyVersion?: string | null) {
  const seal = findStandaloneShowcaseManualPackageSealByDigest(packageSha256, policyVersion);
  return seal ? cloneStandaloneManualPackageSeal(seal) : null;
}

export function createStandaloneShowcaseManualPackageSignoffRequest(input: {
  request_id?: string | null;
  report_id?: string | null;
  scope_id?: string | null;
  manual_review_action?: string | null;
  package_sha256?: string | null;
  manifest_schema_version?: string | null;
  classification?: string | null;
  signoff_mode?: string | null;
  package_kind?: string | null;
  policy_version?: string | null;
}) {
  const packageSha256 = input.package_sha256?.trim() ?? "";
  if (!packageSha256) {
    return null;
  }
  const existing = findStandaloneShowcaseManualPackageSealByDigest(packageSha256, input.policy_version);
  if (existing && !["revoked", "superseded", "failed"].includes(existing.seal_status)) {
    return cloneStandaloneManualPackageSeal(existing);
  }

  const now = new Date().toISOString();
  const nextSeal: ManualPackageSeal = {
    seal_id: crypto.randomUUID(),
    organization_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.org_id,
    package_kind: input.package_kind?.trim() || "manual_review_package",
    request_id: input.request_id?.trim() || input.scope_id?.trim() || "showcase-manual-package",
    report_id: input.report_id?.trim() || null,
    scope_id: input.scope_id?.trim() || input.request_id?.trim() || "showcase-manual-package",
    manual_review_action: input.manual_review_action?.trim() || "compliance_due_diligence_checked",
    package_sha256: packageSha256,
    manifest_schema_version: input.manifest_schema_version?.trim() || "manual_review_package/v2",
    classification: input.classification?.trim() || "restricted_regulatory",
    signoff_mode: input.signoff_mode?.trim() || "compliance_ops_signoff",
    seal_status: "pending_signoff",
    seal_format: "json_detached_signature",
    signature_algorithm: null,
    kms_key_ref: null,
    certificate_fingerprint_sha256: null,
    certificate_bundle_ref: null,
    policy_version: input.policy_version?.trim() || "manual_package_sealing/v1",
    sealed_at: null,
    sealed_by_user_id: null,
    revoked_at: null,
    superseded_by_seal_id: null,
    required_signers: ["compliance_owner"],
    completed_signoffs: 0,
    approved_required_signoffs: 0,
    required_signoffs: 1,
    signoffs: [],
    seal_envelope: {},
    verification_summary: {},
    created_at: now,
    updated_at: now
  };
  const stored = storeStandaloneShowcaseManualPackageSeal(nextSeal);
  syncStandaloneShowcaseEvidenceWorkItemFromSeal(stored);
  return stored;
}

export function recordStandaloneShowcaseManualPackageSignoff(
  sealId: string,
  input: {
    decision?: string | null;
    signer_role?: string | null;
    signoff_method?: string | null;
    ticket_ref?: string | null;
    notes?: string | null;
    signer_display_name?: string | null;
    metadata?: Record<string, unknown> | null;
  }
) {
  const current = findStandaloneShowcaseManualPackageSealById(sealId);
  if (!current) {
    return null;
  }
  const signerRole = input.signer_role?.trim() ?? "";
  if (!signerRole) {
    return "invalid_signer_role" as const;
  }

  const now = new Date().toISOString();
  const nextSignoff: ManualPackageSealSignoff = {
    id: crypto.randomUUID(),
    seal_id: current.seal_id,
    organization_id: current.organization_id,
    signer_role: signerRole,
    signer_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    signer_display_name: input.signer_display_name?.trim() || "Showcase Operator",
    decision: input.decision?.trim() || "approved",
    signoff_method: input.signoff_method?.trim() || "platform_authenticated_2fa",
    ticket_ref: input.ticket_ref?.trim() || null,
    notes: input.notes?.trim() || null,
    signed_at: now,
    metadata: { ...(input.metadata ?? {}) }
  };

  const remainingSignoffs = current.signoffs.filter((entry) => entry.signer_role !== signerRole);
  const stored = storeStandaloneShowcaseManualPackageSeal({
    ...current,
    signoffs: [...remainingSignoffs, nextSignoff],
    updated_at: now
  });
  syncStandaloneShowcaseEvidenceWorkItemFromSeal(stored, {
    signoff_role: signerRole,
    signoff_decision: nextSignoff.decision
  });
  return stored;
}

export function finalizeStandaloneShowcaseManualPackageSeal(
  sealId: string,
  input: { metadata?: Record<string, unknown> | null }
) {
  const current = findStandaloneShowcaseManualPackageSealById(sealId);
  if (!current) {
    return null;
  }
  const normalized = finalizeStandaloneShowcaseManualPackageSealShape(current);
  if (normalized.seal_status !== "ready_to_seal" && normalized.seal_status !== "sealed") {
    return "seal_not_ready" as const;
  }

  const now = new Date().toISOString();
  const stored = storeStandaloneShowcaseManualPackageSeal({
    ...normalized,
    seal_status: "sealed",
    signature_algorithm: "ECDSA_P256_SHA256",
    kms_key_ref: "showcase-kms/manual-package-signing",
    certificate_fingerprint_sha256: buildStandaloneShowcaseHash(`${normalized.seal_id}-cert-fingerprint`),
    certificate_bundle_ref: "showcase-trust-bundle/manual-package/v1",
    sealed_at: normalized.sealed_at ?? now,
    sealed_by_user_id: normalized.sealed_by_user_id ?? STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    updated_at: now
  });
  syncStandaloneShowcaseEvidenceWorkItemFromSeal(stored, {
    ...(input.metadata ?? {}),
    sealed_at: stored.sealed_at
  });
  appendStandaloneShowcaseAuditLog({
    action: "evidence_manual_package_sealed",
    resource_type: "manual_package_seal",
    resource_id: stored.seal_id,
    request_id: stored.request_id,
    report_id: stored.report_id,
    file_hash_sha256: stored.package_sha256,
    metadata: {
      package_sha256: stored.package_sha256,
      seal_id: stored.seal_id,
      manual_review_action: stored.manual_review_action,
      ...(input.metadata ?? {})
    }
  });
  return stored;
}

export function revokeStandaloneShowcaseManualPackageSeal(
  sealId: string,
  input: {
    ticket_ref?: string | null;
    reason?: string | null;
    metadata?: Record<string, unknown> | null;
  }
) {
  const current = findStandaloneShowcaseManualPackageSealById(sealId);
  if (!current) {
    return null;
  }
  const reason = input.reason?.trim() ?? "";
  const ticketRef = input.ticket_ref?.trim() ?? "";
  if (!reason || !ticketRef) {
    return "invalid_revoke_payload" as const;
  }

  const now = new Date().toISOString();
  const stored = storeStandaloneShowcaseManualPackageSeal({
    ...current,
    seal_status: "revoked",
    revoked_at: now,
    updated_at: now
  });
  syncStandaloneShowcaseEvidenceWorkItemFromSeal(stored, {
    reason,
    revoke_ticket_ref: ticketRef,
    ...(input.metadata ?? {})
  });
  appendStandaloneShowcaseAuditLog({
    action: "evidence_manual_package_seal_revoked",
    resource_type: "manual_package_seal",
    resource_id: stored.seal_id,
    request_id: stored.request_id,
    report_id: stored.report_id,
    file_hash_sha256: stored.package_sha256,
    metadata: {
      package_sha256: stored.package_sha256,
      seal_id: stored.seal_id,
      ticket_ref: ticketRef,
      reason,
      ...(input.metadata ?? {})
    }
  });
  return stored;
}

export function supersedeStandaloneShowcaseManualPackageSeal(
  sealId: string,
  input: {
    superseded_by_seal_id?: string | null;
    ticket_ref?: string | null;
    reason?: string | null;
    metadata?: Record<string, unknown> | null;
  }
) {
  const current = findStandaloneShowcaseManualPackageSealById(sealId);
  if (!current) {
    return null;
  }
  const replacementSealId = input.superseded_by_seal_id?.trim() ?? "";
  const reason = input.reason?.trim() ?? "";
  const ticketRef = input.ticket_ref?.trim() ?? "";
  if (!replacementSealId || !reason || !ticketRef) {
    return "invalid_supersede_payload" as const;
  }

  const now = new Date().toISOString();
  const stored = storeStandaloneShowcaseManualPackageSeal({
    ...current,
    seal_status: "superseded",
    superseded_by_seal_id: replacementSealId,
    updated_at: now
  });
  syncStandaloneShowcaseEvidenceWorkItemFromSeal(stored, {
    reason,
    superseded_by_seal_id: replacementSealId,
    supersede_ticket_ref: ticketRef,
    ...(input.metadata ?? {})
  });
  appendStandaloneShowcaseAuditLog({
    action: "evidence_manual_package_seal_superseded",
    resource_type: "manual_package_seal",
    resource_id: stored.seal_id,
    request_id: stored.request_id,
    report_id: stored.report_id,
    file_hash_sha256: stored.package_sha256,
    metadata: {
      package_sha256: stored.package_sha256,
      seal_id: stored.seal_id,
      superseded_by_seal_id: replacementSealId,
      ticket_ref: ticketRef,
      reason,
      ...(input.metadata ?? {})
    }
  });
  return stored;
}

function findStandaloneShowcaseRosCoafById(rosId: string) {
  const normalizedRosId = rosId.trim();
  return standaloneShowcaseRosCoafStore.find((record) => record.ros_id === normalizedRosId) ?? null;
}

function findStandaloneShowcaseRosCoafByReportId(reportId: string) {
  const normalizedReportId = reportId.trim();
  return standaloneShowcaseRosCoafStore.find((record) => record.report_id === normalizedReportId) ?? null;
}

function syncStandaloneShowcaseRosWorkItem(record: ShowcaseRosCoafDetail) {
  const existing = standaloneShowcaseWorkItemsStore.find(
    (item) => item.module === "ros_coaf" && item.resource_type === "ros_record" && item.resource_id === record.ros_id
  );
  return upsertStandaloneShowcaseWorkItem(
    {
      module: "ros_coaf",
      resource_type: "ros_record",
      resource_id: record.ros_id,
      case_id: record.case_id,
      report_external_id: record.report_id,
      priority: existing?.priority ?? "critical",
      queue_status:
        record.status === "SUBMITTED_MANUAL"
          ? "SUBMITTED"
          : record.status === "APPROVED"
            ? "APPROVED"
            : record.status === "REJECTED"
              ? "REJECTED"
              : "UNDER_REVIEW",
      due_at: record.submission_deadline,
      title: `ROS/COAF • ${record.ros_id}`,
      note:
        record.status === "REJECTED"
          ? record.rejection_reason || null
          : record.status === "SUBMITTED_MANUAL"
            ? record.coaf_receipt_hash || null
            : existing?.note ?? null,
      metadata: {
        case_id: record.case_id ?? "",
        owner_label: "showcase-user",
        owner_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
        workspace_status: record.status,
        ros_status: record.status,
        ros_phase:
          record.status === "SUBMITTED_MANUAL"
            ? "submitted"
            : record.status === "APPROVED"
              ? "approved"
              : record.status === "REJECTED"
                ? "rejected"
                : "generated",
        ros_id: record.ros_id,
        report_id: record.report_id,
        created_at: record.created_at,
        approved_at: record.approved_at ?? "",
        approval_2fa_verified: record.approval_2fa_verified,
        submitted_at: record.submitted_at ?? "",
        coaf_protocol_number: record.coaf_protocol_number,
        coaf_receipt_hash: record.coaf_receipt_hash,
        rejection_reason: record.rejection_reason
      } satisfies RosCoafWorkItemMetadata
    },
    existing?.id
  );
}

function appendStandaloneShowcaseRosAudit(
  rosId: string,
  action: string,
  createdAt: string,
  metadata: Record<string, unknown>,
  reportId: string,
  fileHashSha256: string
) {
  const auditEntry: ShowcaseRosCoafAuditEntry = {
    id: crypto.randomUUID(),
    action,
    user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
    created_at: createdAt,
    metadata: { ...metadata }
  };
  standaloneShowcaseRosCoafStore = standaloneShowcaseRosCoafStore.map((record) =>
    record.ros_id === rosId ? { ...record, audit: [...record.audit, auditEntry] } : record
  );
  standaloneShowcaseAuditLogsStore = [
    {
      id: crypto.randomUUID(),
      user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      action,
      resource_type: "ros_record",
      resource_id: rosId,
      request_id: `req-${rosId}-${action}-${createdAt}`,
      report_id: reportId,
      file_hash_sha256: fileHashSha256,
      metadata: { ros_id: rosId, report_id: reportId, ...metadata },
      created_at: createdAt
    },
    ...standaloneShowcaseAuditLogsStore
  ];
  syncStandaloneShowcaseEvidenceRuntimeStores();
}

function normalizeStandaloneAddress(value: string) {
  return value.trim().toLowerCase();
}

function normalizeStandaloneChain(value: string | null | undefined) {
  const normalized = value?.trim().toLowerCase() ?? "";
  return normalized || "ethereum";
}

function parseStandaloneShowcaseLists(value: string | null | undefined) {
  const normalized = value
    ?.split(",")
    .map((entry) => entry.trim())
    .filter(Boolean) ?? [];
  return normalized.length ? Array.from(new Set(normalized)) : ["OFAC", "UN", "EU", "COAF"];
}

function findStandaloneShowcaseSanctionsWorkItem(address: string, chain: string) {
  const normalizedAddress = normalizeStandaloneAddress(address);
  const normalizedChain = normalizeStandaloneChain(chain);
  return (
    standaloneShowcaseWorkItemsStore.find((item) => {
      if (item.module !== "sanctions" || item.resource_type !== "sanctions_screening") {
        return false;
      }
      const metadata = item.metadata as SanctionsWorkItemMetadata;
      return (
        normalizeStandaloneAddress(metadata.address ?? "") === normalizedAddress &&
        normalizeStandaloneChain(metadata.chain) === normalizedChain
      );
    }) ?? null
  );
}

function findStandaloneShowcaseBlockWorkItemByAddress(address: string, chain: string) {
  const normalizedAddress = normalizeStandaloneAddress(address);
  const normalizedChain = normalizeStandaloneChain(chain);
  return (
    standaloneShowcaseWorkItemsStore.find((item) => {
      if (item.module !== "blocks" || item.resource_type !== "preventive_block") {
        return false;
      }
      const metadata = item.metadata as BlocksWorkItemMetadata;
      return (
        normalizeStandaloneAddress(metadata.address ?? "") === normalizedAddress &&
        normalizeStandaloneChain(metadata.chain) === normalizedChain
      );
    }) ?? null
  );
}

function findStandaloneShowcaseBlockWorkItemById(blockId: string) {
  const normalizedBlockId = blockId.trim();
  return (
    standaloneShowcaseWorkItemsStore.find((item) => {
      if (item.module !== "blocks" || item.resource_type !== "preventive_block") {
        return false;
      }
      const metadata = item.metadata as BlocksWorkItemMetadata;
      return item.resource_id === normalizedBlockId || (metadata.block_id ?? "") === normalizedBlockId;
    }) ?? null
  );
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
}): WorkItemListResponse<ShowcaseWorkItemMetadata> {
  refreshStandaloneShowcaseEvidenceRuntimeStores();
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
  refreshStandaloneShowcaseEvidenceRuntimeStores();
  const workItem = standaloneShowcaseWorkItemsStore.find((item) => item.id === workItemId) ?? null;
  return workItem ? cloneStandaloneWorkItem(workItem) : null;
}

export function upsertStandaloneShowcaseWorkItem(
  payload: Partial<ShowcaseWorkItemRecord> & {
    module?: ShowcaseWorkItemRecord["module"];
    resource_type?: ShowcaseWorkItemRecord["resource_type"];
    resource_id?: string;
    case_id?: string | null;
    report_external_id?: string | null;
    priority: "critical" | "high" | "normal";
    queue_status: WorkItemResponse["queue_status"];
    due_at: string | null;
    title: string;
    note: string | null;
    metadata: ShowcaseWorkItemMetadata;
  },
  workItemId?: string
) {
  const now = new Date().toISOString();
  const existingIndex = workItemId ? standaloneShowcaseWorkItemsStore.findIndex((item) => item.id === workItemId) : -1;
  const existing = existingIndex >= 0 ? standaloneShowcaseWorkItemsStore[existingIndex] : null;
  const resolvedId = existing?.id ?? workItemId ?? crypto.randomUUID();
  const nextItem: ShowcaseWorkItemRecord = {
    id: resolvedId,
    module: payload.module ?? existing?.module ?? "reports",
    resource_type: payload.resource_type ?? existing?.resource_type ?? "formal_report_case",
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
        report_id: nextItem.report_external_id ?? null,
        resource_type: nextItem.resource_type
      },
      created_at: now
    }
  ];
  syncStandaloneShowcaseEvidenceRuntimeStores();

  return cloneStandaloneWorkItem(nextItem);
}

export function getStandaloneShowcaseWorkItemTimeline(
  workItemId: string
): WorkItemTimelineResponse<ShowcaseWorkItemRecord> | null {
  refreshStandaloneShowcaseEvidenceRuntimeStores();
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
  refreshStandaloneShowcaseEvidenceRuntimeStores();
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
  syncStandaloneShowcaseEvidenceRuntimeStores();
  return { ...comment };
}

export function listStandaloneShowcaseAuditLogs(filters: {
  requestId?: string | null;
  action?: string | null;
  resourceType?: string | null;
  reportId?: string | null;
  resourceId?: string | null;
  page?: number | null;
  limit?: number | null;
}): AuditLogsResponse {
  refreshStandaloneShowcaseEvidenceRuntimeStores();
  const page = typeof filters.page === "number" && filters.page > 0 ? filters.page : 1;
  const limit = typeof filters.limit === "number" && filters.limit > 0 ? filters.limit : 50;
  const requestId = filters.requestId?.trim() ?? "";
  const action = filters.action?.trim() ?? "";
  const resourceType = filters.resourceType?.trim() ?? "";
  const reportId = filters.reportId?.trim() ?? "";
  const resourceId = filters.resourceId?.trim() ?? "";

  const filtered = standaloneShowcaseAuditLogsStore.filter((entry) => {
    if (requestId && (entry.request_id ?? "") !== requestId) return false;
    if (action && entry.action !== action) return false;
    if (resourceType && entry.resource_type !== resourceType) return false;
    if (reportId && (entry.report_id ?? "") !== reportId) return false;
    if (resourceId && (entry.resource_id ?? "") !== resourceId) return false;
    return true;
  });
  const ordered = filtered
    .slice()
    .sort((left, right) => (right.created_at ?? "").localeCompare(left.created_at ?? ""));
  const offset = (page - 1) * limit;
  const data = ordered.slice(offset, offset + limit).map(cloneStandaloneAuditLog);
  const total = ordered.length;

  return {
    data,
    page,
    count: data.length,
    limit,
    total,
    total_pages: Math.max(1, Math.ceil(total / limit)),
    has_more: offset + data.length < total,
    filters: {
      request_id: requestId || null,
      action: action || null,
      resource_type: resourceType || null,
      report_id: reportId || null,
      resource_id: resourceId || null
    }
  };
}

export function getStandaloneShowcaseSanctionsCheck(input: {
  address: string;
  chain?: string | null;
  lists?: string | null;
}): ShowcaseSanctionsCheckResponse {
  const normalizedAddress = input.address.trim();
  const normalizedChain = normalizeStandaloneChain(input.chain);
  const requestedLists = parseStandaloneShowcaseLists(input.lists);
  const existing = findStandaloneShowcaseSanctionsWorkItem(normalizedAddress, normalizedChain);
  const existingMetadata = (existing?.metadata ?? {}) as SanctionsWorkItemMetadata;
  const seededLists = existingMetadata.matched_lists ?? [];
  const matchedLists = seededLists.length
    ? requestedLists.filter((entry) => seededLists.includes(entry))
    : [];
  const heuristicHit =
    normalizeStandaloneAddress(normalizedAddress) ===
      normalizeStandaloneAddress("0x8ba1f109551bD432803012645Ac136ddd64DBA72") ||
    normalizeStandaloneAddress(normalizedAddress) ===
      normalizeStandaloneAddress("bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh");
  const hit = typeof existingMetadata.hit === "boolean" ? existingMetadata.hit : heuristicHit;

  return {
    address: normalizedAddress,
    chain: normalizedChain,
    provider: existingMetadata.provider ?? "Chainalysis KYT Showcase",
    provider_status: (existingMetadata.provider_status as "live" | "degraded" | undefined) ?? "live",
    degraded_reason: existingMetadata.degraded_reason ?? null,
    capability_status: (existingMetadata.capability_status as "live" | "degraded" | undefined) ?? "live",
    lists: requestedLists,
    hit,
    matched_lists: hit ? matchedLists : [],
    entity_name: hit ? existingMetadata.entity_name ?? "Atlas OTC Desk" : null,
    designation_date: hit ? existingMetadata.designation_date ?? "2025-11-20T00:00:00Z" : null,
    checked_at: new Date().toISOString()
  };
}

export function evaluateStandaloneShowcaseBlock(input: {
  address: string;
  chain?: string | null;
  entity_name?: string | null;
  entity_document?: string | null;
}): ShowcaseBlockEvaluateResponse {
  const normalizedAddress = input.address.trim();
  const normalizedChain = normalizeStandaloneChain(input.chain);
  const existing = findStandaloneShowcaseBlockWorkItemByAddress(normalizedAddress, normalizedChain);
  const metadata = (existing?.metadata ?? {}) as BlocksWorkItemMetadata;
  const heuristicBlocked =
    normalizeStandaloneAddress(normalizedAddress) ===
      normalizeStandaloneAddress("0x8ba1f109551bD432803012645Ac136ddd64DBA72") ||
    normalizeStandaloneAddress(normalizedAddress) ===
      normalizeStandaloneAddress("bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh");

  if (existing) {
    return {
      address: normalizedAddress,
      chain: normalizedChain,
      action: metadata.action ?? "BLOCK",
      requires_coaf_report: metadata.requires_coaf_report === true,
      decision_confidence: typeof metadata.decision_confidence === "number" ? metadata.decision_confidence : 0.94,
      regulatory_basis: metadata.regulatory_basis ?? [],
      matched_lists: metadata.matched_lists ?? [],
      evidence_hash: metadata.evidence_hash ?? null,
      block_id: metadata.block_id ?? existing.resource_id,
      screened_at: new Date().toISOString()
    };
  }

  if (heuristicBlocked) {
    return {
      address: normalizedAddress,
      chain: normalizedChain,
      action: "BLOCK",
      requires_coaf_report: true,
      decision_confidence: 0.9,
      regulatory_basis: [
        "Heurística showcase de exposição sancionatória",
        "Escalonamento operacional para revisão regulatória"
      ],
      matched_lists: ["OFAC"],
      evidence_hash: "showcase-evidence-hash-pending",
      block_id: crypto.randomUUID(),
      screened_at: new Date().toISOString()
    };
  }

  return {
    address: normalizedAddress,
    chain: normalizedChain,
    action: "CLEAR",
    requires_coaf_report: false,
    decision_confidence: 0.82,
    regulatory_basis: ["No critical sanctions or preventive triggers in standalone showcase."],
    matched_lists: [],
    evidence_hash: null,
    block_id: null,
    screened_at: new Date().toISOString()
  };
}

export function liftStandaloneShowcaseBlock(
  blockId: string,
  payload: { reason?: string | null }
): ShowcaseBlockLiftResponse | null {
  const current = findStandaloneShowcaseBlockWorkItemById(blockId);
  if (!current) {
    return null;
  }

  const now = new Date().toISOString();
  standaloneShowcaseWorkItemsStore = standaloneShowcaseWorkItemsStore.map((item) => {
    if (item.id !== current.id) {
      return item;
    }
    const metadata = item.metadata as BlocksWorkItemMetadata;
    return {
      ...item,
      queue_status: "CLOSED",
      note: payload.reason?.trim() || item.note,
      metadata: {
        ...metadata,
        action: "LIFT",
        workspace_status: "LIFTED",
        local_workspace_status: "LIFTED",
        local_block_status: "LIFTED",
        lifted_at: now,
        lift_reason: payload.reason?.trim() || metadata.lift_reason || ""
      },
      updated_at: now,
      last_activity_at: now
    };
  });
  ensureStandaloneWorkItemCollections(current.id);
  standaloneShowcaseTimelineEventsStore[current.id] = [
    ...standaloneShowcaseTimelineEventsStore[current.id],
    {
      id: crypto.randomUUID(),
      event_type: "BLOCK_LIFTED",
      from_status: "BLOCKED",
      to_status: "LIFTED",
      actor_user_id: STANDALONE_SHOWCASE_AUTH_CONTEXT.user_id,
      payload: {
        block_id: blockId.trim(),
        reason: payload.reason?.trim() || null
      },
      created_at: now
    }
  ];
  syncStandaloneShowcaseEvidenceRuntimeStores();

  return {
    block_id: blockId.trim(),
    status: "LIFTED",
    review_status: "COMPLETED",
    lifted_at: now
  };
}

export function resolveStandaloneShowcaseRosRef(reportId: string) {
  const rosRecord = findStandaloneShowcaseRosCoafByReportId(reportId);
  return {
    report_id: reportId.trim(),
    ros_id: rosRecord?.ros_id ?? null
  };
}

export function listStandaloneShowcaseRosCoaf(filters: {
  page?: number | null;
  limit?: number | null;
  reportId?: string | null;
  rosId?: string | null;
}) {
  const page = typeof filters.page === "number" && filters.page > 0 ? filters.page : 1;
  const limit = typeof filters.limit === "number" && filters.limit > 0 ? filters.limit : 100;
  const reportId = filters.reportId?.trim() ?? "";
  const rosId = filters.rosId?.trim() ?? "";
  const filtered = standaloneShowcaseRosCoafStore.filter((record) => {
    if (reportId && record.report_id !== reportId) return false;
    if (rosId && record.ros_id !== rosId) return false;
    return true;
  });
  const ordered = filtered
    .slice()
    .sort((left, right) => (right.last_activity_at ?? "").localeCompare(left.last_activity_at ?? ""));
  const offset = (page - 1) * limit;
  const data = ordered.slice(offset, offset + limit).map((record) => {
    const { audit: _audit, ...listItem } = cloneStandaloneRosCoafRecord(record);
    return listItem;
  });
  return {
    data,
    page,
    limit,
    total: ordered.length,
    has_more: offset + data.length < ordered.length
  };
}

export function getStandaloneShowcaseRosCoafDetail(rosId: string) {
  const record = findStandaloneShowcaseRosCoafById(rosId);
  return record ? cloneStandaloneRosCoafRecord(record) : null;
}

export function generateStandaloneShowcaseRosCoaf(input: { rosId: string }) {
  const normalizedRosId = input.rosId.trim();
  const existing = findStandaloneShowcaseRosCoafById(normalizedRosId);
  if (existing) {
    return {
      ros_id: existing.ros_id,
      report_id: existing.report_id,
      report_type: "coaf_ready_report",
      status: existing.status,
      created_at: existing.created_at,
      file_hash_sha256: existing.pdf_hash,
      content_type: "application/pdf"
    } satisfies ShowcaseRosCoafGenerateResponse;
  }

  const now = new Date().toISOString();
  const nextReportId = `rep-showcase-ros-${normalizedRosId.slice(0, 8)}`;
  const pdfHash = buildStandaloneShowcaseHash(`${normalizedRosId}-pdf`);
  const newRecord: ShowcaseRosCoafDetail = {
    ros_id: normalizedRosId,
    case_id: "case-showcase-002",
    status: "PENDING_APPROVAL",
    report_id: nextReportId,
    created_at: now,
    approved_at: null,
    submitted_at: null,
    coaf_protocol_number: "",
    coaf_receipt_hash: "",
    rejection_reason: "",
    approval_2fa_verified: false,
    submission_deadline: "2026-07-16T12:00:00Z",
    deadline_breached: false,
    last_activity_at: now,
    tipologia_code: "TIP-AML-021",
    tipologia_description: "Operacao suspeita com fluxo transfronteirico e triangulacao em ativos virtuais.",
    trigger_reason: "Registro gerado dinamicamente no standalone showcase para demonstrar trilha ROS/COAF.",
    suspected_amount_brl: 925000,
    suspected_address: "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
    suspected_chain: "ethereum",
    pdf_hash: pdfHash,
    pdf_path: `/standalone-showcase/reports/${nextReportId}.pdf`,
    generated_at: now,
    evidence_hash: buildStandaloneShowcaseHash(`${normalizedRosId}-evidence`),
    evidence_trail_ref: `ev-trail-${normalizedRosId}`,
    updated_at: now,
    retain_until: "2031-07-15T00:00:00Z",
    audit: []
  };

  standaloneShowcaseRosCoafStore = [newRecord, ...standaloneShowcaseRosCoafStore];
  STANDALONE_SHOWCASE_REPORT_HISTORY.push({
    report_id: nextReportId,
    case_id: "case-showcase-002",
    report_type_requested: "coaf_ready_report",
    report_type: "coaf_ready_report",
    content_type: "application/pdf",
    file_hash_sha256: pdfHash,
    onchain_hash: null,
    created_at: now,
    has_download_audit: false
  });
  appendStandaloneShowcaseRosAudit(
    normalizedRosId,
    "coaf_report_generated",
    now,
    {
      case_id: "case-showcase-002",
      file_hash_sha256: pdfHash,
      trigger_reason: "Registro gerado dinamicamente no standalone showcase para demonstrar trilha ROS/COAF."
    },
    nextReportId,
    pdfHash
  );
  syncStandaloneShowcaseRosWorkItem(newRecord);

  return {
    ros_id: normalizedRosId,
    report_id: nextReportId,
    report_type: "coaf_ready_report",
    status: "PENDING_APPROVAL",
    created_at: now,
    file_hash_sha256: pdfHash,
    content_type: "application/pdf"
  } satisfies ShowcaseRosCoafGenerateResponse;
}

export function approveStandaloneShowcaseRosCoaf(
  rosId: string,
  payload: { approved: boolean; rejection_reason?: string | null }
) {
  const current = findStandaloneShowcaseRosCoafById(rosId);
  if (!current) {
    return null;
  }
  const now = new Date().toISOString();
  const nextStatus = payload.approved ? "APPROVED" : "REJECTED";
  const rejectionReason = payload.approved ? "" : payload.rejection_reason?.trim() ?? "";
  standaloneShowcaseRosCoafStore = standaloneShowcaseRosCoafStore.map((record) =>
    record.ros_id === current.ros_id
      ? {
          ...record,
          status: nextStatus,
          approved_at: now,
          approval_2fa_verified: payload.approved,
          rejection_reason: rejectionReason,
          updated_at: now,
          last_activity_at: now
        }
      : record
  );
  appendStandaloneShowcaseRosAudit(
    current.ros_id,
    payload.approved ? "coaf_report_approved" : "coaf_report_rejected",
    now,
    {
      approved_at: now,
      approval_2fa_verified: payload.approved,
      rejection_reason: rejectionReason || null
    },
    current.report_id,
    current.pdf_hash
  );
  const updated = findStandaloneShowcaseRosCoafById(current.ros_id);
  if (updated) {
    syncStandaloneShowcaseRosWorkItem(updated);
  }
  return {
    ros_id: current.ros_id,
    status: nextStatus,
    approved_at: now,
    approval_2fa_verified: payload.approved
  } satisfies ShowcaseRosCoafApproveResponse;
}

export function submitStandaloneShowcaseRosCoaf(
  rosId: string,
  payload: { coaf_protocol_number: string; coaf_receipt_hash?: string | null }
) {
  const current = findStandaloneShowcaseRosCoafById(rosId);
  if (!current) {
    return null;
  }
  const now = new Date().toISOString();
  const receiptHash = payload.coaf_receipt_hash?.trim() || buildStandaloneShowcaseHash(`${rosId}-receipt-${now}`);
  standaloneShowcaseRosCoafStore = standaloneShowcaseRosCoafStore.map((record) =>
    record.ros_id === current.ros_id
      ? {
          ...record,
          status: "SUBMITTED_MANUAL",
          submitted_at: now,
          coaf_protocol_number: payload.coaf_protocol_number.trim(),
          coaf_receipt_hash: receiptHash,
          updated_at: now,
          last_activity_at: now
        }
      : record
  );
  appendStandaloneShowcaseRosAudit(
    current.ros_id,
    "coaf_report_submitted_manual",
    now,
    {
      submitted_at: now,
      coaf_protocol_number: payload.coaf_protocol_number.trim(),
      coaf_receipt_hash: receiptHash
    },
    current.report_id,
    current.pdf_hash
  );
  const updated = findStandaloneShowcaseRosCoafById(current.ros_id);
  if (updated) {
    syncStandaloneShowcaseRosWorkItem(updated);
  }
  return {
    ros_id: current.ros_id,
    status: "SUBMITTED_MANUAL",
    submitted_at: now,
    coaf_protocol_number: payload.coaf_protocol_number.trim(),
    coaf_receipt_hash: receiptHash
  } satisfies ShowcaseRosCoafSubmitResponse;
}

export function buildStandaloneShowcaseRosCoafRegulatoryDossier(rosId: string) {
  const current = findStandaloneShowcaseRosCoafById(rosId);
  if (!current) {
    return null;
  }
  const now = new Date().toISOString();
  const filename = `ontrackchain-ros-coaf-regulatory-dossier-${current.ros_id}.json`;
  const dossierSha256 = buildStandaloneShowcaseHash(`${current.ros_id}-dossier-${current.updated_at}`);
  appendStandaloneShowcaseRosAudit(
    current.ros_id,
    "coaf_regulatory_dossier_downloaded",
    now,
    {
      filename,
      dossier_sha256: dossierSha256
    },
    current.report_id,
    current.pdf_hash
  );
  const refreshed = findStandaloneShowcaseRosCoafById(current.ros_id) ?? current;
  return {
    filename,
    dossierSha256,
    content: {
      mode: "standalone_showcase",
      generated_at: now,
      ros: cloneStandaloneRosCoafRecord(refreshed),
      report: resolveStandaloneShowcaseReport(refreshed.report_id),
      audit_logs: listStandaloneShowcaseAuditLogs({
        resourceType: "ros_record",
        resourceId: refreshed.ros_id,
        limit: 200
      }).data
    }
  };
}

function cloneShowcaseCounterparty(item: ShowcaseCounterpartyRecord): ShowcaseCounterpartyRecord {
  return { ...item };
}

function findShowcaseCounterpartyIndex(counterpartyId: string) {
  return standaloneShowcaseCounterpartiesStore.findIndex((item) => item.id === counterpartyId);
}

function buildShowcaseCounterpartyCreateResponse(item: ShowcaseCounterpartyRecord) {
  return {
    counterparty_id: item.id,
    legal_name: item.legal_name,
    risk_level: item.risk_level,
    kyc_status: item.kyc_status,
    sanctions_cleared: item.sanctions_cleared,
    is_pep: item.is_pep,
    enhanced_dd_required: item.enhanced_dd_required,
    next_review_date: item.next_review_date ?? "",
    status: item.status
  };
}

export function listStandaloneShowcaseCounterparties(input: { limit?: number | null; offset?: number | null }) {
  const limit = typeof input.limit === "number" && input.limit > 0 ? input.limit : 20;
  const offset = typeof input.offset === "number" && input.offset >= 0 ? input.offset : 0;
  const ordered = standaloneShowcaseCounterpartiesStore
    .slice()
    .sort((left, right) => right.created_at.localeCompare(left.created_at));
  return {
    items: ordered.slice(offset, offset + limit).map(cloneShowcaseCounterparty),
    total: ordered.length
  };
}

export function createStandaloneShowcaseCounterparty(payload: {
  counterparty_type?: string | null;
  legal_name?: string | null;
  document_type?: string | null;
  document_number?: string | null;
  wallet_addresses?: Array<{ chain?: string | null; address?: string | null; label?: string | null }> | null;
  declared_risk_context?: string | null;
  onchain_risk_score?: number | null;
}) {
  const legalName = payload.legal_name?.trim() ?? "";
  const documentNumber = payload.document_number?.trim() ?? "";
  if (!legalName || !documentNumber) {
    return null;
  }
  const now = new Date().toISOString();
  const wallet = payload.wallet_addresses?.[0] ?? null;
  const onchainRiskScore = typeof payload.onchain_risk_score === "number" ? payload.onchain_risk_score : null;
  const riskLevel = onchainRiskScore !== null ? Math.max(1, Math.min(4, Math.ceil(onchainRiskScore / 25))) : 2;
  const nextItem: ShowcaseCounterpartyRecord = {
    id: crypto.randomUUID(),
    legal_name: legalName,
    counterparty_type: payload.counterparty_type?.trim() || "CLIENTE_PJ",
    document_type: payload.document_type?.trim() || "CNPJ",
    document_number: documentNumber,
    risk_level: riskLevel,
    kyc_status: "PENDING",
    sanctions_cleared: false,
    is_pep: false,
    enhanced_dd_required: riskLevel >= 3,
    next_review_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    status: "UNDER_REVIEW",
    created_at: now,
    dd_review_status: "pending",
    dd_review_note: payload.declared_risk_context?.trim() || "",
    sof_description: "",
    sof_document_ref: "",
    last_reviewed_at: null,
    wallet_chain: wallet?.chain?.trim() || "",
    wallet_address: wallet?.address?.trim() || "",
    wallet_label: wallet?.label?.trim() || ""
  };
  standaloneShowcaseCounterpartiesStore = [nextItem, ...standaloneShowcaseCounterpartiesStore];
  return buildShowcaseCounterpartyCreateResponse(nextItem);
}

export function reviewStandaloneShowcaseCounterparty(
  counterpartyId: string,
  payload: {
    dd_review_status?: string | null;
    dd_review_note?: string | null;
    sof_description?: string | null;
    sof_document_ref?: string | null;
  }
) {
  const currentIndex = findShowcaseCounterpartyIndex(counterpartyId);
  if (currentIndex < 0) {
    return null;
  }
  const now = new Date().toISOString();
  const current = standaloneShowcaseCounterpartiesStore[currentIndex];
  const nextItem: ShowcaseCounterpartyRecord = {
    ...current,
    dd_review_status: payload.dd_review_status?.trim() || current.dd_review_status || "pending",
    dd_review_note: payload.dd_review_note?.trim() ?? current.dd_review_note ?? "",
    sof_description: payload.sof_description?.trim() ?? current.sof_description ?? "",
    sof_document_ref: payload.sof_document_ref?.trim() ?? current.sof_document_ref ?? "",
    last_reviewed_at: now
  };
  standaloneShowcaseCounterpartiesStore[currentIndex] = nextItem;
  return {
    counterparty_id: nextItem.id,
    dd_review_status: nextItem.dd_review_status ?? "pending",
    dd_review_note: nextItem.dd_review_note ?? "",
    sof_description: nextItem.sof_description ?? "",
    sof_document_ref: nextItem.sof_document_ref ?? "",
    last_reviewed_at: nextItem.last_reviewed_at ?? now
  };
}

function cloneShowcaseBillingLedgerEntry(entry: ShowcaseBillingLedgerEntryRecord): ShowcaseBillingLedgerEntryRecord {
  return { ...entry, metadata: { ...entry.metadata } };
}

function cloneShowcaseBillingActionTotal(entry: ShowcaseBillingActionTotalRecord): ShowcaseBillingActionTotalRecord {
  return { ...entry };
}

export function getStandaloneShowcaseBillingBalance(): ShowcaseBillingBalanceRecord {
  return { ...STANDALONE_SHOWCASE_BILLING_BALANCE };
}

export function getStandaloneShowcaseBillingReconciliation(limit?: number | null): ShowcaseBillingReconciliationRecord {
  const resolvedLimit = typeof limit === "number" && limit > 0 ? limit : 5;
  const orderedLedger = STANDALONE_SHOWCASE_BILLING_LEDGER_SEEDS
    .slice()
    .sort((left, right) => (right.created_at ?? "").localeCompare(left.created_at ?? ""));
  const recent = orderedLedger.slice(0, resolvedLimit).map(cloneShowcaseBillingLedgerEntry);
  const actionTotalsMap = new Map<string, ShowcaseBillingActionTotalRecord>();
  for (const entry of orderedLedger) {
    const current = actionTotalsMap.get(entry.action) ?? {
      action: entry.action,
      entry_count: 0,
      amount_total: 0
    };
    current.entry_count += 1;
    current.amount_total += entry.amount ?? 0;
    actionTotalsMap.set(entry.action, current);
  }

  return {
    generated_at: new Date().toISOString(),
    balance: getStandaloneShowcaseBillingBalance(),
    quotes: {
      investigation: { open_total: 2, expired_total: 1 },
      compliance: { open_total: 1, expired_total: 1 },
      monitoring: { open_total: 3, expired_total: 2 },
      open_total: 6,
      expired_total: 4
    },
    ledger: {
      total_entries: orderedLedger.length,
      action_totals: Array.from(actionTotalsMap.values())
        .sort((left, right) => right.entry_count - left.entry_count || left.action.localeCompare(right.action))
        .map(cloneShowcaseBillingActionTotal),
      recent
    }
  };
}

export function exportStandaloneShowcaseBillingReconciliation(limit?: number | null) {
  const snapshot = getStandaloneShowcaseBillingReconciliation(limit);
  return {
    filename: "billing-reconciliation-showcase.json",
    contentType: "application/json; charset=utf-8",
    body: JSON.stringify(snapshot, null, 2)
  };
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

function cloneShowcaseMonitoringAlert(alert: Alert): Alert {
  return { ...alert, details: { ...(alert.details ?? {}) } };
}

function cloneShowcasePlatformAlert(alert: ShowcasePlatformAlertRecord): ShowcasePlatformAlertRecord {
  return { ...alert, labels: { ...alert.labels }, annotations: { ...alert.annotations } };
}

function cloneShowcaseDlqCase(entry: ShowcaseDlqCaseRecord): ShowcaseDlqCaseRecord {
  return { ...entry };
}

function buildStandaloneShowcaseOperationalAlertsSnapshot(): OperationalAlertsSnapshot {
  const acknowledgedPlatformAlerts = standaloneShowcasePlatformAlertsStore.filter((entry) => entry.triage_status === "acknowledged").length;
  return {
    generated_at: new Date().toISOString(),
    open_total: STANDALONE_SHOWCASE_OPERATIONAL_ALERT_SEED_BASE.filter((entry) => entry.status === "open").length,
    critical_open_total: STANDALONE_SHOWCASE_OPERATIONAL_ALERT_SEED_BASE.filter(
      (entry) => entry.status === "open" && entry.severity === "critical"
    ).length,
    alerts: STANDALONE_SHOWCASE_OPERATIONAL_ALERT_SEED_BASE.map((entry, index) => {
      if (index === 1 && acknowledgedPlatformAlerts > 0) {
        return {
          ...entry,
          value: Math.max(0, entry.value - acknowledgedPlatformAlerts * 5)
        };
      }
      return { ...entry };
    })
  };
}

function buildStandaloneShowcaseOperationsSnapshot(): OperationsSnapshot {
  const dlqFailed = standaloneShowcaseDlqStore.filter((entry) => entry.dlq_state === "failed_permanent").length;
  const dlqResolved = standaloneShowcaseDlqStore.filter(
    (entry) => entry.dlq_state === "acknowledged" || entry.dlq_state === "discarded" || entry.dlq_state === "resolved"
  ).length;
  const recentCases = STANDALONE_SHOWCASE_OPERATION_RECENT_CASES.map((entry) => {
    const dlqEntry = standaloneShowcaseDlqStore.find((candidate) => candidate.case_id === entry.case_id);
    if (!dlqEntry) {
      return { ...entry };
    }
    return {
      ...entry,
      status: dlqEntry.dlq_state === "failed_permanent" ? "failed" : "queued",
      queue_state: dlqEntry.dlq_state === "failed_permanent" ? "dlq_failed" : "queued",
      last_error: dlqEntry.dlq_state === "failed_permanent" ? dlqEntry.failure_reason : null,
      completed_at: dlqEntry.dlq_state === "failed_permanent" ? null : new Date().toISOString()
    };
  });
  return {
    ...STANDALONE_SHOWCASE_OPERATIONS_BASE,
    states: {
      queued: STANDALONE_SHOWCASE_OPERATIONS_BASE.queue.ready + STANDALONE_SHOWCASE_OPERATIONS_BASE.queue.waiting,
      processing: STANDALONE_SHOWCASE_OPERATIONS_BASE.concurrency.global_active,
      dlq_failed: dlqFailed,
      dlq_resolved: dlqResolved
    },
    recent_cases: recentCases,
    generated_at: new Date().toISOString()
  };
}

function buildStandaloneShowcaseMetricsPreview() {
  const operations = buildStandaloneShowcaseOperationsSnapshot();
  const operationalAlerts = buildStandaloneShowcaseOperationalAlertsSnapshot();
  return [
    "# HELP otc_showcase_queue_ready Cases prontos para processamento no showcase",
    "# TYPE otc_showcase_queue_ready gauge",
    `otc_showcase_queue_ready ${operations.queue.ready}`,
    "# HELP otc_showcase_dlq_failed Casos em DLQ permanente",
    "# TYPE otc_showcase_dlq_failed gauge",
    `otc_showcase_dlq_failed ${operations.states.dlq_failed}`,
    "# HELP otc_showcase_platform_alerts_open Alertas de plataforma ainda abertos",
    "# TYPE otc_showcase_platform_alerts_open gauge",
    `otc_showcase_platform_alerts_open ${operationalAlerts.open_total}`
  ].join("\n");
}

function matchesPlatformAlertFilters(entry: ShowcasePlatformAlertRecord, filters: PlatformAlertFilterState) {
  return (
    (filters.status === "all" || entry.status === filters.status) &&
    (filters.triageStatus === "all" || entry.triage_status === filters.triageStatus) &&
    (filters.service === "all" || (entry.service ?? "") === filters.service) &&
    (filters.receiver === "all" || entry.receiver === filters.receiver) &&
    (filters.severity === "all" || (entry.severity ?? "") === filters.severity)
  );
}

function resolveStandaloneShowcasePlatformAlertsByPayload(payload: {
  ids?: string[] | null;
  status?: string | null;
  triage_status?: string | null;
  service?: string | null;
  receiver?: string | null;
  severity?: string | null;
}) {
  const selectedIds = Array.isArray(payload.ids) ? new Set(payload.ids.filter(Boolean)) : null;
  const filters: PlatformAlertFilterState = {
    status: payload.status?.trim() || "all",
    triageStatus: payload.triage_status?.trim() || "all",
    service: payload.service?.trim() || "all",
    receiver: payload.receiver?.trim() || "all",
    severity: payload.severity?.trim() || "all"
  };
  return standaloneShowcasePlatformAlertsStore.filter((entry) => {
    if (selectedIds) {
      return selectedIds.has(entry.id);
    }
    return matchesPlatformAlertFilters(entry, filters);
  });
}

export function listStandaloneShowcaseMonitoringWatchlists() {
  return {
    data: STANDALONE_SHOWCASE_MONITORING_WATCHLISTS.map((entry) => ({ ...entry }))
  };
}

export function listStandaloneShowcaseMonitoringWatchlistItems(watchlistId: string, limit = 20) {
  const resolvedLimit = Number.isFinite(limit) && limit > 0 ? limit : 20;
  return {
    data: (STANDALONE_SHOWCASE_MONITORING_WATCHLIST_ITEMS[watchlistId] ?? []).slice(0, resolvedLimit).map((entry) => ({ ...entry }))
  };
}

export function listStandaloneShowcaseMonitoringAlerts(filters: { watchlistId?: string | null; limit?: number | null }) {
  const resolvedLimit = typeof filters.limit === "number" && filters.limit > 0 ? filters.limit : 50;
  const filtered = standaloneShowcaseMonitoringAlertsStore.filter(
    (entry) => !filters.watchlistId?.trim() || entry.watchlist_id === filters.watchlistId.trim()
  );
  return {
    data: filtered
      .slice()
      .sort((left, right) => right.created_at.localeCompare(left.created_at))
      .slice(0, resolvedLimit)
      .map(cloneShowcaseMonitoringAlert)
  };
}

export function createStandaloneShowcaseMonitoringAlert(payload: {
  watchlist_id: string;
  address: string;
  chain: string;
  severity?: string;
  title?: string;
  details?: Record<string, unknown>;
}) {
  const now = new Date().toISOString();
  const alert: Alert = {
    id: crypto.randomUUID(),
    watchlist_id: payload.watchlist_id,
    address: payload.address,
    chain: payload.chain,
    severity: payload.severity?.trim() || "high",
    title: payload.title?.trim() || "Manual showcase alert",
    details: payload.details ?? {},
    created_at: now
  };
  standaloneShowcaseMonitoringAlertsStore = [alert, ...standaloneShowcaseMonitoringAlertsStore];

  const platformAlert: ShowcasePlatformAlertRecord = {
    id: crypto.randomUUID(),
    receiver: "slack-secops",
    status: "firing",
    triage_status: "pending",
    alertname: "WatchlistSignalRaised",
    service: "watchlists",
    severity: alert.severity,
    fingerprint: `fp-${alert.id}`,
    labels: { chain: alert.chain, source: "showcase_trigger", watchlist_id: alert.watchlist_id },
    annotations: {
      summary: alert.title,
      description: `Triggered for ${alert.address} on ${alert.chain}.`
    },
    first_received_at: now,
    last_received_at: now,
    delivery_count: 1,
    resolved_at: null,
    triaged_at: null,
    triaged_by: null,
    triage_note: null
  };
  standaloneShowcasePlatformAlertsStore = [platformAlert, ...standaloneShowcasePlatformAlertsStore];
  return cloneShowcaseMonitoringAlert(alert);
}

export function listStandaloneShowcasePlatformAlertFilterOptions(): PlatformOperationalAlertFilterOptions {
  return {
    services: Array.from(new Set(standaloneShowcasePlatformAlertsStore.map((entry) => entry.service).filter(Boolean) as string[])).sort(),
    receivers: Array.from(new Set(standaloneShowcasePlatformAlertsStore.map((entry) => entry.receiver).filter(Boolean))).sort(),
    generated_at: new Date().toISOString()
  };
}

export function listStandaloneShowcasePlatformOperationalAlerts(input: {
  filters: PlatformAlertFilterState;
  cursor?: string | null;
  limit?: number | null;
}): PlatformOperationalAlertsSnapshot {
  const resolvedLimit = typeof input.limit === "number" && input.limit > 0 ? input.limit : 20;
  const filtered = standaloneShowcasePlatformAlertsStore
    .filter((entry) => matchesPlatformAlertFilters(entry, input.filters))
    .sort((left, right) => right.last_received_at.localeCompare(left.last_received_at));
  const count = Math.min(filtered.length, resolvedLimit);
  return {
    status_filter: input.filters.status === "all" ? null : input.filters.status,
    triage_status_filter: input.filters.triageStatus === "all" ? null : input.filters.triageStatus,
    service_filter: input.filters.service === "all" ? null : input.filters.service,
    receiver_filter: input.filters.receiver === "all" ? null : input.filters.receiver,
    severity_filter: input.filters.severity === "all" ? null : input.filters.severity,
    cursor: input.cursor?.trim() || null,
    limit: resolvedLimit,
    total_count: filtered.length,
    count,
    has_more: filtered.length > resolvedLimit,
    next_cursor: filtered.length > resolvedLimit ? String(resolvedLimit) : null,
    data: filtered.slice(0, resolvedLimit).map(cloneShowcasePlatformAlert)
  };
}

export function acknowledgeStandaloneShowcasePlatformAlert(eventId: string, payload: { note?: string | null; triaged_by?: string | null }) {
  const now = new Date().toISOString();
  let updated: ShowcasePlatformAlertRecord | null = null;
  standaloneShowcasePlatformAlertsStore = standaloneShowcasePlatformAlertsStore.map((entry) => {
    if (entry.id !== eventId) {
      return entry;
    }
    updated = {
      ...entry,
      triage_status: "acknowledged",
      triaged_at: now,
      triaged_by: payload.triaged_by?.trim() || "showcase-admin",
      triage_note: payload.note?.trim() || "ack_from_showcase"
    };
    return updated;
  });
  return updated ? cloneShowcasePlatformAlert(updated) : null;
}

export function acknowledgeStandaloneShowcasePlatformAlerts(payload: {
  ids?: string[] | null;
  note?: string | null;
  triaged_by?: string | null;
  status?: string | null;
  triage_status?: string | null;
  service?: string | null;
  receiver?: string | null;
  severity?: string | null;
}) {
  const targets = new Set(
    resolveStandaloneShowcasePlatformAlertsByPayload(payload)
      .filter((entry) => entry.triage_status !== "acknowledged")
      .map((entry) => entry.id)
  );
  const now = new Date().toISOString();
  let updatedCount = 0;
  standaloneShowcasePlatformAlertsStore = standaloneShowcasePlatformAlertsStore.map((entry) => {
    if (!targets.has(entry.id)) {
      return entry;
    }
    updatedCount += 1;
    return {
      ...entry,
      triage_status: "acknowledged",
      triaged_at: now,
      triaged_by: payload.triaged_by?.trim() || "showcase-admin",
      triage_note: payload.note?.trim() || "ack_batch_from_showcase"
    };
  });
  return {
    updated_count: updatedCount,
    generated_at: now
  };
}

export function exportStandaloneShowcasePlatformAlerts(payload: {
  format?: PlatformAlertExportFormat;
  scope?: "filtered" | "selected";
  ids?: string[] | null;
  status?: string | null;
  triage_status?: string | null;
  service?: string | null;
  receiver?: string | null;
  severity?: string | null;
}) {
  const format = payload.format === "json" ? "json" : "csv";
  const rows = resolveStandaloneShowcasePlatformAlertsByPayload(payload);
  if (format === "json") {
    return {
      filename: `monitoring-operational-alerts-${payload.scope ?? "filtered"}.json`,
      contentType: "application/json; charset=utf-8",
      body: JSON.stringify({ data: rows.map(cloneShowcasePlatformAlert) }, null, 2)
    };
  }
  const header = ["id", "alertname", "service", "receiver", "status", "triage_status", "severity", "last_received_at"];
  const csvRows = rows.map((entry) =>
    [entry.id, entry.alertname, entry.service ?? "", entry.receiver, entry.status, entry.triage_status, entry.severity ?? "", entry.last_received_at]
      .map((value) => `"${String(value).replace(/"/g, '""')}"`)
      .join(",")
  );
  return {
    filename: `monitoring-operational-alerts-${payload.scope ?? "filtered"}.csv`,
    contentType: "text/csv; charset=utf-8",
    body: [header.join(","), ...csvRows].join("\n")
  };
}

export function getStandaloneShowcaseInvestigationOperations() {
  return buildStandaloneShowcaseOperationsSnapshot();
}

export function getStandaloneShowcaseInvestigationOperationalAlerts() {
  return buildStandaloneShowcaseOperationalAlertsSnapshot();
}

export function getStandaloneShowcaseInvestigationMetricsPreview() {
  return `${buildStandaloneShowcaseMetricsPreview()}\n`;
}

export function getStandaloneShowcaseDlq(input: {
  state?: string | null;
  targetChain?: string | null;
  limit?: number | null;
}): DlqSnapshot {
  const state = input.state?.trim() || "failed_permanent";
  const targetChain = input.targetChain?.trim() || null;
  const resolvedLimit = typeof input.limit === "number" && input.limit > 0 ? input.limit : 100;
  const filtered = standaloneShowcaseDlqStore.filter((entry) => {
    const stateMatches = state === "all" || (entry.dlq_state ?? "") === state;
    const chainMatches = !targetChain || entry.target_chain === targetChain;
    return stateMatches && chainMatches;
  });
  return {
    count: filtered.length,
    credits_available: 120,
    filters: {
      state,
      target_chain: targetChain,
      can_requeue: state === "failed_permanent" ? true : null,
      limit: resolvedLimit
    },
    cases: filtered.slice(0, resolvedLimit).map(cloneShowcaseDlqCase),
    generated_at: new Date().toISOString()
  };
}

export function requeueStandaloneShowcaseDlqCase(caseId: string, payload: { reason?: string | null }) {
  const entry = standaloneShowcaseDlqStore.find((candidate) => candidate.case_id === caseId) ?? null;
  if (!entry) {
    return null;
  }
  const nextEntry: ShowcaseDlqCaseRecord = {
    ...entry,
    status: "queued",
    dlq_state: "resolved",
    dlq_requeue_count: entry.dlq_requeue_count + 1,
    dlq_resolution_note: payload.reason?.trim() || "manual_requeue_from_showcase",
    dlq_acknowledged_at: new Date().toISOString(),
    dlq_acknowledged_by: "showcase-admin",
    can_requeue: false
  };
  standaloneShowcaseDlqStore = standaloneShowcaseDlqStore.map((candidate) => (candidate.case_id === caseId ? nextEntry : candidate));
  return {
    case_id: caseId,
    status: "queued",
    dlq_state: nextEntry.dlq_state,
    resolution_note: nextEntry.dlq_resolution_note
  };
}

export function resolveStandaloneShowcaseDlqCase(
  caseId: string,
  payload: { action?: "acknowledged" | "discarded"; note?: string | null }
) {
  const entry = standaloneShowcaseDlqStore.find((candidate) => candidate.case_id === caseId) ?? null;
  if (!entry) {
    return null;
  }
  const action = payload.action === "discarded" ? "discarded" : "acknowledged";
  const nextEntry: ShowcaseDlqCaseRecord = {
    ...entry,
    dlq_state: action,
    dlq_acknowledged_at: new Date().toISOString(),
    dlq_acknowledged_by: "showcase-admin",
    dlq_resolution_note: payload.note?.trim() || action
  };
  standaloneShowcaseDlqStore = standaloneShowcaseDlqStore.map((candidate) => (candidate.case_id === caseId ? nextEntry : candidate));
  return {
    case_id: caseId,
    dlq_state: nextEntry.dlq_state,
    note: nextEntry.dlq_resolution_note
  };
}

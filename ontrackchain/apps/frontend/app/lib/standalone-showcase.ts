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

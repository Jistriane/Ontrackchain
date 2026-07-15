export const STANDALONE_SHOWCASE_AUTH_CONTEXT = {
  authenticated: true,
  org_id: "showcase-org",
  user_id: "showcase-user",
  linked_user_id: "showcase-user",
  role: "ADMIN",
  plan: "enterprise",
  auth_method: "standalone_showcase",
  mfa_mode: "managed_externally",
  mfa_provider_homologated: "showcase",
  two_factor: "managed_externally"
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

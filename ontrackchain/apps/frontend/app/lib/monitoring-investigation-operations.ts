export type OperationsSnapshot = {
  queue: {
    ready: number;
    waiting: number;
    retry_pending: number;
    retry_due: number;
    wake_signals: number;
  };
  concurrency: {
    org_active: number;
    org_limit: number;
    global_active: number;
    global_limit: number;
    plan: string;
  };
  throughput: {
    completed_last_hour: number;
    failed_last_hour: number;
    billing_recalc_last_hour: number;
    avg_duration_ms_last_20: number;
  };
  states: {
    queued: number;
    processing: number;
    dlq_failed: number;
    dlq_resolved: number;
  };
  recent_cases: Array<{
    case_id: string;
    status: string;
    target_address: string;
    target_chain: string;
    created_at: string | null;
    completed_at: string | null;
    queue_state: string | null;
    last_error: string | null;
    attempt_count: number;
    report_type_canonical: string | null;
    charged_cost: number | null;
    duration_ms: number | null;
  }>;
  security: {
    manual_package_mfa_violations_last_hour: number;
    manual_package_mfa_2fa_required_last_hour: number;
    manual_package_mfa_provider_not_homologated_last_hour: number;
  };
  generated_at: string;
};

export const EMPTY_OPERATIONS_SNAPSHOT: OperationsSnapshot = {
  queue: {
    ready: 0,
    waiting: 0,
    retry_pending: 0,
    retry_due: 0,
    wake_signals: 0
  },
  concurrency: {
    org_active: 0,
    org_limit: 0,
    global_active: 0,
    global_limit: 0,
    plan: "unknown"
  },
  throughput: {
    completed_last_hour: 0,
    failed_last_hour: 0,
    billing_recalc_last_hour: 0,
    avg_duration_ms_last_20: 0
  },
  states: {
    queued: 0,
    processing: 0,
    dlq_failed: 0,
    dlq_resolved: 0
  },
  recent_cases: [],
  security: {
    manual_package_mfa_violations_last_hour: 0,
    manual_package_mfa_2fa_required_last_hour: 0,
    manual_package_mfa_provider_not_homologated_last_hour: 0
  },
  generated_at: ""
};

export function normalizeOperationsSnapshot(snapshot: Partial<OperationsSnapshot> | null | undefined): OperationsSnapshot {
  return {
    queue: {
      ...EMPTY_OPERATIONS_SNAPSHOT.queue,
      ...(snapshot?.queue ?? {})
    },
    concurrency: {
      ...EMPTY_OPERATIONS_SNAPSHOT.concurrency,
      ...(snapshot?.concurrency ?? {})
    },
    throughput: {
      ...EMPTY_OPERATIONS_SNAPSHOT.throughput,
      ...(snapshot?.throughput ?? {})
    },
    states: {
      ...EMPTY_OPERATIONS_SNAPSHOT.states,
      ...(snapshot?.states ?? {})
    },
    recent_cases: Array.isArray(snapshot?.recent_cases) ? snapshot.recent_cases : EMPTY_OPERATIONS_SNAPSHOT.recent_cases,
    security: {
      ...EMPTY_OPERATIONS_SNAPSHOT.security,
      ...(snapshot?.security ?? {})
    },
    generated_at: typeof snapshot?.generated_at === "string" ? snapshot.generated_at : EMPTY_OPERATIONS_SNAPSHOT.generated_at
  };
}

export type OperationalAlertsSnapshot = {
  generated_at: string;
  open_total: number;
  critical_open_total: number;
  alerts: Array<{
    code: string;
    severity: string;
    status: string;
    metric: string;
    value: number;
    threshold: number;
    title: string;
    message: string;
    recommended_action: string;
  }>;
};

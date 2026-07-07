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
  generated_at: string;
};

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

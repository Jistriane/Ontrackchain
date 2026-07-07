export type DlqSnapshot = {
  count: number;
  credits_available: number;
  filters: {
    state: string;
    target_chain: string | null;
    can_requeue: boolean | null;
    limit: number;
  };
  cases: Array<{
    case_id: string;
    status: string;
    target_address: string;
    target_chain: string;
    created_at: string | null;
    completed_at: string | null;
    report_type_canonical: string | null;
    failure_reason: string | null;
    dlq_state: string | null;
    dlq_failed_at: string | null;
    dlq_requeue_count: number;
    dlq_acknowledged_at: string | null;
    dlq_acknowledged_by: string | null;
    dlq_resolution_note: string | null;
    attempt_count: number;
    max_attempts: number;
    credits_estimated: number;
    credits_available: number;
    can_requeue: boolean;
  }>;
  generated_at: string;
};

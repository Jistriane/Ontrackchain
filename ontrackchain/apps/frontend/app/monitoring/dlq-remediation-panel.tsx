import { Message, Panel } from "../../components/ui";
import type { MessageKey } from "../lib/i18n";
import type { DlqSnapshot } from "../lib/monitoring-dlq";

type Translator = (key: MessageKey, values?: Record<string, string | number>) => string;

type DlqRemediationPanelProps = {
  t: Translator;
  dlqFilterState: string;
  setDlqFilterState: (value: string) => void;
  dlqFilterChain: string;
  setDlqFilterChain: (value: string) => void;
  refreshDlq: () => void;
  dlq: DlqSnapshot | null;
  dlqMessage: string | null;
  caseAuditHref: (caseId: string, reportId?: string | null) => string;
  caseEvidenceHref: (caseId: string, reportId?: string | null) => string;
  requeueDlqCase: (caseId: string) => void;
  resolveDlqCase: (caseId: string, action: "acknowledged" | "discarded") => void;
  requeueingCaseId: string | null;
  resolvingCaseId: string | null;
};

export function DlqRemediationPanel({
  t,
  dlqFilterState,
  setDlqFilterState,
  dlqFilterChain,
  setDlqFilterChain,
  refreshDlq,
  dlq,
  dlqMessage,
  caseAuditHref,
  caseEvidenceHref,
  requeueDlqCase,
  resolveDlqCase,
  requeueingCaseId,
  resolvingCaseId
}: DlqRemediationPanelProps) {
  return (
    <Panel title={t("monitoring.dlq.title")}>
      <div className="otc-controls">
        <select
          aria-label={t("monitoring.dlq.filters.stateAria")}
          data-testid="dlq-filter-state"
          value={dlqFilterState}
          onChange={(event) => setDlqFilterState(event.target.value)}
          className="otc-select"
        >
          <option value="failed_permanent">{t("monitoring.dlq.state.open")}</option>
          <option value="resolved">{t("monitoring.dlq.state.resolved")}</option>
          <option value="acknowledged">{t("monitoring.dlq.state.archived")}</option>
          <option value="discarded">{t("monitoring.dlq.state.discarded")}</option>
          <option value="all">{t("monitoring.dlq.state.all")}</option>
        </select>
        <select
          aria-label={t("monitoring.dlq.filters.chainAria")}
          data-testid="dlq-filter-chain"
          value={dlqFilterChain}
          onChange={(event) => setDlqFilterChain(event.target.value)}
          className="otc-select"
        >
          <option value="all">{t("monitoring.dlq.chainAll")}</option>
          <option value="ethereum">Ethereum</option>
          <option value="bitcoin">Bitcoin</option>
          <option value="arbitrum">Arbitrum</option>
          <option value="base">Base</option>
        </select>
        <button type="button" data-testid="dlq-refresh-btn" onClick={refreshDlq} className="otc-button otc-button--ghost">
          {t("monitoring.dlq.refresh")}
        </button>
        <span data-testid="dlq-generated-at" className="otc-monitoring-meta">
          {dlq ? t("monitoring.dlq.snapshot", { value: dlq.generated_at }) : t("monitoring.platform.noSnapshot")}
        </span>
        {dlq ? (
          <span data-testid="dlq-credits-available" className="otc-monitoring-meta">
            {t("monitoring.dlq.creditsAvailable", { count: dlq.credits_available })}
          </span>
        ) : null}
      </div>

      {dlqMessage ? (
        <div data-testid="dlq-message" className="otc-monitoring-banner">
          <Message tone="success">{dlqMessage}</Message>
        </div>
      ) : null}

      {dlq ? (
        dlq.cases.length ? (
          <div className="otc-monitoring-grid otc-monitoring-banner">
            {dlq.cases.map((entry) => (
              <div key={entry.case_id} data-testid="dlq-case-row" className="otc-monitoring-card otc-monitoring-card--warning">
                <div className="otc-monitoring-row">
                  <strong>{entry.case_id}</strong>
                  <span className="otc-monitoring-meta">{entry.dlq_failed_at ?? entry.completed_at ?? t("common.noTimestamp")}</span>
                </div>
                <div className="otc-monitoring-detail">
                  {entry.target_chain} • {entry.report_type_canonical ?? t("common.notAvailable")} • {t("monitoring.dlq.attempt")}{" "}
                  {entry.attempt_count}/{entry.max_attempts}
                </div>
                <div className="otc-monitoring-detail--subtle">
                  {t("monitoring.dlq.cost")}={entry.credits_estimated} • {t("monitoring.dlq.requeues")}={entry.dlq_requeue_count} •{" "}
                  {t("monitoring.dlq.stateLabel")}={entry.dlq_state ?? t("common.notAvailable")}
                </div>
                {entry.failure_reason ? <div className="otc-monitoring-detail--subtle">{t("monitoring.dlq.errorLabel")}: {entry.failure_reason}</div> : null}
                {entry.dlq_acknowledged_at ? (
                  <div className="otc-monitoring-detail--subtle">
                    {t("monitoring.dlq.resolvedAt")} {entry.dlq_acknowledged_at} {t("common.by")}{" "}
                    {entry.dlq_acknowledged_by ?? t("monitoring.platform.adminFallback")}
                  </div>
                ) : null}
                {entry.dlq_resolution_note ? (
                  <div className="otc-monitoring-detail--subtle">{t("monitoring.dlq.note")}: {entry.dlq_resolution_note}</div>
                ) : null}
                <div className="otc-monitoring-actions">
                  <a className="otc-button otc-button--ghost" href={`/cases/${entry.case_id}`}>
                    {t("monitoring.dlq.openCase")}
                  </a>
                  <a className="otc-button otc-button--ghost" href={caseAuditHref(entry.case_id, null)}>
                    {t("monitoring.dlq.openAudit")}
                  </a>
                  <a className="otc-button otc-button--ghost" href={caseEvidenceHref(entry.case_id, null)}>
                    {t("monitoring.dlq.openEvidence")}
                  </a>
                  <button
                    type="button"
                    data-testid={`dlq-requeue-btn-${entry.case_id}`}
                    onClick={() => requeueDlqCase(entry.case_id)}
                    disabled={entry.dlq_state !== "failed_permanent" || !entry.can_requeue || requeueingCaseId === entry.case_id}
                    className="otc-button"
                  >
                    {requeueingCaseId === entry.case_id ? t("monitoring.dlq.requeueLoading") : t("monitoring.dlq.requeue")}
                  </button>
                  <button
                    type="button"
                    data-testid={`dlq-ack-btn-${entry.case_id}`}
                    onClick={() => resolveDlqCase(entry.case_id, "acknowledged")}
                    disabled={entry.dlq_state !== "failed_permanent" || resolvingCaseId === entry.case_id}
                    className="otc-button otc-button--ghost"
                  >
                    {resolvingCaseId === entry.case_id ? t("monitoring.dlq.archiveLoading") : t("monitoring.dlq.archive")}
                  </button>
                  <button
                    type="button"
                    data-testid={`dlq-discard-btn-${entry.case_id}`}
                    onClick={() => resolveDlqCase(entry.case_id, "discarded")}
                    disabled={entry.dlq_state !== "failed_permanent" || resolvingCaseId === entry.case_id}
                    className="otc-button otc-button--ghost"
                  >
                    {resolvingCaseId === entry.case_id ? t("monitoring.dlq.discardLoading") : t("monitoring.dlq.discard")}
                  </button>
                </div>
                {!entry.can_requeue ? <div className="otc-monitoring-detail--subtle">{t("monitoring.dlq.insufficientCredits")}</div> : null}
              </div>
            ))}
          </div>
        ) : (
          <div data-testid="dlq-empty" className="otc-monitoring-banner">
            <Message>{t("monitoring.dlq.empty")}</Message>
          </div>
        )
      ) : (
        <div data-testid="dlq-loading" className="otc-monitoring-banner">
          <Message>{t("monitoring.dlq.loading")}</Message>
        </div>
      )}
    </Panel>
  );
}

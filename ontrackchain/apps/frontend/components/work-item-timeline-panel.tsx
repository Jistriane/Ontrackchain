"use client";

import { Message, Panel } from "./ui";
import type { TimelineLabels } from "../app/lib/work-item-timeline-labels";
import type { WorkCommentResponse, WorkItemTimelineResponse } from "../app/lib/work-item-timeline";

type WorkItemTimelinePanelProps<TItem> = {
  state: "empty_selection" | "local_only" | "ready";
  summary: string | null;
  labels: TimelineLabels;
  timelineError: string | null;
  timelineData: WorkItemTimelineResponse<TItem> | null;
  timelineLoading: boolean;
  commentType: WorkCommentResponse["comment_type"];
  commentBody: string;
  commentSubmitting: boolean;
  onCommentTypeChange: (value: WorkCommentResponse["comment_type"]) => void;
  onCommentBodyChange: (value: string) => void;
  onCommentSubmit: () => void;
  onRefresh?: () => void;
  formatDate: (value: string | null | undefined) => string | null;
  formatEventLabel: (event: WorkItemTimelineResponse<TItem>["events"][number]) => string;
};

export function WorkItemTimelinePanel<TItem>({
  state,
  summary,
  labels,
  timelineError,
  timelineData,
  timelineLoading,
  commentType,
  commentBody,
  commentSubmitting,
  onCommentTypeChange,
  onCommentBodyChange,
  onCommentSubmit,
  onRefresh,
  formatDate,
  formatEventLabel
}: WorkItemTimelinePanelProps<TItem>) {
  return (
    <Panel
      title={labels.title}
      description={labels.description}
      actions={
        state === "ready" && onRefresh ? (
          <button
            className="otc-button otc-button--ghost"
            type="button"
            data-testid="work-item-timeline-refresh"
            onClick={onRefresh}
            disabled={timelineLoading}
          >
            {timelineLoading ? labels.refreshing : labels.refresh}
          </button>
        ) : null
      }
    >
      {state === "empty_selection" ? (
        <Message data-testid="work-item-timeline-empty-selection">{labels.emptySelection}</Message>
      ) : state === "local_only" ? (
        <Message data-testid="work-item-timeline-local-only">{labels.emptyLocal}</Message>
      ) : (
        <div className="otc-stack" data-testid="work-item-timeline-panel">
          {summary ? (
            <div className="otc-message otc-panel-summary" data-testid="work-item-timeline-summary">
              {summary}
            </div>
          ) : null}
          {timelineError ? (
            <Message tone="error" data-testid="work-item-timeline-error">
              {timelineError}
            </Message>
          ) : null}
          {timelineData ? (
            <>
              <div className="otc-grid otc-grid--counterparty-form">
                <label className="otc-field">
                  {labels.commentType}
                  <select
                    className="otc-select"
                    data-testid="work-item-timeline-comment-type"
                    value={commentType}
                    onChange={(event) => onCommentTypeChange(event.target.value as WorkCommentResponse["comment_type"])}
                  >
                    <option value="note">{labels.commentTypes.note}</option>
                    <option value="decision">{labels.commentTypes.decision}</option>
                    <option value="handoff">{labels.commentTypes.handoff}</option>
                  </select>
                </label>
                <label className="otc-field">
                  {labels.comment}
                  <textarea
                    className="otc-textarea"
                    data-testid="work-item-timeline-comment-body"
                    rows={3}
                    value={commentBody}
                    placeholder={labels.commentPlaceholder}
                    onChange={(event) => onCommentBodyChange(event.target.value)}
                  />
                </label>
              </div>
              <div className="otc-controls">
                <button
                  type="button"
                  className="otc-button otc-button--accent"
                  data-testid="work-item-timeline-comment-save"
                  onClick={onCommentSubmit}
                  disabled={commentSubmitting}
                >
                  {commentSubmitting ? labels.commentSaving : labels.commentSave}
                </button>
              </div>
              <div className="otc-grid otc-grid--counterparty-form">
                <div className="otc-stack">
                  <strong>{labels.events}</strong>
                  {timelineData.events.length ? (
                    timelineData.events.map((event) => (
                      <div key={event.id} className="otc-message" data-testid="work-item-timeline-event">
                        <strong>{formatEventLabel(event)}</strong>
                        <div className="otc-muted">{formatDate(event.created_at) ?? event.created_at}</div>
                        {Object.keys(event.payload ?? {}).length ? <div className="otc-muted">{JSON.stringify(event.payload)}</div> : null}
                      </div>
                    ))
                  ) : (
                    <Message>{labels.eventsEmpty}</Message>
                  )}
                </div>
                <div className="otc-stack">
                  <strong>{labels.comments}</strong>
                  {timelineData.comments.length ? (
                    timelineData.comments.map((comment) => (
                      <div key={comment.id} className="otc-message" data-testid="work-item-timeline-comment">
                        <strong>{labels.commentTypes[comment.comment_type]}</strong>
                        <div>{comment.body}</div>
                        <div className="otc-muted">{formatDate(comment.created_at) ?? comment.created_at}</div>
                      </div>
                    ))
                  ) : (
                    <Message>{labels.commentsEmpty}</Message>
                  )}
                </div>
              </div>
            </>
          ) : (
            <Message data-testid="work-item-timeline-empty">{timelineLoading ? labels.loading : labels.empty}</Message>
          )}
        </div>
      )}
    </Panel>
  );
}

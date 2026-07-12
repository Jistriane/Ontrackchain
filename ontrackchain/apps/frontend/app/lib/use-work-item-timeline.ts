"use client";

import { useCallback, useState } from "react";

import { createWorkItemComment, fetchWorkItemTimeline } from "./work-item-timeline-client";
import type { WorkCommentResponse, WorkItemTimelineResponse } from "./work-item-timeline";

type ResolveTimelineError = (error: unknown, fallback: string) => string;

type UseWorkItemTimelineOptions = {
  resolveErrorMessage: ResolveTimelineError;
  loadErrorMessage: string;
  commentErrorMessage: string;
  emptySelectionErrorMessage?: string;
  emptyCommentErrorMessage?: string;
  onCommentSaved?: () => void;
};

export function useWorkItemTimeline<TItem>({
  resolveErrorMessage,
  loadErrorMessage,
  commentErrorMessage,
  emptySelectionErrorMessage,
  emptyCommentErrorMessage,
  onCommentSaved
}: UseWorkItemTimelineOptions) {
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineError, setTimelineError] = useState<string | null>(null);
  const [timelineData, setTimelineData] = useState<WorkItemTimelineResponse<TItem> | null>(null);
  const [commentType, setCommentType] = useState<WorkCommentResponse["comment_type"]>("note");
  const [commentBody, setCommentBody] = useState("");
  const [commentSubmitting, setCommentSubmitting] = useState(false);

  const resetTimeline = useCallback(() => {
    setTimelineData(null);
    setTimelineError(null);
  }, []);

  const loadTimeline = useCallback(
    async (workItemId: string) => {
      setTimelineLoading(true);
      setTimelineError(null);
      const result = await fetchWorkItemTimeline<TItem>(workItemId);
      if (!result.ok) {
        setTimelineData(null);
        setTimelineError(resolveErrorMessage(result.error, loadErrorMessage));
        setTimelineLoading(false);
        return false;
      }
      setTimelineData(result.data);
      setTimelineLoading(false);
      return true;
    },
    [loadErrorMessage, resolveErrorMessage]
  );

  const submitTimelineComment = useCallback(
    async (workItemId: string | null | undefined) => {
      if (!workItemId) {
        if (emptySelectionErrorMessage) {
          setTimelineError(emptySelectionErrorMessage);
        }
        return false;
      }
      if (!commentBody.trim()) {
        if (emptyCommentErrorMessage) {
          setTimelineError(emptyCommentErrorMessage);
        }
        return false;
      }
      setCommentSubmitting(true);
      setTimelineError(null);
      const result = await createWorkItemComment(workItemId, {
        comment_type: commentType,
        body: commentBody.trim()
      });
      setCommentSubmitting(false);
      if (!result.ok) {
        setTimelineError(resolveErrorMessage(result.error, commentErrorMessage));
        return false;
      }
      setCommentBody("");
      setCommentType("note");
      await loadTimeline(workItemId);
      onCommentSaved?.();
      return true;
    },
    [
      commentBody,
      commentErrorMessage,
      commentType,
      emptyCommentErrorMessage,
      emptySelectionErrorMessage,
      loadTimeline,
      onCommentSaved,
      resolveErrorMessage
    ]
  );

  return {
    timelineLoading,
    timelineError,
    timelineData,
    commentType,
    commentBody,
    commentSubmitting,
    setTimelineError,
    setCommentType,
    setCommentBody,
    resetTimeline,
    loadTimeline,
    submitTimelineComment
  };
}

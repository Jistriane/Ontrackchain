import type { WorkCommentResponse, WorkItemTimelineResponse } from "./work-item-timeline";

type TimelineApiError = {
  error?: string;
  detail?: unknown;
} | null;

type TimelineSuccess<T> = {
  ok: true;
  data: T;
};

type TimelineFailure = {
  ok: false;
  error: TimelineApiError;
};

type TimelineResult<T> = TimelineSuccess<T> | TimelineFailure;

export async function fetchWorkItemTimeline<TItem>(workItemId: string): Promise<TimelineResult<WorkItemTimelineResponse<TItem>>> {
  const res = await fetch(`/api/app/operations/work-items/${encodeURIComponent(workItemId)}/timeline`, {
    cache: "no-store"
  });
  const data = (await res.json().catch(() => null)) as WorkItemTimelineResponse<TItem> | TimelineApiError;
  if (!res.ok || !data || !("events" in data) || !("comments" in data)) {
    return { ok: false, error: (data as TimelineApiError) ?? null };
  }
  return { ok: true, data };
}

export async function createWorkItemComment(
  workItemId: string,
  payload: Pick<WorkCommentResponse, "comment_type" | "body">
): Promise<TimelineResult<WorkCommentResponse>> {
  const res = await fetch(`/api/app/operations/work-items/${encodeURIComponent(workItemId)}/comments`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store"
  });
  const data = (await res.json().catch(() => null)) as WorkCommentResponse | TimelineApiError;
  if (!res.ok || !data || !("id" in data)) {
    return { ok: false, error: (data as TimelineApiError) ?? null };
  }
  return { ok: true, data };
}

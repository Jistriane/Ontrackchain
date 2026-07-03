export type WorkEventResponse = {
  id: string;
  event_type: string;
  from_status: string | null;
  to_status: string | null;
  actor_user_id: string | null;
  payload: Record<string, unknown>;
  created_at: string;
};

export type WorkCommentResponse = {
  id: string;
  comment_type: "note" | "decision" | "handoff";
  actor_user_id: string | null;
  body: string;
  created_at: string;
};

export type WorkItemTimelineResponse<TItem> = {
  item: TItem;
  events: WorkEventResponse[];
  comments: WorkCommentResponse[];
};

export function formatTimelineEvent(event: WorkEventResponse) {
  if (event.event_type === "COMMENT_ADDED") {
    return "COMMENT_ADDED";
  }
  if (event.from_status && event.to_status && event.from_status !== event.to_status) {
    return `${event.event_type}: ${event.from_status} -> ${event.to_status}`;
  }
  return event.event_type;
}

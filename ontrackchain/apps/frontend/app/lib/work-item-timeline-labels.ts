import type { MessageKey } from "./i18n";
import type { WorkCommentResponse } from "./work-item-timeline";

export type TimelineLabels = {
  title: string;
  description: string;
  refresh: string;
  refreshing: string;
  emptySelection: string;
  emptyLocal: string;
  loading: string;
  empty: string;
  events: string;
  eventsEmpty: string;
  comments: string;
  commentsEmpty: string;
  commentType: string;
  comment: string;
  commentPlaceholder: string;
  commentSave: string;
  commentSaving: string;
  commentTypes: Record<WorkCommentResponse["comment_type"], string>;
};

type Translator = (key: MessageKey, values?: Record<string, string | number>) => string;

export function buildWorkItemTimelineLabels(tr: Translator, prefix: string): TimelineLabels {
  return {
    title: tr(`${prefix}.title` as MessageKey),
    description: tr(`${prefix}.description` as MessageKey),
    refresh: tr(`${prefix}.refresh` as MessageKey),
    refreshing: tr(`${prefix}.refreshing` as MessageKey),
    emptySelection: tr(`${prefix}.emptySelection` as MessageKey),
    emptyLocal: tr(`${prefix}.emptyLocal` as MessageKey),
    loading: tr(`${prefix}.loading` as MessageKey),
    empty: tr(`${prefix}.empty` as MessageKey),
    events: tr(`${prefix}.events` as MessageKey),
    eventsEmpty: tr(`${prefix}.eventsEmpty` as MessageKey),
    comments: tr(`${prefix}.comments` as MessageKey),
    commentsEmpty: tr(`${prefix}.commentsEmpty` as MessageKey),
    commentType: tr(`${prefix}.commentType` as MessageKey),
    comment: tr(`${prefix}.comment` as MessageKey),
    commentPlaceholder: tr(`${prefix}.commentPlaceholder` as MessageKey),
    commentSave: tr(`${prefix}.commentSave` as MessageKey),
    commentSaving: tr(`${prefix}.commentSaving` as MessageKey),
    commentTypes: {
      note: tr(`${prefix}.commentTypes.note` as MessageKey),
      decision: tr(`${prefix}.commentTypes.decision` as MessageKey),
      handoff: tr(`${prefix}.commentTypes.handoff` as MessageKey)
    }
  };
}

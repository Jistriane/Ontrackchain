"use client";

import {
  readWorkItemMetadataString,
  readWorkItemMetadataStringArray,
  type AlertsWorkItemMetadata,
  type WorkItemResponse
} from "./work-items";

export type AlertRcaContainmentStatus = "not_started" | "in_progress" | "contained" | "validated";

export type AlertRcaSummary = {
  domain: string;
  incidentCommander: string;
  suspectedRootCause: string;
  confirmedRootCause: string;
  containmentStatus: AlertRcaContainmentStatus;
  affectedDomains: string[];
  impactSummary: string;
};

const ALERT_RCA_CONTAINMENT_STATUSES: AlertRcaContainmentStatus[] = ["not_started", "in_progress", "contained", "validated"];

export function normalizeAlertContainmentStatus(value: string | null | undefined): AlertRcaContainmentStatus {
  if (value && ALERT_RCA_CONTAINMENT_STATUSES.includes(value as AlertRcaContainmentStatus)) {
    return value as AlertRcaContainmentStatus;
  }
  return "not_started";
}

export function buildAlertRcaSummary(item: WorkItemResponse<AlertsWorkItemMetadata> | null): AlertRcaSummary | null {
  if (!item) {
    return null;
  }

  const metadata = (item.metadata ?? {}) as Record<string, unknown>;
  const domain = readWorkItemMetadataString(metadata, "domain");
  const incidentCommander = readWorkItemMetadataString(metadata, "incident_commander");
  const suspectedRootCause = readWorkItemMetadataString(metadata, "suspected_root_cause");
  const confirmedRootCause = readWorkItemMetadataString(metadata, "confirmed_root_cause");
  const containmentStatus = normalizeAlertContainmentStatus(readWorkItemMetadataString(metadata, "containment_status"));
  const affectedDomains = readWorkItemMetadataStringArray(metadata, "affected_domains");
  const impactSummary = readWorkItemMetadataString(metadata, "impact_summary");

  if (!domain && !incidentCommander && !suspectedRootCause && !confirmedRootCause && !impactSummary && !affectedDomains.length) {
    return null;
  }

  return {
    domain,
    incidentCommander,
    suspectedRootCause,
    confirmedRootCause,
    containmentStatus,
    affectedDomains,
    impactSummary
  };
}

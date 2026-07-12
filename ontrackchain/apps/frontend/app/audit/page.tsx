"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useI18n } from "../../components/i18n-provider";
import { resolveApiErrorMessage } from "../lib/api-error-catalog";
import { formatDateTime as formatDate } from "../lib/date-format";
import {
  AUDIT_ACTION_VALUES,
  AUDIT_RESOURCE_TYPE_VALUES,
  isAuditActionValue,
  isAuditResourceTypeValue
} from "../lib/audit-catalog";
import { AppShell, CodeBlock, Message, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import {
  buildAuditLogQuery,
  extractAuditApiError,
  type AuditLogEntry,
  type AuditLogQueryFilters,
  type AuditLogsResponse
} from "../lib/audit-log";
import {
  buildOperationalContextLinks,
  type OperationalContextLink,
  inferLogOperationalContext
} from "../lib/operational-context";
import { resolveHashContext } from "../lib/hash-context";
import type { MessageKey } from "../lib/i18n";
type AuditFilters = AuditLogQueryFilters;

type AuditDossierContext = {
  reportId: string;
  rosId: string;
  filename: string;
  dossierSha256: string;
};

type AuditManualPackageContext = {
  eventAction: string;
  eventActionLabel: string;
  requestId: string;
  reportId: string;
  scopeId: string;
  filename: string;
  packageSha256: string;
  manualReviewAction: string;
  manualReviewActionLabel: string;
  workspaceStatus: string;
  sealStatus: string;
  sealId: string;
  signerRole: string;
  signerRoleLabel: string;
  decision: string;
  decisionLabel: string;
  signatureAlgorithm: string;
  trustBundleRef: string;
  verificationMethod: string;
  authRole: string;
  mfaMode: string;
  twoFactorStatus: string;
  mfaProviderHomologated: string;
  mfaViolationDetail: string;
  ticketRef: string;
  governanceReason: string;
  supersededBySealId: string;
  revokedAt: string;
  supersededAt: string;
  evidenceHref: string;
};

type AuditHashContext = {
  primaryHash: string;
  sourceLabel: string;
  artifactTypeLabel: string;
};

type DossierAuditMetrics = {
  totalDownloads: number;
  uniqueRosCount: number;
  latestHash: string;
  latestFilename: string;
  latestReportId: string;
};

type ManualPackageAuditMetrics = {
  totalEvents: number;
  totalExports: number;
  totalSignoffs: number;
  totalSeals: number;
  uniqueScopeCount: number;
  latestHash: string;
  latestFilename: string;
  latestReportId: string;
  latestScopeId: string;
  latestActionLabel: string;
  latestStageLabel: string;
  latestEvidenceHref: string;
};

type ManualPackageGovernanceMetrics = {
  totalEvents: number;
  totalExports: number;
  totalSignoffs: number;
  totalSeals: number;
  totalRevocations: number;
  totalSupersedes: number;
  latestExportToSealDuration: string;
  latestSealToGovernanceDuration: string;
  evidenceHref: string;
};

type ManualPackageMfaMetrics = {
  totalEvents: number;
  uniqueRequestCount: number;
  uniqueSealCount: number;
  total2faRequired: number;
  totalProviderNotHomologated: number;
  latestRequestId: string;
  latestSealId: string;
  latestAuthRole: string;
  latestSignerRoleLabel: string;
  latestMfaMode: string;
};

type ManualPackageMfaFamily = {
  key: string;
  requestId: string;
  sealId: string;
  totalEvents: number;
  total2faRequired: number;
  totalProviderNotHomologated: number;
  latestCreatedAt: string;
  latestAuthRole: string;
  latestSignerRoleLabel: string;
  latestMfaMode: string;
  latestDetail: string;
  dominantTypeLabel: string;
  dominantTypeTone: "success" | "warning" | "danger";
  href: string;
  isActive: boolean;
};

type ManualPackageMfaRoleBreakdownItem = {
  key: string;
  label: string;
  count: number;
};

type ManualPackageMfaRoleSummary = {
  authRoles: ManualPackageMfaRoleBreakdownItem[];
  signerRoles: ManualPackageMfaRoleBreakdownItem[];
};

type ManualPackageMfaTypeSummaryItem = {
  key: string;
  label: string;
  count: number;
  shareLabel: string;
};

const MANUAL_PACKAGE_AUDIT_ACTIONS = new Set([
  "evidence_manual_review_package_exported",
  "evidence_manual_review_package_signoff_requested",
  "evidence_manual_review_package_signoff_recorded",
  "evidence_manual_review_package_sealed",
  "evidence_manual_review_package_seal_revoked",
  "evidence_manual_review_package_seal_superseded"
]);
const MANUAL_PACKAGE_MFA_VIOLATION_ACTION = "evidence_manual_review_package_mfa_violation";
const MANUAL_PACKAGE_CONTEXT_ACTIONS = new Set([...MANUAL_PACKAGE_AUDIT_ACTIONS, MANUAL_PACKAGE_MFA_VIOLATION_ACTION]);

const DEFAULT_FILTERS: AuditFilters = {
  requestId: "",
  action: "",
  resourceType: "",
  reportId: "",
  resourceId: "",
  limit: "50"
};

export default function AuditPage() {
  const { locale, t } = useI18n();
  const searchParams = useSearchParams();
  const activePreset = searchParams.get("preset") ?? "";
  const activeGovernanceSealId = searchParams.get("seal_id")?.trim() ?? "";
  const [filters, setFilters] = useState<AuditFilters>(DEFAULT_FILTERS);
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [count, setCount] = useState(0);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportingRosCoafDossier, setExportingRosCoafDossier] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);
  const [manualPresetLogs, setManualPresetLogs] = useState<AuditLogEntry[]>([]);
  const [manualPresetLoading, setManualPresetLoading] = useState(false);
  const [linkedRosIdFromReport, setLinkedRosIdFromReport] = useState<string | null>(null);
  const [linkedRosLoading, setLinkedRosLoading] = useState(false);
  const latestRequestRef = useRef(0);
  const manualPresetRequestRef = useRef(0);

  function resolveDownloadFilename(contentDisposition: string | null, fallbackName: string) {
    if (!contentDisposition) {
      return fallbackName;
    }

    const match = contentDisposition.match(/filename\*?=(?:UTF-8''|")?([^\";]+)"?/i);
    if (!match) {
      return fallbackName;
    }

    try {
      return decodeURIComponent(match[1]);
    } catch {
      return match[1];
    }
  }

  function summarizeDossierHash(hash: string | null) {
    const normalized = hash?.trim() ?? "";
    if (!normalized) {
      return "n/a";
    }
    return normalized.length > 16 ? `${normalized.slice(0, 16)}...` : normalized;
  }

  function readMetadataString(metadata: Record<string, unknown> | null | undefined, key: string) {
    const value = metadata?.[key];
    return typeof value === "string" && value.trim() ? value.trim() : "";
  }

  function parseAuditTimestamp(value: string | null | undefined) {
    const normalized = value?.trim() ?? "";
    if (!normalized) {
      return null;
    }
    const parsed = Date.parse(normalized);
    return Number.isNaN(parsed) ? null : parsed;
  }

  function formatAuditDurationValue(durationMs: number | null | undefined) {
    if (durationMs == null || durationMs < 0) {
      return t("audit.notAvailable");
    }

    const totalMinutes = Math.round(durationMs / 60_000);
    if (totalMinutes < 1) {
      return "< 1 min";
    }
    if (totalMinutes < 60) {
      return `${totalMinutes} min`;
    }

    const totalHours = Math.floor(totalMinutes / 60);
    const remainingMinutes = totalMinutes % 60;
    if (totalHours < 24) {
      return remainingMinutes ? `${totalHours} h ${remainingMinutes} min` : `${totalHours} h`;
    }

    const totalDays = Math.floor(totalHours / 24);
    const remainingHours = totalHours % 24;
    return remainingHours ? `${totalDays} d ${remainingHours} h` : `${totalDays} d`;
  }

  function renderHashContext(context: AuditHashContext) {
    return (
      <div className="otc-stack" data-testid="audit-hash-context">
        <div>
          <strong>{t("audit.details.activeHash" as MessageKey)}:</strong>{" "}
          <span className="otc-mono">{context.primaryHash}</span>
        </div>
        <div>
          <strong>{t("audit.details.hashSource" as MessageKey)}:</strong> {context.sourceLabel}
        </div>
        <div>
          <strong>{t("audit.details.artifactType" as MessageKey)}:</strong> {context.artifactTypeLabel}
        </div>
      </div>
    );
  }

  function renderDossierDetailContext(context: AuditDossierContext) {
    return (
      <div className="otc-stack otc-controls--spaced" data-testid="audit-dossier-detail-context">
        <strong>{t("audit.details.dossierContextTitle" as MessageKey)}</strong>
        <div>
          <strong>{t("audit.details.dossierFilename" as MessageKey)}:</strong>{" "}
          <span className="otc-mono">{context.filename || t("audit.notAvailable")}</span>
        </div>
        <div>
          <strong>{t("audit.details.dossierHash" as MessageKey)}:</strong>{" "}
          <span className="otc-mono">{context.dossierSha256 || t("audit.notAvailable")}</span>
        </div>
        <div className="otc-controls">
          {context.reportId ? (
            <a
              className="otc-button otc-button--ghost"
              href={`/reports?history_report_id=${encodeURIComponent(context.reportId)}`}
              data-testid="audit-dossier-detail-open-report"
            >
              {t("audit.details.openDossierReport" as MessageKey)}
            </a>
          ) : null}
          {context.rosId ? (
            <a
              className="otc-button otc-button--ghost"
              href={`/ros-coaf?ros_id=${encodeURIComponent(context.rosId)}${
                context.reportId ? `&report_id=${encodeURIComponent(context.reportId)}` : ""
              }`}
              data-testid="audit-dossier-detail-open-roscoaf"
            >
              {t("audit.details.openDossierRosCoaf" as MessageKey)}
            </a>
          ) : null}
        </div>
      </div>
    );
  }

  function renderManualPackageDetailContext(context: AuditManualPackageContext) {
    return (
      <div className="otc-stack otc-controls--spaced" data-testid="audit-manual-package-detail-context">
        <strong>{t("audit.details.manualPackageContextTitle" as MessageKey)}</strong>
        <div>
          <strong>{t("audit.details.manualPackageStage" as MessageKey)}:</strong> {context.eventActionLabel}
        </div>
        <div>
          <strong>{t("audit.details.manualPackageFilename" as MessageKey)}:</strong>{" "}
          <span className="otc-mono">{context.filename || t("audit.notAvailable")}</span>
        </div>
        <div>
          <strong>{t("audit.details.manualPackageHash" as MessageKey)}:</strong>{" "}
          <span className="otc-mono">{context.packageSha256 || t("audit.notAvailable")}</span>
        </div>
        <div>
          <strong>{t("audit.details.manualPackageAction" as MessageKey)}:</strong> {context.manualReviewActionLabel}
        </div>
        <div>
          <strong>{t("audit.details.manualPackageScopeId" as MessageKey)}:</strong>{" "}
          <span className="otc-mono">{context.scopeId || t("audit.notAvailable")}</span>
        </div>
        <div>
          <strong>{t("audit.details.manualPackageWorkspaceStatus" as MessageKey)}:</strong>{" "}
          {context.workspaceStatus || t("audit.notAvailable")}
        </div>
        <div>
          <strong>{t("audit.details.manualPackageSealStatus" as MessageKey)}:</strong>{" "}
          {context.sealStatus || t("audit.notAvailable")}
        </div>
        <div>
          <strong>{t("audit.details.manualPackageSealId" as MessageKey)}:</strong>{" "}
          <span className="otc-mono">{context.sealId || t("audit.notAvailable")}</span>
        </div>
        <div>
          <strong>{t("audit.details.manualPackageSigner" as MessageKey)}:</strong> {context.signerRoleLabel}
        </div>
        <div>
          <strong>{t("audit.details.manualPackageDecision" as MessageKey)}:</strong> {context.decisionLabel}
        </div>
        <div>
          <strong>{t("audit.details.manualPackageSignatureAlgorithm" as MessageKey)}:</strong>{" "}
          {context.signatureAlgorithm || t("audit.notAvailable")}
        </div>
        <div>
          <strong>{t("audit.details.manualPackageTrustBundle" as MessageKey)}:</strong>{" "}
          <span className="otc-mono">{context.trustBundleRef || t("audit.notAvailable")}</span>
        </div>
        <div>
          <strong>{t("audit.details.manualPackageVerificationMethod" as MessageKey)}:</strong>{" "}
          {context.verificationMethod || t("audit.notAvailable")}
        </div>
        {context.authRole ? (
          <div>
            <strong>{t("audit.details.manualPackageAuthRole" as MessageKey)}:</strong> {context.authRole}
          </div>
        ) : null}
        {context.mfaMode ? (
          <div>
            <strong>{t("audit.details.manualPackageMfaMode" as MessageKey)}:</strong> {context.mfaMode}
          </div>
        ) : null}
        {context.twoFactorStatus ? (
          <div>
            <strong>{t("audit.details.manualPackageTwoFactorStatus" as MessageKey)}:</strong> {context.twoFactorStatus}
          </div>
        ) : null}
        {context.mfaProviderHomologated ? (
          <div>
            <strong>{t("audit.details.manualPackageMfaProviderHomologated" as MessageKey)}:</strong> {context.mfaProviderHomologated}
          </div>
        ) : null}
        {context.mfaViolationDetail ? (
          <div>
            <strong>{t("audit.details.manualPackageMfaViolationDetail" as MessageKey)}:</strong> {context.mfaViolationDetail}
          </div>
        ) : null}
        {context.ticketRef ? (
          <div>
            <strong>{t("audit.details.manualPackageTicketRef" as MessageKey)}:</strong>{" "}
            <span className="otc-mono">{context.ticketRef}</span>
          </div>
        ) : null}
        {context.governanceReason ? (
          <div>
            <strong>{t("audit.details.manualPackageGovernanceReason" as MessageKey)}:</strong>{" "}
            {context.governanceReason}
          </div>
        ) : null}
        {context.supersededBySealId ? (
          <div>
            <strong>{t("audit.details.manualPackageSupersededBySealId" as MessageKey)}:</strong>{" "}
            <span className="otc-mono">{context.supersededBySealId}</span>
          </div>
        ) : null}
        {context.revokedAt ? (
          <div>
            <strong>{t("audit.details.manualPackageRevokedAt" as MessageKey)}:</strong>{" "}
            {formatAuditTimestampValue(context.revokedAt)}
          </div>
        ) : null}
        {context.supersededAt ? (
          <div>
            <strong>{t("audit.details.manualPackageSupersededAt" as MessageKey)}:</strong>{" "}
            {formatAuditTimestampValue(context.supersededAt)}
          </div>
        ) : null}
        {context.evidenceHref ? (
          <div className="otc-controls">
            <a
              className="otc-button otc-button--ghost"
              href={context.evidenceHref}
              data-testid="audit-manual-package-detail-open-evidence-source"
            >
              {t("audit.details.openEvidenceManualSource" as MessageKey)}
            </a>
          </div>
        ) : null}
      </div>
    );
  }

  function renderDossierPresetLatestContext(loadingValue: boolean, metrics: DossierAuditMetrics) {
    return (
      <div className="otc-stack otc-controls--spaced" data-testid="audit-dossier-preset-latest-context">
        <span className="otc-muted">{t("audit.presets.latestContext")}</span>
        <div className="otc-controls">
          <span>
            {t("audit.presets.latestContextReportId")}{" "}
            <strong className="otc-mono">
              {loadingValue ? "..." : metrics.latestReportId || t("audit.notAvailable")}
            </strong>
          </span>
          <span>
            {t("audit.presets.latestContextFilename")}{" "}
            <strong className="otc-mono">
              {loadingValue ? "..." : metrics.latestFilename || t("audit.notAvailable")}
            </strong>
          </span>
        </div>
      </div>
    );
  }

  function renderManualPackagePresetLatestContext(loadingValue: boolean, metrics: ManualPackageAuditMetrics) {
    return (
      <div className="otc-stack otc-controls--spaced" data-testid="audit-manual-preset-latest-context">
        <span className="otc-muted">{t("audit.presets.latestContext")}</span>
        <div className="otc-controls">
          <span>
            {t("audit.presets.latestContextScopeId" as MessageKey)}{" "}
            <strong className="otc-mono">
              {loadingValue ? "..." : metrics.latestScopeId || t("audit.notAvailable")}
            </strong>
          </span>
          <span>
            {t("audit.presets.latestContextAction" as MessageKey)}{" "}
            <strong>{loadingValue ? "..." : metrics.latestActionLabel || t("audit.notAvailable")}</strong>
          </span>
          <span>
            {t("audit.presets.latestContextStage" as MessageKey)}{" "}
            <strong>{loadingValue ? "..." : metrics.latestStageLabel || t("audit.notAvailable")}</strong>
          </span>
        </div>
        <div className="otc-controls">
          <span>
            {t("audit.presets.latestContextReportId")}{" "}
            <strong className="otc-mono">
              {loadingValue ? "..." : metrics.latestReportId || t("audit.notAvailable")}
            </strong>
          </span>
          <span>
            {t("audit.presets.latestContextFilename")}{" "}
            <strong className="otc-mono">
              {loadingValue ? "..." : metrics.latestFilename || t("audit.notAvailable")}
            </strong>
          </span>
        </div>
      </div>
    );
  }

  function renderManualPackageMfaPresetLatestContext(loadingValue: boolean, metrics: ManualPackageMfaMetrics) {
    return (
      <div className="otc-stack otc-controls--spaced" data-testid="audit-manual-mfa-preset-latest-context">
        <span className="otc-muted">{t("audit.presets.latestContext")}</span>
        <div className="otc-controls">
          <span>
            {t("audit.presets.latestContextRequestId" as MessageKey)}{" "}
            <strong className="otc-mono">{loadingValue ? "..." : metrics.latestRequestId || t("audit.notAvailable")}</strong>
          </span>
          <span>
            {t("audit.presets.latestContextSealId" as MessageKey)}{" "}
            <strong className="otc-mono">{loadingValue ? "..." : metrics.latestSealId || t("audit.notAvailable")}</strong>
          </span>
        </div>
        <div className="otc-controls">
          <span>
            {t("audit.presets.latestContextAuthRole" as MessageKey)}{" "}
            <strong>{loadingValue ? "..." : metrics.latestAuthRole || t("audit.notAvailable")}</strong>
          </span>
          <span>
            {t("audit.presets.latestContextSignerRole" as MessageKey)}{" "}
            <strong>{loadingValue ? "..." : metrics.latestSignerRoleLabel || t("audit.notAvailable")}</strong>
          </span>
          <span>
            {t("audit.presets.latestContextMfaMode" as MessageKey)}{" "}
            <strong>{loadingValue ? "..." : metrics.latestMfaMode || t("audit.notAvailable")}</strong>
          </span>
        </div>
      </div>
    );
  }

  function resolveAuditActionLabel(value: string) {
    if (!value.trim()) {
      return t("audit.notAvailable");
    }
    return isAuditActionValue(value) ? t(`audit.values.actions.${value}` as MessageKey) : value;
  }

  function resolveAuditResourceTypeLabel(value: string) {
    if (!value.trim()) {
      return t("audit.notAvailable");
    }
    return isAuditResourceTypeValue(value) ? t(`audit.values.resourceTypes.${value}` as MessageKey) : value;
  }

  function formatAuditValue(value: string, label: string) {
    if (!value.trim()) {
      return t("audit.notAvailable");
    }
    return label === value ? value : `${label} (${value})`;
  }

  function formatAuditActionValue(value: string) {
    return formatAuditValue(value, resolveAuditActionLabel(value));
  }

  function formatAuditResourceTypeValue(value: string) {
    return formatAuditValue(value, resolveAuditResourceTypeLabel(value));
  }

  function resolveManualReviewActionLabel(value: string) {
    const normalized = value.trim();
    if (!normalized) {
      return t("audit.notAvailable");
    }
    if (normalized === "compliance_due_diligence_checked" || normalized === "compliance_source_of_funds_checked") {
      return t(`evidenceTrail.values.actions.${normalized}` as MessageKey);
    }
    return resolveAuditActionLabel(normalized);
  }

  function resolveManualPackageSealStatusLabel(value: string) {
    const normalized = value.trim();
    if (!normalized) {
      return t("audit.notAvailable");
    }
    return t(`evidenceTrail.manualPackage.seal.values.${normalized}` as MessageKey);
  }

  function resolveManualPackageSignerRoleLabel(value: string) {
    const normalized = value.trim();
    if (!normalized) {
      return t("audit.notAvailable");
    }
    return t(`evidenceTrail.manualPackage.seal.roles.${normalized}` as MessageKey);
  }

  function resolveManualPackageDecisionLabel(value: string) {
    const normalized = value.trim();
    if (!normalized) {
      return t("audit.notAvailable");
    }
    return t(`evidenceTrail.manualPackage.seal.decisions.${normalized}` as MessageKey);
  }

  function resolveManualReviewDomain(value: string) {
    if (value === "compliance_due_diligence_checked") {
      return "due_diligence";
    }
    if (value === "compliance_source_of_funds_checked") {
      return "source_of_funds";
    }
    return "";
  }

  function buildManualEvidenceHref(input: {
    requestId: string;
    reportId?: string | null;
    manualReviewAction: string;
  }) {
    const requestId = input.requestId.trim();
    const manualReviewAction = input.manualReviewAction.trim();
    if (!requestId || !manualReviewAction) {
      return "";
    }

    const domain = resolveManualReviewDomain(manualReviewAction);
    const query = new URLSearchParams({
      request_id: requestId,
      action: manualReviewAction,
      resource_type: "address",
      audit_origin: "manual_package"
    });
    if (domain) {
      query.set("domain", domain);
    }
    const reportId = input.reportId?.trim() ?? "";
    if (reportId) {
      query.set("report_id", reportId);
    }
    return `/evidence?${query.toString()}`;
  }

  function buildManualPackageMfaAuditHref(input?: { requestId?: string | null; sealId?: string | null }) {
    const query = new URLSearchParams({
      preset: "manual-package-mfa",
      action: MANUAL_PACKAGE_MFA_VIOLATION_ACTION,
      resource_type: "evidence_package_seal"
    });
    const requestId = input?.requestId?.trim() ?? "";
    const sealId = input?.sealId?.trim() ?? "";
    if (requestId) {
      query.set("request_id", requestId);
    }
    if (sealId) {
      query.set("resource_id", sealId);
    }
    return `/audit?${query.toString()}`;
  }

  function formatAuditTimestampValue(value: string | null | undefined) {
    const normalized = value?.trim() ?? "";
    return normalized ? formatDate(normalized, locale) ?? normalized : t("audit.noTimestamp");
  }

  function filtersFromSearchParams(): AuditFilters {
    return {
      requestId: searchParams.get("request_id") ?? "",
      action: searchParams.get("action") ?? "",
      resourceType: searchParams.get("resource_type") ?? "",
      reportId: searchParams.get("report_id") ?? "",
      resourceId: searchParams.get("resource_id") ?? "",
      limit: searchParams.get("limit") ?? DEFAULT_FILTERS.limit
    };
  }

  async function resolveGovernancePresetFilters(nextFilters: AuditFilters) {
    if (activePreset !== "governanca" || nextFilters.requestId.trim() || !activeGovernanceSealId) {
      return nextFilters;
    }

    const params = new URLSearchParams();
    params.set("resource_type", "evidence_package_seal");
    params.set("resource_id", activeGovernanceSealId);
    params.set("limit", "200");
    params.set("page", "1");

    const res = await fetch(`/api/app/audit/logs?${params.toString()}`, { cache: "no-store" });
    const data = (await res.json().catch(() => null)) as AuditLogsResponse | { error?: string } | null;
    if (!res.ok) {
      throw new Error("governance_resolve_failed");
    }

    const payload = data && "data" in data ? data : null;
    const matchingRows = (payload?.data ?? [])
      .filter((entry) => MANUAL_PACKAGE_AUDIT_ACTIONS.has(entry.action))
      .slice()
      .sort((a, b) => String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")));
    const matchedRow = matchingRows[0] ?? null;
    const requestId = matchedRow?.request_id?.trim() ?? readMetadataString(matchedRow?.metadata, "request_id");
    const reportId = matchedRow?.report_id?.trim() ?? readMetadataString(matchedRow?.metadata, "report_id");

    if (!requestId) {
      throw new Error("governance_request_not_found");
    }

    return {
      ...nextFilters,
      requestId,
      reportId: nextFilters.reportId.trim() || reportId,
      action: "",
      resourceType: "",
      resourceId: "",
      limit: "200"
    };
  }

  function resolveManualPackageMfaPresetFilters(nextFilters: AuditFilters): AuditFilters {
    if (activePreset !== "manual-package-mfa") {
      return nextFilters;
    }

    return {
      ...nextFilters,
      action: nextFilters.action.trim() || MANUAL_PACKAGE_MFA_VIOLATION_ACTION,
      resourceType: nextFilters.resourceType.trim() || "evidence_package_seal",
      limit: "200"
    };
  }

  async function fetchLogs(nextFilters: AuditFilters, page = 1) {
    const requestNumber = latestRequestRef.current + 1;
    latestRequestRef.current = requestNumber;
    setLoading(true);
    setError(null);
    setNotice(null);
    const query = buildAuditLogQuery(nextFilters, page);
    const res = await fetch(`/api/app/audit/logs?${query}`, { cache: "no-store" });
    const data = (await res.json().catch(() => null)) as AuditLogsResponse | { error?: string } | null;
    if (requestNumber !== latestRequestRef.current) {
      return;
    }
    if (!res.ok) {
      const apiError = extractAuditApiError(data);
      setLogs([]);
      setCount(0);
      setTotal(0);
      setCurrentPage(1);
      setTotalPages(1);
      setHasMore(false);
      setSelectedLog(null);
      setError(
        apiError
          ? t("audit.errorLoadWithMessage", { message: resolveApiErrorMessage(t, apiError, apiError) })
          : t("audit.errorLoad")
      );
      setLoading(false);
      return;
    }

    const payload = data && "data" in data ? data : null;
    const rows = payload?.data ?? [];
    const filteredRows =
      activePreset === "governanca" && nextFilters.requestId.trim()
        ? rows.filter((entry) => MANUAL_PACKAGE_AUDIT_ACTIONS.has(entry.action))
        : rows;
    const effectiveCount = filteredRows.length;
    setLogs(filteredRows);
    setCount(effectiveCount);
    setTotal(effectiveCount);
    setCurrentPage(Number(payload?.page ?? page));
    setTotalPages(Math.max(1, Number(payload?.total_pages ?? 1)));
    setHasMore(Boolean(payload?.has_more));
    setSelectedLog((current) => filteredRows.find((entry) => entry.id === current?.id) ?? filteredRows[0] ?? null);
    setLoading(false);
  }

  useEffect(() => {
    let cancelled = false;
    const governancePresetSelected = activePreset === "governanca";

    async function loadFromSearchParams() {
      const nextFilters = filtersFromSearchParams();
      if (governancePresetSelected && !nextFilters.requestId.trim() && !activeGovernanceSealId) {
        setFilters(nextFilters);
        setLogs([]);
        setCount(0);
        setTotal(0);
        setCurrentPage(1);
        setTotalPages(1);
        setHasMore(false);
        setSelectedLog(null);
        setError(t("audit.presets.governanceMissingContext" as MessageKey));
        setLoading(false);
        return;
      }

      let effectiveFilters = nextFilters;
      effectiveFilters = resolveManualPackageMfaPresetFilters(effectiveFilters);
      if (governancePresetSelected) {
        effectiveFilters = await resolveGovernancePresetFilters(nextFilters);
        effectiveFilters = {
          ...effectiveFilters,
          action: "",
          resourceType: "",
          resourceId: "",
          limit: "200"
        };
      }

      if (cancelled) {
        return;
      }

      setFilters(effectiveFilters);
      await fetchLogs(effectiveFilters);
    }

    loadFromSearchParams().catch((error: unknown) => {
      if (cancelled) {
        return;
      }
      const message = error instanceof Error ? error.message : "";
      setLogs([]);
      setCount(0);
      setTotal(0);
      setCurrentPage(1);
      setTotalPages(1);
      setHasMore(false);
      setSelectedLog(null);
      setError(
        message === "governance_request_not_found" || message === "governance_resolve_failed"
          ? t("audit.presets.governanceResolveFailed" as MessageKey)
          : t("audit.errorLoad")
      );
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [activeGovernanceSealId, activePreset, searchParams, t]);

  const activeFilterCount = useMemo(() => {
    return [filters.requestId, filters.action, filters.resourceType, filters.reportId, filters.resourceId].filter((value) => value.trim()).length;
  }, [filters]);
  const dossierAuditPresetActive =
    filters.action === "coaf_regulatory_dossier_downloaded" && filters.resourceType === "ros_record";
  const manualPackageGovernancePresetActive = activePreset === "governanca" && Boolean(filters.requestId.trim());
  const manualPackageMfaPresetActive =
    activePreset === "manual-package-mfa" &&
    filters.action === MANUAL_PACKAGE_MFA_VIOLATION_ACTION &&
    filters.resourceType === "evidence_package_seal";
  const manualPackagePresetActive =
    MANUAL_PACKAGE_AUDIT_ACTIONS.has(filters.action) &&
    Boolean(filters.requestId.trim());
  const manualPackageContextRequestId = useMemo(() => {
    if (manualPackageGovernancePresetActive || manualPackagePresetActive) {
      return filters.requestId.trim();
    }
    if (!manualPackageMfaPresetActive) {
      return "";
    }
    return selectedLog?.request_id?.trim() ?? readMetadataString(selectedLog?.metadata, "request_id");
  }, [filters.requestId, manualPackageGovernancePresetActive, manualPackageMfaPresetActive, manualPackagePresetActive, selectedLog]);
  const manualPackageFamilyPresetActive =
    manualPackageGovernancePresetActive || manualPackagePresetActive || manualPackageMfaPresetActive;
  useEffect(() => {
    if (!manualPackageFamilyPresetActive || !manualPackageContextRequestId) {
      setManualPresetLogs([]);
      setManualPresetLoading(false);
      return;
    }

    const requestNumber = manualPresetRequestRef.current + 1;
    manualPresetRequestRef.current = requestNumber;
    setManualPresetLoading(true);
    const params = new URLSearchParams();
    params.set("request_id", manualPackageContextRequestId);
    if (filters.reportId.trim()) {
      params.set("report_id", filters.reportId.trim());
    }
    params.set("limit", "200");
    params.set("page", "1");

    fetch(`/api/app/audit/logs?${params.toString()}`, { cache: "no-store" })
      .then(async (res) => {
        const data = (await res.json().catch(() => null)) as AuditLogsResponse | { error?: string } | null;
        if (requestNumber !== manualPresetRequestRef.current) {
          return;
        }
        if (!res.ok) {
          setManualPresetLogs([]);
          setManualPresetLoading(false);
          return;
        }
        const payload = data && "data" in data ? data : null;
        const familyRows = (payload?.data ?? []).filter((entry) => MANUAL_PACKAGE_CONTEXT_ACTIONS.has(entry.action));
        setManualPresetLogs(familyRows);
        setManualPresetLoading(false);
      })
      .catch(() => {
        if (requestNumber !== manualPresetRequestRef.current) {
          return;
        }
        setManualPresetLogs([]);
        setManualPresetLoading(false);
      });
  }, [filters.reportId, manualPackageContextRequestId, manualPackageFamilyPresetActive]);
  const dossierAuditMetrics: DossierAuditMetrics = useMemo(() => {
    const dossierRows = logs.filter((entry) => entry.action === "coaf_regulatory_dossier_downloaded");
    const uniqueRosIds = new Set(dossierRows.map((entry) => entry.resource_id).filter((value): value is string => Boolean(value?.trim())));
    const latestRow = dossierRows[0] ?? null;
    const latestHash = latestRow ? readMetadataString(latestRow.metadata, "dossier_sha256") : "";
    const latestFilename = latestRow ? readMetadataString(latestRow.metadata, "filename") : "";
    const latestReportId = latestRow?.report_id?.trim() ?? "";
    return {
      totalDownloads: dossierRows.length,
      uniqueRosCount: uniqueRosIds.size,
      latestHash,
      latestFilename,
      latestReportId
    };
  }, [logs]);
  const manualPackageAuditMetrics: ManualPackageAuditMetrics = useMemo(() => {
    const manualRows = (manualPackageFamilyPresetActive ? manualPresetLogs : logs)
      .filter((entry) => MANUAL_PACKAGE_AUDIT_ACTIONS.has(entry.action))
      .slice()
      .sort((a, b) => String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")));
    const uniqueScopeIds = new Set(
      manualRows
        .map((entry) => readMetadataString(entry.metadata, "scope_id"))
        .filter((value): value is string => Boolean(value.trim()))
    );
    const exportRows = manualRows.filter((entry) => entry.action === "evidence_manual_review_package_exported");
    const signoffRows = manualRows.filter(
      (entry) =>
        entry.action === "evidence_manual_review_package_signoff_requested" ||
        entry.action === "evidence_manual_review_package_signoff_recorded"
    );
    const sealRows = manualRows.filter((entry) => entry.action === "evidence_manual_review_package_sealed");
    const latestRow = manualRows[0] ?? null;
    const latestExportRow = exportRows[0] ?? null;
    const latestHash =
      (latestRow && readMetadataString(latestRow.metadata, "package_sha256")) ||
      (latestExportRow && readMetadataString(latestExportRow.metadata, "package_sha256")) ||
      "";
    const latestFilename = latestExportRow ? readMetadataString(latestExportRow.metadata, "filename") : "";
    const latestReportId = latestRow?.report_id?.trim() || latestExportRow?.report_id?.trim() || "";
    const latestScopeId =
      (latestRow && readMetadataString(latestRow.metadata, "scope_id")) ||
      (latestExportRow && readMetadataString(latestExportRow.metadata, "scope_id")) ||
      "";
    const latestAction =
      (latestExportRow && readMetadataString(latestExportRow.metadata, "manual_review_action")) ||
      (latestRow && readMetadataString(latestRow.metadata, "manual_review_action")) ||
      "";
    const latestRequestId =
      latestRow?.request_id?.trim() ||
      readMetadataString(latestRow?.metadata, "request_id") ||
      latestExportRow?.request_id?.trim() ||
      readMetadataString(latestExportRow?.metadata, "request_id");
    return {
      totalEvents: manualRows.length,
      totalExports: exportRows.length,
      totalSignoffs: signoffRows.length,
      totalSeals: sealRows.length,
      uniqueScopeCount: uniqueScopeIds.size,
      latestHash,
      latestFilename,
      latestReportId,
      latestScopeId,
      latestActionLabel: latestAction ? resolveManualReviewActionLabel(latestAction) : t("audit.notAvailable"),
      latestStageLabel: latestRow ? formatAuditActionValue(latestRow.action) : t("audit.notAvailable"),
      latestEvidenceHref: buildManualEvidenceHref({
        requestId: latestRequestId,
        reportId: latestReportId,
        manualReviewAction: latestAction
      })
    };
  }, [logs, manualPackageFamilyPresetActive, manualPresetLogs, t]);
  const manualPackageGovernanceMetrics: ManualPackageGovernanceMetrics = useMemo(() => {
    if (!manualPackageGovernancePresetActive) {
      return {
        totalEvents: 0,
        totalExports: 0,
        totalSignoffs: 0,
        totalSeals: 0,
        totalRevocations: 0,
        totalSupersedes: 0,
        latestExportToSealDuration: t("audit.notAvailable"),
        latestSealToGovernanceDuration: t("audit.notAvailable"),
        evidenceHref: ""
      };
    }

    const manualRows = manualPresetLogs
      .filter((entry) => MANUAL_PACKAGE_AUDIT_ACTIONS.has(entry.action))
      .slice()
      .sort((a, b) => String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")));
    const exportRows = manualRows.filter((entry) => entry.action === "evidence_manual_review_package_exported");
    const signoffRows = manualRows.filter(
      (entry) =>
        entry.action === "evidence_manual_review_package_signoff_requested" ||
        entry.action === "evidence_manual_review_package_signoff_recorded"
    );
    const sealRows = manualRows.filter((entry) => entry.action === "evidence_manual_review_package_sealed");
    const revocationRows = manualRows.filter((entry) => entry.action === "evidence_manual_review_package_seal_revoked");
    const supersedeRows = manualRows.filter((entry) => entry.action === "evidence_manual_review_package_seal_superseded");
    const governanceRows = [...revocationRows, ...supersedeRows]
      .slice()
      .sort((a, b) => String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")));

    const latestSealRow = sealRows[0] ?? null;
    const latestSealTimestamp = parseAuditTimestamp(latestSealRow?.created_at);
    const latestSealPackageSha256 = readMetadataString(latestSealRow?.metadata, "package_sha256");
    const matchingExportRow = exportRows.find((entry) => {
      const exportTimestamp = parseAuditTimestamp(entry.created_at);
      if (latestSealTimestamp == null || exportTimestamp == null || exportTimestamp > latestSealTimestamp) {
        return false;
      }
      const exportPackageSha256 = readMetadataString(entry.metadata, "package_sha256");
      if (latestSealPackageSha256 && exportPackageSha256 === latestSealPackageSha256) {
        return true;
      }
      return Boolean(latestSealRow?.request_id?.trim() && entry.request_id?.trim() === latestSealRow.request_id?.trim());
    });
    const latestExportToSealDuration = (() => {
      const exportTimestamp = parseAuditTimestamp(matchingExportRow?.created_at);
      if (latestSealTimestamp == null || exportTimestamp == null) {
        return t("audit.notAvailable");
      }
      return formatAuditDurationValue(latestSealTimestamp - exportTimestamp);
    })();

    const latestGovernanceRow = governanceRows[0] ?? null;
    const latestGovernanceTimestamp = parseAuditTimestamp(latestGovernanceRow?.created_at);
    const latestGovernanceSealId =
      readMetadataString(latestGovernanceRow?.metadata, "seal_id") ||
      (latestGovernanceRow?.resource_type === "evidence_package_seal"
        ? latestGovernanceRow.resource_id?.trim() ?? ""
        : "");
    const latestGovernancePackageSha256 = readMetadataString(latestGovernanceRow?.metadata, "package_sha256");
    const matchingSealRowForGovernance = sealRows.find((entry) => {
      const sealTimestamp = parseAuditTimestamp(entry.created_at);
      if (latestGovernanceTimestamp == null || sealTimestamp == null || sealTimestamp > latestGovernanceTimestamp) {
        return false;
      }
      const candidateSealId =
        readMetadataString(entry.metadata, "seal_id") ||
        (entry.resource_type === "evidence_package_seal" ? entry.resource_id?.trim() ?? "" : "");
      if (latestGovernanceSealId && candidateSealId === latestGovernanceSealId) {
        return true;
      }
      const candidatePackageSha256 = readMetadataString(entry.metadata, "package_sha256");
      if (latestGovernancePackageSha256 && candidatePackageSha256 === latestGovernancePackageSha256) {
        return true;
      }
      return Boolean(latestGovernanceRow?.request_id?.trim() && entry.request_id?.trim() === latestGovernanceRow.request_id?.trim());
    });
    const latestSealToGovernanceDuration = (() => {
      const sealTimestamp = parseAuditTimestamp(matchingSealRowForGovernance?.created_at);
      if (latestGovernanceTimestamp == null || sealTimestamp == null) {
        return t("audit.notAvailable");
      }
      return formatAuditDurationValue(latestGovernanceTimestamp - sealTimestamp);
    })();

    return {
      totalEvents: manualRows.length,
      totalExports: exportRows.length,
      totalSignoffs: signoffRows.length,
      totalSeals: sealRows.length,
      totalRevocations: revocationRows.length,
      totalSupersedes: supersedeRows.length,
      latestExportToSealDuration,
      latestSealToGovernanceDuration,
      evidenceHref: manualPackageAuditMetrics.latestEvidenceHref
    };
  }, [manualPackageAuditMetrics.latestEvidenceHref, manualPackageGovernancePresetActive, manualPresetLogs, t]);
  const manualPackageMfaMetrics: ManualPackageMfaMetrics = useMemo(() => {
    if (!manualPackageMfaPresetActive) {
      return {
        totalEvents: 0,
        uniqueRequestCount: 0,
        uniqueSealCount: 0,
        total2faRequired: 0,
        totalProviderNotHomologated: 0,
        latestRequestId: "",
        latestSealId: "",
        latestAuthRole: "",
        latestSignerRoleLabel: "",
        latestMfaMode: ""
      };
    }

    const mfaRows = logs
      .filter((entry) => entry.action === MANUAL_PACKAGE_MFA_VIOLATION_ACTION)
      .slice()
      .sort((a, b) => String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")));
    const uniqueRequestIds = new Set(
      mfaRows
        .map((entry) => entry.request_id?.trim() ?? readMetadataString(entry.metadata, "request_id"))
        .filter((value): value is string => Boolean(value))
    );
    const uniqueSealIds = new Set(
      mfaRows
        .map(
          (entry) =>
            readMetadataString(entry.metadata, "seal_id") ||
            (entry.resource_type === "evidence_package_seal" ? entry.resource_id?.trim() ?? "" : "")
        )
        .filter((value): value is string => Boolean(value))
    );
    const total2faRequired = mfaRows.filter((entry) => readMetadataString(entry.metadata, "detail") === "2fa_required").length;
    const totalProviderNotHomologated = mfaRows.filter(
      (entry) => readMetadataString(entry.metadata, "detail") === "mfa_not_homologated_for_oidc"
    ).length;
    const latestRow = mfaRows[0] ?? null;
    const latestRequestId = latestRow?.request_id?.trim() ?? readMetadataString(latestRow?.metadata, "request_id");
    const latestSealId =
      readMetadataString(latestRow?.metadata, "seal_id") ||
      (latestRow?.resource_type === "evidence_package_seal" ? latestRow.resource_id?.trim() ?? "" : "");
    const latestAuthRole = readMetadataString(latestRow?.metadata, "auth_role");
    const latestSignerRole = readMetadataString(latestRow?.metadata, "asserted_signer_role");
    const latestMfaMode = readMetadataString(latestRow?.metadata, "mfa_mode");

    return {
      totalEvents: mfaRows.length,
      uniqueRequestCount: uniqueRequestIds.size,
      uniqueSealCount: uniqueSealIds.size,
      total2faRequired,
      totalProviderNotHomologated,
      latestRequestId,
      latestSealId,
      latestAuthRole,
      latestSignerRoleLabel: resolveManualPackageSignerRoleLabel(latestSignerRole),
      latestMfaMode
    };
  }, [logs, manualPackageMfaPresetActive, t]);
  const manualPackageMfaRoleSummary: ManualPackageMfaRoleSummary = useMemo(() => {
    if (!manualPackageMfaPresetActive) {
      return { authRoles: [], signerRoles: [] };
    }

    const authRoleCounts = new Map<string, number>();
    const signerRoleCounts = new Map<string, number>();
    for (const entry of logs) {
      if (entry.action !== MANUAL_PACKAGE_MFA_VIOLATION_ACTION) {
        continue;
      }
      const authRole = readMetadataString(entry.metadata, "auth_role") || t("audit.notAvailable");
      authRoleCounts.set(authRole, (authRoleCounts.get(authRole) ?? 0) + 1);

      const signerRole = readMetadataString(entry.metadata, "asserted_signer_role");
      const signerRoleLabel = signerRole ? resolveManualPackageSignerRoleLabel(signerRole) : t("audit.notAvailable");
      signerRoleCounts.set(signerRoleLabel, (signerRoleCounts.get(signerRoleLabel) ?? 0) + 1);
    }

    const toSortedItems = (counts: Map<string, number>) =>
      Array.from(counts.entries())
        .map(([label, count]) => ({
          key: `${label}-${count}`,
          label,
          count
        }))
        .sort((a, b) => {
          if (b.count !== a.count) {
            return b.count - a.count;
          }
          return a.label.localeCompare(b.label);
        });

    return {
      authRoles: toSortedItems(authRoleCounts),
      signerRoles: toSortedItems(signerRoleCounts)
    };
  }, [logs, manualPackageMfaPresetActive, t]);
  const manualPackageMfaTypeSummary: ManualPackageMfaTypeSummaryItem[] = useMemo(() => {
    if (!manualPackageMfaPresetActive) {
      return [];
    }

    const totalEvents = manualPackageMfaMetrics.totalEvents;
    const total2faRequired = manualPackageMfaMetrics.total2faRequired;
    const totalProviderNotHomologated = manualPackageMfaMetrics.totalProviderNotHomologated;
    const totalOther = Math.max(0, totalEvents - total2faRequired - totalProviderNotHomologated);
    const buildShareLabel = (count: number) => {
      if (totalEvents <= 0) {
        return "0%";
      }
      return `${Math.round((count / totalEvents) * 100)}%`;
    };

    const items: ManualPackageMfaTypeSummaryItem[] = [
      {
        key: "2fa_required",
        label: t("audit.presets.manualMfaType2faRequired" as MessageKey),
        count: total2faRequired,
        shareLabel: buildShareLabel(total2faRequired)
      },
      {
        key: "mfa_not_homologated_for_oidc",
        label: t("audit.presets.manualMfaTypeProviderNotHomologated" as MessageKey),
        count: totalProviderNotHomologated,
        shareLabel: buildShareLabel(totalProviderNotHomologated)
      }
    ];
    if (totalOther > 0) {
      items.push({
        key: "other",
        label: t("audit.presets.manualMfaTypeOther" as MessageKey),
        count: totalOther,
        shareLabel: buildShareLabel(totalOther)
      });
    }
    return items;
  }, [manualPackageMfaMetrics.total2faRequired, manualPackageMfaMetrics.totalEvents, manualPackageMfaMetrics.totalProviderNotHomologated, manualPackageMfaPresetActive, t]);
  const manualPackageMfaFamilies: ManualPackageMfaFamily[] = useMemo(() => {
    if (!manualPackageMfaPresetActive) {
      return [];
    }

    const resolveDominantType = (family: {
      total2faRequired: number;
      totalProviderNotHomologated: number;
      totalEvents: number;
    }): Pick<ManualPackageMfaFamily, "dominantTypeLabel" | "dominantTypeTone"> => {
      if (family.totalProviderNotHomologated >= family.total2faRequired && family.totalProviderNotHomologated > 0) {
        return {
          dominantTypeLabel: t("audit.presets.manualMfaTypeProviderNotHomologated" as MessageKey),
          dominantTypeTone: "danger"
        };
      }
      if (family.total2faRequired > 0) {
        return {
          dominantTypeLabel: t("audit.presets.manualMfaType2faRequired" as MessageKey),
          dominantTypeTone: "warning"
        };
      }
      return {
        dominantTypeLabel: t("audit.presets.manualMfaTypeOther" as MessageKey),
        dominantTypeTone: "success"
      };
    };

    const families = new Map<string, Omit<ManualPackageMfaFamily, "href" | "isActive">>();
    for (const entry of logs) {
      if (entry.action !== MANUAL_PACKAGE_MFA_VIOLATION_ACTION) {
        continue;
      }
      const requestId = entry.request_id?.trim() ?? readMetadataString(entry.metadata, "request_id");
      const sealId =
        readMetadataString(entry.metadata, "seal_id") ||
        (entry.resource_type === "evidence_package_seal" ? entry.resource_id?.trim() ?? "" : "");
      const key = `${requestId || "no-request"}::${sealId || "no-seal"}`;
      const detail = readMetadataString(entry.metadata, "detail");
      const signerRole = readMetadataString(entry.metadata, "asserted_signer_role");
      const createdAt = entry.created_at?.trim() ?? "";
      const current = families.get(key);

      if (!current) {
        const baseFamily = {
          key,
          requestId,
          sealId,
          totalEvents: 1,
          total2faRequired: detail === "2fa_required" ? 1 : 0,
          totalProviderNotHomologated: detail === "mfa_not_homologated_for_oidc" ? 1 : 0,
          latestCreatedAt: createdAt,
          latestAuthRole: readMetadataString(entry.metadata, "auth_role"),
          latestSignerRoleLabel: resolveManualPackageSignerRoleLabel(signerRole),
          latestMfaMode: readMetadataString(entry.metadata, "mfa_mode"),
          latestDetail: detail
        };
        families.set(key, {
          ...baseFamily,
          ...resolveDominantType(baseFamily)
        });
        continue;
      }

      current.totalEvents += 1;
      if (detail === "2fa_required") {
        current.total2faRequired += 1;
      }
      if (detail === "mfa_not_homologated_for_oidc") {
        current.totalProviderNotHomologated += 1;
      }
      if (createdAt.localeCompare(current.latestCreatedAt) > 0) {
        current.latestCreatedAt = createdAt;
        current.latestAuthRole = readMetadataString(entry.metadata, "auth_role");
        current.latestSignerRoleLabel = resolveManualPackageSignerRoleLabel(signerRole);
        current.latestMfaMode = readMetadataString(entry.metadata, "mfa_mode");
        current.latestDetail = detail;
      }
      const dominantType = resolveDominantType(current);
      current.dominantTypeLabel = dominantType.dominantTypeLabel;
      current.dominantTypeTone = dominantType.dominantTypeTone;
    }

    return Array.from(families.values())
      .map((family) => ({
        ...family,
        href: buildManualPackageMfaAuditHref({ requestId: family.requestId, sealId: family.sealId }),
        isActive:
          (!filters.requestId.trim() || filters.requestId.trim() === family.requestId) &&
          (!filters.resourceId.trim() || filters.resourceId.trim() === family.sealId)
      }))
      .sort((a, b) => {
        if (b.totalEvents !== a.totalEvents) {
          return b.totalEvents - a.totalEvents;
        }
        if (b.totalProviderNotHomologated !== a.totalProviderNotHomologated) {
          return b.totalProviderNotHomologated - a.totalProviderNotHomologated;
        }
        if (b.total2faRequired !== a.total2faRequired) {
          return b.total2faRequired - a.total2faRequired;
        }
        return String(b.latestCreatedAt).localeCompare(String(a.latestCreatedAt));
      });
  }, [filters.requestId, filters.resourceId, logs, manualPackageMfaPresetActive, t]);
  const manualPackageMfaAllHref = buildManualPackageMfaAuditHref();
  const selectedContext = useMemo(() => (selectedLog ? inferLogOperationalContext(selectedLog) : null), [selectedLog]);
  useEffect(() => {
    const reportId = selectedContext?.reportId?.trim() ?? "";
    if (!reportId || Boolean(selectedContext?.rosId)) {
      setLinkedRosIdFromReport(null);
      setLinkedRosLoading(false);
      return;
    }

    setLinkedRosLoading(true);
    fetch(`/api/app/reports/${encodeURIComponent(reportId)}/ros-coaf-ref`, { cache: "no-store" })
      .then(async (res) => {
        const data = (await res.json().catch(() => null)) as { ros_id?: string | null } | null;
        if (!res.ok) {
          setLinkedRosIdFromReport(null);
          setLinkedRosLoading(false);
          return;
        }
        const rosIdValue = typeof data?.ros_id === "string" ? data.ros_id.trim() : "";
        setLinkedRosIdFromReport(rosIdValue ? rosIdValue : null);
        setLinkedRosLoading(false);
      })
      .catch(() => {
        setLinkedRosIdFromReport(null);
        setLinkedRosLoading(false);
      });
  }, [selectedContext?.reportId, selectedContext?.rosId]);
  const selectedContextForLinks = useMemo(() => {
    if (!selectedContext) {
      return null;
    }
    if (selectedContext.rosId) {
      return selectedContext;
    }
    if (linkedRosIdFromReport) {
      return { ...selectedContext, rosId: linkedRosIdFromReport };
    }
    return selectedContext;
  }, [linkedRosIdFromReport, selectedContext]);
  const selectedDossierContext: AuditDossierContext | null = useMemo(() => {
    if (!selectedLog || selectedLog.action !== "coaf_regulatory_dossier_downloaded") {
      return null;
    }

    const reportId = selectedLog.report_id?.trim() ?? "";
    const filename = readMetadataString(selectedLog.metadata, "filename");
    const dossierSha256 = readMetadataString(selectedLog.metadata, "dossier_sha256");
    const rosId =
      selectedContextForLinks?.rosId?.trim() ??
      (selectedLog.resource_type === "ros_record" ? selectedLog.resource_id?.trim() ?? "" : "");

    return {
      reportId,
      filename,
      dossierSha256,
      rosId
    };
  }, [selectedContextForLinks?.rosId, selectedLog]);
  const selectedManualPackageContext: AuditManualPackageContext | null = useMemo(() => {
    if (!selectedLog || !MANUAL_PACKAGE_CONTEXT_ACTIONS.has(selectedLog.action)) {
      return null;
    }

    const requestId = selectedLog.request_id?.trim() ?? readMetadataString(selectedLog.metadata, "request_id");
    const reportId = selectedLog.report_id?.trim() ?? readMetadataString(selectedLog.metadata, "report_id");
    const packageSha256 = readMetadataString(selectedLog.metadata, "package_sha256");
    const contextRows = [...manualPresetLogs, ...logs];
    const matchingExportRow = contextRows.find((entry) => {
      if (entry.action !== "evidence_manual_review_package_exported") {
        return false;
      }
      const exportHash = readMetadataString(entry.metadata, "package_sha256");
      if (packageSha256 && exportHash === packageSha256) {
        return true;
      }
      const exportRequestId = entry.request_id?.trim() ?? readMetadataString(entry.metadata, "request_id");
      return Boolean(requestId && exportRequestId === requestId);
    });

    const scopeId =
      readMetadataString(selectedLog.metadata, "scope_id") || readMetadataString(matchingExportRow?.metadata, "scope_id");
    const filename =
      readMetadataString(selectedLog.metadata, "filename") || readMetadataString(matchingExportRow?.metadata, "filename");
    const resolvedPackageSha256 = packageSha256 || readMetadataString(matchingExportRow?.metadata, "package_sha256");
    const manualReviewAction =
      readMetadataString(selectedLog.metadata, "manual_review_action") ||
      readMetadataString(matchingExportRow?.metadata, "manual_review_action");
    const workspaceStatus =
      readMetadataString(selectedLog.metadata, "workspace_status") ||
      readMetadataString(selectedLog.metadata, "local_workspace_status") ||
      readMetadataString(matchingExportRow?.metadata, "workspace_status") ||
      readMetadataString(matchingExportRow?.metadata, "local_workspace_status");
    const sealStatus = readMetadataString(selectedLog.metadata, "seal_status");
    const sealId =
      readMetadataString(selectedLog.metadata, "seal_id") ||
      (selectedLog.resource_type === "evidence_package_seal" ? selectedLog.resource_id?.trim() ?? "" : "");
    const signerRole = readMetadataString(selectedLog.metadata, "signer_role") || readMetadataString(selectedLog.metadata, "asserted_signer_role");
    const decision = readMetadataString(selectedLog.metadata, "decision");
    const signatureAlgorithm = readMetadataString(selectedLog.metadata, "signature_algorithm");
    const trustBundleRef = readMetadataString(selectedLog.metadata, "certificate_bundle_ref");
    const authRole = readMetadataString(selectedLog.metadata, "auth_role");
    const mfaMode = readMetadataString(selectedLog.metadata, "mfa_mode");
    const twoFactorStatus = readMetadataString(selectedLog.metadata, "two_factor_status");
    const mfaProviderHomologatedValue = selectedLog.metadata?.mfa_provider_homologated;
    const mfaProviderHomologated =
      typeof mfaProviderHomologatedValue === "boolean"
        ? mfaProviderHomologatedValue
          ? "true"
          : "false"
        : readMetadataString(selectedLog.metadata, "mfa_provider_homologated");
    const mfaViolationDetail = readMetadataString(selectedLog.metadata, "detail");
    const ticketRef = readMetadataString(selectedLog.metadata, "ticket_ref");
    const governanceReason = readMetadataString(selectedLog.metadata, "reason");
    const supersededBySealId = readMetadataString(selectedLog.metadata, "superseded_by_seal_id");
    const revokedAt =
      readMetadataString(selectedLog.metadata, "revoked_at") ||
      (selectedLog.action === "evidence_manual_review_package_seal_revoked" ? selectedLog.created_at?.trim() ?? "" : "");
    const supersededAt =
      readMetadataString(selectedLog.metadata, "superseded_at") ||
      (selectedLog.action === "evidence_manual_review_package_seal_superseded"
        ? selectedLog.created_at?.trim() ?? ""
        : "");
    const verificationSummary = selectedLog.metadata?.verification_summary;
    const verificationMethod =
      verificationSummary && typeof verificationSummary === "object" && !Array.isArray(verificationSummary)
        ? readMetadataString(verificationSummary as Record<string, unknown>, "verification_method")
        : "";

    return {
      eventAction: selectedLog.action,
      eventActionLabel: formatAuditActionValue(selectedLog.action),
      requestId,
      reportId,
      scopeId,
      filename,
      packageSha256: resolvedPackageSha256,
      manualReviewAction,
      manualReviewActionLabel: resolveManualReviewActionLabel(manualReviewAction),
      workspaceStatus,
      sealStatus: resolveManualPackageSealStatusLabel(sealStatus),
      sealId,
      signerRole,
      signerRoleLabel: resolveManualPackageSignerRoleLabel(signerRole),
      decision,
      decisionLabel: resolveManualPackageDecisionLabel(decision),
      signatureAlgorithm,
      trustBundleRef,
      verificationMethod,
      authRole,
      mfaMode,
      twoFactorStatus,
      mfaProviderHomologated,
      mfaViolationDetail,
      ticketRef,
      governanceReason,
      supersededBySealId,
      revokedAt,
      supersededAt,
      evidenceHref: buildManualEvidenceHref({ requestId, reportId, manualReviewAction })
    };
  }, [logs, manualPresetLogs, selectedLog, t]);
  const selectedHashContext: AuditHashContext | null = useMemo(() => {
    const resolved = resolveHashContext({
      packageSha256: selectedManualPackageContext?.packageSha256,
      dossierSha256: selectedDossierContext?.dossierSha256,
      fileSha256: selectedLog?.file_hash_sha256
    });
    if (!resolved) {
      return null;
    }

    const isManualPackage = resolved.source === "package";
    const isDossier = resolved.source === "dossier";
    return {
      primaryHash: resolved.primaryHash,
      sourceLabel: t(
        isManualPackage
          ? ("audit.details.hashSourceManualPackage" as MessageKey)
          : isDossier
            ? ("audit.details.hashSourceDossier" as MessageKey)
            : ("audit.details.hashSourceFile" as MessageKey)
      ),
      artifactTypeLabel: t(
        isManualPackage
          ? ("audit.details.artifactTypeManualPackage" as MessageKey)
          : isDossier
            ? ("audit.details.artifactTypeDossier" as MessageKey)
            : ("audit.details.artifactTypeFile" as MessageKey)
      )
    };
  }, [selectedDossierContext?.dossierSha256, selectedLog?.file_hash_sha256, selectedManualPackageContext?.packageSha256, t]);
  const selectedContextLinks = useMemo(() => {
    if (!selectedContextForLinks) {
      return [] as Array<OperationalContextLink & { label: string }>;
    }

    const labelByKind: Record<OperationalContextLink["kind"], string> = {
      case: t("audit.details.openCase"),
      audit: t("audit.details.openCase"),
      evidence: t("audit.details.openEvidence"),
      reports: t("audit.details.openReports"),
      investigate: t("audit.details.openInvestigate"),
      sanctions: t("audit.details.openSanctions"),
      blocks: t("audit.details.openBlocks"),
      counterparty: t("audit.details.openCounterparty"),
      ros: t("audit.details.openRos")
    };

    return buildOperationalContextLinks(selectedContextForLinks, {
      includeEvidence: true,
      evidenceDomain: "all",
      auditFallbackResourceType: "audit_log",
      investigateIncludeCaseId: true
    })
      .filter((link: OperationalContextLink) => link.kind !== "audit")
      .map((link: OperationalContextLink) => ({
        ...link,
        label: labelByKind[link.kind]
      }));
  }, [selectedContextForLinks, t]);

  async function onExportRosCoafRegulatoryDossier(rosId: string) {
    const normalizedRosId = rosId.trim();
    if (!normalizedRosId) {
      return;
    }

    setExportingRosCoafDossier(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch(`/api/app/reports/ros-coaf/${encodeURIComponent(normalizedRosId)}/regulatory-dossier`, { cache: "no-store" });
      const data = (await res.json().catch(() => null)) as { error?: string; detail?: unknown } | null;
      if (!res.ok) {
        setError(resolveApiErrorMessage(t, data, t("audit.details.exportRosDossierError" as MessageKey)));
        setExportingRosCoafDossier(false);
        return;
      }

      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = href;
      link.download = resolveDownloadFilename(
        res.headers.get("content-disposition"),
        `ontrackchain-ros-coaf-regulatory-dossier-${normalizedRosId}.json`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(href);
      setNotice(
        t("audit.details.exportRosDossierSuccess" as MessageKey, {
          hash: summarizeDossierHash(res.headers.get("x-ontrack-dossier-sha256"))
        })
      );
    } catch {
      setError(t("audit.details.exportRosDossierError" as MessageKey));
    } finally {
      setExportingRosCoafDossier(false);
    }
  }

  function updateFilter<K extends keyof AuditFilters>(key: K, value: AuditFilters[K]) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  async function onSearch() {
    await fetchLogs(filters, 1);
  }

  async function onReset() {
    setFilters(DEFAULT_FILTERS);
    await fetchLogs(DEFAULT_FILTERS, 1);
  }

  async function onPreviousPage() {
    if (currentPage <= 1 || loading) {
      return;
    }
    await fetchLogs(filters, currentPage - 1);
  }

  async function onNextPage() {
    if (!hasMore || loading) {
      return;
    }
    await fetchLogs(filters, currentPage + 1);
  }

  async function onExportEvidence() {
    setExporting(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch("/api/app/audit/evidence-export", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          format: "json",
          request_id: filters.requestId.trim() || null,
          action: filters.action.trim() || null,
          resource_type: filters.resourceType.trim() || null,
          report_id: filters.reportId.trim() || null,
          resource_id: filters.resourceId.trim() || null,
          limit: Number(filters.limit),
          include_audit_logs: true,
          include_credit_ledger: true,
          include_reports: true
        })
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as { error?: string } | null;
        throw new Error(
          data?.error ? resolveApiErrorMessage(t, data.error, data.error) : t("audit.errorExport")
        );
      }

      const blob = await res.blob();
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      const disposition = res.headers.get("content-disposition");
      const filenameMatch = disposition?.match(/filename="([^"]+)"/);
      link.href = href;
      link.download = filenameMatch?.[1] ?? "ontrackchain-evidence-bundle.json";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(href);
      setNotice(t("audit.export.success"));
    } catch (exportError) {
      setError(exportError instanceof Error ? exportError.message : t("audit.errorExport"));
    } finally {
      setExporting(false);
    }
  }

  return (
    <AppShell
      title={t("audit.title")}
      subtitle={t("audit.subtitle")}
      activePath="/audit"
      actions={<a href="/dashboard" className="otc-link-button">{t("audit.back")}</a>}
    >
      <MetricGrid>
        <MetricCard label={t("audit.stats.events")} value={loading ? "..." : count} meta={t("audit.stats.eventsMeta")} />
        <MetricCard label={t("audit.stats.total")} value={loading ? "..." : total} meta={t("audit.stats.totalMeta")} />
        <MetricCard label={t("audit.stats.filters")} value={activeFilterCount} meta={t("audit.stats.filtersMeta")} />
        <MetricCard label={t("audit.stats.selected")} value={selectedLog ? formatAuditActionValue(selectedLog.action) : "--"} meta={t("audit.stats.selectedMeta")} />
        <MetricCard label={t("audit.stats.integrity")} value={selectedLog?.file_hash_sha256 ? "SHA-256" : t("audit.notAvailable")} meta={t("audit.stats.integrityMeta")} accent />
      </MetricGrid>

      <Panel title={t("audit.filters.title")} description={t("audit.filters.description")}>
        <div className="otc-grid otc-grid--audit-filters">
          <label className="otc-field">
            {t("audit.filters.requestId")}
            <input className="otc-input" data-testid="audit-filter-request-id" value={filters.requestId} onChange={(e) => updateFilter("requestId", e.target.value)} />
          </label>
          <label className="otc-field">
            {t("audit.filters.action")}
            <select className="otc-select" data-testid="audit-filter-action" value={filters.action} onChange={(e) => updateFilter("action", e.target.value)}>
              <option value="">{t("audit.filters.all")}</option>
              {AUDIT_ACTION_VALUES.map((value) => (
                <option key={value} value={value}>
                  {formatAuditActionValue(value)}
                </option>
              ))}
            </select>
          </label>
          <label className="otc-field">
            {t("audit.filters.resourceType")}
            <select className="otc-select" data-testid="audit-filter-resource-type" value={filters.resourceType} onChange={(e) => updateFilter("resourceType", e.target.value)}>
              <option value="">{t("audit.filters.allMasculine")}</option>
              {AUDIT_RESOURCE_TYPE_VALUES.map((value) => (
                <option key={value} value={value}>
                  {formatAuditResourceTypeValue(value)}
                </option>
              ))}
            </select>
          </label>
          <label className="otc-field">
            {t("audit.filters.reportId")}
            <input className="otc-input" data-testid="audit-filter-report-id" value={filters.reportId} onChange={(e) => updateFilter("reportId", e.target.value)} />
          </label>
          <label className="otc-field">
            {t("audit.filters.resourceId")}
            <input className="otc-input" data-testid="audit-filter-resource-id" value={filters.resourceId} onChange={(e) => updateFilter("resourceId", e.target.value)} />
          </label>
          <label className="otc-field">
            {t("audit.filters.limit")}
            <select className="otc-select" data-testid="audit-filter-limit" value={filters.limit} onChange={(e) => updateFilter("limit", e.target.value)}>
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="200">200</option>
            </select>
          </label>
        </div>
        <div className="otc-controls otc-audit-summary">
          <button type="button" className="otc-button otc-button--accent" data-testid="audit-search-btn" onClick={() => void onSearch()}>
            {t("audit.actions.search")}
          </button>
          <button type="button" className="otc-button otc-button--ghost" data-testid="audit-reset-btn" onClick={() => void onReset()}>
            {t("audit.actions.reset")}
          </button>
          <button type="button" className="otc-button otc-button--ghost" data-testid="audit-export-btn" onClick={() => void onExportEvidence()} disabled={exporting}>
            {exporting ? t("audit.actions.exportLoading") : t("audit.actions.export")}
          </button>
          <span data-testid="audit-summary" className="otc-muted">
            {loading ? t("audit.summary.loading") : t("audit.summary.found", { count: total })}
            {activeFilterCount ? t("audit.summary.activeFilters", { count: activeFilterCount }) : ""}
          </span>
        </div>
      </Panel>

      {error ? <Message tone="error"><span data-testid="audit-error">{error}</span></Message> : null}
      {notice ? <Message tone="success"><span data-testid="audit-export-notice">{notice}</span></Message> : null}
      {dossierAuditPresetActive ? (
        <Message>
          <div className="otc-stack">
            <div className="otc-controls otc-controls--spaced">
              <span data-testid="audit-dossier-preset-notice">
                {t("audit.presets.dossierDownloads", {
                  rosId: filters.resourceId.trim() || t("audit.notAvailable")
                })}
              </span>
              {dossierAuditMetrics.latestReportId ? (
                <a
                  className="otc-link-button"
                  href={`/reports?history_report_id=${encodeURIComponent(dossierAuditMetrics.latestReportId)}`}
                  data-testid="audit-dossier-open-latest-report"
                >
                  {t("audit.presets.openLatestReport")}
                </a>
              ) : null}
              {filters.resourceId.trim() ? (
                <a
                  className="otc-link-button"
                  href={`/ros-coaf?ros_id=${encodeURIComponent(filters.resourceId.trim())}${
                    filters.reportId.trim() ? `&report_id=${encodeURIComponent(filters.reportId.trim())}` : ""
                  }`}
                  data-testid="audit-dossier-open-roscoaf"
                >
                  {t("audit.presets.openRosCoaf")}
                </a>
              ) : null}
            </div>
            {renderDossierPresetLatestContext(loading, dossierAuditMetrics)}
          </div>
        </Message>
      ) : null}
      {manualPackageGovernancePresetActive ? (
        <Message>
          <div className="otc-stack">
            <div className="otc-controls otc-controls--spaced">
              <span data-testid="audit-governance-preset-notice">
                {t("audit.presets.manualPackageGovernance" as MessageKey, {
                  requestId: filters.requestId.trim() || t("audit.notAvailable")
                })}
              </span>
              <a
                className="otc-link-button"
                href={manualPackageGovernanceMetrics.evidenceHref || "#"}
                data-testid="audit-governance-open-evidence"
              >
                {t("audit.presets.openEvidenceManualSource" as MessageKey)}
              </a>
            </div>
            {renderManualPackagePresetLatestContext(loading || manualPresetLoading, manualPackageAuditMetrics)}
          </div>
        </Message>
      ) : null}
      {manualPackagePresetActive && !manualPackageGovernancePresetActive ? (
        <Message>
          <div className="otc-stack">
            <div className="otc-controls otc-controls--spaced">
              <span data-testid="audit-manual-preset-notice">
                {t("audit.presets.manualPackageCustody" as MessageKey, {
                  requestId: filters.requestId.trim() || t("audit.notAvailable")
                })}
              </span>
              <a
                className="otc-link-button"
                href={manualPackageAuditMetrics.latestEvidenceHref || "#"}
                data-testid="audit-manual-open-evidence"
              >
                {t("audit.presets.openEvidenceManualSource" as MessageKey)}
              </a>
              {manualPackageAuditMetrics.latestReportId ? (
                <a
                  className="otc-link-button"
                  href={`/reports?history_report_id=${encodeURIComponent(manualPackageAuditMetrics.latestReportId)}`}
                  data-testid="audit-manual-open-latest-report"
                >
                  {t("audit.presets.openLatestReport")}
                </a>
              ) : null}
            </div>
            {renderManualPackagePresetLatestContext(loading || manualPresetLoading, manualPackageAuditMetrics)}
          </div>
        </Message>
      ) : null}
      {manualPackageMfaPresetActive ? (
        <Message>
          <div className="otc-stack">
            <div className="otc-controls otc-controls--spaced">
              <span data-testid="audit-manual-mfa-preset-notice">
                {t("audit.presets.manualPackageMfaViolations" as MessageKey)}
              </span>
              {selectedManualPackageContext?.evidenceHref ? (
                <a
                  className="otc-link-button"
                  href={selectedManualPackageContext.evidenceHref}
                  data-testid="audit-manual-mfa-open-evidence"
                >
                  {t("audit.presets.openEvidenceManualSource" as MessageKey)}
                </a>
              ) : null}
              {(filters.requestId.trim() || filters.resourceId.trim()) ? (
                <a className="otc-link-button" href={manualPackageMfaAllHref} data-testid="audit-manual-mfa-open-all">
                  {t("audit.presets.openFullMfaScope" as MessageKey)}
                </a>
              ) : null}
            </div>
            {renderManualPackageMfaPresetLatestContext(loading || manualPresetLoading, manualPackageMfaMetrics)}
          </div>
        </Message>
      ) : null}
      {dossierAuditPresetActive ? (
        <MetricGrid>
          <MetricCard
            label={t("audit.presets.metrics.totalDownloads")}
            value={loading ? "..." : dossierAuditMetrics.totalDownloads}
            meta={t("audit.presets.metrics.totalDownloadsMeta")}
          />
          <MetricCard
            label={t("audit.presets.metrics.uniqueRos")}
            value={loading ? "..." : dossierAuditMetrics.uniqueRosCount}
            meta={t("audit.presets.metrics.uniqueRosMeta")}
          />
          <MetricCard
            label={t("audit.presets.metrics.latestHash")}
            value={loading ? "..." : summarizeDossierHash(dossierAuditMetrics.latestHash)}
            meta={t("audit.presets.metrics.latestHashMeta")}
          />
          <MetricCard
            label={t("audit.presets.metrics.latestReportId")}
            value={loading ? "..." : dossierAuditMetrics.latestReportId || t("audit.notAvailable")}
            meta={t("audit.presets.metrics.latestReportIdMeta")}
          />
          <MetricCard
            label={t("audit.presets.metrics.latestFilename")}
            value={loading ? "..." : dossierAuditMetrics.latestFilename || t("audit.notAvailable")}
            meta={t("audit.presets.metrics.latestFilenameMeta")}
          />
        </MetricGrid>
      ) : null}
      {manualPackageGovernancePresetActive ? (
        <MetricGrid>
          <MetricCard
            label={t("audit.presets.metrics.manualTotalEvents" as MessageKey)}
            value={loading || manualPresetLoading ? "..." : manualPackageGovernanceMetrics.totalEvents}
            meta={t("audit.presets.metrics.manualTotalEventsMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualTotalExports" as MessageKey)}
            value={loading || manualPresetLoading ? "..." : manualPackageGovernanceMetrics.totalExports}
            meta={t("audit.presets.metrics.manualTotalExportsMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualTotalSignoffs" as MessageKey)}
            value={loading || manualPresetLoading ? "..." : manualPackageGovernanceMetrics.totalSignoffs}
            meta={t("audit.presets.metrics.manualTotalSignoffsMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualTotalSeals" as MessageKey)}
            value={loading || manualPresetLoading ? "..." : manualPackageGovernanceMetrics.totalSeals}
            meta={t("audit.presets.metrics.manualTotalSealsMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualTotalRevocations" as MessageKey)}
            value={loading || manualPresetLoading ? "..." : manualPackageGovernanceMetrics.totalRevocations}
            meta={t("audit.presets.metrics.manualTotalRevocationsMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualTotalSupersedes" as MessageKey)}
            value={loading || manualPresetLoading ? "..." : manualPackageGovernanceMetrics.totalSupersedes}
            meta={t("audit.presets.metrics.manualTotalSupersedesMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualLatestExportToSeal" as MessageKey)}
            value={loading || manualPresetLoading ? "..." : manualPackageGovernanceMetrics.latestExportToSealDuration}
            meta={t("audit.presets.metrics.manualLatestExportToSealMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualLatestSealToGovernance" as MessageKey)}
            value={loading || manualPresetLoading ? "..." : manualPackageGovernanceMetrics.latestSealToGovernanceDuration}
            meta={t("audit.presets.metrics.manualLatestSealToGovernanceMeta" as MessageKey)}
          />
        </MetricGrid>
      ) : null}
      {manualPackagePresetActive && !manualPackageGovernancePresetActive ? (
        <MetricGrid>
          <MetricCard
            label={t("audit.presets.metrics.manualTotalEvents" as MessageKey)}
            value={loading || manualPresetLoading ? "..." : manualPackageAuditMetrics.totalEvents}
            meta={t("audit.presets.metrics.manualTotalEventsMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualTotalExports" as MessageKey)}
            value={loading ? "..." : manualPackageAuditMetrics.totalExports}
            meta={t("audit.presets.metrics.manualTotalExportsMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualTotalSignoffs" as MessageKey)}
            value={loading || manualPresetLoading ? "..." : manualPackageAuditMetrics.totalSignoffs}
            meta={t("audit.presets.metrics.manualTotalSignoffsMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualTotalSeals" as MessageKey)}
            value={loading || manualPresetLoading ? "..." : manualPackageAuditMetrics.totalSeals}
            meta={t("audit.presets.metrics.manualTotalSealsMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualUniqueScopes" as MessageKey)}
            value={loading || manualPresetLoading ? "..." : manualPackageAuditMetrics.uniqueScopeCount}
            meta={t("audit.presets.metrics.manualUniqueScopesMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualLatestHash" as MessageKey)}
            value={loading || manualPresetLoading ? "..." : summarizeDossierHash(manualPackageAuditMetrics.latestHash)}
            meta={t("audit.presets.metrics.manualLatestHashMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualLatestStage" as MessageKey)}
            value={loading || manualPresetLoading ? "..." : manualPackageAuditMetrics.latestStageLabel}
            meta={t("audit.presets.metrics.manualLatestStageMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualLatestFilename" as MessageKey)}
            value={loading || manualPresetLoading ? "..." : manualPackageAuditMetrics.latestFilename || t("audit.notAvailable")}
            meta={t("audit.presets.metrics.manualLatestFilenameMeta" as MessageKey)}
          />
        </MetricGrid>
      ) : null}
      {manualPackageMfaPresetActive ? (
        <MetricGrid>
          <MetricCard
            label={t("audit.presets.metrics.manualMfaTotalEvents" as MessageKey)}
            value={loading ? "..." : manualPackageMfaMetrics.totalEvents}
            meta={t("audit.presets.metrics.manualMfaTotalEventsMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualMfaUniqueRequests" as MessageKey)}
            value={loading ? "..." : manualPackageMfaMetrics.uniqueRequestCount}
            meta={t("audit.presets.metrics.manualMfaUniqueRequestsMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualMfaUniqueSeals" as MessageKey)}
            value={loading ? "..." : manualPackageMfaMetrics.uniqueSealCount}
            meta={t("audit.presets.metrics.manualMfaUniqueSealsMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualMfa2faRequired" as MessageKey)}
            value={loading ? "..." : manualPackageMfaMetrics.total2faRequired}
            meta={t("audit.presets.metrics.manualMfa2faRequiredMeta" as MessageKey)}
          />
          <MetricCard
            label={t("audit.presets.metrics.manualMfaProviderNotHomologated" as MessageKey)}
            value={loading ? "..." : manualPackageMfaMetrics.totalProviderNotHomologated}
            meta={t("audit.presets.metrics.manualMfaProviderNotHomologatedMeta" as MessageKey)}
          />
        </MetricGrid>
      ) : null}
      {manualPackageMfaPresetActive ? (
        <Panel
          title={t("audit.presets.manualMfaTypeSummaryTitle" as MessageKey)}
          description={t("audit.presets.manualMfaTypeSummaryDescription" as MessageKey)}
        >
          <div className="otc-stack" data-testid="audit-manual-mfa-type-summary">
            {manualPackageMfaTypeSummary.map((item) => (
              <div key={item.key} className="otc-message">
                <div className="otc-controls otc-controls--spaced" data-testid="audit-manual-mfa-type-row">
                  <strong>{item.label}</strong>
                  <span>{item.count}</span>
                </div>
                <div className="otc-muted">
                  {t("audit.presets.manualMfaTypeShare" as MessageKey)} {item.shareLabel}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      ) : null}
      {manualPackageMfaPresetActive ? (
        <Panel
          title={t("audit.presets.manualMfaRoleSummaryTitle" as MessageKey)}
          description={t("audit.presets.manualMfaRoleSummaryDescription" as MessageKey)}
        >
          <div className="otc-stack" data-testid="audit-manual-mfa-role-summary">
            <div className="otc-message">
              <strong>{t("audit.presets.manualMfaAuthRoleBreakdown" as MessageKey)}</strong>
              <div className="otc-stack">
                {manualPackageMfaRoleSummary.authRoles.length ? (
                  manualPackageMfaRoleSummary.authRoles.map((item) => (
                    <div
                      key={item.key}
                      className="otc-controls otc-controls--spaced"
                      data-testid="audit-manual-mfa-auth-role-row"
                    >
                      <span>{item.label}</span>
                      <strong>{item.count}</strong>
                    </div>
                  ))
                ) : (
                  <div>{t("audit.events.empty")}</div>
                )}
              </div>
            </div>
            <div className="otc-message">
              <strong>{t("audit.presets.manualMfaSignerRoleBreakdown" as MessageKey)}</strong>
              <div className="otc-stack">
                {manualPackageMfaRoleSummary.signerRoles.length ? (
                  manualPackageMfaRoleSummary.signerRoles.map((item) => (
                    <div
                      key={item.key}
                      className="otc-controls otc-controls--spaced"
                      data-testid="audit-manual-mfa-signer-role-row"
                    >
                      <span>{item.label}</span>
                      <strong>{item.count}</strong>
                    </div>
                  ))
                ) : (
                  <div>{t("audit.events.empty")}</div>
                )}
              </div>
            </div>
          </div>
        </Panel>
      ) : null}
      {manualPackageMfaPresetActive ? (
        <Panel
          title={t("audit.presets.manualMfaFamiliesTitle" as MessageKey)}
          description={t("audit.presets.manualMfaFamiliesDescription" as MessageKey)}
        >
          {manualPackageMfaFamilies.length ? (
            <div className="otc-stack">
              {manualPackageMfaFamilies.map((family) => (
                <div
                  key={family.key}
                  data-testid="audit-manual-mfa-family-row"
                  className={`otc-message${family.isActive ? " otc-audit-row--selected" : ""}`}
                >
                  <div className="otc-stack">
                    <div className="otc-controls otc-controls--spaced">
                      <strong>
                        {t("audit.presets.familyRequestId" as MessageKey)}{" "}
                        <span className="otc-mono">{family.requestId || t("audit.notAvailable")}</span>
                      </strong>
                      <div className="otc-controls">
                        <span data-testid="audit-manual-mfa-family-dominant-pill">
                          <Pill tone={family.dominantTypeTone}>{family.dominantTypeLabel}</Pill>
                        </span>
                        <span className="otc-muted">
                          {t("audit.presets.familyLatestSeenAt" as MessageKey)} {formatAuditTimestampValue(family.latestCreatedAt)}
                        </span>
                      </div>
                    </div>
                    <div className="otc-controls otc-controls--spaced">
                      <span>
                        {t("audit.presets.familySealId" as MessageKey)}{" "}
                        <span className="otc-mono">{family.sealId || t("audit.notAvailable")}</span>
                      </span>
                      <span>
                        {t("audit.presets.familyLatestAuthRole" as MessageKey)} {family.latestAuthRole || t("audit.notAvailable")}
                      </span>
                      <span>
                        {t("audit.presets.familyLatestSignerRole" as MessageKey)} {family.latestSignerRoleLabel || t("audit.notAvailable")}
                      </span>
                      <span>
                        {t("audit.presets.familyLatestMfaMode" as MessageKey)} {family.latestMfaMode || t("audit.notAvailable")}
                      </span>
                    </div>
                    <div className="otc-controls otc-controls--spaced">
                      <span>{t("audit.presets.familyTotalEvents" as MessageKey)} {family.totalEvents}</span>
                      <span>{t("audit.presets.family2faRequired" as MessageKey)} {family.total2faRequired}</span>
                      <span>{t("audit.presets.familyProviderNotHomologated" as MessageKey)} {family.totalProviderNotHomologated}</span>
                      <span>{t("audit.presets.familyLatestDetail" as MessageKey)} <span className="otc-mono">{family.latestDetail || t("audit.notAvailable")}</span></span>
                    </div>
                    <div className="otc-controls">
                      <a className="otc-link-button" href={family.href} data-testid="audit-manual-mfa-family-open">
                        {family.isActive ? t("audit.presets.familyCurrentScope" as MessageKey) : t("audit.presets.familyOpen" as MessageKey)}
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="otc-message">{t("audit.events.empty")}</div>
          )}
        </Panel>
      ) : null}

      <section className="otc-grid otc-audit-layout">
        <Panel title={t("audit.events.title")} description={t("audit.events.description")}>
          <div className="otc-controls otc-audit-pagination">
            <button
              type="button"
              className="otc-button otc-button--ghost"
              data-testid="audit-prev-page-btn"
              onClick={() => void onPreviousPage()}
              disabled={loading || currentPage <= 1}
            >
              {t("audit.pagination.previous")}
            </button>
            <button
              type="button"
              className="otc-button otc-button--ghost"
              data-testid="audit-next-page-btn"
              onClick={() => void onNextPage()}
              disabled={loading || !hasMore}
            >
              {t("audit.pagination.next")}
            </button>
            <span data-testid="audit-page-summary" className="otc-muted">
              {t("audit.pagination.summary", { page: currentPage, totalPages, total })}
            </span>
          </div>
          {logs.length ? (
            <div className="otc-stack">
              {logs.map((entry) => {
                const isSelected = entry.id === selectedLog?.id;
                return (
                  <button
                    key={entry.id}
                    type="button"
                    data-testid="audit-row"
                    onClick={() => setSelectedLog(entry)}
                    className={`otc-button otc-button--ghost otc-button--stack-start otc-audit-row${isSelected ? " otc-audit-row--selected" : ""}`}
                  >
                    <div className="otc-audit-row__header">
                      <strong>{formatAuditActionValue(entry.action)}</strong>
                      <span className="otc-muted" data-testid={`audit-row-timestamp-${entry.id}`}>
                        {formatAuditTimestampValue(entry.created_at)}
                      </span>
                    </div>
                    <div className="otc-audit-row__resource">{formatAuditResourceTypeValue(entry.resource_type)}{entry.resource_id ? ` • ${entry.resource_id}` : ""}</div>
                    <div className="otc-muted otc-audit-row__meta">request_id: {entry.request_id ?? t("audit.notAvailable")}</div>
                    <div className="otc-muted otc-audit-row__meta otc-audit-row__meta--tight">report_id: {entry.report_id ?? t("audit.notAvailable")}</div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div data-testid="audit-empty" className="otc-message">{t("audit.events.empty")}</div>
          )}
        </Panel>

        <Panel title={t("audit.details.title")} description={t("audit.details.description")}>
          {selectedLog ? (
            <div data-testid="audit-details-panel" className="otc-stack">
              <div><strong>{t("audit.details.action")}:</strong> {formatAuditActionValue(selectedLog.action)}</div>
              <div><strong>{t("audit.details.resourceType")}:</strong> {formatAuditResourceTypeValue(selectedLog.resource_type)}</div>
              <div><strong>{t("audit.details.resourceId")}:</strong> {selectedLog.resource_id ?? t("audit.notAvailable")}</div>
              <div><strong>{t("audit.details.requestId")}:</strong> {selectedLog.request_id ?? t("audit.notAvailable")}</div>
              <div><strong>{t("audit.details.reportId")}:</strong> {selectedLog.report_id ?? t("audit.notAvailable")}</div>
              <div><strong>{t("audit.details.fileSha" as MessageKey)}:</strong> {selectedLog.file_hash_sha256 ?? t("audit.notAvailable")}</div>
              <div><strong>{t("audit.details.caseId")}:</strong> {selectedContext?.caseId || t("audit.notAvailable")}</div>
              <div>
                <strong>{t("audit.details.addressChain")}:</strong>{" "}
                {selectedContext?.address ? `${selectedContext.address} • ${selectedContext.chain}` : t("audit.notAvailable")}
              </div>
              <div><strong>{t("audit.details.counterpartyId")}:</strong> {selectedContext?.counterpartyId || t("audit.notAvailable")}</div>
              <div><strong>{t("audit.details.rosId")}:</strong> {selectedContextForLinks?.rosId || t("audit.notAvailable")}</div>
              {selectedHashContext ? renderHashContext(selectedHashContext) : null}
              {selectedDossierContext ? renderDossierDetailContext(selectedDossierContext) : null}
              {selectedManualPackageContext ? renderManualPackageDetailContext(selectedManualPackageContext) : null}
              <div className="otc-audit-pill">
                <Pill>{formatAuditResourceTypeValue(selectedLog.resource_type)}</Pill>
              </div>
              {selectedContext ? (
                <div className="otc-controls otc-controls--spaced">
                  {linkedRosLoading ? (
                    <button type="button" className="otc-button otc-button--ghost" disabled>
                      {t("audit.details.loadingRosCoaf" as MessageKey)}
                    </button>
                  ) : null}
                  {!linkedRosLoading && selectedContextForLinks?.rosId ? (
                    <button
                      type="button"
                      className="otc-button otc-button--ghost"
                      onClick={() => void onExportRosCoafRegulatoryDossier(selectedContextForLinks.rosId!)}
                      disabled={exportingRosCoafDossier}
                      data-testid="audit-export-ros-dossier"
                    >
                      {exportingRosCoafDossier
                        ? t("audit.details.exportRosDossierLoading" as MessageKey)
                        : t("audit.details.exportRosDossier" as MessageKey)}
                    </button>
                  ) : null}
                  {selectedContextLinks.map((link: OperationalContextLink & { label: string }) => (
                    <a key={`audit-${link.testIdSuffix}`} className="otc-button otc-button--ghost" href={link.href}>
                      {link.label}
                    </a>
                  ))}
                </div>
              ) : null}
              <CodeBlock>
                <span data-testid="audit-metadata">{JSON.stringify(selectedLog.metadata, null, 2)}</span>
              </CodeBlock>
            </div>
          ) : (
            <div className="otc-message">{t("audit.details.empty")}</div>
          )}
        </Panel>
      </section>
    </AppShell>
  );
}

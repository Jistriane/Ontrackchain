import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";
import { authenticateReportRequest, jsonResponse } from "../_shared";
import { canExportSensitiveEvidence } from "../../../../lib/authz";
import {
  buildReportFormalDossierFilename,
  deriveReportFormalDossierSummary,
  type ReportFormalDossierSource
} from "../../../../lib/report-formal-dossier";

type ReportFormalDossierRequest = {
  report: ReportFormalDossierSource;
  has_download_audit: boolean;
  workspace_summary?: {
    work_item_id?: string | null;
    case_id: string;
    report_type?: string | null;
    owner?: string | null;
    priority?: string | null;
    deadline?: string | null;
    status?: string | null;
    source?: string | null;
    note?: string | null;
    last_action_at?: string | null;
  } | null;
};

export async function POST(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const payload = (await request.json().catch(() => null)) as ReportFormalDossierRequest | null;
    if (!payload?.report?.report_id || !payload.report.case_id) {
      return jsonResponse(JSON.stringify({ error: "invalid_formal_dossier_payload" }), 422);
    }

    const dossier = deriveReportFormalDossierSummary(payload.report, payload.has_download_audit);
    const body = {
      package_type: dossier.packageType,
      classification: dossier.classification,
      access_policy: dossier.accessPolicy,
      signoff_mode: dossier.signoffMode,
      anchoring_status: dossier.anchoringStatus,
      download_state: dossier.downloadState,
      custody_state: dossier.custodyState,
      distribution_scope: dossier.distributionScope,
      retention_class: dossier.retentionClass,
      generated_at: new Date().toISOString(),
      mode: "standalone_showcase",
      report: payload.report,
      workspace_summary: payload.workspace_summary ?? null,
      evidence_bundle: {
        summary: "Generated locally in standalone showcase mode.",
        events: [
          { at: "2026-07-15T22:10:00Z", action: "report_generated", actor: "showcase-user" },
          { at: "2026-07-15T22:20:00Z", action: "dossier_packaged", actor: "showcase-user" }
        ]
      }
    };

    return new Response(JSON.stringify(body, null, 2), {
      status: 200,
      headers: {
        "content-type": "application/json",
        "content-disposition": `attachment; filename="${buildReportFormalDossierFilename(payload.report.report_id)}"`
      }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }
  if (!canExportSensitiveEvidence(auth.role)) {
    return jsonResponse(JSON.stringify({ detail: "report_formal_dossier_role_required" }), 403);
  }

  const payload = (await request.json().catch(() => null)) as ReportFormalDossierRequest | null;
  if (!payload?.report?.report_id || !payload.report.case_id) {
    return jsonResponse(JSON.stringify({ error: "invalid_formal_dossier_payload" }), 422);
  }

  const runtimeEnv = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env;
  const baseUrl = runtimeEnv?.INTERNAL_API_BASE_URL ?? runtimeEnv?.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const evidenceRes = await fetch(`${baseUrl}/api/v1/audit/evidence-export`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${auth.token}`,
      "X-Request-Id": requestId,
      "X-Role": auth.role,
      ...(auth.authMethod ? { "X-Auth-Method": auth.authMethod } : {}),
      ...(auth.orgId ? { "X-Org-Id": auth.orgId } : {}),
      ...(auth.userId ? { "X-User-Id": auth.userId } : {}),
      ...(auth.linkedUserId ? { "X-Linked-User-Id": auth.linkedUserId } : {}),
      ...(auth.mfaMode ? { "X-MFA-Mode": auth.mfaMode } : {}),
      ...(auth.mfaProviderHomologated ? { "X-MFA-Provider-Homologated": auth.mfaProviderHomologated } : {}),
      ...(auth.twoFactor ? { "X-2FA": auth.twoFactor } : {}),
      "content-type": "application/json"
    },
    body: JSON.stringify({
      format: "json",
      request_id: payload.report.case_id.trim() || null,
      action: null,
      resource_type: "case",
      report_id: payload.report.report_id.trim() || null,
      resource_id: payload.report.case_id.trim() || null,
      limit: 200,
      include_audit_logs: true,
      include_credit_ledger: true,
      include_reports: true
    }),
    cache: "no-store"
  });

  if (!evidenceRes.ok) {
    return new Response(await evidenceRes.arrayBuffer(), {
      status: evidenceRes.status,
      headers: { "content-type": evidenceRes.headers.get("content-type") ?? "application/json" }
    });
  }

  const dossier = deriveReportFormalDossierSummary(payload.report, payload.has_download_audit);
  const evidenceBundle = (await evidenceRes.json().catch(() => null)) as Record<string, unknown> | null;
  const body = {
    package_type: dossier.packageType,
    classification: dossier.classification,
    access_policy: dossier.accessPolicy,
    signoff_mode: dossier.signoffMode,
    anchoring_status: dossier.anchoringStatus,
    download_state: dossier.downloadState,
    custody_state: dossier.custodyState,
    distribution_scope: dossier.distributionScope,
    retention_class: dossier.retentionClass,
    generated_at: new Date().toISOString(),
    report: payload.report,
    workspace_summary: payload.workspace_summary ?? null,
    evidence_bundle: evidenceBundle
  };

  return new Response(JSON.stringify(body, null, 2), {
    status: 200,
    headers: {
      "content-type": "application/json",
      "content-disposition": `attachment; filename="${buildReportFormalDossierFilename(payload.report.report_id)}"`
    }
  });
}

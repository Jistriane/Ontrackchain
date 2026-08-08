import { cookies } from "next/headers";

import { canDownloadLegalReport, canDownloadReportArtifact } from "../../../../lib/authz";
import { authenticateReportRequest, proxyReportBinaryRequest } from "../_shared";

export async function GET(request: Request) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const url = new URL(request.url);
  const reportId = url.searchParams.get("report_id");
  if (!reportId) {
    return new Response("missing_report_id", { status: 422 });
  }

  const reportType = url.searchParams.get("report_type");
  const twofa = cookies().get("otc_2fa")?.value;

  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  let clientSideBlockedReason: string | null = null;
  if (reportType === "legal_report") {
    if (!canDownloadLegalReport({
      role: auth.role,
      authMethod: auth.authMethod,
      mfaMode: auth.mfaMode,
      mfaProviderHomologated: auth.mfaProviderHomologated,
      twoFactor: twofa ?? auth.twoFactor
    })) {
      if (auth.role !== "ADMIN" && auth.role !== "OTK_ADMIN") {
        clientSideBlockedReason = "legal_report_requires_admin_role";
      } else if (twofa === "managed_externally") {
        clientSideBlockedReason = "mfa_not_homologated_for_oidc";
      } else if (twofa !== "ok" && twofa !== "managed_externally_homologated") {
        clientSideBlockedReason = "2fa_required";
      } else {
        clientSideBlockedReason = "legal_report_requires_admin_role";
      }
    }
  } else if (!canDownloadReportArtifact(auth.role)) {
    clientSideBlockedReason = "report_download_role_required";
  }

  const query = url.searchParams;
  query.delete("report_id");
  if (clientSideBlockedReason) {
    query.set("_client_rbac_reason", clientSideBlockedReason);
  }
  const queryString = query.toString();
  return proxyReportBinaryRequest(auth, {
    method: "GET",
    path: `/api/v1/reports/${encodeURIComponent(reportId)}/download?${queryString}`,
    requestId
  });
}

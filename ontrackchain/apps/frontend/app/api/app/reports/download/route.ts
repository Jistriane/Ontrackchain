import { cookies } from "next/headers";

import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";
import { canDownloadReportArtifact } from "../../../../lib/authz";
import { authenticateReportRequest, proxyReportBinaryRequest } from "../_shared";

export async function GET(request: Request) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const url = new URL(request.url);
  const reportId = url.searchParams.get("report_id");
  if (!reportId) {
    return new Response("missing_report_id", { status: 422 });
  }

  if (isFrontendStandaloneShowcaseMode()) {
    const reportType = url.searchParams.get("report_type") ?? "technical_basic";
    return new Response(
      `OnTrackChain Standalone Showcase\nreport_id=${reportId}\nreport_type=${reportType}\nmode=standalone_showcase\n`,
      {
        status: 200,
        headers: {
          "content-type": "application/pdf",
          "content-disposition": `attachment; filename="${reportId}.pdf"`
        }
      }
    );
  }

  const reportType = url.searchParams.get("report_type");
  const twofa = cookies().get("otc_2fa")?.value;
  if (reportType === "legal_report") {
    if (twofa === "managed_externally") {
      return new Response(JSON.stringify({ detail: "mfa_not_homologated_for_oidc" }), {
        status: 403,
        headers: { "content-type": "application/json" }
      });
    }
    if (twofa !== "ok" && twofa !== "managed_externally_homologated") {
      return new Response(JSON.stringify({ detail: "2fa_required" }), {
        status: 403,
        headers: { "content-type": "application/json" }
      });
    }
  }

  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }
  if (reportType !== "legal_report" && !canDownloadReportArtifact(auth.role)) {
    return new Response(JSON.stringify({ detail: "report_download_role_required" }), {
      status: 403,
      headers: { "content-type": "application/json" }
    });
  }

  const query = url.searchParams;
  query.delete("report_id");
  const queryString = query.toString();
  return proxyReportBinaryRequest(auth, {
    method: "GET",
    path: `/api/v1/reports/${encodeURIComponent(reportId)}/download?${queryString}`,
    requestId
  });
}

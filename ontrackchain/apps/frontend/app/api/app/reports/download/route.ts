import { cookies } from "next/headers";

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

  const query = url.searchParams;
  query.delete("report_id");
  const queryString = query.toString();
  return proxyReportBinaryRequest(auth, {
    method: "GET",
    path: `/api/v1/reports/${encodeURIComponent(reportId)}/download?${queryString}`,
    requestId
  });
}

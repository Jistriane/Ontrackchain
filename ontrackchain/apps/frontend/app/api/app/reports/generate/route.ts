import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";
import { buildStandaloneShowcaseGeneratedReport } from "../../../../lib/standalone-showcase";
import { authenticateReportRequest, proxyReportJsonRequest } from "../_shared";

export async function POST(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const payload = (await request.json().catch(() => null)) as { case_id?: string; report_type?: string } | null;
    if (!payload?.case_id?.trim() || !payload?.report_type?.trim()) {
      return new Response(JSON.stringify({ error: "invalid_generate_report_payload" }), {
        status: 422,
        headers: { "content-type": "application/json" }
      });
    }
    return new Response(
      JSON.stringify(
        buildStandaloneShowcaseGeneratedReport({
          caseId: payload.case_id.trim(),
          reportType: payload.report_type.trim()
        })
      ),
      { status: 200, headers: { "content-type": "application/json" } }
    );
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  return proxyReportJsonRequest(auth, {
    method: "POST",
    path: "/api/v1/reports/generate",
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
}

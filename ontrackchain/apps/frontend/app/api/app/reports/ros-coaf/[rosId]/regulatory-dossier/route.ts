import { isFrontendStandaloneShowcaseMode } from "../../../../../../lib/auth-runtime";
import { buildStandaloneShowcaseRosCoafRegulatoryDossier } from "../../../../../../lib/standalone-showcase";
import { authenticateReportRequest, proxyReportBinaryRequest } from "../../../_shared";

export async function GET(request: Request, context: { params: Promise<{ rosId: string }> }) {
  if (isFrontendStandaloneShowcaseMode()) {
    const { rosId } = await context.params;
    const dossier = buildStandaloneShowcaseRosCoafRegulatoryDossier(rosId);
    if (!dossier) {
      return new Response(JSON.stringify({ error: "ros_not_found" }), {
        status: 404,
        headers: { "content-type": "application/json" }
      });
    }
    return new Response(JSON.stringify(dossier.content, null, 2), {
      status: 200,
      headers: {
        "content-type": "application/json",
        "content-disposition": `attachment; filename="${dossier.filename}"`,
        "x-ontrack-dossier-sha256": dossier.dossierSha256
      }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const { rosId } = await context.params;
  const url = new URL(request.url);
  const limit = url.searchParams.get("limit");
  const query = new URLSearchParams();
  if (limit) {
    query.set("limit", limit);
  }

  const suffix = query.toString();
  return proxyReportBinaryRequest(auth, {
    method: "GET",
    path: `/api/v1/reports/ros-coaf/${encodeURIComponent(rosId)}/regulatory-dossier${suffix ? `?${suffix}` : ""}`,
    requestId
  });
}

import { cookies } from "next/headers";

export async function GET(request: Request) {
  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response("not_authenticated", { status: 401 });
  }

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
    if (twofa !== "ok") {
      return new Response(JSON.stringify({ detail: "2fa_required" }), {
        status: 403,
        headers: { "content-type": "application/json" }
      });
    }
  }

  const query = url.searchParams;
  query.delete("report_id");
  const queryString = query.toString();

  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const target = `${baseUrl}/api/v1/reports/${reportId}/download?${queryString}`;
  const res = await fetch(target, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-2FA": twofa ?? "", "X-Request-Id": requestId },
    cache: "no-store"
  });

  const buf = await res.arrayBuffer();
  const headers = new Headers();
  const contentType = res.headers.get("content-type");
  const contentDisposition = res.headers.get("content-disposition");
  if (contentType) headers.set("content-type", contentType);
  if (contentDisposition) headers.set("content-disposition", contentDisposition);
  return new Response(buf, { status: res.status, headers });
}

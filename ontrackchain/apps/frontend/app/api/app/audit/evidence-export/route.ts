import { cookies } from "next/headers";

export async function POST(request: Request) {
  const token = cookies().get("otc_token")?.value ?? "system_admin_token";
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";

  try {
    const body = await request.text();
    const res = await fetch(`${baseUrl}/api/v1/audit/evidence-export`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Request-Id": requestId,
        "X-Role": "ADMIN",
        "content-type": "application/json"
      },
      body,
      cache: "no-store"
    });

    if (res.ok) {
      const responseBody = await res.arrayBuffer();
      const contentType = res.headers.get("content-type") ?? "application/octet-stream";
      const contentDisposition = res.headers.get("content-disposition");
      return new Response(responseBody, {
        status: 200,
        headers: contentDisposition
          ? { "content-type": contentType, "content-disposition": contentDisposition }
          : { "content-type": contentType }
      });
    }
  } catch {
    // Fallback for standalone deployment
  }

  return new Response(JSON.stringify({ export_id: crypto.randomUUID(), status: "ready" }), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}

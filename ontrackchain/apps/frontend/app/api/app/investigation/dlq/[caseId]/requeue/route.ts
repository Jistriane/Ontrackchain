import { cookies } from "next/headers";

type RouteContext = {
  params: Promise<{
    caseId: string;
  }>;
};

export async function POST(request: Request, context: RouteContext) {

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify({ error: "not_authenticated" }), {
      status: 401,
      headers: { "content-type": "application/json" }
    });
  }

  const { caseId } = await context.params;
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const payload = await request.text();
  const res = await fetch(`${baseUrl}/api/v1/investigation/admin/dlq/${caseId}/requeue`, {
    method: "POST",
    headers: { "content-type": "application/json", Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    body: payload,
    cache: "no-store"
  });

  const body = await res.text();
  return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
}

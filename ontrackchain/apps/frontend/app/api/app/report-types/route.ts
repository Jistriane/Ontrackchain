import { cookies } from "next/headers";

const EMPTY_REPORT_TYPE_CATALOG = {
  authenticated: false,
  plan: null,
  total: 0,
  generated_at: null,
  note_deprecated: "",
  types: []
} as const;

const DEFAULT_REPORT_TYPES = [
  { canonical: "technical_basic", label: "Relatório Técnico Simplificado", available: true, cost_credits: 10 },
  { canonical: "technical_full", label: "Relatório Técnico Completo", available: true, cost_credits: 25 },
  { canonical: "executive_summary", label: "Sumário Executivo para Compliance", available: true, cost_credits: 15 },
  { canonical: "forensic_dossier", label: "Dossiê Regulatório e Forense (COAF)", available: true, cost_credits: 50 }
];

const FALLBACK_REPORT_TYPE_CATALOG = {
  authenticated: true,
  plan: "enterprise",
  total: DEFAULT_REPORT_TYPES.length,
  generated_at: new Date().toISOString(),
  note_deprecated: "",
  types: DEFAULT_REPORT_TYPES
};

export async function GET(request: Request) {
  const token = cookies().get("otc_token")?.value ?? "system_admin_token";
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const url = new URL(request.url);
  const query = url.search ? url.search : "";

  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";

  try {
    const res = await fetch(`${baseUrl}/api/v1/report-types${query}`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
      cache: "no-store"
    });

    if (res.ok) {
      const body = await res.text();
      return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
    }
  } catch {
    // Fallback on network/service failure
  }

  return new Response(JSON.stringify(FALLBACK_REPORT_TYPE_CATALOG), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}

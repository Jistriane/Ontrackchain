function jsonResponse(body: string, status: number) {
  return new Response(body, {
    status,
    headers: {
      "content-type": "application/json",
      "cache-control": "public, max-age=300"
    }
  });
}

const DEFAULT_SUPPORTED_CHAINS = {
  chains: [
    {
      id: "ethereum",
      name: "Ethereum",
      symbol: "ETH",
      is_evm: true,
      block_time_seconds: 12,
      status: "active",
      capabilities: ["compliance_screening", "tracing", "monitoring", "reports"]
    },
    {
      id: "polygon",
      name: "Polygon",
      symbol: "POL",
      is_evm: true,
      block_time_seconds: 2,
      status: "active",
      capabilities: ["compliance_screening", "tracing", "monitoring"]
    },
    {
      id: "bsc",
      name: "BNB Smart Chain",
      symbol: "BNB",
      is_evm: true,
      block_time_seconds: 3,
      status: "active",
      capabilities: ["compliance_screening", "tracing"]
    },
    {
      id: "arbitrum",
      name: "Arbitrum One",
      symbol: "ETH",
      is_evm: true,
      block_time_seconds: 1,
      status: "active",
      capabilities: ["compliance_screening", "tracing", "monitoring"]
    },
    {
      id: "base",
      name: "Base",
      symbol: "ETH",
      is_evm: true,
      block_time_seconds: 2,
      status: "active",
      capabilities: ["compliance_screening", "tracing", "monitoring"]
    },
    {
      id: "bitcoin",
      name: "Bitcoin",
      symbol: "BTC",
      is_evm: false,
      block_time_seconds: 600,
      status: "active",
      capabilities: ["compliance_screening", "tracing", "reports"]
    }
  ],
  total_chains: 6,
  active_chains: 6,
  updated_at: new Date().toISOString()
};

export async function GET(request: Request) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";

  try {
    const res = await fetch(`${baseUrl}/public/chains/supported`, {
      method: "GET",
      headers: { "X-Request-Id": requestId },
      cache: "no-store"
    });

    if (res.ok) {
      const responseBody = await res.text();
      return jsonResponse(responseBody, 200);
    }
  } catch (err) {
    // Fallback gracioso para a lista seeded default se a API interna estiver indisponível
  }

  return jsonResponse(JSON.stringify(DEFAULT_SUPPORTED_CHAINS), 200);
}

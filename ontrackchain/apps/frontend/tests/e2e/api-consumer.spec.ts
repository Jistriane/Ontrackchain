import { test, expect } from "@playwright/test";

const API_KEY = process.env.ONTRACKCHAIN_API_KEY || "otc_live_demo_key";

test("public API retorna score sem autenticação", async ({ request }) => {
  const res = await request.get("/public/wallet/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045?chain=ethereum");
  expect(res.status()).toBe(200);
  const body = (await res.json()) as Record<string, unknown>;
  expect(body).toHaveProperty("risk_score");
});

test("API key funciona para investigação", async ({ request }) => {
  const estimate = await request.post("/api/v1/investigation/estimate", {
    headers: { "X-API-Key": API_KEY },
    data: {
      address: "0x8888888888888888888888888888888888888888",
      chains: ["ethereum"],
      depth: 3,
      report_type: "technical_basic",
      addons: []
    }
  });
  expect(estimate.status()).toBe(200);
  const estimateBody = (await estimate.json()) as { quote_id: string };
  expect(estimateBody.quote_id).toBeTruthy();

  const start = await request.post("/api/v1/investigation/start", {
    headers: { "X-API-Key": API_KEY },
    data: { quote_id: estimateBody.quote_id, confirmed: true }
  });
  expect([200, 202]).toContain(start.status());
  const startBody = (await start.json()) as Record<string, unknown>;
  expect(startBody).toHaveProperty("case_id");
});

test("API key funciona para monitoring e compliance", async ({ request }) => {
  const monitoringCatalog = await request.get("/api/v1/monitoring/operations", {
    headers: { "X-API-Key": API_KEY }
  });
  expect(monitoringCatalog.status()).toBe(200);

  const complianceCatalog = await request.get("/api/v1/compliance/operations", {
    headers: { "X-API-Key": API_KEY }
  });
  expect(complianceCatalog.status()).toBe(200);
});


/**
 * Q3-04 Load Testing - Sprint 22 - k6 v0.50+
 * ============================================================
 * 04 - Smoke Healthz Multi-Service (public-api / compliance-api / investigation-api)
 * Rotas:
 *    GET /healthz  → cada um dos 3 serviços
 *    GET /readyz   → readiness probe
 *
 * Smoke test leve (10 VUs, 10s) - sempre rodar antes de promoção para staging.
 * Thresholds MUITO rigorosos (SLA 99.9% de disponibilidade endpoints fundacionais):
 *   - p95 < 120ms
 *   - 100% status 200
 *   - 0 falhas
 */

import http from "k6/http";
import { check, group } from "k6";

const URLS = {
  public_api:        __ENV.K6_PUBLIC_URL        || "http://127.0.0.1:8001",
  compliance_api:    __ENV.K6_COMPLIANCE_URL    || "http://127.0.0.1:8002",
  investigation_api: __ENV.K6_INVESTIGATION_URL || "http://127.0.0.1:8003",
};

export const options = {
  vus: 10,
  duration: "10s",
  thresholds: {
    http_req_duration:           ["p(95)<120", "p(99)<250"],
    http_req_failed:             ["rate<0.001"],  // 0.1% máximo
    checks:                      ["rate>0.999"],
    "group_duration{group:::public-api}":        ["p(95)<120"],
    "group_duration{group:::compliance-api}":    ["p(95)<120"],
    "group_duration{group:::investigation-api}": ["p(95)<120"],
  },
  summaryTrendStats: ["avg", "min", "med", "max", "p(95)", "p(99)"],
};

function probeService(name, base) {
  group(name, function () {
    const hz = http.get(`${base}/healthz`, { tags: { probe: "liveness", phase: "Q3-04" }, timeout: "1s" });
    check(hz, {
      [`${name} /healthz status 200`]:       (r) => r.status === 200,
      [`${name} /healthz tem status=UP`]:    (r) => {
        try {
          const s = r.json("status") || r.json("data.status");
          return String(s).toUpperCase() === "UP";
        } catch (_) { return /\bUP\b/i.test(r.body || ""); }
      },
    });

    const rz = http.get(`${base}/readyz`, { tags: { probe: "readiness", phase: "Q3-04" }, timeout: "1s" });
    check(rz, {
      [`${name} /readyz status 200/204`]: (r) => r.status === 200 || r.status === 204,
    });
  });
}

export default function () {
  probeService("public-api",        URLS.public_api);
  probeService("compliance-api",    URLS.compliance_api);
  probeService("investigation-api", URLS.investigation_api);
}

/**
 * Q3-04 Load Testing - Sprint 22 - k6 v0.50+
 * ============================================================
 * 03 - Case Management Create Case (investigation-api)
 * Rota:  POST /api/v1/cases
 *
 * Executar:
 *   k6 run tests/k6/03-case-management-create-case.js \
 *       -e K6_BASE_URL=https://investigation.ontrackchain.com.br
 *
 * Casos de investigação são escrita pesada (várias tabelas relacionais,
 * auditoria, worker events → esperado p95 maior que health endpoint).
 * Thresholds:
 *   - p95 < 900ms
 *   - p99 < 2.5s
 *   - 98% de sucesso
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Trend } from "k6/metrics";

const BASE_URL = __ENV.K6_BASE_URL || "http://127.0.0.1:8003";

export const options = {
  stages: [
    { duration: "10s", target: 5  },
    { duration: "25s", target: 25 },
    { duration: "8s",  target: 0  },
  ],
  thresholds: {
    http_req_duration: ["p(95)<900", "p(99)<2500"],
    http_req_failed:   ["rate<0.02"],
    checks:            ["rate>0.98"],
  },
  summaryTrendStats: ["avg", "min", "med", "max", "p(95)", "p(99)"],
};

const caseCreated = new Trend("case_created_ms", true);

const JURISDICTIONS = ["BR", "US", "FI", "EU", "SG", "AE", "CH"];
const CASE_TYPES = ["aml_suspected", "sanction_breach", "fraud_carbon_credit",
                    "pep_conflict", "market_manipulation", "cyber_incident_response"];
const SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

function randomOf(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

export default function () {
  const id = `k6-${__VU}-${Date.now()}`;
  const payload = {
    organization_id: "00000000-0000-0000-0000-000000000300",
    case_number: `CASO-LOAD-${id}`,
    title: `Caso automático Load Testing Q3-04 ${id}`,
    summary: "Gerado automaticamente por k6 load testing Sprint 22 Q3-04. Deve ser ignorado em produção.",
    case_type: randomOf(CASE_TYPES),
    jurisdiction: randomOf(JURISDICTIONS),
    severity: randomOf(SEVERITIES),
    assigned_team_role: "OTK_INVESTIGATOR_ANALYST",
    reporter_user_email: "k6-loadbot@ontrackchain.com.br",
    primary_counterparty_id: `cp_loadtest_${__VU}`,
    labels: ["load-testing", "sprint-22", "q3-04", `vu-${__VU}`],
    sla_deadline_days: randomOf([3, 7, 15, 30, 45]),
    related_wallets: [
      { wallet_address: `0xDEADBEEFCAFE${__VU.toString(16).padStart(8,"0")}`, blockchain: "ethereum" },
    ],
  };

  const params = {
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": id,
      Authorization: __ENV.K6_CASES_BEARER || "Bearer k6.local.demo",
    },
    tags: { route: "create_case_v1", phase: "Q3-04" },
    timeout: "4s",
  };

  const t0 = Date.now();
  const res = http.post(`${BASE_URL}/api/v1/cases`, JSON.stringify(payload), params);
  caseCreated.add(Date.now() - t0);

  check(res, {
    "status 201": (r) => r.status === 201,
    "case_id uuid": (r) => /^[0-9a-f-]{36}$/.test(String(r.json("case_id") || "")),
    "status initial": (r) => ["OPEN", "NEW", "TRIAGE"].includes(String(r.json("status"))),
  });

  sleep(0.12);
}

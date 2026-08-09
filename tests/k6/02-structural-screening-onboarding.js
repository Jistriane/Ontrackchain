/**
 * Q3-04 Load Testing - Sprint 22 - k6 v0.50+
 * ============================================================
 * 02 - Structural Screening Onboarding (compliance-api T2-04 LGPD RIPD Art.15)
 * Rota:  POST /api/v1/compliance/structural-screens (Sprint 20 structural_screens.py)
 *
 * Executar:
 *   k6 run tests/k6/02-structural-screening-onboarding.js \
 *       -e K6_BASE_URL=https://compliance.ontrackchain.com.br
 *
 * SLA / Thresholds (mesmos Sprints 17 → 22):
 *   - p95 duração < 650ms  (screening tem mais cálculos de due-diligence)
 *   - 99% requests 2XX
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Trend } from "k6/metrics";

const BASE_URL = __ENV.K6_BASE_URL || "http://127.0.0.1:8002";

export const options = {
  stages: [
    { duration: "8s",  target: 5  },
    { duration: "20s", target: 30 },
    { duration: "7s",  target: 0  },
  ],
  thresholds: {
    http_req_duration: ["p(95)<650", "p(99)<1800"],
    http_req_failed:   ["rate<0.015"],
    checks:            ["rate>0.985"],
  },
  summaryTrendStats: ["avg", "min", "med", "max", "p(95)", "p(99)"],
};

const assessmentLatency = new Trend("structural_assessment_latency_ms", true);

const SAMPLES = [
  {
    organization_id: "00000000-0000-0000-0000-000000000200",
    counterparty_id: "cp_78901",
    legal_name: "ALVO FACIL CORRETORA DE CAMBIOS S.A.",
    tax_id: "22.333.444/0001-55",
    jurisdiction: "BR",
    obl_obr_01_relationship_due_diligence: {
      relationship_type: "correspondent_banking",
      country_risk_2x2_score: 62,
      kyc_aml_regime_equivalency: "partial",
      resident_agent_appointed: false,
      branches_abroad_count: 4,
      notes: "Operações em paraísos fiscais detectados em análise de grafos",
    },
    obl_obr_02_source_of_funds: {
      primary_source: "foreign_exchange_margin",
      fatf_typology_match_count: 3,
      expected_annual_volume_usd_cents: 42_000_000_00,
      expected_monthly_txn_count: 1800,
      risk_mitigation_controls: [
        "monthly_aml_review",
        "enhanced_due_diligence_high_risk",
        "screening_before_each_txn_above_50k_usd",
      ],
    },
    work_items_required: ["OBR-01", "OBR-02", "OBR-03"],
    requester_user_email: "compliance@ontrackchain.com.br",
  },
  {
    organization_id: "00000000-0000-0000-0000-000000000201",
    counterparty_id: "cp_mercury_01",
    legal_name: "MERCURIO GREEN ENERGY OY",
    tax_id: "FI-98765432",
    jurisdiction: "FI",
    obl_obr_01_relationship_due_diligence: {
      relationship_type: "direct_customer",
      country_risk_2x2_score: 28,
      kyc_aml_regime_equivalency: "full",
      resident_agent_appointed: true,
      branches_abroad_count: 0,
      notes: "Empresa Finlandesa de energia renovável - baixo risco país",
    },
    obl_obr_02_source_of_funds: {
      primary_source: "subsidy_grants",
      fatf_typology_match_count: 0,
      expected_annual_volume_usd_cents: 9_000_000_00,
      expected_monthly_txn_count: 40,
      risk_mitigation_controls: ["quarterly_review"],
    },
    work_items_required: ["OBR-04"],
    requester_user_email: "kyc@ontrackchain.fi",
  },
];

export default function () {
  const payload = SAMPLES[Math.floor(Math.random() * SAMPLES.length)];
  const bodyStr = JSON.stringify(payload);
  const params = {
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": `k6-struct-${__VU}-${Date.now()}`,
      Authorization: __ENV.K6_BEARER || "Bearer eyJhbGciOiJFUzI1NiJ9.k6demo.notused_local",
    },
    tags: { route: "structural_screens_v1", phase: "Q3-04" },
    timeout: "2.5s",
  };

  const t0 = Date.now();
  const res = http.post(
    `${BASE_URL}/api/v1/compliance/structural-screens`,
    bodyStr,
    params,
  );
  assessmentLatency.add(Date.now() - t0);

  check(res, {
    "status 201 Created":        (r) => r.status === 201,
    "overall_assessment válido": (r) => {
      try {
        const level = r.json("overall_assessment");
        return ["BAIXO", "MÉDIO", "ALERTA", "ALTO"].includes(level);
      } catch (_) { return false; }
    },
    "retorna screen_id":         (r) => typeof r.json("screen_id") === "string",
  });

  sleep(0.075);
}

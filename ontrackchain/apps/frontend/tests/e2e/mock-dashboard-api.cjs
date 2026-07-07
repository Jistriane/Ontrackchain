const http = require("http");

const port = Number(process.env.DASHBOARD_MOCK_API_PORT || "4010");

const json = (res, status, body) => {
  res.writeHead(status, { "content-type": "application/json" });
  res.end(JSON.stringify(body));
};

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (url.pathname === "/api/v1/monitoring/watchlists") {
    return json(res, 200, [{ id: "watch-e2e-01", name: "Watchlist E2E", priority: "high" }]);
  }

  if (url.pathname === "/api/v1/billing/balance") {
    return json(res, 200, {
      credits_available: 1000,
      credits_reserved: 12,
      credits_used_total: 345
    });
  }

  if (url.pathname === "/api/v1/investigation/admin/operations") {
    return json(res, 200, {
      queue: {
        ready: 1,
        waiting: 2,
        retry_pending: 0,
        retry_due: 0,
        wake_signals: 0
      },
      concurrency: {
        org_active: 1,
        org_limit: 5,
        global_active: 2,
        global_limit: 10,
        plan: "professional"
      },
      throughput: {
        completed_last_hour: 3,
        failed_last_hour: 0,
        billing_recalc_last_hour: 1,
        avg_duration_ms_last_20: 1200
      },
      states: {
        queued: 2,
        processing: 1,
        dlq_failed: 0,
        dlq_resolved: 0
      },
      recent_cases: [
        {
          case_id: "66666666-6666-4666-8666-666666666666",
          status: "completed",
          target_address: "0xdddddddddddddddddddddddddddddddddddddddd",
          target_chain: "ethereum",
          created_at: "2026-07-06T12:00:00.000Z",
          completed_at: "2026-07-06T12:10:00.000Z",
          queue_state: "completed",
          last_error: null,
          attempt_count: 1,
          report_type_canonical: "coaf_ready_report",
          charged_cost: 42.5,
          duration_ms: 1200
        }
      ],
      generated_at: "2026-07-06T12:15:00.000Z"
    });
  }

  if (url.pathname === "/api/v1/monitoring/operational-alerts") {
    return json(res, 200, { total_count: 4 });
  }

  return json(res, 404, { detail: "not_found", path: url.pathname });
});

server.listen(port, "127.0.0.1", () => {
  console.log(`[mock-dashboard-api] listening on http://127.0.0.1:${port}`);
});

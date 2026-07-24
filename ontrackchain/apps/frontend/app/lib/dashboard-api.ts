export interface DashboardSummary {
  total_cases: number;
  active_cases: number;
  total_alerts: number;
  open_alerts: number;
  total_counterparties: number;
  blocked_counterparties: number;
  total_sanctions_checks: number;
  pending_reviews: number;
  revenue: number;
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const response = await fetch("/api/app/dashboard/summary", { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Failed to fetch dashboard summary");
  }
  return response.json();
}

"use client";

import { useEffect, useState } from "react";

import { AppShell, MetricCard, MetricGrid, Panel, Pill } from "../../../components/ui";
import { useI18n } from "../../../components/i18n-provider";
import { canEvaluateBlock, canLiftBlock } from "../../lib/authz";
import type { MessageKey } from "../../lib/i18n";
import { fetchAuthContext, type AuthContext } from "../../lib/ownership";

type BlockAnalytics = {
  total_blocks: number;
  active_blocks: number;
  lifted_blocks: number;
  pending_review: number;
  blocks_with_coaf: number;
  blocks_last_30_days: number;
  avg_confidence: number;
  chains_distribution: Record<string, number>;
  status_distribution: Record<string, number>;
};

const DEFAULT_ANALYTICS: BlockAnalytics = {
  total_blocks: 0,
  active_blocks: 0,
  lifted_blocks: 0,
  pending_review: 0,
  blocks_with_coaf: 0,
  blocks_last_30_days: 0,
  avg_confidence: 0,
  chains_distribution: {},
  status_distribution: {}
};

export default function BlocksAnalyticsPage() {
  const { t } = useI18n();
  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [authResolved, setAuthResolved] = useState(false);
  const [analytics, setAnalytics] = useState<BlockAnalytics>(DEFAULT_ANALYTICS);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAuthContext()
      .then((context) => setAuthContext(context))
      .catch(() => setAuthContext(null))
      .finally(() => setAuthResolved(true));
  }, []);

  const canRead = authResolved ? (canEvaluateBlock(authContext?.role) || canLiftBlock(authContext?.role)) : null;

  useEffect(() => {
    if (!canRead) return;

    async function loadAnalytics() {
      try {
        const blocksRes = await fetch("/api/app/compliance/blocks", { cache: "no-store" });
        if (blocksRes.ok) {
          const data = await blocksRes.json();
          const items = data.items || [];
          const now = new Date();
          const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

          const totalBlocks = items.length;
          const activeBlocks = items.filter((b: { status: string }) => b.status === "active" || b.status === "BLOCKED").length;
          const liftedBlocks = items.filter((b: { status: string }) => b.status === "lifted" || b.status === "LIFTED").length;
          const pendingReview = items.filter((b: { review_status: string }) => b.review_status === "pending").length;
          const blocksWithCoaf = items.filter((b: { requires_coaf_report: boolean }) => b.requires_coaf_report).length;
          const blocksLast30Days = items.filter((b: { screened_at: string }) => new Date(b.screened_at) >= thirtyDaysAgo).length;

          const totalConfidence = items.reduce((sum: number, b: { decision_confidence: number }) => sum + (b.decision_confidence || 0), 0);
          const avgConfidence = totalBlocks > 0 ? totalConfidence / totalBlocks : 0;

          const chainsDist: Record<string, number> = {};
          const statusDist: Record<string, number> = {};
          items.forEach((b: { chain: string; status: string }) => {
            chainsDist[b.chain] = (chainsDist[b.chain] || 0) + 1;
            statusDist[b.status] = (statusDist[b.status] || 0) + 1;
          });

          setAnalytics({
            total_blocks: totalBlocks,
            active_blocks: activeBlocks,
            lifted_blocks: liftedBlocks,
            pending_review: pendingReview,
            blocks_with_coaf: blocksWithCoaf,
            blocks_last_30_days: blocksLast30Days,
            avg_confidence: Math.round(avgConfidence * 100) / 100,
            chains_distribution: chainsDist,
            status_distribution: statusDist
          });
        }
      } catch {
        setError(t("blocks.analytics.loadError" as MessageKey));
      }
    }

    loadAnalytics();
  }, [canRead, t]);

  if (authResolved && !canRead) {
    return (
      <AppShell title={t("blocks.analytics.title")} subtitle={t("blocks.analytics.subtitle")} activePath="/blocks">
        <Panel title={t("blocks.analytics.accessDenied")}>
          <p>{t("blocks.analytics.accessDeniedDescription")}</p>
        </Panel>
      </AppShell>
    );
  }

  return (
    <AppShell
      title={t("blocks.analytics.title")}
      subtitle={t("blocks.analytics.subtitle")}
      activePath="/blocks"
      actions={<a className="otc-link-button" href="/blocks">{t("blocks.analytics.backToBlocks")}</a>}
    >
      {error && <p className="otc-error">{error}</p>}

      <MetricGrid>
        <MetricCard
          label={t("blocks.analytics.totalBlocks")}
          value={analytics.total_blocks}
          meta={t("blocks.analytics.totalBlocksMeta")}
        />
        <MetricCard
          label={t("blocks.analytics.activeBlocks")}
          value={analytics.active_blocks}
          meta={t("blocks.analytics.activeBlocksMeta")}
          accent
        />
        <MetricCard
          label={t("blocks.analytics.liftedBlocks")}
          value={analytics.lifted_blocks}
          meta={t("blocks.analytics.liftedBlocksMeta")}
        />
        <MetricCard
          label={t("blocks.analytics.pendingReview")}
          value={analytics.pending_review}
          meta={t("blocks.analytics.pendingReviewMeta")}
          accent
        />
      </MetricGrid>

      <MetricGrid>
        <MetricCard
          label={t("blocks.analytics.blocksWithCoaf")}
          value={analytics.blocks_with_coaf}
          meta={t("blocks.analytics.blocksWithCoafMeta")}
        />
        <MetricCard
          label={t("blocks.analytics.blocksLast30Days")}
          value={analytics.blocks_last_30_days}
          meta={t("blocks.analytics.blocksLast30DaysMeta")}
        />
        <MetricCard
          label={t("blocks.analytics.avgConfidence")}
          value={analytics.avg_confidence}
          meta={t("blocks.analytics.avgConfidenceMeta")}
        />
      </MetricGrid>

      <Panel title={t("blocks.analytics.statusDistribution")} description={t("blocks.analytics.statusDistributionDescription")}>
        <table className="otc-table">
          <thead>
            <tr>
              <th>{t("blocks.analytics.status")}</th>
              <th>{t("blocks.analytics.count")}</th>
              <th>{t("blocks.analytics.percentage")}</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(analytics.status_distribution).map(([status, count]) => (
              <tr key={status}>
                <td><Pill>{status}</Pill></td>
                <td>{count}</td>
                <td>{analytics.total_blocks > 0 ? Math.round((count / analytics.total_blocks) * 100) : 0}%</td>
              </tr>
            ))}
            {Object.keys(analytics.status_distribution).length === 0 && (
              <tr><td colSpan={3} className="otc-muted">{t("blocks.analytics.noData")}</td></tr>
            )}
          </tbody>
        </table>
      </Panel>

      <Panel title={t("blocks.analytics.chainsDistribution")} description={t("blocks.analytics.chainsDistributionDescription")}>
        <table className="otc-table">
          <thead>
            <tr>
              <th>{t("blocks.analytics.chain")}</th>
              <th>{t("blocks.analytics.count")}</th>
              <th>{t("blocks.analytics.percentage")}</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(analytics.chains_distribution).map(([chain, count]) => (
              <tr key={chain}>
                <td><Pill>{chain}</Pill></td>
                <td>{count}</td>
                <td>{analytics.total_blocks > 0 ? Math.round((count / analytics.total_blocks) * 100) : 0}%</td>
              </tr>
            ))}
            {Object.keys(analytics.chains_distribution).length === 0 && (
              <tr><td colSpan={3} className="otc-muted">{t("blocks.analytics.noData")}</td></tr>
            )}
          </tbody>
        </table>
      </Panel>
    </AppShell>
  );
}

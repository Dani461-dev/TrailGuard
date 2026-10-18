import React, { useMemo, useState } from "react";
import type { Alert } from "@/lib/trailguardApi";
import { byDay, byDayBand, explainCounts, tierCounts, topUsers } from "./aggregate";
import AreaChart from "./charts/AreaChart";
import StackedBarChart from "./charts/StackedBarChart";
import DonutChart from "./charts/DonutChart";
import Icon from "./Icon";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  RiskRing,
  Skeleton,
  StatCard,
  toast,
} from "./primitives";
import { decisionKey, useDashboardData } from "./useDashboardData";
import {
  cn,
  explainTone,
  fmtDate,
  fmtNum,
  fmtPct,
  RISK_COLOR,
  riskBand,
  riskPct,
  shortUser,
  tierStyle,
} from "./ui";

function RiskBar({ risk, className }: { risk: number; className?: string }) {
  const color = RISK_COLOR[riskBand(risk)];
  return (
    <span
      className={cn(
        "relative inline-block h-1.5 w-16 overflow-hidden rounded-full bg-white/10 align-middle",
        className,
      )}
    >
      <span
        className="absolute inset-y-0 left-0 rounded-full"
        style={{ width: `${riskPct(risk)}%`, background: color }}
      />
    </span>
  );
}

function QueueRow({
  alert,
  onDecide,
}: {
  alert: Alert;
  onDecide: (a: Alert, d: "approve" | "reject") => Promise<void>;
}) {
  const [busy, setBusy] = useState<null | "approve" | "reject">(null);
  const s = tierStyle(alert.tier);

  const run = async (d: "approve" | "reject") => {
    setBusy(d);
    await onDecide(alert, d);
    setBusy(null);
  };

  return (
    <div className="flex items-center gap-3 px-5 py-3 transition hover:bg-white/[0.02]">
      <RiskRing risk={alert.risk} size={44} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm text-text-light">
            user {shortUser(alert.user)}
          </span>
          <span className={`rounded-full px-2 py-0.5 text-[0.64rem] font-semibold ${s.badge}`}>
            tier {alert.tier}
          </span>
        </div>
        <p className="mt-0.5 truncate text-xs text-text-dark">
          {fmtDate(alert.day)} · {alert.action}
        </p>
      </div>
      <div className="flex shrink-0 gap-2">
        <Button
          size="sm"
          variant="ok"
          icon="check"
          disabled={busy !== null}
          onClick={() => run("approve")}
        >
          {busy === "approve" ? "…" : "Approve"}
        </Button>
        <Button
          size="sm"
          variant="danger"
          icon="x"
          disabled={busy !== null}
          onClick={() => run("reject")}
        >
          Reject
        </Button>
      </div>
    </div>
  );
}

export default function Overview() {
  const {
    loading,
    alerts,
    metrics,
    source,
    decisionMap,
    decide,
  } = useDashboardData();

  const days = useMemo(() => byDay(alerts), [alerts]);
  const stacked = useMemo(() => byDayBand(alerts), [alerts]);
  const bandTotals = useMemo(
    () =>
      stacked.reduce(
        (acc, d) => ({
          critical: acc.critical + d.critical,
          moderate: acc.moderate + d.moderate,
          low: acc.low + d.low,
        }),
        { critical: 0, moderate: 0, low: 0 },
      ),
    [stacked],
  );
  const tiers = useMemo(() => tierCounts(alerts), [alerts]);
  const users = useMemo(() => topUsers(alerts, 5), [alerts]);
  const explains = useMemo(() => explainCounts(alerts), [alerts]);
  const recent = useMemo(
    () => [...alerts].sort((a, b) => b.risk - a.risk).slice(0, 6),
    [alerts],
  );
  const pending = useMemo(
    () =>
      alerts.filter(
        (a) => a.requires_human_approval && !decisionMap.has(decisionKey(a)),
      ),
    [alerts, decisionMap],
  );

  const onDecide = async (a: Alert, d: "approve" | "reject") => {
    const res = await decide(a, d);
    if (res.offline) toast("Decision not stored (API offline).", "err");
    else toast(d === "approve" ? "Alert approved." : "Alert rejected.", "ok");
  };

  const areaSeries = days.map((d) => ({
    day: d.day,
    value: d.maxRisk,
    count: d.count,
  }));
  const tierSegments = [
    { label: "tier 3 · ticket", value: tiers[3], color: RISK_COLOR.high },
    { label: "tier 2 · step-up", value: tiers[2], color: RISK_COLOR.mid },
    { label: "tier 1 · log", value: tiers[1], color: RISK_COLOR.low },
  ];
  const maxExplain = Math.max(...explains.map((e) => e.count), 1);

  if (loading) {
    return (
      <div className="space-y-5">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <div className="grid gap-5 lg:grid-cols-3">
          <Skeleton className="h-80 lg:col-span-2" />
          <Skeleton className="h-80" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {source === "sample" && (
        <div className="flex items-start gap-3 rounded-2xl border border-amber-400/25 bg-amber-400/[0.07] px-4 py-3 text-sm text-amber-200/90">
          <Icon name="info" className="mt-0.5 size-4 shrink-0 text-amber-300" />
          <p>
            Showing <strong className="text-amber-200">sample data</strong> —
            not real results. Run the pipeline then <code className="font-mono">make api</code>{" "}
            for real data from <code className="font-mono">outputs/</code>.
          </p>
        </div>
      )}

      {/* KPI */}
      <section className="dr-in grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard
          label="Precision @ budget"
          value={fmtPct(metrics.precision_at_budget)}
          hint="of alerts shown"
          icon="target"
          accent="text-emerald-300"
          bar={metrics.precision_at_budget}
        />
        <StatCard
          label="Recall @ budget"
          value={fmtPct(metrics.recall_at_budget)}
          hint="of malicious user-days"
          icon="gauge"
          accent="text-primary"
          bar={metrics.recall_at_budget}
        />
        <StatCard
          label="Insiders detected"
          value={`${metrics.insiders_detected ?? "—"} / ${metrics.insiders_in_test ?? "?"}`}
          hint="in the test set"
          icon="user"
        />
        <StatCard
          label="Median days-to-detection"
          value={
            typeof metrics.median_days_to_detection === "number"
              ? `${metrics.median_days_to_detection} days`
              : "—"
          }
          hint="since first activity"
          icon="clock"
        />
        <StatCard
          label="Alerts shown"
          value={fmtNum(metrics.n_alerts)}
          hint={
            typeof metrics.alert_budget_per_day === "number"
              ? `budget ${metrics.alert_budget_per_day}/day`
              : undefined
          }
          icon="alert"
          spark={days.map((d) => d.count)}
        />
        <StatCard
          label="Malicious user-days"
          value={fmtNum(metrics.n_malicious_user_days)}
          hint="test label (evaluation only)"
          icon="layers"
        />
      </section>

      {/* charts */}
      <section className="grid gap-5 lg:grid-cols-3">
        <Card className="dr-in lg:col-span-2">
          <CardHeader
            title="Risk score over time"
            subtitle="daily maximum · thresholds 0.60 (step-up) & 0.85 (ticket)"
            icon="chart"
          />
          <div className="p-5">
            <AreaChart series={areaSeries} />
          </div>
        </Card>
        <Card className="dr-in">
          <CardHeader
            title="Tier distribution"
            subtitle={`${alerts.length} alerts · ${pending.length} awaiting`}
            icon="layers"
          />
          <div className="p-5">
            <DonutChart segments={tierSegments} />
          </div>
        </Card>
      </section>

      <section className="grid gap-5 lg:grid-cols-3">
        <Card className="dr-in lg:col-span-2">
          <CardHeader
            title="Alerts per day"
            subtitle="stacked by risk band · tier 3 on top · tier 1 at the bottom"
            icon="calendar"
            action={
              <div className="flex items-center gap-3 text-[0.68rem] text-text-dark">
                <span className="inline-flex items-center gap-1.5">
                  <span className="size-2.5 rounded-sm" style={{ background: RISK_COLOR.high }} />
                  critical <span className="font-mono text-text">{bandTotals.critical}</span>
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <span className="size-2.5 rounded-sm" style={{ background: RISK_COLOR.mid }} />
                  moderate <span className="font-mono text-text">{bandTotals.moderate}</span>
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <span className="size-2.5 rounded-sm" style={{ background: RISK_COLOR.low }} />
                  low <span className="font-mono text-text">{bandTotals.low}</span>
                </span>
              </div>
            }
          />
          <div className="p-5">
            <StackedBarChart data={stacked} />
          </div>
        </Card>
        <Card className="dr-in">
          <CardHeader
            title="Explanation methods"
            subtitle="explain_method across alerts"
            icon="spark"
          />
          <div className="space-y-4 p-5">
            {explains.length === 0 ? (
              <p className="py-6 text-center text-sm text-text-dark">—</p>
            ) : (
              explains.map((e) => (
                <div key={e.method}>
                  <div className="mb-1.5 flex items-center justify-between">
                    <span className={`rounded-md px-2 py-0.5 font-mono text-[0.68rem] ${explainTone(e.method)}`}>
                      {e.method}
                    </span>
                    <span className="font-mono text-xs text-text-dark">
                      {e.count} alert
                    </span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-primary to-primary-light"
                      style={{ width: `${(e.count / maxExplain) * 100}%` }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </section>

      {/* queue + top users */}
      <section className="grid gap-5 lg:grid-cols-3">
        <Card className="dr-in lg:col-span-2">
          <CardHeader
            title="Awaiting approval"
            subtitle="tier 3 — the system never blocks automatically"
            icon="alert"
            action={
              <Badge tone={pending.length ? "secondary" : "emerald"}>
                {pending.length} queued
              </Badge>
            }
          />
          {pending.length === 0 ? (
            <EmptyState
              icon="check"
              title="Nothing waiting"
              hint="All tier-3 alerts have been decided."
            />
          ) : (
            <div className="divide-y divide-border/60">
              {pending.slice(0, 6).map((a) => (
                <QueueRow key={decisionKey(a)} alert={a} onDecide={onDecide} />
              ))}
            </div>
          )}
        </Card>
        <Card className="dr-in">
          <CardHeader
            title="Riskiest users"
            subtitle="top 5"
            icon="users"
          />
          <div className="space-y-3 p-5">
            {users.length === 0 ? (
              <p className="py-6 text-center text-sm text-text-dark">—</p>
            ) : (
              users.map((u, i) => (
                <div key={u.user} className="flex items-center gap-3">
                  <span className="grid size-6 shrink-0 place-items-center rounded-md bg-white/5 font-mono text-[0.68rem] text-text-dark">
                    {i + 1}
                  </span>
                  <span className="min-w-0 flex-1 truncate font-mono text-sm text-text-light">
                    {shortUser(u.user)}
                  </span>
                  <span className="text-[0.68rem] text-text-dark">{u.count}×</span>
                  <RiskBar risk={u.maxRisk} />
                  <span className="w-9 text-right font-mono text-xs text-white">
                    {u.maxRisk.toFixed(2)}
                  </span>
                </div>
              ))
            )}
          </div>
        </Card>
      </section>

      {/* recent alerts */}
      <Card className="dr-in">
        <CardHeader
          title="Latest alerts"
          subtitle="highest risk in the current set"
          icon="list"
          action={
            <a
              href="/dashboard/alerts"
              className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text transition hover:border-primary/40 hover:text-white"
            >
              View all <Icon name="chevronRight" className="size-3.5" />
            </a>
          }
        />
        <div className="overflow-x-auto">
          <table className="w-full min-w-160 text-left text-sm">
            <thead className="text-[0.68rem] uppercase tracking-wide text-text-dark">
              <tr className="border-b border-border/60">
                <th className="px-5 py-2.5 font-medium">User</th>
                <th className="px-4 py-2.5 font-medium">Date</th>
                <th className="px-4 py-2.5 font-medium">Risk</th>
                <th className="px-4 py-2.5 font-medium">Tier</th>
                <th className="px-4 py-2.5 font-medium">Explain</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((a) => {
                const s = tierStyle(a.tier);
                return (
                  <tr
                    key={decisionKey(a)}
                    className="border-b border-border/40 transition hover:bg-white/[0.02]"
                  >
                    <td className="px-5 py-3 font-mono text-text-light">
                      user {shortUser(a.user)}
                    </td>
                    <td className="px-4 py-3 text-text-dark">{fmtDate(a.day)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <RiskBar risk={a.risk} />
                        <span className="font-mono text-xs text-white">
                          {a.risk.toFixed(2)}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2.5 py-0.5 text-[0.66rem] font-semibold ${s.badge}`}>
                        tier {a.tier}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`rounded-md px-2 py-0.5 font-mono text-[0.68rem] ${explainTone(a.explain_method)}`}>
                        {a.explain_method}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

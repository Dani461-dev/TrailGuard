import React, { useEffect, useMemo, useState } from "react";
import type { Alert } from "@/lib/trailguardApi";
import AlertDrawer from "./AlertDrawer";
import { tierCounts } from "./aggregate";
import Icon from "./Icon";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Input,
  Segmented,
  Select,
  Skeleton,
  toast,
} from "./primitives";
import { decisionKey, useDashboardData } from "./useDashboardData";
import {
  cn,
  explainTone,
  fmtDate,
  RISK_COLOR,
  riskBand,
  riskPct,
  shortUser,
  tierStyle,
} from "./ui";

type SortKey = "risk-desc" | "day-desc" | "day-asc" | "user-asc";
type ApprovalFilter = "all" | "pending" | "settled" | "auto";

const PAGE_SIZE = 12;

function RiskCell({ risk }: { risk: number }) {
  const color = RISK_COLOR[riskBand(risk)];
  return (
    <div className="flex items-center gap-2">
      <span className="relative inline-block h-1.5 w-20 overflow-hidden rounded-full bg-white/10">
        <span
          className="absolute inset-y-0 left-0 rounded-full"
          style={{ width: `${riskPct(risk)}%`, background: color }}
        />
      </span>
      <span className="font-mono text-xs text-white">{risk.toFixed(2)}</span>
    </div>
  );
}

export default function AlertsTable() {
  const { loading, alerts, source, decisionMap, decide } = useDashboardData();

  const [query, setQuery] = useState("");
  const [tier, setTier] = useState<string>("all");
  const [explain, setExplain] = useState<string>("all");
  const [approval, setApproval] = useState<ApprovalFilter>("all");
  const [sort, setSort] = useState<SortKey>("risk-desc");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Alert | null>(null);

  const counts = useMemo(() => tierCounts(alerts), [alerts]);
  const explainMethods = useMemo(
    () => [...new Set(alerts.map((a) => a.explain_method))].sort(),
    [alerts],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const rows = alerts.filter((a) => {
      if (tier !== "all" && a.tier !== Number(tier)) return false;
      if (explain !== "all" && a.explain_method !== explain) return false;

      const settled = decisionMap.has(decisionKey(a));
      if (approval === "pending" && !(a.requires_human_approval && !settled)) return false;
      if (approval === "settled" && !settled) return false;
      if (approval === "auto" && a.requires_human_approval) return false;

      if (!q) return true;
      return a.user.toLowerCase().includes(q) || a.day.includes(q);
    });
    const sorted = [...rows];
    if (sort === "risk-desc") sorted.sort((a, b) => b.risk - a.risk);
    else if (sort === "day-desc") sorted.sort((a, b) => b.day.localeCompare(a.day));
    else if (sort === "day-asc") sorted.sort((a, b) => a.day.localeCompare(b.day));
    else sorted.sort((a, b) => a.user.localeCompare(b.user));
    return sorted;
  }, [alerts, tier, explain, approval, query, sort, decisionMap]);

  useEffect(() => setPage(1), [tier, explain, approval, query, sort]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const clampedPage = Math.min(page, pageCount);
  const pageRows = filtered.slice(
    (clampedPage - 1) * PAGE_SIZE,
    clampedPage * PAGE_SIZE,
  );

  const reset = () => {
    setQuery("");
    setTier("all");
    setExplain("all");
    setApproval("all");
    setSort("risk-desc");
  };

  const onDecide = async (
    a: Alert,
    d: "approve" | "reject",
    note?: string,
  ) => {
    const res = await decide(a, d, note);
    if (res.offline) toast("Decision not stored (API offline).", "err");
    else toast(d === "approve" ? "Alert approved." : "Alert rejected.", "ok");
  };

  const selectedDecision = selected
    ? decisionMap.get(decisionKey(selected))
    : undefined;

  return (
    <div className="space-y-5">
      {/* filter card */}
      <Card className="dr-in">
        <div className="flex flex-wrap items-center gap-2 p-4">
          <Input
            icon="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search user / date…"
            className="w-full sm:w-64"
          />
          <Segmented
            value={tier}
            onChange={setTier}
            options={[
              { key: "all", label: "All", count: alerts.length },
              { key: "3", label: "Tier 3", count: counts[3] },
              { key: "2", label: "Tier 2", count: counts[2] },
              { key: "1", label: "Tier 1", count: counts[1] },
            ]}
          />
          <div className="ml-auto flex flex-wrap items-center gap-2">
            <Select value={approval} onChange={(e) => setApproval(e.target.value as ApprovalFilter)}>
              <option value="all">All statuses</option>
              <option value="pending">Awaiting approval</option>
              <option value="settled">Decided</option>
              <option value="auto">Automatic</option>
            </Select>
            <Select value={explain} onChange={(e) => setExplain(e.target.value)}>
              <option value="all">All explain_method</option>
              {explainMethods.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </Select>
            <Select value={sort} onChange={(e) => setSort(e.target.value as SortKey)}>
              <option value="risk-desc">Highest risk</option>
              <option value="day-desc">Newest first</option>
              <option value="day-asc">Oldest first</option>
              <option value="user-asc">User (A–Z)</option>
            </Select>
            <Button variant="subtle" size="sm" icon="refresh" onClick={reset}>
              Reset
            </Button>
          </div>
        </div>
        <div className="flex items-center justify-between border-t border-border/60 px-4 py-2.5 text-xs text-text-dark">
          <span>
            Showing{" "}
            <span className="font-mono text-text">{pageRows.length}</span> of{" "}
            <span className="font-mono text-text">{filtered.length}</span> alerts
            {filtered.length !== alerts.length && ` (of ${alerts.length})`}
          </span>
          <span className="font-mono">
            page {clampedPage}/{pageCount}
          </span>
        </div>
      </Card>

      {/* table */}
      <Card className="dr-in overflow-hidden">
        {loading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-12" />
            ))}
          </div>
        ) : alerts.length === 0 ? (
          <EmptyState
            icon="shield"
            title="No alerts yet"
            hint="Run the pipeline first (make toy), then open the dashboard via make api (Flask :8000)."
          />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon="search"
            title="Nothing matches"
            hint="Try changing the filters or search terms."
            action={
              <Button variant="ghost" size="sm" icon="refresh" onClick={reset}>
                Reset filter
              </Button>
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-200 text-left text-sm">
              <thead className="sticky top-0 z-10 bg-light/95 text-[0.66rem] uppercase tracking-wide text-text-dark backdrop-blur">
                <tr className="border-b border-border">
                  <th className="px-5 py-3 font-medium">User</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Risk</th>
                  <th className="px-4 py-3 font-medium">Tier / action</th>
                  <th className="px-4 py-3 font-medium">Explain</th>
                  <th className="px-4 py-3 font-medium">Approval</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {pageRows.map((a) => {
                  const s = tierStyle(a.tier);
                  const dec = decisionMap.get(decisionKey(a));
                  return (
                    <tr
                      key={decisionKey(a)}
                      onClick={() => setSelected(a)}
                      className="cursor-pointer border-b border-border/40 transition hover:bg-white/[0.03]"
                    >
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <span
                            className="h-8 w-1 rounded-full"
                            style={{ background: RISK_COLOR[riskBand(a.risk)] }}
                          />
                          <span className="font-mono text-text-light">
                            {shortUser(a.user)}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-text-dark">{fmtDate(a.day)}</td>
                      <td className="px-4 py-3">
                        <RiskCell risk={a.risk} />
                      </td>
                      <td className="px-4 py-3">
                        <span className={`rounded-full px-2.5 py-0.5 text-[0.66rem] font-semibold ${s.badge}`}>
                          tier {a.tier}
                        </span>
                        <p className="mt-1 font-mono text-[0.66rem] text-text-dark">
                          {a.action}
                        </p>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`rounded-md px-2 py-0.5 font-mono text-[0.68rem] ${explainTone(a.explain_method)}`}>
                          {a.explain_method}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {dec ? (
                          <Badge tone={dec.decision === "approve" ? "emerald" : "secondary"}>
                            <Icon
                              name={dec.decision === "approve" ? "check" : "x"}
                              className="size-3"
                            />
                            {dec.decision === "approve" ? "Approved" : "Rejected"}
                          </Badge>
                        ) : a.requires_human_approval ? (
                          <Badge tone="amber">
                            <Icon name="clock" className="size-3" /> Waiting
                          </Badge>
                        ) : (
                          <span className="text-xs text-text-dark">Automatic</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-text-dark">
                        <Icon name="chevronRight" className="ml-auto size-4" />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* pagination */}
        {!loading && pageCount > 1 && (
          <div className="flex items-center justify-between border-t border-border/60 px-4 py-3">
            <Button
              variant="ghost"
              size="sm"
              icon="arrowLeft"
              disabled={clampedPage <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <div className="flex items-center gap-1">
              {Array.from({ length: pageCount }).map((_, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setPage(i + 1)}
                  className={cn(
                    "size-7 rounded-lg text-xs font-medium transition",
                    i + 1 === clampedPage
                      ? "bg-primary/20 text-primary"
                      : "text-text-dark hover:bg-white/5 hover:text-text",
                  )}
                >
                  {i + 1}
                </button>
              ))}
            </div>
            <Button
              variant="ghost"
              size="sm"
              disabled={clampedPage >= pageCount}
              onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
            >
              Next
              <Icon name="chevronRight" className="size-3.5" />
            </Button>
          </div>
        )}
      </Card>

      <p className="text-xs text-text-dark">
        Tier 3 (risk ≥ 0.85) requires human approval — the system never blocks
        accounts automatically. Numbers & tiers follow Contract #3.
        {source === "sample" && " Showing sample data (preview)."}
      </p>

      <AlertDrawer
        alert={selected}
        decision={selectedDecision}
        source={source}
        onClose={() => setSelected(null)}
        onDecide={onDecide}
      />
    </div>
  );
}

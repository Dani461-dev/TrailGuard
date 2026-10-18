import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchAlerts,
  fetchConfig,
  fetchDecisions,
  fetchMetrics,
  postDecision,
  type Alert,
  type ConfigInfo,
  type Decision,
  type Metrics,
  type Source,
} from "@/lib/trailguardApi";

export function decisionKey(a: { user: string; day: string }): string {
  return `${a.user}|${a.day}`;
}

export interface DashboardData {
  loading: boolean;
  refreshing: boolean;
  alerts: Alert[];
  metrics: Metrics;
  config: ConfigInfo | null;
  decisions: Decision[];
  decisionMap: Map<string, Decision>;
  source: Source;
  refresh: () => void;
  decide: (
    alert: Alert,
    decision: "approve" | "reject",
    note?: string,
  ) => Promise<{ ok: boolean; offline?: boolean }>;
}

/** Fetch all dashboard data + auto-refresh via the global "trailguard:refresh" event. */
export function useDashboardData(): DashboardData {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [metrics, setMetrics] = useState<Metrics>({});
  const [config, setConfig] = useState<ConfigInfo | null>(null);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [source, setSource] = useState<Source>("sample");

  useEffect(() => {
    let alive = true;
    Promise.all([fetchAlerts(), fetchMetrics(), fetchConfig(), fetchDecisions()]).then(
      ([aRes, mRes, cRes, dRes]) => {
        if (!alive) return;
        setAlerts(aRes.data);
        setMetrics(mRes.data);
        setConfig(cRes.data);
        setDecisions(dRes.data);
        setSource(aRes.source);
        setLoading(false);
        setRefreshing(false);
      },
    );
    return () => {
      alive = false;
    };
  }, [reloadKey]);

  useEffect(() => {
    const onRefresh = () => {
      setRefreshing(true);
      setReloadKey((k) => k + 1);
    };
    window.addEventListener("trailguard:refresh", onRefresh);
    return () => window.removeEventListener("trailguard:refresh", onRefresh);
  }, []);

  const decisionMap = useMemo(() => {
    const m = new Map<string, Decision>();
    for (const d of decisions) m.set(decisionKey(d), d);
    return m;
  }, [decisions]);

  const refresh = useCallback(() => {
    setRefreshing(true);
    setReloadKey((k) => k + 1);
  }, []);

  const decide = useCallback(
    async (alert: Alert, decision: "approve" | "reject", note?: string) => {
      const row: Decision = {
        ts: new Date().toISOString(),
        user: alert.user,
        day: alert.day,
        decision,
        note,
        risk: alert.risk,
        tier: alert.tier,
      };
      setDecisions((prev) => [...prev, row]);
      return postDecision({
        user: alert.user,
        day: alert.day,
        decision,
        note,
        risk: alert.risk,
        tier: alert.tier,
      });
    },
    [],
  );

  return {
    loading,
    refreshing,
    alerts,
    metrics,
    config,
    decisions,
    decisionMap,
    source,
    refresh,
    decide,
  };
}

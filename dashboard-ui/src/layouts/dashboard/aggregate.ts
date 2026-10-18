import type { Alert } from "@/lib/trailguardApi";
import { riskBand, type RiskBand } from "./ui";

export interface DayAgg {
  day: string;
  maxRisk: number;
  count: number;
  sumRisk: number;
  band: RiskBand;
}

/** Agregasi alert per hari, diurutkan naik secara kronologis. */
export function byDay(alerts: Alert[]): DayAgg[] {
  const map = new Map<string, { maxRisk: number; count: number; sumRisk: number }>();
  for (const a of alerts) {
    const cur = map.get(a.day);
    if (cur) {
      cur.maxRisk = Math.max(cur.maxRisk, a.risk);
      cur.sumRisk += a.risk;
      cur.count += 1;
    } else {
      map.set(a.day, { maxRisk: a.risk, sumRisk: a.risk, count: 1 });
    }
  }
  return [...map.entries()]
    .map(([day, v]) => ({
      day,
      maxRisk: v.maxRisk,
      sumRisk: v.sumRisk,
      count: v.count,
      band: riskBand(v.maxRisk),
    }))
    .sort((a, b) => a.day.localeCompare(b.day));
}

export function tierCounts(alerts: Alert[]): { 1: number; 2: number; 3: number } {
  return {
    1: alerts.filter((a) => a.tier === 1).length,
    2: alerts.filter((a) => a.tier === 2).length,
    3: alerts.filter((a) => a.tier === 3).length,
  };
}

export interface UserAgg {
  user: string;
  count: number;
  maxRisk: number;
}

export function topUsers(alerts: Alert[], n = 5): UserAgg[] {
  const map = new Map<string, UserAgg>();
  for (const a of alerts) {
    const cur = map.get(a.user);
    if (cur) {
      cur.count += 1;
      cur.maxRisk = Math.max(cur.maxRisk, a.risk);
    } else {
      map.set(a.user, { user: a.user, count: 1, maxRisk: a.risk });
    }
  }
  return [...map.values()]
    .sort((a, b) => b.maxRisk - a.maxRisk || b.count - a.count)
    .slice(0, n);
}

export function explainCounts(alerts: Alert[]): { method: string; count: number }[] {
  const map = new Map<string, number>();
  for (const a of alerts) map.set(a.explain_method, (map.get(a.explain_method) ?? 0) + 1);
  return [...map.entries()]
    .map(([method, count]) => ({ method, count }))
    .sort((a, b) => b.count - a.count);
}

export interface DayBandAgg {
  day: string;
  total: number;
  critical: number;
  moderate: number;
  low: number;
}

/**
 * Jumlah alert per hari per band risiko (untuk stacked bar chart).
 * Band ≡ tier (ambang 0.60/0.85 sama): critical=tier3, moderate=tier2, low=tier1.
 */
export function byDayBand(alerts: Alert[]): DayBandAgg[] {
  const map = new Map<string, DayBandAgg>();
  for (const a of alerts) {
    let cur = map.get(a.day);
    if (!cur) {
      cur = { day: a.day, total: 0, critical: 0, moderate: 0, low: 0 };
      map.set(a.day, cur);
    }
    cur.total += 1;
    const band = riskBand(a.risk);
    if (band === "high") cur.critical += 1;
    else if (band === "mid") cur.moderate += 1;
    else cur.low += 1;
  }
  return [...map.values()].sort((a, b) => a.day.localeCompare(b.day));
}

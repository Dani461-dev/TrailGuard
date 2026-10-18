export interface TierStyle {
  bar: string;
  badge: string;
  text: string;
  label: string;
}

export const TIER_STYLE: Record<number, TierStyle> = {
  1: {
    bar: "border-l-zinc-500",
    badge: "bg-zinc-500/15 text-zinc-300",
    text: "text-zinc-300",
    label: "log_only",
  },
  2: {
    bar: "border-l-amber-400",
    badge: "bg-amber-400/15 text-amber-300",
    text: "text-amber-300",
    label: "step_up_verification",
  },
  3: {
    bar: "border-l-secondary",
    badge: "bg-secondary/15 text-secondary",
    text: "text-secondary",
    label: "analyst_ticket",
  },
};

export function tierStyle(tier: number): TierStyle {
  return TIER_STYLE[tier] ?? TIER_STYLE[1];
}

export const EXPLAIN_TONE: Record<string, string> = {
  shap: "bg-emerald-400/15 text-emerald-300",
  shapley: "bg-primary/15 text-primary",
  deviation: "bg-amber-400/15 text-amber-300",
};

export function explainTone(method: string): string {
  return EXPLAIN_TONE[method] ?? "bg-white/5 text-text";
}

export function shortUser(user: string): string {
  return user.slice(0, 8);
}

export function fmtPct(v: number | undefined | null): string {
  return typeof v === "number" ? `${Math.round(v * 100)}%` : "—";
}

export function fmtNum(v: number | undefined | null): string {
  return typeof v === "number" ? v.toLocaleString("id-ID") : "—";
}

export type RiskBand = "high" | "mid" | "low";

export function riskBand(risk: number): RiskBand {
  if (risk >= 0.85) return "high";
  if (risk >= 0.6) return "mid";
  return "low";
}

/** Hex accent colors, for SVG & text. */
export const RISK_COLOR: Record<RiskBand, string> = {
  high: "#FF5353",
  mid: "#fbbf24",
  low: "#60a5fa",
};

export const RISK_TEXT: Record<RiskBand, string> = {
  high: "text-secondary",
  mid: "text-amber-300",
  low: "text-primary",
};

export function riskPct(risk: number): number {
  return Math.max(0, Math.min(100, Math.round(risk * 100)));
}

/** Gabung className, abaikan nilai falsy. */
export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

export const RISK_LABEL: Record<RiskBand, string> = {
  high: "critical",
  mid: "moderate",
  low: "low",
};

const BULAN = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "Mei",
  "Jun",
  "Jul",
  "Agu",
  "Sep",
  "Okt",
  "Nov",
  "Des",
];

/** "2010-03-03" → "3 Mar 2010" */
export function fmtDate(day: string): string {
  const [y, m, d] = day.split("-").map(Number);
  if (!y || !m || !d) return day;
  return `${d} ${BULAN[m - 1]} ${y}`;
}

/** "2010-03-03" → "3 Mar" */
export function fmtShortDate(day: string): string {
  const [, m, d] = day.split("-").map(Number);
  if (!m || !d) return day;
  return `${d} ${BULAN[m - 1]}`;
}

/** Boolean → approval status label. */
export function approvalLabel(requires: boolean): string {
  return requires ? "Needs approval" : "Automatic";
}


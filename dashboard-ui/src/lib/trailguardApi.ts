/**
 * TrailGuard dashboard API client.
 * Fetches from Flask (/api/...) when available; otherwise uses sample data (fallback)
 * and tags the source as 'live' | 'sample' so the dashboard stays honest.
 */

export const API_BASE: string =
  (import.meta.env.PUBLIC_API_URL as string | undefined) ?? "";

export interface Reason {
  feature: string;
  label: string;
  value: number;
  contribution?: number;
  z?: number;
}

export interface Alert {
  user: string;
  day: string;
  risk: number;
  label?: number;
  reasons: Reason[];
  explain_method: "shap" | "shapley" | "deviation" | string;
  tier: number;
  action: string;
  requires_human_approval: boolean;
  note?: string;
  summary: string;
}

export interface Metrics {
  alert_budget_per_day?: number;
  n_alerts?: number;
  n_malicious_user_days?: number;
  true_positive_alerts?: number;
  precision_at_budget?: number;
  recall_at_budget?: number;
  insiders_in_test?: number;
  insiders_detected?: number;
  median_days_to_detection?: number | null;
}

export interface Decision {
  ts: string;
  user: string;
  day: string;
  decision: "approve" | "reject";
  note?: string;
  risk?: number;
  tier?: number;
}

export interface ConfigInfo {
  dataset: string;
  explain_method_target?: string;
  policy: { step_up_threshold: number; ticket_threshold: number };
  alert_budget_per_day: number;
  has_alerts: boolean;
  has_metrics: boolean;
}

export interface ReplayEvent {
  ts: string;
  user: string;
  host: string;
  source: string;
  action: string;
  target: string;
  size: string;
}

export type Source = "live" | "sample";

export interface Result<T> {
  data: T;
  source: Source;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) throw new Error(`API ${path} -> ${res.status}`);
  return (await res.json()) as T;
}

// ─── Sample data (fallback) ─────────────────────────────────────────────────

const SAMPLE_ALERTS: Alert[] = [
  {
    user: "7f3ce1b2c497fb5c",
    day: "2010-03-03",
    risk: 0.92,
    label: 1,
    explain_method: "shap",
    tier: 3,
    action: "analyst_ticket",
    requires_human_approval: true,
    note: "Create an analyst ticket; follow-up actions require human approval.",
    reasons: [
      { feature: "n_new_domain", label: "new web domains", value: 7, contribution: 0.31 },
      { feature: "n_usb_connect", label: "USB usage", value: 3, contribution: 0.24 },
      { feature: "n_offhours_logon", label: "off-hours logons", value: 5, contribution: 0.18 },
    ],
    summary:
      "User 7f3ce1b2… on 2010-03-03 has risk 0.92 (tier 3: analyst_ticket). Main causes: new web domains (value 7, adds risk +0.31); USB usage (value 3, adds risk +0.24); off-hours logons (value 5, adds risk +0.18). Requires analyst approval.",
  },
  {
    user: "a91b0d7e6c2f4410",
    day: "2010-03-04",
    risk: 0.71,
    label: 0,
    explain_method: "shapley",
    tier: 2,
    action: "step_up_verification",
    requires_human_approval: false,
    note: "Request additional verification on the next session.",
    reasons: [
      { feature: "email_ext_bytes", label: "outbound email volume", value: 1400000, contribution: 0.33 },
      { feature: "n_new_host", label: "never-seen computer", value: 2, contribution: 0.19 },
    ],
    summary:
      "User a91b0d7e… on 2010-03-04 has risk 0.71 (tier 2: step_up_verification). Main causes: outbound email volume (value 1400000, adds risk +0.33); a never-seen computer (value 2, adds risk +0.19).",
  },
  {
    user: "0c48be1fa7d93e55",
    day: "2010-03-05",
    risk: 0.48,
    label: 0,
    explain_method: "deviation",
    tier: 1,
    action: "log_only",
    requires_human_approval: false,
    note: "Log only.",
    reasons: [
      { feature: "n_http", label: "web visits", value: 42, z: 2.1 },
      { feature: "n_file_ops", label: "file operations", value: 130, z: 1.3 },
    ],
    summary:
      "User 0c48be1f… on 2010-03-05 has risk 0.48 (tier 1: log_only). Main causes: web visits (42, +2.1 SD from habit); file operations (130, +1.3 SD from habit).",
  },
];

const SAMPLE_METRICS: Metrics = {
  alert_budget_per_day: 5,
  n_alerts: 45,
  n_malicious_user_days: 18,
  true_positive_alerts: 12,
  precision_at_budget: 0.27,
  recall_at_budget: 0.67,
  insiders_in_test: 4,
  insiders_detected: 3,
  median_days_to_detection: 2,
};

const SAMPLE_CONFIG: ConfigInfo = {
  dataset: "cert",
  explain_method_target: "shap",
  policy: { step_up_threshold: 0.6, ticket_threshold: 0.85 },
  alert_budget_per_day: 5,
  has_alerts: false,
  has_metrics: false,
};

const SAMPLE_EVENTS: ReplayEvent[] = [
  { ts: "2010-03-03 02:14", user: "7f3ce1b2c497fb5c", host: "9c2a1e77", source: "logon", action: "logon", target: "", size: "0" },
  { ts: "2010-03-03 02:19", user: "7f3ce1b2c497fb5c", host: "9c2a1e77", source: "device", action: "connect", target: "usb", size: "0" },
  { ts: "2010-03-03 02:31", user: "7f3ce1b2c497fb5c", host: "9c2a1e77", source: "file", action: "file_op", target: ".zip", size: "0" },
  { ts: "2010-03-03 02:44", user: "7f3ce1b2c497fb5c", host: "9c2a1e77", source: "http", action: "visit", target: "dyn-dns.example", size: "0" },
  { ts: "2010-03-03 03:02", user: "7f3ce1b2c497fb5c", host: "9c2a1e77", source: "email", action: "email_ext", target: "gmail.com", size: "4200000" },
  { ts: "2010-03-04 09:12", user: "a91b0d7e6c2f4410", host: "1f0b77aa", source: "logon", action: "logon", target: "", size: "0" },
  { ts: "2010-03-04 09:40", user: "a91b0d7e6c2f4410", host: "1f0b77aa", source: "email", action: "email_ext", target: "dropbox.com", size: "1400000" },
];

// ─── API publik ─────────────────────────────────────────────────────────────

export async function fetchAlerts(): Promise<Result<Alert[]>> {
  try {
    const data = await getJson<Alert[]>("/api/alerts?limit=100");
    if (Array.isArray(data) && data.length > 0) return { data, source: "live" };
    return { data: SAMPLE_ALERTS, source: "sample" };
  } catch {
    return { data: SAMPLE_ALERTS, source: "sample" };
  }
}

export async function fetchMetrics(): Promise<Result<Metrics>> {
  try {
    const data = await getJson<Metrics>("/api/metrics");
    if (data && Object.keys(data).length > 0) return { data, source: "live" };
    return { data: SAMPLE_METRICS, source: "sample" };
  } catch {
    return { data: SAMPLE_METRICS, source: "sample" };
  }
}

export async function fetchConfig(): Promise<Result<ConfigInfo>> {
  try {
    const data = await getJson<ConfigInfo>("/api/config");
    if (data && data.dataset) return { data, source: "live" };
    return { data: SAMPLE_CONFIG, source: "sample" };
  } catch {
    return { data: SAMPLE_CONFIG, source: "sample" };
  }
}

export async function fetchDecisions(): Promise<Result<Decision[]>> {
  try {
    const data = await getJson<Decision[]>("/api/decisions");
    return { data: Array.isArray(data) ? data : [], source: "live" };
  } catch {
    return { data: [], source: "sample" };
  }
}

export async function fetchReplay(
  limit = 200,
): Promise<Result<{ events: ReplayEvent[]; available: boolean }>> {
  try {
    const data = await getJson<{ events: ReplayEvent[]; available: boolean }>(
      `/api/replay?limit=${limit}`,
    );
    if (data.available && data.events.length > 0) return { data, source: "live" };
    return { data: { events: SAMPLE_EVENTS, available: false }, source: "sample" };
  } catch {
    return { data: { events: SAMPLE_EVENTS, available: false }, source: "sample" };
  }
}

export async function postDecision(
  body: Pick<Decision, "user" | "day" | "decision"> &
    Partial<Pick<Decision, "note" | "risk" | "tier">>,
): Promise<{ ok: boolean; offline?: boolean }> {
  try {
    const res = await fetch(`${API_BASE}/api/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = (await res.json()) as { ok?: boolean };
    return { ok: Boolean(data.ok) };
  } catch {
    return { ok: false, offline: true };
  }
}

// ─── Streaming replay (SSE) ────────────────────────────────────────────────

export interface StreamHandlers {
  onEvent?: (e: ReplayEvent) => void;
  onAlert?: (a: Alert) => void;
  onEnd?: () => void;
  onError?: () => void;
}

/**
 * Buka stream SSE /api/replay/stream (dipace server, memakai replay() backend).
 * Mengembalikan fungsi penutup. Fallback: bila API mati, pemanggil beralih ke
 * fetchReplay() + timer klien (mode pratinjau).
 */
export function openReplayStream(
  opts: { speedup?: number; limit?: number },
  handlers: StreamHandlers,
): () => void {
  const speedup = opts.speedup ?? 100;
  const limit = opts.limit ?? 1000;
  const es = new EventSource(
    `${API_BASE}/api/replay/stream?speedup=${speedup}&limit=${limit}`,
  );
  es.addEventListener("event", (ev) => {
    try {
      handlers.onEvent?.(JSON.parse((ev as MessageEvent).data) as ReplayEvent);
    } catch {
      /* ignore */
    }
  });
  es.addEventListener("alert", (ev) => {
    try {
      handlers.onAlert?.(JSON.parse((ev as MessageEvent).data) as Alert);
    } catch {
      /* ignore */
    }
  });
  es.addEventListener("end", () => {
    es.close();
    handlers.onEnd?.();
  });
  es.onerror = () => {
    // EventSource reconnect otomatis -> restart replay dari awal tiap 3 dtk.
    // Tutup agar tidak membanjiri; UI memakai fallback pratinjau bila perlu.
    es.close();
    handlers.onError?.();
  };
  return () => es.close();
}

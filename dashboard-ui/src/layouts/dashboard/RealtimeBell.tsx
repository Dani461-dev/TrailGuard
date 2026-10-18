import React, { useEffect, useState } from "react";
import { API_BASE, type Alert } from "@/lib/trailguardApi";
import Icon from "./Icon";
import { toast } from "./primitives";
import { cn, fmtDate, RISK_COLOR, riskBand, shortUser, tierStyle } from "./ui";

type ChannelState = "connecting" | "live" | "offline";

const MAX_ITEMS = 12;
const SWEEP_INTERVAL_MS = 5 * 60 * 1000; // sapuan ulang berkala (menangkap alerts.jsonl yang diperbarui)
const MAX_TOASTS_PER_SWEEP = 3;

/**
 * Realtime alert notifications for the whole dashboard.
 * Listens to the backend SSE stream (alerts_only): one full sweep per connect,
 * deduped across sweeps, then re-sweeps periodically. Offline/sample mode:
 * stays silent and honestly labeled (preview).
 */
export default function RealtimeBell() {
  const [items, setItems] = useState<Alert[]>([]);
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<ChannelState>("connecting");

  useEffect(() => {
    let es: EventSource | null = null;
    let retry: number | undefined;
    const seen = new Set<string>();
    let toasts = 0;

    const connect = () => {
      toasts = 0;
      es = new EventSource(
        `${API_BASE}/api/replay/stream?alerts_only=1&speedup=0&limit=100000`,
      );
      es.onopen = () => setState("live");
      es.onerror = () => {
        es?.close();
        setState("offline");
        retry = window.setTimeout(connect, SWEEP_INTERVAL_MS);
      };
      es.addEventListener("end", () => {
        // Stream selesai — TUTUP (EventSource reconnect otomatis = badai request).
        es?.close();
        setState("live");
        retry = window.setTimeout(connect, SWEEP_INTERVAL_MS);
      });
      es.addEventListener("alert", (ev) => {
        try {
          const a = JSON.parse((ev as MessageEvent).data) as Alert;
          if (!a || typeof a.risk !== "number") return;
          const id = `${a.user}|${a.day}`;
          setState("live");
          if (seen.has(id)) return; // dedupe antar sapuan
          seen.add(id);
          setItems((prev) => [a, ...prev].slice(0, MAX_ITEMS));
          setUnread((u) => u + 1);
          // Toast terbatas (tier-3 saja) agar sapuan awal tidak membanjiri.
          if (a.tier === 3 && toasts < MAX_TOASTS_PER_SWEEP) {
            toasts += 1;
            toast(
              `Tier-3 alert — user ${shortUser(a.user)} (${a.risk.toFixed(2)})`,
              "err",
            );
          }
        } catch {
          /* ignore malformed payload */
        }
      });
    };

    connect();
    return () => {
      es?.close();
      if (retry) window.clearTimeout(retry);
    };
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const live = state === "live";

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => {
          setOpen((v) => !v);
          setUnread(0);
        }}
        aria-label="Realtime alerts"
        title={
          live
            ? "Realtime alert notifications (replay stream)"
            : "Realtime notifications unavailable — backend offline (preview mode)"
        }
        className={cn(
          "relative grid size-9 place-items-center rounded-lg border transition",
          live
            ? "border-emerald-400/40 text-emerald-300 hover:bg-emerald-400/10"
            : "border-border text-text-dark hover:border-primary/40 hover:text-text",
        )}
      >
        <Icon name="bell" className="size-4" />
        {unread > 0 && (
          <span className="absolute -right-1 -top-1 grid min-w-4 place-items-center rounded-full bg-secondary px-1 text-[0.6rem] font-bold leading-4 text-white shadow">
            {unread > 99 ? "99+" : unread}
          </span>
        )}
        <span
          className={cn(
            "absolute -bottom-0.5 left-1/2 size-1.5 -translate-x-1/2 rounded-full",
            live ? "animate-pulse bg-emerald-400" : state === "connecting" ? "bg-amber-400" : "bg-zinc-600",
          )}
        />
      </button>

      {open && (
        <div className="dr-fade absolute right-0 top-full z-40 mt-2 w-80 overflow-hidden rounded-2xl border border-border bg-light/95 shadow-2xl backdrop-blur">
          <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
            <p className="text-xs font-semibold uppercase tracking-wide text-text-dark">
              Realtime alerts
            </p>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[0.62rem] font-semibold",
                live
                  ? "bg-emerald-400/15 text-emerald-300"
                  : state === "connecting"
                    ? "bg-amber-400/15 text-amber-300"
                    : "bg-white/5 text-text-dark",
              )}
            >
              {live ? "live" : state === "connecting" ? "connecting…" : "preview"}
            </span>
          </div>

          {items.length === 0 ? (
            <p className="px-4 py-8 text-center text-xs text-text-dark">
              {live
                ? "Listening — alerts appear here as the stream reaches them."
                : "Backend offline — notifications are disabled (sample mode)."}
            </p>
          ) : (
            <ul className="dr-scroll max-h-96 overflow-y-auto">
              {items.map((a, i) => {
                const s = tierStyle(a.tier);
                return (
                  <li key={`${a.user}|${a.day}|${i}`}>
                    <a
                      href="/dashboard/alerts"
                      onClick={() => setOpen(false)}
                      className="flex items-center gap-3 border-b border-border/50 px-4 py-2.5 transition last:border-0 hover:bg-white/[0.03]"
                    >
                      <span
                        className="size-2 shrink-0 rounded-full"
                        style={{ background: RISK_COLOR[riskBand(a.risk)] }}
                      />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-mono text-xs text-text-light">
                          user {shortUser(a.user)}
                        </span>
                        <span className="block truncate text-[0.68rem] text-text-dark">
                          {fmtDate(a.day)} ·{" "}
                          <span className={`rounded px-1 ${s.badge}`}>tier {a.tier}</span>
                        </span>
                      </span>
                      <span className="font-mono text-xs text-white">
                        {a.risk.toFixed(2)}
                      </span>
                    </a>
                  </li>
                );
              })}
            </ul>
          )}

          <p className="border-t border-border px-4 py-2 text-[0.62rem] text-text-dark">
            Replay-derived alerts (historical playback, deduped, re-swept periodically) — not a live IDS feed.
          </p>
        </div>
      )}
    </div>
  );
}

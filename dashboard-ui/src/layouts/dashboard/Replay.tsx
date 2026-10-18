import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  fetchReplay,
  openReplayStream,
  type Alert,
  type ReplayEvent,
  type Source,
} from "@/lib/trailguardApi";
import Icon from "./Icon";
import { Badge, Button, Card, Segmented, toast } from "./primitives";
import { cn, fmtDate, RISK_COLOR, riskBand, shortUser, tierStyle } from "./ui";

const EVENT_TONE: Record<string, string> = {
  logon: "text-emerald-300",
  logoff: "text-emerald-300/70",
  connect: "text-amber-300",
  disconnect: "text-amber-300/70",
  file_op: "text-primary",
  visit: "text-sky-300",
  email_ext: "text-secondary",
  email_int: "text-text-light",
};

/** kecepatan mode pratinjau (delay klien, ms/event) */
const PREVIEW_SPEEDS = [
  { key: "0", label: "0.5×", ms: 700 },
  { key: "1", label: "1×", ms: 350 },
  { key: "2", label: "2×", ms: 175 },
  { key: "3", label: "4×", ms: 90 },
];

/** kecepatan mode stream (speedup server: 1 dtk nyata = N dtk log) */
const STREAM_SPEEDS = [
  { key: "0", label: "0.5×", speedup: 50 },
  { key: "1", label: "1×", speedup: 100 },
  { key: "2", label: "2×", speedup: 400 },
  { key: "3", label: "4×", speedup: 1000 },
];

const STREAM_LIMIT = 5000;

function EventRow({ e }: { e: ReplayEvent }) {
  return (
    <li className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-xl border border-border bg-body/40 px-4 py-2.5 text-sm">
      <span className="font-mono text-xs text-text-dark">{e.ts.slice(11, 16) || e.ts}</span>
      <span className="font-mono text-xs text-text-light">user {e.user.slice(0, 8)}</span>
      <span
        className={cn(
          "font-mono text-xs font-semibold",
          EVENT_TONE[e.action] ?? "text-text",
        )}
      >
        {e.source}/{e.action}
      </span>
      {e.target && <span className="font-mono text-xs text-text-dark">→ {e.target}</span>}
      {e.size && e.size !== "0" && (
        <span className="ml-auto font-mono text-[0.68rem] text-text-dark">
          {Number(e.size).toLocaleString("id-ID")} bytes
        </span>
      )}
    </li>
  );
}

export default function Replay() {
  const [events, setEvents] = useState<ReplayEvent[]>([]);
  const [source, setSource] = useState<Source>("sample");
  const [available, setAvailable] = useState(false);
  const [loading, setLoading] = useState(true);

  // mode: "stream" = SSE dipace server (live), "preview" = timer klien (fallback)
  const [mode, setMode] = useState<"stream" | "preview">("stream");

  // state mode stream
  const [streaming, setStreaming] = useState(false);
  const [streamed, setStreamed] = useState<ReplayEvent[]>([]);
  const [streamAlerts, setStreamAlerts] = useState<Alert[]>([]);
  const [streamEnded, setStreamEnded] = useState(false);
  const [streamSpeed, setStreamSpeed] = useState("1");
  const closeStream = useRef<(() => void) | null>(null);

  // state mode pratinjau (timer klien)
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [previewSpeed, setPreviewSpeed] = useState("1");
  const timer = useRef<number | null>(null);

  // ── muat daftar event awal (untuk pratinjau & deteksi ketersediaan) ──
  useEffect(() => {
    let alive = true;
    fetchReplay(200).then((res) => {
      if (!alive) return;
      setEvents(res.data.events);
      setAvailable(res.data.available);
      setSource(res.source);
      setMode(res.source === "live" ? "stream" : "preview");
      setLoading(false);
    });
    return () => {
      alive = false;
    };
  }, []);

  // ── mode stream (SSE) ──
  const stopStream = useCallback(() => {
    closeStream.current?.();
    closeStream.current = null;
    setStreaming(false);
  }, []);

  const startStream = useCallback(
    (speedKey = streamSpeed) => {
      closeStream.current?.();
      const sp = STREAM_SPEEDS.find((s) => s.key === speedKey) ?? STREAM_SPEEDS[1];
      setStreamed([]);
      setStreamAlerts([]);
      setStreamEnded(false);
      setStreaming(true);
      closeStream.current = openReplayStream(
        { speedup: sp.speedup, limit: STREAM_LIMIT },
        {
          onEvent: (e) => setStreamed((prev) => [...prev, e]),
          onAlert: (a) => {
            setStreamAlerts((prev) => [a, ...prev]);
            toast(
              `Tier-${a.tier} alert in replay — user ${shortUser(a.user)} (${a.risk.toFixed(2)})`,
              a.tier === 3 ? "err" : a.tier === 2 ? "info" : "ok",
            );
          },
          onEnd: () => {
            setStreaming(false);
            setStreamEnded(true);
            toast("Replay stream finished.", "info");
          },
          onError: () => {
            /* EventSource menyambung ulang otomatis; biarkan */
          },
        },
      );
    },
    [streamSpeed],
  );

  useEffect(() => () => closeStream.current?.(), []);

  const changeStreamSpeed = (key: string) => {
    setStreamSpeed(key);
    if (streaming) {
      startStream(key);
      const sp = STREAM_SPEEDS.find((s) => s.key === key);
      toast(`Stream restarted at ${sp?.label ?? "1×"} (server pacing).`, "info");
    }
  };

  // ── mode pratinjau (timer klien) ──
  const stopPreview = useCallback(() => {
    if (timer.current) window.clearInterval(timer.current);
    timer.current = null;
    setPlaying(false);
  }, []);

  const previewSpeedIdx = PREVIEW_SPEEDS.findIndex((s) => s.key === previewSpeed);

  useEffect(() => {
    if (!playing) return;
    timer.current = window.setInterval(() => {
      setIndex((i) => {
        if (i >= events.length) {
          stopPreview();
          return i;
        }
        return i + 1;
      });
    }, PREVIEW_SPEEDS[previewSpeedIdx].ms);
    return () => {
      if (timer.current) window.clearInterval(timer.current);
    };
  }, [playing, events.length, stopPreview, previewSpeedIdx]);

  const previewVisible = useMemo(() => events.slice(0, index), [events, index]);
  const previewDone = index >= events.length && events.length > 0;
  const live = source === "live";

  const counts = useMemo(() => {
    const m = new Map<string, number>();
    const src = mode === "stream" ? streamed : events;
    for (const e of src) m.set(e.source, (m.get(e.source) ?? 0) + 1);
    return [...m.entries()].sort((a, b) => b[1] - a[1]);
  }, [mode, streamed, events]);

  // feed yang ditampilkan
  const feed = mode === "stream" ? streamed : previewVisible;
  const total = mode === "stream" ? streamed.length : index;
  const totalKnown = mode === "preview" ? events.length : STREAM_LIMIT;

  const primaryClick = () => {
    if (mode === "stream") {
      if (streaming) stopStream();
      else startStream();
    } else {
      if (playing) stopPreview();
      else {
        if (previewDone) setIndex(0);
        setPlaying(true);
      }
    }
  };

  const primaryLabel =
    mode === "stream"
      ? streaming
        ? "Stop"
        : streamEnded
          ? "Replay from start"
          : "Play (live stream)"
      : playing
        ? "Pause"
        : previewDone
          ? "Restart"
          : "Play";

  return (
    <div className="space-y-5">
      <Card className="dr-in overflow-hidden">
        {/* toolbar */}
        <div className="flex flex-wrap items-center gap-3 border-b border-border px-5 py-3">
          <Badge tone="secondary">REPLAY</Badge>
          <Badge tone={live ? "emerald" : "amber"}>
            <span
              className={cn(
                "size-1.5 rounded-full",
                live ? "animate-pulse bg-emerald-400" : "bg-amber-400",
              )}
            />
            {live ? "Live · Flask API" : "Preview · sample"}
          </Badge>

          {live && (
            <Segmented
              value={mode}
              onChange={(k) => {
                if (streaming) stopStream();
                if (playing) stopPreview();
                setMode(k as "stream" | "preview");
              }}
              options={[
                { key: "stream", label: "Server stream" },
                { key: "preview", label: "Local preview" },
              ]}
            />
          )}

          <div className="ml-auto flex flex-wrap items-center gap-3">
            <Button
              variant="primary"
              size="sm"
              icon={mode === "stream" ? (streaming ? "x" : "play") : playing ? "x" : "play"}
              disabled={loading || (mode === "preview" && events.length === 0)}
              onClick={primaryClick}
            >
              {primaryLabel}
            </Button>

            {mode === "preview" ? (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={loading || events.length === 0}
                  onClick={() => {
                    stopPreview();
                    setIndex(events.length);
                  }}
                >
                  Jump to end
                </Button>
                <Segmented
                  value={previewSpeed}
                  onChange={setPreviewSpeed}
                  options={PREVIEW_SPEEDS.map((s) => ({ key: s.key, label: s.label }))}
                />
              </>
            ) : (
              <Segmented
                value={streamSpeed}
                onChange={changeStreamSpeed}
                options={STREAM_SPEEDS.map((s) => ({ key: s.key, label: s.label }))}
              />
            )}

            <span className="font-mono text-xs text-text-dark">
              {total}/{mode === "stream" ? `${totalKnown}+` : totalKnown}{" "}
              {mode === "stream" ? "streamed" : "event"}
            </span>
          </div>
        </div>

        {/* progress */}
        <div className="relative h-1 w-full overflow-hidden bg-white/5">
          {mode === "stream" ? (
            streaming ? (
              <div className="h-full w-1/3 animate-pulse bg-gradient-to-r from-transparent via-primary to-transparent" />
            ) : (
              <div
                className="h-full bg-gradient-to-r from-primary to-secondary transition-[width] duration-300"
                style={{ width: streamEnded ? "100%" : "0%" }}
              />
            )
          ) : (
            <div
              className="h-full bg-gradient-to-r from-primary to-secondary transition-[width] duration-200"
              style={{ width: `${events.length ? (index / events.length) * 100 : 0}%` }}
            />
          )}
        </div>

        {/* counters */}
        {!loading && feed.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 border-b border-border px-5 py-3">
            {counts.map(([src, n]) => (
              <span
                key={src}
                className="inline-flex items-center gap-2 rounded-full border border-border bg-body/40 px-3 py-1 text-[0.7rem] text-text-dark"
              >
                <span className="text-text-light">{src}</span>
                <span className="font-mono">{n}</span>
              </span>
            ))}
            {mode === "stream" && streamAlerts.length > 0 && (
              <span className="ml-auto inline-flex items-center gap-2 text-[0.7rem] text-text-dark">
                <Icon name="bell" className="size-3.5 text-secondary" />
                <span className="font-mono text-secondary">{streamAlerts.length}</span>
                alerts detected
              </span>
            )}
          </div>
        )}

        {/* alerts yang terdeteksi saat stream */}
        {mode === "stream" && streamAlerts.length > 0 && (
          <div className="border-b border-border bg-secondary/[0.04] px-5 py-3">
            <p className="mb-2 text-[0.68rem] font-semibold uppercase tracking-wide text-text-dark">
              Alerts detected during replay
            </p>
            <ul className="flex flex-wrap gap-2">
              {streamAlerts.map((a, i) => {
                const s = tierStyle(a.tier);
                return (
                  <li
                    key={`${a.user}|${a.day}|${i}`}
                    className="dr-in inline-flex items-center gap-2 rounded-lg border border-border bg-body/50 px-3 py-1.5 text-xs"
                  >
                    <span
                      className="size-2 rounded-full"
                      style={{ background: RISK_COLOR[riskBand(a.risk)] }}
                    />
                    <span className="font-mono text-text-light">user {shortUser(a.user)}</span>
                    <span className="text-text-dark">{fmtDate(a.day)}</span>
                    <span className={`rounded px-1.5 py-0.5 font-semibold ${s.badge}`}>
                      tier {a.tier}
                    </span>
                    <span className="font-mono text-white">{a.risk.toFixed(2)}</span>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {/* feed */}
        <div className="dr-scroll max-h-[60vh] overflow-y-auto p-5">
          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="h-11 animate-pulse rounded-xl bg-white/[0.04]" />
              ))}
            </div>
          ) : feed.length === 0 ? (
            <div className="flex flex-col items-center px-6 py-14 text-center">
              <span className="mb-4 grid size-14 place-items-center rounded-2xl border border-border bg-body/50 text-primary/70">
                <Icon name="route" className="size-6" />
              </span>
              <p className="font-secondary text-base font-bold text-white">
                {mode === "stream" && streaming
                  ? "Connecting to the stream…"
                  : "No events to play yet"}
              </p>
              {!live && (
                <code className="mt-3 inline-block rounded-lg bg-body px-4 py-2 font-mono text-sm text-primary">
                  make toy
                </code>
              )}
            </div>
          ) : (
            <ol className="space-y-1.5">
              {feed
                .slice()
                .reverse()
                .map((e, i) => {
                  const idx = feed.length - 1 - i;
                  const prev = idx > 0 ? feed[idx - 1] : null;
                  const showDay = !prev || prev.ts.slice(0, 10) !== e.ts.slice(0, 10);
                  return (
                    <React.Fragment key={`${e.ts}-${idx}`}>
                      {showDay && (
                        <li className="pt-3 pb-1 text-[0.68rem] font-semibold uppercase tracking-wide text-text-dark">
                          {e.ts.slice(0, 10)}
                        </li>
                      )}
                      <EventRow e={e} />
                    </React.Fragment>
                  );
                })}
            </ol>
          )}
        </div>
      </Card>

      <div className="space-y-2 text-xs text-text-dark">
        <p>
          {mode === "stream"
            ? "Server-paced replay (SSE): the backend paces events with replay() — honestly a replay, not real streaming."
            : "Local preview: the browser paces a sample fetched from the API."}
        </p>
        <p>Pseudonymized events (Contract #1). Real IDs are never shown.</p>
        {!available && !loading && (
          <p>
            Real event data is not available yet — this is a sample. For real data:{" "}
            <code className="font-mono text-text">python -m trailguard.pipeline ingest</code>{" "}
            then reload.
          </p>
        )}
      </div>
    </div>
  );
}

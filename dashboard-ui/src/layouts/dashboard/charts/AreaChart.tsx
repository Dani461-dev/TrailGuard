import React, { useId, useState } from "react";
import { fmtDate } from "../ui";

export interface AreaPoint {
  day: string;
  value: number;
  count: number;
}

export interface Threshold {
  value: number;
  label: string;
  color: string;
}

interface Props {
  series: AreaPoint[];
  thresholds?: Threshold[];
  color?: string;
}

const W = 820;
const H = 260;
const PAD = { top: 18, right: 58, bottom: 34, left: 42 };

const DEFAULT_TH: Threshold[] = [
  { value: 0.85, label: "tiket", color: "#FF5353" },
  { value: 0.6, label: "step-up", color: "#fbbf24" },
];

/** Grafik area: skor risiko maksimum per hari + ambang policy. */
export default function AreaChart({
  series,
  thresholds = DEFAULT_TH,
  color = "#937AFF",
}: Props) {
  const gid = useId().replace(/[:]/g, "");
  const [hover, setHover] = useState<number | null>(null);

  if (!series || series.length === 0) {
    return (
      <p className="py-16 text-center text-sm text-text-dark">
        Belum ada data harian.
      </p>
    );
  }

  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;
  const n = series.length;
  const step = n > 1 ? innerW / (n - 1) : 0;

  const x = (i: number) => PAD.left + (n > 1 ? i * step : innerW / 2);
  const y = (v: number) => PAD.top + innerH * (1 - Math.max(0, Math.min(1, v)));

  const line = series
    .map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`)
    .join(" ");
  const area = `${line} L${x(n - 1).toFixed(1)},${y(0).toFixed(1)} L${x(0).toFixed(1)},${y(0).toFixed(1)} Z`;

  const labelEvery = Math.max(1, Math.ceil(n / 8));
  const hoverP = hover !== null ? series[hover] : null;

  return (
    <div className="relative">
      {/* tooltip */}
      {hoverP && (
        <div
          className="pointer-events-none absolute -top-1 z-10 -translate-x-1/2 rounded-lg border border-border bg-body/95 px-3 py-2 text-xs shadow-xl backdrop-blur"
          style={{ left: `${(x(hover!) / W) * 100}%` }}
        >
          <p className="font-medium text-white">{fmtDate(hoverP.day)}</p>
          <p className="mt-0.5 font-mono text-text-dark">
            max risk{" "}
            <span className="text-text">{hoverP.value.toFixed(2)}</span> ·{" "}
            {hoverP.count} alert
          </p>
        </div>
      )}

      <svg
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        role="img"
        aria-label="Skor risiko maksimum per hari"
        className="overflow-visible"
      >
        <defs>
          <linearGradient id={`a-${gid}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.38" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* y grid */}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => (
          <g key={t}>
            <line
              x1={PAD.left}
              x2={W - PAD.right}
              y1={y(t)}
              y2={y(t)}
              stroke="var(--color-border)"
              strokeWidth="1"
              strokeDasharray={t === 0 ? "0" : "3 6"}
            />
            <text
              x={PAD.left - 8}
              y={y(t) + 3}
              textAnchor="end"
              fontSize="10"
              fill="var(--color-text-dark)"
            >
              {t.toFixed(2)}
            </text>
          </g>
        ))}

        {/* thresholds */}
        {thresholds.map((th) => (
          <g key={th.label}>
            <line
              x1={PAD.left}
              x2={W - PAD.right}
              y1={y(th.value)}
              y2={y(th.value)}
              stroke={th.color}
              strokeWidth="1"
              strokeDasharray="5 5"
              strokeOpacity="0.55"
            />
            <text
              x={W - PAD.right + 6}
              y={y(th.value) + 3}
              fontSize="9"
              fill={th.color}
            >
              {th.label}
            </text>
          </g>
        ))}

        {/* area + line */}
        <path d={area} fill={`url(#a-${gid})`} />
        <path
          d={line}
          fill="none"
          stroke={color}
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* points + hover targets */}
        {series.map((p, i) => (
          <g key={p.day}>
            <rect
              x={x(i) - (step || innerW) / 2}
              y={PAD.top}
              width={step || innerW}
              height={innerH}
              fill="transparent"
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
            />
            <circle
              cx={x(i)}
              cy={y(p.value)}
              r={hover === i ? 5 : 3}
              fill="var(--color-body)"
              stroke={color}
              strokeWidth="2"
              opacity={hover === null || hover === i ? 1 : 0.55}
            />
          </g>
        ))}

        {/* x labels */}
        {series.map((p, i) =>
          i % labelEvery === 0 || i === n - 1 ? (
            <text
              key={`x-${p.day}`}
              x={x(i)}
              y={H - 12}
              textAnchor="middle"
              fontSize="9.5"
              fill="var(--color-text-dark)"
            >
              {p.day.slice(5)}
            </text>
          ) : null,
        )}
      </svg>
    </div>
  );
}

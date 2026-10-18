import React, { useState } from "react";

export interface Segment {
  label: string;
  value: number;
  color: string;
}

interface Props {
  segments: Segment[];
  size?: number;
  thickness?: number;
  centerLabel?: string;
}

/** Distribution donut (e.g. tiers) with an interactive legend. */
export default function DonutChart({
  segments,
  size = 176,
  thickness = 22,
  centerLabel = "total",
}: Props) {
  const [hover, setHover] = useState<number | null>(null);

  const total = segments.reduce((s, x) => s + x.value, 0);
  const r = (size - thickness) / 2;
  const c = 2 * Math.PI * r;

  let acc = 0;
  const arcs = segments.map((s) => {
    const frac = total > 0 ? s.value / total : 0;
    const dash = frac * c;
    const arc = { ...s, dash, offset: acc, frac };
    acc += dash;
    return arc;
  });

  const active = hover !== null ? arcs[hover] : null;
  const centerText = active
    ? `${Math.round(active.frac * 100)}%`
    : String(total);

  return (
    <div className="flex flex-col items-center gap-5 sm:flex-row sm:justify-center sm:gap-7">
      <div
        className="relative shrink-0"
        style={{ width: size, height: size }}
        role="img"
        aria-label="Alert distribution by tier"
      >
        <svg viewBox={`0 0 ${size} ${size}`} className="size-full -rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke="var(--color-border)"
            strokeWidth={thickness}
            opacity="0.4"
          />
          {arcs.map((a, i) => (
            <circle
              key={a.label}
              cx={size / 2}
              cy={size / 2}
              r={r}
              fill="none"
              stroke={a.color}
              strokeWidth={hover === i ? thickness + 3 : thickness}
              strokeDasharray={`${Math.max(0, a.dash - 2)} ${c}`}
              strokeDashoffset={-a.offset}
              strokeLinecap="butt"
              opacity={hover === null || hover === i ? 1 : 0.4}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
              className="transition-[stroke-width,opacity]"
            />
          ))}
        </svg>
        <div className="absolute inset-0 grid place-items-center text-center">
          <div>
            <p className="font-secondary text-h5 font-bold leading-none text-white">
              {centerText}
            </p>
            <p className="mt-1 text-[0.66rem] uppercase tracking-wide text-text-dark">
              {active ? active.label : centerLabel}
            </p>
          </div>
        </div>
      </div>

      <ul className="w-full max-w-[15rem] space-y-2">
        {arcs.map((a, i) => (
          <li
            key={a.label}
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(null)}
            className="flex items-center gap-3 rounded-lg px-2 py-1.5 transition hover:bg-white/5"
          >
            <span
              className="size-2.5 rounded-sm"
              style={{ background: a.color }}
            />
            <span className="text-sm text-text">{a.label}</span>
            <span className="ml-auto font-mono text-sm text-white">
              {a.value}
            </span>
            <span className="w-10 text-right font-mono text-xs text-text-dark">
              {Math.round(a.frac * 100)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

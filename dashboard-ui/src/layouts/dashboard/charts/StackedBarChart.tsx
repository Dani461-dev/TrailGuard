import React from "react";
import { fmtDate, fmtShortDate, RISK_COLOR } from "../ui";

export interface StackedDay {
  day: string;
  total: number;
  critical: number;
  moderate: number;
  low: number;
}

interface Props {
  data: StackedDay[];
  height?: number;
}

/** urutan render: kritis di atas, rendah di bawah */
const STACK = [
  { key: "critical", color: RISK_COLOR.high, label: "critical", tier: "tier 3" },
  { key: "moderate", color: RISK_COLOR.mid, label: "moderate", tier: "tier 2" },
  { key: "low", color: RISK_COLOR.low, label: "low", tier: "tier 1" },
] as const;

/**
 * Stacked bar chart: 1 batang per hari, disusun per band risiko
 * (rendah di bawah -> sedang -> kritis di atas). Sumbu-y = jumlah alert.
 */
export default function StackedBarChart({ data, height = 208 }: Props) {
  if (!data || data.length === 0) {
    return (
      <p className="py-12 text-center text-sm text-text-dark">
        No daily data yet.
      </p>
    );
  }

  const max = Math.max(...data.map((d) => d.total), 1);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((t) => ({
    t,
    v: Math.round(max * t),
  }));
  const labelEvery = Math.max(1, Math.ceil(data.length / 12));

  return (
    <div className="flex gap-2">
      {/* sumbu-y */}
      <div className="relative w-7 shrink-0" style={{ height }} aria-hidden="true">
        {ticks.map(({ t, v }) => (
          <span
            key={t}
            className="absolute right-0 -translate-y-1/2 font-mono text-[0.6rem] text-text-dark"
            style={{ top: `${(1 - t) * 100}%` }}
          >
            {v}
          </span>
        ))}
      </div>

      <div className="min-w-0 flex-1">
        {/* plot */}
        <div className="relative" style={{ height }}>
          {/* gridlines */}
          {ticks.map(({ t }) => (
            <span
              key={t}
              className={t === 0 ? "absolute inset-x-0 h-px bg-border" : "absolute inset-x-0 h-px bg-border/50"}
              style={{ top: `${(1 - t) * 100}%` }}
              aria-hidden="true"
            />
          ))}

          {/* bars */}
          <div className="relative flex h-full items-end gap-1">
            {data.map((d) => (
              <div
                key={d.day}
                className="group relative flex h-full flex-1 flex-col justify-end"
              >
                {/* tooltip */}
                <div className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 hidden w-44 -translate-x-1/2 rounded-xl border border-border bg-body/95 p-3 text-left shadow-xl backdrop-blur group-hover:block">
                  <p className="font-medium text-white">{fmtDate(d.day)}</p>
                  <p className="mt-0.5 font-mono text-[0.68rem] text-text-dark">
                    {d.total} alerts
                  </p>
                  <ul className="mt-2 space-y-1">
                    {STACK.map((s) =>
                      d[s.key] > 0 ? (
                        <li key={s.key} className="flex items-center gap-2 text-[0.68rem]">
                          <span
                            className="size-2 shrink-0 rounded-sm"
                            style={{ background: s.color }}
                          />
                          <span className="text-text-dark">
                            {s.tier} · {s.label}
                          </span>
                          <span className="ml-auto font-mono text-text">
                            {d[s.key]}
                          </span>
                        </li>
                      ) : null,
                    )}
                  </ul>
                </div>

                {/* segmen bertumpuk (kritis di atas) */}
                {STACK.map((s, i) => {
                  const v = d[s.key];
                  if (!v) return null;
                  return (
                    <div
                      key={s.key}
                      className="w-full shrink-0 transition-[filter] group-hover:brightness-125"
                      style={{
                        height: `${(v / max) * 100}%`,
                        minHeight: 2,
                        background: s.color,
                        borderRadius: i === 0 ? "3px 3px 0 0" : 0,
                      }}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>

        {/* label tanggal */}
        <div className="mt-2 flex gap-1">
          {data.map((d, i) => (
            <span
              key={`l-${d.day}`}
              className="flex-1 truncate text-center font-mono text-[0.6rem] text-text-dark"
            >
              {i % labelEvery === 0 ? fmtShortDate(d.day) : ""}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

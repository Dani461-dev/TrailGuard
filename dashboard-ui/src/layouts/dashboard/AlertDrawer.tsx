import React, { useState } from "react";
import type { Alert, Decision, Source } from "@/lib/trailguardApi";
import Icon from "./Icon";
import { Badge, Button, Drawer, RiskRing } from "./primitives";
import {
  cn,
  explainTone,
  fmtDate,
  RISK_COLOR,
  riskBand,
  shortUser,
  tierStyle,
} from "./ui";

interface Props {
  alert: Alert | null;
  decision?: Decision;
  source: Source;
  onClose: () => void;
  onDecide: (
    alert: Alert,
    decision: "approve" | "reject",
    note?: string,
  ) => Promise<void>;
}

export default function AlertDrawer({
  alert,
  decision,
  source,
  onClose,
  onDecide,
}: Props) {
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState<null | "approve" | "reject">(null);

  const run = async (d: "approve" | "reject") => {
    if (!alert) return;
    setBusy(d);
    await onDecide(alert, d, note.trim() || undefined);
    setBusy(null);
  };

  if (!alert) return null;

  const s = tierStyle(alert.tier);
  const band = riskBand(alert.risk);
  const maxC = Math.max(
    ...alert.reasons.map((r) => Math.abs(r.contribution ?? r.z ?? 0)),
    0.0001,
  );
  const settled = Boolean(decision);
  const canAct = alert.requires_human_approval && !settled;

  const footer = canAct ? (
    <div className="space-y-3">
      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        rows={2}
        placeholder="Analyst note (optional)…"
        className="w-full resize-none rounded-xl border border-border bg-body/50 px-3 py-2 text-sm text-text placeholder:text-text-dark focus:border-primary focus:outline-none"
      />
      <div className="flex gap-2">
        <Button
          variant="ok"
          icon="check"
          className="flex-1"
          disabled={busy !== null}
          onClick={() => run("approve")}
        >
          {busy === "approve" ? "Saving…" : "Approve"}
        </Button>
        <Button
          variant="danger"
          icon="x"
          className="flex-1"
          disabled={busy !== null}
          onClick={() => run("reject")}
        >
          {busy === "reject" ? "Saving…" : "Reject"}
        </Button>
      </div>
      <p className="text-center text-[0.68rem] text-text-dark">
        {source === "live"
          ? "Decision stored to outputs/decisions.jsonl"
          : "Preview — decisions are not stored on the server"}
      </p>
    </div>
  ) : settled && decision ? (
    <div className="flex items-center justify-between">
      <span
        className={cn(
          "inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-semibold",
          decision.decision === "approve"
            ? "bg-emerald-400/15 text-emerald-300"
            : "bg-secondary/15 text-secondary",
        )}
      >
        <Icon
          name={decision.decision === "approve" ? "check" : "x"}
          className="size-4"
        />
        {decision.decision === "approve" ? "Approved" : "Rejected"}
      </span>
      <span className="font-mono text-xs text-text-dark">
        {decision.ts.slice(0, 16).replace("T", " ")}
      </span>
    </div>
  ) : (
    <p className="text-center text-xs text-text-dark">
      Tier {alert.tier} — no human approval needed (automatic).
    </p>
  );

  return (
    <Drawer
      open={Boolean(alert)}
      onClose={onClose}
      title={`user ${shortUser(alert.user)}`}
      subtitle={`${fmtDate(alert.day)} · ${alert.action}`}
      footer={footer}
    >
      {/* risk summary */}
      <div className="flex items-center gap-4 rounded-2xl border border-border bg-body/40 p-4">
        <RiskRing risk={alert.risk} size={72} />
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-full px-2.5 py-0.5 text-[0.68rem] font-semibold ${s.badge}`}>
              tier {alert.tier} · {s.label}
            </span>
            <span className={`rounded-md px-2 py-0.5 font-mono text-[0.68rem] ${explainTone(alert.explain_method)}`}>
              {alert.explain_method}
            </span>
            <Badge tone={band === "high" ? "secondary" : band === "mid" ? "amber" : "primary"}>
              {band}
            </Badge>
          </div>
          <p className="mt-2 text-xs text-text-dark">
            Scheduled action: <span className="text-text">{alert.action}</span>
            {alert.requires_human_approval ? " · approval required" : ""}
          </p>
        </div>
      </div>

      {/* risk scale */}
      <div className="mt-4">
        <div className="relative h-2 overflow-hidden rounded-full bg-white/5">
          <div
            className="h-full rounded-full"
            style={{ width: `${Math.round(alert.risk * 100)}%`, background: RISK_COLOR[band] }}
          />
          <span className="absolute inset-y-0 w-px bg-amber-400/70" style={{ left: "60%" }} />
          <span className="absolute inset-y-0 w-px bg-secondary/80" style={{ left: "85%" }} />
        </div>
        <div className="mt-1 flex justify-between text-[0.62rem] text-text-dark">
          <span>0.00</span>
          <span className="text-amber-300">step-up 0.60</span>
          <span className="text-secondary">ticket 0.85</span>
          <span>1.00</span>
        </div>
      </div>

      {/* summary */}
      <section className="mt-5">
        <h4 className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-text-dark">
          <Icon name="info" className="size-3.5" /> Summary
        </h4>
        <p className="text-sm leading-6 text-text">{alert.summary}</p>
      </section>

      {/* reasons */}
      <section className="mt-5">
        <h4 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-text-dark">
          <Icon name="spark" className="size-3.5" /> Feature contributions
        </h4>
        <ul className="space-y-3">
          {alert.reasons.map((r, i) => {
            const val = Math.abs(r.contribution ?? r.z ?? 0);
            const width = (val / maxC) * 100;
            const txt =
              typeof r.contribution === "number"
                ? `+${r.contribution.toFixed(3)}`
                : typeof r.z === "number"
                  ? `${r.z >= 0 ? "+" : ""}${r.z.toFixed(1)} SD`
                  : `= ${r.value}`;
            return (
              <li key={`${r.feature}-${i}`}>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="text-text">{r.label}</span>
                  <span className="font-mono text-text-dark">{txt}</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-primary to-primary-light"
                    style={{ width: `${Math.max(6, width)}%` }}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      </section>

      {/* feature table */}
      <section className="mt-5">
        <h4 className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-text-dark">
          <Icon name="layers" className="size-3.5" /> Feature details
        </h4>
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-left text-[0.72rem]">
            <thead className="bg-body/60 text-text-dark">
              <tr>
                <th className="px-3 py-2 font-medium">feature</th>
                <th className="px-3 py-2 font-medium">value</th>
                <th className="px-3 py-2 font-medium">contribution</th>
              </tr>
            </thead>
            <tbody>
              {alert.reasons.map((r, i) => (
                <tr key={`d-${r.feature}-${i}`} className="border-t border-border/60">
                  <td className="px-3 py-1.5 font-mono text-text-light">{r.feature}</td>
                  <td className="px-3 py-1.5 font-mono text-text">{r.value}</td>
                  <td className="px-3 py-1.5 font-mono text-text-dark">
                    {typeof r.contribution === "number"
                      ? `+${r.contribution.toFixed(4)}`
                      : typeof r.z === "number"
                        ? `${r.z.toFixed(2)} SD`
                        : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {alert.note && (
            <p className="border-t border-border/60 px-3 py-2 text-[0.7rem] text-text-dark">
              {alert.note}
            </p>
          )}
        </div>
      </section>

      {typeof alert.label === "number" && (
        <p className="mt-4 text-[0.68rem] text-text-dark">
          Evaluation label (not part of the score): <span className="font-mono text-text">{alert.label}</span>{" "}
          — only available on the test set.
        </p>
      )}
    </Drawer>
  );
}

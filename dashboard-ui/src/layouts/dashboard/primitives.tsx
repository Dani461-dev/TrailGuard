import React, { useEffect, useState } from "react";
import { cn, RISK_COLOR, riskBand } from "./ui";
import Sparkline from "./charts/Sparkline";
import Icon from "./Icon";

/* ───────────────────────────── Card ───────────────────────────── */

export function Card({
  className,
  children,
  as: Tag = "div",
}: {
  className?: string;
  children?: React.ReactNode;
  as?: any;
}) {
  return (
    <Tag
      className={cn(
        "rounded-2xl border border-border bg-light/80 shadow-xl shadow-black/30",
        className,
      )}
    >
      {children}
    </Tag>
  );
}

export function CardHeader({
  title,
  subtitle,
  icon,
  action,
  className,
}: {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  icon?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-start justify-between gap-3 border-b border-border/70 px-5 py-4",
        className,
      )}
    >
      <div className="flex min-w-0 items-start gap-3">
        {icon && (
          <span className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg border border-border bg-body/50 text-primary">
            <Icon name={icon} className="size-4" />
          </span>
        )}
        <div className="min-w-0">
          <h3 className="font-secondary text-sm font-bold text-white">
            {title}
          </h3>
          {subtitle && (
            <p className="mt-0.5 text-xs text-text-dark">{subtitle}</p>
          )}
        </div>
      </div>
      {action}
    </div>
  );
}

/* ───────────────────────────── Badge ──────────────────────────── */

export type Tone =
  | "primary"
  | "secondary"
  | "amber"
  | "emerald"
  | "sky"
  | "zinc"
  | "neutral";

const TONE: Record<Tone, string> = {
  primary: "bg-primary/15 text-primary border-primary/25",
  secondary: "bg-secondary/15 text-secondary border-secondary/25",
  amber: "bg-amber-400/15 text-amber-300 border-amber-400/25",
  emerald: "bg-emerald-400/15 text-emerald-300 border-emerald-400/25",
  sky: "bg-sky-400/15 text-sky-300 border-sky-400/25",
  zinc: "bg-zinc-500/15 text-zinc-300 border-zinc-500/25",
  neutral: "bg-white/5 text-text border-border",
};

export function Badge({
  tone = "neutral",
  children,
  className,
}: {
  tone?: Tone;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[0.68rem] font-semibold",
        TONE[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

/* ───────────────────────────── Button ─────────────────────────── */

type ButtonVariant = "primary" | "ghost" | "ok" | "danger" | "subtle";
type ButtonSize = "sm" | "md";

const BTN_VARIANT: Record<ButtonVariant, string> = {
  primary:
    "bg-primary text-white border border-primary hover:brightness-110 shadow-lg shadow-primary/20",
  ghost:
    "border border-border text-text hover:border-primary/40 hover:text-white",
  ok: "border border-emerald-400/40 bg-emerald-400/10 text-emerald-300 hover:bg-emerald-400/20",
  danger:
    "border border-secondary/40 bg-secondary/10 text-secondary hover:bg-secondary/20",
  subtle: "border border-transparent text-text-dark hover:text-text hover:bg-white/5",
};

const BTN_SIZE: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-xs rounded-lg gap-1.5",
  md: "px-4 py-2 text-sm rounded-xl gap-2",
};

export function Button({
  variant = "ghost",
  size = "md",
  icon,
  className,
  children,
  ...rest
}: {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: string;
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex items-center justify-center font-semibold transition disabled:cursor-not-allowed disabled:opacity-40",
        BTN_VARIANT[variant],
        BTN_SIZE[size],
        className,
      )}
      {...rest}
    >
      {icon && <Icon name={icon} className="size-4" />}
      {children}
    </button>
  );
}

export function IconButton({
  icon,
  label,
  className,
  ...rest
}: {
  icon: string;
  label: string;
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={cn(
        "grid size-9 place-items-center rounded-lg border border-border text-text-dark transition hover:border-primary/40 hover:text-white",
        className,
      )}
      {...rest}
    >
      <Icon name={icon} className="size-4" />
    </button>
  );
}

/* ─────────────────────────── Segmented ────────────────────────── */

export interface SegmentOption {
  key: string;
  label: string;
  count?: number;
}

export function Segmented({
  options,
  value,
  onChange,
  className,
}: {
  options: SegmentOption[];
  value: string;
  onChange: (key: string) => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "inline-flex rounded-xl border border-border bg-body/50 p-0.5",
        className,
      )}
    >
      {options.map((o) => {
        const active = o.key === value;
        return (
          <button
            key={o.key}
            type="button"
            onClick={() => onChange(o.key)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-[0.6rem] px-3 py-1.5 text-xs font-medium transition",
              active
                ? "bg-primary/20 text-primary ring-1 ring-inset ring-primary/35"
                : "text-text-dark hover:text-text",
            )}
          >
            {o.label}
            {typeof o.count === "number" && (
              <span
                className={cn(
                  "rounded-full px-1.5 text-[0.62rem] font-semibold",
                  active ? "bg-primary/20 text-primary" : "bg-white/5 text-text-dark",
                )}
              >
                {o.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

/* ──────────────────────── Inputs / Select ─────────────────────── */

export function Input({
  icon,
  className,
  ...rest
}: { icon?: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className={cn("relative", className)}>
      {icon && (
        <Icon
          name={icon}
          className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-text-dark"
        />
      )}
      <input
        {...rest}
        className={cn(
          "w-full rounded-xl border border-border bg-body/50 py-2 pr-3 text-sm text-text placeholder:text-text-dark transition focus:border-primary focus:outline-none focus:ring-0",
          icon ? "pl-9" : "pl-3",
        )}
      />
    </div>
  );
}

export function Select({
  className,
  children,
  ...rest
}: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...rest}
      className={cn(
        "rounded-xl border border-border bg-body/50 px-3 py-2 text-sm text-text transition focus:border-primary focus:outline-none",
        className,
      )}
    >
      {children}
    </select>
  );
}

/* ─────────────────────────── Skeleton ─────────────────────────── */

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn("animate-pulse rounded-xl bg-white/[0.04]", className)}
      aria-hidden="true"
    />
  );
}

/* ────────────────────────── EmptyState ────────────────────────── */

export function EmptyState({
  icon = "inbox",
  title,
  hint,
  action,
}: {
  icon?: string;
  title: string;
  hint?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-14 text-center">
      <span className="mb-4 grid size-14 place-items-center rounded-2xl border border-border bg-body/50 text-primary/70">
        <Icon name={icon} className="size-6" />
      </span>
      <p className="font-secondary text-base font-bold text-white">{title}</p>
      {hint && <p className="mt-1.5 max-w-md text-sm text-text-dark">{hint}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

/* ──────────────────────────── RiskRing ────────────────────────── */

export function RiskRing({
  risk,
  size = 56,
  className,
}: {
  risk: number;
  size?: number;
  className?: string;
}) {
  const band = riskBand(risk);
  const color = RISK_COLOR[band];
  const stroke = 4;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const dash = c * Math.max(0, Math.min(1, risk));
  return (
    <div
      className={cn("relative shrink-0", className)}
      style={{ width: size, height: size }}
    >
      <svg viewBox={`0 0 ${size} ${size}`} className="absolute inset-0 -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${c}`}
        />
      </svg>
      <span
        className="absolute inset-0 grid place-items-center font-mono font-bold"
        style={{ color, fontSize: size * 0.26 }}
      >
        {risk.toFixed(2)}
      </span>
    </div>
  );
}

/* ──────────────────────────── StatCard ────────────────────────── */

export function StatCard({
  label,
  value,
  hint,
  icon,
  accent = "text-white",
  bar,
  spark,
  sparkColor,
}: {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
  icon: string;
  accent?: string;
  bar?: number;
  spark?: number[];
  sparkColor?: string;
}) {
  return (
    <Card className="group relative overflow-hidden p-5 transition hover:border-primary/40">
      <div className="flex items-start justify-between gap-2">
        <p className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-text-dark">
          {label}
        </p>
        <span className="grid size-8 place-items-center rounded-lg border border-border bg-body/50 text-primary/80 transition group-hover:text-primary">
          <Icon name={icon} className="size-4" />
        </span>
      </div>
      <p className={cn("mt-3 font-secondary text-h5 font-bold leading-none", accent)}>
        {value}
      </p>
      {typeof bar === "number" && (
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/5">
          <div
            className="h-full rounded-full bg-gradient-to-r from-primary to-emerald-400"
            style={{ width: `${Math.max(0, Math.min(1, bar)) * 100}%` }}
          />
        </div>
      )}
      {spark && spark.length > 1 && (
        <div className="mt-3 -mb-1">
          <Sparkline data={spark} color={sparkColor ?? "#937AFF"} height={28} />
        </div>
      )}
      {hint && <p className="mt-1.5 text-xs text-text-dark">{hint}</p>}
    </Card>
  );
}

/* ──────────────────────────── Drawer ──────────────────────────── */

export function Drawer({
  open,
  onClose,
  title,
  subtitle,
  children,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[70] flex justify-end">
      <div
        className="dr-fade absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={typeof title === "string" ? title : "Detail"}
        className="dr-drawer dr-scroll relative flex h-full w-full max-w-lg flex-col overflow-y-auto border-l border-border bg-light shadow-2xl"
      >
        <header className="sticky top-0 z-10 flex items-start justify-between gap-3 border-b border-border bg-light/95 px-5 py-4 backdrop-blur">
          <div className="min-w-0">
            <h2 className="font-secondary text-base font-bold text-white">
              {title}
            </h2>
            {subtitle && (
              <div className="mt-0.5 text-xs text-text-dark">{subtitle}</div>
            )}
          </div>
          <IconButton icon="x" label="Close" onClick={onClose} />
        </header>
        <div className="flex-1 px-5 py-5">{children}</div>
        {footer && (
          <footer className="sticky bottom-0 border-t border-border bg-light/95 px-5 py-4 backdrop-blur">
            {footer}
          </footer>
        )}
      </aside>
    </div>
  );
}

/* ───────────────────────────── Toast ──────────────────────────── */

type ToastTone = "ok" | "err" | "info";
interface ToastItem {
  id: number;
  msg: string;
  tone: ToastTone;
}

const toastListeners = new Set<(t: ToastItem) => void>();
let toastId = 0;

export function toast(msg: string, tone: ToastTone = "ok") {
  const t: ToastItem = { id: toastId++, msg, tone };
  toastListeners.forEach((l) => l(t));
}

const TOAST_TONE: Record<ToastTone, string> = {
  ok: "border-emerald-400/40 text-emerald-300",
  err: "border-secondary/40 text-secondary",
  info: "border-primary/40 text-primary",
};

export function ToastHost() {
  const [items, setItems] = useState<ToastItem[]>([]);
  useEffect(() => {
    const listener = (t: ToastItem) => {
      setItems((prev) => [...prev, t]);
      window.setTimeout(
        () => setItems((prev) => prev.filter((x) => x.id !== t.id)),
        3200,
      );
    };
    toastListeners.add(listener);
    return () => {
      toastListeners.delete(listener);
    };
  }, []);

  return (
    <div className="pointer-events-none fixed bottom-5 right-5 z-[100] flex w-80 flex-col gap-2">
      {items.map((t) => (
        <div
          key={t.id}
          className={cn(
            "dr-toast pointer-events-auto flex items-center gap-3 rounded-xl border bg-light/95 px-4 py-3 text-sm shadow-2xl backdrop-blur",
            TOAST_TONE[t.tone],
          )}
        >
          <Icon
            name={t.tone === "err" ? "alert" : t.tone === "info" ? "info" : "check"}
            className="size-4 shrink-0"
          />
          <span className="text-text">{t.msg}</span>
        </div>
      ))}
    </div>
  );
}

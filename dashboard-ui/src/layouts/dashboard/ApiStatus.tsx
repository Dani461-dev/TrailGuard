import React, { useCallback, useEffect, useState } from "react";
import { fetchConfig, type Source } from "@/lib/trailguardApi";
import Icon from "./Icon";

/** Indikator kecil status sumber data (live Flask API vs data contoh). */
export default function ApiStatus() {
  const [state, setState] = useState<Source | "loading">("loading");
  const [dataset, setDataset] = useState<string>("");

  const load = useCallback(() => {
    let alive = true;
    fetchConfig().then((r) => {
      if (!alive) return;
      setState(r.source);
      setDataset(r.data.dataset);
    });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    const cleanup = load();
    const onRefresh = () => load();
    window.addEventListener("trailguard:refresh", onRefresh);
    return () => {
      cleanup();
      window.removeEventListener("trailguard:refresh", onRefresh);
    };
  }, [load]);

  const live = state === "live";
  const loading = state === "loading";

  return (
    <div className="rounded-xl border border-border bg-body/40 px-3 py-2.5">
      <div className="flex items-center gap-2 text-xs">
        <span
          className={`size-2 rounded-full ${
            loading
              ? "bg-text-dark"
              : live
                ? "animate-pulse bg-emerald-400"
                : "bg-amber-400"
          }`}
        />
        <span className={live ? "text-emerald-300" : "text-amber-300"}>
          {loading ? "Connecting…" : live ? "Live · Flask API" : "Preview · sample"}
        </span>
      </div>
      <div className="mt-1.5 flex items-center gap-1.5 text-[0.68rem] text-text-dark">
        <Icon name="layers" className="size-3" />
        dataset <span className="font-mono text-text">{dataset || "—"}</span>
      </div>
    </div>
  );
}

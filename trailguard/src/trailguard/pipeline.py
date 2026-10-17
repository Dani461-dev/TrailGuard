"""CLI pipeline:  python -m trailguard.pipeline <langkah> [--raw DIR] [--config FILE]

Langkah: ingest -> features -> train -> evaluate -> score  (atau 'all')
Dataset dipilih lewat config: configs/config.yaml (CERT) atau configs/config_lanl.yaml (LANL).
Kontrak data antar-langkah ada di docs/03_DATA_CONTRACTS.md
"""
import argparse
import collections
import json
import time

from .config import load_config, path_of
from .features.registry import spec as feature_spec
from .ingest.pseudonymize import get_key
from .io_utils import read_table, write_table
from .llm.summarizer import template_summary
from .models.evaluate import alert_budget_metrics
from .models.explain import explain_alert
from .models.score import score_frame
from .models.train import load_bundle, save_bundle, temporal_split, train_models
from .policy.policy import decide


def _loaders(cfg, raw):
    ic = cfg["ingest"]
    raw = raw or path_of(cfg, "raw")
    if cfg.get("dataset", "cert") == "lanl":
        from .ingest import loader_lanl as L
        return (lambda key: L.load_events(raw, key, ic["max_rows_per_file"], ic["hash_length"],
                                          ic.get("chunksize", 2_000_000)),
                lambda key: L.load_labels(raw, key, ic["hash_length"]))
    from .ingest import loader as L
    return (lambda key: L.load_events(raw, key, ic["company_domain"], ic["max_rows_per_file"], ic["hash_length"]),
            lambda key: L.load_labels(raw, key, ic["hash_length"]))


def step_ingest(cfg, raw=None):
    key = get_key()
    load_ev, load_lb = _loaders(cfg, raw)
    ev, labels = load_ev(key), load_lb(key)
    p = write_table(ev, cfg, "events")
    write_table(labels, cfg, "labels")
    print(f"[ingest:{cfg.get('dataset', 'cert')}] {len(ev):,} event, {labels.user.nunique()} user berlabel -> {p}")


def step_features(cfg):
    sp = feature_spec(cfg)
    ev = read_table(cfg, "events", ["ts"])
    labels = read_table(cfg, "labels", ["start", "end"])
    feat = sp.add_labels(sp.build_daily_features(ev, cfg), labels)
    write_table(feat, cfg, "features")
    print(f"[features] {len(feat):,} user-hari, {int(feat.label.sum())} berlabel jahat, {len(sp.FEATURE_COLS)} fitur")


def _load_feat(cfg):
    return read_table(cfg, "features", ["day"])


def step_train(cfg):
    import pandas as pd
    sp = feature_spec(cfg)
    train, test, cut = temporal_split(_load_feat(cfg), cfg["model"]["train_fraction"])
    print(f"[train] split di {pd.Timestamp(cut).date()}: train={len(train):,} test={len(test):,} "
          f"(positif train={int(train.label.sum())}, test={int(test.label.sum())})")
    p = path_of(cfg, "model"); p.parent.mkdir(parents=True, exist_ok=True)
    save_bundle(train_models(train, cfg, sp.FEATURE_COLS), p)


def step_evaluate(cfg):
    _, test, _ = temporal_split(_load_feat(cfg), cfg["model"]["train_fraction"])
    scored = score_frame(load_bundle(path_of(cfg, "model")), test, cfg["model"]["ensemble_weight_supervised"])
    m = alert_budget_metrics(scored, cfg["evaluation"]["alert_budget_per_day"])
    p = path_of(cfg, "metrics"); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(m, indent=2))
    print("[evaluate]", json.dumps(m, indent=2))


def step_score(cfg):
    sp = feature_spec(cfg)
    w = cfg["model"]["ensemble_weight_supervised"]
    ec = cfg.get("explain", {})
    bundle = load_bundle(path_of(cfg, "model"))
    _, test, _ = temporal_split(_load_feat(cfg), cfg["model"]["train_fraction"])
    scored = score_frame(bundle, test, w)
    k = cfg["evaluation"]["alert_budget_per_day"]
    top = scored.sort_values(["day", "risk"], ascending=[True, False]).groupby("day").head(k)
    used, n_explained = collections.Counter(), 0
    p = path_of(cfg, "alerts"); p.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with open(p, "w") as f:
        for _, r in top.iterrows():
            pol = decide(float(r.risk), cfg)
            if (ec.get("method", "deviation") != "deviation" and pol["tier"] >= ec.get("min_tier", 2)
                    and n_explained < ec.get("max_alerts", 300)):
                reasons, method = explain_alert(bundle, r, cfg, sp, w)
                n_explained += 1
            else:                                   # tier rendah / melebihi kuota -> penjelasan murah
                from .models.explain import explain_row
                reasons, method = explain_row(r, sp.BASE_COLS, sp.FEATURE_LABELS, ec.get("top_k", 3)), "deviation"
            used[method] += 1
            a = {"user": r.user, "day": str(r.day.date()), "risk": round(float(r.risk), 4),
                 "label": int(r.label), "reasons": reasons, "explain_method": method, **pol}
            a["summary"] = template_summary(a)
            f.write(json.dumps(a) + "\n")
    print(f"[score] {len(top)} alert -> {p} | metode penjelasan: {dict(used)} | {time.time() - t0:.1f}s")
    if used.get("shap"):
        print("[score] 'shap' dipakai -> BOLEH klaim SHAP (library).")
    elif used.get("shapley"):
        print("[score] hanya 'shapley' (implementasi sendiri) -> klaim sebagai 'Shapley-value explanations', BUKAN 'SHAP library'.")


STEPS = {"ingest": step_ingest, "features": step_features, "train": step_train,
         "evaluate": step_evaluate, "score": step_score}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=list(STEPS) + ["all"])
    ap.add_argument("--raw", default=None, help="folder data mentah (default: config paths.raw)")
    ap.add_argument("--config", default=None)
    a = ap.parse_args()
    cfg = load_config(a.config)
    t0 = time.time()
    for name in (STEPS if a.step == "all" else [a.step]):
        STEPS[name](cfg, a.raw) if name == "ingest" else STEPS[name](cfg)
    print(f"selesai dalam {time.time() - t0:.1f} detik")


if __name__ == "__main__":
    main()

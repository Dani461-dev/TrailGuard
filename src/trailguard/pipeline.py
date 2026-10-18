"""CLI pipeline:  python -m trailguard.pipeline <langkah> [--raw DIR] [--config FILE]

Langkah: ingest -> features -> train -> evaluate -> score  (atau 'all')
Dataset dipilih lewat config: configs/config.yaml (CERT) atau configs/config_lanl.yaml (LANL).
Kontrak data antar-langkah ada di docs/03_DATA_CONTRACTS.md

Artefak yang keluar dari sini mengikuti Kontrak #2 (fitur), #3 (alert), #4 (bundle), #5 (metrik),
sehingga dashboard C (`/api/alerts`, `/api/metrics`) bisa membacanya tanpa penyesuaian.
"""
import argparse
import collections
import json
import time

import pandas as pd

from .config import load_config, path_of
from .features.registry import feature_labels, spec as feature_spec, z_suffix_of
from .ingest.pseudonymize import get_key
from .io_utils import read_table, write_table
from .llm.summarizer import template_summary
from .models.evaluate import alert_budget_metrics, baselines, generalization_audit
from .models.explain import explain_alert, explain_row
from .models.score import score_frame
from .models.train import load_bundle, save_bundle, temporal_split, train_models
from .policy.policy import decide, policy_cfg

KEY_RENAMES = {"time_key": "day", "user_hash": "user"}   # nama lama (notebook) -> Kontrak #2
NOT_FEATURES = {"user", "day", "label", "risk", "p_supervised", "p_anomaly"}


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
    """Baca fitur + tentukan kolom fiturnya.

    Menerima dua gaya penamaan supaya `make run` bisa dipakai pada fitur yang SUDAH ada
    (mis. keluaran notebook B1 yang memakai `time_key`/`user_hash`), tanpa harus ingest ulang.
    Yang penting isinya sesuai Kontrak #2: 1 baris = 1 user x 1 hari + kolom `label`.
    Mengembalikan (DataFrame, daftar kolom fitur).
    """
    df = read_table(cfg, "features", ["day"])
    df = df.rename(columns={k: v for k, v in KEY_RENAMES.items() if k in df.columns})
    missing = {"user", "day", "label"} - set(df.columns)
    if missing:
        raise ValueError(f"fitur harus punya kolom {sorted(missing)}; yang ada: {list(df.columns)[:10]}")

    if not pd.api.types.is_datetime64_any_dtype(df["day"]):
        num = pd.to_numeric(df["day"], errors="coerce")
        if cfg.get("dataset") == "lanl" and num.notna().all():
            # LANL: `time_key` = jam sejak awal data (Kontrak #1b: waktu hanya RELATIF bermakna)
            df["day"] = pd.Timestamp("1970-01-01") + pd.to_timedelta(num.astype("int64"), unit="h")
            print("[load] kolom jam LANL -> tanggal berpatokan 1970-01-01 (hanya relatif)")
        else:
            df["day"] = pd.to_datetime(df["day"], errors="coerce")
        if df["day"].isna().any():
            raise ValueError("kolom 'day' tidak terbaca sebagai tanggal")

    wanted = cfg.get("model", {}).get("feature_cols")
    if wanted:
        cols = [c for c in wanted if c in df.columns]
    else:
        spec_cols = feature_spec(cfg).FEATURE_COLS
        cols = spec_cols if set(spec_cols) <= set(df.columns) else [
            c for c in df.columns if c not in NOT_FEATURES and pd.api.types.is_numeric_dtype(df[c])]
    if not cols:
        raise ValueError("tidak ada kolom fitur yang cocok dengan config maupun daftar fitur dataset")
    return df, cols


def step_train(cfg):
    feat, cols = _load_feat(cfg)
    train, test, cut = temporal_split(feat, cfg["model"]["train_fraction"])
    print(f"[train] split di {pd.Timestamp(cut).date()}: train={len(train):,} test={len(test):,} "
          f"(positif train={int(train.label.sum())}, test={int(test.label.sum())}) | {len(cols)} fitur")
    if train.label.sum() == 0:
        print("[train] PERINGATAN: tidak ada label positif di periode train -> model supervised dilewati")
    p = path_of(cfg, "model"); p.parent.mkdir(parents=True, exist_ok=True)
    save_bundle(train_models(train, cfg, cols), p)


def _policy_cfg(cfg, bundle):
    """Ambang tier hasil kalibrasi validasi dipakai untuk alert (lihat policy.policy_cfg)."""
    return policy_cfg(cfg, bundle)


def _model_description(bundle) -> str:
    """Sebutkan model apa yang SEBENARNYA dipakai (hasil pemilihan di validasi), bukan nama paket."""
    if bundle.get("sup") is None:
        return "hanya Isolation Forest (tidak ada label positif di periode train)"
    a, meth = bundle.get("alpha"), bundle.get("combine_method")
    if a is not None and a >= 1.0:
        return "hanya model supervised (alpha=1.0 dipilih di validasi; Isolation Forest tidak menambah)"
    if a is not None and a <= 0.0:
        return "hanya Isolation Forest (alpha=0.0 dipilih di validasi; label tidak membantu)"
    return f"gabungan '{meth}': {a}*p_supervised + sisanya p_anomaly (alpha dipilih di validasi)"


def step_evaluate(cfg):
    """Tulis outputs/metrics.json.

    Kunci Kontrak #5 (`precision_at_budget`, `recall_at_budget`, `insiders_detected`,
    `median_days_to_detection`, ...) ada di TINGKAT TERATAS supaya dashboard/C tetap bisa membacanya;
    blok pembanding, audit generalisasi, dan hasil tuning ditambahkan di bawahnya.
    """
    bundle = load_bundle(path_of(cfg, "model"))
    feat, _ = _load_feat(cfg)
    tf = cfg["model"]["train_fraction"]
    train, test, cut = temporal_split(feat, tf)
    k = cfg["evaluation"]["alert_budget_per_day"]
    tests = baselines(score_frame(bundle, test), k)
    tests["trailguard_hybrid"]["description"] = _model_description(bundle)
    th = bundle.get("thresholds") or {}
    main = dict(tests["trailguard_hybrid"])
    main["description"] = _model_description(bundle)
    m = {
        **main,
        "dataset": cfg.get("dataset", "cert"),
        "alert_budget_per_day": k,
        "split": {"train_fraction": tf, "cut_day": str(pd.Timestamp(cut).date()),
                  "train_days": int(train.day.nunique()), "test_days": int(test.day.nunique())},
        "model": {"selected_supervised_model": "HistGradientBoostingClassifier" if bundle.get("sup") is not None else None,
                  "positive_class_weight": bundle.get("positive_class_weight"),
                  "combine_method": bundle.get("combine_method"),
                  "ensemble_alpha": bundle.get("alpha")},
        "tier_thresholds": {
            "step_up_threshold": (th or cfg["policy"])["step_up_threshold"],
            "ticket_threshold": (th or cfg["policy"])["ticket_threshold"],
            "source": "calibrated_on_validation" if th else "config",
        },
        "tier_calibration": {k: v for k, v in th.items()
                             if k not in ("step_up_threshold", "ticket_threshold")},
        "generalization_audit": generalization_audit(feat, tf, lambda d: score_frame(bundle, d)),
        "test_evaluation": tests,
        "model_selection": bundle.get("selection"),
    }
    p = path_of(cfg, "metrics"); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(m, indent=2))
    print(f"[evaluate] {m['precision_at_budget']=} {m['recall_at_budget']=} "
          f"insiders_detected={m['insiders_detected']}/{m['insiders_in_test']} -> {p}")


def step_score(cfg):
    """Tulis outputs/alerts.jsonl sesuai Kontrak #3 (dashboard C membaca berkas ini)."""
    bundle = load_bundle(path_of(cfg, "model"))
    feat, cols = _load_feat(cfg)
    labels = feature_labels(cfg)
    base = [c for c in cols if not z_suffix_of(c)]
    pol_cfg = _policy_cfg(cfg, bundle)
    ec = cfg.get("explain", {})
    _, test, _ = temporal_split(feat, cfg["model"]["train_fraction"])
    scored = score_frame(bundle, test)
    k = cfg["evaluation"]["alert_budget_per_day"]
    top = scored.sort_values(["day", "risk"], ascending=[True, False]).groupby("day").head(k)
    used, n_explained = collections.Counter(), 0
    p = path_of(cfg, "alerts"); p.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with open(p, "w", encoding="utf-8") as f:
        for _, r in top.iterrows():
            pol = decide(float(r.risk), pol_cfg)
            if (ec.get("method", "deviation") != "deviation" and pol["tier"] >= ec.get("min_tier", 2)
                    and n_explained < ec.get("max_alerts", 300)):
                reasons, method = explain_alert(bundle, r, cfg, labels, base)
                n_explained += 1
            else:                                   # tier rendah / melebihi kuota -> penjelasan murah
                reasons, method = explain_row(r, base, labels, ec.get("top_k", 3)), "deviation"
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

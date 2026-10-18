"""Tes jalur MODEL & FITUR milik Grup B (B-Model + B-Data).

File terpisah dari `tests/test_core.py` (milik C-Lead) supaya tidak bentrok kepemilikan file.
Yang diuji di sini adalah hal-hal yang kalau salah TIDAK kelihatan dari output (diam-diam salah):

  * split temporal tidak boleh melihat masa depan;
  * validasi yang kosong dari label -> tuning dilewati tanpa suara (kasus nyata di LANL);
  * ambang tier hasil kalibrasi harus terurut & tidak boleh membuat semua alert jadi tiket;
  * bundle wajib memuat kunci Kontrak #4 + jejak pemilihan hyperparameter;
  * semua pembanding B5 memakai potongan & alert budget yang SAMA;
  * penjelasan alert harus mencatat `explain_method` dan isinya cocok dengan metode itu;
  * label CERT: filter dataset=r4.2 + tanggal ISO (dua jebakan yang dulu membuat label jadi kosong).
"""
import numpy as np
import pandas as pd
import pytest

from trailguard.config import load_config
from trailguard.features import builder, builder_lanl
from trailguard.features.registry import feature_labels, z_suffix_of
from trailguard.ingest.loader import load_labels
from trailguard.models.evaluate import alert_budget_metrics, baselines, generalization_audit
from trailguard.models.explain import explain_alert
from trailguard.models.score import combine_scores, score_frame
from trailguard.models.train import calibrate_thresholds, split_last, temporal_split, train_models
from trailguard.policy.policy import decide, policy_cfg


# ---------- bantu ----------
def _feat_frame(n_users=10, n_days=40, seed=3):
    """Frame fitur berformat Kontrak #2 (user, day, label, BASE_COLS + *_z) dengan sinyal jelas.

    Dua user pertama adalah "insider": lonjakan di hari 8-10 (agar bagian AWAL periode train juga
    berlabel), di akhir periode train (hari 20-25), DAN di test (hari >= 34). Sengaja jelas supaya
    tes menguji MEKANISME (split, tuning, kalibrasi, kontrak), bukan keberuntungan model.
    """
    rng = np.random.default_rng(seed)
    days = pd.date_range("2010-01-01", periods=n_days)
    rows = []
    for u in range(n_users):
        insider = u < 2
        for i, d in enumerate(days):
            spike = insider and (i in (8, 9, 10) or 20 <= i < 26 or i >= 34)
            base = {c: float(rng.integers(0, 3)) for c in builder.BASE_COLS}
            if spike:
                base["n_http"] = float(rng.integers(40, 60))
                base["n_new_domain"] = float(rng.integers(6, 10))
            row = {"user": f"u{u:02d}", "day": d, "label": int(spike)}
            row.update(base)
            row.update({f"{c}_z": float(np.clip((base[c] - 1.0) * 0.6, -builder.Z_CLIP, builder.Z_CLIP))
                        for c in builder.BASE_COLS})
            rows.append(row)
    return pd.DataFrame(rows)


def _day_label_frame(positive_days, n_days=20):
    """Frame minimal (user/day/label) -- cukup untuk menguji `split_last`."""
    base = pd.Timestamp("2010-01-01")
    return pd.DataFrame({"user": "u1",
                         "day": [base + pd.Timedelta(days=i) for i in range(n_days)],
                         "label": [int(i in positive_days) for i in range(n_days)]})


def _trained():
    """(cfg, frame, train, test, bundle) -- sekali latih, dipakai banyak tes."""
    cfg = load_config()
    f = _feat_frame()
    train, test, _ = temporal_split(f, 0.65)
    return cfg, f, train, test, train_models(train, cfg, builder.FEATURE_COLS)


# ---------- 1) split temporal ----------
def test_temporal_split_never_sees_the_future():
    f = _feat_frame()
    train, test, cut = temporal_split(f, 0.65)
    assert train["day"].max() < cut <= test["day"].min()
    assert train["day"].max() < test["day"].min()
    assert train["label"].sum() > 0 and test["label"].sum() > 0


def test_split_last_does_not_widen_when_val_already_has_positives():
    f = _day_label_frame(set(range(30, 40)), n_days=40)    # seluruh 20% terakhir berlabel
    fit, val = split_last(f, 0.8, min_positives=5)
    assert len(val) == 8 and val["label"].sum() == 8       # jendela bawaan 20% tetap dipakai
    assert fit["day"].max() < val["day"].min()


def test_split_last_widens_window_until_validation_has_positives():
    # kasus nyata LANL: positif menggerombol di TENGAH periode -> 20% hari terakhir kosong label
    f = _day_label_frame(set(range(20, 27)), n_days=40)
    fit0, val0 = split_last(f, 0.8)
    assert val0["label"].sum() == 0                     # jendela bawaan memang tak berlabel

    fit, val = split_last(f, 0.8, min_positives=5)
    assert val["label"].sum() >= 5                       # jendela diperlebar sampai ada label
    assert fit["day"].max() < val["day"].min()           # urutan tetap: latih di masa lalu
    assert len(fit) >= len(f) * 0.5                      # sisakan cukup data untuk melatih
    assert len(val) < len(f)                             # validasi tidak menelan seluruh data


def test_temporal_split_never_sees_the_future_after_widening():
    f = _day_label_frame({12, 13, 14, 15, 16})
    fit, val = split_last(f, 0.8, min_positives=5)
    assert set(fit["day"]).isdisjoint(set(val["day"]))


# ---------- 2) tuning & kalibrasi ----------
def test_calibrate_thresholds_is_ordered_and_bounded():
    rng = np.random.default_rng(0)
    y = np.r_[np.zeros(800), np.ones(40)]
    risk = np.r_[rng.random(800) * 0.4, 0.5 + rng.random(40) * 0.5]
    th = calibrate_thresholds(y, risk)
    assert th["step_up_threshold"] < th["ticket_threshold"]
    assert 0.0 <= th["step_up_threshold"] <= 0.95
    assert th["ticket_threshold"] <= 0.99
    assert th["step_up_threshold"] >= th["tier2_floor_p90_normal"] - 1e-3   # batas alarm palsu
    assert 0.0 <= th["val_f1_at_step_up"] <= 1.0


def test_combine_scores_methods_and_single_row_rank():
    sup, an = np.array([0.1, 0.9, 0.2]), np.array([0.8, 0.05, 0.3])
    assert np.allclose(combine_scores(sup, an, "weighted", 0.6), 0.6 * sup + 0.4 * an)
    assert np.allclose(combine_scores(sup, an, "max"), np.maximum(sup, an))
    # peringkat: urutan naik di kedua cabang -> rerata peringkat 0, 0.5, 1
    assert np.allclose(combine_scores(np.array([0.1, 0.5, 0.9]), np.array([0.2, 0.4, 0.6]), "rank"),
                       [0.0, 0.5, 1.0])
    assert combine_scores(np.array([0.9]), np.array([0.1]), "rank")[0] == 0.5   # satu baris: tak bermakna


def test_train_models_stores_contract_4_keys_and_selection_evidence():
    cfg, f, train, test, bundle = _trained()
    for k in ("sup", "iso", "an_lo", "an_hi", "feature_cols", "base_mean", "base_std",
              "background", "alpha", "combine_method", "thresholds", "positive_class_weight",
              "selection"):
        assert k in bundle, f"kunci Kontrak #4 hilang: {k}"
    assert bundle["combine_method"] in ("weighted", "max", "rank")
    assert 0.0 <= bundle["alpha"] <= 1.0
    sel = bundle["selection"]
    assert sel["val_rows"] > 0 and sel["val_positives"] > 0
    assert sel["winner"]["combine_method"] == bundle["combine_method"]
    assert sel["winner"]["alpha"] == bundle["alpha"]
    assert {c["pos_weight_exp"] for c in sel["supervised_candidates"]} == set(
        __import__("trailguard.models.train", fromlist=["x"]).WEIGHT_EXP_GRID)
    assert bundle["thresholds"]["ticket_threshold"] > bundle["thresholds"]["step_up_threshold"]
    assert bundle["feature_cols"] == builder.FEATURE_COLS


# ---------- 3) skor ----------
def test_score_frame_outputs_probabilities_and_uses_bundle_settings():
    cfg, f, train, test, bundle = _trained()
    scored = score_frame(bundle, test)
    assert {"risk", "p_supervised", "p_anomaly"} <= set(scored.columns)
    assert scored["risk"].between(0, 1).all() and scored["p_anomaly"].between(0, 1).all()
    assert len(scored) == len(test)
    assert np.allclose(score_frame(bundle, test)["risk"], scored["risk"])   # deterministik


def test_single_row_rank_falls_back_to_weighted():
    cfg, f, train, test, bundle = _trained()
    one = score_frame({**bundle, "combine_method": "rank"}, test.iloc[[0]])["risk"].iloc[0]
    exp = score_frame({**bundle, "combine_method": "weighted"}, test.iloc[[0]])["risk"].iloc[0]
    assert one == pytest.approx(exp)          # bukan 0.5 buta


# ---------- 4) evaluasi jujur ----------
def test_alert_budget_metrics_counts_top_k_per_day():
    scored = pd.DataFrame({"user": ["a", "a", "b", "b"],
                           "day": pd.to_datetime(["2010-01-01", "2010-01-01", "2010-01-02", "2010-01-02"]),
                           "risk": [0.9, 0.1, 0.2, 0.8], "label": [1, 0, 0, 1]})
    m = alert_budget_metrics(scored, 1)
    assert m["alert_budget_per_day"] == 1 and m["n_alerts"] == 2
    assert m["true_positive_alerts"] == 2 and m["precision_at_budget"] == 1.0
    assert m["n_malicious_user_days"] == 2 and m["recall_at_budget"] == 1.0
    assert m["insiders_in_test"] == 2 and m["insiders_detected"] == 2
    assert m["median_days_to_detection"] == 0.0


def test_baselines_all_use_the_same_slice_and_budget():
    cfg, f, train, test, bundle = _trained()
    b = baselines(score_frame(bundle, test), 3)
    assert set(b) == {"trailguard_hybrid", "supervised_only", "unsupervised_only",
                      "zscore_baseline", "random_baseline"}
    ref = b["trailguard_hybrid"]
    for name, m in b.items():
        assert m["alert_budget_per_day"] == 3, name
        assert m["n_alerts"] == ref["n_alerts"], name                      # potongan yang sama
        assert m["n_malicious_user_days"] == ref["n_malicious_user_days"], name
        assert "description" in m and "precision_at_budget" in m


def test_generalization_audit_fills_three_slices_from_the_same_model():
    cfg, f, train, test, bundle = _trained()
    audit = generalization_audit(f, 0.65, lambda df: score_frame(bundle, df))
    assert audit["train_rows"] > 0 and audit["val_rows"] > 0 and audit["test_rows"] > 0
    assert audit["val_positives"] > 0 and audit["test_positives"] > 0
    assert audit["test_pr_auc"] is not None and audit["test_pr_auc"] > 0.5   # sinyal dipelajari
    assert audit["train_pr_auc"] >= audit["test_pr_auc"] - 1e-9


# ---------- 5) penjelasan alert ----------
def test_explain_alert_records_method_and_is_consistent_with_it():
    cfg, f, train, test, bundle = _trained()
    labels = feature_labels(cfg)
    row = score_frame(bundle, test)[lambda d: d["label"] == 1].iloc[0]

    reasons, method = explain_alert(bundle, row, {"explain": {"method": "shapley", "top_k": 3}}, labels)
    assert method in ("shap", "shapley", "deviation")      # klaim hanya sesuai `explain_method`
    assert len(reasons) >= 1
    for r in reasons:
        assert {"feature", "label", "value", "contribution"} <= set(r)
        assert r["contribution"] > 0
        assert r["kind"] in ("count", "z")

    dev, dmethod = explain_alert(bundle, row, {"explain": {"method": "deviation", "top_k": 3}}, labels)
    assert dmethod == "deviation"
    assert dev, "baris positif harus punya fitur yang menyimpang"
    for r in dev:
        assert "z" in r and "contribution" not in r        # kontrak: deviation memakai 'z'


def test_z_suffixes_are_recognised_across_feature_naming_styles():
    assert z_suffix_of("n_http_z") == "_z"
    assert z_suffix_of("http_zscore_7d") == "_zscore_7d"
    assert z_suffix_of("unique_dst_pop_z") == "_pop_z"
    assert z_suffix_of("n_http") is None


# ---------- 6) policy memakai ambang hasil kalibrasi ----------
def test_policy_uses_calibrated_thresholds_without_mutating_config():
    cfg = load_config()
    assert policy_cfg(cfg, {}) == cfg                       # tanpa bundle: pakai config
    p = policy_cfg(cfg, {"thresholds": {"step_up_threshold": 0.90, "ticket_threshold": 0.99}})
    assert p["policy"]["ticket_threshold"] == 0.99
    assert cfg["policy"]["ticket_threshold"] == 0.85        # config asli tidak diubah
    assert decide(0.92, p)["tier"] == 2 and decide(0.92, cfg)["tier"] == 3


# ---------- 7) fitur (B3) ----------
def test_cert_features_mask_new_host_in_warmup_and_clip_z():
    cfg = load_config()
    base = pd.Timestamp("2010-01-04")
    ev = pd.DataFrame([{"ts": base + pd.Timedelta(days=d, hours=10), "user": "u1", "host": f"h{d}",
                        "source": "logon", "action": "logon", "target": "", "size": 0}
                       for d in range(5)])
    f = builder.build_daily_features(ev, cfg)
    warm = int(cfg["features"]["warmup_days"])
    assert f["n_new_host"].iloc[:warm].eq(0).all()          # cold start: bukan "komputer baru"
    assert f["n_new_host"].iloc[warm] == 1                  # host ke-4 memang baru
    assert f[builder.Z_COLS].abs().max().max() <= builder.Z_CLIP + 1e-9
    assert set(builder.FEATURE_COLS) <= set(f.columns)


def test_lanl_features_new_hour_detects_unseen_hour_and_respects_warmup():
    cfg = load_config("configs/config_lanl.yaml")
    base = pd.Timestamp("1970-01-01")
    rows = []
    for d in range(6):
        for h in (10, 11):
            rows.append({"ts": base + pd.Timedelta(days=d, hours=h), "user": "U1", "host": "h1",
                         "dst_host": "h2", "orientation": "LogOn", "logon_type": "Network", "success": 1})
    rows.append({"ts": base + pd.Timedelta(days=4, hours=20), "user": "U1", "host": "h1",
                 "dst_host": "h9", "orientation": "LogOn", "logon_type": "Network", "success": 0})
    f = builder_lanl.build_daily_features(pd.DataFrame(rows), cfg)
    warm = int(cfg["features"]["warmup_days"])
    assert f["n_new_hour"].iloc[:warm].sum() == 0           # hari pemanasan tidak dihitung "jam baru"
    d4 = f[f["day"] == base + pd.Timedelta(days=4)].iloc[0]
    assert d4["n_new_hour"] == 1                            # jam 20 belum pernah dipakai user ini
    assert d4["n_fail"] == 1                                # success=0 -> autentikasi gagal
    assert set(builder_lanl.FEATURE_COLS) <= set(f.columns)
    assert f[["n_new_dst", "n_new_src", "n_new_hour"]].iloc[:warm].eq(0).all().all()


# ---------- 7) label CERT (perbaikan bug B2) ----------
def test_load_labels_keeps_only_r42_and_parses_iso_dates(tmp_path):
    d = tmp_path / "answers"
    d.mkdir()
    (d / "insiders.csv").write_text(
        "dataset,scenario,details,user,start,end\n"
        "3,1,1,USER_R3,2010-05-01 00:00:00,2010-05-02 00:00:00\n"
        "4.2,2,1,USER_A,2010-10-23 01:34:19,2010-10-25 01:34:19\n"
        "4.2,2,1,USER_B,2010-11-01 08:00:00,2010-11-03 09:00:00\n", encoding="utf-8")
    lab = load_labels(tmp_path, b"k" * 16)
    assert len(lab) == 2                                    # baris r3 dibuang
    assert lab["start"].notna().all() and lab["end"].notna().all()   # tanggal ISO terbaca
    assert lab["user"].str.len().eq(16).all()
    assert "USER" not in " ".join(lab["user"])               # sudah ter-pseudonim


def test_load_labels_raises_when_no_row_matches_the_release(tmp_path):
    d = tmp_path / "answers"
    d.mkdir()
    (d / "insiders.csv").write_text(
        "dataset,scenario,details,user,start,end\n"
        "6.2,1,1,USER_R6,2010-10-23 01:34:19,2010-10-25 01:34:19\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_labels(tmp_path, b"k" * 16)

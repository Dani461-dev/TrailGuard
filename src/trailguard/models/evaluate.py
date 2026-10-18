"""Evaluasi realistis untuk data sangat langka: alert budget + time-to-detection.

Aturan jujur yang dijaga di sini (lihat B5 & R13 di docs/01_TEAM_ROLES.md):
  * semua angka dihitung pada potongan TEST, bukan train/validasi;
  * model utama SELALU dibandingkan dengan pembanding yang memakai alert budget & potongan yang
    SAMA -- tanpa itu "precision 0.30" tidak berarti apa-apa;
  * jumlah insider yang tertangkap dihitung per ORANG, bukan per baris event;
  * pembanding "z-score" memakai deviasi fitur apa adanya, jadi kalau model kalah dari pembanding
    itu, itu harus tetap dilaporkan.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score


def alert_budget_metrics(scored: pd.DataFrame, k_per_day: int) -> dict:
    alerts = (scored.sort_values(["day", "risk"], ascending=[True, False])
                    .groupby("day").head(k_per_day))
    n_pos = int(scored["label"].sum())
    tp = int(alerts["label"].sum())
    res = {
        "alert_budget_per_day": k_per_day,
        "n_alerts": int(len(alerts)),
        "n_malicious_user_days": n_pos,
        "true_positive_alerts": tp,
        "precision_at_budget": round(tp / max(len(alerts), 1), 4),
        "recall_at_budget": round(tp / max(n_pos, 1), 4),
    }
    # Time to detection per insider (hari sejak aktivitas jahat pertama sampai alert pertama)
    ttd, missed = [], 0
    for user, g in scored[scored.label == 1].groupby("user"):
        start = g["day"].min()
        hit = alerts[(alerts.user == user) & (alerts.label == 1)]
        if hit.empty:
            missed += 1
        else:
            ttd.append((hit["day"].min() - start).days)
    res["insiders_in_test"] = len(ttd) + missed
    res["insiders_detected"] = len(ttd)
    res["median_days_to_detection"] = float(pd.Series(ttd).median()) if ttd else None
    return res


def _max_abs_z(scored: pd.DataFrame) -> np.ndarray:
    """Skor tanpa model: z-score absolut terbesar di baris itu. Sengaja sesederhana mungkin."""
    zc = [c for c in scored.columns if c.endswith("_z") or "_zscore" in c or c.endswith("_pop_z")]
    if not zc:
        return np.zeros(len(scored))
    return scored[zc].abs().max(axis=1).fillna(0).values


def baselines(scored: pd.DataFrame, k_per_day: int) -> dict:
    """Pembanding (B5) -- semuanya memakai potongan & alert budget yang sama dengan model utama."""
    rnd = scored.copy()
    rnd["risk"] = np.random.default_rng(0).random(len(rnd))
    uns = scored.copy()
    uns["risk"] = uns["p_anomaly"]
    sup = scored.copy()
    sup["risk"] = sup["p_supervised"]
    zs = scored.copy()
    zs["risk"] = _max_abs_z(scored)
    return {
        "trailguard_hybrid": {"description": "model utama: supervised + Isolation Forest (hasil tuning)",
                              **alert_budget_metrics(scored, k_per_day)},
        "supervised_only": {"description": "hanya model supervised -> apa yang hilang tanpa deteksi perilaku baru",
                            **alert_budget_metrics(sup, k_per_day)},
        "unsupervised_only": {"description": "hanya Isolation Forest -> apa yang hilang tanpa label",
                              **alert_budget_metrics(uns, k_per_day)},
        "zscore_baseline": {"description": "hanya z-score fitur terbesar -> perlu model sama sekali?",
                            **alert_budget_metrics(zs, k_per_day)},
        "random_baseline": {"description": "skor acak -> batas bawah yang jujur",
                            **alert_budget_metrics(rnd, k_per_day)},
    }


def generalization_audit(feat: pd.DataFrame, train_fraction: float, score_fn) -> dict:
    """PR-AUC di tiga potongan waktu. Selisih train -> test = seberapa besar model menghafal.
    `score_fn(df)` harus mengembalikan DataFrame dengan kolom 'risk'."""
    from .train import MIN_VAL_POSITIVES, split_last, temporal_split
    train, test, _ = temporal_split(feat, train_fraction)
    fit, val = split_last(train, 0.8, MIN_VAL_POSITIVES)
    out = {}
    for name, part in (("train", fit), ("val", val), ("test", test)):
        out[f"{name}_rows"] = int(len(part))
        out[f"{name}_positives"] = int(part["label"].sum())
        out[f"{name}_pr_auc"] = (None if part.empty or part["label"].sum() == 0
                                 else round(float(average_precision_score(part["label"], score_fn(part)["risk"])), 4))
    return out

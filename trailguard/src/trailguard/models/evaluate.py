"""Evaluasi realistis untuk data sangat langka: alert budget + time-to-detection."""
import pandas as pd


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
    # TODO(Grup B): tambah pembanding (acak, hanya-z-score, hanya-supervised) agar klaim bisa dipertanggungjawabkan.
    return res

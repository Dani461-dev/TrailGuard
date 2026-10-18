"""Latih model hibrida: supervised (pola dikenal) + Isolation Forest (perilaku baru)."""
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

try:  # HGB butuh build ekstensi; sklearn lama (mis. 0.23 di s390x) tidak memilikinya
    from sklearn.ensemble import HistGradientBoostingClassifier
except ImportError:  # pragma: no cover - tergantung lingkungan
    HistGradientBoostingClassifier = None


def temporal_split(feat: pd.DataFrame, train_fraction: float):
    """Split berdasarkan WAKTU (bukan acak) agar tidak ada kebocoran masa depan."""
    days = np.sort(feat["day"].unique())
    cut = days[int(len(days) * train_fraction)]
    return feat[feat.day < cut].copy(), feat[feat.day >= cut].copy(), cut


def train_models(train: pd.DataFrame, cfg: dict, feature_cols: list) -> dict:
    mc = cfg["model"]
    X, y = train[feature_cols].values, train["label"].values

    sup = None
    sup_model = None
    if y.sum() > 0:
        pos_w = min((len(y) - y.sum()) / max(y.sum(), 1), 50.0)   # data sangat tidak seimbang
        w = np.where(y == 1, pos_w, 1.0)
        if HistGradientBoostingClassifier is not None:
            sup = HistGradientBoostingClassifier(random_state=mc["random_state"])
            sup_model = "HistGradientBoostingClassifier"
        else:
            from sklearn.ensemble import GradientBoostingClassifier
            print("[train] HistGradientBoostingClassifier tidak tersedia "
                  "-> fallback GradientBoostingClassifier (catat di metrics: sup_model)")
            sup = GradientBoostingClassifier(random_state=mc["random_state"])
            sup_model = "GradientBoostingClassifier"
        sup.fit(X, y, sample_weight=w)
    else:
        print("[train] PERINGATAN: tidak ada label positif di train -> hanya Isolation Forest")

    iso = IsolationForest(n_estimators=mc["isolation_forest"]["n_estimators"],
                          random_state=mc["random_state"], n_jobs=-1)
    iso.fit(X[y == 0])                       # belajar "perilaku normal"
    raw = -iso.score_samples(X)
    lo, hi = np.percentile(raw, 1), np.percentile(raw, 99.9)

    normal = train[train.label == 0][feature_cols]
    return {"sup": sup, "iso": iso, "sup_model": sup_model, "an_lo": lo, "an_hi": hi,
            "base_mean": normal.mean().to_dict(), "base_std": normal.std().replace(0, 1).to_dict(),
            "feature_cols": feature_cols,
            # baris 'normal' sebagai pembanding untuk penjelasan SHAP/Shapley
            "background": normal.sample(min(200, len(normal)), random_state=mc["random_state"]).values}


def save_bundle(bundle: dict, path):
    joblib.dump(bundle, path)


def load_bundle(path) -> dict:
    return joblib.load(path)

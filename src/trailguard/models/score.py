"""Skor risiko gabungan 0..1.

Cara menggabungkan skor supervised (pola yang sudah dikenal) dengan skor anomaly (perilaku baru)
BUKAN tebakan: semua kandidat diukur di validasi temporal oleh models/train.py, dan pemenangnya
disimpan di bundle (kunci `combine_method` + `alpha`). Tiga kandidat:

  weighted -> w*sup + (1-w)*an
  max      -> ambil skor yang lebih ekstrem; satu sinyal kuat sudah cukup untuk membentuk kasus
  rank     -> rerata peringkat persentil di dalam batch. PERHATIAN: peringkat butuh pembanding
              dalam batch, sehingga skor SATU baris selalu 0.5 -> cara ini tidak boleh dipakai
              untuk endpoint /api/score (satu-per-satu). Pipeline memakainya hanya bila ia menang
              di validasi DAN seluruh evaluasi memang dilakukan per-batch.

`alpha` (bobot supervised) juga dipilih di validasi, termasuk titik 0.0 dan 1.0 -- artinya bila
hibrida tidak lebih baik dari satu model tunggal, kandidat tunggal itulah yang akan menang.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def _rank01(a: np.ndarray) -> np.ndarray:
    """Peringkat persentil 0..1 di dalam batch (skor terendah -> 0, tertinggi -> 1)."""
    if len(a) <= 1:
        return np.full(len(a), 0.5)
    return np.argsort(np.argsort(a)) / (len(a) - 1)


def combine_scores(sup: np.ndarray, an: np.ndarray, method: str = "weighted", w: float = 0.6) -> np.ndarray:
    if method == "max":
        return np.maximum(sup, an)
    if method == "rank":
        return 0.5 * (_rank01(sup) + _rank01(an))
    return w * sup + (1 - w) * an


_MIN_RANK_BATCH = 8          # di bawah ini, peringkat tidak bermakna (semua ~0.5)
_rank_fallback_warned = False


def _effective_method(bundle: dict, n: int) -> str:
    """`rank` butuh pembanding di dalam batch. Untuk skor satu-per-satu (API, penjelasan)
    peringkat selalu 0.5 -> otomatis kembali ke 'weighted' agar hasilnya tidak menyesatkan."""
    global _rank_fallback_warned
    method = bundle.get("combine_method", "weighted")
    if method == "rank" and n < _MIN_RANK_BATCH:
        if not _rank_fallback_warned:
            print(f"[score] PERINGATAN: combine_method=rank dipanggil untuk {n} baris -> "
                  "dipakai 'weighted' (peringkat butuh pembanding dalam batch)")
            _rank_fallback_warned = True
        return "weighted"
    return method


def fit_isolation(X_normal, n_estimators: int, random_state: int):
    """Isolation Forest dilatih HANYA pada baris normal (label 0)."""
    iso = IsolationForest(n_estimators=n_estimators, random_state=random_state, n_jobs=-1)
    iso.fit(X_normal)
    return iso


def iso_range(iso, X) -> tuple:
    """Persentil 1 & 99,9 dari skor anomaly -> pemetaan skor mentah ke 0..1."""
    raw = -iso.score_samples(X)
    return float(np.percentile(raw, 1)), float(np.percentile(raw, 99.9))


def anomaly01(iso, X, lo: float, hi: float) -> np.ndarray:
    return np.clip((-iso.score_samples(X) - lo) / (hi - lo + 1e-9), 0, 1)


def risk_from_array(bundle: dict, X: np.ndarray, w_sup: float = None):
    """X: array (n, n_fitur) -> (risk, p_supervised, p_anomaly). Dipakai juga oleh penjelasan SHAP.

    `w_sup=None` (bawaan) = pakai alpha hasil tuning yang tersimpan di bundle."""
    an = anomaly01(bundle["iso"], X, bundle["an_lo"], bundle["an_hi"])
    if bundle["sup"] is None:
        return an, np.zeros(len(X)), an
    sup = bundle["sup"].predict_proba(X)[:, 1]
    w = bundle.get("alpha", 0.6) if w_sup is None else w_sup
    return combine_scores(sup, an, _effective_method(bundle, len(X)), w), sup, an


def score_frame(bundle: dict, feat: pd.DataFrame, w_sup: float = None) -> pd.DataFrame:
    risk, sup, an = risk_from_array(bundle, feat[bundle["feature_cols"]].values, w_sup)
    out = feat.copy()
    out["p_supervised"], out["p_anomaly"], out["risk"] = sup, an, risk
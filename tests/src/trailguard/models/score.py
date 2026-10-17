"""Skor risiko gabungan 0..1."""
import numpy as np
import pandas as pd


def risk_from_array(bundle: dict, X: np.ndarray, w_sup: float = 0.6):
    """X: array (n, n_fitur) -> (risk, p_supervised, p_anomaly). Dipakai juga oleh penjelasan SHAP."""
    an = np.clip((-bundle["iso"].score_samples(X) - bundle["an_lo"]) /
                 (bundle["an_hi"] - bundle["an_lo"] + 1e-9), 0, 1)
    if bundle["sup"] is not None:
        sup = bundle["sup"].predict_proba(X)[:, 1]
        return w_sup * sup + (1 - w_sup) * an, sup, an
    return an, np.zeros(len(X)), an


def score_frame(bundle: dict, feat: pd.DataFrame, w_sup: float = 0.6) -> pd.DataFrame:
    risk, sup, an = risk_from_array(bundle, feat[bundle["feature_cols"]].values, w_sup)
    out = feat.copy()
    out["p_supervised"], out["p_anomaly"], out["risk"] = sup, an, risk
    # TODO(B-Model): bandingkan cara menggabungkan (rata-rata berbobot vs max vs rank) di data validasi.
    return out

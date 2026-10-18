"""Unsupervised helper for B3. Input must already be scaled with the shared Contract B scaler."""
import numpy as np
from sklearn.ensemble import IsolationForest


def train_unsupervised(X_train_scaled, y_train, n_estimators=200, max_samples="auto", random_state=42):
    """Fit IsolationForest on normal training rows only and calibrate the score range.
    Returns (model, min_s, max_s)."""
    X_train_scaled = np.asarray(X_train_scaled)
    y_train = np.asarray(y_train)
    model = IsolationForest(n_estimators=n_estimators, max_samples=max_samples,
                            contamination="auto", random_state=random_state, n_jobs=-1)
    model.fit(X_train_scaled[y_train == 0])
    raw_train_scores = -model.score_samples(X_train_scaled)
    min_s = float(np.percentile(raw_train_scores, 1))
    max_s = float(np.percentile(raw_train_scores, 99))
    return model, min_s, max_s


def get_normalized_unsup_score(model, X_scaled, min_s, max_s):
    """Anomaly score mapped to [0, 1] (higher = more anomalous)."""
    raw = -model.score_samples(np.asarray(X_scaled))
    return np.clip((raw - min_s) / (max_s - min_s + 1e-8), 0.0, 1.0)

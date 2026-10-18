import joblib
import numpy as np
import pandas as pd

def load_bundle(bundle_path: str) -> dict:
    return joblib.load(bundle_path)

def sanitize_and_log_transform(df: pd.DataFrame, feature_cols: list[str]) -> np.ndarray:
    X = df[feature_cols].to_numpy(dtype="float64", copy=True)
    for idx, col_name in enumerate(feature_cols):
        col = X[:, idx]
        if "zscore" in col_name or col_name.endswith("_z"):
            mask_artifact = np.abs(col) > 50.0
            col[mask_artifact] = col[mask_artifact] * 1e-5
            col = np.clip(col, -10.0, 10.0)
        else:
            col = np.clip(col, -1e5, 1e5)
        X[:, idx] = col
    return np.sign(X) * np.log1p(np.abs(X))

def get_normalized_unsup_score(model, X_scaled, min_s, max_s):
    raw = -model.score_samples(X_scaled)
    return np.clip((raw - min_s) / (max_s - min_s + 1e-8), 0.0, 1.0)

def score_and_explain(df_features: pd.DataFrame, bundle: dict) -> list[dict]:
    features = bundle["feature_names"]
    imputer = bundle["imputer"]
    scaler = bundle["scaler"]
    sup_model = bundle["sup_model"]
    unsup_model = bundle["unsup_model"]
    min_s, max_s = bundle["unsup_min_max"]
    alpha = bundle["alpha_weight"]
    thresholds = bundle["thresholds"]
    baseline = bundle["baseline_medians_scaled"]

    X_raw_display = df_features[features].to_numpy(dtype="float64", copy=True)
    X_log = sanitize_and_log_transform(df_features, features)
    X_scaled = scaler.transform(imputer.transform(X_log))

    p_sup = sup_model.predict_proba(X_scaled)[:, 1]
    s_unsup = get_normalized_unsup_score(unsup_model, X_scaled, min_s, max_s)
    scores = alpha * p_sup + (1 - alpha) * s_unsup

    def hybrid_func(x_2d):
        return alpha * sup_model.predict_proba(x_2d)[:, 1] + (1 - alpha) * get_normalized_unsup_score(unsup_model, x_2d, min_s, max_s)

    results = []
    for idx, row in df_features.reset_index(drop=True).iterrows():
        score = float(scores[idx])
        if score >= thresholds["tier_3_analyst_ticket"]:
            tier, approval = "Tier 3 (Analyst Ticket)", True
        elif score >= thresholds["tier_2_step_up"]:
            tier, approval = "Tier 2 (Step-Up Verification)", False
        elif score >= thresholds["tier_1_log_only"]:
            tier, approval = "Tier 1 (Log Only)", False
        else:
            tier, approval = "Normal", False

        reasons = []
        if score >= thresholds["tier_2_step_up"]:
            x_s = X_scaled[idx]
            n_f = len(features)
            base_v = float(hybrid_func(baseline.reshape(1, -1))[0])
            targ_v = float(hybrid_func(x_s.reshape(1, -1))[0])
            if abs(targ_v - base_v) >= 1e-5:
                shap_v = np.zeros(n_f)
                rng = np.random.default_rng(42)
                for _ in range(5):
                    perm = rng.permutation(n_f)
                    curr_x = baseline.copy()
                    curr_val = base_v
                    for fi in perm:
                        curr_x[fi] = x_s[fi]
                        nxt_val = float(hybrid_func(curr_x.reshape(1, -1))[0])
                        shap_v[fi] += (nxt_val - curr_val)
                        curr_val = nxt_val
                shap_v /= 5
                reasons = sorted([
                    {"feature": str(features[i]), "shapley_impact": round(float(shap_v[i]), 4), "feature_value": round(float(X_raw_display[idx, i]), 4)}
                    for i in range(n_f)
                ], key=lambda x: x["shapley_impact"], reverse=True)[:3]

        results.append({
            "dataset": bundle.get("dataset", "UNKNOWN"),
            "time_key": str(row.get("time_key", "")),
            "user_hash": str(row.get("user_hash", "")),
            "risk_score": round(score, 4),
            "sup_score": round(float(p_sup[idx]), 4),
            "unsup_score": round(float(s_unsup[idx]), 4),
            "tier": tier,
            "requires_human_approval": approval,
            "explain_method": bundle.get("explain_method", "shapley"),
            "top_reasons": reasons
        })
    return results

"""B2 LANL feature builder (hourly windows). Input users must already be hashed."""
import json
import numpy as np
import pandas as pd

# 3600 = hourly, 14400 = 4-hour. Confirm with Contract A.
WINDOW_SECONDS = 3600
# normal working hours [8, 18); everything else is off-hours
WORK_START, WORK_END = 8, 18

BASE_FEATURES = [
    "total_auth_events", "fail_auth_count", "fail_auth_ratio", "off_hours_event_ratio",
    "unique_src_computers", "unique_dst_computers", "new_dst_computer_count",
    "network_logon_ratio", "kerberos_auth_ratio",
]
Z_SOURCES = ["total_auth_events", "unique_dst_computers", "fail_auth_count"]
FEATURE_COLUMNS = BASE_FEATURES + [f"{c}_z" for c in Z_SOURCES]


def build_features(auth, redteam, window=WINDOW_SECONDS):
    df = auth.copy()
    df["timestamp"] = df["timestamp"].astype("int64")
    df = df.sort_values("timestamp", kind="stable").reset_index(drop=True)
    df["time_key"] = df["timestamp"] // window

    hour = (df["timestamp"] % 86400) // 3600
    df["is_fail"] = (df["status"] == "Fail").astype(float)
    df["is_off"] = ((hour < WORK_START) | (hour >= WORK_END)).astype(float)
    df["is_network"] = (df["logon_type"] == "Network").astype(float)
    df["is_kerberos"] = (df["auth_type"] == "Kerberos").astype(float)
    df["is_new_dst"] = (~df.duplicated(
        ["user_hash", "dst_computer"])).astype(float)

    g = df.groupby(["user_hash", "time_key"])
    feat = g.agg(
        total_auth_events=("is_fail", "size"),
        fail_auth_count=("is_fail", "sum"),
        off_sum=("is_off", "sum"),
        unique_src_computers=("src_computer", "nunique"),
        unique_dst_computers=("dst_computer", "nunique"),
        new_dst_computer_count=("is_new_dst", "sum"),
        net_sum=("is_network", "sum"),
        kerb_sum=("is_kerberos", "sum"),
    ).reset_index()

    n = feat["total_auth_events"]
    feat["fail_auth_ratio"] = feat["fail_auth_count"] / (n + 1.0)
    feat["off_hours_event_ratio"] = feat["off_sum"] / n
    feat["network_logon_ratio"] = feat["net_sum"] / n
    feat["kerberos_auth_ratio"] = feat["kerb_sum"] / n
    feat = feat.drop(columns=["off_sum", "net_sum", "kerb_sum"])

    feat = feat.sort_values(["user_hash", "time_key"]).reset_index(drop=True)
    for col in Z_SOURCES:
        grp = feat.groupby("user_hash")[col]
        mean = grp.transform(lambda s: s.shift(
            1).rolling(7, min_periods=1).mean())
        std = grp.transform(lambda s: s.shift(
            1).rolling(7, min_periods=1).std())
        feat[f"{col}_z"] = ((feat[col] - mean) /
                            (std.fillna(0.0) + 1e-8)).fillna(0.0)

    rt = redteam.copy()
    rt["time_key"] = rt["timestamp"].astype("int64") // window
    bad = set(zip(rt["user_hash"], rt["time_key"]))
    feat["label"] = [int(k in bad)
                     for k in zip(feat["user_hash"], feat["time_key"])]

    feat = feat.sort_values(["time_key", "user_hash"],
                            kind="stable").reset_index(drop=True)
    feat[FEATURE_COLUMNS] = feat[FEATURE_COLUMNS].astype("float64")
    feat = feat[["time_key", "user_hash", "label"] + FEATURE_COLUMNS]
    assert np.isfinite(feat[FEATURE_COLUMNS].to_numpy()
                       ).all(), "NaN/Inf in features"
    return feat


def build_from_files(auth_path, redteam_path, out_csv, out_json, window=WINDOW_SECONDS):
    auth = pd.read_csv(auth_path)
    red = pd.read_csv(redteam_path)
    feat = build_features(auth, red, window)
    feat.to_csv(out_csv, index=False, compression="gzip")
    with open(out_json, "w") as f:
        json.dump(FEATURE_COLUMNS, f, indent=2)
    return feat

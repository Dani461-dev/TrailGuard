"""Fitur perilaku per user per hari + deviasi terhadap baseline pribadi."""
import numpy as np
import pandas as pd

BASE_COLS = [
    "n_logon", "n_offhours_logon", "n_weekend_logon", "n_distinct_host", "n_new_host",
    "n_usb_connect", "n_file_ops", "n_http", "n_new_domain", "n_email", "n_email_ext",
    "email_ext_bytes",
]
Z_COLS = [f"{c}_z" for c in BASE_COLS]
FEATURE_COLS = BASE_COLS + Z_COLS

# Label ramah-manusia untuk penjelasan alert
FEATURE_LABELS = {
    "n_logon": "jumlah logon", "n_offhours_logon": "logon di luar jam kerja",
    "n_weekend_logon": "logon di akhir pekan", "n_distinct_host": "jumlah komputer berbeda",
    "n_new_host": "komputer yang belum pernah dipakai", "n_usb_connect": "pemakaian USB",
    "n_file_ops": "operasi file", "n_http": "kunjungan web",
    "n_new_domain": "domain web baru", "n_email": "jumlah email",
    "n_email_ext": "email ke luar organisasi", "email_ext_bytes": "volume email ke luar",
}


def build_daily_features(events: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    fc = cfg["features"]
    w0, w1 = fc["work_hours"]
    ev = events.sort_values("ts").copy()
    ev["day"] = ev["ts"].dt.floor("D")
    hour, dow = ev["ts"].dt.hour, ev["ts"].dt.dayofweek
    offh = (hour < w0) | (hour >= w1)

    is_logon = (ev.source == "logon") & (ev.action == "logon")
    first_host = ~ev.duplicated(["user", "host"])               # pertama kali user memakai host
    first_dom = (ev.source == "http") & ~ev.duplicated(["user", "source", "target"])
    # TODO(Grup B): 'baru' di hari-hari awal selalu True (cold start) -> pertimbangkan warm-up.
    ev["n_logon"] = is_logon.astype(int)
    ev["n_offhours_logon"] = (is_logon & offh).astype(int)
    ev["n_weekend_logon"] = (is_logon & (dow >= 5)).astype(int)
    ev["n_new_host"] = (is_logon & first_host).astype(int)
    ev["n_usb_connect"] = ((ev.source == "device") & (ev.action == "connect")).astype(int)
    ev["n_file_ops"] = (ev.source == "file").astype(int)
    ev["n_http"] = (ev.source == "http").astype(int)
    ev["n_new_domain"] = first_dom.astype(int)
    ev["n_email"] = (ev.source == "email").astype(int)
    ev["n_email_ext"] = (ev.action == "email_ext").astype(int)
    ev["email_ext_bytes"] = np.where(ev.action == "email_ext", ev["size"], 0)

    agg = {c: "sum" for c in BASE_COLS if c != "n_distinct_host"}
    agg["host"] = "nunique"
    feat = ev.groupby(["user", "day"]).agg(agg).rename(columns={"host": "n_distinct_host"}).reset_index()
    feat = feat.sort_values(["user", "day"]).reset_index(drop=True)

    win, minp = fc["baseline_window_days"], fc["min_baseline_days"]
    for c in BASE_COLS:
        g = feat.groupby("user")[c]
        mean = g.transform(lambda s: s.shift(1).rolling(win, min_periods=minp).mean())
        std = g.transform(lambda s: s.shift(1).rolling(win, min_periods=minp).std())
        feat[f"{c}_z"] = ((feat[c] - mean) / (std.fillna(0) + 1.0)).fillna(0.0)
    return feat


def add_labels(feat: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    feat = feat.copy()
    feat["label"] = 0
    for r in labels.itertuples(index=False):
        m = (feat.user == r.user) & (feat.day >= r.start.floor("D")) & (feat.day <= r.end.floor("D"))
        feat.loc[m, "label"] = 1
    return feat

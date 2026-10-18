"""Fitur harian untuk log autentikasi LANL (per user per hari) + deviasi terhadap baseline pribadi."""
import pandas as pd

from .builder import Z_CLIP, add_labels  # noqa: F401  (dipakai pipeline; label berbasis rentang waktu sama)

BASE_COLS = ["n_auth", "n_fail", "n_logon", "n_network_logon", "n_remote", "n_distinct_dst",
             "n_new_dst", "n_distinct_src", "n_new_src", "n_night", "n_new_hour"]
Z_COLS = [f"{c}_z" for c in BASE_COLS]
FEATURE_COLS = BASE_COLS + Z_COLS
FEATURE_LABELS = {
    "n_auth": "jumlah autentikasi", "n_fail": "autentikasi gagal", "n_logon": "jumlah logon",
    "n_network_logon": "logon jaringan (remote)", "n_remote": "autentikasi ke komputer lain",
    "n_distinct_dst": "komputer tujuan berbeda", "n_new_dst": "komputer tujuan yang belum pernah dikunjungi",
    "n_distinct_src": "komputer asal berbeda", "n_new_src": "komputer asal baru",
    "n_night": "aktivitas dini hari (proxy, bukan zona waktu nyata)",
    "n_new_hour": "aktivitas pada jam yang belum pernah dipakai user ini",
}


def build_daily_features(events: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    fc = cfg["features"]
    n0, n1 = fc.get("night_hours", [0, 6])
    ev = events.sort_values("ts").copy()
    ev["day"] = ev["ts"].dt.floor("D")
    hour = ev["ts"].dt.hour
    logon = ev.orientation == "LogOn"

    # CATATAN JUJUR: `time` LANL anonim dan zona waktunya tidak diketahui, jadi `n_night` hanyalah
    # proxy berbasis jam sejak 1970-01-01. Karena itu ditambahkan `n_new_hour`: jam yang BELUM PERNAH
    # dipakai user ini sebelumnya -- relatif terhadap kebiasaan user sendiri, jadi tidak bergantung
    # pada zona waktu sama sekali.
    ev["n_auth"] = 1
    ev["n_fail"] = (ev.success == 0).astype(int)
    ev["n_logon"] = logon.astype(int)
    ev["n_network_logon"] = (logon & (ev.logon_type == "Network")).astype(int)
    ev["n_remote"] = (ev.host != ev.dst_host).astype(int)
    ev["n_new_dst"] = (~ev.duplicated(["user", "dst_host"])).astype(int)
    ev["n_new_src"] = (~ev.duplicated(["user", "host"])).astype(int)
    ev["n_night"] = ((hour >= n0) & (hour < n1)).astype(int)
    ev["hour_of_day"] = hour
    ev["n_new_hour"] = (ev.groupby(["user", "hour_of_day"]).cumcount() == 0).astype(int)

    agg = {c: "sum" for c in BASE_COLS if c not in ("n_distinct_dst", "n_distinct_src")}
    agg.update({"dst_host": "nunique", "host": "nunique"})
    feat = (ev.groupby(["user", "day"]).agg(agg)
              .rename(columns={"dst_host": "n_distinct_dst", "host": "n_distinct_src"}).reset_index())
    feat = feat.sort_values(["user", "day"]).reset_index(drop=True)

    # Cold start: di hari-hari pertama, semua tujuan/jam terlihat "baru" (lihat builder.py).
    warmup = int(fc.get("warmup_days", fc["min_baseline_days"]))
    if warmup > 0:
        day_no = feat.groupby("user").cumcount() + 1
        feat.loc[day_no <= warmup, ["n_new_dst", "n_new_src", "n_new_hour"]] = 0

    win, minp = fc["baseline_window_days"], fc["min_baseline_days"]
    for c in BASE_COLS:
        g = feat.groupby("user")[c]
        mean = g.transform(lambda s: s.shift(1).rolling(win, min_periods=minp).mean())
        std = g.transform(lambda s: s.shift(1).rolling(win, min_periods=minp).std())
        feat[f"{c}_z"] = ((feat[c] - mean) / (std.fillna(0) + 1.0)).fillna(0.0).clip(-Z_CLIP, Z_CLIP)
    return feat

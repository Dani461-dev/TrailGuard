"""Loader LANL 'Comprehensive, Multi-Source Cyber-Security Events' (log autentikasi + label red-team).

Format (VERIFIKASI terhadap file asli, https://csr.lanl.gov/data/cyber1/):
  auth.txt(.gz)    : time,src_user@dom,dst_user@dom,src_comp,dst_comp,auth_type,logon_type,orientation,success/fail
  redteam.txt(.gz) : time,user@dom,src_comp,dst_comp
`time` = detik sejak awal data (±58 hari). File asli ~1 miliar baris -> JANGAN dimuat penuh:
pakai scripts/prefilter_lanl.py untuk membuat subset dulu, lalu loader ini membaca per-chunk.
"""
from pathlib import Path

import pandas as pd

from .pseudonymize import pseudonymize_series

AUTH_COLS = ["time", "src_user", "dst_user", "src_comp", "dst_comp",
             "auth_type", "logon_type", "orientation", "outcome"]
RED_COLS = ["time", "user", "src_comp", "dst_comp"]
EVENT_COLS = ["ts", "user", "host", "dst_host", "auth_type", "logon_type", "orientation", "success"]


def _find(raw_dir, base):
    for name in (f"{base}.gz", base):
        if (Path(raw_dir) / name).exists():
            return Path(raw_dir) / name
    raise FileNotFoundError(f"{base}(.gz) tidak ada di {raw_dir}")


def load_events(raw_dir, key, max_rows=None, hash_len=16, chunksize=2_000_000) -> pd.DataFrame:
    f = _find(raw_dir, "auth.txt")
    parts, n = [], 0
    for ch in pd.read_csv(f, names=AUTH_COLS, header=None, chunksize=chunksize, dtype=str):
        ch = ch[ch.src_user.str.startswith("U", na=False)]       # hanya akun manusia, bukan akun komputer (C123$)
        if ch.empty:
            continue
        parts.append(pd.DataFrame({
            "ts": pd.to_datetime(pd.to_numeric(ch.time), unit="s"),
            "user": pseudonymize_series(ch.src_user, key, hash_len),
            "host": pseudonymize_series(ch.src_comp, key, hash_len),
            "dst_host": pseudonymize_series(ch.dst_comp, key, hash_len),
            "auth_type": ch.auth_type, "logon_type": ch.logon_type, "orientation": ch.orientation,
            "success": (ch.outcome == "Success").astype(int)}))
        n += len(ch)
        print(f"[lanl] {n:,} baris dibaca", end="\r")
        if max_rows and n >= max_rows:
            break
    if not parts:
        raise ValueError("Tidak ada event pengguna (src_user diawali 'U') terbaca")
    print()
    return pd.concat(parts, ignore_index=True).sort_values("ts").reset_index(drop=True)[EVENT_COLS]


def load_labels(raw_dir, key, hash_len=16) -> pd.DataFrame:
    """Label = (user, waktu) event red-team. Dibuat kompatibel dgn add_labels(): start=end=waktu event."""
    df = pd.read_csv(_find(raw_dir, "redteam.txt"), names=RED_COLS, header=None, dtype=str)
    ts = pd.to_datetime(pd.to_numeric(df.time), unit="s")
    return pd.DataFrame({"user": pseudonymize_series(df.user, key, hash_len), "start": ts, "end": ts})

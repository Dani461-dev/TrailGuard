"""Loader LANL 'Comprehensive, Multi-Source Cyber-Security Events' (log autentikasi + label red-team).

Dua bentuk sumber diterima (Kontrak #1b di docs/03_DATA_CONTRACTS.md):

  a) MENTAH   auth.txt(.gz) / redteam.txt(.gz): tanpa header, id manusia & komputer apa adanya.
              -> loader inilah yang mem-pseudonim-kan (kunci dari env TRAILGUARD_HMAC_KEY).
  b) SUBSET   hasil scripts/prefilter_lanl.py (lanl_subset_auth.csv.gz, lanl_redteam_hashed.csv.gz):
              ada header dan SEMUA id sudah ter-hash saat prefilter.
              -> loader TIDAK meng-hash ulang (kalau di-hash dua kali, hash label & event tak akan cocok).

Format mentah (https://csr.lanl.gov/data/cyber1/):
  auth.txt(.gz)    : time,src_user@dom,dst_user@dom,src_comp,dst_comp,auth_type,logon_type,orientation,success/fail
  redteam.txt(.gz) : time,user@dom,src_comp,dst_comp
`time` = detik sejak awal data. File asli ~1 miliar baris -> JANGAN dimuat penuh:
jalankan scripts/prefilter_lanl.py dulu (streaming), lalu arahkan config ke folder subset.
"""
import gzip
from pathlib import Path

import pandas as pd

from .pseudonymize import pseudonymize_series

AUTH_COLS = ["time", "src_user", "dst_user", "src_comp", "dst_comp",
             "auth_type", "logon_type", "orientation", "outcome"]
RED_COLS = ["time", "user", "src_comp", "dst_comp"]
EVENT_COLS = ["ts", "user", "host", "dst_host", "auth_type", "logon_type", "orientation", "success"]

# subset prefilter didahulukan supaya `make lanl-run` tidak membaca 1 miliar baris tanpa sengaja
AUTH_NAMES = ("lanl_subset_auth.csv.gz", "lanl_subset_auth.csv", "auth.txt.gz", "auth.txt")
RED_NAMES = ("lanl_redteam_hashed.csv.gz", "lanl_redteam_hashed.csv", "redteam.txt.gz", "redteam.txt")


def _find(raw_dir, names):
    """Cari file; folder hasil ekstrak ('auth.txt/auth.txt') juga dikenali."""
    d = Path(raw_dir)
    for n in names:
        for p in (d / n, d / n / n):          # bentuk kedua = hasil ekstrak arsip
            if p.is_file():
                return p
    raise FileNotFoundError(f"{names[-1]}(.gz) tidak ada di {d} (coba: {', '.join(names)})")


def _sniff(path) -> bool:
    """True bila file berasal dari prefilter (memiliki baris header)."""
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt") as f:
        return f.readline().startswith("time,user_hash")


def _chunks(path, names, pre: bool, chunksize):
    """Baca per-chunk lalu samakan nama kolomnya dengan format mentah, agar satu jalur kode."""
    rd = pd.read_csv(path, header=0 if pre else None, names=None if pre else names,
                     chunksize=chunksize, dtype=str)
    for ch in rd:
        if pre:                                     # subset prefilter -> id sudah ter-hash
            ch = ch.rename(columns={"user_hash": "src_user", "src_host_hash": "src_comp",
                                    "dst_host_hash": "dst_comp", "status": "outcome"})
        else:                                       # file mentah -> buang akun komputer (C123$)
            ch = ch[ch.src_user.str.startswith("U", na=False)]
        if not ch.empty:
            yield ch


def load_events(raw_dir, key, max_rows=None, hash_len=16, chunksize=2_000_000) -> pd.DataFrame:
    f = _find(raw_dir, AUTH_NAMES)
    pre = _sniff(f)
    if not pre:
        print(f"[lanl] membaca file MENTAH {f.name} -> id akan di-hash di sini (kunci env)")
    else:
        print(f"[lanl] membaca SUBSET prefilter {f.name} -> id sudah ter-hash, tidak di-hash ulang")
    parts, n = [], 0
    for ch in _chunks(f, AUTH_COLS, pre, chunksize):
        idf = (lambda s: s) if pre else (lambda s: pseudonymize_series(s, key, hash_len))
        parts.append(pd.DataFrame({
            "ts": pd.to_datetime(pd.to_numeric(ch.time), unit="s"),
            "user": idf(ch.src_user), "host": idf(ch.src_comp), "dst_host": idf(ch.dst_comp),
            "auth_type": ch.auth_type, "logon_type": ch.logon_type, "orientation": ch.orientation,
            "success": (ch.outcome == "Success").astype(int)}))
        n += len(ch)
        print(f"[lanl] {n:,} baris dibaca", end="\r")
        if max_rows and n >= max_rows:
            break
    if not parts:
        raise ValueError("Tidak ada event pengguna terbaca (akun komputer 'C123$' sengaja dibuang)")
    print()
    return pd.concat(parts, ignore_index=True).sort_values("ts").reset_index(drop=True)[EVENT_COLS]


def load_labels(raw_dir, key, hash_len=16) -> pd.DataFrame:
    """Label = (user, waktu) event red-team. Dibuat kompatibel dgn add_labels(): start=end=waktu event."""
    f = _find(raw_dir, RED_NAMES)
    pre = _sniff(f)
    df = pd.read_csv(f, header=0 if pre else None, names=None if pre else RED_COLS, dtype=str)
    if pre:
        df = df.rename(columns={"user_hash": "user"})
    else:
        df["user"] = pseudonymize_series(df["user"], key, hash_len)
    ts = pd.to_datetime(pd.to_numeric(df.time), unit="s")
    return pd.DataFrame({"user": df["user"], "start": ts, "end": ts})

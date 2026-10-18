"""Memuat log CERT (atau toy) -> satu tabel event terpadu + label.

Skema event terpadu (lihat docs/03_DATA_CONTRACTS.md):
    ts (datetime) | user (hash) | host (hash) | source | action | target | size
"""
from pathlib import Path

import pandas as pd

from .pseudonymize import pseudonymize_series

DATE_FMT = "%m/%d/%Y %H:%M:%S"     # log mentah CERT
LABEL_FMTS = (DATE_FMT, "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d")
CERT_RELEASE = "4.2"                # hanya jawaban r4.2 yang dipakai (bukan r2/r3/r6)
EVENT_COLS = ["ts", "user", "host", "source", "action", "target", "size"]


def _to_ts(s: pd.Series) -> pd.Series:
    """Tanggal CERT punya dua bentuk: log memakai '%m/%d/%Y %H:%M:%S', file jawaban memakai ISO
    ('2010-10-23 01:34:19'). Coba semua format; baris yang tetap gagal dibuang (errors='coerce')."""
    ts = pd.to_datetime(s, format=DATE_FMT, errors="coerce")
    miss = ts.isna() & s.notna()
    if miss.any():                              # fallback: ISO & tanggal saja
        ts[miss] = pd.to_datetime(s[miss], errors="coerce")
    return ts


def _read(raw_dir: Path, name: str, usecols, nrows=None):
    f = raw_dir / f"{name}.csv"
    if not f.exists():
        print(f"[loader] {f.name} tidak ada -> dilewati")
        return None
    # http.csv asli ~14 GB: batasi dengan ingest.max_rows_per_file bila memori terbatas.
    df = pd.read_csv(f, usecols=lambda c: c in usecols, nrows=nrows)
    df["ts"] = _to_ts(df["date"])
    return df.dropna(subset=["ts"])


def _ext(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if isinstance(name, str) and "." in name else ""


def _domain(url: str) -> str:
    if not isinstance(url, str):
        return ""
    u = url.split("//", 1)[-1]
    return u.split("/", 1)[0].lower()


def load_events(raw_dir, key: bytes, company_domain="dtaa.com", max_rows=None, hash_len=16):
    raw_dir = Path(raw_dir)
    parts = []

    d = _read(raw_dir, "logon", {"date", "user", "pc", "activity"}, max_rows)
    if d is not None:
        parts.append(pd.DataFrame({"ts": d.ts, "user": d.user, "host": d.pc, "source": "logon",
                                   "action": d.activity.str.lower(), "target": "", "size": 0}))
    d = _read(raw_dir, "device", {"date", "user", "pc", "activity"}, max_rows)
    if d is not None:
        parts.append(pd.DataFrame({"ts": d.ts, "user": d.user, "host": d.pc, "source": "device",
                                   "action": d.activity.str.lower(), "target": "usb", "size": 0}))
    d = _read(raw_dir, "file", {"date", "user", "pc", "filename"}, max_rows)
    if d is not None:
        parts.append(pd.DataFrame({"ts": d.ts, "user": d.user, "host": d.pc, "source": "file",
                                   "action": "file_op", "target": d.filename.map(_ext), "size": 0}))
    d = _read(raw_dir, "http", {"date", "user", "pc", "url"}, max_rows)
    if d is not None:
        parts.append(pd.DataFrame({"ts": d.ts, "user": d.user, "host": d.pc, "source": "http",
                                   "action": "visit", "target": d.url.map(_domain), "size": 0}))
    d = _read(raw_dir, "email", {"date", "user", "pc", "to", "size", "attachments"}, max_rows)
    if d is not None:
        ext = ~d.to.fillna("").str.contains(company_domain, regex=False)
        parts.append(pd.DataFrame({"ts": d.ts, "user": d.user, "host": d.pc, "source": "email",
                                   "action": ext.map({True: "email_ext", False: "email_int"}),
                                   "target": "", "size": d["size"].fillna(0)}))
    if not parts:
        raise FileNotFoundError(f"Tidak ada file log di {raw_dir}")

    ev = pd.concat(parts, ignore_index=True).sort_values("ts").reset_index(drop=True)
    # PSEUDONIMISASI di pintu masuk: setelah ini tidak ada ID asli di memori/disk turunan.
    ev["user"] = pseudonymize_series(ev["user"], key, hash_len)
    ev["host"] = pseudonymize_series(ev["host"], key, hash_len)
    return ev[EVENT_COLS]


def load_labels(raw_dir, key: bytes, hash_len=16) -> pd.DataFrame:
    """Label insider: user + rentang tanggal aktivitas jahat.

    Sumber = answers/insiders.csv (CERT r4.2 maupun data tiruan). Format file jawaban ASLI r4.2:
        dataset,scenario,details,user,start,end
        4.2,2,4058435,ACM2278,2010-10-23 01:34:19,2010-10-25 01:34:19
    Dua jebakan yang sudah ditangani di sini:
      1. kolom `dataset` berisi campuran r2/r3/r4.2/r6 -> WAJIB difilter, kalau tidak labelnya salah;
      2. tanggal memakai ISO, BUKAN format '%m/%d/%Y %H:%M:%S' -> kalau dipaksa, semua jadi NaT
         lalu terbuang diam-diam dan metrik jadi nol.
    """
    f = Path(raw_dir) / "answers" / "insiders.csv"
    if not f.exists():
        print(f"[loader] PERINGATAN: {f} tidak ada -> tanpa label (semua skor jadi tak berlabel)")
        return pd.DataFrame({"user": pd.Series(dtype=str),
                             "start": pd.Series(dtype="datetime64[ns]"),
                             "end": pd.Series(dtype="datetime64[ns]")})
    df = pd.read_csv(f)
    df.columns = [c.lower().strip() for c in df.columns]
    n_all = len(df)
    if "dataset" in df.columns:                      # hanya r4.2 ('4.2', 4.2, atau 'r4.2')
        rel = df["dataset"].astype(str).str.strip().str.lower().str.lstrip("r")
        df = df[rel == CERT_RELEASE].copy()
        if df.empty:
            print(f"[loader] PERINGATAN: tak ada baris dataset={CERT_RELEASE} di {f.name} "
                  f"(total {n_all} baris) -> periksa nilai kolom 'dataset'")
        elif len(df) != n_all:
            print(f"[loader] label: {len(df):,} dari {n_all:,} baris dipakai (hanya r{CERT_RELEASE})")
    df["start"], df["end"] = _to_ts(df["start"]), _to_ts(df["end"])
    n_bad = int(df["start"].isna().sum() + df["end"].isna().sum())
    if n_bad:
        print(f"[loader] PERINGATAN: {n_bad} tanggal label tidak terbaca -> baris dibuang")
    if df.empty:
        raise ValueError(f"Label kosong dari {f} -- periksa format tanggal & kolom 'dataset'")
    df["user"] = pseudonymize_series(df["user"], key, hash_len)
    return df[["user", "start", "end"]].dropna()

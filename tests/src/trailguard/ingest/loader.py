"""Memuat log CERT (atau toy) -> satu tabel event terpadu + label.

Skema event terpadu (lihat docs/03_DATA_CONTRACTS.md):
    ts (datetime) | user (hash) | host (hash) | source | action | target | size
"""
from pathlib import Path

import pandas as pd

from .pseudonymize import pseudonymize_series

DATE_FMT = "%m/%d/%Y %H:%M:%S"
EVENT_COLS = ["ts", "user", "host", "source", "action", "target", "size"]


def _read(raw_dir: Path, name: str, usecols, nrows=None):
    f = raw_dir / f"{name}.csv"
    if not f.exists():
        print(f"[loader] {f.name} tidak ada -> dilewati")
        return None
    # TODO(Grup B/C): untuk http.csv asli yang sangat besar, baca per-chunk / filter user.
    df = pd.read_csv(f, usecols=lambda c: c in usecols, nrows=nrows)
    df["ts"] = pd.to_datetime(df["date"], format=DATE_FMT, errors="coerce")
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
    Format toy = format CERT answers/insiders.csv (kolom: user,start,end).
    TODO(Grup B): cocokkan dengan format file jawaban CERT r4.2 yang sebenarnya.
    """
    f = Path(raw_dir) / "answers" / "insiders.csv"
    df = pd.read_csv(f)
    df.columns = [c.lower() for c in df.columns]
    df["start"] = pd.to_datetime(df["start"], format=DATE_FMT, errors="coerce")
    df["end"] = pd.to_datetime(df["end"], format=DATE_FMT, errors="coerce")
    df["user"] = pseudonymize_series(df["user"], key, hash_len)
    return df[["user", "start", "end"]].dropna()

"""Baca/tulis tabel antar-langkah. CSV.gz = default (jalan di mana saja).
Parquet = dipakai bila io.format=parquet DAN pyarrow terpasang; jika pyarrow tidak ada -> otomatis CSV + peringatan."""
import pandas as pd

from .config import path_of

_warned = False


def table_format(cfg) -> str:
    global _warned
    fmt = cfg.get("io", {}).get("format", "csv")
    if fmt == "parquet":
        try:
            import pyarrow  # noqa: F401
        except Exception as e:
            if not _warned:
                print(f"[io] PERINGATAN: pyarrow tidak bisa dipakai ({type(e).__name__}) -> fallback CSV. "
                      "Jangan klaim Parquet/pyarrow di pitch.")
                _warned = True
            return "csv"
    return fmt


def table_path(cfg, key):
    p = path_of(cfg, key)
    return p.with_name(p.name.split(".")[0] + ".parquet") if table_format(cfg) == "parquet" else p


def write_table(df: pd.DataFrame, cfg, key):
    p = table_path(cfg, key)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p, index=False) if p.suffix == ".parquet" else df.to_csv(p, index=False)
    return p


def read_table(cfg, key, parse_dates=None) -> pd.DataFrame:
    p = table_path(cfg, key)
    if not p.exists():
        raise FileNotFoundError(f"{p} belum ada. Jalankan langkah sebelumnya di pipeline.")
    return pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p, parse_dates=parse_dates)

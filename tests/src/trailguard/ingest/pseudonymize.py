"""Pseudonimisasi: ID asli -> keyed hash (HMAC-SHA256).

Catatan jujur untuk pitch: ini PSEUDONIMISASI (mengurangi eksposur), bukan anonimisasi
dan bukan jaminan privasi formal. Kunci tidak boleh keluar dari instance.
"""
import hashlib
import hmac
import os

import pandas as pd


def get_key(env_var: str = "TRAILGUARD_HMAC_KEY") -> bytes:
    key = os.environ.get(env_var)
    if not key or key.startswith("ganti_dengan"):
        raise RuntimeError(
            f"{env_var} belum diset. Salin .env.example ke .env lalu isi kunci acak, "
            "kemudian jalankan: set -a; source .env; set +a"
        )
    return key.encode()


def pseudonymize(value: str, key: bytes, length: int = 16) -> str:
    return hmac.new(key, str(value).encode(), hashlib.sha256).hexdigest()[:length]


def pseudonymize_series(s: pd.Series, key: bytes, length: int = 16) -> pd.Series:
    """Hash tiap nilai unik sekali saja (cepat untuk data besar)."""
    mapping = {v: pseudonymize(v, key, length) for v in s.dropna().unique()}
    return s.map(mapping)

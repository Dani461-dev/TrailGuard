"""Menyaring auth.txt.gz LANL (~1 miliar baris) menjadi subset yang muat di VM.  STREAMING, memori kecil.

Strategi: simpan SEMUA baris dari user yang ada di redteam.txt (korban) + sampel acak-deterministik
user lain (fraksi --user-fraction) + hanya akun manusia (diawali 'U') + (opsional) batas waktu.

Contoh:
  python scripts/prefilter_lanl.py --src data/raw/lanl_full --out data/raw/lanl_sub \
         --user-fraction 0.02 --max-day 58
Estimasi waktu: pure-Python ±1–3 juta baris/detik di x86; s390x bisa lebih lambat -> UKUR dengan --max-lines
dulu (mis. 5_000_000), jalankan di tmux, dan cek `df -h` sebelum menyalin file ±7 GB.
"""
import argparse
import gzip
import hashlib
import shutil
import time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--src", required=True, help="folder berisi auth.txt.gz & redteam.txt.gz")
ap.add_argument("--out", required=True)
ap.add_argument("--user-fraction", type=float, default=0.02, help="fraksi user non-red-team yang disimpan")
ap.add_argument("--max-day", type=float, default=None, help="buang event setelah hari ke-N")
ap.add_argument("--max-lines", type=int, default=None, help="berhenti setelah N baris (untuk uji kecepatan)")
a = ap.parse_args()

src, out = Path(a.src), Path(a.out)
out.mkdir(parents=True, exist_ok=True)
shutil.copy(src / "redteam.txt.gz", out / "redteam.txt.gz")
with gzip.open(src / "redteam.txt.gz", "rt") as f:
    red_users = {line.split(",")[1] for line in f if line.strip()}
print(f"user red-team: {len(red_users)}")

def keep_user(u: str) -> bool:
    if u in red_users:
        return True
    return int(hashlib.md5(u.encode()).hexdigest(), 16) % 10000 < a.user_fraction * 10000

max_t = a.max_day * 86400 if a.max_day else None
n_in = n_out = 0
cache = {}
t0 = time.time()
with gzip.open(src / "auth.txt.gz", "rt") as fin, gzip.open(out / "auth.txt.gz", "wt") as fout:
    for line in fin:
        n_in += 1
        p = line.split(",", 2)
        u = p[1]
        if u[:1] == "U":
            k = cache.get(u)
            if k is None:
                k = cache[u] = keep_user(u)
            if k and (max_t is None or float(p[0]) <= max_t):
                fout.write(line)
                n_out += 1
        if n_in % 20_000_000 == 0:
            print(f"{n_in:,} baca | {n_out:,} simpan | {n_in / (time.time() - t0):,.0f} baris/dtk")
        if a.max_lines and n_in >= a.max_lines:
            break
print(f"selesai: {n_in:,} baca -> {n_out:,} simpan dalam {time.time() - t0:.0f}s -> {out}")

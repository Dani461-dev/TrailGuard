"""Prefilter LANL: auth.txt -> subset kecil + pseudonimisasi HMAC (streaming).

Kunci diambil dari env TRAILGUARD_HMAC_KEY (lihat .env.example) -- TIDAK ditulis di kode,
dan hanya dipakai di dalam instance. SEMUA id (user, komputer asal, komputer tujuan) di-hash
di sini, sehingga file subset bebas identitas mentah (Kontrak #1b)."""
import argparse, csv, gzip, hmac, hashlib, os, sys, time, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from trailguard.ingest.pseudonymize import get_key  # noqa: E402  (kunci hanya dari env)
_cache = {}
SALT_KEY = None            # diisi di main() dari env TRAILGUARD_HMAC_KEY

def hash_id(value: str) -> str:
    """HMAC-SHA256 keyed -> 16 hex. Nilai apa pun (user ATAU komputer) memakai kunci yang sama."""
    v = str(value).strip()
    h = _cache.get(v)
    if h is None:
        h = hmac.new(SALT_KEY, v.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
        _cache[v] = h
    return h

def is_system_account(user: str) -> bool:
    name = user.split("@")[0]                       # "C123$@DOM1" -> "C123$"
    return name.startswith("ANONYMOUS") or name.endswith("$")

def open_auto(filepath: str, mode: str = "rt"):
    """Membaca file .gz, file teks biasa, maupun file di dalam subfolder ekstraksi."""
    path = Path(filepath)
    
    # Jika path ternyata adalah folder, ambil file di dalam folder tersebut
    if path.is_dir():
        inside_file = path / path.name
        if inside_file.exists():
            path = inside_file

    if not path.exists():
        alt_path = path.with_suffix("") if path.suffix == ".gz" else Path(str(path) + ".gz")
        if alt_path.exists():
            path = alt_path
        else:
            raise FileNotFoundError(f"File tidak ditemukan: {filepath}")
            
    if str(path).endswith(".gz"):
        return gzip.open(path, mode)
    return open(path, mode, encoding="utf-8", errors="ignore")

def main():
    ap = argparse.ArgumentParser()
    default_auth = str(ROOT / "auth.txt") if (ROOT / "auth.txt").exists() else str(ROOT / "auth.txt.gz")
    default_red = str(ROOT / "redteam.txt") if (ROOT / "redteam.txt").exists() else str(ROOT / "redteam.txt.gz")

    ap.add_argument("--auth", default=default_auth)
    ap.add_argument("--redteam", default=default_red)
    ap.add_argument("--out-auth", default=str(ROOT / "data/raw/lanl_subset_auth.csv.gz"))
    ap.add_argument("--out-red", default=str(ROOT / "data/raw/lanl_redteam_hashed.csv.gz"))
    
    # Perbaikan: gunakan %%1000 agar argparse tidak error
    ap.add_argument("--normal-per-mille", type=int, default=25,
                    help="user normal diambil jika crc32(user)%%1000 < nilai ini")
    ap.add_argument("--margin-days", type=float, default=2.0,
                    help="potong data setelah red-team terakhir + margin")
    ap.add_argument("--max-lines", type=int, default=0, help="0 = semua (untuk uji coba isi mis. 2000000)")
    a = ap.parse_args()
    global SALT_KEY
    SALT_KEY = get_key()                    # kunci hanya dari env; gagal = pesan jelas, bukan nilaianya
    Path(a.out_auth).parent.mkdir(parents=True, exist_ok=True)

    # 1) redteam -> himpunan user korban + waktu terakhir
    redteam_users, red_rows = set(), []
    with open_auto(a.redteam, "rt") as f:
        for line in f:
            p = line.strip().split(",")
            if len(p) < 4:
                continue
            red_rows.append((int(p[0]), p[1], p[2], p[3]))
            redteam_users.add(p[1])
    t_last = max(r[0] for r in red_rows)
    t_max = t_last + int(a.margin_days * 86400)
    print(f"[redteam] events={len(red_rows)} users={len(redteam_users)} "
          f"t_first={min(r[0] for r in red_rows)} t_last={t_last} -> cutoff auth di t<={t_max}")

    with gzip.open(a.out_red, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time", "user_hash", "src_host_hash", "dst_host_hash"])
        for t, u, s, d in red_rows:
            w.writerow([t, hash_id(u), hash_id(s), hash_id(d)])

    # 2) stream auth (urut waktu -> boleh berhenti saat t > t_max)
    decision, n_read, n_keep = {}, 0, 0
    t0 = time.time()
    with open_auto(a.auth, "rt") as fin, gzip.open(a.out_auth, "wt", newline="") as fout:
        w = csv.writer(fout)
        w.writerow(["time", "user_hash", "src_host_hash", "dst_host_hash",
                    "auth_type", "logon_type", "orientation", "status"])
        for line in fin:
            n_read += 1
            if a.max_lines and n_read > a.max_lines:
                break
            if n_read % 20_000_000 == 0:
                print(f"  {n_read/1e6:.0f}M baris | kept={n_keep} | {time.time()-t0:.0f}s")
            head = line.split(",", 2)
            t = int(head[0])
            if t > t_max:
                break
            user = head[1]
            d = decision.get(user)
            if d is None:
                if is_system_account(user):
                    d = 0
                elif user in redteam_users:
                    d = 2
                elif zlib.crc32(user.encode()) % 1000 < a.normal_per_mille:
                    d = 1
                else:
                    d = 0
                decision[user] = d
            if d == 0:
                continue
            p = line.rstrip("\n").split(",")
            if len(p) != 9:
                continue
            w.writerow([p[0], hash_id(user), hash_id(p[3]), hash_id(p[4]), p[5], p[6], p[7], p[8]])
            n_keep += 1

    n_red = sum(1 for v in decision.values() if v == 2)
    n_norm = sum(1 for v in decision.values() if v == 1)
    print(f"[selesai] baca={n_read} simpan={n_keep} | user redteam ditemukan={n_red}/{len(redteam_users)} "
          f"| user normal={n_norm} | {time.time()-t0:.0f}s")

if __name__ == "__main__":
    main()
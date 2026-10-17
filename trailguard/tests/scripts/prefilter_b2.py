"""Streaming pre-filter for LANL auth.txt.gz. Raw user IDs are never written to disk.
Usage:
  python scripts/prefilter_lanl.py                      # full run
  python scripts/prefilter_lanl.py --limit 5000000      # quick test on first 5M lines
"""
import argparse
import gzip
import csv
import zlib
import hmac
import hashlib

SALT_KEY = b"TRAILGUARD_GROUP_B_SALT_2026"


def hash_user(u):
    return hmac.new(SALT_KEY, str(u).strip().encode("utf-8"), hashlib.sha256).hexdigest()[:16]


def is_machine(user):
    name = user.split("@")[0]
    return name.startswith("ANONYMOUS") or name.endswith("$")


def keep_normal(user, threshold):
    return zlib.crc32(user.encode()) % 1000 < threshold


ap = argparse.ArgumentParser()
ap.add_argument("--auth", default="data/raw/auth.txt.gz")
ap.add_argument("--red", default="data/raw/redteam.txt.gz")
ap.add_argument("--out", default="data/raw/lanl_subset_auth.csv.gz")
ap.add_argument("--red-out", default="data/raw/lanl_redteam_hashed.csv.gz")
ap.add_argument("--limit", type=int, default=None)
ap.add_argument("--threshold", type=int, default=15,
                help="out of 1000; 15 is about 1.5 percent of users")
a = ap.parse_args()

redteam_users = set()
with gzip.open(a.red, "rt") as f, gzip.open(a.red_out, "wt", newline="") as fo:
    w = csv.writer(fo)
    w.writerow(["timestamp", "user_hash", "src_computer", "dst_computer"])
    for line in f:
        p = line.strip().split(",")
        redteam_users.add(p[1])
        w.writerow([p[0], hash_user(p[1]), p[2], p[3]])
print("redteam users:", len(redteam_users))

kept = set()
normal_kept = set()
with gzip.open(a.auth, "rt") as fin, gzip.open(a.out, "wt", newline="") as fout:
    w = csv.writer(fout)
    w.writerow(["timestamp", "user_hash", "src_computer", "dst_computer",
                "auth_type", "logon_type", "orientation", "status"])
    try:
        for i, line in enumerate(fin):
            if a.limit and i > a.limit:
                break
            if i % 50_000_000 == 0:
                print(i, "lines read", flush=True)
            p = line.rstrip("\n").split(",")
            if len(p) != 9:
                continue
            user = p[1]
            if is_machine(user):
                continue
            if user in redteam_users or keep_normal(user, a.threshold):
                kept.add(user)
                if user not in redteam_users:
                    normal_kept.add(user)
                w.writerow([p[0], hash_user(user)] + p[3:])
    except EOFError:
        print("Hit the end of a partial file")
print("users kept:", len(kept), "| normal users kept:", len(normal_kept))

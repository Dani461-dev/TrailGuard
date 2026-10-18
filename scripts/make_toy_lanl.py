"""Data tiruan berformat LANL (auth.txt.gz + redteam.txt.gz) untuk menguji jalur LANL.
Pakai:  python scripts/make_toy_lanl.py [folder_output]
"""
import gzip
import random
import sys
from pathlib import Path

random.seed(11)
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "data/raw/lanl_toy")
OUT.mkdir(parents=True, exist_ok=True)
DAYS, N_USERS, N_COMP = 40, 50, 80
red = {7: (18, 28), 19: (22, 32), 33: (25, 35)}          # user index -> (hari mulai, hari selesai)
auth, redteam = [], []
for d in range(DAYS):
    for u in range(N_USERS):
        usual = [f"C{(u * 3 + k) % N_COMP}" for k in range(3)]
        is_red = u in red and red[u][0] <= d <= red[u][1]
        for _ in range(random.randint(15, 30)):
            t = d * 86400 + random.randint(8, 17) * 3600 + random.randint(0, 3599)
            c = random.choice(usual)
            ok = "Success" if random.random() > 0.02 else "Fail"
            auth.append((t, f"U{u}@DOM1", f"U{u}@DOM1", usual[0], c, "Kerberos", random.choice(["Network", "Interactive"]), "LogOn", ok))
        auth.append((d * 86400 + 9 * 3600, f"C{u}$@DOM1", f"C{u}$@DOM1", f"C{u}", f"C{u}", "Kerberos", "Network", "LogOn", "Success"))  # akun komputer (harus difilter)
        if is_red:
            for _ in range(random.randint(10, 25)):
                t = d * 86400 + random.randint(1, 4) * 3600 + random.randint(0, 3599)
                dst = f"C{random.randint(0, N_COMP - 1)}"
                ok = "Success" if random.random() > 0.35 else "Fail"
                auth.append((t, f"U{u}@DOM1", f"U{u}@DOM1", usual[0], dst, "NTLM", "Network", "LogOn", ok))
                redteam.append((t, f"U{u}@DOM1", usual[0], dst))
auth.sort()
with gzip.open(OUT / "auth.txt.gz", "wt") as f:
    for r in auth:
        f.write(",".join(map(str, r)) + "\n")
with gzip.open(OUT / "redteam.txt.gz", "wt") as f:
    for r in sorted(redteam):
        f.write(",".join(map(str, r)) + "\n")
print(f"LANL toy -> {OUT}  ({len(auth):,} auth, {len(redteam)} red-team, {len(red)} user disusupi)")

"""Toy LANL-format data for testing the B2 pipeline."""
import gzip
import random

random.seed(42)
DAY = 86400
N_DAYS, N_NORMAL, N_RED = 30, 80, 5
COMPS = [f"C{i}" for i in range(1, 61)]


def work_time(day):
    return day * DAY + random.randint(8, 17) * 3600 + random.randint(0, 3599)


rows, red_rows = [], []
users = [(f"U{i}@DOM1", False) for i in range(N_NORMAL)] + \
    [(f"R{i}@DOM1", True) for i in range(N_RED)]

for u, is_red in users:
    home = random.choice(COMPS)
    usual = random.sample(COMPS, 5)
    for d in range(N_DAYS):
        for _ in range(random.randint(8, 20)):
            dst = random.choice(usual)
            rows.append((work_time(d), u, u, home, dst,
                         random.choice(["Kerberos", "NTLM", "Kerberos"]),
                         random.choice(["Interactive", "Network", "Network"]),
                         "LogOn",
                         "Fail" if random.random() < 0.03 else "Success"))
        if is_red and d >= 21 and random.random() < 0.8:
            hr = random.choice([1, 2, 3, 22, 23])
            for _ in range(random.randint(15, 30)):
                t = d * DAY + hr * 3600 + random.randint(0, 3599)
                dst = random.choice(COMPS)
                rows.append((t, u, u, home, dst, "NTLM", "Network", "LogOn",
                             "Fail" if random.random() < 0.25 else "Success"))
                if random.random() < 0.2:
                    red_rows.append((t, u, home, dst))

for d in range(N_DAYS):
    rows.append((work_time(d), "C1$@DOM1", "C1$@DOM1", "C1", "C2",
                 "Kerberos", "Network", "LogOn", "Success"))

rows.sort()
with gzip.open("data/raw/auth_toy.txt.gz", "wt") as f:
    for r in rows:
        f.write(",".join(map(str, r)) + "\n")
with gzip.open("data/raw/redteam_toy.txt.gz", "wt") as f:
    for r in sorted(red_rows):
        f.write(",".join(map(str, r)) + "\n")
print("auth rows:", len(rows), "| redteam rows:", len(red_rows))

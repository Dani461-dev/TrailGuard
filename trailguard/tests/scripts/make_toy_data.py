"""Buat data tiruan berformat CERT agar semua grup bisa mulai tanpa menunggu dataset asli.
Pakai:  python scripts/make_toy_data.py [folder_output]
"""
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

random.seed(7)
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "data/raw/toy")
(OUT / "answers").mkdir(parents=True, exist_ok=True)
FMT = "%m/%d/%Y %H:%M:%S"
START, DAYS, N_USERS = datetime(2010, 1, 4), 90, 60
users = [f"USR{i:04d}" for i in range(N_USERS)]
home = {u: f"PC-{i:04d}" for i, u in enumerate(users)}
domains = ["news.example", "wiki.example", "docs.example", "mail.example", "shop.example", "dev.example"]
# insider: (user, hari_mulai, hari_selesai)
insiders = [(users[3], 30, 40), (users[10], 55, 65), (users[22], 62, 72), (users[41], 75, 85)]

rows = {k: [] for k in ["logon", "device", "file", "http", "email"]}
n = 0
def eid():
    global n; n += 1; return f"E{n:08d}"
def ts(day, hour, minute=None):
    return (START + timedelta(days=day, hours=hour, minutes=minute if minute is not None else random.randint(0, 59))).strftime(FMT)

for d in range(DAYS):
    dt = START + timedelta(days=d)
    if dt.weekday() >= 5:
        continue
    for u in users:
        bad = any(u == iu and s <= d <= e for iu, s, e in insiders)
        pc = home[u]
        rows["logon"].append((eid(), ts(d, random.randint(8, 9)), u, pc, "Logon"))
        rows["logon"].append((eid(), ts(d, random.randint(17, 18)), u, pc, "Logoff"))
        for _ in range(random.randint(2, 8)):
            rows["file"].append((eid(), ts(d, random.randint(9, 16)), u, pc, f"doc{random.randint(1,50)}.{random.choice(['docx','pdf','txt'])}"))
        for _ in range(random.randint(6, 18)):
            rows["http"].append((eid(), ts(d, random.randint(9, 17)), u, pc, f"http://{random.choice(domains)}/p{random.randint(1,99)}"))
        for _ in range(random.randint(1, 4)):
            rows["email"].append((eid(), ts(d, random.randint(9, 17)), u, pc, f"{random.choice(users)}@dtaa.com", random.randint(2000, 30000), 0))
        if random.random() < 0.02:                         # USB normal, jarang
            rows["device"].append((eid(), ts(d, 12), u, pc, "Connect"))
        if bad:                                            # perilaku insider
            other = f"PC-{random.randint(900, 999):04d}"
            rows["logon"].append((eid(), ts(d, random.randint(22, 23)), u, other, "Logon"))
            rows["device"].append((eid(), ts(d, 23), u, other, "Connect"))
            for _ in range(random.randint(25, 45)):
                rows["file"].append((eid(), ts(d, 23), u, other, f"secret{random.randint(1,300)}.zip"))
            for _ in range(random.randint(3, 8)):
                rows["http"].append((eid(), ts(d, 22), u, other, f"http://jobsite{random.randint(1,40)}.example/apply"))
            for _ in range(random.randint(2, 5)):
                rows["email"].append((eid(), ts(d, 22), u, other, "someone@gmail.com", random.randint(500000, 3000000), 2))

hdr = {"logon": "id,date,user,pc,activity", "device": "id,date,user,pc,activity",
       "file": "id,date,user,pc,filename", "http": "id,date,user,pc,url",
       "email": "id,date,user,pc,to,size,attachments"}
for name, data in rows.items():
    with open(OUT / f"{name}.csv", "w") as f:
        f.write(hdr[name] + "\n")
        for r in data:
            f.write(",".join(map(str, r)) + "\n")
with open(OUT / "answers" / "insiders.csv", "w") as f:
    f.write("user,start,end\n")
    for u, s, e in insiders:
        f.write(f"{u},{(START + timedelta(days=s)).strftime(FMT)},{(START + timedelta(days=e)).strftime(FMT)}\n")
print(f"Toy data -> {OUT}  ({sum(len(v) for v in rows.values()):,} event, {len(insiders)} insider)")

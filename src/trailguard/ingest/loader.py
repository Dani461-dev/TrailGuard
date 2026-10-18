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


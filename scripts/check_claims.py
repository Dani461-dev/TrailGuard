"""Guard klaim: setiap angka di bagian "Results" README harus ada di outputs/*_metrics.json.

Aturan docs (`docs/04_SUBMISSION_CHECKLIST.md` bagian D): angka performa hanya boleh berasal dari
file metrik, split temporal, alert budget -- bukan accuracy, bukan angka data toy. Skrip ini
menegakkannya secara mekanis supaya README tidak bisa "melenceng" dari artefak.

Jalankan (dari root repo):   python scripts/check_claims.py
Kode keluar 1 bila ada angka yang tak dapat ditelusuri -> bisa dipakai di CI/Makefile.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
METRICS = [ROOT / "outputs/metrics.json", ROOT / "outputs/lanl_metrics.json"]


def _floats(obj, out):
    if isinstance(obj, dict):
        for v in obj.values():
            _floats(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _floats(v, out)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        out.append(float(obj))


def results_section(text: str) -> str:
    m = re.search(r"^## Results\s*$(.*?)^## ", text, flags=re.S | re.M)
    return m.group(1) if m else ""


def main() -> int:
    text = README.read_text(encoding="utf-8")
    pool = []
    for p in METRICS:
        if p.exists():
            _floats(json.loads(p.read_text(encoding="utf-8")), pool)
    if not pool:
        print("[claims] TIDAK ADA file metrik -> tak bisa memverifikasi (jalankan `make run` dulu)")
        return 1

    section = results_section(text)
    if not section:
        print("[claims] bagian '## Results' tidak ditemukan di README")
        return 1

    quoted = sorted(set(re.findall(r"(?<![\w.])\d+\.\d+", section)))
    bad = []
    for token in quoted:
        dec = len(token.split(".")[1])
        val = float(token)
        if not any(round(m, dec) == val for m in pool):
            bad.append(token)

    print(f"[claims] {len(quoted)} angka di bagian Results; {len(quoted) - len(bad)} tertelusur")
    if bad:
        print("[claims] GAGAL - angka berikut tak ada di file metrik:", ", ".join(bad))
        return 1
    print("[claims] OK - semua angka Results dapat ditelusuri ke file metrik")
    return 0


if __name__ == "__main__":
    sys.exit(main())

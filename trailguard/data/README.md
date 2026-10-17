# Data

> Folder `raw/`, `interim/`, `processed/` **tidak di-commit** (lihat `.gitignore`).

## Data tiruan (toy) — untuk uji pipeline
```bash
make toy-data          # menghasilkan data/raw/toy/ (60 user, 90 hari, 4 insider)
```
Toy **sengaja mudah** (recall ≈ 1.0). Jangan pernah melaporkan angka toy sebagai hasil.

## CERT Insider Threat Test Dataset (utama)
- Sumber: CERT Division, SEI, Carnegie Mellon University — repositori **KiltHub** (rilis r4.2; r6.2 opsional). Referensi lengkap ada di dokumen desain.
- Berisi: `logon.csv`, `device.csv`, `file.csv`, `http.csv`, `email.csv`, `LDAP/`, `psychometric.csv`, dan folder **jawaban (`answers/`)** yang menandai insider.
- Ukuran **besar** (terutama `http.csv`). Cek ukuran sebelum mengunduh, cek `df -h` & `free -h` di VM, dan gunakan `ingest.max_rows_per_file` di `configs/config.yaml` bila perlu.
- Letakkan di `data/raw/cert_r4.2/` lalu ubah `paths.raw` di config. **Grup B menyesuaikan `ingest/loader.py`** (nama kolom, format tanggal, format file label) — loader saat ini ditulis untuk skema yang saya asumsikan, **verifikasi terhadap file asli**.
- Data sintetis → tidak mewakili jaringan produksi. Sebut ini di Limitations.

## LANL "Comprehensive, Multi-Source Cyber-Security Events" (dataset kedua — TETAP di scope)
- Sumber: https://csr.lanl.gov/data/cyber1/ — log autentikasi de-identifikasi (±58 hari) + label **red team** (`redteam.txt.gz`: event kredensial yang disusupi).
- File yang dipakai: `auth.txt.gz` (**~1 miliar baris, ±7 GB terkompresi**) dan `redteam.txt.gz` (kecil). Format dan nama kolom dalam `ingest/loader_lanl.py` — **verifikasi dengan file asli**.
- **Jangan memuat penuh.** Alur kerja:
  1. `df -h` dan `free -h` di VM; pastikan disk cukup untuk file ±7 GB (+ ruang subset). Jika tidak cukup → kabari PM, jangan unduh membabi buta.
  2. Unduh ke `data/raw/lanl_full/` (di **tmux**).
  3. Ukur kecepatan: `python scripts/prefilter_lanl.py --src data/raw/lanl_full --out /tmp/lanl_test --max-lines 5000000`
  4. Jalankan penuh (tmux): `python scripts/prefilter_lanl.py --src data/raw/lanl_full --out data/raw/lanl_sub --user-fraction 0.02 --max-day 58`
     — menyimpan **semua baris user korban red-team** + sampel 2% user lain, hanya akun manusia.
  5. Pipeline: `python -m trailguard.pipeline all --config configs/config_lanl.yaml --raw data/raw/lanl_sub`
- Uji tanpa data asli: `make lanl-toy` (data tiruan berformat LANL).
- Catatan jujur untuk pitch: LANL kita pakai **sebagai subset**; waktu anonim (hanya relatif); label sangat sedikit — laporkan jumlah positif apa adanya.

# Data

> Folder `raw/`, `interim/`, `processed/` **tidak di-commit** (lihat `.gitignore`).
> Semua ID (user & komputer) di seluruh file antara sudah **ter-pseudonim HMAC**; kunci hanya ada di
> `.env` (`TRAILGUARD_HMAC_KEY`), tidak pernah ditulis di kode dan tidak pernah keluar instance.

## Data tiruan (toy) — untuk uji pipeline
```bash
make toy-data          # menghasilkan data/raw/toy/ (60 user, 90 hari, 4 insider)
make lanl-toy          # menghasilkan data/raw/lanl_toy/ (format LANL)
```
Toy **sengaja mudah** (recall ≈ 1.0) dan keluarannya dipisah (`outputs/toy_*`, `outputs/lanl_toy_*`)
supaya tidak pernah tercampur dengan hasil data asli. Jangan pernah melaporkan angka toy sebagai hasil.

## CERT Insider Threat Test Dataset (dataset utama)
- Sumber: CERT Division, SEI, Carnegie Mellon University (KiltHub, rilis **r4.2**). Referensi lengkap di dokumen desain.
- Isi: `logon.csv`, `device.csv`, `file.csv`, `http.csv`, `email.csv`, `LDAP/`, `psychometric.csv`, dan folder **`answers/`** yang menandai insider.
- Ukuran besar (terutama `http.csv`). Letakkan di `data/raw/cert_r4.2/` (itu nilai default `paths.raw` di `configs/config.yaml`) lalu jalankan `make run`. Untuk uji cepat gunakan `configs/config_toy.yaml` — **jangan** mengubah `paths` config utama hanya supaya uji cepat jalan.

### Dua jebakan file jawaban r4.2 (sudah ditangani `loader.py`, jangan diubah tanpa tes)
1. **`answers/insiders.csv` memuat campuran rilis.** Kolomnya
   `dataset,scenario,details,user,start,end` dan `dataset` berisi `2`/`3`/`4.2`/`6.2`. Loader **hanya**
   memakai baris `4.2`; tanpa filter itu label ikut dari rilis lain dan metrik jadi salah.
2. **Format tanggal berbeda dari log.** Log memakai `%m/%d/%Y %H:%M:%S` (`01/02/2010 07:16:07`),
   sedangkan file jawaban memakai ISO (`2010-10-23 01:34:19`). Memaksa satu format membuat semua label
   jadi `NaT` lalu terbuang **diam-diam** — gejalanya "tidak ada positif sama sekali". Loader mencoba
   beberapa format (`loader.LABEL_FMTS`) dan berteriak (`PERINGATAN`) bila ada baris gagal.

### Dari mana angka CERT di README berasal
- Fitur yang dievaluasi berasal dari **pilot notebook Grup B (B1)**: `data/processed/features_cert.csv.gz`.
  Isinya **330.285 user-hari × 1.000 user × 501 hari** (2010-01-02 → 2011-05-17) dengan **1.364 user-hari
  berlabel** untuk **70 insider** (seluruh insider r4.2). Fitur turunannya memakai `shift(1)`
  (baseline hanya dari hari-hari sebelumnya) sehingga **bebas leakage**.
- File kontrak `data/processed/features.csv.gz` adalah salinan ber-nama-kontrak dari file itu
  (`time_key → day`, `user_hash → user`); 19 fitur hasil notebook dipertahankan apa adanya (z-score-nya
  **tidak** dipotong, berbeda dari jalur `builder.py` yang memotong di ±10 — lihat Limitations).
- `make run` di LinuxONE akan **menulis ulang** `features.csv.gz` dari log mentah memakai `features/builder.py`
  (24 fitur: 12 dasar + 12 deviasi). Kedua bentuk bisa dibaca (`pipeline._load_feat`).
- Data sintetis → tidak mewakili jaringan produksi. Sebut ini di Limitations.

## LANL "Comprehensive, Multi-Source Cyber-Security Events" (dataset kedua — TETAP di scope)
- Sumber: https://csr.lanl.gov/data/cyber1/ — log autentikasi de-identifikasi (58 hari, `auth.txt`)
  + label **red team** (`redteam.txt`): **749 event** kredensial yang disusupi pada **104 user**.
- **Jangan memuat penuh.** Alur kerja (sudah dijalankan; ulangi hanya bila perlu subset baru):
  1. `python scripts/prefilter_lanl.py --normal-per-mille 25 --margin-days 2`
     (default `--auth <root>/auth.txt`, `--redteam <root>/redteam.txt`)
  2. Script **streaming**, menyimpan semua baris user korban + sampel 2,5% user normal
     (`crc32(user) % 1000 < 25`), hanya akun manusia (`U*`, akun sistem `C*$`/`ANONYMOUS` dibuang),
     dan **berhenti** di `t ≤ t_redteam_terakhir + 2 hari`.
  3. Hasil: **15.065.146 baris** disimpan dari **533.885.710 baris** yang dibaca, **300 detik**
     (~**1,78 juta baris/detik** dibaca, ~**50 ribu baris/detik** disimpan — termasuk hashing) →
     `data/raw/lanl_subset_auth.csv.gz` (**±100 MB desimal = 96 MiB**) dan
     `data/raw/lanl_redteam_hashed.csv.gz` (±10 KB). Semua **104/104** user red-team ditemukan.
     Dijalankan ulang dengan parameter sama menghasilkan jumlah baris, cakupan user, dan **seluruh
     metrik hilir yang identik**; byte `.gz` berbeda hanya karena header gzip menyimpan waktu.
  4. Kunci HMAC diambil dari `TRAILGUARD_HMAC_KEY`; **user DAN komputer** di-hash di sini sehingga
     file subset/antara tidak lagi memuat identitas mentah (Kontrak #1b).
- Skema subset: `time,user_hash,src_host_hash,dst_host_hash,auth_type,logon_type,orientation,status`.
  `time` LANL **anonim & hanya relatif** (detik sejak awal data); pipeline memetakannya ke hari
  berpatokan 1970-01-01, jadi angka tanggal LANL di metrik **bukan** tanggal kalender nyata.
- Fitur hasil `features/builder_lanl.py`: **15.065 user-hari × 1.247 user × 32 hari** dengan
  **181 user-hari berlabel** (104 user red team). 22 fitur (11 dasar + 11 deviasi).
- Catatan jujur untuk pitch: LANL dipakai **sebagai subset**; waktu anonim; label sangat sedikit dan
  **menggerombol di paruh awal** sehingga validasi temporal harus diperlebar agar memuat label, dan
  hasil test-nya jauh lebih buruk dari train (lihat `outputs/lanl_metrics.json` + bagian Limitations).
- Format di loader: `ingest/loader_lanl.py` menerima `auth.txt`/`auth.txt.gz` mentah (folder
  `auth.txt/auth.txt` hasil ekstraksi pun boleh) **dan** subset `.csv.gz` di atas.

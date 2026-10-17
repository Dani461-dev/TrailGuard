# 00 — Rencana Proyek TrailGuard (24 jam)

> Dokumen hidup. Pemilik: Project Manager (PM). Setiap perubahan scope dicatat di `05_DECISION_LOG.md`.

## 1. Tujuan satu kalimat
Bangun **pipeline deteksi insider-threat yang berjalan penuh di LinuxONE**, dengan skor risiko yang bisa dijelaskan, ID pengguna ter-pseudonim, dan keputusan akhir di tangan manusia — lalu **buktikan** (screenshot + angka terukur) bahwa semuanya berjalan di LinuxONE.

## 2. Prinsip kerja (karena kita baru di Linux)
1. **Selalu ada versi yang jalan.** `main` harus lolos `make toy` kapan pun. Data tiruan (toy) memungkinkan semua grup bekerja paralel tanpa menunggu data asli.
2. **Kontrak data dulu, kode kemudian.** Antar-grup hanya berkomunikasi lewat file di `docs/03_DATA_CONTRACTS.md`.
3. **Bukti > klaim.** Fitur yang tidak bisa ditunjukkan di video/screenshot = tidak ditulis di README.
4. **Potong scope lebih awal.** Keputusan potong dibuat di Gate, bukan jam ke-20.
5. **Semua orang lulus "Linux survival" di jam pertama** (lihat `02_LINUXONE_BEGINNER_GUIDE.md`), bukan hanya Grup A.

## 3. Prioritas scope (MoSCoW)
| Level | Isi | Batas keputusan |
|---|---|---|
| **MUST** | Jalan di LinuxONE · pseudonimisasi · fitur harian · Isolation Forest + supervised · skor risiko · policy 3 tier (human approval) · dashboard sederhana · evaluasi alert-budget + time-to-detection · **dua dataset: CERT (insider) + LANL (kredensial curian, versi subset)** · **penjelasan berbasis nilai Shapley** (implementasi sendiri dijamin jalan) · screenshot bukti · video ≤3 menit | wajib selesai |
| **TARGET (klaim "SHAP")** | **library `shap`** terpasang & jalan di s390x · **pyarrow/Parquet** | **go/no-go di Gate 1 (H+3)** — lihat §3b |
| **SHOULD** | container jalan · benchmark latensi/throughput · pembanding baseline di evaluasi · LANL: evaluasi lengkap dengan pembanding | Gate 2 (H+9) / Gate 3 |
| **COULD** | LLM kecil untuk ringkasan · replay live dengan kecepatan · tombol approve/reject di dashboard | Gate 3 (H+16) |
| **WON'T** | LANL **penuh** (1 miliar baris, ±7 GB gz) di VM · deep learning · otentikasi multi-user | — |

> **Keputusan (tim):** dua dataset **tetap** di scope sesuai dokumen desain; LANL tidak diturunkan. Agar layak dalam 24 jam, LANL dikerjakan sebagai **subset terstruktur**: semua baris user korban red-team + sampel user lain, via `scripts/prefilter_lanl.py` (streaming). Pipeline LANL terpisah dari CERT (`configs/config_lanl.yaml`) karena lingkungannya berbeda.
> **Konsekuensi yang harus dijaga:** beban B-Data naik → A-Platform mengambil unduh + prefilter LANL (tugas A11). **Checkpoint LANL:** subset terbentuk di VM pada **H+6**, pipeline LANL end-to-end pada **Gate 2 (H+9)**, evaluasi + pembanding pada **Gate 3 (H+16)**. Jika checkpoint meleset, PM memutuskan di Gate — dicatat di Decision Log, bukan diam-diam.

### 3b. SHAP & pyarrow: cara kita mengejar klaimnya dengan jujur
Keduanya **belum terbukti jalan di s390x** (shap menarik `numba`/`llvmlite` yang biasanya harus dikompilasi; pyarrow juga bisa tanpa wheel). Jadi:
1. **H+1–3 (A-Platform):** jalankan `make shap-check`; beri batas ±45 menit per paket; catat hasil di Decision Log. Keluaran tersimpan di `evidence/shap_pyarrow_check.txt`.
2. **Jika `shap` jalan** → pipeline otomatis memakainya (`explain.method: shap`). Alert mencatat `explain_method: "shap"` → **boleh klaim "SHAP"**, dengan screenshot sebagai bukti.
3. **Jika `shap` gagal** → pipeline otomatis turun ke **Shapley buatan sendiri** (`explain_method: "shapley"`): matematis nilai Shapley (sampling permutasi, properti *efficiency* terbukti oleh tes). Klaim yang jujur: *"Shapley-value explanations (implementasi sendiri, gaya SHAP)"*. **Jangan menulis "SHAP library".**
4. **pyarrow:** jika jalan → ubah `io.format: parquet`. Jika tidak → tetap CSV.gz dan jangan klaim Parquet. Pipeline otomatis fallback + peringatan.
5. Satu-satunya sumber kebenaran klaim: kolom `explain_method` di `outputs/alerts.jsonl` dan log `[score] ...` saat `make run`.

## 4. Alur sistem

```
 [Log mentah CERT/toy]
        │  (Grup B: loader)        ┌──────────── semua di dalam LinuxONE ────────────┐
        ▼                          │                                                  │
 ingest/loader ──► ingest/pseudonymize (HMAC, kunci di .env)  ← Grup C               │
        │                                                                             │
        ▼   data/interim/events.csv.gz   (KONTRAK #1)                                 │
 features/builder  ← Grup B                                                           │
        ▼   data/processed/features.csv.gz   (KONTRAK #2)                             │
 models/train (split TEMPORAL) → models/bundle.joblib      ← Grup B                  │
        ▼                                                                             │
 models/score → models/explain → policy/policy → llm/summarizer   ← B + C             │
        ▼   outputs/alerts.jsonl   (KONTRAK #3)                                       │
 api/app (Flask) + dashboard  ← Grup C          container (deploy/) ← Grup A          │
        ▼                                                                             │
 Analis manusia menyetujui tindakan berdampak tinggi                                 │
                                   └──────────────────────────────────────────────────┘
```

## 5. Timeline (H+0 = kick-off di region kalian)
> Waktu penutupan/submission persis: **cek di platform H2S / #announcements**. Rencana ini menargetkan submit di **H+22** agar ada 2 jam penyangga.

| Fase | Jam | Grup A — Platform & Deploy | Grup B — Data & Model | Grup C — Integrasi & Produk |
|---|---|---|---|---|
| **0. Siaga** | H+0–1 | SSH ke VM, `make check`, catat OS/Python/paket | Mulai unduh CERT r4.2 (di laptop dulu), baca skema | Buat repo Git, atur akses, buat `.env` + kunci |
| **1. Fondasi** | H+1–3 | `make setup`, `make toy` di LinuxONE; tabel kompatibilitas paket | Pelajari fitur di data toy; rancang fitur tambahan | Review kontrak data; mulai dashboard dengan data toy |
| ◆ **Gate 1 (H+3)** | | **`make toy` dan `make lanl-toy` sukses di LinuxONE**; **go/no-go SHAP & pyarrow diputuskan** (`make shap-check`); daftar paket OK/GAGAL terdokumentasi | | |
| **2. Data nyata + baseline** | H+3–9 | Pindahkan data CERT ke VM; **unduh + prefilter LANL (selesai H+6)**; mulai Dockerfile | Loader CERT asli, fitur, model baseline, metrik pertama; **mulai loader/fitur LANL setelah subset ada** | Pseudonimisasi di data asli; replay; dashboard membaca `alerts.jsonl` |
| ◆ **Gate 2 (H+9)** | | **End-to-end di data CERT (sampel) di LinuxONE** → alert tampil di dashboard; **pipeline LANL end-to-end pada subset** | | |
| **3. Perbaiki & hubungkan** | H+9–16 | Container jalan; benchmark awal; screenshot pertama | Tuning, pembanding baseline, penjelasan; (COULD: SHAP) | Policy final, ringkasan kasus, (COULD: LLM, approve/reject) |
| ◆ **Gate 3 (H+16)** | | **FEATURE FREEZE.** Setelah ini hanya bug fix, bukti, dokumentasi, video | | |
| **4. Bukti & cerita** | H+16–21 | `make bench`, `make evidence`, screenshot lengkap | Angka final + tabel hasil + batasan jujur | README final, skrip video, latihan demo |
| **5. Rekam & kirim** | H+21–23 | Rekam layar terminal LinuxONE | Narasi data & model | Rekam video (maks 3 menit), submit di H2S |
| **Penyangga** | H+23–24 | Perbaikan darurat saja | | |

**Giliran tidur:** 2 blok bergantian (H+10–14 dan H+14–18), selalu ada 1 orang per grup yang terjaga — detail di `01_TEAM_ROLES.md` §5. Jangan semua begadang; bug tengah malam mahal.

**Ritme koordinasi:** stand-up 10 menit di Discord tiap 3 jam (H+3, 6, 9, …): *selesai apa · sedang apa · terhambat apa*.

## 6. Daftar risiko
| # | Risiko | Dampak | Mitigasi | Pemilik |
|---|---|---|---|---|
| R1 | Paket ML gagal terpasang di s390x (big-endian, tak ada wheel) | Tinggi | Inti hanya pakai paket ringan (sklearn/pandas/flask). Uji opsional di Gate 1. Fallback: HistGradientBoosting, Shapley sendiri / deviasi | A |
| R2 | Scope terlalu besar | Tinggi | MoSCoW §3; Gate memutuskan potong | PM |
| R3 | VM terbatas (RAM/CPU/disk) vs data besar | Sedang | Pakai sampel CERT; `max_rows_per_file`; cek `free -h` | A+B |
| R4 | Koneksi SSH putus, proses mati | Sedang | Selalu jalankan di **tmux** | A |
| R5 | Format label/file CERT asli beda dari toy | Sedang | B menyesuaikan `loader.py` di fase 2 | B |
| R6 | Bukti LinuxONE tidak cukup untuk juri | Tinggi | `make evidence` sejak H+3, screenshot bertanda waktu | A |
| R7 | Klaim berlebihan (mis. "real-time", "SHAP", "privasi formal") | Sedang | Checklist klaim di `04_SUBMISSION_CHECKLIST.md` | C |
| R8 | Bug integrasi menit terakhir | Tinggi | Feature freeze H+16; `main` selalu hijau | PM |
| R9 | Kunci/token bocor ke GitHub | Tinggi | `.gitignore`, `.env` tak di-commit, cek sebelum push | C |
| R10 | Pelanggaran aturan orisinalitas | Fatal | Lihat bagian Integritas di `04_...` | Semua |
| R11 | LANL: data ±7 GB gz / 1 miliar baris; disk, RAM, atau waktu baca di s390x tak cukup | Tinggi | Prefilter streaming ke subset kecil; ukur dengan `--max-lines` dulu; tmux; cek `df -h` sebelum unduh; checkpoint H+6 | A-Platform + B-Data |
| R12 | `shap`/`numba`/`llvmlite` tak bisa dipasang di s390x → klaim SHAP tak terpenuhi | Sedang | Go/no-go H+3; fallback Shapley sendiri (sudah ada, teruji); klaim disesuaikan dengan `explain_method` | A-Platform + B-Model |
| R13 | LANL: label red-team sangat sedikit & time anonim → metrik tidak stabil | Sedang | Laporkan jumlah positif apa adanya + interval ketidakpastian; jangan dibulatkan menjadi klaim besar | B-Model |

## 7. Definition of Done proyek
- [ ] `make toy` dan pipeline pada data CERT berjalan di LinuxONE
- [ ] Dashboard menampilkan alert + alasan + tier + status persetujuan
- [ ] `outputs/metrics.json` & `outputs/benchmark.json` berisi angka nyata
- [ ] Screenshot bukti lengkap di `evidence/`
- [ ] README final, repo publik/bisa diakses juri, tautan open-source & dataset
- [ ] Video ≤3 menit terunggah, submit di H2S dengan judul berformat benar

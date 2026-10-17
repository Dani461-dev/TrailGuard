# 01 — Pembagian Tim & Tanggung Jawab (6 orang: 3 grup × 2 orang)

Karena semua baru di Linux, **Grup A bertugas menjadi "perintis"**: mencoba dulu, lalu menulis resep singkat untuk grup lain.
Setiap grup punya **2 peran yang berbeda** (bukan dua orang mengerjakan hal yang sama) dan saling menjadi **cadangan**.

## 1. Susunan tim

| Grup | Peran | Fokus satu kalimat | Nama |
|---|---|---|---|
| **A — Platform & Deploy** | **A-Platform** | Lingkungan LinuxONE: SSH, Python, paket, data di VM, bukti sistem | ________ |
| | **A-Deploy** | Container, benchmark performa, skrip & Makefile, bukti keamanan | ________ |
| **B — Data & Model** | **B-Data** | Loader CERT asli, pembentukan fitur, kualitas data | ________ |
| | **B-Model** | Model hibrida, tuning, evaluasi jujur, penjelasan alert | ________ |
| **C — Integrasi & Produk** | **C-Lead (juga PM)** | Pipeline, pseudonimisasi, policy, API; menjaga Gate, jam, Decision Log, Git | ________ |
| | **C-Demo** | Dashboard, replay, ringkasan kasus, README, video & submission | ________ |

> **PM = C-Lead** secara default (kerja PM ringan: menjaga Gate & keputusan). Jika C-Lead terlalu sibuk, tukar PM dengan siapa pun yang bebannya paling ringan — tulis di Decision Log.

## 2. Siapa memiliki file apa (hindari bentrok di Git)

| Peran | File yang dimiliki |
|---|---|
| **A-Platform** | `scripts/00_check_env.sh`, `scripts/01_setup_env.sh`, `scripts/check_imports.py`, `scripts/capture_evidence.sh`, **`scripts/test_shap_pyarrow.py`, `scripts/prefilter_lanl.py`**, `requirements*.txt`, `docs/02_*`, `docs/05_*` |
| **A-Deploy** | `deploy/`, `Makefile`, `scripts/benchmark_latency.py`, `evidence/` |
| **B-Data** | `ingest/loader.py`, **`ingest/loader_lanl.py`**, `features/` (termasuk **`builder_lanl.py`**), `io_utils.py`, `scripts/make_toy_data.py`, `scripts/make_toy_lanl.py`, `configs/config_lanl.yaml` (bagian `ingest`/`features`), `data/README.md`, Kontrak #1 & #2 di `docs/03_*` |
| **B-Model** | `models/` (train, score, evaluate, **explain** — SHAP/Shapley), bagian `model`/`evaluation`/`explain` di kedua config, Kontrak #4 & #5 (metrik) |
| **C-Lead** | `pipeline.py`, `ingest/pseudonymize.py`, `policy/`, `api/app.py`, `tests/`, `.gitignore`/`.env.example`, `docs/04_*` bagian F |
| **C-Demo** | `api/templates/`, `ingest/replay.py`, `llm/`, `README.md`, naskah & rekaman video |
| Bersama | `docs/00_*`, `docs/03_*` (perubahan kontrak harus disetujui pembuat **dan** pemakainya) |

Mengubah file milik peran lain → **minta dulu di Discord**, atau buat Pull Request dan tag pemiliknya.

---

## 3. Tugas per orang

### Grup A — LinuxONE Platform & Deploy

**A-Platform** — "pemilik lingkungan"
| ID | Tugas | Jam | Selesai bila… |
|---|---|---|---|
| A1 | SSH ke VM; `make check`; catat OS, Python, RAM, disk | 0–1 | output tersimpan di `evidence/` |
| A2 | `make setup` + `make toy` di LinuxONE | 1–3 | **Gate 1** tercapai |
| A3 | **`make shap-check` (SHAP + pyarrow) — go/no-go.** Pasang `pyarrow`, lalu `shap` (mungkin perlu paket LLVM dev), batas ±45 menit per paket; catat OK/GAGAL + pesan error. Lalu uji lightgbm/xgboost/llama-cpp | 1–3 (shap/pyarrow), 3–6 (lainnya) | hasil di `evidence/shap_pyarrow_check.txt` + tabel `05_DECISION_LOG.md`; **diumumkan di Gate 1** |
| A4 | Tulis resep tmux/venv/tunnel di `02_...` dan **bantu 4 anggota lain login** | 1–3 | semua lulus checklist "Linux survival" |
| A5 | Pindahkan data CERT ke VM; cek RAM/disk cukup | 3–6 | data terbaca di VM |
| A8 | Bukti sistem: screenshot `01`, `02`, `03` (lihat `04_...` §C) | 3–20 | file ada di `evidence/` |
| A11 | **LANL:** cek `df -h`/`free -h`; unduh `auth.txt.gz` + `redteam.txt.gz`; uji kecepatan `prefilter_lanl.py --max-lines 5000000`; jalankan prefilter penuh **di tmux**; hasil ke `data/raw/lanl_sub/` | 3–6 | subset siap & ukurannya dicatat; **checkpoint H+6** |

**A-Deploy** — "pemilik container & performa"
| ID | Tugas | Jam | Selesai bila… |
|---|---|---|---|
| A6 | Dockerfile jalan di s390x (cek image dasar mendukung s390x; fallback `ubi9/python-311`) | 3–12 | `make container` → `/health` OK |
| A7 | Benchmark latensi per-event & throughput skala besar | 10–18 | `outputs/benchmark.json` angka nyata dari LinuxONE |
| A9 | Bukti: screenshot `04` (container), `06` (metrik/benchmark), `07` (CPU/memori saat beban), `08` (keamanan) | 10–20 | file ada di `evidence/` |
| A10 | Rapikan `Makefile`/skrip agar satu perintah menjalankan semuanya | 12–16 | `make toy`, `make bench`, `make container` bersih |

> Jam 0–3 A-Deploy ikut membantu A-Platform (dua orang lebih cepat menemukan masalah paket) sambil mempelajari container.

### Grup B — Data & Pemodelan

**B-Data** — "pemilik data & fitur"
| ID | Tugas | Jam | Selesai bila… |
|---|---|---|---|
| B1 | Unduh CERT r4.2, pahami file & label jawaban (`data/README.md`) | 0–3 | skema dipahami |
| B2 | Sesuaikan `loader.py` ke format CERT asli (+ label) | 3–6 | `make run` jalan pada sampel CERT |
| B3 | Periksa & tambah fitur CERT (cold-start, warm-up, jam kerja per user, dll.) | 3–12 | `features.csv.gz` valid sesuai Kontrak #2 |
| B9 | **LANL:** cocokkan `loader_lanl.py` & `builder_lanl.py` dengan file asli (kolom, `Success`/`Fail`, format redteam); jalankan `make lanl-run` pada subset; perbaiki fitur (mis. proxy jam) | 6–14 | pipeline LANL end-to-end (**Gate 2**) |
| B8 | Cek kualitas data: duplikat, tanggal rusak, user tanpa data, distribusi label | 4–10 | catatan di Decision Log |

**B-Model** — "pemilik model & evaluasi"
| ID | Tugas | Jam | Selesai bila… |
|---|---|---|---|
| B4 | Tuning supervised + Isolation Forest; cara menggabungkan skor | 6–14 | metrik membaik vs baseline |
| B5 | **Evaluasi jujur**: pembanding (acak, z-score saja, supervised saja, IF saja) pada alert budget | 10–16 | tabel pembanding |
| B6 | **Penjelasan SHAP/Shapley** (`explain.py`): jika `shap` lolos A3, uji jalur library (belum teruji di sandbox!); cek kewajaran alasan & waktu hitung di LinuxONE; sesuaikan `explain.n_samples/min_tier/max_alerts` | 9–16 | `explain_method` tercatat; alasan alert masuk akal bagi manusia |
| B7 | Tulis batasan: data sintetis (CERT), subset & anonimisasi waktu (LANL), kelangkaan label, risiko leakage | 16–20 | bagian "Limitations" README |
| B10 | **Evaluasi LANL** dengan pembanding dan jumlah positif apa adanya (R13) | 12–16 | `outputs/lanl_metrics.json` + tabel |

> Jam 0–6 B-Model bekerja dengan **data toy** (`make toy`) agar tidak menunggu B-Data: menyiapkan pembanding dan fungsi evaluasi lebih dulu.
> **Larangan keras:** split acak (harus **temporal**); melaporkan accuracy sebagai metrik utama.

### Grup C — Integrasi & Produk

**C-Lead (PM)** — "pemilik pipeline, keamanan & koordinasi"
| ID | Tugas | Jam | Selesai bila… |
|---|---|---|---|
| C1 | Repo Git, branch per grup, `.env` + kunci HMAC (tidak di-commit) | 0–1 | semua bisa clone & push |
| C2 | Pseudonimisasi diuji di data asli; **slide threat model** (apa bocor/tidak bocor) | 3–9 | tes lulus; 1 slide siap |
| C8 | Menjaga **Gate** (H+3, 9, 16), stand-up 3 jam sekali, Decision Log, `main` tetap hijau | 0–23 | Gate tercatat |
| C9 | Endpoint API & kebijakan: `/api/score`, tier policy final, log keputusan manusia | 6–16 | API stabil untuk dashboard |
| C10 | Review akhir klaim (checklist §D) — **cocokkan klaim SHAP/Parquet dengan `explain_method` & `shap_pyarrow_check.txt`** — & dry-run submission | 20–23 | submit sukses |

**C-Demo** — "pemilik tampilan & cerita"
| ID | Tugas | Jam | Selesai bila… |
|---|---|---|---|
| C3 | Dashboard: daftar alert, tier, alasan, **metode penjelasan**, status "butuh persetujuan"; **pemilih dataset (CERT/LANL)** lewat `TRAILGUARD_CONFIG` | 1–12 | tampil dari `alerts.jsonl` / `lanl_alerts.jsonl` |
| C4 | Replay stream untuk demo — jujur: ini replay | 6–14 | demo mengalirkan event |
| C5 | Ringkasan kasus: template (MUST) → LLM kecil (COULD, hanya fitur ter-pseudonim) | 9–16 | ringkasan tampil di dashboard |
| C6 | COULD: tombol Approve/Reject → tersimpan | 12–16 | log keputusan manusia |
| C7 | README final, naskah & rekaman video ≤3 menit, upload | 16–23 | tersubmit sebelum batas |

---

## 4. Pasangan cadangan (jika ada yang macet atau tidur)

| Peran | Cadangan dalam grup | "Buddy" lintas grup (untuk antarmuka) |
|---|---|---|
| A-Platform ↔ A-Deploy | saling menggantikan | A-Platform ↔ **B-Data** (data di VM) |
| B-Data ↔ B-Model | saling menggantikan | B-Model ↔ **C-Demo** (`alerts.jsonl` → dashboard) |
| C-Lead ↔ C-Demo | saling menggantikan | C-Lead ↔ **A-Deploy** (container & API) |

Aturan buddy: sebelum mengubah kontrak/antarmuka yang dipakai buddy, **kabari dulu**; di Gate 2 buddy melakukan *demo 5 menit* hasil kerjanya satu sama lain.

## 5. Giliran tidur (selalu ada 1 orang per grup yang terjaga)
| Blok | Tidur | Terjaga di grup |
|---|---|---|
| Blok 1 | **A-Platform, B-Data, C-Demo** tidur ±H+10–14 | A-Deploy, B-Model, C-Lead |
| Blok 2 | **A-Deploy, B-Model, C-Lead** tidur ±H+14–18 | A-Platform, B-Data, C-Demo |

Sebelum tidur: tulis **catatan serah-terima** 3 baris di Discord (selesai apa · sedang apa · jebakan). Semua orang hadir penuh di **H+18–24** untuk bukti, video, dan submit.

## 6. Antarmuka antar-grup (siapa menyerahkan apa ke siapa)
- **B-Data → B-Model:** `features.csv.gz` (Kontrak #2).
- **C-Lead → B-Data:** `events.csv.gz` ter-pseudonim (Kontrak #1).
- **B-Model → C-Demo/C-Lead:** `models/bundle.joblib`, `outputs/alerts.jsonl` (Kontrak #3), `metrics.json`.
- **A-Deploy → semua:** container & `benchmark.json`; **A-Platform → semua:** paket terpasang. Butuh paket baru? Minta A-Platform **sebelum** menambah ke `requirements.txt`.

## 7. Aturan Git sederhana
1. Branch: `a-platform/…`, `a-deploy/…`, `b-data/…`, `b-model/…`, `c-lead/…`, `c-demo/…`; merge ke `main` lewat Pull Request kecil, **direview orang dari grup lain**.
2. Sebelum merge: `make toy` harus sukses.
3. Commit kecil & sering. Jangan commit data besar, `.env`, atau `models/*.joblib`.
4. Konflik merge? Berhenti, panggil PM — jangan asal "accept all".

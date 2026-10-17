# 04 — Checklist Submission, Bukti LinuxONE & Skrip Video

## A. Wajib sebelum acara (semua tim)
- [ ] Registrasi individu + **Create a Team** oleh ketua tim di H2S (tim 4–6 orang)
- [ ] Abstrak terkirim (batas **15 Okt**; glossary guidebook menulis 5 Okt — konfirmasi di #helpdesk bila ragu)
- [ ] Hadir di sesi **"Get Your LinuxONE System Ready"** (16 Okt) — wajib
- [ ] Menyelesaikan **2 lab wajib**: (1) Predictive AI Hybrid / multi-model, (2) Predictive AI + Generative AI
- [ ] Semua anggota ada di Discord (#announcements, #helpdesk; **#ibm-z-sme-helpdek hanya buka di hari-H**)
- [ ] Akun LinuxONE Community Cloud aktif; event code **`SSF2026`** dimasukkan di deskripsi proyek

## B. Persyaratan submission (H2S)
- [ ] **Judul proyek memuat nama tim:** `[NamaTim]_IBM Z Datathon 2026 Project`
- [ ] **Video ≤ 3 menit** (wajib): masalah · data pendukung · solusi · **bagaimana memakai IBM Z** (tech stack, tunjukkan instance & model LinuxONE) · demo
- [ ] **Tautan kode** (GitHub/GitLab/zip) — repo dapat diakses juri
- [ ] **Tautan semua sumber open-source** yang dipakai (README §Credits)
- [ ] Opsional: flowchart arsitektur, prototipe
- [ ] Submit sebelum batas (target internal: **H+22**)

## C. Bukti LinuxONE (juri menilai lewat screenshot) — tanggung jawab Grup A
Simpan di `evidence/` dengan nama jelas, **tampilkan jam/tanggal & hostname di layar**.
- [ ] `01_login_and_arch.png` — `uname -a` + `lscpu` (Architecture: **s390x**)
- [ ] `02_resources.png` — `free -h`, `df -h`, `nproc` (sumber daya VM)
- [ ] `03_pipeline_run.png` — `make run` selesai di VM (log & waktu)
- [ ] `04_container.png` — `podman ps`/`docker ps` + `curl localhost:8000/health`
- [ ] `05_dashboard.png` — dashboard (lewat tunnel) dengan alert & tier
- [ ] `06_metrics_benchmark.png` — isi `metrics.json` & `benchmark.json`
- [ ] `07_load.png` — `top`/`htop` saat benchmark skala besar (CPU/memori)
- [ ] `08_security.png` — bukti pseudonimisasi: kolom user berupa hash; `.env`/kunci tidak di repo (`git ls-files | grep env` kosong)
- [ ] `system_info.txt` — keluaran `make evidence`
- [ ] `09_shap_pyarrow_check.png` + `shap_pyarrow_check.txt` — keluaran `make shap-check` (bukti klaim SHAP/pyarrow, atau bukti jujur bahwa fallback dipakai)
- [ ] `10_lanl_subset.png` — ukuran subset LANL & log prefilter (`ls -lh data/raw/lanl_sub`, `df -h`)

> **Jangan mengklaim** fitur khusus IBM Z (akselerator AI on-chip, enkripsi perangkat keras, dll.) kecuali benar-benar bisa ditunjukkan di instance kalian.

## D. Checklist klaim jujur (README & video)
| Boleh diklaim bila… | Jangan klaim bila… |
|---|---|
| "Berjalan di LinuxONE" — ada screenshot `s390x` | hanya jalan di laptop |
| "Near real-time" — ada angka latensi per event + dijelaskan sebagai **replay** | tidak ada pengukuran |
| "Explainable" — alasan alert tampil di dashboard | menyebut metode yang tidak benar-benar dipakai |
| **"SHAP"** — `explain_method: "shap"` di alerts + screenshot `shap_pyarrow_check.txt` menunjukkan `[OK] shap` di LinuxONE | `explain_method` = `shapley` → tulis *"Shapley-value explanations (implementasi sendiri, gaya SHAP)"*; = `deviation` → jangan sebut SHAP |
| **"Parquet/pyarrow"** — `[OK] pyarrow` + `io.format: parquet` benar-benar dipakai | pyarrow gagal / fallback CSV |
| **"Dua dataset"** — hasil CERT **dan** LANL dari `metrics.json` / `lanl_metrics.json`; sebut LANL = **subset** (user korban red-team + sampel user lain) | menyebut LANL penuh/1 miliar baris diproses |
| "Privacy-preserving" → tulis **"mengurangi eksposur lewat pseudonimisasi"** | menyebut jaminan privasi formal / differential privacy |
| Angka performa — dari `metrics.json`, split temporal, alert budget | accuracy, atau angka dari data toy |
| "Human-in-the-loop" — tier 3 butuh persetujuan di UI/log | tidak ada mekanisme persetujuan sama sekali |

## E. Skrip video 3 menit (draf — C yang finalisasi)
| Waktu | Isi | Visual | Pembicara |
|---|---|---|---|
| 0:00–0:20 | **Masalah:** insider/kredensial bocor sulit terlihat; biaya & kewajiban 72 jam UU PDP; kecil/univ tidak punya SOC | 1 slide + 1–2 angka (verifikasi sumber) | C |
| 0:20–0:40 | **Data:** CERT (sintetis, multi-sumber) + batasannya; split temporal | slide data | B |
| 0:40–1:40 | **Demo:** skenario satu akun (logon jam 2 pagi, perangkat baru, USB) → skor naik → alasan → tier → tiket menunggu persetujuan analis | dashboard live | C |
| 1:40–2:30 | **IBM Z/LinuxONE:** terminal `uname/lscpu` s390x, container berjalan, ID ter-hash, latensi & throughput terukur, tech stack | terminal + screenshot | A |
| 2:30–3:00 | **Dampak & kejujuran:** hasil (alert budget, time-to-detection), batasan, langkah berikut; manusia tetap pegang kendali | slide penutup | PM |

Tips: rekam demo **sebelum** H+21 sebagai cadangan; potong ke ≤3:00 (video lebih panjang = risiko skor eksekusi turun); suara jelas > animasi.

## F. Integritas & aturan (BACA — pelanggaran = diskualifikasi)
- Aturan guidebook: proyek harus **dimulai & kodenya ditulis dari nol selama 17–18 Okt**; **dilarang** memakai kode/proyek/ide orang lain; open-source library **boleh** asal tautannya dicantumkan; **dilarang** melanjutkan proyek lama.
- **Kerangka repo ini dibuat dengan bantuan AI (Claude).** Guidebook tidak menyebut aturan tentang alat AI. **Tanyakan ke panitia di #helpdesk** (atau email stemprograms@sstarsfoundation.org) apakah kerangka/kode bantuan AI diperbolehkan dan apakah perlu diungkapkan — sebelum commit pertama. Simpan jawabannya.
- Lakukan **commit pertama setelah kick-off resmi** di region kalian, supaya riwayat Git konsisten dengan aturan.
- Apa pun statusnya, **setiap anggota harus bisa menjelaskan tiap file** yang ia miliki. Tulis ulang/ubah dengan gaya tim sendiri bagian yang belum kalian pahami; jangan kirim kode yang tidak bisa dipertanggungjawabkan.
- Dataset publik (CERT, LANL) **boleh**, cantumkan sumber & lisensi. Tidak boleh ada data pribadi asli.
- Etika & sopan santun: tanpa konten politik/ujaran kebencian; persaingan sehat.

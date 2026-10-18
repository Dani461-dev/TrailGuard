# 05 — Decision Log & Catatan Kompatibilitas

Tulis setiap keputusan penting (1–3 baris). Ini juga bahan jujur untuk bagian "Limitations" dan Q&A juri.

## Keputusan awal (PM, sebelum kick-off)
| # | Keputusan | Alasan | Tinjau ulang bila… |
|---|---|---|---|
| D1 | Flask (bukan FastAPI/Streamlit) | pure-Python; FastAPI/Streamlit menarik pydantic-core/pyarrow yang berisiko di s390x | semua paket terbukti OK di Gate 1 |
| D2 | Data antar-langkah = **CSV.gz default; Parquet opsional** bila pyarrow lolos `make shap-check` | pyarrow berisiko di s390x; pipeline fallback otomatis | pyarrow OK → set `io.format: parquet` |
| D3 | Supervised = `HistGradientBoostingClassifier` (sklearn) | tanpa dependensi tambahan | LightGBM/XGBoost lolos uji A3 dan lebih baik |
| D4 | **Target klaim SHAP.** Urutan penjelasan: `shap` (library) → `shapley` (implementasi sendiri, teruji) → `deviation` | tim ingin klaim SHAP; klaim wajib sesuai metode yang benar-benar jalan | hasil go/no-go H+3 |
| D5 | **LANL tetap di scope** (keputusan tim), dikerjakan sebagai **subset** via prefilter streaming; pipeline terpisah (`config_lanl.yaml`) | data penuh ±1 miliar baris tak layak di VM/24 jam | checkpoint H+6 / Gate 2 / Gate 3 meleset → PM memutuskan di Gate & mencatat di sini |
| D6 | Split TEMPORAL, metrik alert-budget + time-to-detection | data sangat langka, hindari leakage | — |
| D7 | Replay = simulasi stream, dinyatakan jujur | klaim "real-time" harus bisa dibuktikan | — |

## Tabel kompatibilitas paket di LinuxONE (isi oleh Grup A)
| Paket | Versi | Status (OK/GAGAL) | Pesan error / catatan | Waktu pasang |
|---|---|---|---|---|
| pandas | | | | |
| scikit-learn | | | | |
| flask | | | | |
| lightgbm | | | | |
| xgboost | | | | |
| shap | | | | |
| llama-cpp-python | | | | |

## Log keputusan selama acara
| # | Keputusan | Grup | Alasan / konsekuensi |
|---|---|---|---|
| L1 | **Prefilter LANL memakai kunci dari env** (`TRAILGUARD_HMAC_KEY`), dan **user DAN komputer** di-hash di situ | B-Data | Subset versi lama menyimpan nama komputer mentah (`C1234$`) dan memakai salt hardcode = kebocoran identitas. Subset diregenerasi; semua file antara kini bebas ID mentah (Kontrak #1b). |
| L2 | **Keluaran toy dipisah** (`outputs/toy_*`, `outputs/lanl_toy_*` via `config_toy.yaml`/`config_lanl_toy.yaml`) | C-Lead + B-Model | Uji cepat dulu bisa menimpa `outputs/metrics.json`/`alerts.jsonl` milik data asli. `make run`/`lanl-run` kini jelas "data ASLI". |
| L3 | **Semua hyperparameter dipilih di sepotong VALIDASI temporal** (bobot positif, `alpha`, cara gabung, ambang tier); kandidat + skornya disimpan di bundle (`selection`) | B-Model | Menjawab "angka ini dari mana?". Grid `alpha` memuat 0.0 dan 1.0 sehingga hibrida **harus membuktikan diri**, tidak menang karena dipaksa. |
| L4 | **Jendela validasi diperlebar ke belakang** bila tak memuat label (`split_last(..., min_positives=5)`), dengan lantai 50% periode untuk melatih | B-Model | Serangan LANL menggerombol di paruh awal → validasi 20% terakhir kosong dan tuning diam-diam terlewat. Kompromi pragmatis ini **dicatat** di README bagian Limitations. Test tidak pernah disentuh. |
| L5 | **Ambang tier dikalibrasi di validasi** dengan lantai p90 skor normal, dan `policy.policy_cfg` membacanya → pipeline & API memakai ambang yang sama | B-Model + C-Lead | Sebelumnya ambang tetap dari config sehingga tier 3 bisa membanjir. Tier 3 (`ticket_threshold`) dijaga benar-benar langka. |
| L6 | **Bug label CERT diperbaiki**: filter `dataset=4.2` + tanggal ISO multi-format (`loader.LABEL_FMTS`), dengan peringatan keras | B-Data | `answers/insiders.csv` r4.2 mencampur rilis dan memakai ISO, bukan `%m/%d/%Y`. Tanpa ini label jadi `NaT` dan terbuang **diam-diam** → metrik 0. |
| L7 | **Lapisan kompatibilitas fitur** di pipeline: membaca gaya notebook (`time_key`/`user_hash`, `*_zscore_7d`) **dan** gaya builder; kolom model diambil dari file | B-Model | Menjembatani jalur notebook B1 dan `features/builder.py` tanpa mengubah nilai fitur notebook (provenance terjaga). |
| L8 | **Berkas fitur kontrak** `data/processed/features.csv.gz` = salinan ber-nama-kontrak dari `features_cert.csv.gz` (file asli **dipertahankan**) | B-Model | Hasil di README berasal dari fitur pilot yang benar-benar dievaluasi; apa pun yang tidak berubah tidak ditulis ulang. |
| L9 | **Hasil jujur: di kedua dataset validasi memilih `alpha=1.0`** (murni supervised) | B-Model | Isolation Forest tidak menambah nilai terukur di titik operasi itu. Dilaporkan apa adanya + pembanding `unsupervised_only`/`zscore_baseline`, bukan diklaim sebagai manfaat hibrida. |
| L10 | **Drift LANL dilaporkan sebagai hasil negatif** (val PR-AUC 0.99 → test 0.10) | B-Model | Risiko R13. Tidak men-tuning di test untuk menutupi. |
| L11 | **Perbaikan kecil**: `z_suffix_of` memeriksa sufiks terpanjang lebih dulu (`_pop_z` sebelum `_z`); bila bagian *fit* tak berlabel, cabang supervised tetap dilatih pada seluruh train dengan bobot wajar (bukan dibuang) | B-Model | Dua bug halus: label alasan bisa salah untuk fitur `*_pop_z`, dan model bisa kehilangan cabang supervised tanpa pesan jelas. |
| L13 | **Penjaga klaim otomatis** `scripts/check_claims.py`: semua angka di bagian *Results* README harus ada di `outputs/*_metrics.json` | B-Model | Menegakkan aturan "angka wajib tertelusur" secara mekanis; sekarang **25/25 angka tertelusur**. Bisa dipakai di CI/Makefile (keluar 1 bila melenceng). |
| L12 | **Berkas di luar kepemilikan B yang ikut disentuh** karena perbaikan lintas-modul: `Makefile` (A-Deploy), `policy/policy.py` & `pipeline.py` (C-Lead), `api/app.py` + `llm/summarizer.py` (C-Demo), `tests/test_models_b.py` (baru, tak menyentuh `tests/test_core.py` C-Lead) | B-Model | Mohon ditinjau pemiliknya. Semua tercatat di sini supaya bisa ditelusuri/di-*revert*. |

### Rincian pemilihan model (dari `outputs/*_metrics.json` → `model_selection`)| Dataset | Kandidat terbaik kedua | Pemenang | Catatan |
|---|---|---|---|
| CERT r4.2 | `weighted alpha=0.95` (0.7346) | `weighted alpha=1.0` (0.8120) | Murni anomaly (`alpha=0.0`) 0.0283 — jauh lebih buruk |
| LANL subset | `weighted alpha=0.95` (0.1678) | `weighted alpha=1.0` (0.1967) | Murni anomaly (`alpha=0.0`) 0.0166; validasi hanya **14 positif** → kesimpulan ini sendiri tidak stabil |

## Hasil go/no-go (isi oleh A-Platform di H+1–3)
| Item | Hasil (OK/GAGAL) | Versi / pesan error | Waktu pasang | Konsekuensi klaim |
|---|---|---|---|---|
| pyarrow | | | | OK → boleh Parquet · GAGAL → CSV saja |
| shap (library) | | | | OK → boleh klaim "SHAP" · GAGAL → "Shapley sendiri" |
| numba / llvmlite | | | | (penyebab umum kegagalan shap) |

## Catatan LANL (isi oleh A-Platform & B-Data)
| Item | Nilai |
|---|---|
| Ruang disk bebas sebelum unduh | (A-Platform; sumber `auth.txt` 70 GB ada di working copy ini) |
| Kecepatan prefilter (baris/detik, `--max-lines`) | **1.779.619 baris/detik** dibaca · **50.217 baris/detik** disimpan (`baca=533.885.710 simpan=15.065.146`, 300 s) — termasuk hashing HMAC user & komputer |
| Parameter akhir (`--normal-per-mille`, `--margin-days`) | `--normal-per-mille 25` (sampel 2,5% user normal → 1.143 user) · `--margin-days 2` → cutoff `t ≤ 2.729.847` |
| Reproduksibilitas | dijalankan ulang dengan parameter sama: jumlah baris, 104/104 user red-team, dan **seluruh metrik hilir identik** (0,0833 / 0,1471 / 4-26 / 60 alert). Byte `.gz` berbeda hanya karena header gzip menyimpan waktu — bukan karena isinya berbeda. |
| Ukuran subset (baris / MB) | **15.065.146 baris** disimpan · `lanl_subset_auth.csv.gz` **±100 MB** · `lanl_redteam_hashed.csv.gz` ±10 KB |
| Jumlah user red-team & event red-team | **104 user** · **749 event** (setelah dedup: 34 baris identik) → **181 user-hari** berlabel |

## Kualitas data (B8) — diukur, bukan diklaim
| Pemeriksaan | CERT r4.2 (`features.csv.gz`) | LANL subset (`lanl_features.csv.gz`) |
|---|---|---|
| Baris / user / hari | 330.285 / 1.000 / 501 | 15.065 / 1.247 / 32 |
| Duplikat `(user, day)` | **0** | **0** |
| `day` gagal di-parse (NaT) | **0** | **0** |
| Baris tanpa aktivitas (semua fitur 0) | **0** | **0** |
| Kolom fitur (semua bukan-NaN) | 19 | 22 |
| Distribusi label | 328.921 negatif / **1.364 positif (0,41%)** | 14.884 negatif / **181 positif (1,2%)** |
| User berlabel | **70** (= seluruh insider r4.2) | **104** (= seluruh user red-team) |
| Sebaran label | tersebar di 501 hari; puncak 13 user-hari/hari (Agustus 2010) | **menggerombol** di hari ke-2…17 (puncak 45 user-hari) + sedikit di hari ke-27 |

Catatan: (a) file jawaban CERT mentah **tidak ada di working copy ini** (di luar repo) sehingga duplikat pada `answers/insiders.csv` tak bisa diukur di sini — yang bisa dibuktikan adalah **semua 70 insider r4.2 muncul** sebagai user berlabel di fitur; (b) 34 dari 749 event red-team LANL identik (duplikat murni) dan runtuh saat dipetakan ke user-hari, jadi **181** adalah jumlah positif yang benar; (c) sebaran label LANL yang menggerombol itulah alasan validasi temporal harus diperlebar (lihat L4).

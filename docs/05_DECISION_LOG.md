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
| pandas | 1.3.5 | OK | apt (python3-pandas); wheel pip s390x tidak tersedia | cepat |
| scikit-learn | 0.23.2 | OK (HGB GAGAL) | sklearn apt TANPA HistGradientBoostingClassifier; fallback GradientBoostingClassifier aktif (lihat go/no-go) | cepat |
| flask | 2.0.1 | OK | apt (python3-flask) | cepat |
| lightgbm | — | belum diuji | belum diuji di VM | — |
| xgboost | — | belum diuji | belum diuji di VM | — |
| shap | — | GAGAL | `No module named 'shap'`; `make shap-check` → pipeline pakai Shapley sendiri | — |
| llama-cpp-python | — | belum diuji | belum diuji di VM | — |
| pyarrow | — | GAGAL | `No module named 'pyarrow'`; io.format tetap CSV.gz, TIDAK boleh klaim Parquet | — |

## Log keputusan selama acara
| Jam | Keputusan | Oleh | Alasan |
|---|---|---|---|
| H+? | | | |

## Hasil go/no-go (isi oleh A-Platform di H+1–3)
| Item | Hasil (OK/GAGAL) | Versi / pesan error | Waktu pasang | Konsekuensi klaim |
|---|---|---|---|---|
| pyarrow | GAGAL | `No module named 'pyarrow'` | — | CSV.gz saja · JANGAN klaim Parquet |
| shap (library) | GAGAL | `No module named 'shap'` | — | klaim "Shapley sendiri" (BUKAN "SHAP library") |
| numba / llvmlite | GAGAL | tak terpasang (ketergantungan shap) | — | (penyebab umum kegagalan shap) |
| HistGradientBoostingClassifier | GAGAL | sklearn 0.23.2 apt tidak memilikinya | — | fallback GradientBoostingClassifier (tercatat di metrics: sup_model) |
| Node.js untuk dashboard-ui | GAGAL | VM hanya punya node v12.22.9 (apt); tak ada biner resmi linux-s390x untuk v20/v22 | — | R17: bangun dashboard-ui di laptop, salin `dist/` (make ui) |

## Catatan LANL (isi oleh A-Platform & B-Data)
| Item | Nilai |
|---|---|
| Ruang disk bebas sebelum unduh | |
| Kecepatan prefilter (baris/detik, `--max-lines`) | |
| Parameter akhir (`--user-fraction`, `--max-day`) | |
| Ukuran subset (baris / MB) | |
| Jumlah user red-team & event red-team | |

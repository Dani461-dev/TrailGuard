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
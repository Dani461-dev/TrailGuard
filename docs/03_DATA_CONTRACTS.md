# 03 — Kontrak Data Antar-Grup

Aturan: **ubah kontrak = ubah dokumen ini + beritahu pemilik & konsumennya.** Kolom boleh *ditambah*, jangan diganti nama/dihapus tanpa kesepakatan.

## Kontrak #1 — Event terpadu (ter-pseudonim)
- **File:** `data/interim/events.csv.gz` · **Pembuat:** `ingest` (B: loader, C: pseudonymize) · **Konsumen:** `features` (B)
- **Aturan keras:** tidak ada ID asli. `user` & `host` adalah keyed-hash (HMAC-SHA256, 16 hex).

| Kolom | Tipe | Keterangan |
|---|---|---|
| `ts` | datetime | waktu event |
| `user` | str | hash pengguna |
| `host` | str | hash komputer |
| `source` | str | `logon` / `device` / `file` / `http` / `email` |
| `action` | str | `logon`,`logoff`,`connect`,`disconnect`,`file_op`,`visit`,`email_int`,`email_ext` |
| `target` | str | ekstensi file / domain web / `usb` / kosong |
| `size` | num | ukuran (email), selain itu 0 |

**Label:** `data/interim/labels.csv` — kolom `user` (hash sama!), `start`, `end` (rentang aktivitas jahat).

### Kontrak #1b — Event LANL (ter-pseudonim)
- **File:** `data/interim/lanl_events.csv.gz` · **Pembuat:** `ingest/loader_lanl.py` · **Konsumen:** `features/builder_lanl.py`
- Hanya akun manusia (`src_user` diawali `U`; akun sistem `C*$`/`ANONYMOUS` dibuang); `user`, `host`, `dst_host` = keyed-hash.
- Loader menerima **dua** masukan: `auth.txt`/`auth.txt.gz` mentah (folder `auth.txt/auth.txt` hasil ekstraksi pun boleh) **atau** subset hasil `scripts/prefilter_lanl.py` (`*.csv.gz`, ID sudah ter-hash). Pada subset, **komputer juga sudah di-hash** sehingga file antara/subset tidak memuat identitas mentah sama sekali.

| Kolom | Keterangan |
|---|---|
| `ts` | waktu (detik sejak awal data → datetime berpatokan 1970-01-01; hanya **relatif** bermakna) |
| `user`, `host`, `dst_host` | hash pengguna / komputer asal / komputer tujuan |
| `auth_type`, `logon_type`, `orientation` | `Kerberos`/`NTLM`…, `Network`/`Interactive`…, `LogOn`/`LogOff`/`TGS`… |
| `success` | 1 = Success, 0 = Fail |

Label LANL = event red-team (`redteam.txt.gz`) → `labels` dengan `start = end = waktu event`. Fitur LANL (**11 dasar + 11 `_z`**, termasuk `n_new_hour` = jam yang belum pernah dipakai user itu) didefinisikan di `builder_lanl.py`. File lain: `lanl_features.csv.gz`, `models/bundle_lanl.joblib`, `outputs/lanl_alerts.jsonl`, `outputs/lanl_metrics.json`.

### Format file antar-langkah
Default **CSV.gz**. Jika `io.format: parquet` dan pyarrow jalan → ekstensi `.parquet`; jika pyarrow gagal → otomatis kembali ke CSV dengan peringatan (`io_utils.py`). Kode lain **harus** membaca lewat `io_utils.read_table`, bukan `pd.read_csv` langsung.

## Kontrak #2 — Fitur harian
- **File:** `data/processed/features.csv.gz` · **Pembuat:** B · **Konsumen:** B (model), C (API/benchmark)
- 1 baris = 1 `user` × 1 `day`. Kolom: `user`, `day`, `label` (0/1), lalu **FEATURE_COLS** (didefinisikan di `features/builder.py`): 12 fitur dasar `n_*` + 12 deviasi `*_z` (z-score terhadap baseline 14 hari milik user itu sendiri, tanpa melihat hari ini → **bebas leakage**).
- Menambah fitur: tambahkan ke `BASE_COLS` (otomatis menghasilkan `_z`) + `FEATURE_LABELS` agar bisa dijelaskan.
- **Jalur LANL** (file `data/processed/lanl_features.csv.gz`): skema sama, `FEATURE_COLS` dari `features/builder_lanl.py` = **11 dasar + 11 deviasi** (`n_*` + `*_z`). `day` LANL berasal dari waktu anonim (berpatokan 1970-01-01), jadi hanya **urutan relatifnya** yang bermakna.
- **Jalur pilot notebook CERT (B1):** `data/processed/features_cert.csv.gz` memakai nama kunci `time_key`/`user_hash` dan fitur gaya lain (`*_zscore_7d`, `*_spike_ratio`). File kontrak `features.csv.gz` adalah salinan ber-nama-kontrak-nya. `pipeline._load_feat` menormalkan kedua gaya itu; kolom fitur yang dipakai model selalu diambil dari kolom file (bukan daftar tetap), sehingga model tidak bergantung pada satu jalur saja.

## Kontrak #3 — Alert
- **File:** `outputs/alerts.jsonl` (1 JSON per baris) · **Pembuat:** B+C (`pipeline score`) · **Konsumen:** dashboard (C)
```json
{"user": "7f3ce1b2c497fb5c", "day": "2010-03-03", "risk": 0.92, "label": 1,
 "reasons": [{"feature": "n_new_domain", "label": "domain web baru", "value": 7.0, "kind": "count", "contribution": 0.31}],
 "explain_method": "shap",
 "tier": 3, "action": "analyst_ticket", "requires_human_approval": true,
 "note": "...", "summary": "Pengguna 7f3ce1b2… pada 2010-03-03 berisiko 0.92 ..."}
```
> `explain_method` ∈ `shap` | `shapley` | `deviation` — **dasar klaim di pitch**. Item `reasons` berisi `contribution` (kontribusi ke skor risiko, untuk shap/shapley) atau `z` (untuk deviation).
> `reasons[].kind` = `"count"` (nilai = hitungan hari itu) atau `"z"` (nilai = simpanan deviasi) → pemakaian di ringkasan kasus supaya angka tidak dibaca salah.
> `label` hanya ada untuk evaluasi/demo; di sistem sungguhan tidak tersedia. Jangan tampilkan sebagai "jawaban" saat demo tanpa menjelaskannya.

## Kontrak #4 — Model bundle
- **File:** `models/bundle.joblib` (LANL: `models/bundle_lanl.joblib`). Tidak di-commit; dibuat ulang dengan `make run`.
- Kunci wajib (gaya lama, tetap ada): `sup`, `iso`, `an_lo`, `an_hi`, `base_mean`, `base_std`, `feature_cols`.
- Kunci tambahan (hasil tuning, dipakai `score.py` & `policy.py`):
  | Kunci | Arti |
  |---|---|
  | `background` | sampel baris normal sebagai pembanding untuk penjelasan Shapley/SHAP |
  | `alpha` | bobot cabang supervised pada gabungan skor (dipilih di validasi; termasuk 0.0/1.0) |
  | `combine_method` | `weighted` \| `max` \| `rank` (dipilih di validasi) |
  | `thresholds` | ambang tier 2 & 3 hasil kalibrasi validasi (dipakai `policy.policy_cfg`) |
  | `positive_class_weight` | bobot kelas positif yang dipakai supervised |
  | `selection` | kandidat + skor validasi (jawaban untuk "angka ini dari mana?") |
- `alpha`/`combine_method`/`thresholds` **boleh** bernilai `None` (mis. tidak ada positif di validasi) → pemakai wajib punya cadangan: `score.risk_from_array` memakai alpha bawaan dan `policy_cfg` memakai angka dari config.
- **Catatan s390x:** model di-*pickle* pada arsitektur yang sama dengan yang memuatnya → **latih & muat di mesin yang sama (LinuxONE)**; jangan latih di laptop lalu muat di VM.

## Kontrak #5 — Metrik & benchmark
- `outputs/metrics.json` (CERT) dan `outputs/lanl_metrics.json` (LANL), keduanya dari B. Isi:
  | Kunci | Arti |
  |---|---|
  | `precision_at_budget`, `recall_at_budget`, `n_alerts`, `alert_budget_per_day` | metrik utama: hanya `K` alert teratas **per hari** |
  | `n_malicious_user_days`, `true_positive_alerts` | dasar perhitungan precision/recall (jumlah apa adanya) |
  | `insiders_in_test`, `insiders_detected`, `median_days_to_detection` | per ORANG, bukan per baris |
  | `dataset`, `split` | dataset + potongan temporal (tanggal potong, jumlah hari) |
  | `model` | model & hyperparameter yang benar-benar dipakai |
  | `tier_thresholds`, `tier_calibration` | ambang tier + sumbernya (`calibrated_on_validation` \| `config`) |
  | `generalization_audit` | PR-AUC di potongan train/validasi/test → seberapa besar model "menghafal" |
  | `test_evaluation` | model utama + 4 pembanding pada potongan & budget yang **sama** |
  | `model_selection` | seluruh kandidat tuning (bobot positif, alpha, cara gabung) + pemenangnya |
- `outputs/benchmark.json` (A): `single_row_ms_p50/p95`, `batch_rows_per_sec`.
- **Semua angka di video/README harus bisa ditelusuri ke file-file ini.** Bila sebuah angka tidak ada di sini, jangan ditampilkan.

## Endpoint API (C)
| Metode | Path | Fungsi |
|---|---|---|
| GET | `/health` | cek sehat |
| GET | `/api/alerts?limit=N` | alert teratas berdasarkan risiko |
| GET | `/api/metrics` | isi `metrics.json` |
| POST | `/api/score` | body `{"features": {...}}` → `{risk, tier, action, ...}` |

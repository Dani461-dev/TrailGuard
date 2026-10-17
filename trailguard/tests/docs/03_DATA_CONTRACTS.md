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
- Hanya akun manusia (`src_user` diawali `U`); `user`, `host`, `dst_host` = keyed-hash.

| Kolom | Keterangan |
|---|---|
| `ts` | waktu (detik sejak awal data → datetime berpatokan 1970-01-01; hanya **relatif** bermakna) |
| `user`, `host`, `dst_host` | hash pengguna / komputer asal / komputer tujuan |
| `auth_type`, `logon_type`, `orientation` | `Kerberos`/`NTLM`…, `Network`/`Interactive`…, `LogOn`/`LogOff`/`TGS`… |
| `success` | 1 = Success, 0 = Fail |

Label LANL = event red-team (`redteam.txt.gz`) → `labels` dengan `start = end = waktu event`. Fitur LANL (10 dasar + 10 `_z`) didefinisikan di `builder_lanl.py`. File lain: `lanl_features.csv.gz`, `models/bundle_lanl.joblib`, `outputs/lanl_alerts.jsonl`, `outputs/lanl_metrics.json`.

### Format file antar-langkah
Default **CSV.gz**. Jika `io.format: parquet` dan pyarrow jalan → ekstensi `.parquet`; jika pyarrow gagal → otomatis kembali ke CSV dengan peringatan (`io_utils.py`). Kode lain **harus** membaca lewat `io_utils.read_table`, bukan `pd.read_csv` langsung.

## Kontrak #2 — Fitur harian
- **File:** `data/processed/features.csv.gz` · **Pembuat:** B · **Konsumen:** B (model), C (API/benchmark)
- 1 baris = 1 `user` × 1 `day`. Kolom: `user`, `day`, `label` (0/1), lalu **FEATURE_COLS** (didefinisikan di `features/builder.py`): 12 fitur dasar `n_*` + 12 deviasi `*_z` (z-score terhadap baseline 14 hari milik user itu sendiri, tanpa melihat hari ini → **bebas leakage**).
- Menambah fitur: tambahkan ke `BASE_COLS` (otomatis menghasilkan `_z`) + `FEATURE_LABELS` agar bisa dijelaskan.

## Kontrak #3 — Alert
- **File:** `outputs/alerts.jsonl` (1 JSON per baris) · **Pembuat:** B+C (`pipeline score`) · **Konsumen:** dashboard (C)
```json
{"user": "7f3ce1b2c497fb5c", "day": "2010-03-03", "risk": 0.92, "label": 1,
 "reasons": [{"feature": "n_new_domain", "label": "domain web baru", "value": 7.0, "contribution": 0.31}],
 "explain_method": "shap",
 "tier": 3, "action": "analyst_ticket", "requires_human_approval": true,
 "note": "...", "summary": "Pengguna 7f3ce1b2… pada 2010-03-03 berisiko 0.92 ..."}
```
> `explain_method` ∈ `shap` | `shapley` | `deviation` — **dasar klaim di pitch**. Item `reasons` berisi `contribution` (kontribusi ke skor risiko, untuk shap/shapley) atau `z` (untuk deviation).
> `label` hanya ada untuk evaluasi/demo; di sistem sungguhan tidak tersedia. Jangan tampilkan sebagai "jawaban" saat demo tanpa menjelaskannya.

## Kontrak #4 — Model bundle
- **File:** `models/bundle.joblib` (dict: `sup`, `iso`, `an_lo`, `an_hi`, `base_mean`, `base_std`, `feature_cols`). Tidak di-commit; dibuat ulang dengan `make run`.
- **Catatan s390x:** model di-*pickle* pada arsitektur yang sama dengan yang memuatnya → **latih & muat di mesin yang sama (LinuxONE)**; jangan latih di laptop lalu muat di VM.

## Kontrak #5 — Metrik & benchmark
- `outputs/metrics.json` (B): `precision_at_budget`, `recall_at_budget`, `insiders_detected`, `median_days_to_detection`, dll.
- `outputs/benchmark.json` (A): `single_row_ms_p50/p95`, `batch_rows_per_sec`.
- **Semua angka di video/README harus bisa ditelusuri ke dua file ini.**

## Endpoint API (C)
| Metode | Path | Fungsi |
|---|---|---|
| GET | `/health` | cek sehat |
| GET | `/api/alerts?limit=N` | alert teratas berdasarkan risiko |
| GET | `/api/metrics` | isi `metrics.json` |
| POST | `/api/score` | body `{"features": {...}}` → `{risk, tier, action, ...}` |

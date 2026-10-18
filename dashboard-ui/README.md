# TrailGuard — Landing (IBM Z Datathon 2026)

Landing page statis untuk **TrailGuard**: *Privacy-Preserving, Explainable Insider-Threat Detection on IBM LinuxONE*.
Dibangun dengan **Astro + Tailwind CSS** (basis template Automark). Satu halaman, tanpa backend.

- Event code: `SSF2026` · Tema: *AI Secured — Innovation Without Exposure*
- Isi halaman disusun dari repo backend (`../backend`) + Rencana Proyek v3.1
- Sumber konten landing: `src/data/trailguard.ts`

## Menjalankan

```bash
npm install
npm run dev       # http://localhost:4321
npm run build     # hasil statis ke dist/
npm run preview   # pratinjau hasil build
npm run check     # astro check (tipe)
```

> `npm run dev`/`build` menjalankan `scripts/themeGenerator.js` lebih dulu untuk
> menghasilkan `src/styles/generated-theme.css` dari `src/config/theme.json`.

## Deployment ke LinuxONE

Landing ini adalah berkas statis. Dua cara:

1. **Bangun di VM:** `npm ci && npm run build` lalu sajikan `dist/` dengan nginx
   (`config/nginx/nginx.conf` disertakan). Container siap pakai lewat `Dockerfile`.
2. **Bangun di laptop, salin hasil:** bila tooling Node bermasalah di s390x
   (lihat risiko R17), jalankan `npm run build` di laptop lalu salin `dist/` ke VM.

## Halaman

| Rute | Isi |
|---|---|
| `/` | Landing (presentasi proyek) |
| `/dashboard` | Dashboard alert (React): metrik, grafik risiko harian, filter tier, approve/reject |
| `/replay` | Pemutaran ulang event (React) — berlabel jujur **REPLAY** |

### Dashboard & Replay

Dashboard memanggil API Flask (`GET /api/config|alerts|metrics|decisions|replay`,
`POST /api/decision`). Saat dev, Vite mem-*proxy* `/api` → `http://localhost:8000`
(lihat `astro.config.mjs`), jadi jalankan backend di sampingnya:

```bash
# terminal 1 (backend)
cd ../backend && make toy && make api        # Flask :8000

# terminal 2 (frontend)
npm run dev                                  # :4321 -> buka /dashboard
```

Bila API tidak tersedia / belum ada data, dashboard otomatis memakai **data contoh**
dan menampilkan badge “Pratinjau” (bukan angka nyata). Atur URL API lain lewat
`PUBLIC_API_URL` saat build.


## Struktur singkat

```
src/
  data/trailguard.ts              sumber konten landing (semua section)
  pages/index.astro               landing (satu halaman)
  pages/dashboard.astro           halaman dashboard (mount React island)
  pages/replay.astro              halaman replay (mount React island)
  layouts/Base.astro              <head>, Header, Footer, font
  layouts/components/trailguard/  komponen section landing
  layouts/dashboard/              komponen React dashboard & replay + ui.ts
  lib/trailguardApi.ts            klien API + tipe + data contoh (fallback)
  config/{config,menu,social,theme}.json
public/images/{logo.svg,favicon.png,og-image.png}
```

> Pipeline deteksi (Python) ada di repo terpisah: [`../backend`](../backend) — sumber kebenaran konten.

## Catatan

- Angka metrik (precision/recall @ budget, time-to-detection) **belum diisi** —
  menunggu `outputs/metrics.json` dari pipeline. Tidak ada angka toy yang ditampilkan.
- Aturan klaim jujur (SHAP / Parquet / dua dataset) mengikuti
  `../backend/docs/04_SUBMISSION_CHECKLIST.md`.

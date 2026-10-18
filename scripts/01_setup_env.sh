#!/usr/bin/env bash
# Membuat virtualenv & memasang dependensi inti.  Jalankan:  bash scripts/01_setup_env.sh
set -e
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt   # kalau gagal: SALIN PESAN ERRORNYA ke Discord/Grup A
[ -f .env ] || { cp .env.example .env; echo ">> .env dibuat. EDIT dan isi TRAILGUARD_HMAC_KEY."; }
echo "Selesai. Aktifkan lagi nanti dengan:  source .venv/bin/activate"
